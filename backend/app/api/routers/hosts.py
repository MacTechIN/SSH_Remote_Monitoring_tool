from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_current_user, get_db_session
from app.core.security import encrypt_secret
from app.models.entities import Host, ProcessSnapshot
from app.schemas.hosts import (
    HostCreate,
    HostResponse,
    HostUpdate,
    LiveSnapshotResponse,
    ProcessRecordResponse,
    UserSessionResponse,
)
from app.services.ssh import test_connection_sync
from app.worker.tasks import schedule_host_poll

router = APIRouter(prefix="/hosts", tags=["hosts"])


@router.get("", response_model=list[HostResponse])
def list_hosts(
    db: Session = Depends(get_db_session),
    _: str = Depends(get_current_user),
) -> list[Host]:
    return db.query(Host).order_by(Host.name).all()


@router.post("", response_model=HostResponse, status_code=status.HTTP_201_CREATED)
def create_host(
    body: HostCreate,
    db: Session = Depends(get_db_session),
    user: str = Depends(get_current_user),
) -> Host:
    host = Host(
        name=body.name,
        hostname=body.hostname,
        port=body.port,
        ssh_user=body.ssh_user,
        encrypted_key=encrypt_secret(body.private_key),
        poll_interval_sec=body.poll_interval_sec,
        enabled=body.enabled,
    )
    db.add(host)
    db.commit()
    db.refresh(host)
    if host.enabled:
        schedule_host_poll(host.id, host.poll_interval_sec)
    return host


@router.get("/{host_id}", response_model=HostResponse)
def get_host(
    host_id: str,
    db: Session = Depends(get_db_session),
    _: str = Depends(get_current_user),
) -> Host:
    host = db.query(Host).filter(Host.id == host_id).first()
    if not host:
        raise HTTPException(status_code=404, detail="Host not found")
    return host


@router.patch("/{host_id}", response_model=HostResponse)
def update_host(
    host_id: str,
    body: HostUpdate,
    db: Session = Depends(get_db_session),
    _: str = Depends(get_current_user),
) -> Host:
    host = db.query(Host).filter(Host.id == host_id).first()
    if not host:
        raise HTTPException(status_code=404, detail="Host not found")
    data = body.model_dump(exclude_unset=True)
    if "private_key" in data:
        data["encrypted_key"] = encrypt_secret(data.pop("private_key"))
    for k, v in data.items():
        setattr(host, k, v)
    db.commit()
    db.refresh(host)
    if host.enabled:
        schedule_host_poll(host.id, host.poll_interval_sec)
    return host


@router.delete("/{host_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_host(
    host_id: str,
    db: Session = Depends(get_db_session),
    _: str = Depends(get_current_user),
) -> None:
    host = db.query(Host).filter(Host.id == host_id).first()
    if not host:
        raise HTTPException(status_code=404, detail="Host not found")
    db.delete(host)
    db.commit()


@router.post("/{host_id}/test-connection")
def test_host_connection(
    host_id: str,
    db: Session = Depends(get_db_session),
    _: str = Depends(get_current_user),
) -> dict:
    from app.core.security import decrypt_secret

    host = db.query(Host).filter(Host.id == host_id).first()
    if not host:
        raise HTTPException(status_code=404, detail="Host not found")
    key = decrypt_secret(host.encrypted_key)
    ok = test_connection_sync(host.hostname, host.port, host.ssh_user, key)
    return {"ok": ok}


@router.post("/{host_id}/collect")
def collect_now(
    host_id: str,
    db: Session = Depends(get_db_session),
    _: str = Depends(get_current_user),
) -> dict:
    from app.services.collector import collect_host
    from app.worker.redis_notify import publish_snapshot_update
    from app.services.rollup import build_daily_rollup

    snapshot = collect_host(db, host_id)
    if not snapshot:
        raise HTTPException(status_code=400, detail="Collection failed")
    publish_snapshot_update(host_id, snapshot.id, snapshot.collected_at.isoformat())
    build_daily_rollup(db, host_id=host_id)
    return {"ok": True, "snapshot_id": snapshot.id}


@router.get("/{host_id}/live", response_model=LiveSnapshotResponse)
def get_live_snapshot(
    host_id: str,
    db: Session = Depends(get_db_session),
    _: str = Depends(get_current_user),
) -> LiveSnapshotResponse:
    snap = (
        db.query(ProcessSnapshot)
        .options(
            joinedload(ProcessSnapshot.processes),
            joinedload(ProcessSnapshot.sessions),
        )
        .filter(ProcessSnapshot.host_id == host_id)
        .order_by(ProcessSnapshot.collected_at.desc())
        .first()
    )
    if not snap:
        raise HTTPException(status_code=404, detail="No snapshot yet")
    return LiveSnapshotResponse(
        snapshot_id=snap.id,
        host_id=snap.host_id,
        collected_at=snap.collected_at,
        processes=[ProcessRecordResponse.model_validate(p) for p in snap.processes],
        sessions=[UserSessionResponse.model_validate(s) for s in snap.sessions],
    )

from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db_session
from app.models.entities import ProcessRecord, ProcessSnapshot
from app.schemas.search import ProcessSearchResponse, ProcessSearchResult

router = APIRouter(prefix="/search", tags=["search"])


@router.get("/processes", response_model=ProcessSearchResponse)
def search_processes(
    user: str | None = None,
    q: str | None = None,
    from_dt: datetime | None = Query(None, alias="from"),
    to_dt: datetime | None = Query(None, alias="to"),
    host_id: str | None = None,
    limit: int = Query(100, le=500),
    db: Session = Depends(get_db_session),
    _: str = Depends(get_current_user),
) -> ProcessSearchResponse:
    query = (
        db.query(ProcessRecord, ProcessSnapshot)
        .join(ProcessSnapshot, ProcessSnapshot.id == ProcessRecord.snapshot_id)
        .order_by(ProcessSnapshot.collected_at.desc())
    )
    if user:
        query = query.filter(ProcessRecord.user == user)
    if q:
        query = query.filter(ProcessRecord.cmd.ilike(f"%{q}%"))
    if host_id:
        query = query.filter(ProcessSnapshot.host_id == host_id)
    if from_dt:
        query = query.filter(ProcessSnapshot.collected_at >= from_dt)
    if to_dt:
        query = query.filter(ProcessSnapshot.collected_at <= to_dt)

    rows = query.limit(limit).all()
    items = [
        ProcessSearchResult(
            snapshot_id=snap.id,
            host_id=snap.host_id,
            collected_at=snap.collected_at,
            user=rec.user,
            comm=rec.comm,
            cmd=rec.cmd,
            classification=rec.classification.value,
        )
        for rec, snap in rows
    ]
    return ProcessSearchResponse(total=len(items), items=items)

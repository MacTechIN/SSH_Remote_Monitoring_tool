from app.core.database import SessionLocal
from app.models.entities import Host
from app.services.collector import collect_host
from app.services.rollup import build_daily_rollup
from app.worker.celery_app import celery_app


def schedule_host_poll(host_id: str, interval_sec: int) -> None:
    """Register periodic poll for a host via Celery beat schedule (dynamic)."""
    celery_app.conf.beat_schedule = celery_app.conf.get("beat_schedule", {}) or {}
    celery_app.conf.beat_schedule[f"poll-host-{host_id}"] = {
        "task": "app.worker.tasks.poll_host",
        "schedule": float(interval_sec),
        "args": (host_id,),
    }


@celery_app.task(name="app.worker.tasks.poll_host")
def poll_host(host_id: str) -> dict:
    db = SessionLocal()
    try:
        snapshot = collect_host(db, host_id)
        if snapshot:
            from app.worker.redis_notify import publish_snapshot_update

            publish_snapshot_update(host_id, snapshot.id, snapshot.collected_at.isoformat())
            build_daily_rollup(db, host_id=host_id)
            return {"ok": True, "snapshot_id": snapshot.id}
        return {"ok": False, "reason": "host disabled or missing"}
    finally:
        db.close()


@celery_app.task(name="app.worker.tasks.build_daily_rollup")
def build_daily_rollup_task(host_id: str | None = None) -> dict:
    db = SessionLocal()
    try:
        n = build_daily_rollup(db, host_id=host_id)
        return {"written": n}
    finally:
        db.close()


@celery_app.task(name="app.worker.tasks.poll_all_enabled")
def poll_all_enabled() -> dict:
    db = SessionLocal()
    try:
        hosts = db.query(Host).filter(Host.enabled.is_(True)).all()
        for h in hosts:
            poll_host.delay(h.id)
        return {"scheduled": len(hosts)}
    finally:
        db.close()

from celery import Celery

from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "ssh_monitor",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.worker.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    beat_scheduler="celery.beat:PersistentScheduler",
    beat_schedule={
        "rollup-daily": {
            "task": "app.worker.tasks.build_daily_rollup",
            "schedule": 3600.0,
            "args": (),
        },
    },
)

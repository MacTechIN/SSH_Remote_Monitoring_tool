from collections import defaultdict
from datetime import UTC, date, datetime

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.entities import DailyActivityRollup, ProcessClass, ProcessRecord, ProcessSnapshot


def build_daily_rollup(db: Session, host_id: str | None = None, target_date: date | None = None) -> int:
    """Aggregate user process events into hourly rollups for heatmap."""
    target = target_date or datetime.now(UTC).date()
    start = datetime.combine(target, datetime.min.time()).replace(tzinfo=UTC)
    end = datetime.combine(target, datetime.max.time()).replace(tzinfo=UTC)

    q = (
        db.query(
            ProcessSnapshot.host_id,
            ProcessRecord.user,
            func.date_trunc("hour", ProcessSnapshot.collected_at).label("hour_bucket"),
            ProcessRecord.comm,
            func.count(ProcessRecord.id).label("cnt"),
        )
        .join(ProcessRecord, ProcessRecord.snapshot_id == ProcessSnapshot.id)
        .filter(ProcessSnapshot.collected_at >= start, ProcessSnapshot.collected_at <= end)
        .filter(ProcessRecord.classification == ProcessClass.USER)
    )
    if host_id:
        q = q.filter(ProcessSnapshot.host_id == host_id)

    rows = q.group_by(
        ProcessSnapshot.host_id,
        ProcessRecord.user,
        "hour_bucket",
        ProcessRecord.comm,
    ).all()

    buckets: dict[tuple[str, str, int], dict] = defaultdict(lambda: {"count": 0, "processes": defaultdict(int)})

    for row in rows:
        hour = row.hour_bucket.hour if row.hour_bucket else 0
        key = (row.host_id, row.user, hour)
        buckets[key]["count"] += row.cnt
        buckets[key]["processes"][row.comm] += row.cnt

    written = 0
    for (h_id, user, hour), data in buckets.items():
        top = sorted(data["processes"].items(), key=lambda x: -x[1])[:5]
        summary = {"lines": [f"{c} ({n})" for c, n in top]}
        existing = (
            db.query(DailyActivityRollup)
            .filter_by(host_id=h_id, user=user, date=target, hour=hour)
            .first()
        )
        if existing:
            existing.event_count = data["count"]
            existing.summary_json = summary
        else:
            db.add(
                DailyActivityRollup(
                    host_id=h_id,
                    user=user,
                    date=target,
                    hour=hour,
                    event_count=data["count"],
                    summary_json=summary,
                )
            )
        written += 1
    db.commit()
    return written

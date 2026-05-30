from datetime import date, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db_session
from app.models.entities import DailyActivityRollup
from app.schemas.activity import CalendarCell, CalendarResponse, DaySummaryLine, DaySummaryResponse

router = APIRouter(prefix="/activity", tags=["activity"])

MAX_LEVEL = 4


def _level_from_count(count: int, max_count: int) -> int:
    if count <= 0 or max_count <= 0:
        return 0
    ratio = count / max_count
    if ratio < 0.25:
        return 1
    if ratio < 0.5:
        return 2
    if ratio < 0.75:
        return 3
    return 4


@router.get("/calendar", response_model=CalendarResponse)
def get_calendar(
    from_date: date = Query(..., alias="from"),
    to_date: date = Query(..., alias="to"),
    host_id: str | None = None,
    granularity: str = "day",
    db: Session = Depends(get_db_session),
    _: str = Depends(get_current_user),
) -> CalendarResponse:
    q = db.query(
        DailyActivityRollup.date,
        func.sum(DailyActivityRollup.event_count).label("total"),
    ).filter(DailyActivityRollup.date >= from_date, DailyActivityRollup.date <= to_date)
    if host_id:
        q = q.filter(DailyActivityRollup.host_id == host_id)
    rows = q.group_by(DailyActivityRollup.date).all()
    counts = {r.date: int(r.total or 0) for r in rows}
    max_count = max(counts.values(), default=0)

    cells: list[CalendarCell] = []
    current = from_date
    while current <= to_date:
        c = counts.get(current, 0)
        cells.append(
            CalendarCell(
                date=current.isoformat(),
                level=_level_from_count(c, max_count),
                count=c,
            )
        )
        current += timedelta(days=1)

    return CalendarResponse(granularity=granularity, cells=cells)


@router.get("/day-summary", response_model=DaySummaryResponse)
def day_summary(
    date_param: date = Query(..., alias="date"),
    host_id: str | None = None,
    db: Session = Depends(get_db_session),
    _: str = Depends(get_current_user),
) -> DaySummaryResponse:
    q = db.query(DailyActivityRollup).filter(DailyActivityRollup.date == date_param)
    if host_id:
        q = q.filter(DailyActivityRollup.host_id == host_id)
    rollups = q.all()

    by_user: dict[str, list[str]] = {}
    for r in rollups:
        lines = r.summary_json.get("lines", []) if isinstance(r.summary_json, dict) else []
        by_user.setdefault(r.user, []).extend(lines)

    result_lines: list[DaySummaryLine] = []
    for user, parts in sorted(by_user.items()):
        summary = ", ".join(parts[:5]) if parts else "no activity"
        result_lines.append(DaySummaryLine(user=user, summary=summary))

    return DaySummaryResponse(date=date_param.isoformat(), host_id=host_id, lines=result_lines)

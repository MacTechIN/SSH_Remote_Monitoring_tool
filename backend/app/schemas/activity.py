from pydantic import BaseModel


class CalendarCell(BaseModel):
    date: str
    level: int
    count: int


class CalendarResponse(BaseModel):
    granularity: str
    cells: list[CalendarCell]


class DaySummaryLine(BaseModel):
    user: str
    summary: str


class DaySummaryResponse(BaseModel):
    date: str
    host_id: str | None
    lines: list[DaySummaryLine]

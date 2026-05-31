from typing import Protocol

from backend.app.models import HostMetrics


class HistoryRepository(Protocol):
    def init(self) -> None: ...

    def record_metrics(self, metrics: list[HostMetrics]) -> None: ...

    def get_history(self, host_id: str, limit: int = 50) -> list[HostMetrics]: ...

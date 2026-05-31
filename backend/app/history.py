from backend.app.models import HostMetrics
from backend.app.repositories import get_history_repository


def init_db() -> None:
    get_history_repository().init()


def record_metrics(metrics: list[HostMetrics]) -> None:
    get_history_repository().record_metrics(metrics)


def get_history(host_id: str, limit: int = 50) -> list[HostMetrics]:
    return get_history_repository().get_history(host_id, limit=limit)

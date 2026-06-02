from backend.app.models import HostMetrics, ProcessSnapshot
from backend.app.repositories import get_history_repository


def init_db() -> None:
    get_history_repository().init()


def record_metrics(metrics: list[HostMetrics]) -> None:
    get_history_repository().record_metrics(metrics)


def get_history(host_id: str, limit: int = 50) -> list[HostMetrics]:
    return get_history_repository().get_history(host_id, limit=limit)


def record_process_snapshot(snapshot: ProcessSnapshot) -> None:
    get_history_repository().record_process_snapshot(snapshot)


def get_process_history(host_id: str, limit: int = 20) -> list[ProcessSnapshot]:
    return get_history_repository().get_process_history(host_id, limit=limit)

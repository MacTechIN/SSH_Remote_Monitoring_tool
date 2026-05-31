from backend.app.config import get_settings
from backend.app.repositories.file_history import FileHistoryRepository
from backend.app.repositories.file_hosts import FileHostRepository
from backend.app.repositories.history import HistoryRepository
from backend.app.repositories.hosts import HostRepository


def get_host_repository() -> HostRepository:
    if get_settings().storage_backend == "firestore":
        from backend.app.repositories.firestore_hosts import FirestoreHostRepository

        return FirestoreHostRepository()
    return FileHostRepository()


def get_history_repository() -> HistoryRepository:
    if get_settings().storage_backend == "firestore":
        from backend.app.repositories.firestore_history import FirestoreHistoryRepository

        return FirestoreHistoryRepository()
    return FileHistoryRepository()

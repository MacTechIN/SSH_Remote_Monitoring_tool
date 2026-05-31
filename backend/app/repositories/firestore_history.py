from __future__ import annotations

from backend.app.config import get_settings
from backend.app.firebase_app import get_firestore_client
from backend.app.models import HostMetrics

HOSTS_COLLECTION = "hosts"
METRICS_SUBCOLLECTION = "metrics"


class FirestoreHistoryRepository:
    def init(self) -> None:
        return

    def record_metrics(self, metrics: list[HostMetrics]) -> None:
        settings = get_settings()
        if not settings.history_enabled or not metrics:
            return
        db = get_firestore_client()
        for item in metrics:
            payload = item.model_dump(mode="json")
            db.collection(HOSTS_COLLECTION).document(item.host_id).collection(
                METRICS_SUBCOLLECTION
            ).add(payload)

    def get_history(self, host_id: str, limit: int = 50) -> list[HostMetrics]:
        limit = max(1, min(limit, 500))
        query = (
            get_firestore_client()
            .collection(HOSTS_COLLECTION)
            .document(host_id)
            .collection(METRICS_SUBCOLLECTION)
            .order_by("checked_at", direction="DESCENDING")
            .limit(limit)
        )
        return [HostMetrics.model_validate(doc.to_dict()) for doc in query.stream()]

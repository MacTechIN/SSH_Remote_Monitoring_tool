from __future__ import annotations

from backend.app.firebase_app import get_firestore_client
from backend.app.models import HostConfig

HOSTS_COLLECTION = "hosts"


class FirestoreHostRepository:
    def _collection(self):
        return get_firestore_client().collection(HOSTS_COLLECTION)

    def load_hosts(self) -> list[HostConfig]:
        hosts: list[HostConfig] = []
        for doc in self._collection().stream():
            data = doc.to_dict() or {}
            data.setdefault("id", doc.id)
            hosts.append(HostConfig.model_validate(data))
        return sorted(hosts, key=lambda item: item.name.lower())

    def get_host(self, host_id: str) -> HostConfig | None:
        doc = self._collection().document(host_id).get()
        if not doc.exists:
            return None
        data = doc.to_dict() or {}
        data.setdefault("id", doc.id)
        return HostConfig.model_validate(data)

    def add_host(self, host: HostConfig) -> HostConfig:
        ref = self._collection().document(host.id)
        if ref.get().exists:
            raise ValueError(f"Host id '{host.id}' already exists")
        ref.set(host.model_dump(mode="json", exclude_none=True))
        return host

    def update_host(self, host_id: str, updates: dict) -> HostConfig:
        ref = self._collection().document(host_id)
        if not ref.get().exists:
            raise KeyError(f"Host '{host_id}' not found")
        ref.set(updates, merge=True)
        return self.get_host(host_id)  # type: ignore[return-value]

    def delete_host(self, host_id: str) -> None:
        ref = self._collection().document(host_id)
        if not ref.get().exists:
            raise KeyError(f"Host '{host_id}' not found")
        metrics = ref.collection("metrics").limit(500).stream()
        batch = get_firestore_client().batch()
        count = 0
        for metric in metrics:
            batch.delete(metric.reference)
            count += 1
            if count >= 400:
                batch.commit()
                batch = get_firestore_client().batch()
                count = 0
        if count:
            batch.commit()
        ref.delete()

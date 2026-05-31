from __future__ import annotations

import re
import threading

import yaml

from backend.app.config import get_settings
from backend.app.models import HostConfig

_lock = threading.RLock()
_ID_PATTERN = re.compile(r"^[a-z0-9]([a-z0-9-]{0,62}[a-z0-9])?$")


class FileHostRepository:
    def load_hosts(self) -> list[HostConfig]:
        settings = get_settings()
        path = settings.hosts_file
        if not path.is_file():
            return []
        with path.open(encoding="utf-8") as handle:
            raw = yaml.safe_load(handle) or {}
        return [HostConfig.model_validate(item) for item in raw.get("hosts") or []]

    def _write(self, hosts: list[HostConfig]) -> None:
        settings = get_settings()
        path = settings.hosts_file
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"hosts": [h.model_dump(mode="json", exclude_none=True) for h in hosts]}
        with path.open("w", encoding="utf-8") as handle:
            yaml.safe_dump(payload, handle, allow_unicode=True, sort_keys=False)

    def get_host(self, host_id: str) -> HostConfig | None:
        for host in self.load_hosts():
            if host.id == host_id:
                return host
        return None

    def add_host(self, host: HostConfig) -> HostConfig:
        with _lock:
            hosts = self.load_hosts()
            if any(item.id == host.id for item in hosts):
                raise ValueError(f"Host id '{host.id}' already exists")
            hosts.append(host)
            self._write(hosts)
        return host

    def update_host(self, host_id: str, updates: dict) -> HostConfig:
        with _lock:
            hosts = self.load_hosts()
            index = next((i for i, h in enumerate(hosts) if h.id == host_id), None)
            if index is None:
                raise KeyError(f"Host '{host_id}' not found")
            current = hosts[index].model_dump()
            current.update(updates)
            updated = HostConfig.model_validate(current)
            hosts[index] = updated
            self._write(hosts)
        return updated

    def delete_host(self, host_id: str) -> None:
        with _lock:
            hosts = self.load_hosts()
            filtered = [host for host in hosts if host.id != host_id]
            if len(filtered) == len(hosts):
                raise KeyError(f"Host '{host_id}' not found")
            self._write(filtered)

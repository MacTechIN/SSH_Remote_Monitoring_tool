from __future__ import annotations

import re
import threading

import yaml

from backend.app.config import get_settings
from backend.app.models import HostConfig

_lock = threading.RLock()
_ID_PATTERN = re.compile(r"^[a-z0-9]([a-z0-9-]{0,62}[a-z0-9])?$")


def slugify_id(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug[:64] if slug else "host"


def validate_host_id(host_id: str) -> None:
    if not _ID_PATTERN.match(host_id):
        raise ValueError(
            "Host id must be 2-64 chars, lowercase letters, numbers, and hyphens "
            "(cannot start or end with hyphen)."
        )


def load_hosts(settings=None) -> list[HostConfig]:
    settings = settings or get_settings()
    path = settings.hosts_file
    if not path.is_file():
        return []

    with path.open(encoding="utf-8") as handle:
        raw = yaml.safe_load(handle) or {}

    hosts_raw = raw.get("hosts") or []
    return [HostConfig.model_validate(item) for item in hosts_raw]


def _write_hosts_file(hosts: list[HostConfig], settings=None) -> None:
    settings = settings or get_settings()
    path = settings.hosts_file
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"hosts": [host.model_dump(mode="json", exclude_none=True) for host in hosts]}
    with path.open("w", encoding="utf-8") as handle:
        yaml.safe_dump(payload, handle, allow_unicode=True, sort_keys=False)


def save_hosts(hosts: list[HostConfig], settings=None) -> None:
    with _lock:
        _write_hosts_file(hosts, settings)


def unique_host_id(requested_id: str, hosts: list[HostConfig]) -> str:
    validate_host_id(requested_id)
    existing = {host.id for host in hosts}
    if requested_id not in existing:
        return requested_id
    suffix = 2
    while f"{requested_id}-{suffix}" in existing:
        suffix += 1
    return f"{requested_id}-{suffix}"


def get_host(host_id: str, settings=None) -> HostConfig | None:
    for host in load_hosts(settings):
        if host.id == host_id:
            return host
    return None


def add_host(host: HostConfig, settings=None) -> HostConfig:
    validate_host_id(host.id)
    with _lock:
        hosts = load_hosts(settings)
        if any(item.id == host.id for item in hosts):
            raise ValueError(f"Host id '{host.id}' already exists")
        hosts.append(host)
        _write_hosts_file(hosts, settings)
    return host


def update_host(host_id: str, updates: dict, settings=None) -> HostConfig:
    with _lock:
        hosts = load_hosts(settings)
        index = next((i for i, h in enumerate(hosts) if h.id == host_id), None)
        if index is None:
            raise KeyError(f"Host '{host_id}' not found")
        current = hosts[index].model_dump()
        current.update(updates)
        if "id" in updates and updates["id"] != host_id:
            validate_host_id(updates["id"])
            if any(h.id == updates["id"] for h in hosts if h.id != host_id):
                raise ValueError(f"Host id '{updates['id']}' already exists")
        updated = HostConfig.model_validate(current)
        hosts[index] = updated
        _write_hosts_file(hosts, settings)
    return updated


def delete_host(host_id: str, settings=None) -> None:
    with _lock:
        hosts = load_hosts(settings)
        filtered = [host for host in hosts if host.id != host_id]
        if len(filtered) == len(hosts):
            raise KeyError(f"Host '{host_id}' not found")
        _write_hosts_file(filtered, settings)

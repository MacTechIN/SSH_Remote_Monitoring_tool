from __future__ import annotations

import re

from backend.app.models import HostConfig
from backend.app.repositories import get_host_repository

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
    return get_host_repository().load_hosts()


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
    return get_host_repository().get_host(host_id)


def add_host(host: HostConfig, settings=None) -> HostConfig:
    validate_host_id(host.id)
    return get_host_repository().add_host(host)


def update_host(host_id: str, updates: dict, settings=None) -> HostConfig:
    return get_host_repository().update_host(host_id, updates)


def delete_host(host_id: str, settings=None) -> None:
    get_host_repository().delete_host(host_id)

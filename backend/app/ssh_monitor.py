from __future__ import annotations

import re
from datetime import UTC, datetime
from pathlib import Path

import paramiko

from backend.app.config import get_settings, load_hosts, resolve_private_key_path
from backend.app.models import (
    DiskMetrics,
    HostConfig,
    HostMetrics,
    HostStatus,
    MemoryMetrics,
)

METRICS_SCRIPT = """#!/bin/sh
echo "UPTIME:$(uptime -p 2>/dev/null || uptime | sed 's/.*up /up /' | sed 's/,.*//')"
if [ -r /proc/loadavg ]; then
  read l1 l5 l15 rest < /proc/loadavg
  echo "LOAD:$l1 $l5 $l15"
fi
if command -v free >/dev/null 2>&1; then
  free -m | awk '/^Mem:/ {printf "MEM:%s %s %s\\n", $2, $3, $7}'
fi
df -B1 / 2>/dev/null | awk 'NR==2 {printf "DISK:%s %s %s %s\\n", $2, $3, $4, $6}'
"""


def _percent(used: int, total: int) -> float:
    if total <= 0:
        return 0.0
    return round(used / total * 100, 1)


def parse_metrics_output(output: str, host_id: str) -> HostMetrics:
    uptime: str | None = None
    load_1 = load_5 = load_15 = None
    memory: MemoryMetrics | None = None
    disk: DiskMetrics | None = None

    for line in output.splitlines():
        line = line.strip()
        if line.startswith("UPTIME:"):
            uptime = line.removeprefix("UPTIME:").strip() or None
        elif line.startswith("LOAD:"):
            parts = line.removeprefix("LOAD:").split()
            if len(parts) >= 3:
                load_1, load_5, load_15 = (float(parts[0]), float(parts[1]), float(parts[2]))
        elif line.startswith("MEM:"):
            parts = line.removeprefix("MEM:").split()
            if len(parts) >= 3:
                total, used, available = (int(parts[0]), int(parts[1]), int(parts[2]))
                memory = MemoryMetrics(
                    total_mb=total,
                    used_mb=used,
                    available_mb=available,
                    used_percent=_percent(used, total),
                )
        elif line.startswith("DISK:"):
            parts = line.removeprefix("DISK:").split()
            if len(parts) >= 4:
                total, used, available, mount = (
                    int(parts[0]),
                    int(parts[1]),
                    int(parts[2]),
                    parts[3],
                )
                disk = DiskMetrics(
                    total_bytes=total,
                    used_bytes=used,
                    available_bytes=available,
                    used_percent=_percent(used, total),
                    mount=mount,
                )

    return HostMetrics(
        host_id=host_id,
        status=HostStatus.ONLINE,
        checked_at=datetime.now(UTC),
        uptime=uptime,
        load_1=load_1,
        load_5=load_5,
        load_15=load_15,
        memory=memory,
        disk=disk,
    )


def demo_metrics(host: HostConfig) -> HostMetrics:
    seed = sum(ord(c) for c in host.id)
    used_mem = 2048 + (seed % 512)
    total_mem = 4096
    used_disk = 40_000_000_000 + (seed % 10) * 1_000_000_000
    total_disk = 100_000_000_000
    return HostMetrics(
        host_id=host.id,
        status=HostStatus.ONLINE,
        checked_at=datetime.now(UTC),
        uptime="up 12 days, 3 hours",
        load_1=0.15 + (seed % 10) / 100,
        load_5=0.12 + (seed % 8) / 100,
        load_15=0.10 + (seed % 6) / 100,
        memory=MemoryMetrics(
            total_mb=total_mem,
            used_mb=used_mem,
            available_mb=total_mem - used_mem,
            used_percent=_percent(used_mem, total_mem),
        ),
        disk=DiskMetrics(
            total_bytes=total_disk,
            used_bytes=used_disk,
            available_bytes=total_disk - used_disk,
            used_percent=_percent(used_disk, total_disk),
            mount="/",
        ),
    )


def _connect(host: HostConfig, key_path: Path | None) -> paramiko.SSHClient:
    settings = get_settings()
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    connect_kwargs: dict = {
        "hostname": host.hostname,
        "port": host.port,
        "username": host.username,
        "timeout": settings.ssh_connect_timeout,
        "allow_agent": True,
        "look_for_keys": key_path is None,
    }
    if key_path is not None:
        connect_kwargs["key_filename"] = str(key_path)

    client.connect(**connect_kwargs)
    return client


def collect_host_metrics(host: HostConfig) -> HostMetrics:
    settings = get_settings()
    if settings.demo_mode:
        return demo_metrics(host)

    key_path = resolve_private_key_path(host, settings)
    client: paramiko.SSHClient | None = None
    try:
        client = _connect(host, key_path)
        _, stdout, stderr = client.exec_command(
            METRICS_SCRIPT,
            timeout=settings.command_timeout,
        )
        exit_code = stdout.channel.recv_exit_status()
        output = stdout.read().decode("utf-8", errors="replace")
        errors = stderr.read().decode("utf-8", errors="replace").strip()

        if exit_code != 0:
            message = errors or f"Remote script exited with code {exit_code}"
            return HostMetrics(
                host_id=host.id,
                status=HostStatus.ERROR,
                checked_at=datetime.now(UTC),
                error=message,
            )

        if not output.strip():
            return HostMetrics(
                host_id=host.id,
                status=HostStatus.ERROR,
                checked_at=datetime.now(UTC),
                error="Empty response from remote host",
            )

        return parse_metrics_output(output, host.id)
    except paramiko.AuthenticationException:
        return HostMetrics(
            host_id=host.id,
            status=HostStatus.ERROR,
            checked_at=datetime.now(UTC),
            error="SSH authentication failed",
        )
    except (paramiko.SSHException, OSError, TimeoutError) as exc:
        offline_pattern = re.compile(r"(timed out|unable to connect|no route|refused)", re.I)
        status = HostStatus.OFFLINE if offline_pattern.search(str(exc)) else HostStatus.ERROR
        return HostMetrics(
            host_id=host.id,
            status=status,
            checked_at=datetime.now(UTC),
            error=str(exc),
        )
    finally:
        if client is not None:
            client.close()


def collect_all_metrics() -> list[HostMetrics]:
    hosts = load_hosts()
    return [collect_host_metrics(host) for host in hosts]

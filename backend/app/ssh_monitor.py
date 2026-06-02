from __future__ import annotations

import io
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
    ProcessCategory,
    ProcessInfo,
    ProcessSnapshot,
    ProcessSummary,
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

PROCESS_SCRIPT = r"""#!/bin/sh
ps -eo pid=,ppid=,user=,comm=,pcpu=,pmem=,etime=,args= --sort=-pcpu 2>/dev/null | awk '
{
  pid=$1; ppid=$2; user=$3; comm=$4; cpu=$5; mem=$6; elapsed=$7;
  $1=$2=$3=$4=$5=$6=$7="";
  sub(/^ +/, "");
  printf "PROC:%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n", pid, ppid, user, comm, cpu, mem, elapsed, $0
}'
"""

SYSTEM_USERS = {
    "root",
    "daemon",
    "bin",
    "sys",
    "sync",
    "games",
    "man",
    "lp",
    "mail",
    "news",
    "uucp",
    "proxy",
    "www-data",
    "backup",
    "list",
    "irc",
    "_apt",
    "nobody",
    "systemd-network",
    "systemd-resolve",
    "messagebus",
    "sshd",
    "syslog",
}

SYSTEM_COMMANDS = {
    "systemd",
    "kthreadd",
    "kworker",
    "ksoftirqd",
    "migration",
    "rcu_sched",
    "rcu_preempt",
    "watchdog",
    "dbus-daemon",
    "cron",
    "rsyslogd",
    "sshd",
    "agetty",
    "udevd",
    "systemd-journal",
    "systemd-logind",
}

USER_PATH_PREFIXES = ("/home/", "/opt/", "/srv/", "/var/www/", "/usr/local/")


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


def classify_process(user: str, command: str, cmdline: str) -> tuple[ProcessCategory, str]:
    command_lower = command.lower()
    cmdline_lower = cmdline.lower()

    if cmdline.startswith("[") and cmdline.endswith("]"):
        return ProcessCategory.SYSTEM, "kernel thread"
    if any(cmdline.startswith(prefix) for prefix in USER_PATH_PREFIXES):
        return ProcessCategory.USER, "user-managed path"
    if f"/home/{user}/" in cmdline or f"/run/user/" in cmdline:
        return ProcessCategory.USER, "user home or session path"
    if user not in SYSTEM_USERS:
        return ProcessCategory.USER, "non-system account"
    if command_lower in SYSTEM_COMMANDS or cmdline_lower.startswith(("/usr/sbin/", "/sbin/")):
        return ProcessCategory.SYSTEM, "known Linux system process"
    if user == "root":
        return ProcessCategory.SYSTEM, "root-owned system process"
    return ProcessCategory.UNKNOWN, "classification needs review"


def _to_float(value: str) -> float:
    try:
        return float(value)
    except ValueError:
        return 0.0


def _to_int(value: str) -> int:
    try:
        return int(value)
    except ValueError:
        return 0


def _summarize_processes(processes: list[ProcessInfo]) -> ProcessSummary:
    summary = ProcessSummary(total=len(processes))
    for process in processes:
        if process.category == ProcessCategory.SYSTEM:
            summary.system += 1
        elif process.category == ProcessCategory.USER:
            summary.user += 1
        else:
            summary.unknown += 1
    return summary


def parse_process_output(output: str, host_id: str) -> ProcessSnapshot:
    processes: list[ProcessInfo] = []
    for line in output.splitlines():
        if not line.startswith("PROC:"):
            continue
        parts = line.removeprefix("PROC:").split("\t", maxsplit=7)
        if len(parts) != 8:
            continue
        pid, ppid, user, command, cpu, memory, elapsed, cmdline = parts
        category, reason = classify_process(user, command, cmdline or command)
        processes.append(
            ProcessInfo(
                pid=_to_int(pid),
                ppid=_to_int(ppid),
                user=user,
                command=command,
                cpu_percent=_to_float(cpu),
                memory_percent=_to_float(memory),
                elapsed=elapsed or None,
                cmdline=cmdline or command,
                category=category,
                reason=reason,
            )
        )

    return ProcessSnapshot(
        host_id=host_id,
        status=HostStatus.ONLINE,
        collected_at=datetime.now(UTC),
        summary=_summarize_processes(processes),
        processes=processes,
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


def demo_processes(host: HostConfig) -> ProcessSnapshot:
    sample = f"""
PROC:1\t0\troot\tsystemd\t0.0\t0.1\t12-03:10:00\t/sbin/init
PROC:42\t2\troot\tkworker\t0.0\t0.0\t12-03:09:58\t[kworker/0:1]
PROC:901\t1\troot\tsshd\t0.0\t0.2\t2-01:02:03\t/usr/sbin/sshd -D
PROC:1204\t1\t{host.username}\tpython\t4.5\t3.1\t01:14:22\t/home/{host.username}/apps/report-worker/.venv/bin/python worker.py
PROC:1288\t1204\t{host.username}\tnode\t1.8\t4.2\t00:31:09\t/opt/customer-api/node server.js
PROC:1301\t1\tdeploy\tjava\t9.9\t18.4\t03:44:11\t/srv/batch/current/bin/java -jar batch.jar
""".strip()
    return parse_process_output(sample, host.id)


def _load_pkey(settings, key_path: Path | None):
    if key_path is not None and key_path.is_file():
        return paramiko.Ed25519Key.from_private_key_file(str(key_path))
    if settings.ssh_private_key:
        return paramiko.Ed25519Key.from_private_key(io.StringIO(settings.ssh_private_key))
    return None


def _connect(host: HostConfig, key_path: Path | None) -> paramiko.SSHClient:
    settings = get_settings()
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    pkey = _load_pkey(settings, key_path)

    connect_kwargs: dict = {
        "hostname": host.hostname,
        "port": host.port,
        "username": host.username,
        "timeout": settings.ssh_connect_timeout,
        "allow_agent": pkey is None,
        "look_for_keys": pkey is None and key_path is None,
    }
    if pkey is not None:
        connect_kwargs["pkey"] = pkey
    elif key_path is not None:
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


def collect_host_processes(host: HostConfig) -> ProcessSnapshot:
    settings = get_settings()
    if settings.demo_mode:
        return demo_processes(host)

    key_path = resolve_private_key_path(host, settings)
    client: paramiko.SSHClient | None = None
    try:
        client = _connect(host, key_path)
        _, stdout, stderr = client.exec_command(
            PROCESS_SCRIPT,
            timeout=settings.command_timeout,
        )
        exit_code = stdout.channel.recv_exit_status()
        output = stdout.read().decode("utf-8", errors="replace")
        errors = stderr.read().decode("utf-8", errors="replace").strip()

        if exit_code != 0:
            message = errors or f"Remote process script exited with code {exit_code}"
            return ProcessSnapshot(
                host_id=host.id,
                status=HostStatus.ERROR,
                collected_at=datetime.now(UTC),
                error=message,
            )

        if not output.strip():
            return ProcessSnapshot(
                host_id=host.id,
                status=HostStatus.ERROR,
                collected_at=datetime.now(UTC),
                error="Empty process response from remote host",
            )

        return parse_process_output(output, host.id)
    except paramiko.AuthenticationException:
        return ProcessSnapshot(
            host_id=host.id,
            status=HostStatus.ERROR,
            collected_at=datetime.now(UTC),
            error="SSH authentication failed",
        )
    except (paramiko.SSHException, OSError, TimeoutError) as exc:
        offline_pattern = re.compile(r"(timed out|unable to connect|no route|refused)", re.I)
        status = HostStatus.OFFLINE if offline_pattern.search(str(exc)) else HostStatus.ERROR
        return ProcessSnapshot(
            host_id=host.id,
            status=status,
            collected_at=datetime.now(UTC),
            error=str(exc),
        )
    finally:
        if client is not None:
            client.close()


def collect_all_metrics() -> list[HostMetrics]:
    hosts = load_hosts()
    return [collect_host_metrics(host) for host in hosts]

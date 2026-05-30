"""Parse ps(1) and who(1) output — OS variants may need parser_version bumps."""

from __future__ import annotations

from dataclasses import dataclass

PARSER_VERSION = "1"


@dataclass
class ParsedProcess:
    pid: int
    ppid: int
    user: str
    comm: str
    cmd: str
    cpu_percent: float | None
    mem_percent: float | None


@dataclass
class ParsedSession:
    user: str
    tty: str | None
    login_at: str | None
    idle: str | None
    from_ip: str | None


def parse_ps(output: str) -> list[ParsedProcess]:
    lines = [ln for ln in output.strip().splitlines() if ln.strip()]
    if len(lines) < 2:
        return []
    results: list[ParsedProcess] = []
    for line in lines[1:]:
        parsed = _parse_ps_line(line)
        if parsed:
            results.append(parsed)
    return results


def _parse_ps_line(line: str) -> ParsedProcess | None:
    parts = line.split()
    if len(parts) < 8:
        return None
    try:
        pid = int(parts[0])
        ppid = int(parts[1])
        user = parts[2]
        comm = parts[3]
        cpu = float(parts[-3]) if parts[-3] not in ("-", "") else None
        mem = float(parts[-2]) if parts[-2] not in ("-", "") else None
        cmd = " ".join(parts[4:-3]) or comm
        return ParsedProcess(pid=pid, ppid=ppid, user=user, comm=comm, cmd=cmd, cpu_percent=cpu, mem_percent=mem)
    except (ValueError, IndexError):
        return None


def parse_who(output: str) -> list[ParsedSession]:
    sessions: list[ParsedSession] = []
    for line in output.strip().splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split()
        if len(parts) < 1:
            continue
        user = parts[0]
        tty = parts[1] if len(parts) > 1 else None
        login_at = parts[2] if len(parts) > 2 else None
        idle = parts[4] if len(parts) > 4 else None
        from_ip = parts[5].strip("()") if len(parts) > 5 else None
        sessions.append(
            ParsedSession(user=user, tty=tty, login_at=login_at, idle=idle, from_ip=from_ip)
        )
    return sessions


# Fallback: extract users from ps when who is empty
def session_users_from_ps(processes: list[ParsedProcess]) -> set[str]:
    return {p.user for p in processes if p.user and p.user != "root"}

"""SSH execution via asyncssh — sync wrapper for Celery."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass

import asyncssh

from app.core.config import get_settings

settings = get_settings()

PS_COMMAND = "ps -eo pid,ppid,user:32,comm,cmd,%cpu,%mem,etime --sort=-%cpu | head -n 200"
WHO_COMMAND = "who -u 2>/dev/null || who"


@dataclass
class SshCommandResult:
    stdout: str
    stderr: str
    exit_status: int


async def _run_commands(
    hostname: str,
    port: int,
    username: str,
    private_key: str,
    commands: list[str],
) -> list[SshCommandResult]:
    key = asyncssh.import_private_key(private_key)
    results: list[SshCommandResult] = []
    async with asyncssh.connect(
        hostname,
        port=port,
        username=username,
        client_keys=[key],
        known_hosts=None,
        login_timeout=settings.ssh_command_timeout,
    ) as conn:
        for cmd in commands:
            result = await asyncio.wait_for(
                conn.run(cmd, check=False),
                timeout=settings.ssh_command_timeout,
            )
            results.append(
                SshCommandResult(
                    stdout=result.stdout or "",
                    stderr=result.stderr or "",
                    exit_status=result.exit_status or 0,
                )
            )
    return results


def run_on_host(
    hostname: str,
    port: int,
    username: str,
    private_key: str,
    commands: list[str] | None = None,
) -> tuple[str, str]:
    cmds = commands or [PS_COMMAND, WHO_COMMAND]
    results = asyncio.run(_run_commands(hostname, port, username, private_key, cmds))
    ps_out = results[0].stdout if results else ""
    who_out = results[1].stdout if len(results) > 1 else ""
    return ps_out, who_out


async def test_connection(hostname: str, port: int, username: str, private_key: str) -> bool:
    try:
        await _run_commands(hostname, port, username, private_key, ["echo ok"])
        return True
    except (asyncssh.Error, asyncio.TimeoutError, OSError):
        return False


def test_connection_sync(hostname: str, port: int, username: str, private_key: str) -> bool:
    return asyncio.run(test_connection(hostname, port, username, private_key))

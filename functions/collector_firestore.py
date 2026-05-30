"""Collect SSH snapshot and persist to Firestore."""

from __future__ import annotations

import sys
from datetime import UTC, datetime
from pathlib import Path

# Reuse Docker backend parsers / classifier / ssh
BACKEND = Path(__file__).resolve().parent.parent / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.core.config import get_settings
from app.core.security import decrypt_secret
from app.models.entities import ProcessClass
from app.services.classifier import DEFAULT_SYSTEM_COMM, classify_process
from app.services.parser import PARSER_VERSION, parse_ps, parse_who
from app.services.ssh import run_on_host

from firestore_repo import FirestoreRepo

settings = get_settings()


def _seed_rules_fs(repo: FirestoreRepo) -> None:
    if repo.list_rules():
        return
    repo.seed_rules(
        [
            {
                "rule_type": "comm_allowlist",
                "pattern": comm,
                "classification": ProcessClass.SYSTEM.value,
                "enabled": True,
            }
            for comm in DEFAULT_SYSTEM_COMM
        ]
    )


def collect_host_firestore(repo: FirestoreRepo, host_id: str) -> dict | None:
    host = repo.get_host(host_id)
    if not host or not host.get("enabled", True):
        return None

    _seed_rules_fs(repo)
    key = decrypt_secret(host["encrypted_key"])
    ps_out, who_out = run_on_host(host["hostname"], host["port"], host["ssh_user"], key)
    processes_parsed = parse_ps(ps_out)
    sessions_parsed = parse_who(who_out)
    rules_raw = repo.list_rules()

    class _Rule:
        def __init__(self, d: dict):
            self.rule_type = d["rule_type"]
            self.pattern = d["pattern"]
            self.classification = ProcessClass(d["classification"])
            self.enabled = d.get("enabled", True)

    rules = [_Rule(r) for r in rules_raw]
    processes = []
    for proc in processes_parsed:
        cls = classify_process(proc, sessions_parsed, rules)
        processes.append(
            {
                "pid": proc.pid,
                "ppid": proc.ppid,
                "user": proc.user,
                "comm": proc.comm,
                "cmd": proc.cmd,
                "cpu_percent": proc.cpu_percent,
                "mem_percent": proc.mem_percent,
                "classification": cls.value,
            }
        )
    sessions = [
        {
            "user": s.user,
            "tty": s.tty,
            "login_at": s.login_at,
            "idle": s.idle,
            "from_ip": s.from_ip,
        }
        for s in sessions_parsed
    ]
    return repo.save_snapshot(
        host_id,
        datetime.now(UTC),
        PARSER_VERSION,
        processes,
        sessions,
    )


def build_rollup_firestore(repo: FirestoreRepo, host_id: str | None = None) -> int:
    from datetime import date

    today = datetime.now(UTC).date()
    hosts = [repo.get_host(host_id)] if host_id else [h for h in repo.list_hosts()]
    written = 0
    for host in hosts:
        if not host:
            continue
        snap = repo.latest_snapshot(host["id"])
        if not snap:
            continue
        hour = snap["collected_at"].hour if hasattr(snap["collected_at"], "hour") else 0
        by_user: dict[str, dict] = {}
        for p in snap.get("processes", []):
            if p.get("classification") != "user":
                continue
            u = p["user"]
            by_user.setdefault(u, {"count": 0, "comms": {}})
            by_user[u]["count"] += 1
            c = p["comm"]
            by_user[u]["comms"][c] = by_user[u]["comms"].get(c, 0) + 1
        for user, data in by_user.items():
            top = sorted(data["comms"].items(), key=lambda x: -x[1])[:5]
            summary = {"lines": [f"{c} ({n})" for c, n in top]}
            repo.upsert_rollup(host["id"], user, today, hour, data["count"], summary)
            written += 1
    return written

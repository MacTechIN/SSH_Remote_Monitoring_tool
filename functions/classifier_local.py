"""Classifier without SQLAlchemy (Firebase Functions)."""

from __future__ import annotations

import enum
from dataclasses import dataclass

from app.core.config import get_settings
from app.services.parser import ParsedProcess, ParsedSession

settings = get_settings()


class ProcessClass(str, enum.Enum):
    SYSTEM = "system"
    USER = "user"
    UNKNOWN = "unknown"


DEFAULT_SYSTEM_COMM = frozenset(
    {"systemd", "sshd", "cron", "rsyslogd", "dbus-daemon", "agetty", "udisksd", "polkitd"}
)


@dataclass
class Rule:
    rule_type: str
    pattern: str
    classification: ProcessClass
    enabled: bool = True


def classify_process(
    proc: ParsedProcess,
    sessions: list[ParsedSession],
    rules: list[Rule],
) -> ProcessClass:
    session_users = {s.user for s in sessions}
    for rule in rules:
        if not rule.enabled:
            continue
        if rule.rule_type == "comm_allowlist" and proc.comm == rule.pattern:
            return rule.classification
        if rule.rule_type == "user_allowlist" and proc.user == rule.pattern:
            return rule.classification

    if proc.comm in DEFAULT_SYSTEM_COMM or proc.user == "root":
        if proc.ppid == 1 or proc.comm in DEFAULT_SYSTEM_COMM:
            return ProcessClass.SYSTEM

    try:
        import pwd

        uid = pwd.getpwnam(proc.user).pw_uid
    except (KeyError, ImportError):
        uid = None

    if uid is not None and uid >= settings.min_user_uid:
        return ProcessClass.USER
    if proc.user in session_users and proc.user != "root":
        return ProcessClass.USER

    return ProcessClass.UNKNOWN

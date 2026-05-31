from __future__ import annotations

import json
import sqlite3
from datetime import UTC
from pathlib import Path

from backend.app.config import get_settings
from backend.app.models import HostMetrics

_SCHEMA = """
CREATE TABLE IF NOT EXISTS metric_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    host_id TEXT NOT NULL,
    checked_at TEXT NOT NULL,
    status TEXT NOT NULL,
    payload TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_metric_host_time
    ON metric_snapshots (host_id, checked_at DESC);
"""


def _db_path() -> Path:
    settings = get_settings()
    return settings.metrics_db_path


def init_db() -> None:
    path = _db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as conn:
        conn.executescript(_SCHEMA)


def record_metrics(metrics: list[HostMetrics]) -> None:
    settings = get_settings()
    if not settings.history_enabled or not metrics:
        return

    init_db()
    path = _db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = [
        (
            item.host_id,
            item.checked_at.astimezone(UTC).isoformat(),
            item.status.value,
            json.dumps(item.model_dump(mode="json")),
        )
        for item in metrics
    ]
    with sqlite3.connect(path) as conn:
        conn.executemany(
            """
            INSERT INTO metric_snapshots (host_id, checked_at, status, payload)
            VALUES (?, ?, ?, ?)
            """,
            rows,
        )


def get_history(host_id: str, limit: int = 50) -> list[HostMetrics]:
    limit = max(1, min(limit, 500))
    path = _db_path()
    if not path.is_file():
        return []

    with sqlite3.connect(path) as conn:
        cursor = conn.execute(
            """
            SELECT payload FROM metric_snapshots
            WHERE host_id = ?
            ORDER BY checked_at DESC
            LIMIT ?
            """,
            (host_id, limit),
        )
        rows = cursor.fetchall()

    return [HostMetrics.model_validate(json.loads(row[0])) for row in rows]

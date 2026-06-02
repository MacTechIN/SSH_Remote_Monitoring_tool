from __future__ import annotations

import json
import sqlite3
from datetime import UTC
from pathlib import Path

from backend.app.config import get_settings
from backend.app.models import HostMetrics, ProcessSnapshot

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
CREATE TABLE IF NOT EXISTS process_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    host_id TEXT NOT NULL,
    collected_at TEXT NOT NULL,
    status TEXT NOT NULL,
    payload TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_process_host_time
    ON process_snapshots (host_id, collected_at DESC);
"""


class FileHistoryRepository:
    def _db_path(self) -> Path:
        return get_settings().metrics_db_path

    def init(self) -> None:
        path = self._db_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(path) as conn:
            conn.executescript(_SCHEMA)

    def record_metrics(self, metrics: list[HostMetrics]) -> None:
        settings = get_settings()
        if not settings.history_enabled or not metrics:
            return
        self.init()
        rows = [
            (
                item.host_id,
                item.checked_at.astimezone(UTC).isoformat(),
                item.status.value,
                json.dumps(item.model_dump(mode="json")),
            )
            for item in metrics
        ]
        with sqlite3.connect(self._db_path()) as conn:
            conn.executemany(
                """
                INSERT INTO metric_snapshots (host_id, checked_at, status, payload)
                VALUES (?, ?, ?, ?)
                """,
                rows,
            )

    def get_history(self, host_id: str, limit: int = 50) -> list[HostMetrics]:
        limit = max(1, min(limit, 500))
        path = self._db_path()
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

    def record_process_snapshot(self, snapshot: ProcessSnapshot) -> None:
        settings = get_settings()
        if not settings.history_enabled:
            return
        self.init()
        row = (
            snapshot.host_id,
            snapshot.collected_at.astimezone(UTC).isoformat(),
            snapshot.status.value,
            json.dumps(snapshot.model_dump(mode="json")),
        )
        with sqlite3.connect(self._db_path()) as conn:
            conn.execute(
                """
                INSERT INTO process_snapshots (host_id, collected_at, status, payload)
                VALUES (?, ?, ?, ?)
                """,
                row,
            )

    def get_process_history(self, host_id: str, limit: int = 20) -> list[ProcessSnapshot]:
        limit = max(1, min(limit, 100))
        path = self._db_path()
        if not path.is_file():
            return []
        with sqlite3.connect(path) as conn:
            cursor = conn.execute(
                """
                SELECT payload FROM process_snapshots
                WHERE host_id = ?
                ORDER BY collected_at DESC
                LIMIT ?
                """,
                (host_id, limit),
            )
            rows = cursor.fetchall()
        return [ProcessSnapshot.model_validate(json.loads(row[0])) for row in rows]

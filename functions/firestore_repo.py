"""Firestore persistence for Firebase deployment (replaces PostgreSQL)."""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime
from typing import Any

from google.cloud import firestore

from firestore_client import get_db

HOSTS = "hosts"
SNAPSHOTS = "snapshots"
ROLLUPS = "daily_activity_rollups"
RULES = "classification_rules"


def _id() -> str:
    return str(uuid.uuid4())


class FirestoreRepo:
    def __init__(self) -> None:
        self.db = get_db()

    # --- hosts ---
    def list_hosts(self) -> list[dict[str, Any]]:
        return [doc.to_dict() | {"id": doc.id} for doc in self.db.collection(HOSTS).stream()]

    def get_host(self, host_id: str) -> dict[str, Any] | None:
        doc = self.db.collection(HOSTS).document(host_id).get()
        if not doc.exists:
            return None
        return doc.to_dict() | {"id": doc.id}

    def create_host(self, data: dict[str, Any]) -> dict[str, Any]:
        hid = _id()
        now = datetime.now(UTC)
        payload = {
            **data,
            "created_at": now,
            "updated_at": now,
        }
        self.db.collection(HOSTS).document(hid).set(payload)
        return payload | {"id": hid}

    def update_host(self, host_id: str, data: dict[str, Any]) -> dict[str, Any] | None:
        ref = self.db.collection(HOSTS).document(host_id)
        if not ref.get().exists:
            return None
        data["updated_at"] = datetime.now(UTC)
        ref.update(data)
        return self.get_host(host_id)

    def delete_host(self, host_id: str) -> bool:
        ref = self.db.collection(HOSTS).document(host_id)
        if not ref.get().exists:
            return False
        for snap in ref.collection(SNAPSHOTS).stream():
            snap.reference.delete()
        ref.delete()
        return True

    # --- snapshots ---
    def save_snapshot(
        self,
        host_id: str,
        collected_at: datetime,
        parser_version: str,
        processes: list[dict],
        sessions: list[dict],
    ) -> dict[str, Any]:
        sid = _id()
        payload = {
            "host_id": host_id,
            "collected_at": collected_at,
            "parser_version": parser_version,
            "processes": processes,
            "sessions": sessions,
        }
        self.db.collection(HOSTS).document(host_id).collection(SNAPSHOTS).document(sid).set(payload)
        self.db.collection(HOSTS).document(host_id).update({"latest_snapshot_id": sid})
        return payload | {"id": sid}

    def latest_snapshot(self, host_id: str) -> dict[str, Any] | None:
        snaps = (
            self.db.collection(HOSTS)
            .document(host_id)
            .collection(SNAPSHOTS)
            .order_by("collected_at", direction=firestore.Query.DESCENDING)
            .limit(1)
        )
        docs = list(snaps.stream())
        if not docs:
            return None
        d = docs[0]
        return d.to_dict() | {"id": d.id}

    def search_processes(
        self,
        *,
        user: str | None = None,
        q: str | None = None,
        host_id: str | None = None,
        from_dt: datetime | None = None,
        to_dt: datetime | None = None,
        limit: int = 100,
    ) -> list[dict]:
        hosts = [host_id] if host_id else [h["id"] for h in self.list_hosts()]
        results: list[dict] = []
        for hid in hosts:
            for doc in (
                self.db.collection(HOSTS)
                .document(hid)
                .collection(SNAPSHOTS)
                .order_by("collected_at", direction=firestore.Query.DESCENDING)
                .limit(50)
                .stream()
            ):
                snap = doc.to_dict() | {"id": doc.id}
                collected_at = snap.get("collected_at")
                if from_dt and collected_at and collected_at < from_dt:
                    continue
                if to_dt and collected_at and collected_at > to_dt:
                    continue
                for p in snap.get("processes", []):
                    if user and p.get("user") != user:
                        continue
                    if q and q.lower() not in (p.get("cmd") or "").lower():
                        continue
                    results.append(
                        {
                            "snapshot_id": snap["id"],
                            "host_id": hid,
                            "collected_at": collected_at,
                            **p,
                        }
                    )
                    if len(results) >= limit:
                        return results
        return results

    # --- rollups ---
    def upsert_rollup(
        self,
        host_id: str,
        user: str,
        day: date,
        hour: int,
        event_count: int,
        summary_json: dict,
    ) -> None:
        doc_id = f"{host_id}_{user}_{day.isoformat()}_{hour}"
        self.db.collection(ROLLUPS).document(doc_id).set(
            {
                "host_id": host_id,
                "user": user,
                "date": day.isoformat(),
                "hour": hour,
                "event_count": event_count,
                "summary_json": summary_json,
            },
            merge=True,
        )

    def calendar_cells(
        self, from_date: date, to_date: date, host_id: str | None = None
    ) -> list[dict]:
        q = self.db.collection(ROLLUPS)
        if host_id:
            q = q.where("host_id", "==", host_id)
        by_day: dict[str, int] = {}
        for doc in q.stream():
            d = doc.to_dict()
            day = d.get("date")
            if not day:
                continue
            if day < from_date.isoformat() or day > to_date.isoformat():
                continue
            by_day[day] = by_day.get(day, 0) + int(d.get("event_count", 0))

        max_c = max(by_day.values(), default=0)
        cells = []
        current = from_date
        while current <= to_date:
            c = by_day.get(current.isoformat(), 0)
            level = 0
            if c > 0 and max_c > 0:
                ratio = c / max_c
                if ratio < 0.25:
                    level = 1
                elif ratio < 0.5:
                    level = 2
                elif ratio < 0.75:
                    level = 3
                else:
                    level = 4
            cells.append({"date": current.isoformat(), "level": level, "count": c})
            current = date.fromordinal(current.toordinal() + 1)
        return cells

    def day_summary(self, day: date, host_id: str | None = None) -> list[dict]:
        q = self.db.collection(ROLLUPS).where("date", "==", day.isoformat())
        if host_id:
            q = q.where("host_id", "==", host_id)
        by_user: dict[str, list[str]] = {}
        for doc in q.stream():
            d = doc.to_dict()
            user = d.get("user", "")
            lines = (d.get("summary_json") or {}).get("lines", [])
            by_user.setdefault(user, []).extend(lines)
        return [
            {"user": u, "summary": ", ".join(parts[:5]) if parts else "no activity"}
            for u, parts in sorted(by_user.items())
        ]

    def list_rules(self) -> list[dict]:
        return [d.to_dict() | {"id": d.id} for d in self.db.collection(RULES).stream()]

    def seed_rules(self, rules: list[dict]) -> None:
        if list(self.db.collection(RULES).limit(1).stream()):
            return
        for r in rules:
            self.db.collection(RULES).document(_id()).set(r)

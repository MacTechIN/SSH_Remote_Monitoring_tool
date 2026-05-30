"""FastAPI application for Firebase Cloud Functions (Firestore backend)."""

from __future__ import annotations

from datetime import date, datetime

from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from config import apply_to_backend_settings, firebase_settings
from collector_firestore import build_rollup_firestore, collect_host_firestore
from firestore_repo import FirestoreRepo

apply_to_backend_settings()

import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.core.security import create_access_token, decrypt_secret, encrypt_secret, decode_access_token
from app.services.ssh import test_connection_sync

security = HTTPBearer(auto_error=False)
app = FastAPI(title="SSH Monitor API (Firebase)")
fs_settings = firebase_settings()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in fs_settings["cors_origins"].split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_repo() -> FirestoreRepo:
    return FirestoreRepo()


def get_user(creds: HTTPAuthorizationCredentials | None = Depends(security)) -> str:
    if not creds or not creds.credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")
    sub = decode_access_token(creds.credentials)
    if not sub:
        raise HTTPException(status_code=401, detail="Invalid token")
    return sub


class LoginRequest(BaseModel):
    username: str
    password: str


class HostCreate(BaseModel):
    name: str
    hostname: str
    port: int = 22
    ssh_user: str
    private_key: str
    poll_interval_sec: int = 60
    enabled: bool = True


class HostUpdate(BaseModel):
    name: str | None = None
    hostname: str | None = None
    port: int | None = None
    ssh_user: str | None = None
    private_key: str | None = None
    poll_interval_sec: int | None = None
    enabled: bool | None = None


@app.get("/api/v1/health")
def health():
    return {"status": "ok", "platform": "firebase"}


@app.post("/api/v1/auth/login")
def login(body: LoginRequest):
    if body.username != fs_settings["admin_username"] or body.password != fs_settings["admin_password"]:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {"access_token": create_access_token(body.username), "token_type": "bearer"}


@app.get("/api/v1/hosts")
def list_hosts(repo: FirestoreRepo = Depends(get_repo), _: str = Depends(get_user)):
    return [_serialize_host(h) for h in repo.list_hosts()]


@app.post("/api/v1/hosts", status_code=201)
def create_host(body: HostCreate, repo: FirestoreRepo = Depends(get_repo), _: str = Depends(get_user)):
    h = repo.create_host(
        {
            "name": body.name,
            "hostname": body.hostname,
            "port": body.port,
            "ssh_user": body.ssh_user,
            "encrypted_key": encrypt_secret(body.private_key),
            "poll_interval_sec": body.poll_interval_sec,
            "enabled": body.enabled,
        }
    )
    return _serialize_host(h)


@app.get("/api/v1/hosts/{host_id}")
def get_host(host_id: str, repo: FirestoreRepo = Depends(get_repo), _: str = Depends(get_user)):
    h = repo.get_host(host_id)
    if not h:
        raise HTTPException(status_code=404, detail="Not found")
    return _serialize_host(h)


@app.patch("/api/v1/hosts/{host_id}")
def update_host(
    host_id: str, body: HostUpdate, repo: FirestoreRepo = Depends(get_repo), _: str = Depends(get_user)
):
    data = body.model_dump(exclude_unset=True)
    if "private_key" in data:
        data["encrypted_key"] = encrypt_secret(data.pop("private_key"))
    h = repo.update_host(host_id, data)
    if not h:
        raise HTTPException(status_code=404, detail="Not found")
    return _serialize_host(h)


@app.delete("/api/v1/hosts/{host_id}", status_code=204)
def delete_host(host_id: str, repo: FirestoreRepo = Depends(get_repo), _: str = Depends(get_user)):
    if not repo.delete_host(host_id):
        raise HTTPException(status_code=404, detail="Not found")


@app.post("/api/v1/hosts/{host_id}/test-connection")
def test_connection(host_id: str, repo: FirestoreRepo = Depends(get_repo), _: str = Depends(get_user)):
    h = repo.get_host(host_id)
    if not h:
        raise HTTPException(status_code=404, detail="Not found")
    key = decrypt_secret(h["encrypted_key"])
    ok = test_connection_sync(h["hostname"], h["port"], h["ssh_user"], key)
    return {"ok": ok}


@app.post("/api/v1/hosts/{host_id}/collect")
def collect_now(host_id: str, repo: FirestoreRepo = Depends(get_repo), _: str = Depends(get_user)):
    snap = collect_host_firestore(repo, host_id)
    if not snap:
        raise HTTPException(status_code=400, detail="Collection failed")
    build_rollup_firestore(repo, host_id)
    return {"ok": True, "snapshot_id": snap["id"]}


@app.get("/api/v1/hosts/{host_id}/live")
def live(host_id: str, repo: FirestoreRepo = Depends(get_repo), _: str = Depends(get_user)):
    snap = repo.latest_snapshot(host_id)
    if not snap:
        raise HTTPException(status_code=404, detail="No snapshot")
    return {
        "snapshot_id": snap["id"],
        "host_id": host_id,
        "collected_at": snap["collected_at"],
        "processes": snap.get("processes", []),
        "sessions": snap.get("sessions", []),
    }


@app.get("/api/v1/activity/calendar")
def calendar(
    from_date: date = Query(..., alias="from"),
    to_date: date = Query(..., alias="to"),
    host_id: str | None = None,
    granularity: str = "day",
    repo: FirestoreRepo = Depends(get_repo),
    _: str = Depends(get_user),
):
    cells = repo.calendar_cells(from_date, to_date, host_id)
    return {"granularity": granularity, "cells": cells}


@app.get("/api/v1/activity/day-summary")
def day_summary(
    date_param: date = Query(..., alias="date"),
    host_id: str | None = None,
    repo: FirestoreRepo = Depends(get_repo),
    _: str = Depends(get_user),
):
    lines = repo.day_summary(date_param, host_id)
    return {"date": date_param.isoformat(), "host_id": host_id, "lines": lines}


@app.get("/api/v1/search/processes")
def search_processes(
    user: str | None = None,
    q: str | None = None,
    from_dt: datetime | None = Query(None, alias="from"),
    to_dt: datetime | None = Query(None, alias="to"),
    host_id: str | None = None,
    limit: int = Query(100, le=500),
    repo: FirestoreRepo = Depends(get_repo),
    _: str = Depends(get_user),
):
    items = repo.search_processes(user=user, q=q, host_id=host_id, from_dt=from_dt, to_dt=to_dt, limit=limit)
    return {"total": len(items), "items": items}


def _serialize_host(h: dict) -> dict:
    return {
        "id": h["id"],
        "name": h["name"],
        "hostname": h["hostname"],
        "port": h.get("port", 22),
        "ssh_user": h["ssh_user"],
        "poll_interval_sec": h.get("poll_interval_sec", 60),
        "enabled": h.get("enabled", True),
        "created_at": h.get("created_at"),
        "updated_at": h.get("updated_at"),
    }

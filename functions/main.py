"""
Firebase Cloud Functions entry points.

- api: FastAPI (Firestore) via Mangum ASGI adapter
- scheduled_poll: replaces Celery Beat + worker for enabled hosts
"""

from __future__ import annotations

import json

import httpx
from firebase_admin import initialize_app
from firebase_functions import https_fn, options, scheduler_fn

from api_app import app as fastapi_app
from collector_firestore import build_rollup_firestore, collect_host_firestore
from config import apply_to_backend_settings
from firestore_repo import FirestoreRepo

initialize_app()
apply_to_backend_settings()

_asgi_transport = httpx.ASGITransport(app=fastapi_app)

CORS = options.CorsOptions(
    cors_origins="*",
    cors_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
)


@https_fn.on_request(
    cors=CORS,
    memory=options.MemoryOption.MB_1024,
    timeout_sec=300,
    max_instances=10,
    secrets=["ENCRYPTION_KEY", "JWT_SECRET", "ADMIN_USERNAME", "ADMIN_PASSWORD"],
)
def api(req: https_fn.Request) -> https_fn.Response:
    """HTTP API — same routes as Docker FastAPI (/api/v1/...)."""
    path = req.path
    if req.query_string:
        path = f"{path}?{req.query_string}"
    url = f"http://firebase{path}"

    with httpx.Client(transport=_asgi_transport, base_url="http://firebase") as client:
        upstream = client.build_request(
            method=req.method,
            url=url,
            headers={k: v for k, v in req.headers.items() if k.lower() != "host"},
            content=req.get_data(),
        )
        response = client.send(upstream)

    return https_fn.Response(
        response.content,
        status=response.status_code,
        headers=dict(response.headers),
    )


@scheduler_fn.on_schedule(
    schedule="every 1 minutes",
    memory=options.MemoryOption.MB_1024,
    timeout_sec=300,
    secrets=["ENCRYPTION_KEY", "JWT_SECRET"],
)
def scheduled_poll(event: scheduler_fn.ScheduledEvent) -> None:
    """Poll all enabled hosts (Celery Beat replacement)."""
    repo = FirestoreRepo()
    hosts = [h for h in repo.list_hosts() if h.get("enabled", True)]
    results = []
    for host in hosts:
        try:
            snap = collect_host_firestore(repo, host["id"])
            if snap:
                build_rollup_firestore(repo, host["id"])
                results.append({"host_id": host["id"], "ok": True})
        except Exception as e:
            results.append({"host_id": host["id"], "ok": False, "error": str(e)})
    print(json.dumps({"polled": len(hosts), "results": results}))

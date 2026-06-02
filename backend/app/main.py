from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from backend.app.config import get_settings, load_hosts
from backend.app.firebase_auth import verify_firebase_token
from backend.app.history import (
    get_history,
    get_process_history,
    init_db,
    record_metrics,
    record_process_snapshot,
)
from backend.app.host_store import (
    add_host,
    delete_host,
    get_host,
    slugify_id,
    unique_host_id,
    update_host,
)
from backend.app.models import (
    HostConfig,
    HostCreateRequest,
    HostMetrics,
    HostSummary,
    HostUpdateRequest,
    ProcessSnapshot,
)
from backend.app.ssh_monitor import collect_all_metrics, collect_host_metrics, collect_host_processes

STATIC_DIR = Path(__file__).resolve().parent / "static"


@asynccontextmanager
async def lifespan(_app: FastAPI):
    if get_settings().storage_backend == "file":
        init_db()
    yield


app = FastAPI(
    title="SSH Remote Monitoring",
    description="Monitor Linux servers over SSH",
    version="0.3.0",
    lifespan=lifespan,
)

settings = get_settings()
origins = [item.strip() for item in settings.cors_origins.split(",") if item.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if STATIC_DIR.is_dir():
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


def _to_summary(host: HostConfig) -> HostSummary:
    return HostSummary(
        id=host.id,
        name=host.name,
        hostname=host.hostname,
        port=host.port,
        username=host.username,
    )


def _collect_and_record(host: HostConfig | None = None) -> list[HostMetrics]:
    metrics = [collect_host_metrics(host)] if host else collect_all_metrics()
    record_metrics(metrics)
    return metrics


def _collect_and_record_processes(host: HostConfig) -> ProcessSnapshot:
    snapshot = collect_host_processes(host)
    record_process_snapshot(snapshot)
    return snapshot


@app.get("/api/health")
def health() -> dict[str, str]:
    settings = get_settings()
    return {
        "status": "ok",
        "storage_backend": settings.storage_backend,
        "demo_mode": str(settings.demo_mode).lower(),
        "history_enabled": str(settings.history_enabled).lower(),
        "firebase_auth_required": str(settings.firebase_auth_required).lower(),
    }


@app.get("/api/hosts", response_model=list[HostSummary])
def list_hosts(_user: dict | None = Depends(verify_firebase_token)) -> list[HostSummary]:
    return [_to_summary(host) for host in load_hosts()]


@app.post("/api/hosts", response_model=HostSummary, status_code=201)
def create_host(
    body: HostCreateRequest,
    _user: dict | None = Depends(verify_firebase_token),
) -> HostSummary:
    hosts = load_hosts()
    base_id = body.id or slugify_id(body.name)
    host_id = unique_host_id(base_id, hosts)
    host = HostConfig(
        id=host_id,
        name=body.name,
        hostname=body.hostname,
        port=body.port,
        username=body.username,
        private_key_path=body.private_key_path,
    )
    try:
        created = add_host(host)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _to_summary(created)


@app.put("/api/hosts/{host_id}", response_model=HostSummary)
def replace_host(
    host_id: str,
    body: HostUpdateRequest,
    _user: dict | None = Depends(verify_firebase_token),
) -> HostSummary:
    updates = body.model_dump(exclude_none=True)
    if not updates:
        host = get_host(host_id)
        if host is None:
            raise HTTPException(status_code=404, detail=f"Host '{host_id}' not found")
        return _to_summary(host)
    try:
        updated = update_host(host_id, updates)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _to_summary(updated)


@app.delete("/api/hosts/{host_id}", status_code=204)
def remove_host(host_id: str, _user: dict | None = Depends(verify_firebase_token)) -> None:
    try:
        delete_host(host_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/api/metrics", response_model=list[HostMetrics])
def all_metrics(_user: dict | None = Depends(verify_firebase_token)) -> list[HostMetrics]:
    return _collect_and_record()


@app.get("/api/hosts/{host_id}/metrics", response_model=HostMetrics)
def host_metrics(
    host_id: str,
    _user: dict | None = Depends(verify_firebase_token),
) -> HostMetrics:
    host = get_host(host_id)
    if host is None:
        raise HTTPException(status_code=404, detail=f"Host '{host_id}' not found")
    return _collect_and_record(host)[0]


@app.get("/api/hosts/{host_id}/history", response_model=list[HostMetrics])
def host_history(
    host_id: str,
    limit: int = Query(default=50, ge=1, le=500),
    _user: dict | None = Depends(verify_firebase_token),
) -> list[HostMetrics]:
    if get_host(host_id) is None:
        raise HTTPException(status_code=404, detail=f"Host '{host_id}' not found")
    return get_history(host_id, limit=limit)



@app.get("/api/hosts/{host_id}/processes", response_model=ProcessSnapshot)
def host_processes(
    host_id: str,
    _user: dict | None = Depends(verify_firebase_token),
) -> ProcessSnapshot:
    host = get_host(host_id)
    if host is None:
        raise HTTPException(status_code=404, detail=f"Host '{host_id}' not found")
    return _collect_and_record_processes(host)


@app.get("/api/hosts/{host_id}/process-history", response_model=list[ProcessSnapshot])
def host_process_history(
    host_id: str,
    limit: int = Query(default=10, ge=1, le=100),
    _user: dict | None = Depends(verify_firebase_token),
) -> list[ProcessSnapshot]:
    if get_host(host_id) is None:
        raise HTTPException(status_code=404, detail=f"Host '{host_id}' not found")
    return get_process_history(host_id, limit=limit)


@app.get("/firebase-config.js")
def firebase_config() -> FileResponse:
    path = STATIC_DIR / "firebase-config.js"
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Firebase config not found")
    return FileResponse(path, media_type="application/javascript")

@app.get("/")
def index() -> FileResponse:
    index_path = STATIC_DIR / "index.html"
    if not index_path.is_file():
        raise HTTPException(status_code=404, detail="Dashboard not found")
    return FileResponse(index_path)

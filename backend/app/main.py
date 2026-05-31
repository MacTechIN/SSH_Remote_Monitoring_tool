from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from backend.app.config import get_settings, load_hosts
from backend.app.history import get_history, init_db, record_metrics
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
)
from backend.app.ssh_monitor import collect_all_metrics, collect_host_metrics

STATIC_DIR = Path(__file__).resolve().parent / "static"


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="SSH Remote Monitoring",
    description="Monitor Linux servers over SSH",
    version="0.2.0",
    lifespan=lifespan,
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


@app.get("/api/health")
def health() -> dict[str, str]:
    settings = get_settings()
    return {
        "status": "ok",
        "demo_mode": str(settings.demo_mode).lower(),
        "history_enabled": str(settings.history_enabled).lower(),
    }


@app.get("/api/hosts", response_model=list[HostSummary])
def list_hosts() -> list[HostSummary]:
    return [_to_summary(host) for host in load_hosts()]


@app.post("/api/hosts", response_model=HostSummary, status_code=201)
def create_host(body: HostCreateRequest) -> HostSummary:
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
def replace_host(host_id: str, body: HostUpdateRequest) -> HostSummary:
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
def remove_host(host_id: str) -> None:
    try:
        delete_host(host_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/api/metrics", response_model=list[HostMetrics])
def all_metrics() -> list[HostMetrics]:
    return _collect_and_record()


@app.get("/api/hosts/{host_id}/metrics", response_model=HostMetrics)
def host_metrics(host_id: str) -> HostMetrics:
    host = get_host(host_id)
    if host is None:
        raise HTTPException(status_code=404, detail=f"Host '{host_id}' not found")
    return _collect_and_record(host)[0]


@app.get("/api/hosts/{host_id}/history", response_model=list[HostMetrics])
def host_history(
    host_id: str,
    limit: int = Query(default=50, ge=1, le=500),
) -> list[HostMetrics]:
    if get_host(host_id) is None:
        raise HTTPException(status_code=404, detail=f"Host '{host_id}' not found")
    return get_history(host_id, limit=limit)


@app.get("/")
def index() -> FileResponse:
    index_path = STATIC_DIR / "index.html"
    if not index_path.is_file():
        raise HTTPException(status_code=404, detail="Dashboard not found")
    return FileResponse(index_path)

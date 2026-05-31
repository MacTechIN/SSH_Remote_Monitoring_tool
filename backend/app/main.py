from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from backend.app.config import get_settings, load_hosts
from backend.app.models import HostMetrics, HostSummary
from backend.app.ssh_monitor import collect_all_metrics, collect_host_metrics

STATIC_DIR = Path(__file__).resolve().parent / "static"

app = FastAPI(
    title="SSH Remote Monitoring",
    description="Monitor Linux servers over SSH",
    version="0.1.0",
)

if STATIC_DIR.is_dir():
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/api/health")
def health() -> dict[str, str]:
    settings = get_settings()
    return {
        "status": "ok",
        "demo_mode": str(settings.demo_mode).lower(),
    }


@app.get("/api/hosts", response_model=list[HostSummary])
def list_hosts() -> list[HostSummary]:
    return [
        HostSummary(
            id=host.id,
            name=host.name,
            hostname=host.hostname,
            port=host.port,
            username=host.username,
        )
        for host in load_hosts()
    ]


@app.get("/api/metrics", response_model=list[HostMetrics])
def all_metrics() -> list[HostMetrics]:
    return collect_all_metrics()


@app.get("/api/hosts/{host_id}/metrics", response_model=HostMetrics)
def host_metrics(host_id: str) -> HostMetrics:
    for host in load_hosts():
        if host.id == host_id:
            return collect_host_metrics(host)
    raise HTTPException(status_code=404, detail=f"Host '{host_id}' not found")


@app.get("/")
def index() -> FileResponse:
    index_path = STATIC_DIR / "index.html"
    if not index_path.is_file():
        raise HTTPException(status_code=404, detail="Dashboard not found")
    return FileResponse(index_path)

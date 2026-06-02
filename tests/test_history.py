from pathlib import Path

import pytest
import yaml
from fastapi.testclient import TestClient

from backend.app.config import get_settings
from backend.app.main import app


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    hosts_file = tmp_path / "hosts.yaml"
    db_file = tmp_path / "metrics.db"
    hosts_file.write_text(
        yaml.dump(
            {
                "hosts": [
                    {
                        "id": "demo",
                        "name": "Demo",
                        "hostname": "127.0.0.1",
                        "port": 22,
                        "username": "ubuntu",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("HOSTS_FILE", str(hosts_file))
    monkeypatch.setenv("METRICS_DB_PATH", str(db_file))
    monkeypatch.setenv("DEMO_MODE", "true")
    get_settings.cache_clear()
    with TestClient(app) as client:
        yield client
    get_settings.cache_clear()


def test_metrics_record_history(client: TestClient):
    client.get("/api/metrics")
    history = client.get("/api/hosts/demo/history").json()
    assert len(history) >= 1
    assert history[0]["host_id"] == "demo"


def test_process_analysis_record_history(client: TestClient):
    response = client.get("/api/hosts/demo/processes")
    assert response.status_code == 200
    snapshot = response.json()
    assert snapshot["summary"]["user"] >= 1

    history = client.get("/api/hosts/demo/process-history").json()
    assert len(history) >= 1
    assert history[0]["host_id"] == "demo"
    assert history[0]["summary"]["user"] >= 1

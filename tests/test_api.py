from pathlib import Path

import pytest
import yaml
from fastapi.testclient import TestClient

from backend.app.config import get_settings
from backend.app.main import app


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    hosts_file = tmp_path / "hosts.yaml"
    hosts_file.write_text(
        yaml.dump(
            {
                "hosts": [
                    {
                        "id": "demo",
                        "name": "Demo Host",
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
    monkeypatch.setenv("DEMO_MODE", "true")
    get_settings.cache_clear()
    yield TestClient(app)
    get_settings.cache_clear()


def test_health(client: TestClient):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_hosts_and_metrics(client: TestClient):
    hosts = client.get("/api/hosts").json()
    assert len(hosts) == 1
    assert hosts[0]["id"] == "demo"

    metrics = client.get("/api/metrics").json()
    assert len(metrics) == 1
    assert metrics[0]["status"] == "online"
    assert metrics[0]["memory"]["total_mb"] == 4096


def test_dashboard(client: TestClient):
    response = client.get("/")
    assert response.status_code == 200
    assert "SSH Remote Monitoring" in response.text

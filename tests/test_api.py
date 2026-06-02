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
    with TestClient(app) as client:
        yield client
    get_settings.cache_clear()


def test_health(client):
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


def test_host_process_analysis(client: TestClient):
    snapshot = client.get("/api/hosts/demo/processes")
    assert snapshot.status_code == 200
    body = snapshot.json()
    assert body["status"] == "online"
    assert body["summary"]["user"] >= 1
    assert body["summary"]["system"] >= 1
    assert any(process["category"] == "user" for process in body["processes"])

    history = client.get("/api/hosts/demo/process-history")
    assert history.status_code == 200
    assert history.json()[0]["summary"]["user"] >= 1


def test_dashboard(client: TestClient):
    response = client.get("/")
    assert response.status_code == 200
    assert "SSH Remote Monitoring" in response.text


def test_host_crud(client: TestClient):
    created = client.post(
        "/api/hosts",
        json={
            "name": "New Host",
            "hostname": "10.0.0.5",
            "port": 2222,
            "username": "deploy",
        },
    )
    assert created.status_code == 201
    host_id = created.json()["id"]
    assert host_id == "new-host"

    updated = client.put(f"/api/hosts/{host_id}", json={"name": "Renamed"}).json()
    assert updated["name"] == "Renamed"

    listed = client.get("/api/hosts").json()
    assert any(item["id"] == host_id for item in listed)

    deleted = client.delete(f"/api/hosts/{host_id}")
    assert deleted.status_code == 204

from pathlib import Path

import pytest
import yaml

from backend.app.config import get_settings
from backend.app.host_store import (
    add_host,
    delete_host,
    load_hosts,
    slugify_id,
    unique_host_id,
    update_host,
)
from backend.app.models import HostConfig


@pytest.fixture(autouse=True)
def hosts_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    path = tmp_path / "hosts.yaml"
    monkeypatch.setenv("HOSTS_FILE", str(path))
    get_settings.cache_clear()
    yield path
    get_settings.cache_clear()


def test_slugify_and_unique_id():
    assert slugify_id("My Server 01") == "my-server-01"
    hosts = [HostConfig(id="web", name="Web", hostname="1.1.1.1", username="root")]
    assert unique_host_id("web", hosts) == "web-2"


def test_add_update_delete(hosts_file: Path):
    host = HostConfig(id="srv", name="Srv", hostname="10.0.0.2", username="ubuntu")
    add_host(host)
    assert len(load_hosts()) == 1

    update_host("srv", {"name": "Updated"})
    saved = yaml.safe_load(hosts_file.read_text(encoding="utf-8"))
    assert saved["hosts"][0]["name"] == "Updated"

    delete_host("srv")
    assert load_hosts() == []

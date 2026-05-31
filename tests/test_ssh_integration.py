import os
import socket
from pathlib import Path

import pytest

from backend.app.config import get_settings
from backend.app.models import HostConfig
from backend.app.ssh_monitor import collect_host_metrics


def _port_open(port: int = 22) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(1)
        return sock.connect_ex(("127.0.0.1", port)) == 0


@pytest.mark.integration
def test_real_ssh_metrics(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    if os.getenv("RUN_SSH_INTEGRATION") != "1":
        pytest.skip("Set RUN_SSH_INTEGRATION=1 after scripts/setup-local-ssh.sh")
    if not _port_open():
        pytest.skip("SSH port 22 is not available")

    monkeypatch.delenv("DEMO_MODE", raising=False)
    get_settings.cache_clear()

    host = HostConfig(
        id="local",
        name="Local",
        hostname="127.0.0.1",
        port=22,
        username=os.getenv("USER", "ubuntu"),
        private_key_path=str(Path.home() / ".ssh" / "id_ed25519"),
    )
    metrics = collect_host_metrics(host)

    assert metrics.status.value == "online", metrics.error
    assert metrics.memory is not None
    assert metrics.disk is not None

from backend.app.models import HostConfig
from backend.app.ssh_monitor import demo_metrics, parse_metrics_output


def test_parse_metrics_output():
    sample = """
UPTIME:up 2 days, 4 hours
LOAD:0.42 0.38 0.35
MEM:8192 4096 3800
DISK:100000000000 45000000000 50000000000 /
""".strip()

    metrics = parse_metrics_output(sample, "test-host")

    assert metrics.host_id == "test-host"
    assert metrics.status.value == "online"
    assert metrics.uptime == "up 2 days, 4 hours"
    assert metrics.load_1 == 0.42
    assert metrics.memory is not None
    assert metrics.memory.total_mb == 8192
    assert metrics.disk is not None
    assert metrics.disk.used_percent == 45.0


def test_demo_metrics_stable():
    host = HostConfig(
        id="demo-1",
        name="Demo",
        hostname="127.0.0.1",
        username="ubuntu",
    )
    first = demo_metrics(host)
    second = demo_metrics(host)
    assert first.host_id == second.host_id
    assert first.memory.used_mb == second.memory.used_mb

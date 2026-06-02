from backend.app.models import HostConfig
from backend.app.ssh_monitor import demo_metrics, demo_processes, parse_metrics_output, parse_process_output


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


def test_parse_process_output_classifies_system_and_user_processes():
    sample = """
PROC:1\t0\troot\tsystemd\t0.0\t0.1\t12-03:10:00\t/sbin/init
PROC:42\t2\troot\tkworker\t0.0\t0.0\t12-03:09:58\t[kworker/0:1]
PROC:1204\t1\tubuntu\tpython\t4.5\t3.1\t01:14:22\t/home/ubuntu/app/worker.py
PROC:1301\t1\tdeploy\tjava\t9.9\t18.4\t03:44:11\t/srv/batch/bin/java -jar batch.jar
""".strip()

    snapshot = parse_process_output(sample, "test-host")

    assert snapshot.host_id == "test-host"
    assert snapshot.status.value == "online"
    assert snapshot.summary.total == 4
    assert snapshot.summary.system == 2
    assert snapshot.summary.user == 2
    assert [process.pid for process in snapshot.processes if process.category == "user"] == [
        1204,
        1301,
    ]


def test_demo_processes_stable():
    host = HostConfig(
        id="demo-1",
        name="Demo",
        hostname="127.0.0.1",
        username="ubuntu",
    )

    snapshot = demo_processes(host)

    assert snapshot.summary.user >= 1
    assert snapshot.summary.system >= 1
    assert any(process.category == "user" for process in snapshot.processes)

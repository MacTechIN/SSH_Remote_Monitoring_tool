from pathlib import Path

from app.services.parser import parse_ps, parse_who

FIXTURES = Path(__file__).parent / "fixtures"


def test_parse_ps_ubuntu_sample():
    text = (FIXTURES / "ps_ubuntu_sample.txt").read_text()
    procs = parse_ps(text)
    assert len(procs) >= 3
    bash = next(p for p in procs if p.comm == "bash")
    assert bash.user == "alice"
    assert bash.pid == 5678


def test_parse_who_empty():
    assert parse_who("") == []

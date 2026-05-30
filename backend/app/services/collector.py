from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.core.security import decrypt_secret
from app.models.entities import Host, ProcessRecord, ProcessSnapshot, UserSession
from app.services.classifier import classify_process, seed_default_rules
from app.services.parser import PARSER_VERSION, parse_ps, parse_who
from app.services.ssh import run_on_host


def collect_host(db: Session, host_id: str) -> ProcessSnapshot | None:
    host = db.query(Host).filter(Host.id == host_id, Host.enabled.is_(True)).first()
    if not host:
        return None

    seed_default_rules(db)
    private_key = decrypt_secret(host.encrypted_key)
    ps_out, who_out = run_on_host(host.hostname, host.port, host.ssh_user, private_key)

    processes = parse_ps(ps_out)
    sessions = parse_who(who_out)
    from app.models.entities import ClassificationRule

    rules = db.query(ClassificationRule).filter(ClassificationRule.enabled.is_(True)).all()

    snapshot = ProcessSnapshot(
        host_id=host.id,
        collected_at=datetime.now(UTC),
        parser_version=PARSER_VERSION,
    )
    db.add(snapshot)
    db.flush()

    for proc in processes:
        classification = classify_process(proc, sessions, rules)
        db.add(
            ProcessRecord(
                snapshot_id=snapshot.id,
                pid=proc.pid,
                ppid=proc.ppid,
                user=proc.user,
                comm=proc.comm,
                cmd=proc.cmd,
                cpu_percent=proc.cpu_percent,
                mem_percent=proc.mem_percent,
                classification=classification,
            )
        )

    for sess in sessions:
        db.add(
            UserSession(
                snapshot_id=snapshot.id,
                user=sess.user,
                tty=sess.tty,
                login_at=sess.login_at,
                idle=sess.idle,
                from_ip=sess.from_ip,
            )
        )

    db.commit()
    db.refresh(snapshot)
    return snapshot

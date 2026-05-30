import enum
import uuid
from datetime import date, datetime

from sqlalchemy import JSON, Boolean, Date, DateTime, Enum, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class ProcessClass(str, enum.Enum):
    SYSTEM = "system"
    USER = "user"
    UNKNOWN = "unknown"


class Host(Base):
    __tablename__ = "hosts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    hostname: Mapped[str] = mapped_column(String(255), nullable=False)
    port: Mapped[int] = mapped_column(Integer, default=22)
    ssh_user: Mapped[str] = mapped_column(String(128), nullable=False)
    encrypted_key: Mapped[str] = mapped_column(Text, nullable=False)
    poll_interval_sec: Mapped[int] = mapped_column(Integer, default=60)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )

    snapshots: Mapped[list["ProcessSnapshot"]] = relationship(back_populates="host")


class ProcessSnapshot(Base):
    __tablename__ = "process_snapshots"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    host_id: Mapped[str] = mapped_column(String(36), ForeignKey("hosts.id", ondelete="CASCADE"), index=True)
    collected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    parser_version: Mapped[str] = mapped_column(String(32), default="1")

    host: Mapped["Host"] = relationship(back_populates="snapshots")
    processes: Mapped[list["ProcessRecord"]] = relationship(back_populates="snapshot", cascade="all, delete-orphan")
    sessions: Mapped[list["UserSession"]] = relationship(back_populates="snapshot", cascade="all, delete-orphan")


class ProcessRecord(Base):
    __tablename__ = "process_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    snapshot_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("process_snapshots.id", ondelete="CASCADE"), index=True
    )
    pid: Mapped[int] = mapped_column(Integer)
    ppid: Mapped[int] = mapped_column(Integer)
    user: Mapped[str] = mapped_column(String(128))
    comm: Mapped[str] = mapped_column(String(255))
    cmd: Mapped[str] = mapped_column(Text)
    cpu_percent: Mapped[float | None] = mapped_column(Float, nullable=True)
    mem_percent: Mapped[float | None] = mapped_column(Float, nullable=True)
    classification: Mapped[ProcessClass] = mapped_column(Enum(ProcessClass), default=ProcessClass.UNKNOWN)

    snapshot: Mapped["ProcessSnapshot"] = relationship(back_populates="processes")


class UserSession(Base):
    __tablename__ = "user_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    snapshot_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("process_snapshots.id", ondelete="CASCADE"), index=True
    )
    user: Mapped[str] = mapped_column(String(128))
    tty: Mapped[str | None] = mapped_column(String(64), nullable=True)
    login_at: Mapped[str | None] = mapped_column(String(64), nullable=True)
    idle: Mapped[str | None] = mapped_column(String(64), nullable=True)
    from_ip: Mapped[str | None] = mapped_column(String(64), nullable=True)

    snapshot: Mapped["ProcessSnapshot"] = relationship(back_populates="sessions")


class DailyActivityRollup(Base):
    __tablename__ = "daily_activity_rollups"
    __table_args__ = (UniqueConstraint("host_id", "user", "date", "hour", name="uq_rollup_host_user_date_hour"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    host_id: Mapped[str] = mapped_column(String(36), ForeignKey("hosts.id", ondelete="CASCADE"), index=True)
    user: Mapped[str] = mapped_column(String(128))
    date: Mapped[date] = mapped_column(Date, index=True)
    hour: Mapped[int] = mapped_column(Integer)
    event_count: Mapped[int] = mapped_column(Integer, default=0)
    summary_json: Mapped[dict] = mapped_column(JSON, default=dict)


class ClassificationRule(Base):
    __tablename__ = "classification_rules"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    rule_type: Mapped[str] = mapped_column(String(32))
    pattern: Mapped[str] = mapped_column(String(255))
    classification: Mapped[ProcessClass] = mapped_column(Enum(ProcessClass))
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    actor: Mapped[str] = mapped_column(String(128))
    action: Mapped[str] = mapped_column(String(64))
    target: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

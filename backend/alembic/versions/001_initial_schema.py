"""initial schema

Revision ID: 001
Revises:
Create Date: 2026-05-30

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "hosts",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("hostname", sa.String(255), nullable=False),
        sa.Column("port", sa.Integer(), server_default="22"),
        sa.Column("ssh_user", sa.String(128), nullable=False),
        sa.Column("encrypted_key", sa.Text(), nullable=False),
        sa.Column("poll_interval_sec", sa.Integer(), server_default="60"),
        sa.Column("enabled", sa.Boolean(), server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True)),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
    )
    op.create_table(
        "process_snapshots",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("host_id", sa.String(36), sa.ForeignKey("hosts.id", ondelete="CASCADE")),
        sa.Column("collected_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("parser_version", sa.String(32)),
    )
    op.create_index("ix_snapshots_host_collected", "process_snapshots", ["host_id", "collected_at"])

    op.create_table(
        "process_records",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("snapshot_id", sa.String(36), sa.ForeignKey("process_snapshots.id", ondelete="CASCADE")),
        sa.Column("pid", sa.Integer()),
        sa.Column("ppid", sa.Integer()),
        sa.Column("user", sa.String(128)),
        sa.Column("comm", sa.String(255)),
        sa.Column("cmd", sa.Text()),
        sa.Column("cpu_percent", sa.Float()),
        sa.Column("mem_percent", sa.Float()),
        sa.Column("classification", sa.Enum("system", "user", "unknown", name="processclass")),
    )
    op.create_table(
        "user_sessions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("snapshot_id", sa.String(36), sa.ForeignKey("process_snapshots.id", ondelete="CASCADE")),
        sa.Column("user", sa.String(128)),
        sa.Column("tty", sa.String(64)),
        sa.Column("login_at", sa.String(64)),
        sa.Column("idle", sa.String(64)),
        sa.Column("from_ip", sa.String(64)),
    )
    op.create_table(
        "daily_activity_rollups",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("host_id", sa.String(36), sa.ForeignKey("hosts.id", ondelete="CASCADE")),
        sa.Column("user", sa.String(128)),
        sa.Column("date", sa.Date()),
        sa.Column("hour", sa.Integer()),
        sa.Column("event_count", sa.Integer()),
        sa.Column("summary_json", sa.JSON()),
        sa.UniqueConstraint("host_id", "user", "date", "hour", name="uq_rollup_host_user_date_hour"),
    )
    op.create_table(
        "classification_rules",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("rule_type", sa.String(32)),
        sa.Column("pattern", sa.String(255)),
        sa.Column("classification", sa.Enum("system", "user", "unknown", name="processclass")),
        sa.Column("enabled", sa.Boolean(), server_default="true"),
    )
    op.create_table(
        "audit_events",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("actor", sa.String(128)),
        sa.Column("action", sa.String(64)),
        sa.Column("target", sa.String(255)),
        sa.Column("created_at", sa.DateTime(timezone=True)),
    )


def downgrade() -> None:
    op.drop_table("audit_events")
    op.drop_table("classification_rules")
    op.drop_table("daily_activity_rollups")
    op.drop_table("user_sessions")
    op.drop_table("process_records")
    op.drop_table("process_snapshots")
    op.drop_table("hosts")
    op.execute("DROP TYPE IF EXISTS processclass")

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class HostStatus(StrEnum):
    ONLINE = "online"
    OFFLINE = "offline"
    ERROR = "error"


class HostConfig(BaseModel):
    id: str
    name: str
    hostname: str
    port: int = 22
    username: str
    private_key_path: str | None = None


class HostSummary(BaseModel):
    id: str
    name: str
    hostname: str
    port: int
    username: str


class MemoryMetrics(BaseModel):
    total_mb: int
    used_mb: int
    available_mb: int
    used_percent: float


class DiskMetrics(BaseModel):
    total_bytes: int
    used_bytes: int
    available_bytes: int
    used_percent: float
    mount: str = "/"


class HostMetrics(BaseModel):
    host_id: str
    status: HostStatus
    checked_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    uptime: str | None = None
    load_1: float | None = None
    load_5: float | None = None
    load_15: float | None = None
    memory: MemoryMetrics | None = None
    disk: DiskMetrics | None = None
    error: str | None = None

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class HostStatus(StrEnum):
    ONLINE = "online"
    OFFLINE = "offline"
    ERROR = "error"


class ProcessCategory(StrEnum):
    SYSTEM = "system"
    USER = "user"
    UNKNOWN = "unknown"


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


class HostCreateRequest(BaseModel):
    id: str | None = None
    name: str
    hostname: str
    port: int = 22
    username: str
    private_key_path: str | None = None


class HostUpdateRequest(BaseModel):
    name: str | None = None
    hostname: str | None = None
    port: int | None = None
    username: str | None = None
    private_key_path: str | None = None


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


class ProcessInfo(BaseModel):
    pid: int
    ppid: int
    user: str
    command: str
    cpu_percent: float = 0.0
    memory_percent: float = 0.0
    elapsed: str | None = None
    cmdline: str
    category: ProcessCategory = ProcessCategory.UNKNOWN
    reason: str | None = None


class ProcessSummary(BaseModel):
    total: int = 0
    system: int = 0
    user: int = 0
    unknown: int = 0


class ProcessSnapshot(BaseModel):
    host_id: str
    status: HostStatus
    collected_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    summary: ProcessSummary = Field(default_factory=ProcessSummary)
    processes: list[ProcessInfo] = Field(default_factory=list)
    error: str | None = None

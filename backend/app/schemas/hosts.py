from datetime import datetime

from pydantic import BaseModel, Field


class HostCreate(BaseModel):
    name: str
    hostname: str
    port: int = 22
    ssh_user: str
    private_key: str = Field(description="PEM private key plaintext; stored encrypted")
    poll_interval_sec: int = 60
    enabled: bool = True


class HostUpdate(BaseModel):
    name: str | None = None
    hostname: str | None = None
    port: int | None = None
    ssh_user: str | None = None
    private_key: str | None = None
    poll_interval_sec: int | None = None
    enabled: bool | None = None


class HostResponse(BaseModel):
    id: str
    name: str
    hostname: str
    port: int
    ssh_user: str
    poll_interval_sec: int
    enabled: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProcessRecordResponse(BaseModel):
    pid: int
    ppid: int
    user: str
    comm: str
    cmd: str
    cpu_percent: float | None
    mem_percent: float | None
    classification: str

    model_config = {"from_attributes": True}


class UserSessionResponse(BaseModel):
    user: str
    tty: str | None
    login_at: str | None
    idle: str | None
    from_ip: str | None

    model_config = {"from_attributes": True}


class LiveSnapshotResponse(BaseModel):
    snapshot_id: str
    host_id: str
    collected_at: datetime
    processes: list[ProcessRecordResponse]
    sessions: list[UserSessionResponse]

from datetime import datetime

from pydantic import BaseModel


class ProcessSearchResult(BaseModel):
    snapshot_id: str
    host_id: str
    collected_at: datetime
    user: str
    comm: str
    cmd: str
    classification: str

    model_config = {"from_attributes": True}


class ProcessSearchResponse(BaseModel):
    total: int
    items: list[ProcessSearchResult]

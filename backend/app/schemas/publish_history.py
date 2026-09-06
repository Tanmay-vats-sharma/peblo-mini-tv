from datetime import datetime

from pydantic import BaseModel, ConfigDict


class PublishHistoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    triggered_by: int | None = None
    status: str
    catalogue_path: str | None = None
    show_count: int
    episode_count: int
    error_count: int
    message: str | None = None
    started_at: datetime
    completed_at: datetime | None = None
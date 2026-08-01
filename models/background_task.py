"""Canonical durable background-task model."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from models.enums import BackgroundTaskStatus


class BackgroundTask(BaseModel):
    """Safe task metadata returned by persistence boundaries."""

    model_config = ConfigDict(frozen=True)

    id: UUID
    user_id: UUID | None = None
    task_type: str = Field(min_length=1, max_length=100)
    status: BackgroundTaskStatus
    resource_id: UUID | None = None
    attempt_count: int = Field(ge=0, le=11)
    max_attempts: int = Field(ge=1, le=11)
    error_code: str | None = Field(default=None, max_length=100)
    created_at: datetime
    updated_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None

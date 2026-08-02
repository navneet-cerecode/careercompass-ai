"""Authenticated saved-job transport contracts."""

from datetime import datetime

from pydantic import Field

from api.schemas.common import APIModel
from api.schemas.jobs import JobResponse


class SaveJobRequest(APIModel):
    notes: str | None = Field(default=None, max_length=2_000)


class SavedJobResponse(APIModel):
    job: JobResponse
    notes: str | None = None
    created_at: datetime
    updated_at: datetime


class SavedJobListResponse(APIModel):
    items: tuple[SavedJobResponse, ...] = ()

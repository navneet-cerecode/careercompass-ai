"""Job discovery request and response contracts."""

from enum import StrEnum
from datetime import datetime
from uuid import UUID

from pydantic import Field

from api.schemas.common import APIModel
from api.schemas.jobs import JobResponse
from models.enums import EmploymentType
from models.enums import BackgroundTaskStatus
from services.job_discovery.providers.contracts import DatePosted


class JobSearchRequest(APIModel):
    role: str = Field(min_length=1)
    location: str = Field(min_length=1)
    country: str | None = Field(default=None, min_length=2, max_length=2)
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
    remote_only: bool | None = None
    employment_types: tuple[EmploymentType, ...] = ()
    date_posted: DatePosted = DatePosted.ALL


class JobSearchStatus(StrEnum):
    COMPLETE = "complete"
    PARTIAL = "partial"
    FAILED = "failed"


class ProviderFailureResponse(APIModel):
    provider_name: str
    code: str = "provider_failed"


class JobSearchResponse(APIModel):
    status: JobSearchStatus
    jobs: tuple[JobResponse, ...] = ()
    provider_failures: tuple[ProviderFailureResponse, ...] = ()
    providers_attempted: int
    providers_succeeded: int


class JobSearchTaskCreatedResponse(APIModel):
    task_id: UUID
    access_token: str
    status: BackgroundTaskStatus


class JobSearchTaskResponse(APIModel):
    task_id: UUID
    status: BackgroundTaskStatus
    attempt_count: int
    max_attempts: int
    error_code: str | None = None
    cancellation_requested: bool = False
    created_at: datetime
    updated_at: datetime
    result: JobSearchResponse | None = None

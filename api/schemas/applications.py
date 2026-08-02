"""Authenticated assisted-application tracking contracts."""

from datetime import datetime
from uuid import UUID

from pydantic import Field

from api.schemas.common import APIModel
from api.schemas.jobs import JobResponse
from models.enums import ApplicationStatus


class CreateApplicationRequest(APIModel):
    job_id: UUID
    resume_id: UUID | None = None
    notes: str | None = Field(default=None, max_length=4_000)
    next_action: str | None = Field(default=None, max_length=500)
    next_action_due_at: datetime | None = None


class TransitionApplicationRequest(APIModel):
    status: ApplicationStatus
    note: str | None = Field(default=None, max_length=2_000)
    next_action: str | None = Field(default=None, max_length=500)
    next_action_due_at: datetime | None = None


class UpdateApplicationPlanRequest(APIModel):
    notes: str | None = Field(default=None, max_length=4_000)
    next_action: str | None = Field(default=None, max_length=500)
    next_action_due_at: datetime | None = None


class ApplicationEventResponse(APIModel):
    id: UUID
    previous_status: ApplicationStatus | None
    new_status: ApplicationStatus
    note: str | None = None
    occurred_at: datetime


class ApplicationResponse(APIModel):
    id: UUID
    job: JobResponse
    status: ApplicationStatus
    allowed_next_statuses: tuple[ApplicationStatus, ...] = ()
    resume_id: UUID | None = None
    applied_at: datetime | None = None
    notes: str | None = None
    next_action: str | None = None
    next_action_due_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class ApplicationDetailResponse(ApplicationResponse):
    events: tuple[ApplicationEventResponse, ...] = ()


class ApplicationListResponse(APIModel):
    items: tuple[ApplicationResponse, ...] = ()

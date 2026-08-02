"""Authenticated application reminder contracts."""

from datetime import datetime
from uuid import UUID

from api.schemas.common import APIModel
from api.schemas.jobs import JobResponse
from models.enums import ApplicationReminderStatus, ApplicationStatus


class UpdateApplicationReminderRequest(APIModel):
    status: ApplicationReminderStatus


class ApplicationReminderResponse(APIModel):
    id: UUID
    application_id: UUID
    job: JobResponse
    application_status: ApplicationStatus
    next_action: str
    due_at: datetime
    status: ApplicationReminderStatus
    read_at: datetime | None = None
    dismissed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class ApplicationReminderListResponse(APIModel):
    items: tuple[ApplicationReminderResponse, ...] = ()

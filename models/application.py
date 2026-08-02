"""Canonical saved-job and application tracking models."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from models.enums import ApplicationReminderStatus, ApplicationStatus


class SavedJob(BaseModel):
    model_config = ConfigDict(frozen=True)

    user_id: UUID
    job_id: UUID
    notes: str | None = None
    created_at: datetime
    updated_at: datetime


class ApplicationEvent(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: UUID
    application_id: UUID
    previous_status: ApplicationStatus | None
    new_status: ApplicationStatus
    note: str | None = None
    occurred_at: datetime


class JobApplication(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: UUID
    user_id: UUID
    job_id: UUID
    status: ApplicationStatus
    resume_id: UUID | None = None
    applied_at: datetime | None = None
    notes: str | None = None
    next_action: str | None = None
    next_action_due_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class ApplicationReminder(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: UUID
    user_id: UUID
    application_id: UUID
    due_at: datetime
    next_action: str
    status: ApplicationReminderStatus
    read_at: datetime | None = None
    dismissed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

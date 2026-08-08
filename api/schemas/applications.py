"""Authenticated assisted-application tracking contracts."""

from datetime import datetime
from typing import Literal
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


class UpdateApplicationPacketRequest(APIModel):
    tailored_resume_id: UUID | None = None
    cover_letter_id: UUID | None = None
    job_details_reviewed: bool = False
    resume_reviewed: bool = False
    cover_letter_reviewed: bool = False
    employer_questions_reviewed: bool = False


class ConfirmExternalSubmissionRequest(APIModel):
    confirm_external_submission: Literal[True]


class ApplicationDocumentOptionResponse(APIModel):
    id: UUID
    version: int
    source_resume_id: UUID
    approved_at: datetime


class ApplicationPacketResponse(APIModel):
    id: UUID
    application_id: UUID
    source_resume_id: UUID | None = None
    tailored_resume_id: UUID | None = None
    cover_letter_id: UUID | None = None
    job_details_reviewed: bool
    resume_reviewed: bool
    cover_letter_reviewed: bool
    employer_questions_reviewed: bool
    ready_at: datetime | None = None
    application_status: ApplicationStatus
    blockers: tuple[str, ...] = ()
    can_mark_ready: bool
    can_confirm_submitted: bool
    available_tailored_resumes: tuple[ApplicationDocumentOptionResponse, ...] = ()
    available_cover_letters: tuple[ApplicationDocumentOptionResponse, ...] = ()
    created_at: datetime
    updated_at: datetime


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
    packet_ready: bool = False
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

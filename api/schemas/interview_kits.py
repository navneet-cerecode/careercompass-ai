"""Interview preparation API contracts."""

from datetime import datetime
from uuid import UUID

from pydantic import Field

from api.schemas.common import APIModel
from api.schemas.jobs import JobResponse
from models.enums import ApplicationStatus
from models.interview_kit import InterviewQuestionCategory


class InterviewQuestionResponse(APIModel):
    id: str
    category: InterviewQuestionCategory
    question: str
    why_it_matters: str
    evidence_prompts: tuple[str, ...]


class InterviewKitResponse(APIModel):
    id: UUID
    application_id: UUID
    resume_id: UUID
    application_status: ApplicationStatus
    job: JobResponse
    questions: tuple[InterviewQuestionResponse, ...]
    responses: dict[str, str]
    reviewed_at: datetime | None
    created_at: datetime
    updated_at: datetime


class UpdateInterviewKitRequest(APIModel):
    responses: dict[str, str] = Field(default_factory=dict)
    confirm_reviewed: bool = False

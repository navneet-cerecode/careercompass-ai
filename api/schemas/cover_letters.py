"""Cover letter review, version, and export contracts."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from api.schemas.common import APIModel
from pydantic import Field, field_validator


class CreateCoverLetterRequest(APIModel):
    plan_id: UUID


class CoverLetterContentRequest(APIModel):
    candidate_name: str = Field(min_length=1, max_length=200)
    candidate_email: str | None = Field(default=None, max_length=320)
    company_name: str = Field(min_length=1, max_length=300)
    job_title: str = Field(min_length=1, max_length=300)
    salutation: str = Field(min_length=1, max_length=200)
    opening: str = Field(min_length=1, max_length=1_500)
    evidence_paragraph: str = Field(min_length=1, max_length=2_500)
    motivation_paragraph: str = Field(min_length=1, max_length=1_500)
    closing_paragraph: str = Field(min_length=1, max_length=1_500)
    sign_off: str = Field(min_length=1, max_length=200)

    @field_validator("*")
    @classmethod
    def strip_text(cls, value: str | None) -> str | None:
        return value.strip() if isinstance(value, str) else value


class ApproveCoverLetterRequest(APIModel):
    confirm_factual_accuracy: Literal[True]


class CoverLetterEvidenceResponse(APIModel):
    kind: Literal["skill", "experience", "project"]
    source_index: int
    source_text: str


class CoverLetterResponse(APIModel):
    id: UUID
    plan_id: UUID
    source_resume_id: UUID
    job_id: UUID
    version: int
    suggested: CoverLetterContentRequest
    accepted: CoverLetterContentRequest
    evidence: tuple[CoverLetterEvidenceResponse, ...] = ()
    verification_status: Literal["pending_review", "user_verified"]
    user_review_required: bool
    approved_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class CoverLetterVersionListResponse(APIModel):
    items: tuple[CoverLetterResponse, ...] = ()

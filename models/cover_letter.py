"""Versioned, user-reviewed cover letter contracts."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class CoverLetterContent(BaseModel):
    """Editable cover letter content bounded for safe document generation."""

    model_config = ConfigDict(frozen=True)

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


class CoverLetterEvidence(BaseModel):
    """Verified source material used by the deterministic suggestion."""

    model_config = ConfigDict(frozen=True)

    kind: Literal["skill", "experience", "project"]
    source_index: int = Field(ge=0)
    source_text: str = Field(min_length=1)


class CoverLetterVersion(BaseModel):
    """An immutable suggestion and accepted-content snapshot."""

    model_config = ConfigDict(frozen=True)

    id: UUID
    user_id: UUID
    plan_id: UUID
    source_resume_id: UUID
    job_id: UUID
    version: int
    suggested: CoverLetterContent
    accepted: CoverLetterContent
    evidence: tuple[CoverLetterEvidence, ...] = ()
    verification_status: Literal["pending_review", "user_verified"] = "pending_review"
    user_review_required: bool = True
    approved_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

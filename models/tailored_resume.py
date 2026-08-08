"""Versioned, user-reviewed tailored resume contracts."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from models.skill import Skill

SectionChoice = Literal["original", "suggested"]
VerificationStatus = Literal["pending_review", "user_verified"]


class TailoredResumeContent(BaseModel):
    """A complete resume snapshot suitable for comparison and export."""

    model_config = ConfigDict(frozen=True)

    name: str
    email: str | None = None
    phone: str | None = None
    linkedin: str | None = None
    github: str | None = None
    education: tuple[str, ...] = ()
    experience: tuple[str, ...] = ()
    projects: tuple[str, ...] = ()
    skills: tuple[Skill, ...] = ()
    certifications: tuple[str, ...] = ()
    achievements: tuple[str, ...] = ()


class TailoredResumeSelections(BaseModel):
    """The only transformations this phase permits."""

    model_config = ConfigDict(frozen=True)

    skills: SectionChoice = "suggested"
    experience: SectionChoice = "suggested"
    projects: SectionChoice = "suggested"


class TailoredResumeVersion(BaseModel):
    """A durable original/suggested/accepted comparison snapshot."""

    model_config = ConfigDict(frozen=True)

    id: UUID
    user_id: UUID
    plan_id: UUID
    source_resume_id: UUID
    job_id: UUID
    version: int
    original: TailoredResumeContent
    suggested: TailoredResumeContent
    accepted: TailoredResumeContent
    selections: TailoredResumeSelections
    verification_status: VerificationStatus = "pending_review"
    user_review_required: bool = True
    approved_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

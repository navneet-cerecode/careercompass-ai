"""Tailored resume review, version, and export contracts."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from api.schemas.common import APIModel, SkillResponse


class CreateTailoredResumeRequest(APIModel):
    plan_id: UUID


class TailoredResumeSelectionsRequest(APIModel):
    skills: Literal["original", "suggested"] = "suggested"
    experience: Literal["original", "suggested"] = "suggested"
    projects: Literal["original", "suggested"] = "suggested"


class ApproveTailoredResumeRequest(APIModel):
    confirm_factual_accuracy: Literal[True]


class TailoredResumeContentResponse(APIModel):
    name: str
    email: str | None = None
    phone: str | None = None
    linkedin: str | None = None
    github: str | None = None
    education: tuple[str, ...] = ()
    experience: tuple[str, ...] = ()
    projects: tuple[str, ...] = ()
    skills: tuple[SkillResponse, ...] = ()
    certifications: tuple[str, ...] = ()
    achievements: tuple[str, ...] = ()


class TailoredResumeResponse(APIModel):
    id: UUID
    plan_id: UUID
    source_resume_id: UUID
    job_id: UUID
    version: int
    original: TailoredResumeContentResponse
    suggested: TailoredResumeContentResponse
    accepted: TailoredResumeContentResponse
    selections: TailoredResumeSelectionsRequest
    verification_status: Literal["pending_review", "user_verified"]
    user_review_required: bool
    approved_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class TailoredResumeVersionListResponse(APIModel):
    items: tuple[TailoredResumeResponse, ...] = ()

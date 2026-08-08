"""Factual tailoring-plan transport contracts."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from api.schemas.common import APIModel, SkillResponse


class CreateTailoringPlanRequest(APIModel):
    job_id: UUID
    resume_id: UUID | None = None


class TailoringEvidenceResponse(APIModel):
    section: Literal["experience", "project"]
    source_index: int
    source_text: str
    matched_terms: tuple[str, ...] = ()


class TailoringPlanResponse(APIModel):
    id: UUID
    source_resume_id: UUID
    job_id: UUID
    skills: tuple[SkillResponse, ...] = ()
    experience: tuple[str, ...] = ()
    projects: tuple[str, ...] = ()
    matched_skills: tuple[SkillResponse, ...] = ()
    missing_skills: tuple[SkillResponse, ...] = ()
    evidence: tuple[TailoringEvidenceResponse, ...] = ()
    user_review_required: bool
    algorithm_version: str
    created_at: datetime
    updated_at: datetime

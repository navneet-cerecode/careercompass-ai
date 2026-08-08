"""Factual, user-reviewed resume tailoring contracts."""

from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from models.skill import Skill


class TailoringEvidence(BaseModel):
    """Existing resume evidence prioritized for a target job."""

    model_config = ConfigDict(frozen=True)

    section: Literal["experience", "project"]
    source_index: int = Field(ge=0)
    source_text: str = Field(min_length=1)
    matched_terms: tuple[str, ...] = ()


class FactualTailoringPlan(BaseModel):
    """A non-generative ordering plan that cannot add candidate claims."""

    model_config = ConfigDict(frozen=True)

    source_resume_id: UUID
    job_id: UUID
    skills: tuple[Skill, ...] = ()
    experience: tuple[str, ...] = ()
    projects: tuple[str, ...] = ()
    matched_skills: tuple[Skill, ...] = ()
    missing_skills: tuple[Skill, ...] = ()
    evidence: tuple[TailoringEvidence, ...] = ()
    user_review_required: Literal[True] = True
    algorithm_version: str = "factual-ordering-v1"

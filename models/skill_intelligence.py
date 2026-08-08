"""Owner-scoped, evidence-only skill intelligence contracts."""

from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict

SkillEvidenceStatus = Literal["supported", "develop", "resume_only"]


class SkillRoleReference(BaseModel):
    model_config = ConfigDict(frozen=True)

    job_id: UUID
    title: str
    company: str


class SkillIntelligenceItem(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str
    category: str | None = None
    status: SkillEvidenceStatus
    resume_evidenced: bool
    observed_role_count: int
    observed_roles: tuple[SkillRoleReference, ...] = ()


class SkillIntelligenceSnapshot(BaseModel):
    model_config = ConfigDict(frozen=True)

    resume_id: UUID | None
    roles_analyzed: int
    roles_with_skill_data: int
    roles_without_skill_data: int
    search_history_roles: int
    saved_roles: int
    application_roles: int
    skills: tuple[SkillIntelligenceItem, ...] = ()

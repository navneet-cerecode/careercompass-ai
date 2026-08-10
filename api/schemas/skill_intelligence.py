"""Skill intelligence API responses."""

from uuid import UUID

from api.schemas.common import APIModel
from models.skill_intelligence import SkillEvidenceStatus, SkillMatchConfidence


class SkillRoleReferenceResponse(APIModel):
    job_id: UUID
    title: str
    company: str


class SkillIntelligenceItemResponse(APIModel):
    name: str
    category: str | None
    status: SkillEvidenceStatus
    resume_evidenced: bool
    match_confidence: SkillMatchConfidence | None
    matched_terms: tuple[str, ...]
    observed_role_count: int
    observed_roles: tuple[SkillRoleReferenceResponse, ...]


class SkillIntelligenceResponse(APIModel):
    resume_id: UUID | None
    roles_analyzed: int
    roles_with_skill_data: int
    roles_without_skill_data: int
    search_history_roles: int
    saved_roles: int
    application_roles: int
    skills: tuple[SkillIntelligenceItemResponse, ...]

"""Skill intelligence API responses."""

from datetime import datetime
from uuid import UUID

from api.schemas.common import APIModel
from models.skill_intelligence import (
    RoleClusterBasis,
    SkillEvidenceStatus,
    SkillMatchConfidence,
)


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


class RoleClusterResponse(APIModel):
    label: str
    basis: RoleClusterBasis
    role_count: int
    roles: tuple[SkillRoleReferenceResponse, ...]


class RoleHistoryWindowResponse(APIModel):
    first_observed_at: datetime | None
    last_observed_at: datetime | None
    observed_last_7_days: int
    observed_8_to_30_days: int
    observed_over_30_days: int


class SkillIntelligenceResponse(APIModel):
    resume_id: UUID | None
    roles_analyzed: int
    roles_with_skill_data: int
    roles_without_skill_data: int
    search_history_roles: int
    saved_roles: int
    application_roles: int
    history_window: RoleHistoryWindowResponse
    role_clusters: tuple[RoleClusterResponse, ...]
    skills: tuple[SkillIntelligenceItemResponse, ...]

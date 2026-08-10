"""Owner-scoped, evidence-only skill intelligence contracts."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict

SkillEvidenceStatus = Literal["supported", "develop", "resume_only"]
SkillMatchConfidence = Literal["exact", "curated_high"]
RoleClusterBasis = Literal["search_intent", "role_title"]


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
    match_confidence: SkillMatchConfidence | None = None
    matched_terms: tuple[str, ...] = ()
    observed_role_count: int
    observed_roles: tuple[SkillRoleReference, ...] = ()


class RoleCluster(BaseModel):
    model_config = ConfigDict(frozen=True)

    label: str
    basis: RoleClusterBasis
    role_count: int
    roles: tuple[SkillRoleReference, ...] = ()


class RoleHistoryWindow(BaseModel):
    model_config = ConfigDict(frozen=True)

    first_observed_at: datetime | None = None
    last_observed_at: datetime | None = None
    observed_last_7_days: int = 0
    observed_8_to_30_days: int = 0
    observed_over_30_days: int = 0


class SkillIntelligenceSnapshot(BaseModel):
    model_config = ConfigDict(frozen=True)

    resume_id: UUID | None
    roles_analyzed: int
    roles_with_skill_data: int
    roles_without_skill_data: int
    search_history_roles: int
    saved_roles: int
    application_roles: int
    history_window: RoleHistoryWindow = RoleHistoryWindow()
    role_clusters: tuple[RoleCluster, ...] = ()
    skills: tuple[SkillIntelligenceItem, ...] = ()

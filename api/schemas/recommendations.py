"""Recommendation transport contracts."""

from uuid import UUID, uuid4

from pydantic import EmailStr, Field

from api.schemas.common import APIModel, SkillResponse
from api.schemas.jobs import JobResponse


class ScoreComponentResponse(APIModel):
    name: str
    score: float
    explanation: str
    matched_skills: tuple[SkillResponse, ...] = ()
    missing_skills: tuple[SkillResponse, ...] = ()


class MatchAssessmentResponse(APIModel):
    id: UUID
    job: JobResponse
    score: float
    components: tuple[ScoreComponentResponse, ...] = ()
    matched_skills: tuple[SkillResponse, ...] = ()
    missing_skills: tuple[SkillResponse, ...] = ()
    recruiter_summary: str | None = None
    recommendations: tuple[str, ...] = ()
    confidence: float | None = None
    algorithm_version: str


class JobRecommendationResponse(APIModel):
    id: UUID
    assessment: MatchAssessmentResponse
    rank: int | None = None


class ResumeRecommendationInput(APIModel):
    """User-reviewed resume content accepted by the ranking endpoint."""

    id: UUID = Field(default_factory=uuid4)
    name: str = Field(min_length=1)
    email: EmailStr | None = None
    phone: str | None = None
    linkedin: str | None = None
    github: str | None = None
    education: tuple[str, ...] = ()
    experience: tuple[str, ...] = ()
    projects: tuple[str, ...] = ()
    skills: tuple[SkillResponse, ...] = ()
    certifications: tuple[str, ...] = ()
    achievements: tuple[str, ...] = ()
    raw_text: str = Field(min_length=1)


class RecommendationRequest(APIModel):
    resume: ResumeRecommendationInput
    job_ids: tuple[UUID, ...] = Field(min_length=1, max_length=100)


class RecommendationBatchResponse(APIModel):
    recommendations: tuple[JobRecommendationResponse, ...]

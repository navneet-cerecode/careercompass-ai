"""Canonical assessment of one resume against one job."""

from uuid import UUID, uuid4

from pydantic import AliasChoices, BaseModel, ConfigDict, Field

from models.job import Job
from models.score_component import ScoreComponent
from models.skill import Skill


class MatchAssessment(BaseModel):
    """Versioned and explainable result of evaluating a candidate for a job."""

    model_config = ConfigDict(
        populate_by_name=True,
        validate_assignment=True,
    )

    id: UUID = Field(default_factory=uuid4)
    job: Job
    score: float = Field(
        ge=0,
        le=100,
        validation_alias=AliasChoices("score", "match_score"),
    )
    components: list[ScoreComponent] = Field(
        default_factory=list,
        validation_alias=AliasChoices("components", "signal_results"),
    )
    matched_skills: list[Skill] = Field(default_factory=list)
    missing_skills: list[Skill] = Field(default_factory=list)
    recruiter_summary: str | None = None
    recommendations: list[str] = Field(default_factory=list)
    confidence: float | None = Field(default=None, ge=0, le=1)
    algorithm_version: str = Field(default="unversioned", min_length=1)

    @property
    def match_score(self) -> float:
        """Compatibility attribute for the former MatchResult model."""
        return self.score

    @property
    def signal_results(self) -> list[ScoreComponent]:
        """Compatibility attribute for former recommendation result models."""
        return self.components

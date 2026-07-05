"""
Job Recommendation Model.

Represents a recommended job together with
its recommendation score and optional AI insights.
"""

from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field

from models.job import Job
from models.skill import Skill

from services.recommendation.models.signal_result import (
    SignalResult,
)


class JobRecommendation(BaseModel):
    """
    Represents a ranked job recommendation.
    """

    model_config = ConfigDict(
        validate_assignment=True
    )

    id: UUID = Field(
        default_factory=uuid4,
    )

    job: Job

    score: float

    matched_skills: list[Skill] = Field(
        default_factory=list,
    )

    missing_skills: list[Skill] = Field(
        default_factory=list,
    )

    signal_results: list[SignalResult] = Field(
        default_factory=list,
    )

    recruiter_summary: str | None = None

    recommendations: list[str] = Field(
        default_factory=list,
    )
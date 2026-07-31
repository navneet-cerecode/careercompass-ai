"""User-facing ranked recommendation backed by a match assessment."""

from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, model_validator

from models.job import Job
from models.match_assessment import MatchAssessment
from models.score_component import ScoreComponent
from models.skill import Skill


class JobRecommendation(BaseModel):
    """Ranked presentation record that references one canonical assessment."""

    model_config = ConfigDict(
        validate_assignment=True,
    )

    id: UUID = Field(default_factory=uuid4)
    assessment: MatchAssessment
    rank: int | None = Field(default=None, ge=1)

    @model_validator(mode="before")
    @classmethod
    def adapt_legacy_shape(cls, value):
        """Accept the former flat constructor during the migration window."""
        if not isinstance(value, dict) or "assessment" in value:
            return value

        if "job" not in value or "score" not in value:
            return value

        data = dict(value)
        assessment_fields = {
            "job": data.pop("job"),
            "score": data.pop("score"),
            "components": data.pop("signal_results", []),
            "matched_skills": data.pop("matched_skills", []),
            "missing_skills": data.pop("missing_skills", []),
            "recruiter_summary": data.pop("recruiter_summary", None),
            "recommendations": data.pop("recommendations", []),
            "algorithm_version": data.pop("algorithm_version", "legacy"),
        }
        data["assessment"] = assessment_fields
        return data

    @property
    def job(self) -> Job:
        return self.assessment.job

    @property
    def score(self) -> float:
        return self.assessment.score

    @property
    def matched_skills(self) -> list[Skill]:
        return self.assessment.matched_skills

    @property
    def missing_skills(self) -> list[Skill]:
        return self.assessment.missing_skills

    @property
    def signal_results(self) -> list[ScoreComponent]:
        return self.assessment.components

    @property
    def recruiter_summary(self) -> str | None:
        return self.assessment.recruiter_summary

    @property
    def recommendations(self) -> list[str]:
        return self.assessment.recommendations

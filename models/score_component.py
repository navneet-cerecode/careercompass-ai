"""Canonical explainable score component model."""

from pydantic import AliasChoices, BaseModel, ConfigDict, Field

from models.skill import Skill


class ScoreComponent(BaseModel):
    """One bounded and explainable contribution to a match score."""

    model_config = ConfigDict(
        populate_by_name=True,
        validate_assignment=True,
    )

    name: str = Field(
        min_length=1,
        validation_alias=AliasChoices("name", "signal_name"),
    )
    score: float = Field(ge=0, le=100)
    explanation: str = Field(
        default="",
        validation_alias=AliasChoices("explanation", "reason"),
    )
    matched_skills: list[Skill] = Field(default_factory=list)
    missing_skills: list[Skill] = Field(default_factory=list)

    @property
    def signal_name(self) -> str:
        """Compatibility attribute for the former SignalResult model."""
        return self.name

    @property
    def reason(self) -> str:
        """Compatibility attribute for the former SignalResult model."""
        return self.explanation

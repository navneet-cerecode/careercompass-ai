"""
Represents the output of a recommendation signal.
"""

from pydantic import BaseModel, Field

from models.skill import Skill


class SignalResult(BaseModel):
    """
    Output produced by one recommendation signal.
    """

    signal_name: str

    score: float

    reason: str

    matched_skills: list[Skill] = Field(
        default_factory=list
    )

    missing_skills: list[Skill] = Field(
        default_factory=list
    )
"""
File: models/match.py

Description:
Defines the MatchResult model representing the evaluation
of a candidate's resume against a job posting.

Author:
Navneet Prakash Yadav
"""

from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field

from models.job import Job
from models.skill import Skill


class MatchResult(BaseModel):
    """
    Represents the result of matching a resume
    against a single job.
    """

    model_config = ConfigDict(
        validate_assignment=True
    )

    id: UUID = Field(
        default_factory=uuid4,
        description="Unique identifier for this match result."
    )

    job: Job = Field(
        ...,
        description="The evaluated job."
    )

    match_score: float = Field(
        ...,
        ge=0,
        le=100,
        description="Overall compatibility score."
    )

    matched_skills: list[Skill] = Field(
        default_factory=list,
        description="Skills present in both the resume and the job description."
    )

    missing_skills: list[Skill] = Field(
        default_factory=list,
        description="Required skills missing from the resume."
    )

    recruiter_summary: str = Field(
        ...,
        description="AI-generated explanation of the match."
    )

    recommendations: list[str] = Field(
        default_factory=list,
        description="Actionable recommendations for improving the match."
    )
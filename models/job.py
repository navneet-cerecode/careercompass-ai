"""
File: models/job.py

Description:
Defines the canonical Job model used throughout the application.

Every job collected from any source (Greenhouse, Lever,
company careers page, etc.) is normalized into this model.

Author:
Navneet Prakash Yadav
"""

from uuid import UUID, uuid4

from pydantic import AnyHttpUrl, BaseModel, Field

from models.enums import (
    EmploymentType,
    ExperienceLevel,
    JobSource,
)
from models.skill import Skill


class Job(BaseModel):
    """
    Represents a normalized job posting.
    """

    id: UUID = Field(
        default_factory=uuid4,
        description="Unique internal identifier for the job."
    )

    title: str = Field(
        ...,
        description="Job title."
    )

    company: str = Field(
        ...,
        description="Company offering the job."
    )

    location: str = Field(
        ...,
        description="Job location."
    )

    description: str = Field(
        ...,
        description="Complete job description."
    )

    required_skills: list[Skill] = Field(
        default_factory=list,
        description="Skills required for this position."
    )

    experience_level: ExperienceLevel = Field(
        default=ExperienceLevel.ENTRY
    )

    employment_type: EmploymentType = Field(
        default=EmploymentType.FULL_TIME
    )

    source: JobSource = Field(
        default=JobSource.OTHER
    )

    url: AnyHttpUrl = Field(
        ...,
        description="Application URL."
    )
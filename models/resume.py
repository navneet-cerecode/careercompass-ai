"""
Resume domain model.
"""

from uuid import UUID
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from models.skill import Skill


class Resume(BaseModel):
    """
    Represents a parsed candidate resume.
    """

    model_config = ConfigDict(
        validate_assignment=True,
    )

    id: UUID = Field(default_factory=uuid4)

    name: str

    email: EmailStr | None = None

    phone: str | None = None

    linkedin: str | None = None

    github: str | None = None

    education: list[str] = Field(default_factory=list)

    experience: list[str] = Field(default_factory=list)

    projects: list[str] = Field(default_factory=list)

    skills: list[Skill] = Field(default_factory=list)

    certifications: list[str] = Field(default_factory=list)

    achievements: list[str] = Field(default_factory=list)

    raw_text: str

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Resume name cannot be empty.")
        return value

    @field_validator("raw_text")
    @classmethod
    def validate_raw_text(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Resume text cannot be empty.")
        return value

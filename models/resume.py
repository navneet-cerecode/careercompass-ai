"""
Resume domain model.
"""

from uuid import uuid4
from uuid import UUID

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import EmailStr

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

    education: list[str] = []

    experience: list[str] = []

    projects: list[str] = []

    skills: list[Skill] = []

    certifications: list[str] = []

    achievements: list[str] = []

    raw_text: str
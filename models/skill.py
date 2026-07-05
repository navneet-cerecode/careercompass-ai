"""
File: models/skill.py

Description:
Defines the Skill domain model used throughout the application.
A Skill represents a technology, framework, language, tool, or concept
possessed by a candidate or required by a job.

Author:
Navneet Prakash Yadav
"""

from typing import Optional

from pydantic import BaseModel, Field, field_validator


class Skill(BaseModel):
    """
    Represents a single technical skill.
    """

    name: str = Field(
        ...,
        description="Name of the skill."
    )

    category: Optional[str] = Field(
        default=None,
        description="Optional category of the skill."
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        """
        Normalize the skill name.

        Example:
            ' python ' -> 'Python'
            'PYTORCH' -> 'Pytorch'
        """
        value = value.strip()

        if not value:
            raise ValueError("Skill name cannot be empty.")

        return value.title()
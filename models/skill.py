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

    name: str = Field(..., description="Name of the skill.")

    category: Optional[str] = Field(default=None, description="Optional category of the skill.")

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("Skill name cannot be empty.")

        canonical_names = {
            "api": "API",
            "aws": "AWS",
            "c#": "C#",
            "c++": "C++",
            "gcp": "GCP",
            "github": "GitHub",
            "javascript": "JavaScript",
            "mysql": "MySQL",
            "nlp": "NLP",
            "node.js": "Node.js",
            "numpy": "NumPy",
            "opencv": "OpenCV",
            "pytorch": "PyTorch",
            "react.js": "React.js",
            "scikit-learn": "Scikit-learn",
            "sql": "SQL",
            "tensorflow": "TensorFlow",
            "typescript": "TypeScript",
        }

        return canonical_names.get(value.casefold(), value.title())

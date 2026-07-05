"""
Dummy job provider.

Used during development until real providers
(JobSpy, Playwright) are integrated.
"""

from models.enums import (
    EmploymentType,
    ExperienceLevel,
    JobSource,
)
from models.job import Job
from models.skill import Skill

from .base_provider import BaseProvider


class DummyProvider(BaseProvider):
    """
    Returns hardcoded jobs for development.
    """

    def search(
        self,
        role: str,
        location: str,
    ) -> list[Job]:

        return [
            Job(
                title=role,
                company="Google",
                location=location,
                description="Python, SQL and Machine Learning",
                required_skills=[
                    Skill(name="Python"),
                    Skill(name="SQL"),
                    Skill(name="Machine Learning"),
                ],
                experience_level=ExperienceLevel.ENTRY,
                employment_type=EmploymentType.FULL_TIME,
                source=JobSource.OTHER,
                url="https://careers.google.com/",
            )
        ]
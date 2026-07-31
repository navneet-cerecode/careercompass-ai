"""Deterministic development job provider."""

from collections.abc import Mapping
from typing import Any

from models.enums import EmploymentType, ExperienceLevel, JobSource
from models.job import Job
from models.skill import Skill

from services.job_discovery.providers.base_provider import BaseProvider
from services.job_discovery.providers.contracts import (
    JobSearchQuery,
    ProviderCapabilities,
)


class DummyProvider(BaseProvider):
    """Return deterministic jobs for development and contract tests."""

    CAPABILITIES = ProviderCapabilities(
        location_filter=True,
    )

    @property
    def provider_name(self) -> str:
        return "dummy"

    @property
    def capabilities(self) -> ProviderCapabilities:
        return self.CAPABILITIES

    def search_jobs(
        self,
        query: JobSearchQuery,
    ) -> list[Job]:
        return [
            self.normalize_job(
                {
                    "title": query.role,
                    "location": query.location,
                }
            )
        ]

    def normalize_job(
        self,
        raw_job: Mapping[str, Any],
    ) -> Job:
        return Job(
            title=str(raw_job["title"]),
            company="Google",
            location=str(raw_job["location"]),
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

"""Workday job provider."""

from collections.abc import Mapping
from typing import Any

import requests

from models.enums import EmploymentType, ExperienceLevel, JobSource
from models.job import Job

from services.job_discovery.providers.base_provider import BaseProvider
from services.job_discovery.providers.contracts import (
    JobSearchQuery,
    ProviderCapabilities,
    ProviderConfig,
)
from services.job_discovery.providers.errors import ProviderPayloadError


class WorkdayProvider(BaseProvider):
    """Provider for configured Workday career portals."""

    CAPABILITIES = ProviderCapabilities(
        pagination=True,
    )

    def __init__(self, company: ProviderConfig):
        self.company = company
        self.api_url = company["api_url"]

    @property
    def provider_name(self) -> str:
        company_id = self.company.get("id") or self.company["name"].lower()
        return f"workday:{company_id}"

    @property
    def capabilities(self) -> ProviderCapabilities:
        return self.CAPABILITIES

    def search_jobs(
        self,
        query: JobSearchQuery,
    ) -> list[Job]:
        response = requests.post(
            self.api_url,
            json={
                "limit": query.page_size,
                "offset": (query.page - 1) * query.page_size,
                "searchText": query.role,
            },
            timeout=30,
        )
        response.raise_for_status()

        data = response.json()
        if not isinstance(data, Mapping):
            raise ProviderPayloadError("Workday returned an invalid response object.")

        raw_jobs = data.get("jobPostings", [])
        if not isinstance(raw_jobs, list):
            raise ProviderPayloadError("Workday returned an invalid jobs collection.")

        return [self.normalize_job(item) for item in raw_jobs]

    def normalize_job(
        self,
        raw_job: Mapping[str, Any],
    ) -> Job:
        if not isinstance(raw_job, Mapping):
            raise ProviderPayloadError("Workday returned an invalid job object.")

        base_url = self.company["careers_url"].rstrip("/")
        external_path = str(raw_job["externalPath"]).lstrip("/")

        return Job(
            title=str(raw_job["title"]),
            company=self.company["name"],
            location=raw_job.get("locationsText") or "Unknown",
            description="",
            required_skills=[],
            experience_level=ExperienceLevel.ENTRY,
            employment_type=EmploymentType.FULL_TIME,
            source=JobSource.WORKDAY,
            url=f"{base_url}/{external_path}",
        )

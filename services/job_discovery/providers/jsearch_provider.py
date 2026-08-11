"""JSearch job provider."""

from collections.abc import Mapping
from typing import Any

import requests

from core.config import settings
from models.enums import EmploymentType, ExperienceLevel, JobSource
from models.job import Job

from services.job_discovery.providers.base_provider import BaseProvider
from services.job_discovery.providers.contracts import (
    JobSearchQuery,
    ProviderCapabilities,
    ProviderConfig,
)
from services.job_discovery.providers.errors import (
    ProviderConfigurationError,
    ProviderPayloadError,
)


class JSearchProvider(BaseProvider):
    """JSearch adapter backed by RapidAPI."""

    BASE_URL = "https://jsearch.p.rapidapi.com/search-v2"
    CAPABILITIES = ProviderCapabilities(
        location_filter=True,
        country_filter=True,
        date_posted_filter=True,
        pagination=True,
    )

    def __init__(
        self,
        company: ProviderConfig,
        api_key: str | None = None,
    ):
        self.company = company

        if api_key is None and settings.rapidapi_key is not None:
            api_key = settings.rapidapi_key.get_secret_value()

        if not api_key:
            raise ProviderConfigurationError("Missing RAPIDAPI_KEY.")

        self.api_key = api_key

    @property
    def provider_name(self) -> str:
        return "jsearch"

    @property
    def capabilities(self) -> ProviderCapabilities:
        return self.CAPABILITIES

    def search_jobs(
        self,
        query: JobSearchQuery,
    ) -> list[Job]:
        headers = {
            "X-RapidAPI-Key": self.api_key,
            "X-RapidAPI-Host": "jsearch.p.rapidapi.com",
        }
        params = {
            "query": f"{query.role} jobs in {query.location}",
            "page": str(query.page),
            "num_pages": "1",
            "date_posted": query.date_posted.value,
        }

        country = query.country or self.company.get("country")
        if country:
            params["country"] = country

        response = requests.get(
            self.BASE_URL,
            headers=headers,
            params=params,
            timeout=30,
        )
        response.raise_for_status()

        payload = response.json()
        data = payload.get("data", {})
        if not isinstance(data, Mapping):
            raise ProviderPayloadError("JSearch returned an invalid data object.")

        raw_jobs = data.get("jobs", [])

        if not isinstance(raw_jobs, list):
            raise ProviderPayloadError("JSearch returned an invalid jobs collection.")

        return [self.normalize_job(item) for item in raw_jobs]

    def normalize_job(
        self,
        raw_job: Mapping[str, Any],
    ) -> Job:
        if not isinstance(raw_job, Mapping):
            raise ProviderPayloadError("JSearch returned an invalid job object.")

        apply_url = raw_job.get("job_apply_link")
        if not apply_url:
            raise ProviderPayloadError("JSearch job is missing an application URL.")

        return Job(
            title=raw_job.get("job_title") or "Unknown",
            company=raw_job.get("employer_name") or "Unknown",
            location=raw_job.get("job_location") or "Unknown",
            description=raw_job.get("job_description") or "",
            required_skills=[],
            experience_level=ExperienceLevel.ENTRY,
            employment_type=EmploymentType.FULL_TIME,
            source=JobSource.JSEARCH,
            source_name=self.provider_name,
            external_id=raw_job.get("job_uid") or raw_job.get("job_id"),
            source_url=raw_job.get("job_google_link") or apply_url,
            url=apply_url,
        )

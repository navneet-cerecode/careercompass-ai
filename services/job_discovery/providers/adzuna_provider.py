"""Adzuna job provider."""

from collections.abc import Mapping
from typing import Any

import requests

from core.config import settings
from models.enums import EmploymentType, ExperienceLevel, JobSource
from models.job import Job
from services.job_discovery.providers.base_provider import BaseProvider
from services.job_discovery.providers.contracts import (
    DatePosted,
    JobSearchQuery,
    ProviderCapabilities,
    ProviderConfig,
)
from services.job_discovery.providers.errors import (
    ProviderConfigurationError,
    ProviderPayloadError,
)


class AdzunaProvider(BaseProvider):
    """Adapter for Adzuna's country-specific search API."""

    BASE_URL = "https://api.adzuna.com/v1/api/jobs"
    CAPABILITIES = ProviderCapabilities(
        location_filter=True,
        country_filter=True,
        employment_type_filter=True,
        date_posted_filter=True,
        pagination=True,
    )
    DAYS_OLD = {
        DatePosted.TODAY: 1,
        DatePosted.THREE_DAYS: 3,
        DatePosted.WEEK: 7,
        DatePosted.MONTH: 30,
    }

    def __init__(
        self,
        company: ProviderConfig,
        app_id: str | None = None,
        app_key: str | None = None,
    ):
        self.company = company
        if app_id is None and settings.adzuna_app_id is not None:
            app_id = settings.adzuna_app_id.get_secret_value()
        if app_key is None and settings.adzuna_app_key is not None:
            app_key = settings.adzuna_app_key.get_secret_value()
        if not app_id or not app_key:
            raise ProviderConfigurationError(
                "ADZUNA_APP_ID and ADZUNA_APP_KEY are required."
            )
        self.app_id = app_id
        self.app_key = app_key

    @property
    def provider_name(self) -> str:
        return "adzuna"

    @property
    def capabilities(self) -> ProviderCapabilities:
        return self.CAPABILITIES

    def search_jobs(self, query: JobSearchQuery) -> list[Job]:
        country = query.country or self.company.get("country")
        if not country:
            raise ProviderConfigurationError("Adzuna requires a two-letter country code.")

        params: dict[str, str | int] = {
            "app_id": self.app_id,
            "app_key": self.app_key,
            "results_per_page": query.page_size,
            "what": query.role,
            "where": query.location,
            "content-type": "application/json",
        }
        if query.date_posted in self.DAYS_OLD:
            params["max_days_old"] = self.DAYS_OLD[query.date_posted]
        selected_types = set(query.employment_types)
        if selected_types == {EmploymentType.FULL_TIME}:
            params["full_time"] = 1
        elif selected_types == {EmploymentType.PART_TIME}:
            params["part_time"] = 1
        elif selected_types == {EmploymentType.CONTRACT}:
            params["contract"] = 1

        response = requests.get(
            f"{self.BASE_URL}/{country}/search/{query.page}",
            params=params,
            timeout=30,
        )
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, Mapping):
            raise ProviderPayloadError("Adzuna returned an invalid response object.")
        raw_jobs = payload.get("results", [])
        if not isinstance(raw_jobs, list):
            raise ProviderPayloadError("Adzuna returned an invalid jobs collection.")
        return [self.normalize_job(item) for item in raw_jobs]

    def normalize_job(self, raw_job: Mapping[str, Any]) -> Job:
        if not isinstance(raw_job, Mapping):
            raise ProviderPayloadError("Adzuna returned an invalid job object.")
        url = raw_job.get("redirect_url")
        if not url:
            raise ProviderPayloadError("Adzuna job is missing an application URL.")

        return Job(
            title=str(raw_job.get("title") or "Unknown"),
            company=self._display_name(raw_job.get("company")),
            location=self._display_name(raw_job.get("location")),
            description=str(raw_job.get("description") or ""),
            required_skills=[],
            experience_level=ExperienceLevel.ENTRY,
            employment_type=self._employment_type(raw_job),
            source=JobSource.ADZUNA,
            source_name=self.provider_name,
            external_id=str(raw_job.get("id") or url),
            source_url=str(url),
            url=str(url),
        )

    @staticmethod
    def _display_name(value: Any) -> str:
        if isinstance(value, Mapping):
            return str(value.get("display_name") or "Unknown")
        return "Unknown"

    @staticmethod
    def _employment_type(raw_job: Mapping[str, Any]) -> EmploymentType:
        if raw_job.get("contract_time") == "part_time":
            return EmploymentType.PART_TIME
        if raw_job.get("contract_type") == "contract":
            return EmploymentType.CONTRACT
        return EmploymentType.FULL_TIME

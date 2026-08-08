"""Arbeitnow job provider for its public Germany and UK feeds."""

import html
import re
from collections.abc import Mapping
from typing import Any

import requests

from models.enums import EmploymentType, ExperienceLevel, JobSource
from models.job import Job
from models.skill import Skill
from services.job_discovery.providers.base_provider import BaseProvider
from services.job_discovery.providers.contracts import (
    JobSearchQuery,
    ProviderCapabilities,
    ProviderConfig,
)
from services.job_discovery.providers.errors import ProviderPayloadError


class ArbeitnowProvider(BaseProvider):
    """Adapter for Arbeitnow's public, keyless job-board API."""

    ENDPOINTS = {
        "de": "https://www.arbeitnow.com/api/job-board-api",
        "gb": "https://www.arbeitnow.co.uk/api/job-board-api",
    }
    CAPABILITIES = ProviderCapabilities(
        location_filter=True,
        country_filter=True,
        remote_filter=True,
        pagination=True,
    )

    def __init__(self, company: ProviderConfig):
        self.company = company

    @property
    def provider_name(self) -> str:
        return "arbeitnow"

    @property
    def capabilities(self) -> ProviderCapabilities:
        return self.CAPABILITIES

    def search_jobs(self, query: JobSearchQuery) -> list[Job]:
        country = self._country_for(query)
        if country is None:
            return []

        response = requests.get(
            self.ENDPOINTS[country],
            params={"page": query.page},
            timeout=30,
        )
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, Mapping):
            raise ProviderPayloadError("Arbeitnow returned an invalid response object.")
        raw_jobs = payload.get("data", [])
        if not isinstance(raw_jobs, list):
            raise ProviderPayloadError("Arbeitnow returned an invalid jobs collection.")

        return [
            self.normalize_job(item)
            for item in raw_jobs
            if isinstance(item, Mapping) and self._matches(item, query, country)
        ][: query.page_size]

    def normalize_job(self, raw_job: Mapping[str, Any]) -> Job:
        url = raw_job.get("url")
        if not url:
            raise ProviderPayloadError("Arbeitnow job is missing an application URL.")

        tags = raw_job.get("tags") if isinstance(raw_job.get("tags"), list) else []
        description = html.unescape(re.sub(r"<[^>]+>", " ", str(raw_job.get("description") or "")))
        return Job(
            title=str(raw_job.get("title") or "Unknown"),
            company=str(raw_job.get("company_name") or "Unknown"),
            location=str(
                raw_job.get("location") or ("Remote" if raw_job.get("remote") else "Unknown")
            ),
            description=" ".join(description.split()),
            required_skills=[Skill(name=str(tag), category="Provider tag") for tag in tags],
            experience_level=ExperienceLevel.ENTRY,
            employment_type=self._employment_type(raw_job),
            source=JobSource.ARBEITNOW,
            source_name=self.provider_name,
            external_id=str(raw_job.get("slug") or url),
            source_url=url,
            url=url,
        )

    @classmethod
    def _country_for(cls, query: JobSearchQuery) -> str | None:
        if query.country in cls.ENDPOINTS:
            return query.country
        location = query.location.casefold()
        if location in {"germany", "deutschland"}:
            return "de"
        if location in {"uk", "united kingdom", "great britain"}:
            return "gb"
        return None

    @staticmethod
    def _matches(raw_job: Mapping[str, Any], query: JobSearchQuery, country: str) -> bool:
        searchable = " ".join(
            [
                str(raw_job.get("title") or ""),
                " ".join(str(tag) for tag in raw_job.get("tags", []) if tag),
            ]
        ).casefold()
        role_terms = re.findall(r"[\w+#.-]+", query.role.casefold())
        if role_terms and not all(term in searchable for term in role_terms):
            return False
        if query.remote_only and not raw_job.get("remote"):
            return False

        generic_locations = {
            "de": {"germany", "deutschland"},
            "gb": {"uk", "united kingdom", "great britain"},
        }
        requested_location = query.location.casefold()
        if requested_location in generic_locations[country]:
            return True
        if requested_location == "remote":
            return bool(raw_job.get("remote"))
        return requested_location in str(raw_job.get("location") or "").casefold()

    @staticmethod
    def _employment_type(raw_job: Mapping[str, Any]) -> EmploymentType:
        values = " ".join(str(value) for value in raw_job.get("job_types", []) if value).casefold()
        if "part" in values:
            return EmploymentType.PART_TIME
        if "intern" in values:
            return EmploymentType.INTERNSHIP
        if "contract" in values or "freelance" in values:
            return EmploymentType.CONTRACT
        return EmploymentType.FULL_TIME

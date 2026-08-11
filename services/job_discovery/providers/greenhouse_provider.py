"""Read-only Greenhouse job-board provider."""

import html
import re
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


class GreenhouseProvider(BaseProvider):
    """Provider for one configured public Greenhouse job board."""

    ENDPOINT = "https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs"
    CAPABILITIES = ProviderCapabilities(
        location_filter=True,
        remote_filter=True,
        pagination=True,
    )
    ROLE_MODIFIERS = {
        "associate",
        "director",
        "executive",
        "head",
        "junior",
        "lead",
        "manager",
        "principal",
        "senior",
        "specialist",
    }

    def __init__(self, company: ProviderConfig) -> None:
        self.company = company
        self.board_token = company["board_token"]

    @property
    def provider_name(self) -> str:
        return f"greenhouse:{self.company['id']}"

    @property
    def capabilities(self) -> ProviderCapabilities:
        return self.CAPABILITIES

    def search_jobs(self, query: JobSearchQuery) -> list[Job]:
        response = requests.get(
            self.ENDPOINT.format(board_token=self.board_token),
            params={"content": "true"},
            timeout=30,
        )
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, Mapping):
            raise ProviderPayloadError("Greenhouse returned an invalid response object.")
        raw_jobs = payload.get("jobs", [])
        if not isinstance(raw_jobs, list):
            raise ProviderPayloadError("Greenhouse returned an invalid jobs collection.")

        matching = [
            self.normalize_job(item)
            for item in raw_jobs
            if isinstance(item, Mapping) and self._matches(item, query)
        ]
        start = (query.page - 1) * query.page_size
        return matching[start : start + query.page_size]

    def normalize_job(self, raw_job: Mapping[str, Any]) -> Job:
        url = raw_job.get("absolute_url")
        if not url:
            raise ProviderPayloadError("Greenhouse job is missing a listing URL.")
        location = raw_job.get("location")
        location_name = location.get("name") if isinstance(location, Mapping) else None
        content = html.unescape(str(raw_job.get("content") or ""))
        description = html.unescape(re.sub(r"<[^>]+>", " ", content))
        title = str(raw_job.get("title") or "Unknown")

        return Job(
            title=title,
            company=self.company["name"],
            location=str(location_name or "Unknown"),
            description=" ".join(description.split()),
            required_skills=[],
            experience_level=self._experience_level(title),
            employment_type=(
                EmploymentType.REMOTE
                if "remote" in str(location_name).casefold()
                else EmploymentType.FULL_TIME
            ),
            source=JobSource.GREENHOUSE,
            source_name="Greenhouse",
            external_id=str(raw_job.get("id") or url),
            source_url=str(url),
            url=str(url),
        )

    @classmethod
    def _matches(cls, raw_job: Mapping[str, Any], query: JobSearchQuery) -> bool:
        title = str(raw_job.get("title") or "").casefold()
        role_terms = [
            term
            for term in re.findall(r"[\w+#.-]+", query.role.casefold())
            if term not in cls.ROLE_MODIFIERS
        ] or re.findall(r"[\w+#.-]+", query.role.casefold())
        if role_terms and not all(term in title for term in role_terms):
            return False

        location = raw_job.get("location")
        location_name = (
            str(location.get("name") or "") if isinstance(location, Mapping) else ""
        ).casefold()
        if query.remote_only or query.location.casefold() == "remote":
            return "remote" in location_name
        return query.location.casefold() in location_name

    @staticmethod
    def _experience_level(title: str) -> ExperienceLevel:
        normalized = title.casefold()
        if "principal" in normalized:
            return ExperienceLevel.PRINCIPAL
        if "lead" in normalized or "director" in normalized or "head" in normalized:
            return ExperienceLevel.LEAD
        if "senior" in normalized or "sr." in normalized:
            return ExperienceLevel.SENIOR
        return ExperienceLevel.ENTRY

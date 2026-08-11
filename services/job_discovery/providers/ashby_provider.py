"""Read-only Ashby job-board provider."""

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


class AshbyProvider(BaseProvider):
    """Provider for one configured public Ashby job board."""

    ENDPOINT = "https://api.ashbyhq.com/posting-api/job-board/{job_board_name}"
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
        "sr.",
    }

    def __init__(self, company: ProviderConfig) -> None:
        self.company = company
        self.job_board_name = company["job_board_name"]
        self.endpoint = self.ENDPOINT.format(job_board_name=self.job_board_name)

    @property
    def provider_name(self) -> str:
        return f"ashby:{self.company['id']}"

    @property
    def capabilities(self) -> ProviderCapabilities:
        return self.CAPABILITIES

    def search_jobs(self, query: JobSearchQuery) -> list[Job]:
        response = requests.get(
            self.endpoint,
            params={"includeCompensation": "false"},
            timeout=30,
        )
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, Mapping):
            raise ProviderPayloadError("Ashby returned an invalid response object.")
        raw_jobs = payload.get("jobs", [])
        if not isinstance(raw_jobs, list):
            raise ProviderPayloadError("Ashby returned an invalid jobs collection.")

        matching = [
            self.normalize_job(item)
            for item in raw_jobs
            if isinstance(item, Mapping)
            and item.get("isListed") is True
            and self._matches(item, query)
        ]
        start = (query.page - 1) * query.page_size
        return matching[start : start + query.page_size]

    def normalize_job(self, raw_job: Mapping[str, Any]) -> Job:
        url = raw_job.get("jobUrl")
        if not url:
            raise ProviderPayloadError("Ashby job is missing a listing URL.")
        title = str(raw_job.get("title") or "Unknown")
        location = str(raw_job.get("location") or "Unknown").strip()
        description = raw_job.get("descriptionPlain")
        if not description:
            description_html = html.unescape(str(raw_job.get("descriptionHtml") or ""))
            description = re.sub(r"<[^>]+>", " ", description_html)

        return Job(
            title=title,
            company=self.company["name"],
            location=location,
            description=" ".join(str(description).split()),
            required_skills=[],
            experience_level=self._experience_level(title),
            employment_type=self._employment_type(raw_job),
            source=JobSource.ASHBY,
            source_name="Ashby",
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

        location_names = [str(raw_job.get("location") or "")]
        countries = [cls._country(raw_job.get("address"))]
        secondary = raw_job.get("secondaryLocations")
        if isinstance(secondary, list):
            for location in secondary:
                if isinstance(location, Mapping):
                    location_names.append(str(location.get("location") or ""))
                    countries.append(cls._country(location.get("address")))

        location_text = " ".join(location_names).casefold()
        if query.remote_only or query.location.casefold() == "remote":
            return (
                raw_job.get("isRemote") is True
                or str(raw_job.get("workplaceType") or "").casefold() == "remote"
                or "remote" in location_text
            )

        requested = query.location.casefold()
        if requested in location_text:
            return True
        return requested == "india" and any(country in {"india", "in"} for country in countries)

    @staticmethod
    def _country(address: Any) -> str:
        if not isinstance(address, Mapping):
            return ""
        postal = address.get("postalAddress")
        if not isinstance(postal, Mapping):
            return ""
        return str(postal.get("addressCountry") or "").casefold()

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

    @staticmethod
    def _employment_type(raw_job: Mapping[str, Any]) -> EmploymentType:
        if (
            raw_job.get("isRemote") is True
            or str(raw_job.get("workplaceType") or "").casefold() == "remote"
        ):
            return EmploymentType.REMOTE
        value = str(raw_job.get("employmentType") or "").casefold()
        if value == "parttime":
            return EmploymentType.PART_TIME
        if value == "intern":
            return EmploymentType.INTERNSHIP
        if value in {"contract", "temporary"}:
            return EmploymentType.CONTRACT
        return EmploymentType.FULL_TIME

"""Read-only Lever postings provider."""

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


class LeverProvider(BaseProvider):
    """Provider for one configured public Lever careers site."""

    ENDPOINT = "https://api.lever.co/v0/postings/{site_name}"
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
        self.site_name = company["site_name"]
        self.endpoint = self.ENDPOINT.format(site_name=self.site_name)

    @property
    def provider_name(self) -> str:
        return f"lever:{self.company['id']}"

    @property
    def capabilities(self) -> ProviderCapabilities:
        return self.CAPABILITIES

    def search_jobs(self, query: JobSearchQuery) -> list[Job]:
        response = requests.get(
            self.endpoint,
            params={"mode": "json"},
            timeout=30,
        )
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, list):
            raise ProviderPayloadError("Lever returned an invalid jobs collection.")

        matching = [
            self.normalize_job(item)
            for item in payload
            if isinstance(item, Mapping) and self._matches(item, query)
        ]
        start = (query.page - 1) * query.page_size
        return matching[start : start + query.page_size]

    def normalize_job(self, raw_job: Mapping[str, Any]) -> Job:
        url = raw_job.get("hostedUrl")
        if not url:
            raise ProviderPayloadError("Lever job is missing a listing URL.")
        title = str(raw_job.get("text") or "Unknown")
        categories = raw_job.get("categories")
        location = (
            str(categories.get("location") or "Unknown")
            if isinstance(categories, Mapping)
            else "Unknown"
        )
        description_parts = [
            str(raw_job.get("descriptionPlain") or ""),
            self._list_text(raw_job.get("lists")),
            str(raw_job.get("additionalPlain") or ""),
        ]

        return Job(
            title=title,
            company=self.company["name"],
            location=location,
            description=" ".join(" ".join(description_parts).split()),
            required_skills=[],
            experience_level=self._experience_level(title),
            employment_type=self._employment_type(raw_job),
            source=JobSource.LEVER,
            source_name="Lever",
            external_id=str(raw_job.get("id") or url),
            source_url=str(url),
            url=str(url),
        )

    @classmethod
    def _matches(cls, raw_job: Mapping[str, Any], query: JobSearchQuery) -> bool:
        title = str(raw_job.get("text") or "").casefold()
        role_terms = [
            term
            for term in re.findall(r"[\w+#.-]+", query.role.casefold())
            if term not in cls.ROLE_MODIFIERS
        ] or re.findall(r"[\w+#.-]+", query.role.casefold())
        if role_terms and not all(term in title for term in role_terms):
            return False

        categories = raw_job.get("categories")
        if not isinstance(categories, Mapping):
            return False
        locations = [str(categories.get("location") or "")]
        all_locations = categories.get("allLocations")
        if isinstance(all_locations, list):
            locations.extend(str(location) for location in all_locations)
        location_text = " ".join(locations).casefold()

        if query.remote_only or query.location.casefold() == "remote":
            return (
                str(raw_job.get("workplaceType") or "").casefold() == "remote"
                or "remote" in location_text
            )
        requested = query.location.casefold()
        if requested in location_text:
            return True
        return requested == "india" and str(raw_job.get("country") or "").casefold() == "in"

    @staticmethod
    def _list_text(lists: Any) -> str:
        if not isinstance(lists, list):
            return ""
        parts = []
        for section in lists:
            if not isinstance(section, Mapping):
                continue
            parts.append(str(section.get("text") or ""))
            content = html.unescape(str(section.get("content") or ""))
            parts.append(re.sub(r"<[^>]+>", " ", content))
        return " ".join(parts)

    @staticmethod
    def _experience_level(title: str) -> ExperienceLevel:
        normalized = title.casefold()
        if "principal" in normalized:
            return ExperienceLevel.PRINCIPAL
        if any(term in normalized for term in ("lead", "director", "head", "vice president")):
            return ExperienceLevel.LEAD
        if "senior" in normalized or "sr." in normalized:
            return ExperienceLevel.SENIOR
        return ExperienceLevel.ENTRY

    @staticmethod
    def _employment_type(raw_job: Mapping[str, Any]) -> EmploymentType:
        if str(raw_job.get("workplaceType") or "").casefold() == "remote":
            return EmploymentType.REMOTE
        categories = raw_job.get("categories")
        commitment = (
            str(categories.get("commitment") or "").casefold()
            if isinstance(categories, Mapping)
            else ""
        )
        if "part time" in commitment or "part-time" in commitment:
            return EmploymentType.PART_TIME
        if "intern" in commitment or "apprentice" in commitment:
            return EmploymentType.INTERNSHIP
        if "contract" in commitment or "temporary" in commitment or "fixed term" in commitment:
            return EmploymentType.CONTRACT
        return EmploymentType.FULL_TIME

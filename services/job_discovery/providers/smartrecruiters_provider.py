"""Read-only SmartRecruiters company-posting provider."""

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


class SmartRecruitersProvider(BaseProvider):
    """Provider for one configured public SmartRecruiters company feed."""

    ENDPOINT = "https://api.smartrecruiters.com/v1/companies/{company}/postings"
    CAPABILITIES = ProviderCapabilities(
        location_filter=True,
        country_filter=True,
        remote_filter=True,
        pagination=True,
        job_details=True,
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
        self.company_identifier = company["company_identifier"]
        self.endpoint = self.ENDPOINT.format(company=self.company_identifier)

    @property
    def provider_name(self) -> str:
        return f"smartrecruiters:{self.company['id']}"

    @property
    def capabilities(self) -> ProviderCapabilities:
        return self.CAPABILITIES

    def search_jobs(self, query: JobSearchQuery) -> list[Job]:
        response = requests.get(
            self.endpoint,
            params={
                "q": query.role,
                "country": query.country or self.company.get("country"),
                "destination": "PUBLIC",
                "limit": query.page_size,
                "offset": (query.page - 1) * query.page_size,
            },
            timeout=30,
        )
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, Mapping):
            raise ProviderPayloadError("SmartRecruiters returned an invalid response object.")
        raw_jobs = payload.get("content", [])
        if not isinstance(raw_jobs, list):
            raise ProviderPayloadError("SmartRecruiters returned an invalid jobs collection.")

        jobs = []
        for item in raw_jobs:
            if not isinstance(item, Mapping) or not self._matches(item, query):
                continue
            posting_id = item.get("id")
            if not posting_id:
                continue
            detail_response = requests.get(
                f"{self.endpoint}/{posting_id}",
                timeout=30,
            )
            detail_response.raise_for_status()
            detail = detail_response.json()
            if not isinstance(detail, Mapping):
                raise ProviderPayloadError("SmartRecruiters returned an invalid job object.")
            jobs.append(self.normalize_job(detail))
        return jobs

    def normalize_job(self, raw_job: Mapping[str, Any]) -> Job:
        url = raw_job.get("jobAdUrl") or raw_job.get("applyUrl")
        if not url:
            raise ProviderPayloadError("SmartRecruiters job is missing a listing URL.")
        title = str(raw_job.get("name") or "Unknown")
        location = raw_job.get("location")
        location_name = (
            str(location.get("fullLocation") or location.get("city") or "Unknown")
            if isinstance(location, Mapping)
            else "Unknown"
        )
        sections = raw_job.get("jobAd")
        sections = sections.get("sections") if isinstance(sections, Mapping) else None
        description_parts = []
        if isinstance(sections, Mapping):
            for key in ("jobDescription", "qualifications", "additionalInformation"):
                section = sections.get(key)
                if isinstance(section, Mapping) and section.get("text"):
                    description_parts.append(str(section["text"]))
        description = html.unescape(re.sub(r"<[^>]+>", " ", " ".join(description_parts)))

        return Job(
            title=title,
            company=self.company["name"],
            location=location_name,
            description=" ".join(description.split()),
            required_skills=[],
            experience_level=self._experience_level(raw_job),
            employment_type=self._employment_type(raw_job),
            source=JobSource.SMARTRECRUITERS,
            source_name="SmartRecruiters",
            external_id=str(raw_job.get("uuid") or raw_job.get("id") or url),
            source_url=str(url),
            url=str(url),
        )

    @classmethod
    def _matches(cls, raw_job: Mapping[str, Any], query: JobSearchQuery) -> bool:
        title = str(raw_job.get("name") or "").casefold()
        role_terms = [
            term
            for term in re.findall(r"[\w+#.-]+", query.role.casefold())
            if term not in cls.ROLE_MODIFIERS
        ] or re.findall(r"[\w+#.-]+", query.role.casefold())
        if role_terms and not all(term in title for term in role_terms):
            return False

        location = raw_job.get("location")
        if not isinstance(location, Mapping):
            return False
        location_name = str(location.get("fullLocation") or location.get("city") or "").casefold()
        if query.remote_only or query.location.casefold() == "remote":
            return location.get("remote") is True or "remote" in location_name
        requested = query.location.casefold()
        if requested in location_name:
            return True
        return requested == "india" and str(location.get("country") or "").casefold() == "in"

    @staticmethod
    def _experience_level(raw_job: Mapping[str, Any]) -> ExperienceLevel:
        level = raw_job.get("experienceLevel")
        value = str(level.get("id") or "").casefold() if isinstance(level, Mapping) else ""
        if "executive" in value or "director" in value:
            return ExperienceLevel.LEAD
        if "mid_senior" in value:
            return ExperienceLevel.SENIOR
        if "associate" in value:
            return ExperienceLevel.MID
        return ExperienceLevel.ENTRY

    @staticmethod
    def _employment_type(raw_job: Mapping[str, Any]) -> EmploymentType:
        location = raw_job.get("location")
        if isinstance(location, Mapping) and location.get("remote") is True:
            return EmploymentType.REMOTE
        employment = raw_job.get("typeOfEmployment")
        value = str(employment.get("id") or "").casefold() if isinstance(employment, Mapping) else ""
        if "part" in value:
            return EmploymentType.PART_TIME
        if "intern" in value:
            return EmploymentType.INTERNSHIP
        if "contract" in value or "temporary" in value:
            return EmploymentType.CONTRACT
        return EmploymentType.FULL_TIME

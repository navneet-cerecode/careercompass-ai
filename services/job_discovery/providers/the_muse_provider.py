"""The Muse provider with strict local relevance filtering."""

import html
import re
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


class TheMuseProvider(BaseProvider):
    """Credential-gated adapter for The Muse public jobs API."""

    ENDPOINT = "https://www.themuse.com/api/public/jobs"
    CAPABILITIES = ProviderCapabilities(
        location_filter=True,
        remote_filter=True,
        pagination=True,
    )
    CATEGORY_RULES = (
        ("Accounting and Finance", ("accounting", "accountant", "finance")),
        ("Customer Service", ("customer service", "customer support")),
        ("Account Management", ("account", "customer success")),
        ("Administration and Office", ("administr", "reception", "office assistant")),
        ("Advertising and Marketing", ("marketing", "advertising")),
        ("Animal Care", ("animal", "pet care", "veterinar")),
        ("Arts", ("artist", "curator", "museum")),
        ("Cleaning and Facilities", ("cleaning", "custod", "facilit", "janitor")),
        ("Construction", ("construction", "carpenter", "plumber", "electrician")),
        ("Entertainment and Travel Services", ("entertainment", "travel", "tourism")),
        ("Farming and Outdoors", ("agriculture", "farm", "horticulture")),
        ("Transportation and Logistics", ("logistics", "transport", "supply chain")),
        ("Business Operations", ("operation", "procurement", "business analyst")),
        (
            "Food and Hospitality Services",
            ("hospitality", "restaurant", "chef", "food", "barista", "sommelier"),
        ),
        ("Healthcare", ("health", "medical", "pharmacy", "patient care")),
        ("Nurses", ("nurse", "nursing")),
        ("Human Resources and Recruitment", ("human resources", "recruit", "talent")),
        ("Legal Services", ("legal", "lawyer", "attorney")),
        (
            "Installation, Maintenance, and Repairs",
            ("installation", "installer", "maintenance", "repair", "technician"),
        ),
        ("Manufacturing and Warehouse", ("manufactur", "warehouse")),
        ("Media, PR, and Communications", ("communications", "media", "public relations")),
        ("Mental Health", ("mental health", "therapist", "counselor", "psychologist")),
        ("Personal Care and Services", ("beautician", "personal care", "stylist")),
        ("Project Management", ("project",)),
        ("Product Management", ("product",)),
        ("Protective Services", ("firefighter", "police", "security guard")),
        ("Real Estate", ("property", "real estate")),
        ("Retail", ("retail",)),
        ("Sales", ("sales",)),
        ("Education", ("education", "teacher", "teaching")),
        ("Social Services", ("community outreach", "social worker")),
        ("Sports, Fitness, and Recreation", ("fitness", "sports", "trainer")),
        ("Writing and Editing", ("writer", "writing", "editor")),
        ("Design and UX", ("design", "ux", "user experience")),
        ("Data and Analytics", ("data", "analytics")),
        (
            "Science and Engineering",
            ("mechanical", "civil engineer", "electrical engineer", "chemical engineer"),
        ),
        (
            "Software Engineering",
            ("software", "developer", "backend", "frontend", "full stack", "ai engineer"),
        ),
    )
    ROLE_MODIFIERS = {
        "associate",
        "analyst",
        "coordinator",
        "director",
        "executive",
        "engineer",
        "head",
        "junior",
        "lead",
        "manager",
        "senior",
        "specialist",
    }

    def __init__(
        self,
        company: ProviderConfig,
        api_key: str | None = None,
    ) -> None:
        self.company = company
        if api_key is None and settings.the_muse_api_key is not None:
            api_key = settings.the_muse_api_key.get_secret_value()
        if not api_key:
            raise ProviderConfigurationError("THE_MUSE_API_KEY is required.")
        self.api_key = api_key

    @property
    def provider_name(self) -> str:
        return "the_muse"

    @property
    def capabilities(self) -> ProviderCapabilities:
        return self.CAPABILITIES

    def search_jobs(self, query: JobSearchQuery) -> list[Job]:
        category = self._category_for(query.role)
        if category is None:
            return []

        response = requests.get(
            self.ENDPOINT,
            params={
                "api_key": self.api_key,
                "category": category,
                "location": query.location,
                "page": query.page - 1,
            },
            timeout=30,
        )
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, Mapping):
            raise ProviderPayloadError("The Muse returned an invalid response object.")
        raw_jobs = payload.get("results", [])
        if not isinstance(raw_jobs, list):
            raise ProviderPayloadError("The Muse returned an invalid jobs collection.")
        return [
            self.normalize_job(item)
            for item in raw_jobs
            if isinstance(item, Mapping) and self._matches(item, query)
        ][: query.page_size]

    def normalize_job(self, raw_job: Mapping[str, Any]) -> Job:
        refs = raw_job.get("refs")
        url = refs.get("landing_page") if isinstance(refs, Mapping) else None
        if not url:
            raise ProviderPayloadError("The Muse job is missing a listing URL.")

        description = html.unescape(re.sub(r"<[^>]+>", " ", str(raw_job.get("contents") or "")))
        locations = self._names(raw_job.get("locations"))
        company = raw_job.get("company")
        company_name = company.get("name") if isinstance(company, Mapping) else None
        return Job(
            title=str(raw_job.get("name") or "Unknown"),
            company=str(company_name or "Unknown"),
            location=", ".join(locations) or "Unknown",
            description=" ".join(description.split()),
            required_skills=[],
            experience_level=self._experience_level(raw_job),
            employment_type=(
                EmploymentType.REMOTE
                if locations and all("remote" in location.casefold() for location in locations)
                else EmploymentType.FULL_TIME
            ),
            source=JobSource.THE_MUSE,
            source_name=self.provider_name,
            external_id=str(raw_job.get("id") or url),
            source_url=str(url),
            url=str(url),
        )

    @classmethod
    def _category_for(cls, role: str) -> str | None:
        normalized = role.casefold()
        return next(
            (
                category
                for category, terms in cls.CATEGORY_RULES
                if any(term in normalized for term in terms)
            ),
            None,
        )

    @classmethod
    def _matches(cls, raw_job: Mapping[str, Any], query: JobSearchQuery) -> bool:
        title = str(raw_job.get("name") or "").casefold()
        role_terms = [
            term
            for term in re.findall(r"[\w+#.-]+", query.role.casefold())
            if term not in cls.ROLE_MODIFIERS
        ] or re.findall(r"[\w+#.-]+", query.role.casefold())
        if role_terms and not any(term in title for term in role_terms):
            return False

        locations = cls._names(raw_job.get("locations"))
        if query.remote_only or query.location.casefold() == "remote":
            return any("remote" in location.casefold() for location in locations)
        requested = query.location.casefold()
        return any(requested in location.casefold() for location in locations)

    @staticmethod
    def _names(value: Any) -> list[str]:
        if not isinstance(value, list):
            return []
        return [
            str(item["name"])
            for item in value
            if isinstance(item, Mapping) and item.get("name")
        ]

    @classmethod
    def _experience_level(cls, raw_job: Mapping[str, Any]) -> ExperienceLevel:
        levels = " ".join(cls._names(raw_job.get("levels"))).casefold()
        if "senior" in levels:
            return ExperienceLevel.SENIOR
        if "management" in levels:
            return ExperienceLevel.LEAD
        if "mid" in levels:
            return ExperienceLevel.MID
        return ExperienceLevel.ENTRY

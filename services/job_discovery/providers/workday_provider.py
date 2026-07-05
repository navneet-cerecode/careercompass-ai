"""
Workday Job Provider.

Fetches jobs from Workday Career Sites.
"""

import requests

from models.enums import (
    EmploymentType,
    ExperienceLevel,
    JobSource,
)

from models.job import Job

from .base_provider import BaseProvider


class WorkdayProvider(BaseProvider):
    """
    Provider for Workday career portals.
    """

    def __init__(self, company: dict):

        self.company = company
        self.api_url = company["api_url"]

    def search(
        self,
        role: str,
        location: str,
    ) -> list[Job]:

        response = requests.post(
            self.api_url,
            json={
                "limit": 20,
                "offset": 0,
                "searchText": role,
            },
            timeout=30,
        )

        response.raise_for_status()

        data = response.json()

        jobs = []

        for item in data.get("jobPostings", []):

            jobs.append(
                Job(
                    title=item["title"],
                    company=self.company["name"],
                    location=item.get(
                        "locationsText",
                        "Unknown",
                    ),
                    description="",
                    required_skills=[],
                    experience_level=ExperienceLevel.ENTRY,
                    employment_type=EmploymentType.FULL_TIME,
                    source=JobSource.OTHER,

                    # ✅ FIXED URL
                    url=(
                        self.company["careers_url"]
                        + item["externalPath"]
                    ),
                )
            )

        return jobs
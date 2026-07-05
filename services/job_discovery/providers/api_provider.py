"""
API Provider.

Fetches jobs from the JSearch API.
"""

import os

import requests
from dotenv import load_dotenv

from models.enums import (
    EmploymentType,
    ExperienceLevel,
    JobSource,
)

from models.job import Job

from services.job_discovery.providers.base_provider import (
    BaseProvider,
)

load_dotenv()


class APIProvider(BaseProvider):
    """
    Generic provider backed by JSearch.
    """

    BASE_URL = "https://jsearch.p.rapidapi.com/search-v2"

    def __init__(
        self,
        company: dict,
    ):

        self.company = company

        self.api_key = os.getenv(
            "RAPIDAPI_KEY"
        )

        if not self.api_key:

            raise RuntimeError(
                "Missing RAPIDAPI_KEY."
            )

    def search(
        self,
        role: str,
        location: str,
    ) -> list[Job]:

        headers = {

            "X-RapidAPI-Key": self.api_key,

            "X-RapidAPI-Host": "jsearch.p.rapidapi.com",

        }

        params = {

            "query": f"{role} jobs in {location}",

            "page": "1",

            "num_pages": "1",

            "country": "in",

            "date_posted": "all",

        }

        response = requests.get(

            self.BASE_URL,

            headers=headers,

            params=params,

            timeout=30,

        )

        response.raise_for_status()

        payload = response.json()

        jobs = []

        for item in payload.get(
            "data",
            {},
        ).get(
            "jobs",
            [],
        ):

            jobs.append(

                Job(

                    title=item.get(
                        "job_title",
                        "Unknown",
                    ),

                    company=item.get(
                        "employer_name",
                        "Unknown",
                    ),

                    location=item.get(
                        "job_location",
                        "Unknown",
                    ),

                    description=item.get(
                        "job_description",
                        "",
                    ),

                    required_skills=[],

                    experience_level=ExperienceLevel.ENTRY,

                    employment_type=EmploymentType.FULL_TIME,

                    source=JobSource.OTHER,

                    url=item.get(
                        "job_apply_link",
                        "",
                    ),

                )

            )

        return jobs
"""
Deduplicate Stage.

Removes duplicate jobs.
"""

from models.job import Job
from services.job_discovery.fingerprint import job_fingerprint


class DeduplicateStage:
    def process(
        self,
        jobs: list[Job],
    ) -> list[Job]:

        seen = set()

        unique_jobs = []

        for job in jobs:
            key = job_fingerprint(job)

            if key in seen:
                continue

            seen.add(key)

            unique_jobs.append(job)

        return unique_jobs

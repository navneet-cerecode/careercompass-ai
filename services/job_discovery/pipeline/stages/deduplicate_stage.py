"""
Deduplicate Stage.

Removes duplicate jobs.
"""

from models.job import Job


class DeduplicateStage:
    def process(
        self,
        jobs: list[Job],
    ) -> list[Job]:

        seen = set()

        unique_jobs = []

        for job in jobs:
            key = (
                job.company.lower(),
                job.title.lower(),
                job.location.lower(),
            )

            if key in seen:
                continue

            seen.add(key)

            unique_jobs.append(job)

        return unique_jobs

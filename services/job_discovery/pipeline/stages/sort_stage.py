"""
Sort Stage.

Sorts jobs alphabetically.
"""

from models.job import Job


class SortStage:

    def process(
        self,
        jobs: list[Job],
    ) -> list[Job]:

        return sorted(

            jobs,

            key=lambda job: (
                job.company.lower(),
                job.title.lower(),
            ),
        )
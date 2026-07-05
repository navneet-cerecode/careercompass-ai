"""
Job Discovery Service.

Coordinates all providers and processes jobs
through the discovery pipeline.
"""

from models.job import Job

from services.job_discovery.pipeline.job_pipeline import (
    JobPipeline,
)

from services.job_discovery.pipeline.stages.deduplicate_stage import (
    DeduplicateStage,
)

from services.job_discovery.pipeline.stages.sort_stage import (
    SortStage,
)

from services.job_discovery.providers.companies import (
    COMPANIES,
)

from services.job_discovery.providers.provider_factory import (
    ProviderFactory,
)


class JobDiscoveryService:

    def __init__(self):

        self.providers = []

        for company in COMPANIES:

            if not company.get(
                "enabled",
                True,
            ):
                continue

            self.providers.append(

                ProviderFactory.create(
                    company
                )

            )

        self.pipeline = JobPipeline()

        self.pipeline.add_stage(
            DeduplicateStage()
        )

        self.pipeline.add_stage(
            SortStage()
        )

    def discover(
        self,
        role: str,
        location: str,
    ) -> list[Job]:

        jobs = []

        for provider in self.providers:

            try:

                jobs.extend(

                    provider.search(
                        role,
                        location,
                    )

                )
            except Exception as e:

              import traceback

              print("\n" + "=" * 60)
              print(f"Provider failed: {provider.company['name']}")
              traceback.print_exc()
              print("=" * 60 + "\n")

              raise

        return self.pipeline.process(
            jobs
        )
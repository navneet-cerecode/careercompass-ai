"""Coordinate job providers and the normalization pipeline."""

import logging
from collections.abc import Iterable
from dataclasses import dataclass

from models.job import Job

from services.job_discovery.pipeline.job_pipeline import JobPipeline
from services.job_discovery.pipeline.stages.deduplicate_stage import (
    DeduplicateStage,
)
from services.job_discovery.pipeline.stages.sort_stage import SortStage
from services.job_discovery.providers.base_provider import BaseProvider
from services.job_discovery.providers.companies import COMPANIES
from services.job_discovery.providers.contracts import JobSearchQuery
from services.job_discovery.providers.provider_factory import ProviderFactory

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ProviderFailure:
    provider_name: str
    error_type: str


@dataclass(frozen=True)
class JobDiscoveryResult:
    jobs: tuple[Job, ...]
    failures: tuple[ProviderFailure, ...]
    providers_attempted: int
    providers_succeeded: int


class JobDiscoveryService:
    """Search configured providers through one typed orchestration boundary."""

    def __init__(
        self,
        providers: Iterable[BaseProvider] | None = None,
        pipeline: JobPipeline | None = None,
    ):
        if providers is None:
            self.providers, self.initialization_failures = self._build_configured_providers()
        else:
            self.providers = list(providers)
            self.initialization_failures = []
        self.pipeline = pipeline or self._build_default_pipeline()

    @staticmethod
    def _build_configured_providers() -> tuple[list[BaseProvider], list[ProviderFailure]]:
        providers = []
        failures = []
        for company in COMPANIES:
            if not company.get("enabled", True):
                continue
            try:
                providers.append(ProviderFactory.create(company))
            except Exception as error:
                provider_name = company.get("id") or company["name"]
                logger.exception("Provider initialization failed: %s", provider_name)
                failures.append(
                    ProviderFailure(
                        provider_name=provider_name,
                        error_type=type(error).__name__,
                    )
                )
        return providers, failures

    @staticmethod
    def _build_default_pipeline() -> JobPipeline:
        pipeline = JobPipeline()
        pipeline.add_stage(DeduplicateStage())
        pipeline.add_stage(SortStage())
        return pipeline

    def discover(
        self,
        role: str,
        location: str,
    ) -> list[Job]:
        """Compatibility entry point for the existing facade and graph."""
        return self.discover_jobs(
            JobSearchQuery(
                role=role,
                location=location,
            )
        )

    def discover_jobs(
        self,
        query: JobSearchQuery,
    ) -> list[Job]:
        """Compatibility method returning jobs from every successful provider."""
        return list(self.discover_jobs_with_status(query).jobs)

    def discover_jobs_with_status(
        self,
        query: JobSearchQuery,
    ) -> JobDiscoveryResult:
        """Search all providers and retain bounded partial-failure metadata."""
        jobs = []
        failures = list(self.initialization_failures)
        providers_succeeded = 0

        for provider in self.providers:
            try:
                jobs.extend(provider.search_jobs(query))
                providers_succeeded += 1
            except Exception as error:
                logger.exception(
                    "Provider search failed: %s",
                    provider.provider_name,
                )
                failures.append(
                    ProviderFailure(
                        provider_name=provider.provider_name,
                        error_type=type(error).__name__,
                    )
                )

        processed_jobs = self.pipeline.process(jobs)
        return JobDiscoveryResult(
            jobs=tuple(processed_jobs),
            failures=tuple(failures),
            providers_attempted=len(self.providers) + len(self.initialization_failures),
            providers_succeeded=providers_succeeded,
        )

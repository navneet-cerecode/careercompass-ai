"""Coordinate job providers and the normalization pipeline."""

import logging
from collections.abc import Iterable

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


class JobDiscoveryService:
    """Search configured providers through one typed orchestration boundary."""

    def __init__(
        self,
        providers: Iterable[BaseProvider] | None = None,
        pipeline: JobPipeline | None = None,
    ):
        self.providers = (
            list(providers) if providers is not None else self._build_configured_providers()
        )
        self.pipeline = pipeline or self._build_default_pipeline()

    @staticmethod
    def _build_configured_providers() -> list[BaseProvider]:
        providers = []
        for company in COMPANIES:
            if not company.get("enabled", True):
                continue
            providers.append(ProviderFactory.create(company))
        return providers

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
        """Search every configured provider with one typed query."""
        jobs = []
        for provider in self.providers:
            try:
                jobs.extend(provider.search_jobs(query))
            except Exception:
                logger.exception(
                    "Provider search failed: %s",
                    provider.provider_name,
                )
                raise

        return self.pipeline.process(jobs)

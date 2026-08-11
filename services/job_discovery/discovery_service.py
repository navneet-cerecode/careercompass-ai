"""Coordinate job providers and the normalization pipeline."""

import logging
import time
from collections.abc import Iterable
from dataclasses import dataclass

import requests

from models.job_discovery_task import ProviderFailureCode
from models.job import Job

from services.job_discovery.pipeline.job_pipeline import JobPipeline
from services.job_discovery.pipeline.stages.deduplicate_stage import (
    DeduplicateStage,
)
from services.job_discovery.pipeline.stages.sort_stage import SortStage
from services.job_discovery.providers.base_provider import BaseProvider
from services.job_discovery.providers.companies import COMPANIES
from services.job_discovery.providers.contracts import JobSearchQuery
from services.job_discovery.providers.errors import (
    ProviderConfigurationError,
    ProviderPayloadError,
)
from services.job_discovery.providers.provider_factory import ProviderFactory

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ProviderFailure:
    provider_name: str
    error_type: str
    code: ProviderFailureCode = ProviderFailureCode.FAILED
    attempts: int = 1


@dataclass(frozen=True)
class JobDiscoveryResult:
    jobs: tuple[Job, ...]
    failures: tuple[ProviderFailure, ...]
    providers_attempted: int
    providers_succeeded: int


class JobDiscoveryService:
    """Search configured providers through one typed orchestration boundary."""

    MAX_PROVIDER_ATTEMPTS = 2
    MAX_RETRY_DELAY_SECONDS = 2.0
    RETRYABLE_HTTP_STATUS_CODES = {408, 429, 500, 502, 503, 504}

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
                        code=ProviderFailureCode.MISCONFIGURED,
                        attempts=0,
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
            attempts = 0
            try:
                while True:
                    attempts += 1
                    try:
                        provider_jobs = provider.search_jobs(query)
                        break
                    except Exception as error:
                        if attempts >= self.MAX_PROVIDER_ATTEMPTS or not self._is_retryable(error):
                            raise
                        time.sleep(self._retry_delay(error, attempts))
                jobs.extend(provider_jobs)
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
                        code=self._failure_code(error),
                        attempts=attempts,
                    )
                )

        processed_jobs = self.pipeline.process(jobs)
        return JobDiscoveryResult(
            jobs=tuple(processed_jobs),
            failures=tuple(failures),
            providers_attempted=len(self.providers) + len(self.initialization_failures),
            providers_succeeded=providers_succeeded,
        )

    @classmethod
    def _is_retryable(cls, error: Exception) -> bool:
        if isinstance(
            error,
            (TimeoutError, ConnectionError, requests.Timeout, requests.ConnectionError),
        ):
            return True
        return isinstance(error, requests.HTTPError) and cls._status_code(error) in (
            cls.RETRYABLE_HTTP_STATUS_CODES
        )

    @classmethod
    def _retry_delay(cls, error: Exception, attempt: int) -> float:
        response = getattr(error, "response", None)
        if cls._status_code(error) == 429 and response is not None:
            retry_after = response.headers.get("Retry-After")
            try:
                return min(max(float(retry_after), 0.0), cls.MAX_RETRY_DELAY_SECONDS)
            except (TypeError, ValueError):
                pass
        return min(0.25 * (2 ** (attempt - 1)), cls.MAX_RETRY_DELAY_SECONDS)

    @classmethod
    def _failure_code(cls, error: Exception) -> ProviderFailureCode:
        if isinstance(error, ProviderConfigurationError):
            return ProviderFailureCode.MISCONFIGURED
        if isinstance(error, ProviderPayloadError):
            return ProviderFailureCode.INVALID_RESPONSE
        if isinstance(error, (TimeoutError, requests.Timeout)):
            return ProviderFailureCode.TIMEOUT
        if isinstance(error, requests.HTTPError):
            status_code = cls._status_code(error)
            if status_code == 429:
                return ProviderFailureCode.RATE_LIMITED
            if status_code in cls.RETRYABLE_HTTP_STATUS_CODES:
                return ProviderFailureCode.UNAVAILABLE
        if isinstance(error, (ConnectionError, requests.ConnectionError)):
            return ProviderFailureCode.UNAVAILABLE
        return ProviderFailureCode.FAILED

    @staticmethod
    def _status_code(error: Exception) -> int | None:
        response = getattr(error, "response", None)
        return getattr(response, "status_code", None)

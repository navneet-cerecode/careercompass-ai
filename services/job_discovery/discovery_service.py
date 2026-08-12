"""Coordinate job providers and the normalization pipeline."""

import logging
import time
import json
from collections import Counter
from collections.abc import Iterable
from concurrent.futures import ThreadPoolExecutor, wait
from dataclasses import dataclass
from time import perf_counter

import requests

from models.job_discovery_task import ProviderFailureCode
from models.job import Job

from services.job_discovery.pipeline.job_pipeline import JobPipeline
from services.job_discovery.quality import JobRejectionReason, rejection_reason
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
provider_logger = logging.getLogger("solarahire.providers")


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
    quality_rejections: tuple["ProviderQualityRejection", ...] = ()


@dataclass(frozen=True)
class ProviderQualityRejection:
    provider_name: str
    reason: JobRejectionReason
    count: int


class JobDiscoveryService:
    """Search configured providers through one typed orchestration boundary."""

    MAX_PROVIDER_ATTEMPTS = 2
    MAX_RETRY_DELAY_SECONDS = 2.0
    RETRYABLE_HTTP_STATUS_CODES = {408, 429, 500, 502, 503, 504}
    DEFAULT_MAX_WORKERS = 8
    DEFAULT_SEARCH_TIMEOUT_SECONDS = 45.0

    def __init__(
        self,
        providers: Iterable[BaseProvider] | None = None,
        pipeline: JobPipeline | None = None,
        max_workers: int = DEFAULT_MAX_WORKERS,
        search_timeout_seconds: float = DEFAULT_SEARCH_TIMEOUT_SECONDS,
    ):
        if providers is None:
            self.providers, self.initialization_failures = self._build_configured_providers()
        else:
            self.providers = list(providers)
            self.initialization_failures = []
        self.pipeline = pipeline or self._build_default_pipeline()
        self.search_timeout_seconds = search_timeout_seconds
        self.executor = ThreadPoolExecutor(
            max_workers=max(1, min(max_workers, len(self.providers) or 1)),
            thread_name_prefix="provider-search",
        )

    def close(self) -> None:
        self.executor.shutdown(wait=False, cancel_futures=True)

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
        quality_rejections = []
        providers_succeeded = 0
        futures = [
            (provider, self.executor.submit(self._search_provider, provider, query))
            for provider in self.providers
        ]
        _, pending = wait(
            [future for _, future in futures],
            timeout=self.search_timeout_seconds,
        )

        for provider, future in futures:
            if future in pending:
                attempts = 0 if future.cancel() else 1
                failure = ProviderFailure(
                    provider_name=provider.provider_name,
                    error_type="SearchBudgetExceeded",
                    code=ProviderFailureCode.TIMEOUT,
                    attempts=attempts,
                )
                failures.append(failure)
                self._log_attempt(
                    provider_name=provider.provider_name,
                    outcome="unavailable",
                    duration_ms=self.search_timeout_seconds * 1000,
                    attempts=attempts,
                    failure_code=failure.code,
                )
                continue

            provider_jobs, failure, duration_ms, attempts, rejection_counts = future.result()
            if failure is not None:
                failures.append(failure)
                self._log_attempt(
                    provider_name=provider.provider_name,
                    outcome="failed",
                    duration_ms=duration_ms,
                    attempts=attempts,
                    failure_code=failure.code,
                )
                continue

            jobs.extend(provider_jobs)
            quality_rejections.extend(
                ProviderQualityRejection(provider.provider_name, reason, count)
                for reason, count in rejection_counts.items()
            )
            providers_succeeded += 1
            self._log_attempt(
                provider_name=provider.provider_name,
                outcome="healthy",
                duration_ms=duration_ms,
                attempts=attempts,
                job_count=len(provider_jobs),
                rejection_counts=rejection_counts,
            )

        processed_jobs = self.pipeline.process(jobs)
        return JobDiscoveryResult(
            jobs=tuple(processed_jobs),
            failures=tuple(failures),
            providers_attempted=len(self.providers) + len(self.initialization_failures),
            providers_succeeded=providers_succeeded,
            quality_rejections=tuple(quality_rejections),
        )

    def _search_provider(
        self,
        provider: BaseProvider,
        query: JobSearchQuery,
    ) -> tuple[
        list[Job],
        ProviderFailure | None,
        float,
        int,
        Counter[JobRejectionReason],
    ]:
        started = perf_counter()
        attempts = 0
        try:
            while True:
                attempts += 1
                try:
                    jobs = provider.search_jobs(query)
                    accepted_jobs = []
                    rejection_counts = Counter()
                    for job in jobs:
                        reason = rejection_reason(job, query.role)
                        if reason is None:
                            accepted_jobs.append(job)
                        else:
                            rejection_counts[reason] += 1
                    return (
                        accepted_jobs,
                        None,
                        (perf_counter() - started) * 1000,
                        attempts,
                        rejection_counts,
                    )
                except Exception as error:
                    if attempts >= self.MAX_PROVIDER_ATTEMPTS or not self._is_retryable(error):
                        raise
                    time.sleep(self._retry_delay(error, attempts))
        except Exception as error:
            logger.warning(
                "Provider search failed: %s; error_type=%s",
                provider.provider_name,
                type(error).__name__,
            )
            return (
                [],
                ProviderFailure(
                    provider_name=provider.provider_name,
                    error_type=type(error).__name__,
                    code=self._failure_code(error),
                    attempts=attempts,
                ),
                (perf_counter() - started) * 1000,
                attempts,
                Counter(),
            )

    @staticmethod
    def _log_attempt(
        *,
        provider_name: str,
        outcome: str,
        duration_ms: float,
        attempts: int,
        job_count: int = 0,
        failure_code: ProviderFailureCode | None = None,
        rejection_counts: Counter[JobRejectionReason] | None = None,
    ) -> None:
        event = {
            "schema_version": 1,
            "kind": "provider_search",
            "provider": provider_name,
            "outcome": outcome,
            "duration_ms": round(duration_ms, 2),
            "attempts": attempts,
            "job_count": job_count,
        }
        if failure_code is not None:
            event["failure_code"] = failure_code.value
        if rejection_counts:
            event["rejected_job_count"] = sum(rejection_counts.values())
            event["rejection_reasons"] = {
                reason.value: count for reason, count in sorted(rejection_counts.items())
            }
        provider_logger.info(json.dumps(event, separators=(",", ":"), sort_keys=True))

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

"""Canonical interface for all job providers."""

from abc import ABC, abstractmethod
from collections.abc import Mapping
from typing import Any

from models.job import Job

from services.job_discovery.providers.contracts import (
    JobSearchQuery,
    ProviderCapabilities,
    ProviderHealth,
    ProviderHealthStatus,
)
from services.job_discovery.providers.errors import ProviderCapabilityError


class BaseProvider(ABC):
    """Provider-neutral job discovery contract."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Stable provider identifier used for attribution and telemetry."""
        raise NotImplementedError

    @property
    @abstractmethod
    def capabilities(self) -> ProviderCapabilities:
        """Return only capabilities implemented by this adapter."""
        raise NotImplementedError

    @abstractmethod
    def search_jobs(
        self,
        query: JobSearchQuery,
    ) -> list[Job]:
        """Search using a provider-neutral typed query."""
        raise NotImplementedError

    @abstractmethod
    def normalize_job(
        self,
        raw_job: Mapping[str, Any],
    ) -> Job:
        """Normalize one provider payload into the canonical Job model."""
        raise NotImplementedError

    @property
    def name(self) -> str:
        """Compatibility attribute for the former duplicate provider contract."""
        return self.provider_name

    def search(
        self,
        role: str,
        location: str,
    ) -> list[Job]:
        """Compatibility adapter for the prototype's positional search API."""
        return self.search_jobs(
            JobSearchQuery(
                role=role,
                location=location,
            )
        )

    def get_job_details(self, external_id: str) -> Job:
        """Return job details when the provider advertises that capability."""
        raise ProviderCapabilityError(
            f"{self.provider_name} does not implement job detail retrieval."
        )

    def health_check(self) -> ProviderHealth:
        """Return an honest unknown status until a live check is implemented."""
        return ProviderHealth(
            provider_name=self.provider_name,
            status=ProviderHealthStatus.UNKNOWN,
            message="Live health check is not implemented.",
        )

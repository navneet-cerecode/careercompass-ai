"""Canonical job provider contracts and built-in adapters."""

from services.job_discovery.providers.base_provider import BaseProvider
from services.job_discovery.providers.contracts import (
    DatePosted,
    JobSearchQuery,
    ProviderCapabilities,
    ProviderConfig,
    ProviderHealth,
    ProviderHealthStatus,
)
from services.job_discovery.providers.jsearch_provider import JSearchProvider
from services.job_discovery.providers.workday_provider import WorkdayProvider

__all__ = [
    "BaseProvider",
    "DatePosted",
    "JobSearchQuery",
    "JSearchProvider",
    "ProviderCapabilities",
    "ProviderConfig",
    "ProviderHealth",
    "ProviderHealthStatus",
    "WorkdayProvider",
]

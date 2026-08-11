"""Canonical job provider contracts and built-in adapters."""

from services.job_discovery.providers.base_provider import BaseProvider
from services.job_discovery.providers.adzuna_provider import AdzunaProvider
from services.job_discovery.providers.arbeitnow_provider import ArbeitnowProvider
from services.job_discovery.providers.contracts import (
    DatePosted,
    JobSearchQuery,
    ProviderCapabilities,
    ProviderConfig,
    ProviderHealth,
    ProviderHealthStatus,
)
from services.job_discovery.providers.jsearch_provider import JSearchProvider
from services.job_discovery.providers.greenhouse_provider import GreenhouseProvider
from services.job_discovery.providers.the_muse_provider import TheMuseProvider
from services.job_discovery.providers.workday_provider import WorkdayProvider

__all__ = [
    "BaseProvider",
    "AdzunaProvider",
    "ArbeitnowProvider",
    "DatePosted",
    "JobSearchQuery",
    "JSearchProvider",
    "GreenhouseProvider",
    "TheMuseProvider",
    "ProviderCapabilities",
    "ProviderConfig",
    "ProviderHealth",
    "ProviderHealthStatus",
    "WorkdayProvider",
]

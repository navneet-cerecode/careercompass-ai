"""Backward-compatible import for the canonical provider contract."""

from services.job_discovery.providers.base_provider import BaseProvider
from services.job_discovery.providers.contracts import (
    JobSearchQuery,
    ProviderCapabilities,
    ProviderHealth,
    ProviderHealthStatus,
)

__all__ = [
    "BaseProvider",
    "JobSearchQuery",
    "ProviderCapabilities",
    "ProviderHealth",
    "ProviderHealthStatus",
]

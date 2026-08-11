"""Durable input and output for an asynchronous job-discovery task."""

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class JobDiscoveryOutcomeStatus(StrEnum):
    COMPLETE = "complete"
    PARTIAL = "partial"
    FAILED = "failed"


class ProviderFailureCode(StrEnum):
    TIMEOUT = "provider_timeout"
    RATE_LIMITED = "provider_rate_limited"
    UNAVAILABLE = "provider_unavailable"
    INVALID_RESPONSE = "provider_invalid_response"
    MISCONFIGURED = "provider_misconfigured"
    FAILED = "provider_failed"


class ProviderFailureDetail(BaseModel):
    model_config = ConfigDict(frozen=True)

    provider_name: str
    code: ProviderFailureCode = ProviderFailureCode.FAILED
    attempts: int = Field(default=1, ge=0)


class JobDiscoveryOutcome(BaseModel):
    model_config = ConfigDict(frozen=True)

    status: JobDiscoveryOutcomeStatus
    provider_failures: tuple[ProviderFailureDetail, ...] = ()
    providers_attempted: int
    providers_succeeded: int

    @property
    def provider_names_failed(self) -> tuple[str, ...]:
        """Compatibility view for callers that need only source names."""
        return tuple(failure.provider_name for failure in self.provider_failures)

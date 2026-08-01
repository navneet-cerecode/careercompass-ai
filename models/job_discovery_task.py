"""Durable input and output for an asynchronous job-discovery task."""

from enum import StrEnum

from pydantic import BaseModel, ConfigDict


class JobDiscoveryOutcomeStatus(StrEnum):
    COMPLETE = "complete"
    PARTIAL = "partial"
    FAILED = "failed"


class JobDiscoveryOutcome(BaseModel):
    model_config = ConfigDict(frozen=True)

    status: JobDiscoveryOutcomeStatus
    provider_names_failed: tuple[str, ...] = ()
    providers_attempted: int
    providers_succeeded: int

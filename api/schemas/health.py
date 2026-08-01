"""Health endpoint response contracts."""

from enum import StrEnum

from pydantic import BaseModel, Field


class HealthStatus(StrEnum):
    OK = "ok"
    READY = "ready"
    NOT_READY = "not_ready"


class HealthResponse(BaseModel):
    """Stable response returned by liveness and readiness probes."""

    status: HealthStatus
    service: str
    version: str
    checks: dict[str, str] = Field(default_factory=dict)

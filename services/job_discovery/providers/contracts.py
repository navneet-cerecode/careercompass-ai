"""Typed contracts shared by every job provider."""

from enum import Enum
from typing import Required, TypedDict

from pydantic import BaseModel, ConfigDict, Field, field_validator

from models.enums import EmploymentType


class ProviderConfig(TypedDict, total=False):
    """Registry shape shared by the provider factory and adapters."""

    id: Required[str]
    name: Required[str]
    platform: Required[str]
    enabled: bool
    priority: int
    country: str
    api_url: str
    careers_url: str


class DatePosted(str, Enum):
    """Portable date filters supported by job discovery."""

    ALL = "all"
    TODAY = "today"
    THREE_DAYS = "3days"
    WEEK = "week"
    MONTH = "month"


class JobSearchQuery(BaseModel):
    """Provider-neutral job search input."""

    model_config = ConfigDict(frozen=True)

    role: str = Field(min_length=1)
    location: str = Field(min_length=1)
    country: str | None = Field(default=None, min_length=2, max_length=2)
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
    remote_only: bool | None = None
    employment_types: list[EmploymentType] = Field(default_factory=list)
    date_posted: DatePosted = DatePosted.ALL

    @field_validator("role", "location")
    @classmethod
    def normalize_required_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Search text cannot be blank.")
        return value

    @field_validator("country")
    @classmethod
    def normalize_country(cls, value: str | None) -> str | None:
        return value.lower() if value else None


class ProviderCapabilities(BaseModel):
    """Features actually implemented by a provider adapter."""

    model_config = ConfigDict(frozen=True)

    location_filter: bool = False
    country_filter: bool = False
    remote_filter: bool = False
    employment_type_filter: bool = False
    date_posted_filter: bool = False
    pagination: bool = False
    job_details: bool = False
    live_health_check: bool = False


class ProviderHealthStatus(str, Enum):
    """Normalized provider health states."""

    UNKNOWN = "unknown"
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"


class ProviderHealth(BaseModel):
    """Result of a provider health check."""

    provider_name: str
    status: ProviderHealthStatus
    message: str | None = None

"""Privacy-bounded operational telemetry and product analytics."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
import hashlib
import hmac
import json
import logging
from time import perf_counter
from typing import Protocol
from uuid import UUID, uuid4

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

http_logger = logging.getLogger("solarahire.http")
analytics_logger = logging.getLogger("solarahire.analytics")


class ProductEventName(StrEnum):
    RESUME_PARSED = "resume_parsed"
    JOB_SEARCH_REQUESTED = "job_search_requested"
    RECOMMENDATIONS_GENERATED = "recommendations_generated"
    JOB_SAVED = "job_saved"
    APPLICATION_TRACKING_STARTED = "application_tracking_started"
    APPLICATION_STATUS_CHANGED = "application_status_changed"
    BILLING_SUMMARY_VIEWED = "billing_summary_viewed"


AnalyticsValue = bool | int | str

EVENT_PROPERTIES: dict[ProductEventName, frozenset[str]] = {
    ProductEventName.RESUME_PARSED: frozenset({"authenticated"}),
    ProductEventName.JOB_SEARCH_REQUESTED: frozenset(
        {"authenticated", "remote_only", "employment_type_count"}
    ),
    ProductEventName.RECOMMENDATIONS_GENERATED: frozenset(
        {"jobs_considered", "recommendations_returned"}
    ),
    ProductEventName.JOB_SAVED: frozenset({"has_notes"}),
    ProductEventName.APPLICATION_TRACKING_STARTED: frozenset({"has_resume", "has_next_action"}),
    ProductEventName.APPLICATION_STATUS_CHANGED: frozenset({"to_status"}),
    ProductEventName.BILLING_SUMMARY_VIEWED: frozenset({"plan", "status"}),
}

BOOLEAN_PROPERTIES = frozenset(
    {"authenticated", "remote_only", "has_notes", "has_resume", "has_next_action"}
)
COUNT_PROPERTIES = frozenset(
    {"employment_type_count", "jobs_considered", "recommendations_returned"}
)
ENUM_PROPERTIES: dict[str, frozenset[str]] = {
    "to_status": frozenset(
        {
            "Discovered",
            "Saved",
            "Preparing",
            "Ready to apply",
            "Applied",
            "Under review",
            "Assessment",
            "Interview",
            "Offer",
            "Rejected",
            "Withdrawn",
        }
    ),
    "plan": frozenset({"free", "pro"}),
    "status": frozenset({"active", "trialing", "past_due", "cancelled", "incomplete"}),
}


@dataclass(frozen=True)
class ProductEvent:
    name: ProductEventName
    actor_id: str | None
    properties: Mapping[str, AnalyticsValue]

    def as_dict(self) -> dict[str, object]:
        return {
            "schema_version": 1,
            "kind": "product_event",
            "event": self.name.value,
            "actor_id": self.actor_id,
            "properties": dict(self.properties),
        }


class AnalyticsSink(Protocol):
    def emit(self, event: ProductEvent) -> None: ...


class NullAnalyticsSink:
    def emit(self, event: ProductEvent) -> None:
        del event


class StructuredLogAnalyticsSink:
    def emit(self, event: ProductEvent) -> None:
        analytics_logger.info(json.dumps(event.as_dict(), separators=(",", ":"), sort_keys=True))


class ProductAnalytics:
    """Emit aggregate-friendly events through an interchangeable sink."""

    def __init__(self, sink: AnalyticsSink, *, identity_salt: bytes | None = None) -> None:
        self.sink = sink
        self.identity_salt = identity_salt

    def track(
        self,
        name: ProductEventName,
        *,
        user_id: UUID | None = None,
        properties: Mapping[str, AnalyticsValue] | None = None,
    ) -> None:
        safe_properties = dict(properties or {})
        unexpected = set(safe_properties) - EVENT_PROPERTIES[name]
        if unexpected:
            raise ValueError(
                f"Unexpected analytics properties for {name.value}: {sorted(unexpected)}"
            )
        for key, value in safe_properties.items():
            if not _valid_property(key, value):
                raise ValueError(f"Invalid analytics property value for {key}.")
        event = ProductEvent(
            name=name,
            actor_id=self._actor_id(user_id),
            properties=safe_properties,
        )
        try:
            self.sink.emit(event)
        except Exception:
            analytics_logger.warning(
                "Product analytics sink failed for event %s.",
                name.value,
                exc_info=True,
            )

    def _actor_id(self, user_id: UUID | None) -> str | None:
        if user_id is None or self.identity_salt is None:
            return None
        return hmac.new(
            self.identity_salt,
            str(user_id).encode(),
            hashlib.sha256,
        ).hexdigest()


def build_product_analytics(*, enabled: bool, identity_salt: bytes | None) -> ProductAnalytics:
    sink: AnalyticsSink = StructuredLogAnalyticsSink() if enabled else NullAnalyticsSink()
    return ProductAnalytics(sink, identity_salt=identity_salt)


class RequestTelemetryMiddleware(BaseHTTPMiddleware):
    """Add correlation IDs and emit one PII-minimized record per request."""

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        request_id = _request_id(request.headers.get("x-request-id"))
        started = perf_counter()
        status_code = 500
        try:
            response = await call_next(request)
            status_code = response.status_code
            response.headers["X-Request-ID"] = request_id
            response.headers.setdefault("Cache-Control", "no-store")
            response.headers.setdefault("X-Content-Type-Options", "nosniff")
            response.headers.setdefault("X-Frame-Options", "DENY")
            response.headers.setdefault("Referrer-Policy", "no-referrer")
            response.headers.setdefault(
                "Permissions-Policy",
                "camera=(), microphone=(), geolocation=()",
            )
            return response
        finally:
            route_template = _route_template(request)
            event = {
                "kind": "http_request",
                "request_id": request_id,
                "method": request.method,
                "route": route_template,
                "status_code": status_code,
                "duration_ms": round((perf_counter() - started) * 1000, 2),
            }
            http_logger.info(json.dumps(event, separators=(",", ":"), sort_keys=True))


def _request_id(value: str | None) -> str:
    if value is not None and 8 <= len(value) <= 64 and value.replace("-", "").isalnum():
        return value
    return uuid4().hex


def _route_template(request: Request) -> str:
    if request.scope.get("route") is None:
        return "unmatched"
    template = request.url.path
    for name, value in request.path_params.items():
        template = template.replace(str(value), f"{{{name}}}")
    return template


def _valid_property(key: str, value: AnalyticsValue) -> bool:
    if key in BOOLEAN_PROPERTIES:
        return type(value) is bool
    if key in COUNT_PROPERTIES:
        return type(value) is int and 0 <= value <= 10_000
    if key in ENUM_PROPERTIES:
        return type(value) is str and value in ENUM_PROPERTIES[key]
    return False

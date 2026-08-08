import json
import logging
from uuid import uuid4

from fastapi.testclient import TestClient
import pytest

from api.application import create_app
from core.config import Settings
from core.observability import (
    ProductAnalytics,
    ProductEvent,
    ProductEventName,
)


class CapturingSink:
    def __init__(self) -> None:
        self.events: list[ProductEvent] = []

    def emit(self, event: ProductEvent) -> None:
        self.events.append(event)


class FailingSink:
    def emit(self, event: ProductEvent) -> None:
        del event
        raise RuntimeError("provider unavailable")


def test_product_analytics_hashes_actor_and_rejects_unapproved_properties():
    sink = CapturingSink()
    analytics = ProductAnalytics(sink, identity_salt=b"a-safe-test-salt-that-is-long-enough")
    user_id = uuid4()

    analytics.track(
        ProductEventName.JOB_SAVED,
        user_id=user_id,
        properties={"has_notes": True},
    )

    event = sink.events[0]
    assert event.actor_id is not None
    assert event.actor_id != str(user_id)
    assert str(user_id) not in json.dumps(event.as_dict())
    with pytest.raises(ValueError, match="Unexpected analytics properties"):
        analytics.track(
            ProductEventName.JOB_SAVED,
            properties={"email": "private@example.com"},
        )
    with pytest.raises(ValueError, match="Invalid analytics property value"):
        analytics.track(
            ProductEventName.BILLING_SUMMARY_VIEWED,
            properties={"plan": "private@example.com", "status": "active"},
        )


def test_product_operation_is_not_failed_by_analytics_provider_error(caplog):
    analytics = ProductAnalytics(FailingSink())
    logging.getLogger("solarahire.analytics").disabled = False

    with caplog.at_level(logging.WARNING, logger="solarahire.analytics"):
        analytics.track(ProductEventName.JOB_SAVED, properties={"has_notes": False})

    assert "job_saved" in caplog.records[-1].message


def test_request_telemetry_uses_route_template_without_query_or_path_identifier(caplog):
    application = create_app(Settings(_env_file=None))
    client = TestClient(application)
    job_id = uuid4()
    logging.getLogger("solarahire.http").disabled = False

    with caplog.at_level(logging.INFO, logger="solarahire.http"):
        response = client.get(
            f"/api/v1/jobs/{job_id}?email=private@example.com",
            headers={"X-Request-ID": "request-1234"},
        )

    assert response.headers["X-Request-ID"] == "request-1234"
    payload = json.loads(caplog.records[-1].message)
    assert payload["route"] == "/api/v1/jobs/{job_id}"
    assert str(job_id) not in caplog.records[-1].message
    assert "private@example.com" not in caplog.records[-1].message

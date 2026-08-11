"""Tests for the canonical frontend smoke gate."""

from email.message import Message
from urllib.error import URLError

import pytest

from scripts.smoke_frontend import (
    EndpointCheck,
    SmokeCheckError,
    build_checks,
    normalize_base_url,
    run_check,
)


class FakeResponse:
    def __init__(
        self,
        body: bytes,
        *,
        status: int = 200,
        content_type: str = "application/json",
    ):
        self.body = body
        self.status = status
        self.headers = Message()
        self.headers["Content-Type"] = content_type

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return None

    def read(self, amount: int = -1) -> bytes:
        return self.body if amount < 0 else self.body[:amount]


def test_build_checks_targets_only_read_only_canonical_routes():
    checks = build_checks("http://127.0.0.1:8000/", "http://localhost:3000/")

    assert [check.url for check in checks] == [
        "http://127.0.0.1:8000/api/v1/health/live",
        "http://127.0.0.1:8000/api/v1/health/ready",
        "http://localhost:3000/",
        "http://localhost:3000/workspace",
    ]


def test_build_checks_can_verify_oidc_signing_key_connectivity():
    checks = build_checks(
        "http://127.0.0.1:8000/",
        "http://localhost:3000/",
        "https://identity.example.test/.well-known/jwks.json",
    )

    assert checks[-1] == EndpointCheck(
        name="OIDC signing keys",
        url="https://identity.example.test/.well-known/jwks.json",
        content_type="application/json",
        marker=b'"keys"',
    )


def test_normalize_base_url_rejects_non_http_origins():
    with pytest.raises(ValueError, match="absolute HTTP"):
        normalize_base_url("file:///tmp/app", setting_name="--frontend-url")


def test_run_check_accepts_expected_content_type_and_marker():
    check = EndpointCheck(
        name="Ready",
        url="http://localhost/ready",
        content_type="application/json",
        marker=b'"status":"ready"',
    )

    run_check(
        check,
        opener=lambda request, timeout: FakeResponse(b'{"status":"ready"}'),
    )


@pytest.mark.parametrize(
    ("response", "message"),
    [
        (FakeResponse(b"{}", status=503), "HTTP 503"),
        (FakeResponse(b"{}", content_type="text/plain"), "returned text/plain"),
        (FakeResponse(b"{}"), "readiness marker"),
    ],
)
def test_run_check_reports_safe_failure_reasons(response, message):
    check = EndpointCheck(
        name="Ready",
        url="http://localhost/ready",
        content_type="application/json",
        marker=b'"status":"ready"',
    )

    with pytest.raises(SmokeCheckError, match=message):
        run_check(check, opener=lambda request, timeout: response)


def test_run_check_hides_transport_details():
    check = EndpointCheck(
        name="Ready",
        url="http://localhost/ready",
        content_type="application/json",
        marker=b'"status":"ready"',
    )

    def unavailable(request, timeout):
        raise URLError("sensitive network detail")

    with pytest.raises(SmokeCheckError, match="Ready is unavailable") as error:
        run_check(check, opener=unavailable)

    assert "sensitive network detail" not in str(error.value)

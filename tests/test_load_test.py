from argparse import ArgumentTypeError
from email.message import Message

import pytest

from scripts.load_test import RequestResult, Target, parse_target, run_target, summarize
from scripts.stress_worker import require_test_database_url


class FakeResponse:
    status = 200
    headers = Message()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return None

    def read(self, amount=-1):
        return b"{}"


def test_parse_target_requires_named_http_url():
    assert parse_target("ready=http://localhost/ready") == Target(
        name="ready",
        url="http://localhost/ready",
    )

    with pytest.raises(ArgumentTypeError, match="NAME=http"):
        parse_target("file:///tmp/result")


def test_run_target_collects_bounded_concurrent_requests():
    calls = []

    def opener(request, timeout):
        calls.append((request.full_url, timeout))
        return FakeResponse()

    summary = run_target(
        Target("ready", "http://localhost/ready"),
        request_count=5,
        concurrency=2,
        timeout_seconds=1,
        opener=opener,
    )

    assert len(calls) == 6  # one warm-up plus the measured requests
    assert summary.requests == 5
    assert summary.succeeded == 5
    assert summary.failed == 0


def test_summary_reports_nearest_rank_percentiles_and_safe_errors():
    summary = summarize(
        Target("ready", "http://localhost/ready"),
        [
            RequestResult(10, 200),
            RequestResult(20, 200),
            RequestResult(30, 503, "http_503"),
            RequestResult(40, None, "transport_error"),
        ],
        elapsed_seconds=1,
    )

    assert summary.error_rate == 0.5
    assert summary.requests_per_second == 4
    assert summary.p50_ms == 20
    assert summary.p95_ms == 40
    assert summary.errors == {"http_503": 1, "transport_error": 1}


def test_worker_stress_requires_dedicated_postgresql_database():
    assert (
        require_test_database_url("postgresql+psycopg://localhost/solarahire_test")
        == "postgresql+psycopg://localhost/solarahire_test"
    )

    with pytest.raises(ValueError, match="dedicated PostgreSQL"):
        require_test_database_url("postgresql+psycopg://localhost/solarahire")

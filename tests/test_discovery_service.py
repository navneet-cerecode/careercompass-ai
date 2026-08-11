import json
import logging
import requests
from threading import Barrier, Event
from time import perf_counter

from models.job import Job
from models.job_discovery_task import ProviderFailureCode
from services.job_discovery.discovery_service import JobDiscoveryService
from services.job_discovery.providers.base_provider import BaseProvider
from services.job_discovery.providers.contracts import (
    JobSearchQuery,
    ProviderCapabilities,
)


class RecordingProvider(BaseProvider):
    def __init__(self, jobs):
        self.jobs = jobs
        self.queries = []

    @property
    def provider_name(self):
        return "recording"

    @property
    def capabilities(self):
        return ProviderCapabilities(location_filter=True)

    def search_jobs(self, query):
        self.queries.append(query)
        return self.jobs

    def normalize_job(self, raw_job):
        raise AssertionError("Normalization is not used by this test provider")


class FailingProvider(RecordingProvider):
    @property
    def provider_name(self):
        return "failing"

    def search_jobs(self, query):
        self.queries.append(query)
        raise TimeoutError("synthetic provider timeout")


class InvalidPayloadProvider(FailingProvider):
    @property
    def provider_name(self):
        return "invalid-payload"

    def search_jobs(self, query):
        from services.job_discovery.providers.errors import ProviderPayloadError

        self.queries.append(query)
        raise ProviderPayloadError("synthetic invalid payload")


class RateLimitedProvider(RecordingProvider):
    @property
    def provider_name(self):
        return "rate-limited"

    def search_jobs(self, query):
        self.queries.append(query)
        if len(self.queries) == 1:
            response = requests.Response()
            response.status_code = 429
            response.headers["Retry-After"] = "10"
            raise requests.HTTPError(response=response)
        return self.jobs


class BarrierProvider(RecordingProvider):
    def __init__(self, name, jobs, barrier):
        super().__init__(jobs)
        self._name = name
        self.barrier = barrier

    @property
    def provider_name(self):
        return self._name

    def search_jobs(self, query):
        self.queries.append(query)
        self.barrier.wait(timeout=1)
        return self.jobs


class WaitingProvider(RecordingProvider):
    @property
    def provider_name(self):
        return "waiting"

    def __init__(self, release):
        super().__init__([])
        self.release = release

    def search_jobs(self, query):
        self.queries.append(query)
        self.release.wait(timeout=1)
        return []


def make_job(*, location="India"):
    return Job(
        title="Data Engineer",
        company="Example Corp",
        location=location,
        description="Python and SQL",
        url=f"https://example.com/jobs/{location.lower()}",
    )


def test_discovery_service_passes_one_typed_query_to_injected_providers():
    first = RecordingProvider([make_job()])
    second = RecordingProvider([make_job(), make_job(location="Hyderabad")])
    service = JobDiscoveryService(providers=[first, second])

    jobs = service.discover("Data Engineer", "India")

    assert len(jobs) == 2
    assert all(isinstance(query, JobSearchQuery) for query in first.queries)
    assert first.queries == second.queries
    assert first.queries[0].role == "Data Engineer"
    assert first.queries[0].location == "India"


def test_discovery_service_accepts_explicit_empty_provider_list():
    service = JobDiscoveryService(providers=[])

    assert service.discover("Data Engineer", "India") == []


def test_discovery_service_retries_timeout_and_returns_sanitized_partial_failure(monkeypatch):
    successful = RecordingProvider([make_job()])
    failing = FailingProvider([])
    delays = []
    monkeypatch.setattr("services.job_discovery.discovery_service.time.sleep", delays.append)
    service = JobDiscoveryService(providers=[failing, successful])

    result = service.discover_jobs_with_status(
        JobSearchQuery(role="Data Engineer", location="India")
    )

    assert len(result.jobs) == 1
    assert result.providers_attempted == 2
    assert result.providers_succeeded == 1
    assert result.failures[0].provider_name == "failing"
    assert result.failures[0].error_type == "TimeoutError"
    assert result.failures[0].code == ProviderFailureCode.TIMEOUT
    assert result.failures[0].attempts == 2
    assert len(failing.queries) == 2
    assert delays == [0.25]


def test_discovery_service_honors_bounded_retry_after(monkeypatch):
    provider = RateLimitedProvider([make_job()])
    delays = []
    monkeypatch.setattr("services.job_discovery.discovery_service.time.sleep", delays.append)

    result = JobDiscoveryService(providers=[provider]).discover_jobs_with_status(
        JobSearchQuery(role="Data Engineer", location="India")
    )

    assert len(result.jobs) == 1
    assert result.failures == ()
    assert len(provider.queries) == 2
    assert delays == [2.0]


def test_discovery_service_does_not_retry_invalid_payload(monkeypatch):
    provider = InvalidPayloadProvider([])
    sleep = monkeypatch.setattr(
        "services.job_discovery.discovery_service.time.sleep",
        lambda _: (_ for _ in ()).throw(AssertionError("must not retry")),
    )

    result = JobDiscoveryService(providers=[provider]).discover_jobs_with_status(
        JobSearchQuery(role="Data Engineer", location="India")
    )

    assert sleep is None
    assert len(provider.queries) == 1
    assert result.failures[0].code == ProviderFailureCode.INVALID_RESPONSE
    assert result.failures[0].attempts == 1


def test_discovery_service_runs_providers_concurrently():
    barrier = Barrier(2)
    service = JobDiscoveryService(
        providers=[
            BarrierProvider("first", [make_job()], barrier),
            BarrierProvider("second", [make_job(location="Pune")], barrier),
        ],
        max_workers=2,
        search_timeout_seconds=1,
    )

    result = service.discover_jobs_with_status(
        JobSearchQuery(role="Data Engineer", location="India")
    )
    service.close()

    assert result.providers_succeeded == 2
    assert len(result.jobs) == 2


def test_discovery_service_returns_completed_results_at_search_budget():
    release = Event()
    service = JobDiscoveryService(
        providers=[WaitingProvider(release), RecordingProvider([make_job()])],
        max_workers=2,
        search_timeout_seconds=0.02,
    )

    started = perf_counter()
    result = service.discover_jobs_with_status(
        JobSearchQuery(role="Data Engineer", location="India")
    )
    elapsed = perf_counter() - started
    release.set()
    service.close()

    assert elapsed < 0.2
    assert len(result.jobs) == 1
    assert result.providers_succeeded == 1
    assert result.failures[0].provider_name == "waiting"
    assert result.failures[0].error_type == "SearchBudgetExceeded"
    assert result.failures[0].code == ProviderFailureCode.TIMEOUT


def test_discovery_service_logs_privacy_bounded_provider_latency(caplog):
    logging.getLogger("solarahire.providers").disabled = False
    service = JobDiscoveryService(providers=[RecordingProvider([make_job()])])

    with caplog.at_level(logging.INFO, logger="solarahire.providers"):
        service.discover_jobs_with_status(
            JobSearchQuery(role="Private Role", location="Private Location")
        )
    service.close()

    event = json.loads(caplog.records[-1].message)
    assert event["kind"] == "provider_search"
    assert event["provider"] == "recording"
    assert event["outcome"] == "healthy"
    assert event["job_count"] == 1
    assert event["attempts"] == 1
    assert event["duration_ms"] >= 0
    assert "Private Role" not in caplog.records[-1].message
    assert "Private Location" not in caplog.records[-1].message

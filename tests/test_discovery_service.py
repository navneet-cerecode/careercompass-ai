import requests

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

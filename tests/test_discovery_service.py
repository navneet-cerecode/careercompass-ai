from models.job import Job
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

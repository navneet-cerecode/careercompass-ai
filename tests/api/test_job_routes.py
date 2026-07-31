from fastapi.testclient import TestClient

from api.application import create_app
from api.dependencies import get_job_discovery_service
from core.config import Settings
from models.job import Job
from services.job_discovery.discovery_service import (
    JobDiscoveryResult,
    ProviderFailure,
)


def make_job() -> Job:
    return Job(
        title="Data Engineer",
        company="Example Corp",
        location="India",
        description="Python and SQL",
        url="https://example.com/jobs/1",
    )


def make_client(result: JobDiscoveryResult) -> TestClient:
    class StubDiscoveryService:
        def discover_jobs_with_status(self, query):
            assert query.role == "Data Engineer"
            assert query.location == "India"
            return result

    application = create_app(Settings(_env_file=None))
    application.dependency_overrides[get_job_discovery_service] = StubDiscoveryService
    return TestClient(application)


def test_job_search_returns_partial_results_and_provider_metadata():
    job = make_job()
    result = JobDiscoveryResult(
        jobs=(job,),
        failures=(ProviderFailure("jsearch", "TimeoutError"),),
        providers_attempted=2,
        providers_succeeded=1,
    )
    client = make_client(result)

    response = client.post(
        "/api/v1/jobs/search",
        json={"role": "Data Engineer", "location": "India"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "partial"
    assert payload["jobs"][0]["id"] == str(job.id)
    assert payload["provider_failures"] == [{"provider_name": "jsearch", "code": "provider_failed"}]

    detail_response = client.get(f"/api/v1/jobs/{job.id}")
    assert detail_response.status_code == 200
    assert detail_response.json()["title"] == "Data Engineer"


def test_job_search_reports_total_provider_failure_without_fake_results():
    result = JobDiscoveryResult(
        jobs=(),
        failures=(ProviderFailure("jsearch", "ConnectionError"),),
        providers_attempted=1,
        providers_succeeded=0,
    )

    response = make_client(result).post(
        "/api/v1/jobs/search",
        json={"role": "Data Engineer", "location": "India"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "failed"
    assert response.json()["jobs"] == []


def test_job_details_returns_stable_not_found_error():
    result = JobDiscoveryResult(
        jobs=(),
        failures=(),
        providers_attempted=0,
        providers_succeeded=0,
    )
    client = make_client(result)

    response = client.get("/api/v1/jobs/00000000-0000-0000-0000-000000000000")

    assert response.status_code == 404
    assert response.json() == {
        "code": "job_not_found",
        "message": "The requested job was not found.",
    }

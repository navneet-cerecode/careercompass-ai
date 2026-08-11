from datetime import UTC, datetime
from uuid import uuid4

from fastapi.testclient import TestClient

from api.application import create_app
from api.dependencies import (
    get_job_discovery_service,
    get_job_discovery_task_service,
)
from api.services.job_discovery_tasks import JobDiscoveryTaskSnapshot
from core.config import Settings
from database.base import Base
from database.session import Database
from models.job import Job
from models.background_task import BackgroundTask
from models.enums import BackgroundTaskStatus
from models.job_discovery_task import JobDiscoveryOutcome, JobDiscoveryOutcomeStatus
from models.job_discovery_task import ProviderFailureCode
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
    database = Database("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(database.engine)
    application.state.database = database
    application.dependency_overrides[get_job_discovery_service] = StubDiscoveryService
    return TestClient(application)


def test_job_search_returns_partial_results_and_provider_metadata():
    job = make_job()
    result = JobDiscoveryResult(
        jobs=(job,),
        failures=(
            ProviderFailure(
                "jsearch",
                "TimeoutError",
                ProviderFailureCode.TIMEOUT,
                2,
            ),
        ),
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
    assert payload["provider_failures"] == [
        {
            "provider_name": "jsearch",
            "code": "provider_timeout",
            "attempts": 2,
            "health_status": "unavailable",
        }
    ]

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


def test_job_details_survive_api_process_recreation(tmp_path):
    job = make_job()
    result = JobDiscoveryResult(
        jobs=(job,),
        failures=(),
        providers_attempted=1,
        providers_succeeded=1,
    )
    database_url = f"sqlite+pysqlite:///{tmp_path / 'persistent.db'}"
    database = Database(database_url)
    Base.metadata.create_all(database.engine)

    class StubDiscoveryService:
        def discover_jobs_with_status(self, query):
            return result

    settings = Settings(database_url=database_url, _env_file=None)
    first_application = create_app(settings)
    first_application.dependency_overrides[get_job_discovery_service] = StubDiscoveryService
    search_response = TestClient(first_application).post(
        "/api/v1/jobs/search",
        json={"role": "Data Engineer", "location": "India"},
    )
    persisted_id = search_response.json()["jobs"][0]["id"]

    second_application = create_app(settings)
    detail_response = TestClient(second_application).get(f"/api/v1/jobs/{persisted_id}")

    assert detail_response.status_code == 200
    assert detail_response.json()["id"] == persisted_id


def test_database_backed_route_fails_cleanly_without_configuration():
    application = create_app(Settings(_env_file=None))

    response = TestClient(application).get("/api/v1/jobs/00000000-0000-0000-0000-000000000000")

    assert response.status_code == 503
    assert response.json()["code"] == "database_not_configured"


def test_async_search_creation_and_capability_scoped_polling():
    job = make_job()
    now = datetime.now(UTC)
    task = BackgroundTask(
        id=uuid4(),
        task_type="job.discovery",
        status=BackgroundTaskStatus.SUCCEEDED,
        attempt_count=1,
        max_attempts=4,
        created_at=now,
        updated_at=now,
        finished_at=now,
    )

    class StubTaskService:
        def create(self, *, request, idempotency_key, user_id=None):
            assert request.role == "Data Engineer"
            assert idempotency_key == "browser-search-123"
            assert user_id is None
            return JobDiscoveryTaskSnapshot(task=task), "opaque-capability-token"

        def get(self, *, task_id, token, user_id=None):
            assert user_id is None
            if task_id != task.id or token != "opaque-capability-token":
                return None
            return JobDiscoveryTaskSnapshot(
                task=task,
                outcome=JobDiscoveryOutcome(
                    status=JobDiscoveryOutcomeStatus.COMPLETE,
                    providers_attempted=2,
                    providers_succeeded=2,
                ),
                jobs=(job,),
            )

        def cancel(self, *, task_id, token, user_id=None):
            assert user_id is None
            if task_id != task.id or token != "opaque-capability-token":
                return None
            return JobDiscoveryTaskSnapshot(
                task=task.model_copy(
                    update={
                        "status": BackgroundTaskStatus.CANCELLED,
                        "cancel_requested_at": now,
                    }
                )
            )

    application = create_app(Settings(_env_file=None))
    application.dependency_overrides[get_job_discovery_task_service] = StubTaskService
    client = TestClient(application)

    created = client.post(
        "/api/v1/jobs/search-tasks",
        headers={"Idempotency-Key": "browser-search-123"},
        json={"role": "Data Engineer", "location": "India"},
    )
    assert created.status_code == 202
    assert created.json() == {
        "task_id": str(task.id),
        "access_token": "opaque-capability-token",
        "status": "succeeded",
    }

    polled = client.get(
        f"/api/v1/jobs/search-tasks/{task.id}",
        headers={"X-Task-Token": "opaque-capability-token"},
    )
    assert polled.status_code == 200
    assert polled.json()["result"]["jobs"][0]["id"] == str(job.id)

    denied = client.get(
        f"/api/v1/jobs/search-tasks/{task.id}",
        headers={"X-Task-Token": "wrong-token-that-is-long-enough"},
    )
    assert denied.status_code == 404
    assert denied.json()["code"] == "task_not_found"

    cancelled = client.delete(
        f"/api/v1/jobs/search-tasks/{task.id}",
        headers={"X-Task-Token": "opaque-capability-token"},
    )
    assert cancelled.status_code == 200
    assert cancelled.json()["status"] == "cancelled"
    assert cancelled.json()["cancellation_requested"] is True

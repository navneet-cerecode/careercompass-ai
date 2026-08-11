from api.schemas.job_search import JobSearchRequest
from database.base import Base
from database.repositories.job_discovery_tasks import JobDiscoveryTaskRepository
from database.session import Database
from models.enums import BackgroundTaskStatus
from models.job import Job
from models.job_discovery_task import ProviderFailureCode
from services.job_discovery.discovery_service import JobDiscoveryResult, ProviderFailure
from workers.execution import BackgroundTaskRunner
from workers.job_discovery import RunJobDiscovery


def test_worker_discovers_and_persists_ordered_jobs():
    database = Database("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(database.engine)
    with database.session() as session:
        task, _ = JobDiscoveryTaskRepository(session).create(
            request=JobSearchRequest(role="AI Engineer", location="India"),
            idempotency_key="worker-discovery-1",
            max_attempts=2,
        )

    class StubDiscovery:
        def discover_jobs_with_status(self, query):
            assert query.role == "AI Engineer"
            return JobDiscoveryResult(
                jobs=(
                    Job(
                        title="AI Engineer",
                        company="Example",
                        location="India",
                        description="Build reliable AI systems.",
                        url="https://example.com/job",
                    ),
                ),
                failures=(
                    ProviderFailure(
                        "adzuna",
                        "TimeoutError",
                        ProviderFailureCode.TIMEOUT,
                        2,
                    ),
                ),
                providers_attempted=2,
                providers_succeeded=1,
            )

    outcome = BackgroundTaskRunner(database).run(
        task_id=task.id,
        user_id=None,
        operation=RunJobDiscovery(database, StubDiscovery()),
    )

    assert outcome.task.status == BackgroundTaskStatus.SUCCEEDED
    with database.session() as session:
        result = JobDiscoveryTaskRepository(session).get_result(task.id)
    assert result is not None
    discovery_outcome, jobs = result
    assert discovery_outcome.status.value == "partial"
    assert discovery_outcome.provider_failures[0].code == ProviderFailureCode.TIMEOUT
    assert discovery_outcome.provider_failures[0].attempts == 2
    assert jobs[0].company == "Example"

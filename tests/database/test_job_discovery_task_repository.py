import pytest

from api.schemas.job_search import JobSearchRequest
from database.base import Base
from database.repositories.job_discovery_tasks import JobDiscoveryTaskRepository
from database.repositories.tasks import IdempotencyConflict
from database.session import Database
from models.job import Job
from models.job_discovery_task import JobDiscoveryOutcome, JobDiscoveryOutcomeStatus


def test_discovery_request_is_idempotent_and_results_keep_rank_order():
    database = Database("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(database.engine)
    request = JobSearchRequest(role="AI Engineer", location="India")
    jobs = (
        Job(
            title="AI Engineer",
            company="First",
            location="India",
            description="Build reliable AI systems.",
            url="https://example.com/first",
        ),
        Job(
            title="ML Engineer",
            company="Second",
            location="India",
            description="Build reliable ML systems.",
            url="https://example.com/second",
        ),
    )

    with database.session() as session:
        repository = JobDiscoveryTaskRepository(session)
        task, created = repository.create(
            request=request,
            idempotency_key="discovery-request-1",
            max_attempts=4,
        )
        repeated, repeated_created = repository.create(
            request=request,
            idempotency_key="discovery-request-1",
            max_attempts=4,
        )
        persisted = repository.save_result(
            task_id=task.id,
            jobs=jobs,
            outcome=JobDiscoveryOutcome(
                status=JobDiscoveryOutcomeStatus.PARTIAL,
                provider_names_failed=("adzuna",),
                providers_attempted=4,
                providers_succeeded=3,
            ),
        )

    assert created is True
    assert repeated_created is False
    assert repeated.id == task.id
    with database.session() as session:
        loaded_request = JobDiscoveryTaskRepository(session).get_request(task.id)
        loaded = JobDiscoveryTaskRepository(session).get_result(task.id)
    assert loaded_request == request
    assert loaded is not None
    outcome, loaded_jobs = loaded
    assert loaded_jobs == persisted
    assert [job.company for job in loaded_jobs] == ["First", "Second"]
    assert outcome.provider_names_failed == ("adzuna",)


def test_discovery_idempotency_key_rejects_changed_inputs():
    database = Database("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(database.engine)

    with database.session() as session:
        repository = JobDiscoveryTaskRepository(session)
        repository.create(
            request=JobSearchRequest(role="AI Engineer", location="India"),
            idempotency_key="same-browser-intent",
            max_attempts=4,
        )
        with pytest.raises(IdempotencyConflict):
            repository.create(
                request=JobSearchRequest(role="Data Engineer", location="India"),
                idempotency_key="same-browser-intent",
                max_attempts=4,
            )

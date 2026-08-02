"""Real PostgreSQL migration and repository integration gate."""

import os
from datetime import UTC, datetime, timedelta

import pytest
from alembic import command
from alembic.runtime.migration import MigrationContext
from sqlalchemy.engine import make_url

from database.alembic import build_alembic_config
from database.repositories.applications import ApplicationRepository, SavedJobRepository
from database.repositories.application_reminders import ApplicationReminderRepository
from database.repositories.jobs import JobRepository
from database.repositories.identities import IdentityRepository
from database.repositories.job_discovery_tasks import JobDiscoveryTaskRepository
from database.repositories.tasks import BackgroundTaskRepository
from database.repositories.task_outbox import TaskOutboxRepository
from database.repositories.users import UserRepository
from database.session import Database
from models.enums import ApplicationStatus, BackgroundTaskStatus
from models.job import Job
from models.identity import VerifiedIdentity
from api.schemas.job_search import JobSearchRequest
from models.job_discovery_task import JobDiscoveryOutcome, JobDiscoveryOutcomeStatus

pytestmark = pytest.mark.postgres


def require_postgresql_url() -> str:
    database_url = os.getenv("TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("TEST_DATABASE_URL is not configured.")
    if not database_url.startswith(("postgresql://", "postgresql+psycopg://")):
        pytest.fail("TEST_DATABASE_URL must identify a dedicated PostgreSQL database.")
    database_name = make_url(database_url).database or ""
    if not database_name.endswith("_test"):
        pytest.fail("TEST_DATABASE_URL database name must end with '_test'.")
    return database_url


def test_postgresql_migrations_and_owner_scoped_repositories():
    database_url = require_postgresql_url()
    config = build_alembic_config(database_url)
    database = Database(database_url)

    try:
        command.downgrade(config, "base")
        command.upgrade(config, "head")
        with database.engine.connect() as connection:
            assert MigrationContext.configure(connection).get_current_revision() == "0010"
        assert database.check_connection() is True

        with database.session() as session:
            principal = IdentityRepository(session).provision(
                VerifiedIdentity(
                    issuer="https://identity.example.test/",
                    subject="postgres-identity-gate",
                    email="identity-gate@example.com",
                    name="Identity Gate",
                )
            )
            assert principal.subject == "postgres-identity-gate"
            user = UserRepository(session).create(
                email="postgres-gate@example.com",
                name="PostgreSQL Gate",
            )
            job = JobRepository(session).upsert(
                Job(
                    title="Reliability Engineer",
                    company="CareerCompass Test",
                    location="Remote",
                    description="Validate PostgreSQL persistence.",
                    url="https://example.com/jobs/postgres-gate",
                )
            )
            saved_job = SavedJobRepository(session).save(
                user_id=user.id,
                job_id=job.id,
                notes="Integration gate",
            )
            application = ApplicationRepository(session).create(
                user_id=user.id,
                job_id=job.id,
                status=ApplicationStatus.SAVED,
                next_action="Review the role",
                next_action_due_at=datetime.now(UTC) + timedelta(hours=12),
            )
            reminder_result = ApplicationReminderRepository(session).reconcile(
                now=datetime.now(UTC),
                upcoming_before=datetime.now(UTC) + timedelta(hours=24),
                limit=100,
            )
            assert reminder_result.created == 1
            task_repository = BackgroundTaskRepository(session)
            task = task_repository.create(
                task_type="job.discovery",
                idempotency_key="postgres-task-gate",
                user_id=user.id,
                resource_id=job.id,
                max_attempts=2,
            )
            task_repository.start(task_id=task.id, user_id=user.id)
            task_repository.record_failure(
                task_id=task.id,
                user_id=user.id,
                error_code="provider_timeout",
                retryable=True,
            )
            task_repository.start(task_id=task.id, user_id=user.id)
            completed_task = task_repository.complete(
                task_id=task.id,
                user_id=user.id,
            )
            assert completed_task is not None
            assert completed_task.status == BackgroundTaskStatus.SUCCEEDED
            discovery_repository = JobDiscoveryTaskRepository(session)
            discovery_task, created = discovery_repository.create(
                request=JobSearchRequest(
                    role="Reliability Engineer",
                    location="Remote",
                ),
                idempotency_key="postgres-discovery-gate",
                max_attempts=2,
            )
            assert created is True
            assert TaskOutboxRepository(session).get_pending_for_task(discovery_task.id) is not None
            discovery_repository.save_result(
                task_id=discovery_task.id,
                jobs=(job,),
                outcome=JobDiscoveryOutcome(
                    status=JobDiscoveryOutcomeStatus.COMPLETE,
                    providers_attempted=1,
                    providers_succeeded=1,
                ),
            )

        with database.session() as session:
            assert (
                SavedJobRepository(session).get(
                    user_id=user.id,
                    job_id=job.id,
                )
                == saved_job
            )
            loaded = ApplicationRepository(session).get(
                user_id=user.id,
                application_id=application.id,
            )
            assert loaded is not None
            assert loaded.status == ApplicationStatus.SAVED
            reminders = ApplicationReminderRepository(session).list(user_id=user.id)
            assert len(reminders) == 1
            assert reminders[0].application_id == application.id
            loaded_task = BackgroundTaskRepository(session).get(
                task_id=task.id,
                user_id=user.id,
            )
            assert loaded_task is not None
            assert loaded_task.status == BackgroundTaskStatus.SUCCEEDED
            assert loaded_task.attempt_count == 2
            discovery_result = JobDiscoveryTaskRepository(session).get_result(discovery_task.id)
            assert discovery_result is not None
            assert discovery_result[1][0].id == job.id
    finally:
        database.dispose()
        command.downgrade(config, "base")

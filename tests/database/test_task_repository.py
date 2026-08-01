from uuid import uuid4

import pytest
from sqlalchemy import select

from database.base import Base
from database.models.tasks import BackgroundTaskRecord
from database.repositories.tasks import (
    BackgroundTaskRepository,
    IdempotencyConflict,
    InvalidTaskTransition,
)
from database.repositories.users import UserRepository
from database.session import Database
from models.enums import BackgroundTaskStatus


def make_database() -> Database:
    database = Database("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(database.engine)
    return database


def test_task_creation_is_idempotent_without_storing_plaintext_key():
    database = make_database()
    with database.session() as session:
        owner = UserRepository(session).create(email="owner@example.com", name="Owner")
        repository = BackgroundTaskRepository(session)
        resource_id = uuid4()

        first = repository.create(
            task_type="job.discovery",
            idempotency_key="request-12345678",
            user_id=owner.id,
            resource_id=resource_id,
        )
        repeated = repository.create(
            task_type="job.discovery",
            idempotency_key="request-12345678",
            user_id=owner.id,
            resource_id=resource_id,
        )
        record = session.scalar(
            select(BackgroundTaskRecord).where(BackgroundTaskRecord.id == first.id)
        )

        assert repeated == first
        assert len(repository.list(user_id=owner.id)) == 1
        assert record is not None
        assert record.idempotency_fingerprint != "request-12345678"
        assert len(record.idempotency_fingerprint) == 64


def test_idempotency_is_owner_scoped_and_rejects_changed_inputs():
    database = make_database()
    with database.session() as session:
        users = UserRepository(session)
        owner = users.create(email="owner@example.com", name="Owner")
        other = users.create(email="other@example.com", name="Other")
        repository = BackgroundTaskRepository(session)
        resource_id = uuid4()

        owner_task = repository.create(
            task_type="job.discovery",
            idempotency_key="shared-request-key",
            user_id=owner.id,
            resource_id=resource_id,
        )
        other_task = repository.create(
            task_type="job.discovery",
            idempotency_key="shared-request-key",
            user_id=other.id,
            resource_id=resource_id,
        )

        assert owner_task.id != other_task.id
        with pytest.raises(IdempotencyConflict, match="different task inputs"):
            repository.create(
                task_type="job.discovery",
                idempotency_key="shared-request-key",
                user_id=owner.id,
                resource_id=uuid4(),
            )


def test_tasks_are_owner_scoped_and_support_anonymous_records():
    database = make_database()
    with database.session() as session:
        users = UserRepository(session)
        owner = users.create(email="owner@example.com", name="Owner")
        other = users.create(email="other@example.com", name="Other")
        repository = BackgroundTaskRepository(session)

        owned = repository.create(
            task_type="job.discovery",
            idempotency_key="owned-request-key",
            user_id=owner.id,
        )
        anonymous = repository.create(
            task_type="job.discovery",
            idempotency_key="anonymous-request",
        )

        assert repository.get(task_id=owned.id, user_id=owner.id) == owned
        assert repository.get(task_id=owned.id, user_id=other.id) is None
        assert repository.get(task_id=owned.id, user_id=None) is None
        assert repository.get(task_id=anonymous.id, user_id=None) == anonymous
        assert repository.get(task_id=anonymous.id, user_id=owner.id) is None

        with pytest.raises(ValueError, match="User does not exist"):
            repository.create(
                task_type="job.discovery",
                idempotency_key="missing-user-key",
                user_id=uuid4(),
            )


def test_task_success_and_cancellation_lifecycles_are_enforced():
    database = make_database()
    with database.session() as session:
        repository = BackgroundTaskRepository(session)
        successful = repository.create(
            task_type="job.discovery",
            idempotency_key="successful-request",
        )
        running = repository.start(task_id=successful.id, user_id=None)

        assert running is not None
        assert running.status == BackgroundTaskStatus.RUNNING
        assert running.attempt_count == 1
        assert running.started_at is not None

        completed = repository.complete(task_id=successful.id, user_id=None)
        assert completed is not None
        assert completed.status == BackgroundTaskStatus.SUCCEEDED
        assert completed.finished_at is not None

        with pytest.raises(InvalidTaskTransition, match="current status is 'succeeded'"):
            repository.start(task_id=successful.id, user_id=None)

        cancellable = repository.create(
            task_type="job.discovery",
            idempotency_key="cancelled-request",
        )
        cancelled = repository.cancel(task_id=cancellable.id, user_id=None)
        assert cancelled is not None
        assert cancelled.status == BackgroundTaskStatus.CANCELLED
        assert cancelled.finished_at is not None


def test_retryable_failures_stop_at_the_attempt_limit():
    database = make_database()
    with database.session() as session:
        repository = BackgroundTaskRepository(session)
        task = repository.create(
            task_type="job.discovery",
            idempotency_key="retryable-request",
            max_attempts=2,
        )

        repository.start(task_id=task.id, user_id=None)
        retry = repository.record_failure(
            task_id=task.id,
            user_id=None,
            error_code="provider_timeout",
            retryable=True,
        )
        assert retry is not None
        assert retry.status == BackgroundTaskStatus.QUEUED
        assert retry.error_code == "provider_timeout"
        assert retry.finished_at is None

        repository.start(task_id=task.id, user_id=None)
        failed = repository.record_failure(
            task_id=task.id,
            user_id=None,
            error_code="provider_timeout",
            retryable=True,
        )
        assert failed is not None
        assert failed.status == BackgroundTaskStatus.FAILED
        assert failed.attempt_count == 2
        assert failed.finished_at is not None


def test_failure_records_accept_safe_codes_only():
    database = make_database()
    with database.session() as session:
        repository = BackgroundTaskRepository(session)
        task = repository.create(
            task_type="job.discovery",
            idempotency_key="safe-errors-only",
        )
        repository.start(task_id=task.id, user_id=None)

        with pytest.raises(ValueError, match="Error codes"):
            repository.record_failure(
                task_id=task.id,
                user_id=None,
                error_code="Provider timed out: secret payload",
                retryable=False,
            )

        unchanged = repository.get(task_id=task.id, user_id=None)
        assert unchanged is not None
        assert unchanged.status == BackgroundTaskStatus.RUNNING
        assert unchanged.error_code is None

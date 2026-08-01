from threading import Event

from database.base import Base
from database.repositories.tasks import BackgroundTaskRepository
from database.session import Database
from models.enums import BackgroundTaskStatus
from workers.execution import BackgroundTaskRunner, TaskOperationError
from workers.operations import run_system_probe


def make_database() -> Database:
    database = Database("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(database.engine)
    return database


def create_task(database: Database, *, task_type: str = "system.probe", max_attempts: int = 4):
    with database.session() as session:
        return BackgroundTaskRepository(session).create(
            task_type=task_type,
            idempotency_key=f"{task_type}-request-key",
            max_attempts=max_attempts,
        )


def test_runner_commits_running_state_before_operation_and_completes():
    database = make_database()
    task = create_task(database)
    observed_statuses = []

    def operation(_task):
        with database.session() as session:
            persisted = BackgroundTaskRepository(session).get(
                task_id=task.id,
                user_id=None,
            )
            assert persisted is not None
            observed_statuses.append(persisted.status)

    outcome = BackgroundTaskRunner(database).run(
        task_id=task.id,
        user_id=None,
        operation=operation,
    )

    assert observed_statuses == [BackgroundTaskStatus.RUNNING]
    assert outcome.task.status == BackgroundTaskStatus.SUCCEEDED
    assert outcome.should_retry is False
    assert outcome.duplicate_delivery is False


def test_runner_sanitizes_unexpected_errors_and_requests_bounded_retry():
    database = make_database()
    task = create_task(database, max_attempts=2)

    def unsafe_operation(_task):
        raise RuntimeError("sensitive provider response")

    first = BackgroundTaskRunner(database).run(
        task_id=task.id,
        user_id=None,
        operation=unsafe_operation,
    )
    second = BackgroundTaskRunner(database).run(
        task_id=task.id,
        user_id=None,
        operation=unsafe_operation,
    )

    assert first.task.status == BackgroundTaskStatus.QUEUED
    assert first.task.error_code == "unexpected_error"
    assert first.should_retry is True
    assert second.task.status == BackgroundTaskStatus.FAILED
    assert second.task.error_code == "unexpected_error"
    assert second.should_retry is False
    assert "sensitive provider response" not in repr(second)


def test_runner_respects_permanent_operation_failures():
    database = make_database()
    task = create_task(database)

    def rejected_operation(_task):
        raise TaskOperationError("invalid_task_input", retryable=False)

    outcome = BackgroundTaskRunner(database).run(
        task_id=task.id,
        user_id=None,
        operation=rejected_operation,
    )

    assert outcome.task.status == BackgroundTaskStatus.FAILED
    assert outcome.task.error_code == "invalid_task_input"
    assert outcome.should_retry is False


def test_runner_suppresses_duplicate_terminal_delivery():
    database = make_database()
    task = create_task(database)
    executions = []
    runner = BackgroundTaskRunner(database)

    first = runner.run(
        task_id=task.id,
        user_id=None,
        operation=lambda _task: executions.append("executed"),
    )
    duplicate = runner.run(
        task_id=task.id,
        user_id=None,
        operation=lambda _task: executions.append("executed-again"),
    )

    assert first.task.status == BackgroundTaskStatus.SUCCEEDED
    assert duplicate.task.status == BackgroundTaskStatus.SUCCEEDED
    assert duplicate.duplicate_delivery is True
    assert executions == ["executed"]


def test_system_probe_rejects_another_task_type_without_external_work():
    database = make_database()
    task = create_task(database, task_type="job.discovery")

    outcome = BackgroundTaskRunner(database).run(
        task_id=task.id,
        user_id=None,
        operation=run_system_probe,
    )

    assert outcome.task.status == BackgroundTaskStatus.FAILED
    assert outcome.task.error_code == "invalid_task_type"


def test_runner_heartbeats_during_long_operations():
    database = make_database()
    task = create_task(database)

    def operation(_task):
        Event().wait(0.05)

    outcome = BackgroundTaskRunner(
        database,
        heartbeat_interval_seconds=0.01,
    ).run(
        task_id=task.id,
        user_id=None,
        operation=operation,
    )

    assert outcome.task.status == BackgroundTaskStatus.SUCCEEDED
    assert outcome.task.heartbeat_at is not None
    assert outcome.task.started_at is not None
    assert outcome.task.heartbeat_at >= outcome.task.started_at

from unittest.mock import Mock

from dramatiq import Worker
from dramatiq.brokers.stub import StubBroker

from core.config import Settings
from database.base import Base
from database.repositories.tasks import BackgroundTaskRepository
from database.session import Database
from models.enums import BackgroundTaskStatus
from workers.actors import build_system_probe_actor, build_task_maintenance_actor
from workers.execution import BackgroundTaskRunner
from workers.middleware import DatabaseDisposalMiddleware


def test_system_probe_actor_uses_bounded_execution_options():
    broker = StubBroker()
    database = Database("sqlite+pysqlite:///:memory:")
    settings = Settings(
        _env_file=None,
        worker_queue_name="worker_test",
        worker_max_retries=2,
        worker_time_limit_ms=45_000,
        worker_message_max_age_ms=90_000,
    )

    actor = build_system_probe_actor(
        broker=broker,
        runner=BackgroundTaskRunner(database),
        app_settings=settings,
        actor_name="system_probe_options_test",
    )

    assert actor.queue_name == "worker_test"
    assert actor.options["max_retries"] == 2
    assert actor.options["time_limit"] == 45_000
    assert actor.options["max_age"] == 90_000
    assert actor.options["min_backoff"] == 1_000
    assert actor.options["max_backoff"] == 30_000


def test_system_probe_actor_executes_with_stub_broker():
    broker = StubBroker()
    database = Database("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(database.engine)
    settings = Settings(_env_file=None, worker_queue_name="worker_test")
    with database.session() as session:
        task = BackgroundTaskRepository(session).create(
            task_type="system.probe",
            idempotency_key="stub-broker-probe",
        )
    actor = build_system_probe_actor(
        broker=broker,
        runner=BackgroundTaskRunner(database),
        app_settings=settings,
        actor_name="system_probe_stub_test",
    )
    worker = Worker(
        broker,
        queues={actor.queue_name},
        worker_threads=1,
        worker_timeout=100,
    )

    try:
        worker.start()
        actor.send(str(task.id))
        broker.join(actor.queue_name, timeout=5_000)
        worker.join()
    finally:
        worker.stop(timeout=5_000)

    with database.session() as session:
        completed = BackgroundTaskRepository(session).get(
            task_id=task.id,
            user_id=None,
        )
        assert completed is not None
        assert completed.status == BackgroundTaskStatus.SUCCEEDED


def test_worker_shutdown_disposes_database_connections():
    database = Mock()
    discovery = Mock()
    middleware = DatabaseDisposalMiddleware(database, discovery)

    middleware.after_worker_shutdown(Mock(), Mock())

    database.dispose.assert_called_once_with()
    discovery.close.assert_called_once_with()


def test_task_maintenance_actor_uses_bounded_worker_options():
    broker = StubBroker()
    maintenance = Mock()
    settings = Settings(
        _env_file=None,
        worker_queue_name="maintenance_test",
        worker_max_retries=2,
    )
    actor = build_task_maintenance_actor(
        broker=broker,
        maintenance=maintenance,
        app_settings=settings,
        actor_name="task_maintenance_test",
    )

    actor.fn()

    maintenance.run.assert_called_once_with()
    assert actor.queue_name == "maintenance_test"
    assert actor.options["max_retries"] == 2

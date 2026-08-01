"""Live Redis integration gate for the worker broker."""

import os
from uuid import uuid4

import pytest
from dramatiq import Worker
from dramatiq.brokers.redis import RedisBroker

from core.config import Settings
from database.base import Base
from database.repositories.tasks import BackgroundTaskRepository
from database.session import Database
from models.enums import BackgroundTaskStatus
from workers.actors import build_system_probe_actor
from workers.broker import build_broker
from workers.execution import BackgroundTaskRunner


@pytest.mark.redis
def test_redis_broker_connects_with_explicit_test_url():
    redis_url = os.getenv("TEST_REDIS_URL")
    if redis_url is None:
        pytest.skip("TEST_REDIS_URL is required for the Redis integration gate.")

    broker = build_broker(
        Settings(
            _env_file=None,
            redis_url=redis_url,
            worker_broker_namespace="careercompass_test",
        )
    )
    try:
        assert broker.client.ping() is True
        assert broker.namespace == "careercompass_test"
    finally:
        broker.close()


@pytest.mark.redis
def test_system_probe_executes_through_live_redis(tmp_path):
    redis_url = os.getenv("TEST_REDIS_URL")
    if redis_url is None:
        pytest.skip("TEST_REDIS_URL is required for the Redis integration gate.")

    suffix = uuid4().hex
    broker = RedisBroker(
        url=redis_url,
        namespace=f"careercompass-test-{suffix}",
    )
    database = Database(f"sqlite+pysqlite:///{tmp_path / 'worker.db'}")
    Base.metadata.create_all(database.engine)
    settings = Settings(
        _env_file=None,
        worker_queue_name=f"probe_{suffix}",
        worker_max_retries=0,
    )
    with database.session() as session:
        task = BackgroundTaskRepository(session).create(
            task_type="system.probe",
            idempotency_key=f"redis-probe-{suffix}",
            max_attempts=1,
        )
    actor = build_system_probe_actor(
        broker=broker,
        runner=BackgroundTaskRunner(database),
        app_settings=settings,
        actor_name=f"system_probe_{suffix}",
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
        broker.join(actor.queue_name, timeout=10_000)
        worker.join()
        with database.session() as session:
            completed = BackgroundTaskRepository(session).get(
                task_id=task.id,
                user_id=None,
            )
            assert completed is not None
            assert completed.status == BackgroundTaskStatus.SUCCEEDED
    finally:
        worker.stop(timeout=5_000)
        broker.flush_all()
        broker.close()
        database.dispose()

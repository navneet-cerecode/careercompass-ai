"""Live Redis integration gate for the worker broker."""

import os
from uuid import uuid4

import pytest
from dramatiq import Worker
from dramatiq.brokers.redis import RedisBroker

from core.config import Settings
from database.base import Base
from database.repositories.tasks import BackgroundTaskRepository
from database.repositories.job_discovery_tasks import JobDiscoveryTaskRepository
from database.session import Database
from models.enums import BackgroundTaskStatus
from models.job import Job
from api.schemas.job_search import JobSearchRequest
from services.job_discovery.discovery_service import JobDiscoveryResult
from workers.actors import build_job_discovery_actor, build_system_probe_actor
from workers.broker import build_broker
from workers.execution import BackgroundTaskRunner
from workers.job_discovery import RunJobDiscovery


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


@pytest.mark.redis
def test_job_discovery_executes_through_live_redis(tmp_path):
    redis_url = os.getenv("TEST_REDIS_URL")
    if redis_url is None:
        pytest.skip("TEST_REDIS_URL is required for the Redis integration gate.")

    suffix = uuid4().hex
    broker = RedisBroker(
        url=redis_url,
        namespace=f"careercompass-discovery-test-{suffix}",
    )
    database = Database(f"sqlite+pysqlite:///{tmp_path / 'discovery-worker.db'}")
    Base.metadata.create_all(database.engine)
    settings = Settings(
        _env_file=None,
        worker_queue_name=f"discovery_{suffix}",
        worker_max_retries=0,
    )
    with database.session() as session:
        task, _ = JobDiscoveryTaskRepository(session).create(
            request=JobSearchRequest(role="AI Engineer", location="India"),
            idempotency_key=f"redis-discovery-{suffix}",
            max_attempts=1,
        )

    class StubDiscovery:
        def discover_jobs_with_status(self, query):
            return JobDiscoveryResult(
                jobs=(
                    Job(
                        title=query.role,
                        company="Redis Integration",
                        location=query.location,
                        description="Validate the complete discovery worker boundary.",
                        url="https://example.com/redis-discovery",
                    ),
                ),
                failures=(),
                providers_attempted=1,
                providers_succeeded=1,
            )

    actor = build_job_discovery_actor(
        broker=broker,
        runner=BackgroundTaskRunner(database),
        operation=RunJobDiscovery(database, StubDiscovery()),
        app_settings=settings,
        actor_name=f"job_discovery_{suffix}",
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
            result = JobDiscoveryTaskRepository(session).get_result(task.id)
        assert completed is not None
        assert completed.status == BackgroundTaskStatus.SUCCEEDED
        assert result is not None
        assert result[1][0].company == "Redis Integration"
    finally:
        worker.stop(timeout=5_000)
        broker.flush_all()
        broker.close()
        database.dispose()

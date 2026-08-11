"""Measure synthetic task throughput through PostgreSQL, Redis, and Dramatiq."""

from __future__ import annotations

import argparse
import json
import os
import time
from uuid import uuid4

from alembic import command
from dramatiq import Worker
from dramatiq.brokers.redis import RedisBroker
from sqlalchemy import delete
from sqlalchemy.engine import make_url

from core.config import Settings
from database.alembic import build_alembic_config
from database.models.tasks import BackgroundTaskRecord
from database.repositories.tasks import BackgroundTaskRepository
from database.session import Database
from models.enums import BackgroundTaskStatus
from workers.actors import build_system_probe_actor
from workers.execution import BackgroundTaskRunner


def require_test_database_url(value: str | None) -> str:
    if value is None:
        raise ValueError("TEST_DATABASE_URL is required.")
    parsed = make_url(value)
    if not parsed.drivername.startswith("postgresql") or not (parsed.database or "").endswith(
        "_test"
    ):
        raise ValueError("TEST_DATABASE_URL must use a dedicated PostgreSQL *_test database.")
    return value


def run(*, task_count: int, threads: int, timeout_seconds: float) -> dict[str, float | int]:
    database_url = require_test_database_url(os.getenv("TEST_DATABASE_URL"))
    command.upgrade(build_alembic_config(database_url), "head")
    database = Database(database_url)
    redis_url = os.getenv("TEST_REDIS_URL")
    if redis_url is None:
        database.dispose()
        raise ValueError("TEST_REDIS_URL is required.")

    suffix = uuid4().hex
    queue_name = f"stress_{suffix}"
    broker = RedisBroker(url=redis_url, namespace=f"solarahire-stress-{suffix}")
    settings = Settings(
        _env_file=None,
        worker_queue_name=queue_name,
        worker_max_retries=0,
    )
    actor = build_system_probe_actor(
        broker=broker,
        runner=BackgroundTaskRunner(database),
        app_settings=settings,
        actor_name=f"system_probe_{suffix}",
    )
    worker = Worker(
        broker,
        queues={queue_name},
        worker_threads=threads,
        worker_timeout=100,
    )
    task_ids = []
    try:
        with database.session() as session:
            repository = BackgroundTaskRepository(session)
            for index in range(task_count):
                task = repository.create(
                    task_type="system.probe",
                    idempotency_key=f"stress-{suffix}-{index}",
                    max_attempts=1,
                )
                task_ids.append(task.id)

        worker.start()
        started = time.perf_counter()
        for task_id in task_ids:
            actor.send(str(task_id))
        broker.join(queue_name, timeout=int(timeout_seconds * 1000))
        worker.join()
        elapsed = time.perf_counter() - started

        with database.session() as session:
            completed = [
                BackgroundTaskRepository(session).get(task_id=task_id, user_id=None)
                for task_id in task_ids
            ]
        succeeded = sum(
            task is not None and task.status == BackgroundTaskStatus.SUCCEEDED for task in completed
        )
        return {
            "tasks": task_count,
            "succeeded": succeeded,
            "failed": task_count - succeeded,
            "elapsed_seconds": round(elapsed, 3),
            "tasks_per_second": round(task_count / elapsed, 2),
        }
    finally:
        try:
            worker.stop(timeout=5_000)
            broker.flush_all()
            keys = tuple(broker.client.scan_iter(match=f"{broker.namespace}:*"))
            if keys:
                broker.client.delete(*keys)
        finally:
            try:
                broker.close()
            finally:
                try:
                    if task_ids:
                        with database.session() as session:
                            session.execute(
                                delete(BackgroundTaskRecord).where(
                                    BackgroundTaskRecord.id.in_(task_ids)
                                )
                            )
                finally:
                    database.dispose()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tasks", type=int, default=50)
    parser.add_argument("--threads", type=int, default=4)
    parser.add_argument("--timeout-seconds", type=float, default=30)
    args = parser.parse_args()
    if args.tasks < 1 or args.threads < 1 or args.timeout_seconds <= 0:
        parser.error("tasks, threads, and timeout must be positive")
    try:
        result = run(
            task_count=args.tasks,
            threads=args.threads,
            timeout_seconds=args.timeout_seconds,
        )
    except ValueError as error:
        parser.error(str(error))
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())

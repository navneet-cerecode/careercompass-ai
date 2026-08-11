"""Production Dramatiq module loaded by the worker command."""

import dramatiq

from core.config import settings
from database.session import Database
from services.job_discovery.discovery_service import JobDiscoveryService
from workers.actors import (
    build_job_discovery_actor,
    build_system_probe_actor,
    build_task_maintenance_actor,
)
from workers.broker import build_broker
from workers.execution import BackgroundTaskRunner
from workers.middleware import DatabaseDisposalMiddleware
from workers.job_discovery import RunJobDiscovery
from workers.maintenance import TaskMaintenance
from workers.outbox import TaskOutboxDispatcher
from workers.publisher import BackgroundTaskPublisher

broker = build_broker(settings)
database = Database(
    settings.require_database_url(),
    pool_size=settings.database_pool_size,
    pool_timeout_seconds=settings.database_pool_timeout_seconds,
)
job_discovery_service = JobDiscoveryService()
broker.add_middleware(DatabaseDisposalMiddleware(database, job_discovery_service))
dramatiq.set_broker(broker)

task_runner = BackgroundTaskRunner(
    database,
    heartbeat_interval_seconds=settings.worker_heartbeat_seconds,
)
system_probe = build_system_probe_actor(
    broker=broker,
    runner=task_runner,
    app_settings=settings,
)
job_discovery = build_job_discovery_actor(
    broker=broker,
    runner=task_runner,
    operation=RunJobDiscovery(database, job_discovery_service),
    app_settings=settings,
)
task_publisher = BackgroundTaskPublisher(
    broker,
    queue_name=settings.worker_queue_name,
)
task_maintenance = build_task_maintenance_actor(
    broker=broker,
    maintenance=TaskMaintenance(
        database=database,
        dispatcher=TaskOutboxDispatcher(database, task_publisher),
        settings=settings,
    ),
    app_settings=settings,
)

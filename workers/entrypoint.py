"""Production Dramatiq module loaded by the worker command."""

import dramatiq

from core.config import settings
from database.session import Database
from workers.actors import build_system_probe_actor
from workers.broker import build_broker
from workers.execution import BackgroundTaskRunner
from workers.middleware import DatabaseDisposalMiddleware

broker = build_broker(settings)
database = Database(
    settings.require_database_url(),
    pool_size=settings.database_pool_size,
    pool_timeout_seconds=settings.database_pool_timeout_seconds,
)
broker.add_middleware(DatabaseDisposalMiddleware(database))
dramatiq.set_broker(broker)

task_runner = BackgroundTaskRunner(database)
system_probe = build_system_probe_actor(
    broker=broker,
    runner=task_runner,
    app_settings=settings,
)

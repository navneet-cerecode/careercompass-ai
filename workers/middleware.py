"""Worker lifecycle middleware."""

from dramatiq import Broker, Middleware, Worker

from database.session import Database


class DatabaseDisposalMiddleware(Middleware):
    """Release pooled database connections during worker shutdown."""

    def __init__(self, database: Database) -> None:
        self.database = database

    def after_worker_shutdown(self, broker: Broker, worker: Worker) -> None:
        self.database.dispose()

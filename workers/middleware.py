"""Worker lifecycle middleware."""

from dramatiq import Broker, Middleware, Worker

from database.session import Database


class DatabaseDisposalMiddleware(Middleware):
    """Release process-owned resources during worker shutdown."""

    def __init__(self, database: Database, *resources) -> None:
        self.database = database
        self.resources = resources

    def after_worker_shutdown(self, broker: Broker, worker: Worker) -> None:
        for resource in self.resources:
            resource.close()
        self.database.dispose()

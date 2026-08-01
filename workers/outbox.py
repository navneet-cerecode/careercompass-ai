"""Publish durable task-outbox records to the broker."""

from uuid import UUID

from database.repositories.task_outbox import TaskOutboxMessage, TaskOutboxRepository
from database.session import Database
from workers.publisher import BackgroundTaskPublisher


class TaskOutboxDispatcher:
    def __init__(
        self,
        database: Database,
        publisher: BackgroundTaskPublisher,
    ) -> None:
        self.database = database
        self.publisher = publisher

    def dispatch_task(self, task_id: UUID) -> bool:
        with self.database.session() as session:
            message = TaskOutboxRepository(session).get_pending_for_task(task_id)
        if message is None:
            return False
        self._publish(message)
        return True

    def dispatch_pending(self, *, limit: int) -> tuple[int, int]:
        with self.database.session() as session:
            messages = TaskOutboxRepository(session).list_pending(limit=limit)
        published = 0
        failed = 0
        for message in messages:
            try:
                self._publish(message)
                published += 1
            except Exception:
                failed += 1
        return published, failed

    def _publish(self, message: TaskOutboxMessage) -> None:
        try:
            self.publisher.enqueue(
                actor_name=message.actor_name,
                task_id=message.task_id,
            )
        except Exception:
            with self.database.session() as session:
                TaskOutboxRepository(session).record_attempt(
                    message.id,
                    published=False,
                )
            raise
        with self.database.session() as session:
            TaskOutboxRepository(session).record_attempt(
                message.id,
                published=True,
            )

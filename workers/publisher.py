"""Broker publisher that transports identifiers, never user payloads."""

from uuid import UUID

from dramatiq import Broker, Message


class BackgroundTaskPublisher:
    def __init__(self, broker: Broker, *, queue_name: str) -> None:
        self.broker = broker
        self.queue_name = queue_name

    def enqueue_job_discovery(self, task_id: UUID) -> None:
        self.broker.enqueue(
            Message(
                queue_name=self.queue_name,
                actor_name="job_discovery",
                args=(str(task_id), None),
                kwargs={},
                options={},
            )
        )

"""Broker publisher that transports identifiers, never user payloads."""

from uuid import UUID

from dramatiq import Broker, Message


class BackgroundTaskPublisher:
    def __init__(self, broker: Broker, *, queue_name: str) -> None:
        self.broker = broker
        self.queue_name = queue_name

    def enqueue_job_discovery(self, task_id: UUID) -> None:
        self.enqueue(actor_name="job_discovery", task_id=task_id)

    def enqueue(self, *, actor_name: str, task_id: UUID) -> None:
        if actor_name != "job_discovery":
            raise ValueError("Unsupported task actor.")
        self.broker.enqueue(
            Message(
                queue_name=self.queue_name,
                actor_name=actor_name,
                args=(str(task_id), None),
                kwargs={},
                options={},
            )
        )

    def enqueue_maintenance(self) -> None:
        self.broker.enqueue(
            Message(
                queue_name=self.queue_name,
                actor_name="task_maintenance",
                args=(),
                kwargs={},
                options={},
            )
        )

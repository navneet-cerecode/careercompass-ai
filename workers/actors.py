"""Actor factories with explicit infrastructure dependencies."""

import logging
from uuid import UUID

import dramatiq
from dramatiq import Broker

from core.config import Settings
from workers.execution import BackgroundTaskRunner, TaskNotFoundError
from workers.operations import run_system_probe

logger = logging.getLogger(__name__)


class RetryableTaskExecution(RuntimeError):
    """A sanitized signal that allows Dramatiq to schedule a bounded retry."""


def build_system_probe_actor(
    *,
    broker: Broker,
    runner: BackgroundTaskRunner,
    app_settings: Settings,
    actor_name: str = "system_probe",
) -> dramatiq.Actor:
    """Build the first harmless worker actor."""

    @dramatiq.actor(
        actor_name=actor_name,
        broker=broker,
        queue_name=app_settings.worker_queue_name,
        max_retries=app_settings.worker_max_retries,
        min_backoff=1_000,
        max_backoff=30_000,
        time_limit=app_settings.worker_time_limit_ms,
        max_age=app_settings.worker_message_max_age_ms,
    )
    def system_probe(task_id: str, user_id: str | None = None) -> None:
        try:
            parsed_task_id = UUID(task_id)
            parsed_user_id = UUID(user_id) if user_id is not None else None
        except ValueError:
            logger.warning("Rejected worker message with invalid identifiers.")
            return

        try:
            outcome = runner.run(
                task_id=parsed_task_id,
                user_id=parsed_user_id,
                operation=run_system_probe,
            )
        except TaskNotFoundError:
            logger.warning("Rejected worker message for an unavailable task.")
            return
        except Exception as error:
            logger.error(
                "Worker runtime failed before task completion; error_type=%s",
                type(error).__name__,
            )
            raise RetryableTaskExecution("task_runtime_unavailable") from None

        if outcome.should_retry:
            raise RetryableTaskExecution(outcome.task.error_code or "retryable_failure")

    return system_probe

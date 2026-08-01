"""Safe operations used to prove the worker execution boundary."""

from models.background_task import BackgroundTask
from workers.execution import TaskOperationError


def run_system_probe(task: BackgroundTask) -> None:
    """Validate worker delivery without calling providers or handling user data."""
    if task.task_type != "system.probe":
        raise TaskOperationError("invalid_task_type", retryable=False)

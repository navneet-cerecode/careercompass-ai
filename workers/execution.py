"""Transaction-safe execution boundary for durable background tasks."""

import logging
import re
from collections.abc import Callable
from dataclasses import dataclass
from threading import Event, Thread
from uuid import UUID

from database.repositories.tasks import (
    BackgroundTaskRepository,
    InvalidTaskTransition,
)
from database.session import Database
from models.background_task import BackgroundTask
from models.enums import BackgroundTaskStatus

TaskOperation = Callable[[BackgroundTask], None]
ERROR_CODE_PATTERN = re.compile(r"^[a-z][a-z0-9_]{0,99}$")
logger = logging.getLogger(__name__)


class TaskOperationError(RuntimeError):
    """A sanitized application-operation failure."""

    def __init__(self, error_code: str, *, retryable: bool) -> None:
        normalized_code = error_code.strip().casefold()
        if ERROR_CODE_PATTERN.fullmatch(normalized_code) is None:
            raise ValueError("Task operation error codes must be safe identifiers.")
        super().__init__(normalized_code)
        self.error_code = normalized_code
        self.retryable = retryable


class TaskNotFoundError(RuntimeError):
    """Raised when a broker message references no task in its owner scope."""

    def __init__(self) -> None:
        super().__init__("task_not_found")


@dataclass(frozen=True)
class TaskExecutionOutcome:
    task: BackgroundTask
    should_retry: bool = False
    duplicate_delivery: bool = False


class BackgroundTaskRunner:
    """Execute one operation without holding a database transaction open."""

    def __init__(
        self,
        database: Database,
        *,
        heartbeat_interval_seconds: float = 30,
    ) -> None:
        if heartbeat_interval_seconds <= 0:
            raise ValueError("Heartbeat interval must be positive.")
        self.database = database
        self.heartbeat_interval_seconds = heartbeat_interval_seconds

    def run(
        self,
        *,
        task_id: UUID,
        user_id: UUID | None,
        operation: TaskOperation,
    ) -> TaskExecutionOutcome:
        started = self._start(task_id=task_id, user_id=user_id)
        if started.status != BackgroundTaskStatus.RUNNING:
            return TaskExecutionOutcome(
                task=started,
                duplicate_delivery=True,
            )

        stop_heartbeat = Event()
        heartbeat_thread = Thread(
            target=self._heartbeat_loop,
            kwargs={
                "task_id": task_id,
                "user_id": user_id,
                "stop": stop_heartbeat,
            },
            daemon=True,
            name=f"task-heartbeat-{task_id}",
        )
        heartbeat_thread.start()
        try:
            operation(started)
        except TaskOperationError as error:
            return self._fail(
                task_id=task_id,
                user_id=user_id,
                error_code=error.error_code,
                retryable=error.retryable,
            )
        except Exception as error:
            logger.error(
                "Task operation failed; error_type=%s",
                type(error).__name__,
            )
            return self._fail(
                task_id=task_id,
                user_id=user_id,
                error_code="unexpected_error",
                retryable=True,
            )
        finally:
            stop_heartbeat.set()
            heartbeat_thread.join(timeout=self.heartbeat_interval_seconds + 1)

        with self.database.session() as session:
            completed = BackgroundTaskRepository(session).complete(
                task_id=task_id,
                user_id=user_id,
            )
            if completed is None:
                raise TaskNotFoundError
            return TaskExecutionOutcome(task=completed)

    def _heartbeat_loop(
        self,
        *,
        task_id: UUID,
        user_id: UUID | None,
        stop: Event,
    ) -> None:
        while not stop.wait(self.heartbeat_interval_seconds):
            try:
                with self.database.session() as session:
                    task = BackgroundTaskRepository(session).heartbeat(
                        task_id=task_id,
                        user_id=user_id,
                    )
                if task is None or task.status != BackgroundTaskStatus.RUNNING:
                    return
            except Exception as error:
                logger.error(
                    "Task heartbeat failed; error_type=%s",
                    type(error).__name__,
                )
                return

    def _start(
        self,
        *,
        task_id: UUID,
        user_id: UUID | None,
    ) -> BackgroundTask:
        with self.database.session() as session:
            repository = BackgroundTaskRepository(session)
            try:
                started = repository.start(task_id=task_id, user_id=user_id)
            except InvalidTaskTransition:
                existing = repository.get(task_id=task_id, user_id=user_id)
                if existing is None:
                    raise TaskNotFoundError from None
                return existing
            if started is None:
                raise TaskNotFoundError
            return started

    def _fail(
        self,
        *,
        task_id: UUID,
        user_id: UUID | None,
        error_code: str,
        retryable: bool,
    ) -> TaskExecutionOutcome:
        with self.database.session() as session:
            failed = BackgroundTaskRepository(session).record_failure(
                task_id=task_id,
                user_id=user_id,
                error_code=error_code,
                retryable=retryable,
            )
            if failed is None:
                raise TaskNotFoundError
            return TaskExecutionOutcome(
                task=failed,
                should_retry=failed.status == BackgroundTaskStatus.QUEUED,
            )

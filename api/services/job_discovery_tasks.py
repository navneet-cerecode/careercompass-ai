"""Application service for creating and safely polling discovery tasks."""

from dataclasses import dataclass
from uuid import UUID

from api.errors import APIError
from api.schemas.job_search import JobSearchRequest
from api.services.task_capability import TaskCapability
from database.repositories.job_discovery_tasks import JobDiscoveryTaskRepository
from database.repositories.tasks import BackgroundTaskRepository
from database.repositories.tasks import InvalidTaskTransition
from database.session import Database
from models.background_task import BackgroundTask
from models.enums import BackgroundTaskStatus
from models.job import Job
from models.job_discovery_task import JobDiscoveryOutcome
from workers.publisher import BackgroundTaskPublisher
from workers.outbox import TaskOutboxDispatcher


@dataclass(frozen=True)
class JobDiscoveryTaskSnapshot:
    task: BackgroundTask
    outcome: JobDiscoveryOutcome | None = None
    jobs: tuple[Job, ...] = ()


class JobDiscoveryTaskService:
    def __init__(
        self,
        *,
        database: Database,
        publisher: BackgroundTaskPublisher,
        capability: TaskCapability,
        max_attempts: int,
    ) -> None:
        self.database = database
        self.publisher = publisher
        self.capability = capability
        self.max_attempts = max_attempts

    def create(
        self,
        *,
        request: JobSearchRequest,
        idempotency_key: str,
    ) -> tuple[JobDiscoveryTaskSnapshot, str]:
        with self.database.session() as session:
            task, _ = JobDiscoveryTaskRepository(session).create(
                request=request,
                idempotency_key=idempotency_key,
                max_attempts=self.max_attempts,
            )
        if task.status.value == "queued":
            try:
                TaskOutboxDispatcher(
                    self.database,
                    self.publisher,
                ).dispatch_task(task.id)
            except Exception as error:
                raise APIError(
                    503,
                    "worker_unavailable",
                    "Job discovery could not be queued. Retry this search shortly.",
                ) from error
        return JobDiscoveryTaskSnapshot(task=task), self.capability.issue(task.id)

    def get(self, *, task_id: UUID, token: str) -> JobDiscoveryTaskSnapshot | None:
        if not self.capability.verify(task_id, token):
            return None
        with self.database.session() as session:
            task = BackgroundTaskRepository(session).get(task_id=task_id, user_id=None)
            if task is None or task.task_type != "job.discovery":
                return None
            if task.status != BackgroundTaskStatus.SUCCEEDED:
                return JobDiscoveryTaskSnapshot(task=task)
            result = JobDiscoveryTaskRepository(session).get_result(task_id)
            if result is None:
                return JobDiscoveryTaskSnapshot(task=task)
            outcome, jobs = result
            return JobDiscoveryTaskSnapshot(task=task, outcome=outcome, jobs=jobs)

    def cancel(self, *, task_id: UUID, token: str) -> JobDiscoveryTaskSnapshot | None:
        if not self.capability.verify(task_id, token):
            return None
        with self.database.session() as session:
            repository = BackgroundTaskRepository(session)
            task = repository.get(task_id=task_id, user_id=None)
            if task is None or task.task_type != "job.discovery":
                return None
            try:
                cancelled = repository.request_cancel(
                    task_id=task_id,
                    user_id=None,
                )
            except InvalidTaskTransition as error:
                raise APIError(
                    409,
                    "task_not_cancellable",
                    "This search has already finished and cannot be cancelled.",
                ) from error
            assert cancelled is not None
            return JobDiscoveryTaskSnapshot(task=cancelled)

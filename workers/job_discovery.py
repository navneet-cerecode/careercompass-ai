"""Worker-side operation for durable job discovery."""

from database.repositories.job_discovery_tasks import JobDiscoveryTaskRepository
from database.session import Database
from models.background_task import BackgroundTask
from models.job_discovery_task import JobDiscoveryOutcome, JobDiscoveryOutcomeStatus
from services.job_discovery.discovery_service import JobDiscoveryService
from services.job_discovery.providers.contracts import JobSearchQuery
from workers.execution import TaskOperationError


class RunJobDiscovery:
    def __init__(
        self,
        database: Database,
        discovery: JobDiscoveryService,
    ) -> None:
        self.database = database
        self.discovery = discovery

    def __call__(self, task: BackgroundTask) -> None:
        if task.task_type != "job.discovery":
            raise TaskOperationError("invalid_task_type", retryable=False)
        with self.database.session() as session:
            request = JobDiscoveryTaskRepository(session).get_request(task.id)
        if request is None:
            raise TaskOperationError("discovery_request_missing", retryable=False)

        result = self.discovery.discover_jobs_with_status(
            JobSearchQuery(
                role=request.role,
                location=request.location,
                country=request.country,
                page=request.page,
                page_size=request.page_size,
                remote_only=request.remote_only,
                employment_types=list(request.employment_types),
                date_posted=request.date_posted,
            )
        )
        if result.failures and result.providers_succeeded:
            status = JobDiscoveryOutcomeStatus.PARTIAL
        elif result.failures:
            status = JobDiscoveryOutcomeStatus.FAILED
        else:
            status = JobDiscoveryOutcomeStatus.COMPLETE

        with self.database.session() as session:
            JobDiscoveryTaskRepository(session).save_result(
                task_id=task.id,
                jobs=result.jobs,
                outcome=JobDiscoveryOutcome(
                    status=status,
                    provider_names_failed=tuple(
                        failure.provider_name for failure in result.failures
                    ),
                    providers_attempted=result.providers_attempted,
                    providers_succeeded=result.providers_succeeded,
                ),
            )

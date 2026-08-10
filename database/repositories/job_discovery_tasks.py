"""Persistence boundary for asynchronous discovery inputs and ordered results."""

from datetime import datetime
from typing import NamedTuple
from uuid import UUID

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from api.schemas.job_search import JobSearchRequest
from database.models.job_discovery_tasks import (
    JobDiscoveryTaskRecord,
    JobDiscoveryTaskResultRecord,
)
from database.models.tasks import BackgroundTaskRecord
from database.repositories.jobs import JobRepository
from database.repositories.tasks import BackgroundTaskRepository, IdempotencyConflict
from database.repositories.task_outbox import TaskOutboxRepository
from models.background_task import BackgroundTask
from models.job import Job
from models.job_discovery_task import JobDiscoveryOutcome, JobDiscoveryOutcomeStatus


class JobHistoryObservation(NamedTuple):
    job_id: UUID
    role: str
    first_observed_at: datetime
    last_observed_at: datetime


class JobDiscoveryTaskRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(
        self,
        *,
        request: JobSearchRequest,
        idempotency_key: str,
        max_attempts: int,
        user_id: UUID | None = None,
    ) -> tuple[BackgroundTask, bool]:
        task = BackgroundTaskRepository(self.session).create(
            task_type="job.discovery",
            idempotency_key=idempotency_key,
            max_attempts=max_attempts,
            user_id=user_id,
        )
        record = self.session.get(JobDiscoveryTaskRecord, task.id)
        if record is not None:
            if self._request_from_record(record) != request:
                raise IdempotencyConflict(
                    "Idempotency key was already used for different discovery inputs."
                )
            TaskOutboxRepository(self.session).ensure(
                task_id=task.id,
                actor_name="job_discovery",
            )
            return task, False

        self.session.add(
            JobDiscoveryTaskRecord(
                task_id=task.id,
                role=request.role,
                location=request.location,
                country=request.country,
                page=request.page,
                page_size=request.page_size,
                remote_only=request.remote_only,
                employment_types=[item.value for item in request.employment_types],
                date_posted=request.date_posted.value,
            )
        )
        self.session.flush()
        TaskOutboxRepository(self.session).ensure(
            task_id=task.id,
            actor_name="job_discovery",
        )
        return task, True

    def get_request(self, task_id: UUID) -> JobSearchRequest | None:
        record = self.session.get(JobDiscoveryTaskRecord, task_id)
        return self._request_from_record(record) if record is not None else None

    def list_user_job_ids(self, *, user_id: UUID, limit: int = 100) -> tuple[UUID, ...]:
        return tuple(
            observation.job_id
            for observation in self.list_user_job_observations(
                user_id=user_id,
                limit=limit,
            )
        )

    def list_user_job_observations(
        self,
        *,
        user_id: UUID,
        limit: int = 100,
    ) -> tuple[JobHistoryObservation, ...]:
        observed_rows = self.session.execute(
            select(
                JobDiscoveryTaskResultRecord.job_id,
                func.min(BackgroundTaskRecord.created_at),
                func.max(BackgroundTaskRecord.updated_at),
            )
            .join(
                BackgroundTaskRecord,
                BackgroundTaskRecord.id == JobDiscoveryTaskResultRecord.task_id,
            )
            .where(
                BackgroundTaskRecord.user_id == user_id,
                BackgroundTaskRecord.status == "succeeded",
            )
            .group_by(JobDiscoveryTaskResultRecord.job_id)
            .order_by(func.max(BackgroundTaskRecord.updated_at).desc())
            .limit(limit)
        ).all()
        if not observed_rows:
            return ()

        job_ids = tuple(row[0] for row in observed_rows)
        latest_roles: dict[UUID, str] = {}
        for job_id, role in self.session.execute(
            select(
                JobDiscoveryTaskResultRecord.job_id,
                JobDiscoveryTaskRecord.role,
            )
            .join(
                JobDiscoveryTaskRecord,
                JobDiscoveryTaskRecord.task_id == JobDiscoveryTaskResultRecord.task_id,
            )
            .join(
                BackgroundTaskRecord,
                BackgroundTaskRecord.id == JobDiscoveryTaskResultRecord.task_id,
            )
            .where(
                JobDiscoveryTaskResultRecord.job_id.in_(job_ids),
                BackgroundTaskRecord.user_id == user_id,
                BackgroundTaskRecord.status == "succeeded",
            )
            .order_by(BackgroundTaskRecord.updated_at.desc())
        ).all():
            latest_roles.setdefault(job_id, role)

        return tuple(
            JobHistoryObservation(
                job_id=job_id,
                role=latest_roles[job_id],
                first_observed_at=first_observed_at,
                last_observed_at=last_observed_at,
            )
            for job_id, first_observed_at, last_observed_at in observed_rows
        )

    def save_result(
        self,
        *,
        task_id: UUID,
        jobs: tuple[Job, ...],
        outcome: JobDiscoveryOutcome,
    ) -> tuple[Job, ...]:
        record = self.session.get(JobDiscoveryTaskRecord, task_id)
        if record is None:
            raise ValueError("Discovery task does not exist.")
        persisted = JobRepository(self.session).upsert_many(jobs)
        self.session.execute(
            delete(JobDiscoveryTaskResultRecord).where(
                JobDiscoveryTaskResultRecord.task_id == task_id
            )
        )
        self.session.add_all(
            JobDiscoveryTaskResultRecord(
                task_id=task_id,
                job_id=job.id,
                position=position,
            )
            for position, job in enumerate(persisted)
        )
        record.result_status = outcome.status.value
        record.provider_names_failed = list(outcome.provider_names_failed)
        record.providers_attempted = outcome.providers_attempted
        record.providers_succeeded = outcome.providers_succeeded
        self.session.flush()
        return persisted

    def get_result(
        self,
        task_id: UUID,
    ) -> tuple[JobDiscoveryOutcome, tuple[Job, ...]] | None:
        record = self.session.get(JobDiscoveryTaskRecord, task_id)
        if record is None or record.result_status is None:
            return None
        job_ids = tuple(
            self.session.scalars(
                select(JobDiscoveryTaskResultRecord.job_id)
                .where(JobDiscoveryTaskResultRecord.task_id == task_id)
                .order_by(JobDiscoveryTaskResultRecord.position)
            ).all()
        )
        jobs = JobRepository(self.session).get_many(job_ids) if job_ids else ()
        if jobs is None:
            raise ValueError("A discovery result references an unavailable job.")
        return (
            JobDiscoveryOutcome(
                status=JobDiscoveryOutcomeStatus(record.result_status),
                provider_names_failed=tuple(record.provider_names_failed),
                providers_attempted=record.providers_attempted or 0,
                providers_succeeded=record.providers_succeeded or 0,
            ),
            jobs,
        )

    @staticmethod
    def _request_from_record(record: JobDiscoveryTaskRecord) -> JobSearchRequest:
        return JobSearchRequest(
            role=record.role,
            location=record.location,
            country=record.country,
            page=record.page,
            page_size=record.page_size,
            remote_only=record.remote_only,
            employment_types=tuple(record.employment_types),
            date_posted=record.date_posted,
        )

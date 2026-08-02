"""Application service for owner-scoped assisted application tracking."""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from database.repositories.applications import ApplicationRepository
from database.repositories.jobs import JobRepository
from database.session import Database
from models.application import ApplicationEvent, JobApplication
from models.enums import ApplicationStatus
from models.job import Job


@dataclass(frozen=True)
class ApplicationSnapshot:
    application: JobApplication
    job: Job
    events: tuple[ApplicationEvent, ...] = ()


class ApplicationTrackingService:
    def __init__(self, database: Database) -> None:
        self.database = database

    def create(
        self,
        *,
        user_id: UUID,
        job_id: UUID,
        resume_id: UUID | None = None,
        notes: str | None = None,
        next_action: str | None = None,
        next_action_due_at: datetime | None = None,
    ) -> ApplicationSnapshot | None:
        with self.database.session() as session:
            jobs = JobRepository(session)
            job = jobs.get(job_id)
            if job is None:
                return None
            repository = ApplicationRepository(session)
            application = repository.create(
                user_id=user_id,
                job_id=job_id,
                status=ApplicationStatus.PREPARING,
                resume_id=resume_id,
                notes=notes,
                next_action=next_action,
                next_action_due_at=next_action_due_at,
            )
            return ApplicationSnapshot(
                application=application,
                job=job,
                events=repository.events(
                    user_id=user_id,
                    application_id=application.id,
                ),
            )

    def list(self, *, user_id: UUID) -> tuple[ApplicationSnapshot, ...]:
        with self.database.session() as session:
            applications = ApplicationRepository(session).list(user_id=user_id)
            if not applications:
                return ()
            jobs = JobRepository(session).get_many(
                tuple(application.job_id for application in applications)
            )
            if jobs is None:
                raise RuntimeError("An application references a missing catalog entry.")
            return tuple(
                ApplicationSnapshot(application=application, job=job)
                for application, job in zip(applications, jobs, strict=True)
            )

    def get(
        self,
        *,
        user_id: UUID,
        application_id: UUID,
    ) -> ApplicationSnapshot | None:
        with self.database.session() as session:
            repository = ApplicationRepository(session)
            application = repository.get(
                user_id=user_id,
                application_id=application_id,
            )
            if application is None:
                return None
            job = JobRepository(session).get(application.job_id)
            if job is None:
                raise RuntimeError("An application references a missing catalog entry.")
            return ApplicationSnapshot(
                application=application,
                job=job,
                events=repository.events(
                    user_id=user_id,
                    application_id=application_id,
                ),
            )

    def transition(
        self,
        *,
        user_id: UUID,
        application_id: UUID,
        new_status: ApplicationStatus,
        note: str | None = None,
        next_action: str | None = None,
        next_action_due_at: datetime | None = None,
    ) -> ApplicationSnapshot | None:
        with self.database.session() as session:
            repository = ApplicationRepository(session)
            application = repository.transition(
                user_id=user_id,
                application_id=application_id,
                new_status=new_status,
                note=note,
                next_action=next_action,
                next_action_due_at=next_action_due_at,
            )
            if application is None:
                return None
            job = JobRepository(session).get(application.job_id)
            if job is None:
                raise RuntimeError("An application references a missing catalog entry.")
            return ApplicationSnapshot(
                application=application,
                job=job,
                events=repository.events(
                    user_id=user_id,
                    application_id=application_id,
                ),
            )

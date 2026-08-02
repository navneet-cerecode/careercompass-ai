"""Owner-scoped application reminder service."""

from dataclasses import dataclass
from uuid import UUID

from database.repositories.application_reminders import ApplicationReminderRepository
from database.repositories.applications import ApplicationRepository
from database.repositories.jobs import JobRepository
from database.session import Database
from models.application import ApplicationReminder, JobApplication
from models.enums import ApplicationReminderStatus
from models.job import Job


@dataclass(frozen=True)
class ApplicationReminderSnapshot:
    reminder: ApplicationReminder
    application: JobApplication
    job: Job


class ApplicationReminderService:
    def __init__(self, database: Database) -> None:
        self.database = database

    def list(self, *, user_id: UUID) -> tuple[ApplicationReminderSnapshot, ...]:
        with self.database.session() as session:
            reminders = ApplicationReminderRepository(session).list(user_id=user_id)
            return tuple(
                self._snapshot(
                    session=session,
                    user_id=user_id,
                    reminder=reminder,
                )
                for reminder in reminders
            )

    def set_status(
        self,
        *,
        user_id: UUID,
        reminder_id: UUID,
        status: ApplicationReminderStatus,
    ) -> ApplicationReminderSnapshot | None:
        with self.database.session() as session:
            reminder = ApplicationReminderRepository(session).set_status(
                user_id=user_id,
                reminder_id=reminder_id,
                status=status,
            )
            if reminder is None:
                return None
            return self._snapshot(
                session=session,
                user_id=user_id,
                reminder=reminder,
            )

    @staticmethod
    def _snapshot(
        *,
        session,
        user_id: UUID,
        reminder: ApplicationReminder,
    ) -> ApplicationReminderSnapshot:
        application = ApplicationRepository(session).get(
            user_id=user_id,
            application_id=reminder.application_id,
        )
        if application is None:
            raise RuntimeError("A reminder references a missing application.")
        job = JobRepository(session).get(application.job_id)
        if job is None:
            raise RuntimeError("A reminder references a missing catalog entry.")
        return ApplicationReminderSnapshot(
            reminder=reminder,
            application=application,
            job=job,
        )

"""Owner-scoped saved job and application tracking repositories."""

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from database.models.applications import (
    ApplicationEventRecord,
    ApplicationRecord,
    SavedJobRecord,
)
from database.models.jobs import JobRecord
from database.models.resumes import ResumeRecord
from database.models.users import UserRecord
from models.application import ApplicationEvent, JobApplication, SavedJob
from models.enums import ApplicationStatus

ALLOWED_TRANSITIONS: dict[ApplicationStatus, frozenset[ApplicationStatus]] = {
    ApplicationStatus.DISCOVERED: frozenset(
        {
            ApplicationStatus.SAVED,
            ApplicationStatus.PREPARING,
            ApplicationStatus.WITHDRAWN,
        }
    ),
    ApplicationStatus.SAVED: frozenset({ApplicationStatus.PREPARING, ApplicationStatus.WITHDRAWN}),
    ApplicationStatus.PREPARING: frozenset(
        {ApplicationStatus.READY_TO_APPLY, ApplicationStatus.WITHDRAWN}
    ),
    ApplicationStatus.READY_TO_APPLY: frozenset(
        {ApplicationStatus.APPLIED, ApplicationStatus.WITHDRAWN}
    ),
    ApplicationStatus.APPLIED: frozenset(
        {
            ApplicationStatus.UNDER_REVIEW,
            ApplicationStatus.ASSESSMENT,
            ApplicationStatus.INTERVIEW,
            ApplicationStatus.REJECTED,
            ApplicationStatus.WITHDRAWN,
        }
    ),
    ApplicationStatus.UNDER_REVIEW: frozenset(
        {
            ApplicationStatus.ASSESSMENT,
            ApplicationStatus.INTERVIEW,
            ApplicationStatus.REJECTED,
            ApplicationStatus.WITHDRAWN,
        }
    ),
    ApplicationStatus.ASSESSMENT: frozenset(
        {
            ApplicationStatus.INTERVIEW,
            ApplicationStatus.REJECTED,
            ApplicationStatus.WITHDRAWN,
        }
    ),
    ApplicationStatus.INTERVIEW: frozenset(
        {
            ApplicationStatus.OFFER,
            ApplicationStatus.REJECTED,
            ApplicationStatus.WITHDRAWN,
        }
    ),
    ApplicationStatus.OFFER: frozenset({ApplicationStatus.WITHDRAWN}),
    ApplicationStatus.REJECTED: frozenset(),
    ApplicationStatus.WITHDRAWN: frozenset(),
}


class InvalidApplicationTransition(ValueError):
    """Raised when an application status change violates the workflow."""


class ApplicationAlreadyTracked(ValueError):
    """Raised when a user already tracks the requested job."""


class InvalidResumeSelection(ValueError):
    """Raised when a selected resume is not owned by the application owner."""


class SavedJobRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def save(self, *, user_id: UUID, job_id: UUID, notes: str | None = None) -> SavedJob:
        self._require_user_and_job(user_id=user_id, job_id=job_id)
        record = self.session.get(SavedJobRecord, (user_id, job_id))
        if record is None:
            record = SavedJobRecord(user_id=user_id, job_id=job_id, notes=notes)
            self.session.add(record)
        else:
            record.notes = notes
            record.updated_at = datetime.now(timezone.utc)
        self.session.flush()
        self.session.refresh(record)
        return self._to_domain(record)

    def get(self, *, user_id: UUID, job_id: UUID) -> SavedJob | None:
        record = self.session.get(SavedJobRecord, (user_id, job_id))
        return self._to_domain(record) if record is not None else None

    def list(self, *, user_id: UUID) -> tuple[SavedJob, ...]:
        records = self.session.scalars(
            select(SavedJobRecord)
            .where(SavedJobRecord.user_id == user_id)
            .order_by(SavedJobRecord.created_at.desc())
        ).all()
        return tuple(self._to_domain(record) for record in records)

    def remove(self, *, user_id: UUID, job_id: UUID) -> bool:
        result = self.session.execute(
            delete(SavedJobRecord).where(
                SavedJobRecord.user_id == user_id,
                SavedJobRecord.job_id == job_id,
            )
        )
        return bool(result.rowcount)

    def _require_user_and_job(self, *, user_id: UUID, job_id: UUID) -> None:
        if self.session.get(UserRecord, user_id) is None:
            raise ValueError("User does not exist.")
        if self.session.get(JobRecord, job_id) is None:
            raise ValueError("Job does not exist.")

    @staticmethod
    def _to_domain(record: SavedJobRecord) -> SavedJob:
        return SavedJob.model_validate(record, from_attributes=True)


class ApplicationRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(
        self,
        *,
        user_id: UUID,
        job_id: UUID,
        status: ApplicationStatus = ApplicationStatus.DISCOVERED,
        resume_id: UUID | None = None,
        notes: str | None = None,
        next_action: str | None = None,
        next_action_due_at: datetime | None = None,
    ) -> JobApplication:
        self._require_owned_dependencies(
            user_id=user_id,
            job_id=job_id,
            resume_id=resume_id,
        )
        existing = self.session.scalar(
            select(ApplicationRecord).where(
                ApplicationRecord.user_id == user_id,
                ApplicationRecord.job_id == job_id,
            )
        )
        if existing is not None:
            raise ApplicationAlreadyTracked("An application for this job already exists.")

        record = ApplicationRecord(
            user_id=user_id,
            job_id=job_id,
            resume_id=resume_id,
            status=status.value,
            applied_at=datetime.now(timezone.utc) if status == ApplicationStatus.APPLIED else None,
            notes=notes,
            next_action=next_action,
            next_action_due_at=next_action_due_at,
        )
        self.session.add(record)
        self.session.flush()
        self._record_event(record, previous_status=None, new_status=status, note="Created")
        self.session.flush()
        self.session.refresh(record)
        return self._to_domain(record)

    def get(self, *, user_id: UUID, application_id: UUID) -> JobApplication | None:
        record = self._get_record(user_id=user_id, application_id=application_id)
        return self._to_domain(record) if record is not None else None

    def list(self, *, user_id: UUID) -> tuple[JobApplication, ...]:
        records = self.session.scalars(
            select(ApplicationRecord)
            .where(ApplicationRecord.user_id == user_id)
            .order_by(ApplicationRecord.updated_at.desc())
        ).all()
        return tuple(self._to_domain(record) for record in records)

    def transition(
        self,
        *,
        user_id: UUID,
        application_id: UUID,
        new_status: ApplicationStatus,
        note: str | None = None,
        next_action: str | None = None,
        next_action_due_at: datetime | None = None,
    ) -> JobApplication | None:
        record = self._get_record(user_id=user_id, application_id=application_id)
        if record is None:
            return None

        current_status = ApplicationStatus(record.status)
        if new_status not in ALLOWED_TRANSITIONS[current_status]:
            raise InvalidApplicationTransition(
                f"Cannot transition application from {current_status.value!r} "
                f"to {new_status.value!r}."
            )

        record.status = new_status.value
        record.next_action = next_action
        record.next_action_due_at = next_action_due_at
        record.updated_at = datetime.now(timezone.utc)
        if new_status == ApplicationStatus.APPLIED and record.applied_at is None:
            record.applied_at = datetime.now(timezone.utc)
        self._record_event(
            record,
            previous_status=current_status,
            new_status=new_status,
            note=note,
        )
        self.session.flush()
        self.session.refresh(record)
        return self._to_domain(record)

    def update_plan(
        self,
        *,
        user_id: UUID,
        application_id: UUID,
        notes: str | None = None,
        next_action: str | None = None,
        next_action_due_at: datetime | None = None,
    ) -> JobApplication | None:
        record = self._get_record(user_id=user_id, application_id=application_id)
        if record is None:
            return None
        record.notes = notes
        record.next_action = next_action
        record.next_action_due_at = next_action_due_at
        record.updated_at = datetime.now(timezone.utc)
        self.session.flush()
        self.session.refresh(record)
        return self._to_domain(record)

    def events(
        self,
        *,
        user_id: UUID,
        application_id: UUID,
    ) -> tuple[ApplicationEvent, ...]:
        if self._get_record(user_id=user_id, application_id=application_id) is None:
            return ()
        records = self.session.scalars(
            select(ApplicationEventRecord)
            .where(ApplicationEventRecord.application_id == application_id)
            .order_by(
                ApplicationEventRecord.occurred_at,
                ApplicationEventRecord.id,
            )
        ).all()
        return tuple(
            ApplicationEvent.model_validate(record, from_attributes=True) for record in records
        )

    def _get_record(
        self,
        *,
        user_id: UUID,
        application_id: UUID,
    ) -> ApplicationRecord | None:
        return self.session.scalar(
            select(ApplicationRecord).where(
                ApplicationRecord.id == application_id,
                ApplicationRecord.user_id == user_id,
            )
        )

    def _require_owned_dependencies(
        self,
        *,
        user_id: UUID,
        job_id: UUID,
        resume_id: UUID | None,
    ) -> None:
        if self.session.get(UserRecord, user_id) is None:
            raise ValueError("User does not exist.")
        if self.session.get(JobRecord, job_id) is None:
            raise ValueError("Job does not exist.")
        if resume_id is not None:
            resume = self.session.scalar(
                select(ResumeRecord).where(
                    ResumeRecord.id == resume_id,
                    ResumeRecord.user_id == user_id,
                )
            )
            if resume is None:
                raise InvalidResumeSelection("Resume does not belong to the user.")

    def _record_event(
        self,
        record: ApplicationRecord,
        *,
        previous_status: ApplicationStatus | None,
        new_status: ApplicationStatus,
        note: str | None,
    ) -> None:
        self.session.add(
            ApplicationEventRecord(
                application_id=record.id,
                previous_status=previous_status.value if previous_status else None,
                new_status=new_status.value,
                note=note,
                occurred_at=datetime.now(timezone.utc),
            )
        )

    @staticmethod
    def _to_domain(record: ApplicationRecord) -> JobApplication:
        return JobApplication.model_validate(record, from_attributes=True)

"""Owner-scoped application packet persistence."""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from database.models.applications import ApplicationPacketRecord, ApplicationRecord
from models.application_packet import ApplicationPacket


class ApplicationPacketLocked(ValueError):
    """Raised when a ready packet is changed."""


class ApplicationPacketRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get(
        self,
        *,
        user_id: UUID,
        application_id: UUID,
    ) -> ApplicationPacket | None:
        record = self._get_record(user_id=user_id, application_id=application_id)
        return self._to_domain(record) if record is not None else None

    def get_or_create(
        self,
        *,
        user_id: UUID,
        application_id: UUID,
        source_resume_id: UUID | None,
    ) -> ApplicationPacket | None:
        application = self.session.scalar(
            select(ApplicationRecord).where(
                ApplicationRecord.id == application_id,
                ApplicationRecord.user_id == user_id,
            )
        )
        if application is None:
            return None
        record = self._get_record(user_id=user_id, application_id=application_id)
        if record is None:
            record = ApplicationPacketRecord(
                user_id=user_id,
                application_id=application_id,
                source_resume_id=source_resume_id,
            )
            self.session.add(record)
        elif record.source_resume_id is None and record.ready_at is None:
            record.source_resume_id = source_resume_id
        self.session.flush()
        self.session.refresh(record)
        return self._to_domain(record)

    def update(
        self,
        *,
        user_id: UUID,
        application_id: UUID,
        source_resume_id: UUID | None,
        tailored_resume_id: UUID | None,
        cover_letter_id: UUID | None,
        job_details_reviewed: bool,
        resume_reviewed: bool,
        cover_letter_reviewed: bool,
        employer_questions_reviewed: bool,
    ) -> ApplicationPacket | None:
        record = self._get_record(user_id=user_id, application_id=application_id)
        if record is None:
            return None
        if record.ready_at is not None:
            raise ApplicationPacketLocked("A ready application packet is immutable.")
        record.source_resume_id = source_resume_id
        record.tailored_resume_id = tailored_resume_id
        record.cover_letter_id = cover_letter_id
        record.job_details_reviewed = job_details_reviewed
        record.resume_reviewed = resume_reviewed
        record.cover_letter_reviewed = cover_letter_reviewed
        record.employer_questions_reviewed = employer_questions_reviewed
        record.updated_at = datetime.now(UTC)
        self.session.flush()
        self.session.refresh(record)
        return self._to_domain(record)

    def mark_ready(
        self,
        *,
        user_id: UUID,
        application_id: UUID,
    ) -> ApplicationPacket | None:
        record = self._get_record(user_id=user_id, application_id=application_id)
        if record is None:
            return None
        if record.ready_at is None:
            record.ready_at = datetime.now(UTC)
            record.updated_at = record.ready_at
            self.session.flush()
            self.session.refresh(record)
        return self._to_domain(record)

    def ready_application_ids(
        self,
        *,
        user_id: UUID,
        application_ids: tuple[UUID, ...],
    ) -> frozenset[UUID]:
        if not application_ids:
            return frozenset()
        ids = self.session.scalars(
            select(ApplicationPacketRecord.application_id).where(
                ApplicationPacketRecord.user_id == user_id,
                ApplicationPacketRecord.application_id.in_(application_ids),
                ApplicationPacketRecord.ready_at.is_not(None),
            )
        ).all()
        return frozenset(ids)

    def _get_record(
        self,
        *,
        user_id: UUID,
        application_id: UUID,
    ) -> ApplicationPacketRecord | None:
        return self.session.scalar(
            select(ApplicationPacketRecord).where(
                ApplicationPacketRecord.user_id == user_id,
                ApplicationPacketRecord.application_id == application_id,
            )
        )

    @staticmethod
    def _to_domain(record: ApplicationPacketRecord) -> ApplicationPacket:
        return ApplicationPacket.model_validate(record, from_attributes=True)

"""Owner-scoped interview kit persistence."""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from database.models.applications import ApplicationRecord
from database.models.interviews import InterviewKitRecord
from models.interview_kit import InterviewKit, InterviewQuestion


class InterviewKitRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, *, user_id: UUID, application_id: UUID) -> InterviewKit | None:
        record = self._get_record(user_id=user_id, application_id=application_id)
        return self._to_domain(record) if record is not None else None

    def create(
        self,
        *,
        user_id: UUID,
        application_id: UUID,
        resume_id: UUID,
        questions: tuple[InterviewQuestion, ...],
    ) -> InterviewKit | None:
        application = self.session.scalar(
            select(ApplicationRecord).where(
                ApplicationRecord.id == application_id,
                ApplicationRecord.user_id == user_id,
            )
        )
        if application is None:
            return None
        existing = self._get_record(user_id=user_id, application_id=application_id)
        if existing is not None:
            return self._to_domain(existing)
        record = InterviewKitRecord(
            user_id=user_id,
            application_id=application_id,
            resume_id=resume_id,
            questions=[question.model_dump(mode="json") for question in questions],
            responses={},
        )
        self.session.add(record)
        self.session.flush()
        self.session.refresh(record)
        return self._to_domain(record)

    def update(
        self,
        *,
        user_id: UUID,
        application_id: UUID,
        responses: dict[str, str],
        confirm_reviewed: bool,
    ) -> InterviewKit | None:
        record = self._get_record(user_id=user_id, application_id=application_id)
        if record is None:
            return None
        question_ids = {str(question["id"]) for question in record.questions}
        if not set(responses) <= question_ids:
            raise ValueError("Responses contain an unknown interview question.")
        record.responses = responses
        record.reviewed_at = datetime.now(UTC) if confirm_reviewed else None
        record.updated_at = datetime.now(UTC)
        self.session.flush()
        self.session.refresh(record)
        return self._to_domain(record)

    def _get_record(
        self,
        *,
        user_id: UUID,
        application_id: UUID,
    ) -> InterviewKitRecord | None:
        return self.session.scalar(
            select(InterviewKitRecord).where(
                InterviewKitRecord.user_id == user_id,
                InterviewKitRecord.application_id == application_id,
            )
        )

    @staticmethod
    def _to_domain(record: InterviewKitRecord) -> InterviewKit:
        return InterviewKit(
            id=record.id,
            user_id=record.user_id,
            application_id=record.application_id,
            resume_id=record.resume_id,
            questions=tuple(
                InterviewQuestion.model_validate(question)
                for question in record.questions
            ),
            responses=dict(record.responses),
            reviewed_at=record.reviewed_at,
            created_at=record.created_at,
            updated_at=record.updated_at,
        )

"""Owner-scoped tailored resume version persistence."""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from database.models.tailoring import TailoredResumeRecord
from models.tailored_resume import (
    TailoredResumeContent,
    TailoredResumeSelections,
    TailoredResumeVersion,
)


class TailoredResumeRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, *, user_id: UUID, tailored_resume_id: UUID) -> TailoredResumeVersion | None:
        record = self.session.scalar(
            select(TailoredResumeRecord).where(
                TailoredResumeRecord.id == tailored_resume_id,
                TailoredResumeRecord.user_id == user_id,
            )
        )
        return self._to_domain(record) if record is not None else None

    def get_latest_for_plan(
        self,
        *,
        user_id: UUID,
        plan_id: UUID,
    ) -> TailoredResumeVersion | None:
        record = self.session.scalar(
            select(TailoredResumeRecord)
            .where(
                TailoredResumeRecord.user_id == user_id,
                TailoredResumeRecord.plan_id == plan_id,
            )
            .order_by(TailoredResumeRecord.version.desc())
            .limit(1)
        )
        return self._to_domain(record) if record is not None else None

    def list_versions(
        self,
        *,
        user_id: UUID,
        plan_id: UUID,
    ) -> tuple[TailoredResumeVersion, ...]:
        records = self.session.scalars(
            select(TailoredResumeRecord)
            .where(
                TailoredResumeRecord.user_id == user_id,
                TailoredResumeRecord.plan_id == plan_id,
            )
            .order_by(TailoredResumeRecord.version.desc())
        ).all()
        return tuple(self._to_domain(record) for record in records)

    def create_version(
        self,
        *,
        user_id: UUID,
        plan_id: UUID,
        source_resume_id: UUID,
        job_id: UUID,
        original: TailoredResumeContent,
        suggested: TailoredResumeContent,
        accepted: TailoredResumeContent,
        selections: TailoredResumeSelections,
    ) -> TailoredResumeVersion:
        latest_version = self.session.scalar(
            select(func.max(TailoredResumeRecord.version)).where(
                TailoredResumeRecord.user_id == user_id,
                TailoredResumeRecord.plan_id == plan_id,
            )
        )
        record = TailoredResumeRecord(
            user_id=user_id,
            plan_id=plan_id,
            source_resume_id=source_resume_id,
            job_id=job_id,
            version=(latest_version or 0) + 1,
            original_content=original.model_dump(mode="json"),
            suggested_content=suggested.model_dump(mode="json"),
            accepted_content=accepted.model_dump(mode="json"),
            selections=selections.model_dump(mode="json"),
            verification_status="pending_review",
            user_review_required=True,
        )
        self.session.add(record)
        self.session.flush()
        self.session.refresh(record)
        return self._to_domain(record)

    def approve(
        self,
        *,
        user_id: UUID,
        tailored_resume_id: UUID,
    ) -> TailoredResumeVersion | None:
        record = self.session.scalar(
            select(TailoredResumeRecord).where(
                TailoredResumeRecord.id == tailored_resume_id,
                TailoredResumeRecord.user_id == user_id,
            )
        )
        if record is None:
            return None
        if record.verification_status == "user_verified":
            return self._to_domain(record)
        record.verification_status = "user_verified"
        record.user_review_required = False
        record.approved_at = datetime.now(UTC)
        self.session.flush()
        self.session.refresh(record)
        return self._to_domain(record)

    @staticmethod
    def _to_domain(record: TailoredResumeRecord) -> TailoredResumeVersion:
        return TailoredResumeVersion(
            id=record.id,
            user_id=record.user_id,
            plan_id=record.plan_id,
            source_resume_id=record.source_resume_id,
            job_id=record.job_id,
            version=record.version,
            original=TailoredResumeContent.model_validate(record.original_content),
            suggested=TailoredResumeContent.model_validate(record.suggested_content),
            accepted=TailoredResumeContent.model_validate(record.accepted_content),
            selections=TailoredResumeSelections.model_validate(record.selections),
            verification_status=record.verification_status,
            user_review_required=record.user_review_required,
            approved_at=record.approved_at,
            created_at=record.created_at,
            updated_at=record.updated_at,
        )

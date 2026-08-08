"""Owner-scoped cover letter version persistence."""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from database.models.tailoring import CoverLetterRecord
from models.cover_letter import CoverLetterContent, CoverLetterEvidence, CoverLetterVersion


class CoverLetterRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, *, user_id: UUID, cover_letter_id: UUID) -> CoverLetterVersion | None:
        record = self.session.scalar(
            select(CoverLetterRecord).where(
                CoverLetterRecord.id == cover_letter_id,
                CoverLetterRecord.user_id == user_id,
            )
        )
        return self._to_domain(record) if record is not None else None

    def get_latest_for_plan(
        self,
        *,
        user_id: UUID,
        plan_id: UUID,
    ) -> CoverLetterVersion | None:
        record = self.session.scalar(
            select(CoverLetterRecord)
            .where(
                CoverLetterRecord.user_id == user_id,
                CoverLetterRecord.plan_id == plan_id,
            )
            .order_by(CoverLetterRecord.version.desc())
            .limit(1)
        )
        return self._to_domain(record) if record is not None else None

    def list_versions(
        self,
        *,
        user_id: UUID,
        plan_id: UUID,
    ) -> tuple[CoverLetterVersion, ...]:
        records = self.session.scalars(
            select(CoverLetterRecord)
            .where(
                CoverLetterRecord.user_id == user_id,
                CoverLetterRecord.plan_id == plan_id,
            )
            .order_by(CoverLetterRecord.version.desc())
        ).all()
        return tuple(self._to_domain(record) for record in records)

    def create_version(
        self,
        *,
        user_id: UUID,
        plan_id: UUID,
        source_resume_id: UUID,
        job_id: UUID,
        suggested: CoverLetterContent,
        accepted: CoverLetterContent,
        evidence: tuple[CoverLetterEvidence, ...],
    ) -> CoverLetterVersion:
        latest_version = self.session.scalar(
            select(func.max(CoverLetterRecord.version)).where(
                CoverLetterRecord.user_id == user_id,
                CoverLetterRecord.plan_id == plan_id,
            )
        )
        record = CoverLetterRecord(
            user_id=user_id,
            plan_id=plan_id,
            source_resume_id=source_resume_id,
            job_id=job_id,
            version=(latest_version or 0) + 1,
            suggested_content=suggested.model_dump(mode="json"),
            accepted_content=accepted.model_dump(mode="json"),
            evidence=[item.model_dump(mode="json") for item in evidence],
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
        cover_letter_id: UUID,
    ) -> CoverLetterVersion | None:
        record = self.session.scalar(
            select(CoverLetterRecord).where(
                CoverLetterRecord.id == cover_letter_id,
                CoverLetterRecord.user_id == user_id,
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
    def _to_domain(record: CoverLetterRecord) -> CoverLetterVersion:
        return CoverLetterVersion(
            id=record.id,
            user_id=record.user_id,
            plan_id=record.plan_id,
            source_resume_id=record.source_resume_id,
            job_id=record.job_id,
            version=record.version,
            suggested=CoverLetterContent.model_validate(record.suggested_content),
            accepted=CoverLetterContent.model_validate(record.accepted_content),
            evidence=tuple(CoverLetterEvidence.model_validate(item) for item in record.evidence),
            verification_status=record.verification_status,
            user_review_required=record.user_review_required,
            approved_at=record.approved_at,
            created_at=record.created_at,
            updated_at=record.updated_at,
        )

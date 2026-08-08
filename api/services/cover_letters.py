"""Owner-scoped cover letter version and export orchestration."""

import re
from dataclasses import dataclass
from uuid import UUID

from database.repositories.cover_letters import CoverLetterRepository
from database.repositories.jobs import JobRepository
from database.repositories.resumes import ResumeRepository
from database.repositories.subscriptions import SubscriptionRepository
from database.repositories.tailoring import TailoringPlanRepository
from database.session import Database
from models.cover_letter import CoverLetterContent, CoverLetterVersion
from services.tailoring import (
    CoverLetterDocumentExporter,
    ExportFormat,
    FactualCoverLetterComposer,
)

SAFE_FILENAME = re.compile(r"[^a-z0-9]+")


class CoverLetterUnavailable(Exception):
    """Raised when the account lacks tailored-document access."""


class CoverLetterNotFound(Exception):
    """Raised when an owner-scoped source or version is unavailable."""


class StaleCoverLetterVersion(Exception):
    """Raised when a change does not target the latest version."""


class CoverLetterReviewRequired(Exception):
    """Raised when an unverified version is exported."""


class CoverLetterSourceLocked(Exception):
    """Raised when a revision attempts to alter persisted identity or job facts."""


@dataclass(frozen=True)
class ExportedCoverLetter:
    filename: str
    content_type: str
    content: bytes


class CoverLetterService:
    def __init__(
        self,
        database: Database,
        composer: FactualCoverLetterComposer | None = None,
        exporter: CoverLetterDocumentExporter | None = None,
    ) -> None:
        self.database = database
        self.composer = composer or FactualCoverLetterComposer()
        self.exporter = exporter or CoverLetterDocumentExporter()

    def create(self, *, user_id: UUID, plan_id: UUID) -> CoverLetterVersion:
        with self.database.session() as session:
            self._require_entitlement(session, user_id)
            repository = CoverLetterRepository(session)
            existing = repository.get_latest_for_plan(user_id=user_id, plan_id=plan_id)
            if existing is not None:
                return existing

            persisted_plan = TailoringPlanRepository(session).get(
                user_id=user_id,
                plan_id=plan_id,
            )
            if persisted_plan is None:
                raise CoverLetterNotFound
            plan = persisted_plan.plan
            persisted_resume = ResumeRepository(session).get(
                user_id=user_id,
                resume_id=plan.source_resume_id,
            )
            job = JobRepository(session).get(plan.job_id)
            if persisted_resume is None or job is None:
                raise CoverLetterNotFound

            suggested, evidence = self.composer.compose(
                resume=persisted_resume.resume,
                job=job,
                plan=plan,
            )
            return repository.create_version(
                user_id=user_id,
                plan_id=plan_id,
                source_resume_id=plan.source_resume_id,
                job_id=plan.job_id,
                suggested=suggested,
                accepted=suggested,
                evidence=evidence,
            )

    def get(self, *, user_id: UUID, cover_letter_id: UUID) -> CoverLetterVersion | None:
        with self.database.session() as session:
            return CoverLetterRepository(session).get(
                user_id=user_id,
                cover_letter_id=cover_letter_id,
            )

    def list_versions(
        self,
        *,
        user_id: UUID,
        cover_letter_id: UUID,
    ) -> tuple[CoverLetterVersion, ...]:
        with self.database.session() as session:
            repository = CoverLetterRepository(session)
            current = repository.get(user_id=user_id, cover_letter_id=cover_letter_id)
            if current is None:
                raise CoverLetterNotFound
            return repository.list_versions(user_id=user_id, plan_id=current.plan_id)

    def revise(
        self,
        *,
        user_id: UUID,
        cover_letter_id: UUID,
        content: CoverLetterContent,
    ) -> CoverLetterVersion:
        with self.database.session() as session:
            self._require_entitlement(session, user_id)
            repository = CoverLetterRepository(session)
            current = repository.get(user_id=user_id, cover_letter_id=cover_letter_id)
            if current is None:
                raise CoverLetterNotFound
            latest = repository.get_latest_for_plan(user_id=user_id, plan_id=current.plan_id)
            if latest is None or latest.id != current.id:
                raise StaleCoverLetterVersion
            if current.accepted == content:
                return current
            if (
                content.candidate_name != current.accepted.candidate_name
                or content.candidate_email != current.accepted.candidate_email
                or content.company_name != current.accepted.company_name
                or content.job_title != current.accepted.job_title
            ):
                raise CoverLetterSourceLocked
            return repository.create_version(
                user_id=user_id,
                plan_id=current.plan_id,
                source_resume_id=current.source_resume_id,
                job_id=current.job_id,
                suggested=current.suggested,
                accepted=content,
                evidence=current.evidence,
            )

    def approve(self, *, user_id: UUID, cover_letter_id: UUID) -> CoverLetterVersion:
        with self.database.session() as session:
            self._require_entitlement(session, user_id)
            repository = CoverLetterRepository(session)
            current = repository.get(user_id=user_id, cover_letter_id=cover_letter_id)
            if current is None:
                raise CoverLetterNotFound
            latest = repository.get_latest_for_plan(user_id=user_id, plan_id=current.plan_id)
            if latest is None or latest.id != current.id:
                raise StaleCoverLetterVersion
            approved = repository.approve(user_id=user_id, cover_letter_id=cover_letter_id)
            if approved is None:
                raise CoverLetterNotFound
            return approved

    def export(
        self,
        *,
        user_id: UUID,
        cover_letter_id: UUID,
        export_format: ExportFormat,
    ) -> ExportedCoverLetter:
        with self.database.session() as session:
            self._require_entitlement(session, user_id)
            version = CoverLetterRepository(session).get(
                user_id=user_id,
                cover_letter_id=cover_letter_id,
            )
            if version is None:
                raise CoverLetterNotFound
            if version.verification_status != "user_verified":
                raise CoverLetterReviewRequired

        slug = SAFE_FILENAME.sub(
            "-",
            f"{version.accepted.company_name}-{version.accepted.job_title}".casefold(),
        ).strip("-")
        return ExportedCoverLetter(
            filename=f"solara-hire-{slug or 'cover-letter'}.{export_format}",
            content_type=(
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                if export_format == "docx"
                else "application/pdf"
            ),
            content=self.exporter.render(version.accepted, export_format),
        )

    @staticmethod
    def _require_entitlement(session, user_id: UUID) -> None:
        subscriptions = SubscriptionRepository(session)
        subscription = subscriptions.get_or_create_free(user_id=user_id)
        if not subscriptions.entitlements(subscription).tailored_documents:
            raise CoverLetterUnavailable

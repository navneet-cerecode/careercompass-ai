"""Owner-scoped tailored resume version and export orchestration."""

import re
from dataclasses import dataclass
from uuid import UUID

from database.repositories.jobs import JobRepository
from database.repositories.resumes import ResumeRepository
from database.repositories.subscriptions import SubscriptionRepository
from database.repositories.tailored_resumes import TailoredResumeRepository
from database.repositories.tailoring import TailoringPlanRepository
from database.session import Database
from models.resume import Resume
from models.tailored_resume import (
    TailoredResumeContent,
    TailoredResumeSelections,
    TailoredResumeVersion,
)
from models.tailoring import FactualTailoringPlan
from services.tailoring import ExportFormat, ResumeDocumentExporter

SAFE_FILENAME = re.compile(r"[^a-z0-9]+")


class TailoredResumeUnavailable(Exception):
    """Raised when the account lacks tailored-document access."""


class TailoredResumeNotFound(Exception):
    """Raised when an owner-scoped plan, resume, job, or version is unavailable."""


class StaleTailoredResumeVersion(Exception):
    """Raised when a revision or approval does not target the latest version."""


class TailoredResumeReviewRequired(Exception):
    """Raised when an unverified version is exported."""


@dataclass(frozen=True)
class ExportedResume:
    filename: str
    content_type: str
    content: bytes


class TailoredResumeService:
    def __init__(
        self,
        database: Database,
        exporter: ResumeDocumentExporter | None = None,
    ) -> None:
        self.database = database
        self.exporter = exporter or ResumeDocumentExporter()

    def create(self, *, user_id: UUID, plan_id: UUID) -> TailoredResumeVersion:
        with self.database.session() as session:
            self._require_entitlement(session, user_id)
            versions = TailoredResumeRepository(session)
            existing = versions.get_latest_for_plan(user_id=user_id, plan_id=plan_id)
            if existing is not None:
                return existing

            persisted_plan = TailoringPlanRepository(session).get(
                user_id=user_id,
                plan_id=plan_id,
            )
            if persisted_plan is None:
                raise TailoredResumeNotFound
            plan = persisted_plan.plan
            persisted_resume = ResumeRepository(session).get(
                user_id=user_id,
                resume_id=plan.source_resume_id,
            )
            if persisted_resume is None:
                raise TailoredResumeNotFound
            if JobRepository(session).get(plan.job_id) is None:
                raise TailoredResumeNotFound

            original = self._content_from_resume(persisted_resume.resume)
            suggested = self._suggested_content(original, plan)
            selections = TailoredResumeSelections()
            return versions.create_version(
                user_id=user_id,
                plan_id=plan_id,
                source_resume_id=plan.source_resume_id,
                job_id=plan.job_id,
                original=original,
                suggested=suggested,
                accepted=self._accepted_content(original, suggested, selections),
                selections=selections,
            )

    def get(
        self,
        *,
        user_id: UUID,
        tailored_resume_id: UUID,
    ) -> TailoredResumeVersion | None:
        with self.database.session() as session:
            return TailoredResumeRepository(session).get(
                user_id=user_id,
                tailored_resume_id=tailored_resume_id,
            )

    def list_versions(
        self,
        *,
        user_id: UUID,
        tailored_resume_id: UUID,
    ) -> tuple[TailoredResumeVersion, ...]:
        with self.database.session() as session:
            repository = TailoredResumeRepository(session)
            current = repository.get(
                user_id=user_id,
                tailored_resume_id=tailored_resume_id,
            )
            if current is None:
                raise TailoredResumeNotFound
            return repository.list_versions(user_id=user_id, plan_id=current.plan_id)

    def revise(
        self,
        *,
        user_id: UUID,
        tailored_resume_id: UUID,
        selections: TailoredResumeSelections,
    ) -> TailoredResumeVersion:
        with self.database.session() as session:
            self._require_entitlement(session, user_id)
            repository = TailoredResumeRepository(session)
            current = repository.get(
                user_id=user_id,
                tailored_resume_id=tailored_resume_id,
            )
            if current is None:
                raise TailoredResumeNotFound
            latest = repository.get_latest_for_plan(
                user_id=user_id,
                plan_id=current.plan_id,
            )
            if latest is None or latest.id != current.id:
                raise StaleTailoredResumeVersion
            if current.selections == selections:
                return current
            return repository.create_version(
                user_id=user_id,
                plan_id=current.plan_id,
                source_resume_id=current.source_resume_id,
                job_id=current.job_id,
                original=current.original,
                suggested=current.suggested,
                accepted=self._accepted_content(
                    current.original,
                    current.suggested,
                    selections,
                ),
                selections=selections,
            )

    def approve(
        self,
        *,
        user_id: UUID,
        tailored_resume_id: UUID,
    ) -> TailoredResumeVersion:
        with self.database.session() as session:
            self._require_entitlement(session, user_id)
            repository = TailoredResumeRepository(session)
            current = repository.get(
                user_id=user_id,
                tailored_resume_id=tailored_resume_id,
            )
            if current is None:
                raise TailoredResumeNotFound
            latest = repository.get_latest_for_plan(
                user_id=user_id,
                plan_id=current.plan_id,
            )
            if latest is None or latest.id != current.id:
                raise StaleTailoredResumeVersion
            approved = repository.approve(
                user_id=user_id,
                tailored_resume_id=tailored_resume_id,
            )
            if approved is None:
                raise TailoredResumeNotFound
            return approved

    def export(
        self,
        *,
        user_id: UUID,
        tailored_resume_id: UUID,
        export_format: ExportFormat,
    ) -> ExportedResume:
        with self.database.session() as session:
            self._require_entitlement(session, user_id)
            version = TailoredResumeRepository(session).get(
                user_id=user_id,
                tailored_resume_id=tailored_resume_id,
            )
            if version is None:
                raise TailoredResumeNotFound
            if version.verification_status != "user_verified":
                raise TailoredResumeReviewRequired
            job = JobRepository(session).get(version.job_id)
            if job is None:
                raise TailoredResumeNotFound

        slug = SAFE_FILENAME.sub("-", f"{job.company}-{job.title}".casefold()).strip("-")
        extension = export_format
        return ExportedResume(
            filename=f"solara-hire-{slug or 'tailored-resume'}.{extension}",
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
            raise TailoredResumeUnavailable

    @staticmethod
    def _content_from_resume(resume: Resume) -> TailoredResumeContent:
        return TailoredResumeContent(
            name=resume.name,
            email=str(resume.email) if resume.email else None,
            phone=resume.phone,
            linkedin=resume.linkedin,
            github=resume.github,
            education=tuple(resume.education),
            experience=tuple(resume.experience),
            projects=tuple(resume.projects),
            skills=tuple(resume.skills),
            certifications=tuple(resume.certifications),
            achievements=tuple(resume.achievements),
        )

    @staticmethod
    def _suggested_content(
        original: TailoredResumeContent,
        plan: FactualTailoringPlan,
    ) -> TailoredResumeContent:
        return original.model_copy(
            update={
                "skills": plan.skills,
                "experience": plan.experience,
                "projects": plan.projects,
            }
        )

    @staticmethod
    def _accepted_content(
        original: TailoredResumeContent,
        suggested: TailoredResumeContent,
        selections: TailoredResumeSelections,
    ) -> TailoredResumeContent:
        return original.model_copy(
            update={
                "skills": (
                    suggested.skills if selections.skills == "suggested" else original.skills
                ),
                "experience": (
                    suggested.experience
                    if selections.experience == "suggested"
                    else original.experience
                ),
                "projects": (
                    suggested.projects if selections.projects == "suggested" else original.projects
                ),
            }
        )

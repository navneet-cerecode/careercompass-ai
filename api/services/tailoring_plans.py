"""Owner-scoped factual tailoring-plan orchestration."""

from uuid import UUID

from database.repositories.jobs import JobRepository
from database.repositories.resumes import ResumeRepository
from database.repositories.subscriptions import SubscriptionRepository
from database.repositories.tailoring import PersistedTailoringPlan, TailoringPlanRepository
from database.session import Database
from services.tailoring import FactualTailoringService


class TailoredDocumentsUnavailable(Exception):
    """Raised when the account cannot create tailored documents."""


class TailoringResumeNotFound(Exception):
    """Raised when the requested owner-scoped resume is unavailable."""


class TailoringJobNotFound(Exception):
    """Raised when the requested catalog job is unavailable."""


class TailoringPlanService:
    def __init__(
        self,
        database: Database,
        planner: FactualTailoringService | None = None,
    ) -> None:
        self.database = database
        self.planner = planner or FactualTailoringService()

    def create(
        self,
        *,
        user_id: UUID,
        job_id: UUID,
        resume_id: UUID | None = None,
    ) -> PersistedTailoringPlan:
        with self.database.session() as session:
            subscriptions = SubscriptionRepository(session)
            subscription = subscriptions.get_or_create_free(user_id=user_id)
            if not subscriptions.entitlements(subscription).tailored_documents:
                raise TailoredDocumentsUnavailable

            resumes = ResumeRepository(session)
            persisted_resume = (
                resumes.get(user_id=user_id, resume_id=resume_id)
                if resume_id is not None
                else resumes.get_active(user_id=user_id)
            )
            if persisted_resume is None:
                raise TailoringResumeNotFound

            job = JobRepository(session).get(job_id)
            if job is None:
                raise TailoringJobNotFound

            plan = self.planner.create_plan(persisted_resume.resume, job)
            return TailoringPlanRepository(session).save(user_id=user_id, plan=plan)

    def get(self, *, user_id: UUID, plan_id: UUID) -> PersistedTailoringPlan | None:
        with self.database.session() as session:
            return TailoringPlanRepository(session).get(user_id=user_id, plan_id=plan_id)

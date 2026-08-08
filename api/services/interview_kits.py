"""Evidence-grounded interview preparation orchestration."""

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy.exc import IntegrityError

from database.repositories.applications import ApplicationRepository
from database.repositories.interview_kits import InterviewKitRepository
from database.repositories.jobs import JobRepository
from database.repositories.resumes import ResumeRepository
from database.session import Database
from models.application import JobApplication
from models.enums import ApplicationStatus
from models.interview_kit import InterviewKit, InterviewQuestion
from models.job import Job
from models.resume import Resume

ALLOWED_INTERVIEW_PREPARATION_STATUSES = {
    ApplicationStatus.APPLIED,
    ApplicationStatus.UNDER_REVIEW,
    ApplicationStatus.ASSESSMENT,
    ApplicationStatus.INTERVIEW,
}


class InterviewKitNotFound(Exception):
    """Raised when an owner-scoped application or kit is unavailable."""


class InterviewKitResumeRequired(Exception):
    """Raised when no verified resume can ground the preparation."""


class InterviewKitInvalidStatus(Exception):
    """Raised when preparation is requested before an application is submitted."""


class InterviewKitInvalidResponse(Exception):
    """Raised when draft notes do not match the generated question set."""


@dataclass(frozen=True)
class InterviewKitSnapshot:
    kit: InterviewKit
    application: JobApplication
    job: Job


class InterviewKitService:
    def __init__(self, database: Database) -> None:
        self.database = database

    def create(self, *, user_id: UUID, application_id: UUID) -> InterviewKitSnapshot:
        try:
            with self.database.session() as session:
                application = ApplicationRepository(session).get(
                    user_id=user_id,
                    application_id=application_id,
                )
                if application is None:
                    raise InterviewKitNotFound
                if application.status not in ALLOWED_INTERVIEW_PREPARATION_STATUSES:
                    raise InterviewKitInvalidStatus
                persisted_resume = (
                    ResumeRepository(session).get(
                        user_id=user_id,
                        resume_id=application.resume_id,
                    )
                    if application.resume_id is not None
                    else ResumeRepository(session).get_active(user_id=user_id)
                )
                if persisted_resume is None:
                    raise InterviewKitResumeRequired
                job = JobRepository(session).get(application.job_id)
                if job is None:
                    raise InterviewKitNotFound
                kit = InterviewKitRepository(session).create(
                    user_id=user_id,
                    application_id=application_id,
                    resume_id=persisted_resume.resume.id,
                    questions=self._questions(job=job, resume=persisted_resume.resume),
                )
                if kit is None:
                    raise InterviewKitNotFound
                return InterviewKitSnapshot(kit=kit, application=application, job=job)
        except IntegrityError:
            return self.get(user_id=user_id, application_id=application_id)

    def get(self, *, user_id: UUID, application_id: UUID) -> InterviewKitSnapshot:
        with self.database.session() as session:
            application = ApplicationRepository(session).get(
                user_id=user_id,
                application_id=application_id,
            )
            kit = InterviewKitRepository(session).get(
                user_id=user_id,
                application_id=application_id,
            )
            if application is None or kit is None:
                raise InterviewKitNotFound
            job = JobRepository(session).get(application.job_id)
            if job is None:
                raise InterviewKitNotFound
            return InterviewKitSnapshot(kit=kit, application=application, job=job)

    def update(
        self,
        *,
        user_id: UUID,
        application_id: UUID,
        responses: dict[str, str],
        confirm_reviewed: bool,
    ) -> InterviewKitSnapshot:
        cleaned = {key: value.strip() for key, value in responses.items() if value.strip()}
        if any(len(value) > 4_000 for value in cleaned.values()) or sum(
            len(value) for value in cleaned.values()
        ) > 20_000:
            raise InterviewKitInvalidResponse
        with self.database.session() as session:
            applications = ApplicationRepository(session)
            application = applications.get(user_id=user_id, application_id=application_id)
            if application is None:
                raise InterviewKitNotFound
            try:
                kit = InterviewKitRepository(session).update(
                    user_id=user_id,
                    application_id=application_id,
                    responses=cleaned,
                    confirm_reviewed=confirm_reviewed,
                )
            except ValueError as error:
                raise InterviewKitInvalidResponse from error
            if kit is None:
                raise InterviewKitNotFound
            job = JobRepository(session).get(application.job_id)
            if job is None:
                raise InterviewKitNotFound
            return InterviewKitSnapshot(kit=kit, application=application, job=job)

    @classmethod
    def _questions(cls, *, job: Job, resume: Resume) -> tuple[InterviewQuestion, ...]:
        evidence = tuple(resume.experience + resume.projects + resume.achievements)
        resume_skills = {skill.name.casefold(): skill.name for skill in resume.skills}
        required = []
        seen: set[str] = set()
        for skill in job.required_skills:
            key = skill.name.casefold()
            if key not in seen:
                required.append(skill.name)
                seen.add(key)

        questions: list[InterviewQuestion] = [
            InterviewQuestion(
                id="career-story",
                category="career_story",
                question=f"How does your experience prepare you for the {job.title} role?",
                why_it_matters="A clear career story helps the interviewer connect your verified experience to this role.",
                evidence_prompts=cls._evidence_prompts(evidence) or (
                    "Choose one verified experience, project, or achievement from your resume.",
                ),
            )
        ]
        matched = [skill for skill in required if skill.casefold() in resume_skills][:2]
        for index, skill in enumerate(matched, start=1):
            questions.append(
                InterviewQuestion(
                    id=f"role-skill-{index}",
                    category="role_specific",
                    question=f"Tell me about a time you used {skill} to produce a useful outcome.",
                    why_it_matters=f"{skill} appears in the role requirements and in your verified resume skills.",
                    evidence_prompts=cls._evidence_prompts(evidence, contains=skill) or (
                        f"Use only a real example that demonstrates {skill}; add context and a measurable result if known.",
                    ),
                )
            )
        missing = [skill for skill in required if skill.casefold() not in resume_skills]
        if missing:
            skill = missing[0]
            questions.append(
                InterviewQuestion(
                    id="skill-gap",
                    category="skill_gap",
                    question=f"How would you approach work requiring {skill}, which is not evidenced in your current resume?",
                    why_it_matters="Addressing a gap directly is more credible than implying experience you have not documented.",
                    evidence_prompts=(
                        "State your actual level honestly.",
                        "Connect a genuinely transferable skill or learning example only if it is true.",
                    ),
                )
            )
        questions.extend(
            (
                InterviewQuestion(
                    id="motivation",
                    category="motivation",
                    question=f"Why are you interested in this {job.title} opportunity at {job.company}?",
                    why_it_matters="Motivation is personal and should come from you, not be inferred from a resume.",
                    evidence_prompts=(
                        "Name what genuinely interests you about the work or organization.",
                        "Do not claim company knowledge you have not independently verified.",
                    ),
                ),
                InterviewQuestion(
                    id="behavioral",
                    category="behavioral",
                    question="Describe a difficult collaboration or decision and what you learned from it.",
                    why_it_matters="This reveals how you work with people, handle tradeoffs, and reflect on outcomes.",
                    evidence_prompts=cls._evidence_prompts(evidence) or (
                        "Choose a real situation and separate the situation, your action, and the result.",
                    ),
                ),
            )
        )
        return tuple(questions)

    @staticmethod
    def _evidence_prompts(
        evidence: tuple[str, ...],
        *,
        contains: str | None = None,
    ) -> tuple[str, ...]:
        candidates = evidence
        if contains is not None:
            candidates = tuple(item for item in evidence if contains.casefold() in item.casefold())
        return tuple(f"Resume evidence: {item[:300]}" for item in candidates[:2])

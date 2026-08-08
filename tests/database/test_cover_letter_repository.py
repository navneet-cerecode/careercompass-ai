from database.base import Base
from database.repositories.cover_letters import CoverLetterRepository
from database.repositories.jobs import JobRepository
from database.repositories.resumes import ResumeRepository
from database.repositories.tailoring import TailoringPlanRepository
from database.repositories.users import UserRepository
from database.session import Database
from models.cover_letter import CoverLetterContent, CoverLetterEvidence
from models.job import Job
from models.resume import Resume
from models.skill import Skill
from services.tailoring import FactualTailoringService


def content() -> CoverLetterContent:
    return CoverLetterContent(
        candidate_name="Owner",
        candidate_email="owner@example.com",
        company_name="Example Ltd",
        job_title="Operations Manager",
        salutation="Dear hiring team,",
        opening="I am applying for the Operations Manager position at Example Ltd.",
        evidence_paragraph="My verified background includes Excel.",
        motivation_paragraph="I am interested in learning more about the role.",
        closing_paragraph="Thank you for considering my application.",
        sign_off="Sincerely,",
    )


def test_cover_letter_repository_versions_and_approves_owner_scoped_content():
    database = Database("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(database.engine)
    with database.session() as session:
        users = UserRepository(session)
        owner = users.create(email="owner@example.com", name="Owner")
        other = users.create(email="other@example.com", name="Other")
        resume = (
            ResumeRepository(session)
            .save_version(
                user_id=owner.id,
                resume=Resume(
                    name="Owner",
                    raw_text="Excel operations coordinator",
                    skills=[Skill(name="Excel")],
                ),
            )
            .resume
        )
        job = JobRepository(session).upsert(
            Job(
                title="Operations Manager",
                company="Example Ltd",
                location="India",
                description="Manage operations with Excel.",
                required_skills=[Skill(name="Excel")],
                url="https://example.com/jobs/operations",
            )
        )
        plan = TailoringPlanRepository(session).save(
            user_id=owner.id,
            plan=FactualTailoringService().create_plan(resume, job),
        )
        repository = CoverLetterRepository(session)
        suggested = content()
        evidence = (CoverLetterEvidence(kind="skill", source_index=0, source_text="Excel"),)
        first = repository.create_version(
            user_id=owner.id,
            plan_id=plan.id,
            source_resume_id=resume.id,
            job_id=job.id,
            suggested=suggested,
            accepted=suggested,
            evidence=evidence,
        )
        edited = suggested.model_copy(update={"opening": "I am applying for this role."})
        second = repository.create_version(
            user_id=owner.id,
            plan_id=plan.id,
            source_resume_id=resume.id,
            job_id=job.id,
            suggested=suggested,
            accepted=edited,
            evidence=evidence,
        )
        approved = repository.approve(user_id=owner.id, cover_letter_id=second.id)

        assert first.version == 1
        assert second.version == 2
        assert [
            item.id for item in repository.list_versions(user_id=owner.id, plan_id=plan.id)
        ] == [second.id, first.id]
        assert approved is not None
        assert approved.verification_status == "user_verified"
        assert approved.approved_at is not None
        assert repository.get(user_id=other.id, cover_letter_id=second.id) is None

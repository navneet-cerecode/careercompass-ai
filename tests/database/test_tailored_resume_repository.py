from database.base import Base
from database.repositories.jobs import JobRepository
from database.repositories.resumes import ResumeRepository
from database.repositories.tailored_resumes import TailoredResumeRepository
from database.repositories.tailoring import TailoringPlanRepository
from database.repositories.users import UserRepository
from database.session import Database
from models.job import Job
from models.resume import Resume
from models.skill import Skill
from models.tailored_resume import TailoredResumeContent, TailoredResumeSelections
from services.tailoring import FactualTailoringService


def test_tailored_resume_repository_versions_and_approves_owner_scoped_content():
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
                    skills=[Skill(name="Communication"), Skill(name="Excel")],
                    experience=["Coordinated meetings.", "Built Excel reports."],
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
        original = TailoredResumeContent(
            name=resume.name,
            skills=tuple(resume.skills),
            experience=tuple(resume.experience),
        )
        suggested = original.model_copy(
            update={
                "skills": plan.plan.skills,
                "experience": plan.plan.experience,
            }
        )
        repository = TailoredResumeRepository(session)
        first = repository.create_version(
            user_id=owner.id,
            plan_id=plan.id,
            source_resume_id=resume.id,
            job_id=job.id,
            original=original,
            suggested=suggested,
            accepted=suggested,
            selections=TailoredResumeSelections(),
        )
        second = repository.create_version(
            user_id=owner.id,
            plan_id=plan.id,
            source_resume_id=resume.id,
            job_id=job.id,
            original=original,
            suggested=suggested,
            accepted=original,
            selections=TailoredResumeSelections(
                skills="original",
                experience="original",
                projects="original",
            ),
        )
        approved = repository.approve(
            user_id=owner.id,
            tailored_resume_id=second.id,
        )

        assert first.version == 1
        assert second.version == 2
        assert [
            item.id for item in repository.list_versions(user_id=owner.id, plan_id=plan.id)
        ] == [
            second.id,
            first.id,
        ]
        assert approved is not None
        assert approved.verification_status == "user_verified"
        assert approved.user_review_required is False
        assert approved.approved_at is not None
        assert repository.get(user_id=other.id, tailored_resume_id=second.id) is None

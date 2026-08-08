from sqlalchemy import func, select

from database.base import Base
from database.models.tailoring import TailoringPlanRecord
from database.repositories.jobs import JobRepository
from database.repositories.resumes import ResumeRepository
from database.repositories.tailoring import TailoringPlanRepository
from database.repositories.users import UserRepository
from database.session import Database
from models.job import Job
from models.resume import Resume
from models.skill import Skill
from services.tailoring import FactualTailoringService


def test_tailoring_repository_is_idempotent_and_owner_scoped():
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
                description="Excel inventory operations",
                required_skills=[Skill(name="Excel")],
                url="https://example.com/jobs/operations",
            )
        )
        plan = FactualTailoringService().create_plan(resume, job)
        repository = TailoringPlanRepository(session)
        first = repository.save(user_id=owner.id, plan=plan)
        second = repository.save(user_id=owner.id, plan=plan)

        assert first.id == second.id
        assert repository.get(user_id=other.id, plan_id=first.id) is None
        assert session.scalar(select(func.count()).select_from(TailoringPlanRecord)) == 1

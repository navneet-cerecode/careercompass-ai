from sqlalchemy import func, select

from database.base import Base
from database.models.resumes import ResumeRecord, SkillRecord
from database.repositories.resumes import ResumeRepository
from database.repositories.users import UserRepository
from database.session import Database
from models.resume import Resume
from models.skill import Skill


def make_database() -> Database:
    database = Database("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(database.engine)
    return database


def make_resume(raw_text: str) -> Resume:
    return Resume(
        name="Ada Lovelace",
        email="ada@example.com",
        raw_text=raw_text,
        skills=[Skill(name="Python"), Skill(name="SQL")],
        projects=["Analytical Engine"],
    )


def test_resume_repository_versions_profiles_and_reuses_normalized_skills():
    database = make_database()
    with database.session() as session:
        user = UserRepository(session).create(
            email="ADA@EXAMPLE.COM",
            name="Ada Lovelace",
        )
        repository = ResumeRepository(session)
        first = repository.save_version(
            user_id=user.id,
            resume=make_resume("Ada Lovelace\nPython"),
            original_filename="../ada-v1.txt",
        )
        second = repository.save_version(
            user_id=user.id,
            resume=make_resume("Ada Lovelace\nPython and SQL"),
            original_filename="ada-v2.txt",
        )

    assert first.version == 1
    assert second.version == 2
    assert second.is_active is True
    assert second.original_filename == "ada-v2.txt"

    with database.session() as session:
        assert session.scalar(select(func.count()).select_from(SkillRecord)) == 2
        records = session.scalars(select(ResumeRecord).order_by(ResumeRecord.version)).all()
        assert [record.is_active for record in records] == [False, True]


def test_resume_repository_enforces_owner_scope():
    database = make_database()
    with database.session() as session:
        users = UserRepository(session)
        owner = users.create(email="owner@example.com", name="Owner")
        other = users.create(email="other@example.com", name="Other")
        saved = ResumeRepository(session).save_version(
            user_id=owner.id,
            resume=make_resume("Owner\nPython"),
        )

    with database.session() as session:
        repository = ResumeRepository(session)
        assert repository.get(user_id=other.id, resume_id=saved.resume.id) is None
        loaded = repository.get(
            user_id=owner.id,
            resume_id=saved.resume.id,
        )

    assert loaded is not None
    assert loaded.resume.raw_text == "Owner\nPython"
    assert [skill.name for skill in loaded.resume.skills] == ["Python", "SQL"]


def test_resume_repository_preserves_skill_order_across_sessions():
    database = make_database()
    with database.session() as session:
        owner = UserRepository(session).create(email="owner@example.com", name="Owner")
        saved = ResumeRepository(session).save_version(
            user_id=owner.id,
            resume=make_resume("Owner\nPython"),
        )

    with database.session() as session:
        loaded = ResumeRepository(session).get(
            user_id=owner.id,
            resume_id=saved.resume.id,
        )

    assert loaded is not None
    assert [skill.name for skill in loaded.resume.skills] == ["Python", "SQL"]


def test_user_repository_normalizes_email_and_rejects_duplicates():
    database = make_database()
    with database.session() as session:
        repository = UserRepository(session)
        user = repository.create(
            email="  ADA@EXAMPLE.COM ",
            name=" Ada Lovelace ",
        )

        assert user.email == "ada@example.com"
        assert user.name == "Ada Lovelace"

        try:
            repository.create(
                email="ada@example.com",
                name="Duplicate",
            )
        except ValueError as error:
            assert "already exists" in str(error)
        else:
            raise AssertionError("Duplicate user email was accepted")

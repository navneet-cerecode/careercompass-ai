from sqlalchemy import func, select

from database.base import Base
from database.models.jobs import JobRecord, JobSourceRecord
from database.repositories.jobs import JobRepository
from database.session import Database
from models.enums import JobSource
from models.job import Job
from models.skill import Skill


def make_database() -> Database:
    database = Database("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(database.engine)
    return database


def make_job(
    *,
    source: JobSource = JobSource.JSEARCH,
    source_name: str = "jsearch",
    source_url: str = "https://source.example/jobs/1",
    description: str = "Python",
    required_skills=None,
) -> Job:
    return Job(
        title="Data Engineer",
        company="Example Corp",
        location="India",
        description=description,
        required_skills=required_skills or [],
        source=source,
        source_name=source_name,
        external_id=f"{source_name}-1",
        source_url=source_url,
        url=source_url,
    )


def test_repository_merges_duplicate_jobs_and_preserves_sources():
    database = make_database()
    first = make_job()
    duplicate = make_job(
        source=JobSource.WORKDAY,
        source_name="workday:example",
        source_url="https://careers.example/jobs/1",
        description="Python, SQL, and data pipelines",
    )

    with database.session() as session:
        repository = JobRepository(session)
        persisted_first = repository.upsert(first)
        persisted_duplicate = repository.upsert(duplicate)

    assert persisted_first.id == persisted_duplicate.id
    assert persisted_duplicate.description == "Python, SQL, and data pipelines"

    with database.session() as session:
        assert session.scalar(select(func.count()).select_from(JobRecord)) == 1
        assert session.scalar(select(func.count()).select_from(JobSourceRecord)) == 2


def test_repository_returns_jobs_in_requested_order():
    database = make_database()
    first = make_job()
    second = make_job(
        source_url="https://source.example/jobs/2",
    ).model_copy(
        update={
            "title": "Machine Learning Engineer",
            "external_id": "jsearch-2",
        }
    )

    with database.session() as session:
        repository = JobRepository(session)
        persisted = repository.upsert_many((first, second))

    with database.session() as session:
        loaded = JobRepository(session).get_many((persisted[1].id, persisted[0].id))

    assert loaded is not None
    assert [job.title for job in loaded] == [
        "Machine Learning Engineer",
        "Data Engineer",
    ]


def test_repository_tracks_stable_provider_identity_when_source_url_changes():
    database = make_database()
    first = make_job(source_url="https://source.example/jobs/old")
    refreshed = make_job(source_url="https://source.example/jobs/new")

    with database.session() as session:
        repository = JobRepository(session)
        persisted_first = repository.upsert(first)
        persisted_refreshed = repository.upsert(refreshed)

    assert persisted_first.id == persisted_refreshed.id
    with database.session() as session:
        sources = session.scalars(select(JobSourceRecord)).all()
        assert len(sources) == 1
        assert sources[0].external_id == "jsearch-1"
        assert sources[0].source_url == "https://source.example/jobs/new"


def test_repository_preserves_required_skills():
    database = make_database()
    job = make_job(required_skills=[Skill(name="Inventory Planning")])

    with database.session() as session:
        persisted = JobRepository(session).upsert(job)
    with database.session() as session:
        loaded = JobRepository(session).get(persisted.id)

    assert loaded is not None
    assert [skill.name for skill in loaded.required_skills] == ["Inventory Planning"]

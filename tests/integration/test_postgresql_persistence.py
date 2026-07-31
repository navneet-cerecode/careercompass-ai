"""Real PostgreSQL migration and repository integration gate."""

import os

import pytest
from alembic import command
from alembic.runtime.migration import MigrationContext
from sqlalchemy.engine import make_url

from database.alembic import build_alembic_config
from database.repositories.applications import ApplicationRepository, SavedJobRepository
from database.repositories.jobs import JobRepository
from database.repositories.users import UserRepository
from database.session import Database
from models.enums import ApplicationStatus
from models.job import Job

pytestmark = pytest.mark.postgres


def require_postgresql_url() -> str:
    database_url = os.getenv("TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("TEST_DATABASE_URL is not configured.")
    if not database_url.startswith(("postgresql://", "postgresql+psycopg://")):
        pytest.fail("TEST_DATABASE_URL must identify a dedicated PostgreSQL database.")
    database_name = make_url(database_url).database or ""
    if not database_name.endswith("_test"):
        pytest.fail("TEST_DATABASE_URL database name must end with '_test'.")
    return database_url


def test_postgresql_migrations_and_owner_scoped_repositories():
    database_url = require_postgresql_url()
    config = build_alembic_config(database_url)
    database = Database(database_url)

    try:
        command.downgrade(config, "base")
        command.upgrade(config, "head")
        with database.engine.connect() as connection:
            assert MigrationContext.configure(connection).get_current_revision() == "0005"
        assert database.check_connection() is True

        with database.session() as session:
            user = UserRepository(session).create(
                email="postgres-gate@example.com",
                name="PostgreSQL Gate",
            )
            job = JobRepository(session).upsert(
                Job(
                    title="Reliability Engineer",
                    company="CareerCompass Test",
                    location="Remote",
                    description="Validate PostgreSQL persistence.",
                    url="https://example.com/jobs/postgres-gate",
                )
            )
            saved_job = SavedJobRepository(session).save(
                user_id=user.id,
                job_id=job.id,
                notes="Integration gate",
            )
            application = ApplicationRepository(session).create(
                user_id=user.id,
                job_id=job.id,
                status=ApplicationStatus.SAVED,
            )

        with database.session() as session:
            assert (
                SavedJobRepository(session).get(
                    user_id=user.id,
                    job_id=job.id,
                )
                == saved_job
            )
            loaded = ApplicationRepository(session).get(
                user_id=user.id,
                application_id=application.id,
            )
            assert loaded is not None
            assert loaded.status == ApplicationStatus.SAVED
    finally:
        database.dispose()
        command.downgrade(config, "base")

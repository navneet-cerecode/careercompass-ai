from alembic import command
from alembic.runtime.migration import MigrationContext
from sqlalchemy import create_engine, inspect

from database.alembic import build_alembic_config


def current_revision(database_url: str) -> str | None:
    engine = create_engine(database_url)
    with engine.connect() as connection:
        return MigrationContext.configure(connection).get_current_revision()


def test_baseline_migration_upgrades_and_downgrades(tmp_path):
    database_url = f"sqlite+pysqlite:///{tmp_path / 'migration.db'}"
    config = build_alembic_config(database_url)

    command.upgrade(config, "0001")
    assert current_revision(database_url) == "0001"

    command.downgrade(config, "base")
    assert current_revision(database_url) is None


def test_job_schema_migration_is_reversible(tmp_path):
    database_url = f"sqlite+pysqlite:///{tmp_path / 'jobs.db'}"
    config = build_alembic_config(database_url)

    command.upgrade(config, "0002")
    engine = create_engine(database_url)
    assert current_revision(database_url) == "0002"
    assert {"jobs", "job_sources"} <= set(inspect(engine).get_table_names())

    command.downgrade(config, "0001")
    assert "jobs" not in inspect(engine).get_table_names()


def test_resume_ownership_schema_migration_is_reversible(tmp_path):
    database_url = f"sqlite+pysqlite:///{tmp_path / 'resumes.db'}"
    config = build_alembic_config(database_url)

    command.upgrade(config, "0003")
    engine = create_engine(database_url)
    assert current_revision(database_url) == "0003"
    assert {"users", "resumes", "skills", "resume_skills"} <= set(inspect(engine).get_table_names())

    command.downgrade(config, "0002")
    assert "resumes" not in inspect(engine).get_table_names()


def test_history_schema_migration_is_reversible(tmp_path):
    database_url = f"sqlite+pysqlite:///{tmp_path / 'history.db'}"
    config = build_alembic_config(database_url)

    command.upgrade(config, "0004")
    engine = create_engine(database_url)
    assert current_revision(database_url) == "0004"
    assert {"searches", "search_results", "recommendations"} <= set(
        inspect(engine).get_table_names()
    )

    command.downgrade(config, "0003")
    assert "recommendations" not in inspect(engine).get_table_names()


def test_application_tracking_schema_migration_is_reversible(tmp_path):
    database_url = f"sqlite+pysqlite:///{tmp_path / 'applications.db'}"
    config = build_alembic_config(database_url)

    command.upgrade(config, "0005")
    engine = create_engine(database_url)
    assert current_revision(database_url) == "0005"
    assert {"saved_jobs", "applications", "application_events"} <= set(
        inspect(engine).get_table_names()
    )

    command.downgrade(config, "0004")
    assert "applications" not in inspect(engine).get_table_names()


def test_background_task_schema_migration_is_reversible(tmp_path):
    database_url = f"sqlite+pysqlite:///{tmp_path / 'tasks.db'}"
    config = build_alembic_config(database_url)

    command.upgrade(config, "0006")
    engine = create_engine(database_url)
    assert current_revision(database_url) == "0006"
    assert "background_tasks" in inspect(engine).get_table_names()
    check_names = {
        constraint["name"]
        for constraint in inspect(engine).get_check_constraints("background_tasks")
    }
    assert {
        "ck_background_tasks_attempt_count_nonnegative",
        "ck_background_tasks_attempt_count_within_limit",
        "ck_background_tasks_max_attempts_bounds",
        "ck_background_tasks_status",
    } <= check_names

    command.downgrade(config, "0005")
    assert "background_tasks" not in inspect(engine).get_table_names()


def test_job_discovery_task_schema_migration_is_reversible(tmp_path):
    database_url = f"sqlite+pysqlite:///{tmp_path / 'discovery-tasks.db'}"
    config = build_alembic_config(database_url)

    command.upgrade(config, "0007")
    engine = create_engine(database_url)
    assert current_revision(database_url) == "0007"
    assert {"job_discovery_tasks", "job_discovery_task_results"} <= set(
        inspect(engine).get_table_names()
    )

    command.downgrade(config, "0006")
    assert "job_discovery_tasks" not in inspect(engine).get_table_names()


def test_task_hardening_schema_migration_is_reversible(tmp_path):
    database_url = f"sqlite+pysqlite:///{tmp_path / 'task-hardening.db'}"
    config = build_alembic_config(database_url)

    command.upgrade(config, "0008")
    engine = create_engine(database_url)
    inspector = inspect(engine)
    assert current_revision(database_url) == "0008"
    assert "task_outbox" in inspector.get_table_names()
    task_columns = {column["name"] for column in inspector.get_columns("background_tasks")}
    assert {"heartbeat_at", "cancel_requested_at"} <= task_columns

    command.downgrade(config, "0007")
    assert "task_outbox" not in inspect(engine).get_table_names()


def test_external_identity_schema_migration_is_reversible(tmp_path):
    database_url = f"sqlite+pysqlite:///{tmp_path / 'identities.db'}"
    config = build_alembic_config(database_url)

    command.upgrade(config, "head")
    engine = create_engine(database_url)
    assert current_revision(database_url) == "0009"
    assert "user_identities" in inspect(engine).get_table_names()

    command.downgrade(config, "0008")
    assert "user_identities" not in inspect(engine).get_table_names()

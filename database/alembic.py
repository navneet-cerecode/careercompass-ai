"""Programmatic Alembic configuration without credentials in source control."""

from pathlib import Path

from alembic.config import Config

from database.url import sqlalchemy_database_url

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def build_alembic_config(database_url: str) -> Config:
    config = Config(str(PROJECT_ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(PROJECT_ROOT / "database/migrations"))
    config.set_main_option(
        "sqlalchemy.url",
        sqlalchemy_database_url(database_url).replace("%", "%%"),
    )
    return config

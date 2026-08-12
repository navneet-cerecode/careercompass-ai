import pytest

from core.config import Settings
from database.url import sqlalchemy_database_url


def test_database_url_is_required_only_when_persistence_is_used():
    settings = Settings(_env_file=None)

    with pytest.raises(ValueError, match="DATABASE_URL is required"):
        settings.require_database_url()


def test_database_url_remains_secret_in_settings_representation():
    settings = Settings(
        database_url="postgresql+psycopg://user:secret@localhost/careercompass",
        _env_file=None,
    )

    assert settings.require_database_url().endswith("@localhost/careercompass")
    assert "secret@localhost" not in repr(settings)


@pytest.mark.parametrize("scheme", ["postgresql", "postgres"])
def test_platform_postgres_urls_select_psycopg3(scheme):
    assert sqlalchemy_database_url(f"{scheme}://user:secret@db/app") == (
        "postgresql+psycopg://user:secret@db/app"
    )


def test_explicit_database_driver_is_preserved():
    url = "postgresql+psycopg://user:secret@db/app"
    assert sqlalchemy_database_url(url) == url

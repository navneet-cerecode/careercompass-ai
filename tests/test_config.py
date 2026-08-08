from pathlib import Path

import pytest
from pydantic import ValidationError


def test_settings_load_without_credentials(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    monkeypatch.delenv("RAPIDAPI_KEY", raising=False)
    from core.config import Settings

    settings = Settings(_env_file=None)

    assert settings.groq_api_key is None
    assert settings.rapidapi_key is None
    assert settings.groq_model == "llama-3.3-70b-versatile"
    assert settings.temperature == 0.2
    assert settings.max_tokens == 1024
    assert settings.max_jobs == 50
    assert settings.default_location == "India"


def test_settings_load_prefixed_llm_configuration(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "test-groq-key")
    monkeypatch.setenv("RAPIDAPI_KEY", "test-rapidapi-key")
    monkeypatch.setenv("GROQ_TEMPERATURE", "0.35")
    monkeypatch.setenv("GROQ_MAX_TOKENS", "2048")

    from core.config import Settings

    settings = Settings(_env_file=None)

    assert settings.groq_api_key is not None
    assert settings.groq_api_key.get_secret_value() == "test-groq-key"
    assert settings.rapidapi_key is not None
    assert settings.rapidapi_key.get_secret_value() == "test-rapidapi-key"
    assert settings.temperature == 0.35
    assert settings.max_tokens == 2048
    assert "test-groq-key" not in repr(settings)
    assert "test-rapidapi-key" not in repr(settings)


def test_environment_example_documents_required_credentials():
    content = Path(".env.example").read_text(encoding="utf-8")

    assert "GROQ_API_KEY=" in content
    assert "RAPIDAPI_KEY=" in content
    assert "GROQ_MODEL=" in content
    assert "REDIS_URL=" in content
    assert "WORKER_MESSAGE_MAX_AGE_MS=" in content


def test_worker_settings_are_safe_without_a_broker(monkeypatch):
    monkeypatch.delenv("REDIS_URL", raising=False)
    from core.config import Settings

    settings = Settings(_env_file=None)

    assert settings.redis_url is None
    assert settings.worker_broker_namespace == "careercompass"
    assert settings.worker_queue_name == "careercompass"
    assert settings.worker_max_retries == 3
    assert settings.worker_time_limit_ms == 300_000
    assert settings.worker_message_max_age_ms == 3_600_000

    try:
        settings.require_redis_url()
    except ValueError as error:
        assert str(error) == "REDIS_URL is required for background workers."
    else:
        raise AssertionError("Missing REDIS_URL should fail at the worker boundary.")


def test_worker_settings_hide_redis_credentials(monkeypatch):
    monkeypatch.setenv("REDIS_URL", "redis://:private-password@redis.internal:6379/0")
    monkeypatch.setenv("WORKER_MAX_RETRIES", "5")
    monkeypatch.setenv("WORKER_TIME_LIMIT_MS", "120000")
    from core.config import Settings

    settings = Settings(_env_file=None)

    assert settings.require_redis_url().endswith("@redis.internal:6379/0")
    assert settings.worker_max_retries == 5
    assert settings.worker_time_limit_ms == 120_000
    assert "private-password" not in repr(settings)


def test_production_configuration_fails_closed_when_dependencies_are_missing():
    from core.config import Settings

    with pytest.raises(ValidationError, match="DATABASE_URL.*REDIS_URL.*TASK_TOKEN_SECRET"):
        Settings(APP_ENVIRONMENT="production", _env_file=None)


def test_production_configuration_requires_https_identity_and_explicit_hosts():
    from core.config import Settings

    common = {
        "APP_ENVIRONMENT": "production",
        "DATABASE_URL": "postgresql+psycopg://app:password@db/app",
        "REDIS_URL": "redis://redis:6379/0",
        "TASK_TOKEN_SECRET": "test-task-secret-that-is-at-least-32-bytes",
        "auth_audience": "urn:solarahire:api",
        "_env_file": None,
    }
    with pytest.raises(ValidationError, match="must use HTTPS"):
        Settings(
            **common,
            auth_issuer="http://identity.example.test/",
            auth_jwks_url="http://identity.example.test/jwks.json",
        )
    with pytest.raises(ValidationError, match="explicit hostnames"):
        Settings(
            **common,
            auth_issuer="https://identity.example.test/",
            auth_jwks_url="https://identity.example.test/jwks.json",
            ALLOWED_HOSTS="*",
        )

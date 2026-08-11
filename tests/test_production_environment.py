from scripts.check_production_env import validate_environment


def valid_environment() -> dict[str, str]:
    return {
        "APP_ENVIRONMENT": "production",
        "ALLOWED_HOSTS": "api,api.solarahire.test",
        "DATABASE_URL": "postgresql+psycopg://app:private@db.internal/app",
        "REDIS_URL": "rediss://default:private@redis.internal:6379/0",
        "TASK_TOKEN_SECRET": "task-secret-that-is-longer-than-thirty-two-bytes",
        "AUTH_ISSUER": "https://tenant.auth0.test/",
        "AUTH_AUDIENCE": "urn:solarahire:api",
        "AUTH_JWKS_URL": "https://tenant.auth0.test/.well-known/jwks.json",
        "APP_BASE_URL": "https://app.solarahire.test",
        "SOLARAHIRE_SITE_URL": "https://app.solarahire.test",
        "SOLARAHIRE_API_URL": "http://api:8000",
        "AUTH0_DOMAIN": "tenant.auth0.test",
        "AUTH0_CLIENT_ID": "public-client-id",
        "AUTH0_CLIENT_SECRET": "client-secret-not-printed",
        "AUTH0_SECRET": "session-secret-that-is-longer-than-thirty-two-bytes",
        "AUTH0_AUDIENCE": "urn:solarahire:api",
        "GROQ_API_KEY": "configured-groq-key",
        "RAPIDAPI_KEY": "configured-rapidapi-key",
    }


def test_production_environment_check_accepts_complete_secure_configuration():
    assert validate_environment(valid_environment()) == ()


def test_production_environment_check_reports_names_without_secret_values():
    values = valid_environment()
    values["AUTH0_CLIENT_SECRET"] = "replace-with-private-value"
    values["APP_BASE_URL"] = "http://localhost:3000"

    errors = validate_environment(values)

    assert any("AUTH0_CLIENT_SECRET" in error for error in errors)
    assert any("APP_BASE_URL: HTTPS" in error for error in errors)
    assert "replace-with-private-value" not in " ".join(errors)


def test_production_environment_check_rejects_identity_and_origin_drift():
    values = valid_environment()
    values["AUTH0_AUDIENCE"] = "wrong-audience"
    values["AUTH0_DOMAIN"] = "wrong.auth0.test"
    values["SOLARAHIRE_SITE_URL"] = "https://other.solarahire.test"

    errors = validate_environment(values)

    assert any("AUTH0_AUDIENCE" in error for error in errors)
    assert any("AUTH0_DOMAIN" in error for error in errors)
    assert any("same origin" in error for error in errors)


def test_production_environment_check_requires_analytics_salt_only_when_enabled():
    values = valid_environment()
    values["ANALYTICS_ENABLED"] = "true"
    values["ANALYTICS_IDENTITY_SALT"] = "replace-with-private-salt"

    assert any("ANALYTICS_IDENTITY_SALT" in error for error in validate_environment(values))

    values["ANALYTICS_ENABLED"] = "false"
    assert not any("ANALYTICS_IDENTITY_SALT" in error for error in validate_environment(values))


def test_production_environment_check_rejects_backend_placeholders():
    values = valid_environment()
    values["DATABASE_URL"] = "postgresql+psycopg://app:replace-with-password@db.internal/app"
    values["TASK_TOKEN_SECRET"] = "replace-with-task-secret-that-is-long-enough"

    errors = validate_environment(values)

    assert any("DATABASE_URL" in error for error in errors)
    assert any("TASK_TOKEN_SECRET" in error for error in errors)
    assert "replace-with-password" not in " ".join(errors)

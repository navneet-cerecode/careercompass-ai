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
        "AUTH0_DOMAIN": "tenant.auth0.test",
        "AUTH0_CLIENT_ID": "public-client-id",
        "AUTH0_CLIENT_SECRET": "client-secret-not-printed",
        "AUTH0_SECRET": "session-secret-that-is-longer-than-thirty-two-bytes",
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

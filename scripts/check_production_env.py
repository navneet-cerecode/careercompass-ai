"""Fail-closed production environment diagnostic without printing values."""

import os
from urllib.parse import urlparse

from pydantic import ValidationError

from core.config import Settings

FRONTEND_REQUIRED = (
    "APP_BASE_URL",
    "SOLARAHIRE_SITE_URL",
    "SOLARAHIRE_API_URL",
    "AUTH0_DOMAIN",
    "AUTH0_CLIENT_ID",
    "AUTH0_CLIENT_SECRET",
    "AUTH0_SECRET",
    "AUTH0_AUDIENCE",
)
BACKEND_REQUIRED = (
    "DATABASE_URL",
    "REDIS_URL",
    "TASK_TOKEN_SECRET",
    "AUTH_ISSUER",
    "AUTH_AUDIENCE",
    "AUTH_JWKS_URL",
)
EXTERNAL_PROVIDER_REQUIRED = ("GROQ_API_KEY", "RAPIDAPI_KEY")


def validate_environment(environ: dict[str, str] | None = None) -> tuple[str, ...]:
    values = environ if environ is not None else dict(os.environ)
    errors: list[str] = []
    settings_values = dict(values)
    for environment_name, field_name in {
        "AUTH_ISSUER": "auth_issuer",
        "AUTH_AUDIENCE": "auth_audience",
        "AUTH_JWKS_URL": "auth_jwks_url",
    }.items():
        if environment_name in values:
            settings_values[field_name] = values[environment_name]
    try:
        Settings(_env_file=None, **settings_values)
    except ValidationError as error:
        errors.append(f"Backend settings: {error.error_count()} validation error(s).")

    for name in (*BACKEND_REQUIRED, *FRONTEND_REQUIRED, *EXTERNAL_PROVIDER_REQUIRED):
        value = values.get(name, "").strip()
        if not value:
            errors.append(f"{name}: missing.")
        elif _is_placeholder(value):
            errors.append(f"{name}: placeholder value must be replaced.")

    for name in ("APP_BASE_URL", "SOLARAHIRE_SITE_URL"):
        value = values.get(name, "")
        if value and urlparse(value).scheme != "https":
            errors.append(f"{name}: HTTPS is required.")

    api_url = values.get("SOLARAHIRE_API_URL", "")
    if api_url and urlparse(api_url).scheme not in {"http", "https"}:
        errors.append("SOLARAHIRE_API_URL: HTTP or HTTPS is required.")

    if _origin(values.get("APP_BASE_URL", "")) != _origin(values.get("SOLARAHIRE_SITE_URL", "")):
        errors.append("APP_BASE_URL and SOLARAHIRE_SITE_URL must use the same origin.")

    auth0_domain = values.get("AUTH0_DOMAIN", "").strip()
    identity_hosts = {
        urlparse(values.get(name, "")).hostname
        for name in ("AUTH_ISSUER", "AUTH_JWKS_URL")
        if values.get(name)
    }
    if auth0_domain and ("/" in auth0_domain or "://" in auth0_domain):
        errors.append("AUTH0_DOMAIN: use a hostname without a scheme or path.")
    elif auth0_domain and identity_hosts != {auth0_domain}:
        errors.append("AUTH0_DOMAIN must match the issuer and signing-key host.")

    if values.get("AUTH0_AUDIENCE") != values.get("AUTH_AUDIENCE"):
        errors.append("AUTH0_AUDIENCE must match AUTH_AUDIENCE.")

    auth0_secret = values.get("AUTH0_SECRET", "")
    if auth0_secret and len(auth0_secret) < 32:
        errors.append("AUTH0_SECRET: must contain at least 32 characters.")

    analytics_enabled = values.get("ANALYTICS_ENABLED", "false").casefold() in {
        "1",
        "true",
        "yes",
        "on",
    }
    analytics_salt = values.get("ANALYTICS_IDENTITY_SALT", "").strip()
    if analytics_enabled and (len(analytics_salt) < 32 or _is_placeholder(analytics_salt)):
        errors.append(
            "ANALYTICS_IDENTITY_SALT: a non-placeholder value of at least 32 characters is required."
        )
    return tuple(errors)


def _is_placeholder(value: str) -> bool:
    normalized = value.casefold()
    return "replace-with" in normalized or ".example" in normalized


def _origin(value: str) -> tuple[str, str | None, int | None]:
    parsed = urlparse(value)
    return parsed.scheme, parsed.hostname, parsed.port


def main() -> int:
    errors = validate_environment()
    if errors:
        print("Production environment check failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Production environment check passed. No secret values were printed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Fail-closed production environment diagnostic without printing values."""

import os
from urllib.parse import urlparse

from pydantic import ValidationError

from core.config import Settings

FRONTEND_REQUIRED = (
    "APP_BASE_URL",
    "SOLARAHIRE_SITE_URL",
    "AUTH0_DOMAIN",
    "AUTH0_CLIENT_ID",
    "AUTH0_CLIENT_SECRET",
    "AUTH0_SECRET",
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

    for name in (*FRONTEND_REQUIRED, *EXTERNAL_PROVIDER_REQUIRED):
        value = values.get(name, "").strip()
        if not value:
            errors.append(f"{name}: missing.")
        elif _is_placeholder(value):
            errors.append(f"{name}: placeholder value must be replaced.")

    for name in ("APP_BASE_URL", "SOLARAHIRE_SITE_URL"):
        value = values.get(name, "")
        if value and urlparse(value).scheme != "https":
            errors.append(f"{name}: HTTPS is required.")

    auth0_secret = values.get("AUTH0_SECRET", "")
    if auth0_secret and len(auth0_secret) < 32:
        errors.append("AUTH0_SECRET: must contain at least 32 characters.")
    return tuple(errors)


def _is_placeholder(value: str) -> bool:
    normalized = value.casefold()
    return "replace-with" in normalized or ".example" in normalized


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

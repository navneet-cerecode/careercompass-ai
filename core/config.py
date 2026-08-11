"""
File: config.py

Description:
Centralized application configuration using Pydantic Settings.

All environment variables and application constants
should be accessed through this file.

Author: Navneet Prakash Yadav
"""

from pathlib import Path

from pydantic import AliasChoices, Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from the .env file.
    """

    # ==========================
    # API Keys
    # ==========================

    groq_api_key: SecretStr | None = Field(
        default=None,
        alias="GROQ_API_KEY",
    )

    rapidapi_key: SecretStr | None = Field(
        default=None,
        alias="RAPIDAPI_KEY",
    )

    adzuna_app_id: SecretStr | None = Field(default=None, alias="ADZUNA_APP_ID")
    adzuna_app_key: SecretStr | None = Field(default=None, alias="ADZUNA_APP_KEY")
    the_muse_api_key: SecretStr | None = Field(default=None, alias="THE_MUSE_API_KEY")

    # ==========================
    # LLM Configuration
    # ==========================

    groq_model: str = Field(
        "llama-3.3-70b-versatile",
        alias="GROQ_MODEL",
    )

    temperature: float = Field(
        default=0.2,
        validation_alias=AliasChoices(
            "GROQ_TEMPERATURE",
            "TEMPERATURE",
        ),
    )

    max_tokens: int = Field(
        default=1024,
        validation_alias=AliasChoices(
            "GROQ_MAX_TOKENS",
            "MAX_TOKENS",
        ),
    )

    # ==========================
    # Application
    # ==========================

    app_name: str = "Solara Hire"

    version: str = "1.0.0"

    environment: str = Field(
        default="development",
        pattern=r"^(development|test|production)$",
        alias="APP_ENVIRONMENT",
    )
    allowed_hosts: str = Field(
        default="localhost,127.0.0.1,testserver",
        alias="ALLOWED_HOSTS",
    )

    # ==========================
    # Job Search
    # ==========================

    max_jobs: int = 50

    default_location: str = "India"

    max_resume_upload_bytes: int = Field(default=5 * 1024 * 1024, ge=1)

    # ==========================
    # Database
    # ==========================

    database_path: Path = Path("database/jobs.db")

    database_url: SecretStr | None = Field(
        default=None,
        validation_alias=AliasChoices("DATABASE_URL", "database_url"),
    )

    database_pool_size: int = Field(default=5, ge=1, le=50)

    database_pool_timeout_seconds: int = Field(default=10, ge=1, le=120)

    def require_database_url(self) -> str:
        if self.database_url is None:
            raise ValueError("DATABASE_URL is required for persistence.")
        return self.database_url.get_secret_value()

    # ==========================
    # Background Workers
    # ==========================

    redis_url: SecretStr | None = Field(
        default=None,
        validation_alias=AliasChoices("REDIS_URL", "redis_url"),
    )

    worker_broker_namespace: str = Field(
        default="careercompass",
        min_length=1,
        pattern=r"^[a-z0-9_-]+$",
    )

    worker_queue_name: str = Field(
        default="careercompass",
        min_length=1,
        pattern=r"^[a-z0-9_-]+$",
    )

    worker_max_retries: int = Field(default=3, ge=0, le=10)

    worker_time_limit_ms: int = Field(
        default=5 * 60 * 1000,
        ge=1_000,
        le=60 * 60 * 1000,
    )

    worker_message_max_age_ms: int = Field(
        default=60 * 60 * 1000,
        ge=1_000,
        le=24 * 60 * 60 * 1000,
    )

    def require_redis_url(self) -> str:
        if self.redis_url is None:
            raise ValueError("REDIS_URL is required for background workers.")
        return self.redis_url.get_secret_value()

    task_token_secret: SecretStr | None = Field(
        default=None,
        min_length=32,
        validation_alias=AliasChoices("TASK_TOKEN_SECRET", "task_token_secret"),
    )

    worker_heartbeat_seconds: int = Field(default=30, ge=5, le=300)

    task_stale_after_seconds: int = Field(default=10 * 60, ge=60, le=24 * 60 * 60)

    task_delivery_retry_seconds: int = Field(default=2 * 60, ge=30, le=60 * 60)

    task_queue_expiry_seconds: int = Field(
        default=30 * 60,
        ge=60,
        le=7 * 24 * 60 * 60,
    )

    task_retention_days: int = Field(default=30, ge=1, le=365)

    task_maintenance_batch_size: int = Field(default=100, ge=1, le=1_000)

    application_reminder_lead_hours: int = Field(default=24, ge=1, le=168)

    # ==========================
    # Authentication
    # ==========================

    auth_issuer: str | None = Field(default=None, min_length=8)
    auth_audience: str | None = Field(default=None, min_length=1)
    auth_jwks_url: str | None = Field(default=None, min_length=8)
    auth_jwks_cache_seconds: int = Field(default=300, ge=30, le=24 * 60 * 60)
    auth_http_timeout_seconds: int = Field(default=5, ge=1, le=30)

    def require_auth_config(self) -> tuple[str, str, str]:
        if not self.auth_issuer or not self.auth_audience or not self.auth_jwks_url:
            raise ValueError(
                "AUTH_ISSUER, AUTH_AUDIENCE, and AUTH_JWKS_URL are required for authentication."
            )
        return self.auth_issuer, self.auth_audience, self.auth_jwks_url

    def allowed_host_list(self) -> list[str]:
        return [host.strip() for host in self.allowed_hosts.split(",") if host.strip()]

    # ==========================
    # Logging
    # ==========================

    log_level: str = "INFO"

    analytics_enabled: bool = Field(default=False, alias="ANALYTICS_ENABLED")
    analytics_identity_salt: SecretStr | None = Field(
        default=None,
        min_length=32,
        alias="ANALYTICS_IDENTITY_SALT",
    )

    @model_validator(mode="after")
    def validate_production_configuration(self) -> "Settings":
        if self.environment != "production":
            return self

        missing: list[str] = []
        if self.database_url is None:
            missing.append("DATABASE_URL")
        if self.redis_url is None:
            missing.append("REDIS_URL")
        if self.task_token_secret is None:
            missing.append("TASK_TOKEN_SECRET")
        if not self.auth_issuer:
            missing.append("AUTH_ISSUER")
        if not self.auth_audience:
            missing.append("AUTH_AUDIENCE")
        if not self.auth_jwks_url:
            missing.append("AUTH_JWKS_URL")
        if missing:
            raise ValueError(
                "Production configuration is missing required values: " + ", ".join(missing)
            )

        if not self.auth_issuer.startswith("https://") or not self.auth_jwks_url.startswith(
            "https://"
        ):
            raise ValueError("Production identity endpoints must use HTTPS.")
        hosts = self.allowed_host_list()
        if not hosts or "*" in hosts:
            raise ValueError("Production ALLOWED_HOSTS must contain explicit hostnames.")
        return self

    # ==========================
    # Pydantic Config
    # ==========================

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()

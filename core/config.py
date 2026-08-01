"""
File: config.py

Description:
Centralized application configuration using Pydantic Settings.

All environment variables and application constants
should be accessed through this file.

Author: Navneet Prakash Yadav
"""

from pathlib import Path

from pydantic import AliasChoices, Field, SecretStr
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

    app_name: str = "CareerCompass AI"

    version: str = "1.0.0"

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

    # ==========================
    # Logging
    # ==========================

    log_level: str = "INFO"

    # ==========================
    # Pydantic Config
    # ==========================

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()

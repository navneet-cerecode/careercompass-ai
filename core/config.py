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

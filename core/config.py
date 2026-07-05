"""
File: config.py

Description:
Centralized application configuration using Pydantic Settings.

All environment variables and application constants
should be accessed through this file.

Author: Navneet Prakash Yadav
"""

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from the .env file.
    """

    # ==========================
    # API Keys
     # ==========================

    groq_api_key: str = Field(
    ...,
    alias="GROQ_API_KEY",
    )

# ==========================
# LLM Configuration
# ==========================

    groq_model: str = Field(
    "llama-3.3-70b-versatile",
    alias="GROQ_MODEL",
    )

    temperature: float = 0.2

    max_tokens: int = 1024

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
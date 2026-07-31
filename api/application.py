"""FastAPI application factory."""

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError

from api.errors import (
    APIError,
    api_error_handler,
    request_validation_error_handler,
)
from api.services.job_catalog import InMemoryJobCatalog
from api.v1.router import api_router
from core.config import Settings, settings


def create_app(app_settings: Settings | None = None) -> FastAPI:
    """Build an API instance without constructing external service clients."""
    active_settings = app_settings or settings
    application = FastAPI(
        title=active_settings.app_name,
        version=active_settings.version,
        description="Typed HTTP API for CareerCompass AI.",
    )
    application.state.settings = active_settings
    application.state.job_catalog = InMemoryJobCatalog(
        max_entries=max(active_settings.max_jobs * 10, 1)
    )
    application.add_exception_handler(APIError, api_error_handler)
    application.add_exception_handler(
        RequestValidationError,
        request_validation_error_handler,
    )
    application.include_router(api_router, prefix="/api/v1")
    return application

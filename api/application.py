"""FastAPI application factory."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from threading import Lock

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError

from api.errors import (
    APIError,
    api_error_handler,
    request_validation_error_handler,
)
from api.v1.router import api_router
from core.config import Settings, settings


@asynccontextmanager
async def application_lifespan(application: FastAPI) -> AsyncIterator[None]:
    yield
    database = application.state.database
    if database is not None:
        database.dispose()


def create_app(app_settings: Settings | None = None) -> FastAPI:
    """Build an API instance without constructing external service clients."""
    active_settings = app_settings or settings
    application = FastAPI(
        title=active_settings.app_name,
        version=active_settings.version,
        description="Typed HTTP API for CareerCompass AI.",
        lifespan=application_lifespan,
    )
    application.state.settings = active_settings
    application.state.database = None
    application.state.database_lock = Lock()
    application.add_exception_handler(APIError, api_error_handler)
    application.add_exception_handler(
        RequestValidationError,
        request_validation_error_handler,
    )
    application.include_router(api_router, prefix="/api/v1")
    return application

"""FastAPI application factory."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from threading import Lock
import secrets

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from starlette.middleware.trustedhost import TrustedHostMiddleware

from api.errors import (
    APIError,
    api_error_handler,
    request_validation_error_handler,
)
from api.v1.router import api_router
from core.config import Settings, settings
from core.observability import RequestTelemetryMiddleware, build_product_analytics


@asynccontextmanager
async def application_lifespan(application: FastAPI) -> AsyncIterator[None]:
    yield
    discovery = application.state.job_discovery_service
    if discovery is not None:
        discovery.close()
    database = application.state.database
    if database is not None:
        database.dispose()
    broker = application.state.task_broker
    if broker is not None:
        broker.close()


def create_app(app_settings: Settings | None = None) -> FastAPI:
    """Build an API instance without constructing external service clients."""
    active_settings = app_settings or settings
    application = FastAPI(
        title=active_settings.app_name,
        version=active_settings.version,
        description="Typed HTTP API for Solara Hire.",
        lifespan=application_lifespan,
    )
    application.state.settings = active_settings
    application.state.database = None
    application.state.database_lock = Lock()
    application.state.task_broker = None
    application.state.task_broker_lock = Lock()
    application.state.job_discovery_service = None
    configured_secret = (
        active_settings.task_token_secret.get_secret_value().encode()
        if active_settings.task_token_secret is not None
        else secrets.token_bytes(32)
    )
    application.state.task_token_secret = configured_secret
    application.state.oidc_verifier = None
    application.state.oidc_verifier_lock = Lock()
    analytics_salt = (
        active_settings.analytics_identity_salt.get_secret_value().encode()
        if active_settings.analytics_identity_salt is not None
        else None
    )
    application.state.product_analytics = build_product_analytics(
        enabled=active_settings.analytics_enabled,
        identity_salt=analytics_salt,
    )
    application.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=active_settings.allowed_host_list(),
    )
    application.add_middleware(RequestTelemetryMiddleware)
    application.add_exception_handler(APIError, api_error_handler)
    application.add_exception_handler(
        RequestValidationError,
        request_validation_error_handler,
    )
    application.include_router(api_router, prefix="/api/v1")
    return application

"""Shared FastAPI dependencies."""

from typing import Annotated

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from api.errors import APIError
from api.services.job_catalog import JobCatalog
from api.services.job_discovery_tasks import JobDiscoveryTaskService
from api.services.task_capability import TaskCapability
from core.config import Settings
from database.session import Database
from database.repositories.identities import IdentityLinkRequired, IdentityRepository
from database.repositories.users import UserRepository
from models.identity import AuthenticatedPrincipal
from services.auth.oidc import OIDCTokenVerifier, TokenValidationError
from services.job_discovery.discovery_service import JobDiscoveryService
from services.recommendation.recommendation_service import RecommendationService
from services.resume.extractor import ResumeExtractor
from services.resume.parser_service import ResumeParserService
from workers.broker import build_broker
from workers.publisher import BackgroundTaskPublisher

bearer_scheme = HTTPBearer(auto_error=False)


def get_settings(request: Request) -> Settings:
    """Return the settings instance owned by the current application."""
    return request.app.state.settings


def get_resume_parser() -> ResumeParserService:
    return ResumeParserService()


def get_resume_extractor() -> ResumeExtractor:
    return ResumeExtractor()


def get_database(request: Request) -> Database:
    database = request.app.state.database
    if database is None:
        with request.app.state.database_lock:
            database = request.app.state.database
            if database is None:
                settings = get_settings(request)
                try:
                    database_url = settings.require_database_url()
                except ValueError as error:
                    raise APIError(
                        503,
                        "database_not_configured",
                        "Database persistence is not configured.",
                    ) from error

                database = Database(
                    database_url,
                    pool_size=settings.database_pool_size,
                    pool_timeout_seconds=settings.database_pool_timeout_seconds,
                )
                request.app.state.database = database
    return database


def get_job_catalog(database: Annotated[Database, Depends(get_database)]) -> JobCatalog:
    return JobCatalog(database)


def get_job_discovery_service(request: Request) -> JobDiscoveryService:
    service = getattr(request.app.state, "job_discovery_service", None)
    if service is None:
        service = JobDiscoveryService()
        request.app.state.job_discovery_service = service
    return service


def get_job_discovery_task_service(
    request: Request,
    database: Annotated[Database, Depends(get_database)],
) -> JobDiscoveryTaskService:
    broker = request.app.state.task_broker
    if broker is None:
        with request.app.state.task_broker_lock:
            broker = request.app.state.task_broker
            if broker is None:
                try:
                    broker = build_broker(get_settings(request))
                except ValueError as error:
                    raise APIError(
                        503,
                        "worker_not_configured",
                        "Asynchronous job discovery is not configured.",
                    ) from error
                request.app.state.task_broker = broker
    settings = get_settings(request)
    return JobDiscoveryTaskService(
        database=database,
        publisher=BackgroundTaskPublisher(
            broker,
            queue_name=settings.worker_queue_name,
        ),
        capability=TaskCapability(request.app.state.task_token_secret),
        max_attempts=settings.worker_max_retries + 1,
    )


def get_recommendation_service(request: Request) -> RecommendationService:
    service = getattr(request.app.state, "recommendation_service", None)
    if service is None:
        service = RecommendationService()
        request.app.state.recommendation_service = service
    return service


def get_oidc_verifier(request: Request) -> OIDCTokenVerifier:
    verifier = request.app.state.oidc_verifier
    if verifier is None:
        with request.app.state.oidc_verifier_lock:
            verifier = request.app.state.oidc_verifier
            if verifier is None:
                settings = get_settings(request)
                try:
                    issuer, audience, jwks_url = settings.require_auth_config()
                except ValueError as error:
                    raise APIError(
                        503,
                        "authentication_not_configured",
                        "Authentication is not configured.",
                    ) from error
                verifier = OIDCTokenVerifier(
                    issuer=issuer,
                    audience=audience,
                    jwks_url=jwks_url,
                    jwks_cache_seconds=settings.auth_jwks_cache_seconds,
                    http_timeout_seconds=settings.auth_http_timeout_seconds,
                )
                request.app.state.oidc_verifier = verifier
    return verifier


def get_optional_principal(
    request: Request,
) -> AuthenticatedPrincipal | None:
    authorization = request.headers.get("authorization")
    if authorization is None:
        return None
    scheme, separator, token = authorization.partition(" ")
    if separator != " " or scheme.casefold() != "bearer" or not token or len(token) > 8_192:
        raise APIError(
            401,
            "invalid_access_token",
            "The access token is invalid.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return _resolve_principal(request, token)


def _resolve_principal(
    request: Request,
    token: str,
) -> AuthenticatedPrincipal:
    try:
        identity = get_oidc_verifier(request).verify(token)
    except TokenValidationError as error:
        raise APIError(
            401,
            "invalid_access_token",
            "The access token is invalid.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from error

    database = get_database(request)
    try:
        with database.session() as session:
            principal = IdentityRepository(session).provision(identity)
            user = UserRepository(session).get(principal.user_id)
            if user is None or not user.is_active:
                raise APIError(403, "account_inactive", "This account is not active.")
            return principal
    except IdentityLinkRequired as error:
        raise APIError(
            409,
            "identity_link_required",
            "This verified identity requires an explicit account-linking review.",
        ) from error


def get_required_principal(
    request: Request,
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(bearer_scheme),
    ],
) -> AuthenticatedPrincipal:
    if credentials is None:
        raise APIError(
            401,
            "authentication_required",
            "Authentication is required.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if credentials.scheme.casefold() != "bearer" or len(credentials.credentials) > 8_192:
        raise APIError(
            401,
            "invalid_access_token",
            "The access token is invalid.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return _resolve_principal(request, credentials.credentials)

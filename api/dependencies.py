"""Shared FastAPI dependencies."""

from typing import Annotated

from fastapi import Depends, Request

from api.errors import APIError
from api.services.job_catalog import JobCatalog
from api.services.job_discovery_tasks import JobDiscoveryTaskService
from api.services.task_capability import TaskCapability
from core.config import Settings
from database.session import Database
from services.job_discovery.discovery_service import JobDiscoveryService
from services.recommendation.recommendation_service import RecommendationService
from services.resume.extractor import ResumeExtractor
from services.resume.parser_service import ResumeParserService
from workers.broker import build_broker
from workers.publisher import BackgroundTaskPublisher


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

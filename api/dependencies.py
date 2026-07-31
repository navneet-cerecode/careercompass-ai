"""Shared FastAPI dependencies."""

from fastapi import Request

from api.services.job_catalog import InMemoryJobCatalog
from core.config import Settings
from services.job_discovery.discovery_service import JobDiscoveryService
from services.recommendation.recommendation_service import RecommendationService
from services.resume.extractor import ResumeExtractor
from services.resume.parser_service import ResumeParserService


def get_settings(request: Request) -> Settings:
    """Return the settings instance owned by the current application."""
    return request.app.state.settings


def get_resume_parser() -> ResumeParserService:
    return ResumeParserService()


def get_resume_extractor() -> ResumeExtractor:
    return ResumeExtractor()


def get_job_catalog(request: Request) -> InMemoryJobCatalog:
    return request.app.state.job_catalog


def get_job_discovery_service(request: Request) -> JobDiscoveryService:
    service = getattr(request.app.state, "job_discovery_service", None)
    if service is None:
        service = JobDiscoveryService()
        request.app.state.job_discovery_service = service
    return service


def get_recommendation_service(request: Request) -> RecommendationService:
    service = getattr(request.app.state, "recommendation_service", None)
    if service is None:
        service = RecommendationService()
        request.app.state.recommendation_service = service
    return service

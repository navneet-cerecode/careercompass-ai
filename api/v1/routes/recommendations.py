"""Job recommendation endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends
from starlette.concurrency import run_in_threadpool

from api.dependencies import get_job_catalog, get_recommendation_service
from api.errors import APIError, ErrorResponse
from api.mappers import map_recommendation, map_resume_input
from api.schemas.recommendations import (
    RecommendationBatchResponse,
    RecommendationRequest,
)
from api.services.job_catalog import JobCatalog
from services.recommendation.recommendation_service import RecommendationService

router = APIRouter()
RecommendationDependency = Annotated[
    RecommendationService,
    Depends(get_recommendation_service),
]
CatalogDependency = Annotated[JobCatalog, Depends(get_job_catalog)]


@router.post(
    "",
    response_model=RecommendationBatchResponse,
    responses={
        404: {"model": ErrorResponse},
        503: {"model": ErrorResponse},
    },
    summary="Rank discovered jobs against a reviewed resume",
)
async def recommend_jobs(
    request: RecommendationRequest,
    service: RecommendationDependency,
    catalog: CatalogDependency,
) -> RecommendationBatchResponse:
    jobs = await run_in_threadpool(catalog.get_many, request.job_ids)
    if jobs is None:
        raise APIError(
            404,
            "jobs_not_found",
            "One or more requested jobs were not found.",
        )

    resume = map_resume_input(request.resume)

    try:
        recommendations = await run_in_threadpool(
            service.recommend_jobs,
            resume,
            list(jobs),
        )
    except Exception as error:
        raise APIError(
            503,
            "recommendation_unavailable",
            "Job recommendations are temporarily unavailable.",
        ) from error

    return RecommendationBatchResponse(
        recommendations=tuple(
            map_recommendation(recommendation) for recommendation in recommendations
        )
    )

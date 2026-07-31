"""Job discovery and detail endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from starlette.concurrency import run_in_threadpool

from api.dependencies import get_job_catalog, get_job_discovery_service
from api.errors import APIError, ErrorResponse
from api.mappers import map_job
from api.schemas.job_search import (
    JobSearchRequest,
    JobSearchResponse,
    JobSearchStatus,
    ProviderFailureResponse,
)
from api.schemas.jobs import JobResponse
from api.services.job_catalog import JobCatalog
from services.job_discovery.discovery_service import JobDiscoveryService
from services.job_discovery.providers.contracts import JobSearchQuery

router = APIRouter()
DiscoveryDependency = Annotated[
    JobDiscoveryService,
    Depends(get_job_discovery_service),
]
CatalogDependency = Annotated[JobCatalog, Depends(get_job_catalog)]


@router.post(
    "/search",
    response_model=JobSearchResponse,
    summary="Search configured job providers",
)
async def search_jobs(
    request: JobSearchRequest,
    discovery: DiscoveryDependency,
    catalog: CatalogDependency,
) -> JobSearchResponse:
    query = JobSearchQuery(
        role=request.role,
        location=request.location,
        country=request.country,
        page=request.page,
        page_size=request.page_size,
        remote_only=request.remote_only,
        employment_types=list(request.employment_types),
        date_posted=request.date_posted,
    )
    result = await run_in_threadpool(discovery.discover_jobs_with_status, query)
    persisted_jobs = await run_in_threadpool(catalog.add_many, result.jobs)

    if result.failures and result.providers_succeeded:
        status = JobSearchStatus.PARTIAL
    elif result.failures:
        status = JobSearchStatus.FAILED
    else:
        status = JobSearchStatus.COMPLETE

    return JobSearchResponse(
        status=status,
        jobs=tuple(map_job(job) for job in persisted_jobs),
        provider_failures=tuple(
            ProviderFailureResponse(provider_name=failure.provider_name)
            for failure in result.failures
        ),
        providers_attempted=result.providers_attempted,
        providers_succeeded=result.providers_succeeded,
    )


@router.get(
    "/{job_id}",
    response_model=JobResponse,
    responses={404: {"model": ErrorResponse}},
    summary="Get a job returned by this API process",
)
def get_job(job_id: UUID, catalog: CatalogDependency) -> JobResponse:
    job = catalog.get(job_id)
    if job is None:
        raise APIError(404, "job_not_found", "The requested job was not found.")
    return map_job(job)

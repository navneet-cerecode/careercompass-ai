"""Job discovery and detail endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Header
from starlette.concurrency import run_in_threadpool

from api.dependencies import (
    get_job_catalog,
    get_job_discovery_service,
    get_job_discovery_task_service,
    get_optional_principal,
)
from api.errors import APIError, ErrorResponse
from api.mappers import map_job
from api.schemas.job_search import (
    JobSearchRequest,
    JobSearchResponse,
    JobSearchStatus,
    JobSearchTaskCreatedResponse,
    JobSearchTaskResponse,
    ProviderFailureResponse,
)
from api.schemas.jobs import JobResponse
from api.services.job_catalog import JobCatalog
from api.services.job_discovery_tasks import JobDiscoveryTaskService
from database.repositories.tasks import IdempotencyConflict
from models.identity import AuthenticatedPrincipal
from services.job_discovery.discovery_service import JobDiscoveryService
from services.job_discovery.providers.contracts import JobSearchQuery

router = APIRouter()
DiscoveryDependency = Annotated[
    JobDiscoveryService,
    Depends(get_job_discovery_service),
]
CatalogDependency = Annotated[JobCatalog, Depends(get_job_catalog)]
TaskServiceDependency = Annotated[
    JobDiscoveryTaskService,
    Depends(get_job_discovery_task_service),
]
OptionalPrincipalDependency = Annotated[
    AuthenticatedPrincipal | None,
    Depends(get_optional_principal),
]


def _map_search_result(snapshot) -> JobSearchResponse | None:
    if snapshot.outcome is None:
        return None
    return JobSearchResponse(
        status=JobSearchStatus(snapshot.outcome.status.value),
        jobs=tuple(map_job(job) for job in snapshot.jobs),
        provider_failures=tuple(
            ProviderFailureResponse(provider_name=name)
            for name in snapshot.outcome.provider_names_failed
        ),
        providers_attempted=snapshot.outcome.providers_attempted,
        providers_succeeded=snapshot.outcome.providers_succeeded,
    )


def _map_task_snapshot(snapshot) -> JobSearchTaskResponse:
    return JobSearchTaskResponse(
        task_id=snapshot.task.id,
        status=snapshot.task.status,
        attempt_count=snapshot.task.attempt_count,
        max_attempts=snapshot.task.max_attempts,
        error_code=snapshot.task.error_code,
        cancellation_requested=snapshot.task.cancel_requested_at is not None,
        created_at=snapshot.task.created_at,
        updated_at=snapshot.task.updated_at,
        result=_map_search_result(snapshot),
    )


@router.post(
    "/search-tasks",
    response_model=JobSearchTaskCreatedResponse,
    status_code=202,
    responses={409: {"model": ErrorResponse}, 503: {"model": ErrorResponse}},
    openapi_extra={"security": [{}, {"HTTPBearer": []}]},
    summary="Create an asynchronous job-discovery task",
)
def create_search_task(
    request: JobSearchRequest,
    tasks: TaskServiceDependency,
    principal: OptionalPrincipalDependency,
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key", min_length=8, max_length=200)],
) -> JobSearchTaskCreatedResponse:
    try:
        snapshot, token = tasks.create(
            request=request,
            idempotency_key=idempotency_key,
            user_id=principal.user_id if principal is not None else None,
        )
    except IdempotencyConflict as error:
        raise APIError(
            409,
            "idempotency_conflict",
            "This idempotency key was already used for another search.",
        ) from error
    return JobSearchTaskCreatedResponse(
        task_id=snapshot.task.id,
        access_token=token,
        status=snapshot.task.status,
    )


@router.get(
    "/search-tasks/{task_id}",
    response_model=JobSearchTaskResponse,
    responses={404: {"model": ErrorResponse}},
    openapi_extra={"security": [{}, {"HTTPBearer": []}]},
    summary="Poll an asynchronous job-discovery task",
)
def get_search_task(
    task_id: UUID,
    tasks: TaskServiceDependency,
    principal: OptionalPrincipalDependency,
    task_token: Annotated[str, Header(alias="X-Task-Token", min_length=20, max_length=200)],
) -> JobSearchTaskResponse:
    snapshot = tasks.get(
        task_id=task_id,
        token=task_token,
        user_id=principal.user_id if principal is not None else None,
    )
    if snapshot is None:
        raise APIError(404, "task_not_found", "The requested task was not found.")
    return _map_task_snapshot(snapshot)


@router.delete(
    "/search-tasks/{task_id}",
    response_model=JobSearchTaskResponse,
    responses={404: {"model": ErrorResponse}, 409: {"model": ErrorResponse}},
    openapi_extra={"security": [{}, {"HTTPBearer": []}]},
    summary="Request cancellation of an asynchronous job search",
)
def cancel_search_task(
    task_id: UUID,
    tasks: TaskServiceDependency,
    principal: OptionalPrincipalDependency,
    task_token: Annotated[str, Header(alias="X-Task-Token", min_length=20, max_length=200)],
) -> JobSearchTaskResponse:
    snapshot = tasks.cancel(
        task_id=task_id,
        token=task_token,
        user_id=principal.user_id if principal is not None else None,
    )
    if snapshot is None:
        raise APIError(404, "task_not_found", "The requested task was not found.")
    return _map_task_snapshot(snapshot)


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

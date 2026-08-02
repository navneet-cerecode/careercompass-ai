"""Authenticated saved-job endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Response

from api.dependencies import get_required_principal, get_saved_job_service
from api.errors import APIError, ErrorResponse
from api.mappers import map_job
from api.schemas.saved_jobs import (
    SaveJobRequest,
    SavedJobListResponse,
    SavedJobResponse,
)
from api.services.saved_jobs import SavedJobService, SavedJobSnapshot
from models.identity import AuthenticatedPrincipal

router = APIRouter()
PrincipalDependency = Annotated[
    AuthenticatedPrincipal,
    Depends(get_required_principal),
]
SavedJobServiceDependency = Annotated[
    SavedJobService,
    Depends(get_saved_job_service),
]


def _map_saved_job(snapshot: SavedJobSnapshot) -> SavedJobResponse:
    return SavedJobResponse(
        job=map_job(snapshot.job),
        notes=snapshot.saved_job.notes,
        created_at=snapshot.saved_job.created_at,
        updated_at=snapshot.saved_job.updated_at,
    )


@router.get(
    "",
    response_model=SavedJobListResponse,
    responses={401: {"model": ErrorResponse}},
    summary="List the current account's saved jobs",
)
def list_saved_jobs(
    principal: PrincipalDependency,
    saved_jobs: SavedJobServiceDependency,
) -> SavedJobListResponse:
    return SavedJobListResponse(
        items=tuple(
            _map_saved_job(snapshot) for snapshot in saved_jobs.list(user_id=principal.user_id)
        )
    )


@router.put(
    "/{job_id}",
    response_model=SavedJobResponse,
    responses={
        401: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
    },
    summary="Save or update a job for the current account",
)
def save_job(
    job_id: UUID,
    request: SaveJobRequest,
    principal: PrincipalDependency,
    saved_jobs: SavedJobServiceDependency,
) -> SavedJobResponse:
    snapshot = saved_jobs.save(
        user_id=principal.user_id,
        job_id=job_id,
        notes=request.notes,
    )
    if snapshot is None:
        raise APIError(404, "job_not_found", "The requested job was not found.")
    return _map_saved_job(snapshot)


@router.delete(
    "/{job_id}",
    status_code=204,
    responses={
        401: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
    },
    summary="Remove a saved job from the current account",
)
def remove_saved_job(
    job_id: UUID,
    principal: PrincipalDependency,
    saved_jobs: SavedJobServiceDependency,
) -> Response:
    removed = saved_jobs.remove(user_id=principal.user_id, job_id=job_id)
    if not removed:
        raise APIError(
            404,
            "saved_job_not_found",
            "The requested saved job was not found.",
        )
    return Response(status_code=204)

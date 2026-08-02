"""Authenticated assisted-application tracking endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status

from api.dependencies import (
    get_application_tracking_service,
    get_required_principal,
)
from api.errors import APIError, ErrorResponse
from api.mappers import map_job
from api.schemas.applications import (
    ApplicationDetailResponse,
    ApplicationEventResponse,
    ApplicationListResponse,
    ApplicationResponse,
    CreateApplicationRequest,
    TransitionApplicationRequest,
    UpdateApplicationPlanRequest,
)
from api.services.applications import ApplicationSnapshot, ApplicationTrackingService
from database.repositories.applications import (
    ApplicationAlreadyTracked,
    InvalidApplicationTransition,
    InvalidResumeSelection,
)
from database.repositories.applications import ALLOWED_TRANSITIONS
from models.application import ApplicationEvent
from models.enums import ApplicationStatus
from models.identity import AuthenticatedPrincipal

router = APIRouter()
PrincipalDependency = Annotated[
    AuthenticatedPrincipal,
    Depends(get_required_principal),
]
ApplicationServiceDependency = Annotated[
    ApplicationTrackingService,
    Depends(get_application_tracking_service),
]


def _allowed_next_statuses(
    current_status: ApplicationStatus,
) -> tuple[ApplicationStatus, ...]:
    allowed = ALLOWED_TRANSITIONS[current_status]
    return tuple(status for status in ApplicationStatus if status in allowed)


def _map_event(event: ApplicationEvent) -> ApplicationEventResponse:
    return ApplicationEventResponse(
        id=event.id,
        previous_status=event.previous_status,
        new_status=event.new_status,
        note=event.note,
        occurred_at=event.occurred_at,
    )


def _map_application(snapshot: ApplicationSnapshot) -> ApplicationResponse:
    application = snapshot.application
    return ApplicationResponse(
        id=application.id,
        job=map_job(snapshot.job),
        status=application.status,
        allowed_next_statuses=_allowed_next_statuses(application.status),
        resume_id=application.resume_id,
        applied_at=application.applied_at,
        notes=application.notes,
        next_action=application.next_action,
        next_action_due_at=application.next_action_due_at,
        created_at=application.created_at,
        updated_at=application.updated_at,
    )


def _map_application_detail(
    snapshot: ApplicationSnapshot,
) -> ApplicationDetailResponse:
    response = _map_application(snapshot)
    return ApplicationDetailResponse(
        **response.model_dump(),
        events=tuple(_map_event(event) for event in snapshot.events),
    )


@router.get(
    "",
    response_model=ApplicationListResponse,
    responses={401: {"model": ErrorResponse}},
    summary="List the current account's application trackers",
)
def list_applications(
    principal: PrincipalDependency,
    applications: ApplicationServiceDependency,
) -> ApplicationListResponse:
    return ApplicationListResponse(
        items=tuple(
            _map_application(snapshot) for snapshot in applications.list(user_id=principal.user_id)
        )
    )


@router.post(
    "",
    response_model=ApplicationDetailResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        401: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
        409: {"model": ErrorResponse},
    },
    summary="Start tracking a job application",
)
def create_application(
    request: CreateApplicationRequest,
    principal: PrincipalDependency,
    applications: ApplicationServiceDependency,
) -> ApplicationDetailResponse:
    try:
        snapshot = applications.create(
            user_id=principal.user_id,
            job_id=request.job_id,
            resume_id=request.resume_id,
            notes=request.notes,
            next_action=request.next_action,
            next_action_due_at=request.next_action_due_at,
        )
    except InvalidResumeSelection as error:
        raise APIError(
            404,
            "resume_not_found",
            "The selected resume was not found.",
        ) from error
    except ApplicationAlreadyTracked as error:
        raise APIError(
            409,
            "application_already_exists",
            "This job is already in your application tracker.",
        ) from error
    if snapshot is None:
        raise APIError(404, "job_not_found", "The requested job was not found.")
    return _map_application_detail(snapshot)


@router.get(
    "/{application_id}",
    response_model=ApplicationDetailResponse,
    responses={
        401: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
    },
    summary="Get an application tracker and its status history",
)
def get_application(
    application_id: UUID,
    principal: PrincipalDependency,
    applications: ApplicationServiceDependency,
) -> ApplicationDetailResponse:
    snapshot = applications.get(
        user_id=principal.user_id,
        application_id=application_id,
    )
    if snapshot is None:
        raise APIError(
            404,
            "application_not_found",
            "The requested application was not found.",
        )
    return _map_application_detail(snapshot)


@router.patch(
    "/{application_id}",
    response_model=ApplicationDetailResponse,
    responses={
        401: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
    },
    summary="Update application planning details",
)
def update_application_plan(
    application_id: UUID,
    request: UpdateApplicationPlanRequest,
    principal: PrincipalDependency,
    applications: ApplicationServiceDependency,
) -> ApplicationDetailResponse:
    snapshot = applications.update_plan(
        user_id=principal.user_id,
        application_id=application_id,
        notes=request.notes,
        next_action=request.next_action,
        next_action_due_at=request.next_action_due_at,
    )
    if snapshot is None:
        raise APIError(
            404,
            "application_not_found",
            "The requested application was not found.",
        )
    return _map_application_detail(snapshot)


@router.patch(
    "/{application_id}/status",
    response_model=ApplicationDetailResponse,
    responses={
        401: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
        409: {"model": ErrorResponse},
    },
    summary="Move an application to an allowed next status",
)
def transition_application(
    application_id: UUID,
    request: TransitionApplicationRequest,
    principal: PrincipalDependency,
    applications: ApplicationServiceDependency,
) -> ApplicationDetailResponse:
    try:
        snapshot = applications.transition(
            user_id=principal.user_id,
            application_id=application_id,
            new_status=request.status,
            note=request.note,
            next_action=request.next_action,
            next_action_due_at=request.next_action_due_at,
        )
    except InvalidApplicationTransition as error:
        raise APIError(
            409,
            "invalid_application_transition",
            str(error),
        ) from error
    if snapshot is None:
        raise APIError(
            404,
            "application_not_found",
            "The requested application was not found.",
        )
    return _map_application_detail(snapshot)

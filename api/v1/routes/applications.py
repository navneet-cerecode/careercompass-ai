"""Authenticated assisted-application tracking endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status

from api.dependencies import (
    get_application_packet_service,
    get_application_tracking_service,
    get_product_analytics,
    get_required_principal,
)
from api.errors import APIError, ErrorResponse
from api.mappers import map_job
from api.schemas.applications import (
    ApplicationDocumentOptionResponse,
    ApplicationDetailResponse,
    ApplicationEventResponse,
    ApplicationListResponse,
    ApplicationResponse,
    ApplicationPacketResponse,
    ConfirmExternalSubmissionRequest,
    CreateApplicationRequest,
    TransitionApplicationRequest,
    UpdateApplicationPacketRequest,
    UpdateApplicationPlanRequest,
)
from api.services.application_packets import (
    ApplicationPacketIncomplete,
    ApplicationPacketInvalidDocument,
    ApplicationPacketInvalidStatus,
    ApplicationPacketNotFound,
    ApplicationPacketService,
    ApplicationPacketSnapshot,
)
from api.services.applications import (
    ApplicationPacketRequired,
    ApplicationSnapshot,
    ApplicationTrackingService,
)
from core.observability import ProductAnalytics, ProductEventName
from database.repositories.application_packets import ApplicationPacketLocked
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
ApplicationPacketServiceDependency = Annotated[
    ApplicationPacketService,
    Depends(get_application_packet_service),
]
AnalyticsDependency = Annotated[ProductAnalytics, Depends(get_product_analytics)]


def _allowed_next_statuses(
    current_status: ApplicationStatus,
) -> tuple[ApplicationStatus, ...]:
    allowed = ALLOWED_TRANSITIONS[current_status] - {
        ApplicationStatus.READY_TO_APPLY,
        ApplicationStatus.APPLIED,
    }
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
        packet_ready=snapshot.packet_ready,
        resume_id=application.resume_id,
        applied_at=application.applied_at,
        notes=application.notes,
        next_action=application.next_action,
        next_action_due_at=application.next_action_due_at,
        created_at=application.created_at,
        updated_at=application.updated_at,
    )


def _map_packet(snapshot: ApplicationPacketSnapshot) -> ApplicationPacketResponse:
    packet = snapshot.packet
    return ApplicationPacketResponse(
        id=packet.id,
        application_id=packet.application_id,
        source_resume_id=packet.source_resume_id,
        tailored_resume_id=packet.tailored_resume_id,
        cover_letter_id=packet.cover_letter_id,
        job_details_reviewed=packet.job_details_reviewed,
        resume_reviewed=packet.resume_reviewed,
        cover_letter_reviewed=packet.cover_letter_reviewed,
        employer_questions_reviewed=packet.employer_questions_reviewed,
        ready_at=packet.ready_at,
        application_status=snapshot.application.status,
        blockers=snapshot.blockers,
        can_mark_ready=(
            packet.ready_at is None
            and not snapshot.blockers
            and snapshot.application.status == ApplicationStatus.PREPARING
        ),
        can_confirm_submitted=(
            packet.ready_at is not None
            and snapshot.application.status == ApplicationStatus.READY_TO_APPLY
        ),
        available_tailored_resumes=tuple(
            ApplicationDocumentOptionResponse(**option.__dict__)
            for option in snapshot.tailored_resumes
        ),
        available_cover_letters=tuple(
            ApplicationDocumentOptionResponse(**option.__dict__)
            for option in snapshot.cover_letters
        ),
        created_at=packet.created_at,
        updated_at=packet.updated_at,
    )


def _raise_packet_error(error: Exception) -> None:
    if isinstance(error, ApplicationPacketNotFound):
        raise APIError(
            404,
            "application_packet_not_found",
            "The application packet was not found.",
        ) from error
    if isinstance(error, ApplicationPacketInvalidDocument):
        raise APIError(
            409,
            "invalid_application_document",
            "Select a verified document created for this job and resume.",
        ) from error
    if isinstance(error, ApplicationPacketIncomplete):
        raise APIError(
            409,
            "application_packet_incomplete",
            "Complete every required review before continuing: "
            + ", ".join(error.blockers),
        ) from error
    if isinstance(error, ApplicationPacketLocked):
        raise APIError(
            409,
            "application_packet_locked",
            "This reviewed packet is locked. Start a new revision to make changes.",
        ) from error
    if isinstance(error, ApplicationPacketInvalidStatus):
        raise APIError(
            409,
            "invalid_application_packet_status",
            "This action is not available at the application's current status.",
        ) from error
    raise error


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
    analytics: AnalyticsDependency,
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
    analytics.track(
        ProductEventName.APPLICATION_TRACKING_STARTED,
        user_id=principal.user_id,
        properties={
            "has_resume": request.resume_id is not None,
            "has_next_action": bool(request.next_action and request.next_action.strip()),
        },
    )
    return _map_application_detail(snapshot)


@router.post(
    "/{application_id}/packet",
    response_model=ApplicationPacketResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        401: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
    },
    summary="Create or load a review-first application packet",
)
def create_application_packet(
    application_id: UUID,
    principal: PrincipalDependency,
    packets: ApplicationPacketServiceDependency,
) -> ApplicationPacketResponse:
    try:
        return _map_packet(
            packets.create(
                user_id=principal.user_id,
                application_id=application_id,
            )
        )
    except ApplicationPacketNotFound as error:
        _raise_packet_error(error)
        raise AssertionError("unreachable") from error


@router.get(
    "/{application_id}/packet",
    response_model=ApplicationPacketResponse,
    responses={
        401: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
    },
    summary="Get an application packet",
)
def get_application_packet(
    application_id: UUID,
    principal: PrincipalDependency,
    packets: ApplicationPacketServiceDependency,
) -> ApplicationPacketResponse:
    try:
        return _map_packet(
            packets.get(
                user_id=principal.user_id,
                application_id=application_id,
            )
        )
    except ApplicationPacketNotFound as error:
        _raise_packet_error(error)
        raise AssertionError("unreachable") from error


@router.patch(
    "/{application_id}/packet",
    response_model=ApplicationPacketResponse,
    responses={
        401: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
        409: {"model": ErrorResponse},
    },
    summary="Save reviewed application packet choices",
)
def update_application_packet(
    application_id: UUID,
    request: UpdateApplicationPacketRequest,
    principal: PrincipalDependency,
    packets: ApplicationPacketServiceDependency,
) -> ApplicationPacketResponse:
    try:
        return _map_packet(
            packets.update(
                user_id=principal.user_id,
                application_id=application_id,
                tailored_resume_id=request.tailored_resume_id,
                cover_letter_id=request.cover_letter_id,
                job_details_reviewed=request.job_details_reviewed,
                resume_reviewed=request.resume_reviewed,
                cover_letter_reviewed=request.cover_letter_reviewed,
                employer_questions_reviewed=request.employer_questions_reviewed,
            )
        )
    except (
        ApplicationPacketInvalidDocument,
        ApplicationPacketLocked,
        ApplicationPacketNotFound,
    ) as error:
        _raise_packet_error(error)
        raise AssertionError("unreachable") from error


@router.post(
    "/{application_id}/packet/ready",
    response_model=ApplicationPacketResponse,
    responses={
        401: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
        409: {"model": ErrorResponse},
    },
    summary="Lock a reviewed packet and mark the application ready",
)
def mark_application_packet_ready(
    application_id: UUID,
    principal: PrincipalDependency,
    packets: ApplicationPacketServiceDependency,
) -> ApplicationPacketResponse:
    try:
        return _map_packet(
            packets.mark_ready(
                user_id=principal.user_id,
                application_id=application_id,
            )
        )
    except (
        ApplicationPacketIncomplete,
        ApplicationPacketInvalidStatus,
        ApplicationPacketNotFound,
    ) as error:
        _raise_packet_error(error)
        raise AssertionError("unreachable") from error


@router.post(
    "/{application_id}/packet/submitted",
    response_model=ApplicationPacketResponse,
    responses={
        401: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
        409: {"model": ErrorResponse},
    },
    summary="Record the user's confirmation of an external submission",
)
def confirm_external_submission(
    application_id: UUID,
    request: ConfirmExternalSubmissionRequest,
    principal: PrincipalDependency,
    packets: ApplicationPacketServiceDependency,
) -> ApplicationPacketResponse:
    del request
    try:
        return _map_packet(
            packets.confirm_submitted(
                user_id=principal.user_id,
                application_id=application_id,
            )
        )
    except (
        ApplicationPacketIncomplete,
        ApplicationPacketInvalidStatus,
        ApplicationPacketNotFound,
    ) as error:
        _raise_packet_error(error)
        raise AssertionError("unreachable") from error


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
    analytics: AnalyticsDependency,
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
    except ApplicationPacketRequired as error:
        raise APIError(
            409,
            "application_packet_required",
            str(error),
        ) from error
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
    analytics.track(
        ProductEventName.APPLICATION_STATUS_CHANGED,
        user_id=principal.user_id,
        properties={"to_status": request.status.value},
    )
    return _map_application_detail(snapshot)

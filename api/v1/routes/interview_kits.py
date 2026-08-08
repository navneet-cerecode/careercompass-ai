"""Authenticated interview preparation endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status

from api.dependencies import get_interview_kit_service, get_required_principal
from api.errors import APIError, ErrorResponse
from api.mappers import map_job
from api.schemas.interview_kits import (
    InterviewKitResponse,
    InterviewQuestionResponse,
    UpdateInterviewKitRequest,
)
from api.services.interview_kits import (
    InterviewKitInvalidResponse,
    InterviewKitInvalidStatus,
    InterviewKitNotFound,
    InterviewKitResumeRequired,
    InterviewKitService,
    InterviewKitSnapshot,
)
from models.identity import AuthenticatedPrincipal

router = APIRouter()
PrincipalDependency = Annotated[AuthenticatedPrincipal, Depends(get_required_principal)]
ServiceDependency = Annotated[InterviewKitService, Depends(get_interview_kit_service)]


def _map(snapshot: InterviewKitSnapshot) -> InterviewKitResponse:
    kit = snapshot.kit
    return InterviewKitResponse(
        id=kit.id,
        application_id=kit.application_id,
        resume_id=kit.resume_id,
        application_status=snapshot.application.status,
        job=map_job(snapshot.job),
        questions=tuple(
            InterviewQuestionResponse(**question.model_dump()) for question in kit.questions
        ),
        responses=kit.responses,
        reviewed_at=kit.reviewed_at,
        created_at=kit.created_at,
        updated_at=kit.updated_at,
    )


def _raise(error: Exception) -> None:
    if isinstance(error, InterviewKitNotFound):
        raise APIError(404, "interview_kit_not_found", "The interview preparation kit was not found.") from error
    if isinstance(error, InterviewKitResumeRequired):
        raise APIError(409, "interview_resume_required", "Upload a resume before preparing for an interview.") from error
    if isinstance(error, InterviewKitInvalidStatus):
        raise APIError(409, "interview_kit_unavailable", "Interview preparation becomes available after you record an application as submitted.") from error
    if isinstance(error, InterviewKitInvalidResponse):
        raise APIError(422, "invalid_interview_response", "Interview notes must match the current questions and stay within the size limit.") from error
    raise error


@router.post(
    "/{application_id}/interview-kit",
    response_model=InterviewKitResponse,
    status_code=status.HTTP_201_CREATED,
    responses={401: {"model": ErrorResponse}, 404: {"model": ErrorResponse}, 409: {"model": ErrorResponse}},
    summary="Create an evidence-grounded interview preparation kit",
)
def create_interview_kit(
    application_id: UUID,
    principal: PrincipalDependency,
    service: ServiceDependency,
) -> InterviewKitResponse:
    try:
        return _map(service.create(user_id=principal.user_id, application_id=application_id))
    except Exception as error:
        _raise(error)


@router.get(
    "/{application_id}/interview-kit",
    response_model=InterviewKitResponse,
    responses={401: {"model": ErrorResponse}, 404: {"model": ErrorResponse}},
    summary="Read an interview preparation kit",
)
def get_interview_kit(
    application_id: UUID,
    principal: PrincipalDependency,
    service: ServiceDependency,
) -> InterviewKitResponse:
    try:
        return _map(service.get(user_id=principal.user_id, application_id=application_id))
    except Exception as error:
        _raise(error)


@router.patch(
    "/{application_id}/interview-kit",
    response_model=InterviewKitResponse,
    responses={401: {"model": ErrorResponse}, 404: {"model": ErrorResponse}, 422: {"model": ErrorResponse}},
    summary="Save user-authored interview notes",
)
def update_interview_kit(
    application_id: UUID,
    request: UpdateInterviewKitRequest,
    principal: PrincipalDependency,
    service: ServiceDependency,
) -> InterviewKitResponse:
    try:
        return _map(
            service.update(
                user_id=principal.user_id,
                application_id=application_id,
                responses=request.responses,
                confirm_reviewed=request.confirm_reviewed,
            )
        )
    except Exception as error:
        _raise(error)

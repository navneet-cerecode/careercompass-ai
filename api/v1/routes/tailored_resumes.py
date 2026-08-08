"""Authenticated tailored resume review and export endpoints."""

from typing import Annotated, Literal, NoReturn
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response

from api.dependencies import get_required_principal, get_tailored_resume_service
from api.errors import APIError, ErrorResponse
from api.schemas.common import SkillResponse
from api.schemas.tailored_resumes import (
    ApproveTailoredResumeRequest,
    CreateTailoredResumeRequest,
    TailoredResumeContentResponse,
    TailoredResumeResponse,
    TailoredResumeSelectionsRequest,
    TailoredResumeVersionListResponse,
)
from api.services.tailored_resumes import (
    StaleTailoredResumeVersion,
    TailoredResumeNotFound,
    TailoredResumeReviewRequired,
    TailoredResumeService,
    TailoredResumeUnavailable,
)
from models.identity import AuthenticatedPrincipal
from models.tailored_resume import (
    TailoredResumeContent,
    TailoredResumeSelections,
    TailoredResumeVersion,
)

router = APIRouter()
PrincipalDependency = Annotated[AuthenticatedPrincipal, Depends(get_required_principal)]
ServiceDependency = Annotated[TailoredResumeService, Depends(get_tailored_resume_service)]


def _map_content(content: TailoredResumeContent) -> TailoredResumeContentResponse:
    return TailoredResumeContentResponse(
        **content.model_dump(exclude={"skills"}),
        skills=tuple(
            SkillResponse.model_validate(skill, from_attributes=True) for skill in content.skills
        ),
    )


def _map_version(version: TailoredResumeVersion) -> TailoredResumeResponse:
    return TailoredResumeResponse(
        id=version.id,
        plan_id=version.plan_id,
        source_resume_id=version.source_resume_id,
        job_id=version.job_id,
        version=version.version,
        original=_map_content(version.original),
        suggested=_map_content(version.suggested),
        accepted=_map_content(version.accepted),
        selections=TailoredResumeSelectionsRequest.model_validate(version.selections.model_dump()),
        verification_status=version.verification_status,
        user_review_required=version.user_review_required,
        approved_at=version.approved_at,
        created_at=version.created_at,
        updated_at=version.updated_at,
    )


def _raise_service_error(error: Exception) -> NoReturn:
    if isinstance(error, TailoredResumeUnavailable):
        raise APIError(
            403,
            "tailored_documents_unavailable",
            "Your current plan does not include tailored documents.",
        ) from error
    if isinstance(error, TailoredResumeNotFound):
        raise APIError(
            404,
            "tailored_resume_not_found",
            "The tailored resume was not found.",
        ) from error
    if isinstance(error, StaleTailoredResumeVersion):
        raise APIError(
            409,
            "stale_tailored_resume_version",
            "A newer version exists. Reload it before making another decision.",
        ) from error
    if isinstance(error, TailoredResumeReviewRequired):
        raise APIError(
            409,
            "tailored_resume_review_required",
            "Review and confirm factual accuracy before exporting this resume.",
        ) from error
    raise error


@router.post(
    "",
    response_model=TailoredResumeResponse,
    status_code=201,
    responses={
        401: {"model": ErrorResponse},
        403: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
    },
    summary="Create or load the latest tailored resume draft",
)
def create_tailored_resume(
    request: CreateTailoredResumeRequest,
    principal: PrincipalDependency,
    service: ServiceDependency,
) -> TailoredResumeResponse:
    try:
        version = service.create(user_id=principal.user_id, plan_id=request.plan_id)
    except (TailoredResumeUnavailable, TailoredResumeNotFound) as error:
        _raise_service_error(error)
    return _map_version(version)


@router.get(
    "/{tailored_resume_id}",
    response_model=TailoredResumeResponse,
    responses={401: {"model": ErrorResponse}, 404: {"model": ErrorResponse}},
    summary="Get an owner-scoped tailored resume version",
)
def get_tailored_resume(
    tailored_resume_id: UUID,
    principal: PrincipalDependency,
    service: ServiceDependency,
) -> TailoredResumeResponse:
    version = service.get(
        user_id=principal.user_id,
        tailored_resume_id=tailored_resume_id,
    )
    if version is None:
        _raise_service_error(TailoredResumeNotFound())
    return _map_version(version)


@router.get(
    "/{tailored_resume_id}/versions",
    response_model=TailoredResumeVersionListResponse,
    responses={401: {"model": ErrorResponse}, 404: {"model": ErrorResponse}},
    summary="List the version history for a tailored resume",
)
def list_tailored_resume_versions(
    tailored_resume_id: UUID,
    principal: PrincipalDependency,
    service: ServiceDependency,
) -> TailoredResumeVersionListResponse:
    try:
        versions = service.list_versions(
            user_id=principal.user_id,
            tailored_resume_id=tailored_resume_id,
        )
    except TailoredResumeNotFound as error:
        _raise_service_error(error)
    return TailoredResumeVersionListResponse(items=tuple(map(_map_version, versions)))


@router.post(
    "/{tailored_resume_id}/revisions",
    response_model=TailoredResumeResponse,
    status_code=201,
    responses={
        401: {"model": ErrorResponse},
        403: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
        409: {"model": ErrorResponse},
    },
    summary="Save reviewed section choices as a new version",
)
def revise_tailored_resume(
    tailored_resume_id: UUID,
    request: TailoredResumeSelectionsRequest,
    principal: PrincipalDependency,
    service: ServiceDependency,
) -> TailoredResumeResponse:
    try:
        version = service.revise(
            user_id=principal.user_id,
            tailored_resume_id=tailored_resume_id,
            selections=TailoredResumeSelections.model_validate(request.model_dump()),
        )
    except (
        TailoredResumeUnavailable,
        TailoredResumeNotFound,
        StaleTailoredResumeVersion,
    ) as error:
        _raise_service_error(error)
    return _map_version(version)


@router.post(
    "/{tailored_resume_id}/approve",
    response_model=TailoredResumeResponse,
    responses={
        401: {"model": ErrorResponse},
        403: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
        409: {"model": ErrorResponse},
    },
    summary="Confirm factual accuracy for the latest tailored resume version",
)
def approve_tailored_resume(
    tailored_resume_id: UUID,
    request: ApproveTailoredResumeRequest,
    principal: PrincipalDependency,
    service: ServiceDependency,
) -> TailoredResumeResponse:
    del request
    try:
        version = service.approve(
            user_id=principal.user_id,
            tailored_resume_id=tailored_resume_id,
        )
    except (
        TailoredResumeUnavailable,
        TailoredResumeNotFound,
        StaleTailoredResumeVersion,
    ) as error:
        _raise_service_error(error)
    return _map_version(version)


@router.get(
    "/{tailored_resume_id}/export",
    responses={
        401: {"model": ErrorResponse},
        403: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
        409: {"model": ErrorResponse},
    },
    summary="Export a user-verified tailored resume",
)
def export_tailored_resume(
    tailored_resume_id: UUID,
    principal: PrincipalDependency,
    service: ServiceDependency,
    export_format: Annotated[Literal["docx", "pdf"], Query(alias="format")] = "pdf",
) -> Response:
    try:
        exported = service.export(
            user_id=principal.user_id,
            tailored_resume_id=tailored_resume_id,
            export_format=export_format,
        )
    except (
        TailoredResumeUnavailable,
        TailoredResumeNotFound,
        TailoredResumeReviewRequired,
    ) as error:
        _raise_service_error(error)
    return Response(
        content=exported.content,
        media_type=exported.content_type,
        headers={
            "Content-Disposition": f'attachment; filename="{exported.filename}"',
            "Cache-Control": "private, no-store",
        },
    )

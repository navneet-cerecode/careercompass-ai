"""Authenticated cover letter review and export endpoints."""

from typing import Annotated, Literal, NoReturn
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response

from api.dependencies import get_cover_letter_service, get_required_principal
from api.errors import APIError, ErrorResponse
from api.schemas.cover_letters import (
    ApproveCoverLetterRequest,
    CoverLetterContentRequest,
    CoverLetterEvidenceResponse,
    CoverLetterResponse,
    CoverLetterVersionListResponse,
    CreateCoverLetterRequest,
)
from api.services.cover_letters import (
    CoverLetterNotFound,
    CoverLetterReviewRequired,
    CoverLetterService,
    CoverLetterSourceLocked,
    CoverLetterUnavailable,
    StaleCoverLetterVersion,
)
from models.cover_letter import CoverLetterContent, CoverLetterVersion
from models.identity import AuthenticatedPrincipal

router = APIRouter()
PrincipalDependency = Annotated[AuthenticatedPrincipal, Depends(get_required_principal)]
ServiceDependency = Annotated[CoverLetterService, Depends(get_cover_letter_service)]


def _map_version(version: CoverLetterVersion) -> CoverLetterResponse:
    return CoverLetterResponse(
        id=version.id,
        plan_id=version.plan_id,
        source_resume_id=version.source_resume_id,
        job_id=version.job_id,
        version=version.version,
        suggested=CoverLetterContentRequest.model_validate(version.suggested.model_dump()),
        accepted=CoverLetterContentRequest.model_validate(version.accepted.model_dump()),
        evidence=tuple(
            CoverLetterEvidenceResponse.model_validate(item.model_dump())
            for item in version.evidence
        ),
        verification_status=version.verification_status,
        user_review_required=version.user_review_required,
        approved_at=version.approved_at,
        created_at=version.created_at,
        updated_at=version.updated_at,
    )


def _raise_service_error(error: Exception) -> NoReturn:
    if isinstance(error, CoverLetterUnavailable):
        raise APIError(
            403,
            "cover_letters_unavailable",
            "Your current plan does not include cover letters.",
        ) from error
    if isinstance(error, CoverLetterNotFound):
        raise APIError(404, "cover_letter_not_found", "The cover letter was not found.") from error
    if isinstance(error, StaleCoverLetterVersion):
        raise APIError(
            409,
            "stale_cover_letter_version",
            "A newer version exists. Reload it before making another change.",
        ) from error
    if isinstance(error, CoverLetterReviewRequired):
        raise APIError(
            409,
            "cover_letter_review_required",
            "Review and confirm factual accuracy before exporting this cover letter.",
        ) from error
    if isinstance(error, CoverLetterSourceLocked):
        raise APIError(
            409,
            "cover_letter_source_locked",
            "Candidate identity and target-job fields come from verified sources and cannot be edited here.",
        ) from error
    raise error


@router.post(
    "",
    response_model=CoverLetterResponse,
    status_code=201,
    responses={401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}, 404: {"model": ErrorResponse}},
    summary="Create or load the latest cover letter draft",
)
def create_cover_letter(
    request: CreateCoverLetterRequest,
    principal: PrincipalDependency,
    service: ServiceDependency,
) -> CoverLetterResponse:
    try:
        version = service.create(user_id=principal.user_id, plan_id=request.plan_id)
    except (CoverLetterUnavailable, CoverLetterNotFound) as error:
        _raise_service_error(error)
    return _map_version(version)


@router.get(
    "/{cover_letter_id}",
    response_model=CoverLetterResponse,
    responses={401: {"model": ErrorResponse}, 404: {"model": ErrorResponse}},
    summary="Get an owner-scoped cover letter version",
)
def get_cover_letter(
    cover_letter_id: UUID,
    principal: PrincipalDependency,
    service: ServiceDependency,
) -> CoverLetterResponse:
    version = service.get(user_id=principal.user_id, cover_letter_id=cover_letter_id)
    if version is None:
        _raise_service_error(CoverLetterNotFound())
    return _map_version(version)


@router.get(
    "/{cover_letter_id}/versions",
    response_model=CoverLetterVersionListResponse,
    responses={401: {"model": ErrorResponse}, 404: {"model": ErrorResponse}},
    summary="List the version history for a cover letter",
)
def list_cover_letter_versions(
    cover_letter_id: UUID,
    principal: PrincipalDependency,
    service: ServiceDependency,
) -> CoverLetterVersionListResponse:
    try:
        versions = service.list_versions(
            user_id=principal.user_id,
            cover_letter_id=cover_letter_id,
        )
    except CoverLetterNotFound as error:
        _raise_service_error(error)
    return CoverLetterVersionListResponse(items=tuple(map(_map_version, versions)))


@router.post(
    "/{cover_letter_id}/revisions",
    response_model=CoverLetterResponse,
    status_code=201,
    responses={
        401: {"model": ErrorResponse},
        403: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
        409: {"model": ErrorResponse},
    },
    summary="Save edited cover letter content as a new version",
)
def revise_cover_letter(
    cover_letter_id: UUID,
    request: CoverLetterContentRequest,
    principal: PrincipalDependency,
    service: ServiceDependency,
) -> CoverLetterResponse:
    try:
        version = service.revise(
            user_id=principal.user_id,
            cover_letter_id=cover_letter_id,
            content=CoverLetterContent.model_validate(request.model_dump()),
        )
    except (
        CoverLetterUnavailable,
        CoverLetterNotFound,
        CoverLetterSourceLocked,
        StaleCoverLetterVersion,
    ) as error:
        _raise_service_error(error)
    return _map_version(version)


@router.post(
    "/{cover_letter_id}/approve",
    response_model=CoverLetterResponse,
    responses={
        401: {"model": ErrorResponse},
        403: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
        409: {"model": ErrorResponse},
    },
    summary="Confirm factual accuracy for the latest cover letter version",
)
def approve_cover_letter(
    cover_letter_id: UUID,
    request: ApproveCoverLetterRequest,
    principal: PrincipalDependency,
    service: ServiceDependency,
) -> CoverLetterResponse:
    del request
    try:
        version = service.approve(user_id=principal.user_id, cover_letter_id=cover_letter_id)
    except (CoverLetterUnavailable, CoverLetterNotFound, StaleCoverLetterVersion) as error:
        _raise_service_error(error)
    return _map_version(version)


@router.get(
    "/{cover_letter_id}/export",
    responses={
        401: {"model": ErrorResponse},
        403: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
        409: {"model": ErrorResponse},
    },
    summary="Export a user-verified cover letter",
)
def export_cover_letter(
    cover_letter_id: UUID,
    principal: PrincipalDependency,
    service: ServiceDependency,
    export_format: Annotated[Literal["docx", "pdf"], Query(alias="format")] = "pdf",
) -> Response:
    try:
        exported = service.export(
            user_id=principal.user_id,
            cover_letter_id=cover_letter_id,
            export_format=export_format,
        )
    except (
        CoverLetterUnavailable,
        CoverLetterNotFound,
        CoverLetterReviewRequired,
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

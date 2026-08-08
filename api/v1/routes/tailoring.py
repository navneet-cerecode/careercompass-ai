"""Authenticated factual tailoring-plan endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends

from api.dependencies import get_required_principal, get_tailoring_plan_service
from api.errors import APIError, ErrorResponse
from api.schemas.common import SkillResponse
from api.schemas.tailoring import (
    CreateTailoringPlanRequest,
    TailoringEvidenceResponse,
    TailoringPlanResponse,
)
from api.services.tailoring_plans import (
    TailoredDocumentsUnavailable,
    TailoringJobNotFound,
    TailoringPlanService,
    TailoringResumeNotFound,
)
from database.repositories.tailoring import PersistedTailoringPlan
from models.identity import AuthenticatedPrincipal

router = APIRouter()
PrincipalDependency = Annotated[AuthenticatedPrincipal, Depends(get_required_principal)]
TailoringServiceDependency = Annotated[
    TailoringPlanService,
    Depends(get_tailoring_plan_service),
]


def _map_plan(snapshot: PersistedTailoringPlan) -> TailoringPlanResponse:
    plan = snapshot.plan
    return TailoringPlanResponse(
        id=snapshot.id,
        source_resume_id=plan.source_resume_id,
        job_id=plan.job_id,
        skills=tuple(
            SkillResponse.model_validate(skill, from_attributes=True) for skill in plan.skills
        ),
        experience=plan.experience,
        projects=plan.projects,
        matched_skills=tuple(
            SkillResponse.model_validate(skill, from_attributes=True)
            for skill in plan.matched_skills
        ),
        missing_skills=tuple(
            SkillResponse.model_validate(skill, from_attributes=True)
            for skill in plan.missing_skills
        ),
        evidence=tuple(
            TailoringEvidenceResponse.model_validate(item, from_attributes=True)
            for item in plan.evidence
        ),
        user_review_required=plan.user_review_required,
        algorithm_version=plan.algorithm_version,
        created_at=snapshot.created_at,
        updated_at=snapshot.updated_at,
    )


@router.post(
    "",
    response_model=TailoringPlanResponse,
    status_code=201,
    responses={
        401: {"model": ErrorResponse},
        403: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
    },
    summary="Create a factual tailoring plan for a selected job",
)
def create_tailoring_plan(
    request: CreateTailoringPlanRequest,
    principal: PrincipalDependency,
    tailoring: TailoringServiceDependency,
) -> TailoringPlanResponse:
    try:
        snapshot = tailoring.create(
            user_id=principal.user_id,
            job_id=request.job_id,
            resume_id=request.resume_id,
        )
    except TailoredDocumentsUnavailable as error:
        raise APIError(
            403,
            "tailored_documents_unavailable",
            "Your current plan does not include tailored documents.",
        ) from error
    except TailoringResumeNotFound as error:
        raise APIError(404, "resume_not_found", "The requested resume was not found.") from error
    except TailoringJobNotFound as error:
        raise APIError(404, "job_not_found", "The requested job was not found.") from error
    return _map_plan(snapshot)


@router.get(
    "/{plan_id}",
    response_model=TailoringPlanResponse,
    responses={401: {"model": ErrorResponse}, 404: {"model": ErrorResponse}},
    summary="Get an owner-scoped factual tailoring plan",
)
def get_tailoring_plan(
    plan_id: UUID,
    principal: PrincipalDependency,
    tailoring: TailoringServiceDependency,
) -> TailoringPlanResponse:
    snapshot = tailoring.get(user_id=principal.user_id, plan_id=plan_id)
    if snapshot is None:
        raise APIError(404, "tailoring_plan_not_found", "The tailoring plan was not found.")
    return _map_plan(snapshot)

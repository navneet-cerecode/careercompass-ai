"""Authenticated skill intelligence endpoint."""

from typing import Annotated

from fastapi import APIRouter, Depends

from api.dependencies import get_required_principal, get_skill_intelligence_service
from api.errors import ErrorResponse
from api.schemas.skill_intelligence import SkillIntelligenceResponse
from api.services.skill_intelligence import SkillIntelligenceService
from models.identity import AuthenticatedPrincipal

router = APIRouter()
PrincipalDependency = Annotated[AuthenticatedPrincipal, Depends(get_required_principal)]
ServiceDependency = Annotated[
    SkillIntelligenceService,
    Depends(get_skill_intelligence_service),
]


@router.get(
    "",
    response_model=SkillIntelligenceResponse,
    responses={401: {"model": ErrorResponse}},
    summary="Compare verified resume evidence with roles in the user's history",
)
def get_skill_intelligence(
    principal: PrincipalDependency,
    service: ServiceDependency,
) -> SkillIntelligenceResponse:
    return SkillIntelligenceResponse.model_validate(
        service.get(user_id=principal.user_id),
        from_attributes=True,
    )

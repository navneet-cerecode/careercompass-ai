"""Verified account endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends

from api.dependencies import get_required_principal
from api.errors import ErrorResponse
from api.schemas.auth import AuthenticatedUserResponse
from models.identity import AuthenticatedPrincipal

router = APIRouter()
PrincipalDependency = Annotated[
    AuthenticatedPrincipal,
    Depends(get_required_principal),
]


@router.get(
    "/me",
    response_model=AuthenticatedUserResponse,
    responses={
        401: {"model": ErrorResponse},
        403: {"model": ErrorResponse},
        409: {"model": ErrorResponse},
        503: {"model": ErrorResponse},
    },
    summary="Get the verified current account",
)
def get_current_account(
    principal: PrincipalDependency,
) -> AuthenticatedUserResponse:
    return AuthenticatedUserResponse(
        id=principal.user_id,
        email=principal.email,
        name=principal.name,
    )

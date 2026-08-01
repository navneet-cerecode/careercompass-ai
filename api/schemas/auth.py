"""Authenticated account transport contracts."""

from uuid import UUID

from pydantic import EmailStr

from api.schemas.common import APIModel


class AuthenticatedUserResponse(APIModel):
    id: UUID
    email: EmailStr
    name: str

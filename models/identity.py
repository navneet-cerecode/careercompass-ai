"""Verified identity values crossing the authentication boundary."""

from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class VerifiedIdentity(BaseModel):
    model_config = ConfigDict(frozen=True)

    issuer: str = Field(min_length=1, max_length=500)
    subject: str = Field(min_length=1, max_length=500)
    email: EmailStr
    name: str = Field(min_length=1, max_length=200)


class AuthenticatedPrincipal(BaseModel):
    model_config = ConfigDict(frozen=True)

    user_id: UUID
    issuer: str
    subject: str
    email: EmailStr
    name: str

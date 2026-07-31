"""Shared public API value objects."""

from pydantic import BaseModel, ConfigDict


class APIModel(BaseModel):
    """Base behavior for immutable response contracts."""

    model_config = ConfigDict(frozen=True)


class SkillResponse(APIModel):
    name: str
    category: str | None = None

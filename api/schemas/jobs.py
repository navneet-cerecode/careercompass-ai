"""Job transport contracts."""

from uuid import UUID

from pydantic import AnyHttpUrl

from api.schemas.common import APIModel, SkillResponse
from models.enums import EmploymentType, ExperienceLevel, JobSource


class JobResponse(APIModel):
    id: UUID
    title: str
    company: str
    location: str
    description: str
    required_skills: tuple[SkillResponse, ...] = ()
    experience_level: ExperienceLevel
    employment_type: EmploymentType
    source: JobSource
    source_name: str | None = None
    external_id: str | None = None
    source_url: AnyHttpUrl | None = None
    url: AnyHttpUrl

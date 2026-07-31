"""Resume transport contracts."""

from uuid import UUID

from pydantic import EmailStr

from api.schemas.common import APIModel, SkillResponse


class ResumeResponse(APIModel):
    """Structured resume data safe for ordinary API responses."""

    id: UUID
    name: str
    email: EmailStr | None = None
    phone: str | None = None
    linkedin: str | None = None
    github: str | None = None
    education: tuple[str, ...] = ()
    experience: tuple[str, ...] = ()
    projects: tuple[str, ...] = ()
    skills: tuple[SkillResponse, ...] = ()
    certifications: tuple[str, ...] = ()
    achievements: tuple[str, ...] = ()


class ParsedResumeResponse(APIModel):
    """One-time parsing response that returns user-submitted source text."""

    resume: ResumeResponse
    raw_text: str

"""User-reviewed application packet state."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ApplicationPacket(BaseModel):
    """Documents and confirmations prepared before an external application."""

    model_config = ConfigDict(frozen=True)

    id: UUID
    user_id: UUID
    application_id: UUID
    source_resume_id: UUID | None = None
    tailored_resume_id: UUID | None = None
    cover_letter_id: UUID | None = None
    job_details_reviewed: bool = False
    resume_reviewed: bool = False
    cover_letter_reviewed: bool = False
    employer_questions_reviewed: bool = False
    ready_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

"""Evidence-grounded interview preparation contracts."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict

InterviewQuestionCategory = Literal[
    "career_story",
    "role_specific",
    "skill_gap",
    "motivation",
    "behavioral",
]


class InterviewQuestion(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str
    category: InterviewQuestionCategory
    question: str
    why_it_matters: str
    evidence_prompts: tuple[str, ...] = ()


class InterviewKit(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: UUID
    user_id: UUID
    application_id: UUID
    resume_id: UUID
    questions: tuple[InterviewQuestion, ...]
    responses: dict[str, str]
    reviewed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

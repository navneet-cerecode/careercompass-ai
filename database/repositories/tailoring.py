"""Owner-scoped factual tailoring-plan persistence."""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from database.models.tailoring import TailoringPlanRecord
from models.skill import Skill
from models.tailoring import FactualTailoringPlan, TailoringEvidence


@dataclass(frozen=True)
class PersistedTailoringPlan:
    id: UUID
    user_id: UUID
    plan: FactualTailoringPlan
    created_at: datetime
    updated_at: datetime


class TailoringPlanRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def save(self, *, user_id: UUID, plan: FactualTailoringPlan) -> PersistedTailoringPlan:
        record = self.session.scalar(
            select(TailoringPlanRecord).where(
                TailoringPlanRecord.user_id == user_id,
                TailoringPlanRecord.resume_id == plan.source_resume_id,
                TailoringPlanRecord.job_id == plan.job_id,
                TailoringPlanRecord.algorithm_version == plan.algorithm_version,
            )
        )
        values = {
            "skills": [skill.model_dump(mode="json") for skill in plan.skills],
            "experience": list(plan.experience),
            "projects": list(plan.projects),
            "matched_skills": [skill.model_dump(mode="json") for skill in plan.matched_skills],
            "missing_skills": [skill.model_dump(mode="json") for skill in plan.missing_skills],
            "evidence": [item.model_dump(mode="json") for item in plan.evidence],
            "user_review_required": plan.user_review_required,
        }
        if record is None:
            record = TailoringPlanRecord(
                user_id=user_id,
                resume_id=plan.source_resume_id,
                job_id=plan.job_id,
                algorithm_version=plan.algorithm_version,
                **values,
            )
            self.session.add(record)
        else:
            for name, value in values.items():
                setattr(record, name, value)
        self.session.flush()
        self.session.refresh(record)
        return self._to_domain(record)

    def get(self, *, user_id: UUID, plan_id: UUID) -> PersistedTailoringPlan | None:
        record = self.session.scalar(
            select(TailoringPlanRecord).where(
                TailoringPlanRecord.id == plan_id,
                TailoringPlanRecord.user_id == user_id,
            )
        )
        return self._to_domain(record) if record is not None else None

    @staticmethod
    def _to_domain(record: TailoringPlanRecord) -> PersistedTailoringPlan:
        return PersistedTailoringPlan(
            id=record.id,
            user_id=record.user_id,
            plan=FactualTailoringPlan(
                source_resume_id=record.resume_id,
                job_id=record.job_id,
                skills=tuple(Skill.model_validate(value) for value in record.skills),
                experience=tuple(record.experience),
                projects=tuple(record.projects),
                matched_skills=tuple(
                    Skill.model_validate(value) for value in record.matched_skills
                ),
                missing_skills=tuple(
                    Skill.model_validate(value) for value in record.missing_skills
                ),
                evidence=tuple(
                    TailoringEvidence.model_validate(value) for value in record.evidence
                ),
                user_review_required=record.user_review_required,
                algorithm_version=record.algorithm_version,
            ),
            created_at=record.created_at,
            updated_at=record.updated_at,
        )

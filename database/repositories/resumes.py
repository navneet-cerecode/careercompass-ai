"""Versioned resume persistence with normalized skills."""

import hashlib
from dataclasses import dataclass
from pathlib import Path
from uuid import UUID, uuid4

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session, selectinload

from database.models.resumes import (
    ResumeRecord,
    ResumeSkillRecord,
    SkillRecord,
)
from models.resume import Resume
from models.skill import Skill


@dataclass(frozen=True)
class PersistedResume:
    user_id: UUID
    version: int
    is_active: bool
    resume: Resume
    original_filename: str | None


class ResumeRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def save_version(
        self,
        *,
        user_id: UUID,
        resume: Resume,
        original_filename: str | None = None,
    ) -> PersistedResume:
        latest_version = self.session.scalar(
            select(func.max(ResumeRecord.version)).where(ResumeRecord.user_id == user_id)
        )
        version = (latest_version or 0) + 1
        self.session.execute(
            update(ResumeRecord)
            .where(
                ResumeRecord.user_id == user_id,
                ResumeRecord.is_active.is_(True),
            )
            .values(is_active=False)
        )

        record_id = resume.id
        if self.session.get(ResumeRecord, record_id) is not None:
            record_id = uuid4()

        record = ResumeRecord(
            id=record_id,
            user_id=user_id,
            version=version,
            is_active=True,
            original_filename=(Path(original_filename).name if original_filename else None),
            name=resume.name,
            email=str(resume.email) if resume.email else None,
            phone=resume.phone,
            linkedin=resume.linkedin,
            github=resume.github,
            raw_text=resume.raw_text,
            content_sha256=hashlib.sha256(resume.raw_text.encode("utf-8")).hexdigest(),
            education=list(resume.education),
            experience=list(resume.experience),
            projects=list(resume.projects),
            certifications=list(resume.certifications),
            achievements=list(resume.achievements),
        )
        self.session.add(record)
        self._set_skills(record, resume.skills)
        self.session.flush()
        return self._to_domain(record)

    def get(self, *, user_id: UUID, resume_id: UUID) -> PersistedResume | None:
        record = self.session.scalar(
            select(ResumeRecord)
            .where(
                ResumeRecord.id == resume_id,
                ResumeRecord.user_id == user_id,
            )
            .options(selectinload(ResumeRecord.skill_links).selectinload(ResumeSkillRecord.skill))
        )
        return self._to_domain(record) if record is not None else None

    def get_active(self, *, user_id: UUID) -> PersistedResume | None:
        record = self.session.scalar(
            select(ResumeRecord)
            .where(
                ResumeRecord.user_id == user_id,
                ResumeRecord.is_active.is_(True),
            )
            .options(selectinload(ResumeRecord.skill_links).selectinload(ResumeSkillRecord.skill))
        )
        return self._to_domain(record) if record is not None else None

    def _set_skills(self, record: ResumeRecord, skills: list[Skill]) -> None:
        seen: set[str] = set()
        for position, skill in enumerate(skills, start=1):
            normalized_name = skill.name.strip().casefold()
            if normalized_name in seen:
                continue
            seen.add(normalized_name)

            skill_record = self.session.scalar(
                select(SkillRecord).where(SkillRecord.normalized_name == normalized_name)
            )
            if skill_record is None:
                skill_record = SkillRecord(
                    normalized_name=normalized_name,
                    display_name=skill.name,
                    category=skill.category,
                )
                self.session.add(skill_record)

            record.skill_links.append(
                ResumeSkillRecord(
                    skill=skill_record,
                    position=position,
                )
            )

    @staticmethod
    def _to_domain(record: ResumeRecord) -> PersistedResume:
        return PersistedResume(
            user_id=record.user_id,
            version=record.version,
            is_active=record.is_active,
            original_filename=record.original_filename,
            resume=Resume(
                id=record.id,
                name=record.name,
                email=record.email,
                phone=record.phone,
                linkedin=record.linkedin,
                github=record.github,
                education=list(record.education),
                experience=list(record.experience),
                projects=list(record.projects),
                skills=[
                    Skill(
                        name=link.skill.display_name,
                        category=link.skill.category,
                    )
                    for link in record.skill_links
                ],
                certifications=list(record.certifications),
                achievements=list(record.achievements),
                raw_text=record.raw_text,
            ),
        )

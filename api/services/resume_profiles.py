"""Owner-scoped durable resume profiles."""

from uuid import UUID

from database.repositories.resumes import ResumeRepository
from database.session import Database
from models.resume import Resume


class ResumeProfileService:
    def __init__(self, database: Database) -> None:
        self.database = database

    def save(
        self,
        *,
        user_id: UUID,
        resume: Resume,
        original_filename: str | None,
    ) -> Resume:
        with self.database.session() as session:
            persisted = ResumeRepository(session).save_version(
                user_id=user_id,
                resume=resume,
                original_filename=original_filename,
            )
            return persisted.resume

    def get_current(self, *, user_id: UUID) -> Resume | None:
        with self.database.session() as session:
            persisted = ResumeRepository(session).get_active(user_id=user_id)
            return persisted.resume if persisted is not None else None

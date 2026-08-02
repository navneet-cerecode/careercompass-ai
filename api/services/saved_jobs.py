"""Application service for owner-scoped saved jobs."""

from dataclasses import dataclass
from uuid import UUID

from database.repositories.applications import SavedJobRepository
from database.repositories.jobs import JobRepository
from database.session import Database
from models.application import SavedJob
from models.job import Job


@dataclass(frozen=True)
class SavedJobSnapshot:
    saved_job: SavedJob
    job: Job


class SavedJobService:
    def __init__(self, database: Database) -> None:
        self.database = database

    def save(
        self,
        *,
        user_id: UUID,
        job_id: UUID,
        notes: str | None = None,
    ) -> SavedJobSnapshot | None:
        with self.database.session() as session:
            jobs = JobRepository(session)
            job = jobs.get(job_id)
            if job is None:
                return None
            saved_job = SavedJobRepository(session).save(
                user_id=user_id,
                job_id=job_id,
                notes=notes,
            )
            return SavedJobSnapshot(saved_job=saved_job, job=job)

    def list(self, *, user_id: UUID) -> tuple[SavedJobSnapshot, ...]:
        with self.database.session() as session:
            saved_jobs = SavedJobRepository(session).list(user_id=user_id)
            if not saved_jobs:
                return ()
            jobs = JobRepository(session).get_many(
                tuple(saved_job.job_id for saved_job in saved_jobs)
            )
            if jobs is None:
                raise RuntimeError("A saved job references a missing catalog entry.")
            return tuple(
                SavedJobSnapshot(saved_job=saved_job, job=job)
                for saved_job, job in zip(saved_jobs, jobs, strict=True)
            )

    def remove(self, *, user_id: UUID, job_id: UUID) -> bool:
        with self.database.session() as session:
            return SavedJobRepository(session).remove(
                user_id=user_id,
                job_id=job_id,
            )

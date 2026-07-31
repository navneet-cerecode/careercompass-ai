"""Persistence-backed job catalog adapter."""

from uuid import UUID

from database.repositories.jobs import JobRepository
from database.session import Database
from models.job import Job


class JobCatalog:
    def __init__(self, database: Database) -> None:
        self.database = database

    def add_many(self, jobs: tuple[Job, ...]) -> tuple[Job, ...]:
        with self.database.session() as session:
            return JobRepository(session).upsert_many(jobs)

    def get(self, job_id: UUID) -> Job | None:
        with self.database.session() as session:
            return JobRepository(session).get(job_id)

    def get_many(self, job_ids: tuple[UUID, ...]) -> tuple[Job, ...] | None:
        with self.database.session() as session:
            return JobRepository(session).get_many(job_ids)

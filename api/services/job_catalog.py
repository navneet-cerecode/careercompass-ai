"""Bounded transitional job catalog used until PostgreSQL is introduced."""

from threading import Lock
from uuid import UUID

from models.job import Job


class InMemoryJobCatalog:
    def __init__(self, max_entries: int) -> None:
        self.max_entries = max_entries
        self._jobs: dict[UUID, Job] = {}
        self._lock = Lock()

    def add_many(self, jobs: tuple[Job, ...]) -> None:
        with self._lock:
            for job in jobs:
                self._jobs[job.id] = job
            while len(self._jobs) > self.max_entries:
                oldest_id = next(iter(self._jobs))
                del self._jobs[oldest_id]

    def get(self, job_id: UUID) -> Job | None:
        with self._lock:
            return self._jobs.get(job_id)

    def get_many(self, job_ids: tuple[UUID, ...]) -> tuple[Job, ...] | None:
        with self._lock:
            if any(job_id not in self._jobs for job_id in job_ids):
                return None
            return tuple(self._jobs[job_id] for job_id in job_ids)

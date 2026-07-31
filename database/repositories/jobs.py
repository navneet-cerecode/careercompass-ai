"""Repository mapping canonical jobs to durable records."""

from collections.abc import Iterable
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from database.models.jobs import JobRecord, JobSourceRecord
from models.enums import EmploymentType, ExperienceLevel, JobSource
from models.job import Job
from services.job_discovery.fingerprint import (
    job_fingerprint,
    normalize_fingerprint_text,
)


class JobRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def upsert_many(self, jobs: Iterable[Job]) -> tuple[Job, ...]:
        return tuple(self.upsert(job) for job in jobs)

    def upsert(self, job: Job) -> Job:
        fingerprint = job_fingerprint(job)
        record = self.session.scalar(
            select(JobRecord)
            .where(JobRecord.fingerprint == fingerprint)
            .options(selectinload(JobRecord.sources))
        )

        if record is None:
            record = JobRecord(
                id=job.id,
                fingerprint=fingerprint,
                title=job.title,
                normalized_title=normalize_fingerprint_text(job.title),
                company=job.company,
                normalized_company=normalize_fingerprint_text(job.company),
                location=job.location,
                normalized_location=normalize_fingerprint_text(job.location),
                description=job.description,
                experience_level=job.experience_level.value,
                employment_type=job.employment_type.value,
                primary_source=job.source.value,
                apply_url=str(job.url),
            )
            self.session.add(record)
        else:
            record.last_seen_at = datetime.now(UTC)
            record.is_active = True
            if len(job.description) > len(record.description):
                record.description = job.description
            if record.apply_url != str(job.url) and job.source != JobSource.OTHER:
                record.apply_url = str(job.url)

        self._upsert_source(record, job)
        self.session.flush()
        return self._to_domain(record, preferred_job=job)

    def get(self, job_id: UUID) -> Job | None:
        record = self.session.scalar(
            select(JobRecord).where(JobRecord.id == job_id).options(selectinload(JobRecord.sources))
        )
        return self._to_domain(record) if record is not None else None

    def get_many(self, job_ids: tuple[UUID, ...]) -> tuple[Job, ...] | None:
        records = self.session.scalars(
            select(JobRecord)
            .where(JobRecord.id.in_(job_ids))
            .options(selectinload(JobRecord.sources))
        ).all()
        by_id = {record.id: record for record in records}
        if any(job_id not in by_id for job_id in job_ids):
            return None
        return tuple(self._to_domain(by_id[job_id]) for job_id in job_ids)

    def _upsert_source(self, record: JobRecord, job: Job) -> None:
        provider_name = job.source_name or job.source.value.casefold()
        source_url = str(job.source_url or job.url)
        source = next(
            (
                item
                for item in record.sources
                if item.provider_name == provider_name and item.source_url == source_url
            ),
            None,
        )
        if source is None:
            record.sources.append(
                JobSourceRecord(
                    provider_name=provider_name,
                    external_id=job.external_id,
                    source_url=source_url,
                )
            )
        else:
            source.last_seen_at = datetime.now(UTC)
            source.external_id = job.external_id or source.external_id

    @staticmethod
    def _to_domain(record: JobRecord, preferred_job: Job | None = None) -> Job:
        source_record = None
        if preferred_job is not None:
            provider_name = preferred_job.source_name or preferred_job.source.value.casefold()
            source_record = next(
                (item for item in record.sources if item.provider_name == provider_name),
                None,
            )
        if source_record is None and record.sources:
            source_record = record.sources[0]

        return Job(
            id=record.id,
            title=record.title,
            company=record.company,
            location=record.location,
            description=record.description,
            experience_level=ExperienceLevel(record.experience_level),
            employment_type=EmploymentType(record.employment_type),
            source=JobSource(record.primary_source),
            source_name=source_record.provider_name if source_record else None,
            external_id=source_record.external_id if source_record else None,
            source_url=source_record.source_url if source_record else None,
            url=record.apply_url,
        )

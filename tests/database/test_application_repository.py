from datetime import datetime, timezone

import pytest

from database.base import Base
from database.repositories.applications import (
    ApplicationRepository,
    InvalidApplicationTransition,
    SavedJobRepository,
)
from database.repositories.jobs import JobRepository
from database.repositories.resumes import ResumeRepository
from database.repositories.users import UserRepository
from database.session import Database
from models.enums import ApplicationStatus
from models.job import Job
from models.resume import Resume


def make_database() -> Database:
    database = Database("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(database.engine)
    return database


def seed_owner_and_job(session):
    users = UserRepository(session)
    owner = users.create(email="owner@example.com", name="Owner")
    other = users.create(email="other@example.com", name="Other")
    job = JobRepository(session).upsert(
        Job(
            title="Platform Engineer",
            company="Example Corp",
            location="Remote",
            description="Build reliable services.",
            url="https://example.com/jobs/platform",
        )
    )
    return owner, other, job


def test_saved_jobs_are_idempotent_and_owner_scoped():
    database = make_database()
    with database.session() as session:
        owner, other, job = seed_owner_and_job(session)
        repository = SavedJobRepository(session)

        first = repository.save(user_id=owner.id, job_id=job.id, notes="Review")
        updated = repository.save(user_id=owner.id, job_id=job.id, notes="Priority")

        assert updated.created_at == first.created_at
        assert updated.notes == "Priority"
        assert len(repository.list(user_id=owner.id)) == 1
        assert repository.get(user_id=other.id, job_id=job.id) is None
        assert repository.remove(user_id=other.id, job_id=job.id) is False
        assert repository.remove(user_id=owner.id, job_id=job.id) is True
        assert repository.get(user_id=owner.id, job_id=job.id) is None


def test_application_transitions_are_validated_and_audited():
    database = make_database()
    with database.session() as session:
        owner, _, job = seed_owner_and_job(session)
        resume = ResumeRepository(session).save_version(
            user_id=owner.id,
            resume=Resume(name="Owner", raw_text="Platform engineer"),
        )
        repository = ApplicationRepository(session)
        application = repository.create(
            user_id=owner.id,
            job_id=job.id,
            resume_id=resume.resume.id,
            status=ApplicationStatus.SAVED,
        )

        for status in (
            ApplicationStatus.PREPARING,
            ApplicationStatus.READY_TO_APPLY,
            ApplicationStatus.APPLIED,
            ApplicationStatus.INTERVIEW,
            ApplicationStatus.OFFER,
        ):
            application = repository.transition(
                user_id=owner.id,
                application_id=application.id,
                new_status=status,
                note=f"Moved to {status.value}",
            )
            assert application is not None

        assert application.status == ApplicationStatus.OFFER
        assert application.applied_at is not None
        events = repository.events(user_id=owner.id, application_id=application.id)
        assert [event.new_status for event in events] == [
            ApplicationStatus.SAVED,
            ApplicationStatus.PREPARING,
            ApplicationStatus.READY_TO_APPLY,
            ApplicationStatus.APPLIED,
            ApplicationStatus.INTERVIEW,
            ApplicationStatus.OFFER,
        ]
        assert events[0].previous_status is None
        assert events[-1].previous_status == ApplicationStatus.INTERVIEW


def test_invalid_and_terminal_transitions_do_not_create_events():
    database = make_database()
    with database.session() as session:
        owner, _, job = seed_owner_and_job(session)
        repository = ApplicationRepository(session)
        application = repository.create(user_id=owner.id, job_id=job.id)

        with pytest.raises(InvalidApplicationTransition, match="Cannot transition"):
            repository.transition(
                user_id=owner.id,
                application_id=application.id,
                new_status=ApplicationStatus.OFFER,
            )
        assert len(repository.events(user_id=owner.id, application_id=application.id)) == 1

        withdrawn = repository.transition(
            user_id=owner.id,
            application_id=application.id,
            new_status=ApplicationStatus.WITHDRAWN,
        )
        assert withdrawn is not None
        with pytest.raises(InvalidApplicationTransition):
            repository.transition(
                user_id=owner.id,
                application_id=application.id,
                new_status=ApplicationStatus.SAVED,
            )
        assert len(repository.events(user_id=owner.id, application_id=application.id)) == 2


def test_applications_and_events_are_owner_scoped():
    database = make_database()
    with database.session() as session:
        owner, other, job = seed_owner_and_job(session)
        repository = ApplicationRepository(session)
        application = repository.create(user_id=owner.id, job_id=job.id)

        assert repository.get(user_id=other.id, application_id=application.id) is None
        assert repository.list(user_id=other.id) == ()
        assert repository.events(user_id=other.id, application_id=application.id) == ()
        assert (
            repository.transition(
                user_id=other.id,
                application_id=application.id,
                new_status=ApplicationStatus.SAVED,
            )
            is None
        )


def test_application_rejects_another_users_resume_and_duplicate_job():
    database = make_database()
    with database.session() as session:
        owner, other, job = seed_owner_and_job(session)
        other_resume = ResumeRepository(session).save_version(
            user_id=other.id,
            resume=Resume(name="Other", raw_text="Other resume"),
        )
        repository = ApplicationRepository(session)

        with pytest.raises(ValueError, match="does not belong"):
            repository.create(
                user_id=owner.id,
                job_id=job.id,
                resume_id=other_resume.resume.id,
            )

        repository.create(
            user_id=owner.id,
            job_id=job.id,
            next_action_due_at=datetime.now(timezone.utc),
        )
        with pytest.raises(ValueError, match="already exists"):
            repository.create(user_id=owner.id, job_id=job.id)

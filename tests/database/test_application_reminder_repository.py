from datetime import UTC, datetime, timedelta

from database.base import Base
from database.repositories.application_reminders import ApplicationReminderRepository
from database.repositories.applications import ApplicationRepository
from database.repositories.jobs import JobRepository
from database.repositories.users import UserRepository
from database.session import Database
from models.enums import ApplicationReminderStatus, ApplicationStatus
from models.job import Job


def make_database() -> Database:
    database = Database("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(database.engine)
    return database


def seed_application(session, *, due_at: datetime, next_action: str = "Follow up"):
    user = UserRepository(session).create(email="owner@example.com", name="Owner")
    job = JobRepository(session).upsert(
        Job(
            title="Platform Engineer",
            company="Example Corp",
            location="Remote",
            description="Build reliable systems.",
            url="https://example.com/jobs/platform",
        )
    )
    application = ApplicationRepository(session).create(
        user_id=user.id,
        job_id=job.id,
        status=ApplicationStatus.APPLIED,
        next_action=next_action,
        next_action_due_at=due_at,
    )
    return user, application


def test_reconciliation_is_idempotent_and_owner_scoped():
    database = make_database()
    now = datetime(2026, 8, 2, 9, tzinfo=UTC)
    with database.session() as session:
        owner, application = seed_application(
            session,
            due_at=now + timedelta(hours=12),
        )
        other = UserRepository(session).create(email="other@example.com", name="Other")
        reminders = ApplicationReminderRepository(session)

        first = reminders.reconcile(
            now=now,
            upcoming_before=now + timedelta(hours=24),
            limit=100,
        )
        second = reminders.reconcile(
            now=now,
            upcoming_before=now + timedelta(hours=24),
            limit=100,
        )

        assert first.created == 1
        assert second.created == 0
        assert len(reminders.list(user_id=owner.id)) == 1
        assert reminders.list(user_id=other.id) == ()
        assert reminders.list(user_id=owner.id)[0].application_id == application.id


def test_changed_plan_dismisses_stale_reminder_and_creates_replacement():
    database = make_database()
    now = datetime(2026, 8, 2, 9, tzinfo=UTC)
    original_due_at = now + timedelta(hours=12)
    replacement_due_at = now + timedelta(hours=18)
    with database.session() as session:
        owner, application = seed_application(session, due_at=original_due_at)
        reminders = ApplicationReminderRepository(session)
        reminders.reconcile(
            now=now,
            upcoming_before=now + timedelta(hours=24),
            limit=100,
        )
        ApplicationRepository(session).update_plan(
            user_id=owner.id,
            application_id=application.id,
            next_action="Prepare interview questions",
            next_action_due_at=replacement_due_at,
        )

        result = reminders.reconcile(
            now=now,
            upcoming_before=now + timedelta(hours=24),
            limit=100,
        )

        assert result.dismissed == 1
        assert result.created == 1
        visible = reminders.list(user_id=owner.id)
        assert len(visible) == 1
        assert visible[0].next_action == "Prepare interview questions"
        assert visible[0].due_at.replace(tzinfo=UTC) == replacement_due_at


def test_terminal_application_dismisses_active_reminder():
    database = make_database()
    now = datetime(2026, 8, 2, 9, tzinfo=UTC)
    with database.session() as session:
        owner, application = seed_application(
            session,
            due_at=now + timedelta(hours=12),
        )
        reminders = ApplicationReminderRepository(session)
        reminders.reconcile(
            now=now,
            upcoming_before=now + timedelta(hours=24),
            limit=100,
        )
        ApplicationRepository(session).transition(
            user_id=owner.id,
            application_id=application.id,
            new_status=ApplicationStatus.REJECTED,
        )

        result = reminders.reconcile(
            now=now,
            upcoming_before=now + timedelta(hours=24),
            limit=100,
        )

        assert result.dismissed == 1
        assert reminders.list(user_id=owner.id) == ()


def test_user_can_read_and_dismiss_only_owned_reminders():
    database = make_database()
    now = datetime(2026, 8, 2, 9, tzinfo=UTC)
    with database.session() as session:
        owner, _ = seed_application(session, due_at=now)
        other = UserRepository(session).create(email="other@example.com", name="Other")
        reminders = ApplicationReminderRepository(session)
        reminders.reconcile(now=now, upcoming_before=now, limit=100)
        reminder = reminders.list(user_id=owner.id)[0]

        assert (
            reminders.set_status(
                user_id=other.id,
                reminder_id=reminder.id,
                status=ApplicationReminderStatus.READ,
            )
            is None
        )
        read = reminders.set_status(
            user_id=owner.id,
            reminder_id=reminder.id,
            status=ApplicationReminderStatus.READ,
        )
        assert read is not None
        assert read.status == ApplicationReminderStatus.READ
        assert read.read_at is not None

        dismissed = reminders.set_status(
            user_id=owner.id,
            reminder_id=reminder.id,
            status=ApplicationReminderStatus.DISMISSED,
        )
        assert dismissed is not None
        assert reminders.list(user_id=owner.id) == ()

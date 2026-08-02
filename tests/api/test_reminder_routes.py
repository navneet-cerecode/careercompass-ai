from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient

from api.application import create_app
from api.dependencies import get_required_principal
from core.config import Settings
from database.base import Base
from database.repositories.application_reminders import ApplicationReminderRepository
from database.repositories.applications import ApplicationRepository
from database.repositories.jobs import JobRepository
from database.repositories.users import UserRepository
from database.session import Database
from models.enums import ApplicationStatus
from models.identity import AuthenticatedPrincipal
from models.job import Job


def principal_for(user) -> AuthenticatedPrincipal:
    return AuthenticatedPrincipal(
        user_id=user.id,
        issuer="https://identity.example.test/",
        subject=f"subject-{user.id}",
        email=user.email,
        name=user.name,
    )


def make_client():
    database = Database("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(database.engine)
    now = datetime(2026, 8, 2, 9, tzinfo=UTC)
    with database.session() as session:
        owner = UserRepository(session).create(email="owner@example.com", name="Owner")
        other = UserRepository(session).create(email="other@example.com", name="Other")
        job = JobRepository(session).upsert(
            Job(
                title="Platform Engineer",
                company="Example Corp",
                location="Remote",
                description="Build systems.",
                url="https://example.com/jobs/platform",
            )
        )
        application = ApplicationRepository(session).create(
            user_id=owner.id,
            job_id=job.id,
            status=ApplicationStatus.APPLIED,
            next_action="Follow up with the recruiter",
            next_action_due_at=now + timedelta(hours=12),
        )
        ApplicationReminderRepository(session).reconcile(
            now=now,
            upcoming_before=now + timedelta(hours=24),
            limit=100,
        )

    app = create_app(Settings(_env_file=None))
    app.state.database = database
    app.dependency_overrides[get_required_principal] = lambda: principal_for(owner)
    return app, TestClient(app), owner, other, application


def test_reminders_require_authentication():
    response = TestClient(create_app(Settings(_env_file=None))).get("/api/v1/reminders")

    assert response.status_code == 401
    assert response.json()["code"] == "authentication_required"


def test_reminders_are_owner_scoped_and_include_application_context():
    app, client, owner, other, application = make_client()

    listed = client.get("/api/v1/reminders")

    assert listed.status_code == 200
    item = listed.json()["items"][0]
    assert item["application_id"] == str(application.id)
    assert item["application_status"] == "Applied"
    assert item["next_action"] == "Follow up with the recruiter"
    assert item["job"]["title"] == "Platform Engineer"

    app.dependency_overrides[get_required_principal] = lambda: principal_for(other)
    assert client.get("/api/v1/reminders").json() == {"items": []}

    app.dependency_overrides[get_required_principal] = lambda: principal_for(owner)


def test_reminder_can_be_read_and_dismissed():
    _, client, _, _, _ = make_client()
    reminder_id = client.get("/api/v1/reminders").json()["items"][0]["id"]

    read = client.patch(
        f"/api/v1/reminders/{reminder_id}",
        json={"status": "read"},
    )
    assert read.status_code == 200
    assert read.json()["status"] == "read"
    assert read.json()["read_at"] is not None

    dismissed = client.patch(
        f"/api/v1/reminders/{reminder_id}",
        json={"status": "dismissed"},
    )
    assert dismissed.status_code == 200
    assert dismissed.json()["status"] == "dismissed"
    assert dismissed.json()["dismissed_at"] is not None
    assert client.get("/api/v1/reminders").json() == {"items": []}


def test_another_user_cannot_change_a_reminder():
    app, client, _, other, _ = make_client()
    reminder_id = client.get("/api/v1/reminders").json()["items"][0]["id"]
    app.dependency_overrides[get_required_principal] = lambda: principal_for(other)

    response = client.patch(
        f"/api/v1/reminders/{reminder_id}",
        json={"status": "read"},
    )

    assert response.status_code == 404
    assert response.json()["code"] == "application_reminder_not_found"

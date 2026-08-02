from fastapi.testclient import TestClient
from uuid import UUID

from api.application import create_app
from api.dependencies import get_required_principal
from core.config import Settings
from database.base import Base
from database.repositories.applications import ApplicationRepository
from database.repositories.jobs import JobRepository
from database.repositories.resumes import ResumeRepository
from database.repositories.users import UserRepository
from database.session import Database
from models.identity import AuthenticatedPrincipal
from models.job import Job
from models.resume import Resume


def make_principal(user) -> AuthenticatedPrincipal:
    return AuthenticatedPrincipal(
        user_id=user.id,
        issuer="https://identity.example.test/",
        subject=f"subject-{user.id}",
        email=user.email,
        name=user.name,
    )


def make_authenticated_client():
    database = Database("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(database.engine)
    with database.session() as session:
        users = UserRepository(session)
        owner = users.create(email="owner@example.com", name="Owner")
        other = users.create(email="other@example.com", name="Other")
        job = JobRepository(session).upsert(
            Job(
                title="Platform Engineer",
                company="Example Corp",
                location="Remote",
                description="Build reliable Python services.",
                url="https://example.com/jobs/platform",
            )
        )
        owner_resume = ResumeRepository(session).save_version(
            user_id=owner.id,
            resume=Resume(name="Owner", raw_text="Platform engineer"),
        )
        other_resume = ResumeRepository(session).save_version(
            user_id=other.id,
            resume=Resume(name="Other", raw_text="Other engineer"),
        )

    application = create_app(Settings(_env_file=None))
    application.state.database = database
    application.dependency_overrides[get_required_principal] = lambda: make_principal(owner)
    return (
        application,
        TestClient(application),
        database,
        owner,
        other,
        job,
        owner_resume,
        other_resume,
    )


def test_applications_require_authentication():
    application = create_app(Settings(_env_file=None))

    response = TestClient(application).get("/api/v1/applications")

    assert response.status_code == 401
    assert response.json()["code"] == "authentication_required"
    assert response.headers["www-authenticate"] == "Bearer"


def test_application_create_list_detail_and_transition_are_owner_scoped():
    (
        application,
        client,
        _,
        owner,
        other,
        job,
        owner_resume,
        _,
    ) = make_authenticated_client()

    created = client.post(
        "/api/v1/applications",
        json={
            "job_id": str(job.id),
            "resume_id": str(owner_resume.resume.id),
            "notes": "Tailor the impact bullets.",
            "next_action": "Review the job evidence",
        },
    )
    assert created.status_code == 201
    payload = created.json()
    application_id = payload["id"]
    assert payload["job"]["id"] == str(job.id)
    assert payload["status"] == "Preparing"
    assert payload["allowed_next_statuses"] == ["Ready to apply", "Withdrawn"]
    assert payload["events"][0]["previous_status"] is None
    assert payload["events"][0]["new_status"] == "Preparing"

    listed = client.get("/api/v1/applications")
    assert listed.status_code == 200
    assert [item["id"] for item in listed.json()["items"]] == [application_id]
    assert "events" not in listed.json()["items"][0]

    detail = client.get(f"/api/v1/applications/{application_id}")
    assert detail.status_code == 200
    assert len(detail.json()["events"]) == 1

    transitioned = client.patch(
        f"/api/v1/applications/{application_id}/status",
        json={
            "status": "Ready to apply",
            "note": "Evidence reviewed by the user.",
            "next_action": "Open the verified employer page",
        },
    )
    assert transitioned.status_code == 200
    assert transitioned.json()["status"] == "Ready to apply"
    assert transitioned.json()["allowed_next_statuses"] == ["Applied", "Withdrawn"]
    assert [event["new_status"] for event in transitioned.json()["events"]] == [
        "Preparing",
        "Ready to apply",
    ]

    application.dependency_overrides[get_required_principal] = lambda: make_principal(other)
    assert client.get("/api/v1/applications").json() == {"items": []}
    hidden_detail = client.get(f"/api/v1/applications/{application_id}")
    assert hidden_detail.status_code == 404
    hidden_transition = client.patch(
        f"/api/v1/applications/{application_id}/status",
        json={"status": "Applied"},
    )
    assert hidden_transition.status_code == 404

    application.dependency_overrides[get_required_principal] = lambda: make_principal(owner)
    assert client.get(f"/api/v1/applications/{application_id}").status_code == 200


def test_invalid_transition_is_stable_and_does_not_append_an_event():
    _, client, database, owner, _, job, _, _ = make_authenticated_client()
    created = client.post(
        "/api/v1/applications",
        json={"job_id": str(job.id)},
    ).json()

    response = client.patch(
        f"/api/v1/applications/{created['id']}/status",
        json={"status": "Offer"},
    )

    assert response.status_code == 409
    assert response.json()["code"] == "invalid_application_transition"
    with database.session() as session:
        events = ApplicationRepository(session).events(
            user_id=owner.id,
            application_id=UUID(created["id"]),
        )
        assert len(events) == 1


def test_duplicate_job_and_unknown_dependencies_return_stable_errors():
    _, client, _, _, _, job, _, _ = make_authenticated_client()
    first = client.post(
        "/api/v1/applications",
        json={"job_id": str(job.id)},
    )
    assert first.status_code == 201

    duplicate = client.post(
        "/api/v1/applications",
        json={"job_id": str(job.id)},
    )
    assert duplicate.status_code == 409
    assert duplicate.json()["code"] == "application_already_exists"

    unknown_job = client.post(
        "/api/v1/applications",
        json={"job_id": "00000000-0000-0000-0000-000000000000"},
    )
    assert unknown_job.status_code == 404
    assert unknown_job.json()["code"] == "job_not_found"

    second_job_client = make_authenticated_client()
    second_client = second_job_client[1]
    second_job = second_job_client[5]
    foreign_resume = second_job_client[7]
    invalid_resume = second_client.post(
        "/api/v1/applications",
        json={
            "job_id": str(second_job.id),
            "resume_id": str(foreign_resume.resume.id),
        },
    )
    assert invalid_resume.status_code == 404
    assert invalid_resume.json()["code"] == "resume_not_found"


def test_transition_to_applied_sets_timestamp_and_preserves_audit_history():
    _, client, _, _, _, job, _, _ = make_authenticated_client()
    created = client.post(
        "/api/v1/applications",
        json={"job_id": str(job.id)},
    ).json()
    application_id = created["id"]

    ready = client.patch(
        f"/api/v1/applications/{application_id}/status",
        json={"status": "Ready to apply"},
    )
    assert ready.status_code == 200
    applied = client.patch(
        f"/api/v1/applications/{application_id}/status",
        json={"status": "Applied", "note": "Submitted after final review."},
    )

    assert applied.status_code == 200
    assert applied.json()["applied_at"] is not None
    assert [event["new_status"] for event in applied.json()["events"]] == [
        "Preparing",
        "Ready to apply",
        "Applied",
    ]
    assert applied.json()["events"][-1]["note"] == "Submitted after final review."

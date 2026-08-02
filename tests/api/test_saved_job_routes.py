from fastapi.testclient import TestClient

from api.application import create_app
from api.dependencies import get_required_principal
from core.config import Settings
from database.base import Base
from database.repositories.jobs import JobRepository
from database.repositories.users import UserRepository
from database.session import Database
from models.identity import AuthenticatedPrincipal
from models.job import Job


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

    application = create_app(Settings(_env_file=None))
    application.state.database = database
    application.dependency_overrides[get_required_principal] = lambda: make_principal(owner)
    return application, TestClient(application), owner, other, job


def test_saved_jobs_require_authentication():
    application = create_app(Settings(_env_file=None))

    response = TestClient(application).get("/api/v1/saved-jobs")

    assert response.status_code == 401
    assert response.json()["code"] == "authentication_required"
    assert response.headers["www-authenticate"] == "Bearer"


def test_saved_job_crud_is_idempotent_and_owner_scoped():
    application, client, owner, other, job = make_authenticated_client()

    created = client.put(
        f"/api/v1/saved-jobs/{job.id}",
        json={"notes": "Review after work"},
    )
    assert created.status_code == 200
    assert created.json()["job"]["id"] == str(job.id)
    assert created.json()["notes"] == "Review after work"

    updated = client.put(
        f"/api/v1/saved-jobs/{job.id}",
        json={"notes": "Priority role"},
    )
    assert updated.status_code == 200
    assert updated.json()["notes"] == "Priority role"
    assert updated.json()["created_at"] == created.json()["created_at"]

    listed = client.get("/api/v1/saved-jobs")
    assert listed.status_code == 200
    assert [item["job"]["id"] for item in listed.json()["items"]] == [str(job.id)]

    application.dependency_overrides[get_required_principal] = lambda: make_principal(other)
    other_list = client.get("/api/v1/saved-jobs")
    assert other_list.status_code == 200
    assert other_list.json() == {"items": []}

    hidden_remove = client.delete(f"/api/v1/saved-jobs/{job.id}")
    assert hidden_remove.status_code == 404
    assert hidden_remove.json()["code"] == "saved_job_not_found"

    application.dependency_overrides[get_required_principal] = lambda: make_principal(owner)
    removed = client.delete(f"/api/v1/saved-jobs/{job.id}")
    assert removed.status_code == 204
    assert removed.content == b""
    assert client.get("/api/v1/saved-jobs").json() == {"items": []}


def test_saving_unknown_job_returns_stable_not_found_error():
    _, client, _, _, _ = make_authenticated_client()

    response = client.put(
        "/api/v1/saved-jobs/00000000-0000-0000-0000-000000000000",
        json={},
    )

    assert response.status_code == 404
    assert response.json() == {
        "code": "job_not_found",
        "message": "The requested job was not found.",
    }


def test_saved_job_notes_are_bounded():
    _, client, _, _, job = make_authenticated_client()

    response = client.put(
        f"/api/v1/saved-jobs/{job.id}",
        json={"notes": "x" * 2_001},
    )

    assert response.status_code == 422
    assert response.json()["code"] == "request_validation_failed"

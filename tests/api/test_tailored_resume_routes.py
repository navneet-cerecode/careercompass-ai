from fastapi.testclient import TestClient

from api.application import create_app
from api.dependencies import get_required_principal
from core.config import Settings
from database.base import Base
from database.models.subscriptions import SubscriptionRecord
from database.repositories.jobs import JobRepository
from database.repositories.resumes import ResumeRepository
from database.repositories.users import UserRepository
from database.session import Database
from models.enums import SubscriptionPlan, SubscriptionStatus
from models.identity import AuthenticatedPrincipal
from models.job import Job
from models.resume import Resume
from models.skill import Skill


def principal_for(user) -> AuthenticatedPrincipal:
    return AuthenticatedPrincipal(
        user_id=user.id,
        issuer="https://identity.example.test/",
        subject=f"subject-{user.id}",
        email=user.email,
        name=user.name,
    )


def build_fixture():
    database = Database("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(database.engine)
    with database.session() as session:
        users = UserRepository(session)
        owner = users.create(email="owner@example.com", name="Owner")
        other = users.create(email="other@example.com", name="Other")
        ResumeRepository(session).save_version(
            user_id=owner.id,
            resume=Resume(
                name="Owner",
                email="owner@example.com",
                raw_text="Excel operations coordinator",
                skills=[Skill(name="Communication"), Skill(name="Excel")],
                experience=["Coordinated meetings.", "Built Excel inventory reports."],
                projects=["Created a weekly stock forecast."],
                education=["Bachelor of Commerce"],
            ),
        )
        job = JobRepository(session).upsert(
            Job(
                title="Operations Manager",
                company="Example Ltd",
                location="India",
                description="Manage inventory operations using Excel.",
                required_skills=[Skill(name="Excel"), Skill(name="Inventory Planning")],
                url="https://example.com/jobs/operations",
            )
        )
        session.add(
            SubscriptionRecord(
                user_id=owner.id,
                plan=SubscriptionPlan.PRO.value,
                status=SubscriptionStatus.ACTIVE.value,
                cancel_at_period_end=False,
            )
        )

    application = create_app(Settings(_env_file=None))
    application.state.database = database
    application.dependency_overrides[get_required_principal] = lambda: principal_for(owner)
    return TestClient(application), application, owner, other, job


def create_plan_and_draft(client: TestClient, job_id) -> tuple[dict, dict]:
    plan_response = client.post("/api/v1/tailoring-plans", json={"job_id": str(job_id)})
    assert plan_response.status_code == 201
    draft_response = client.post(
        "/api/v1/tailored-resumes",
        json={"plan_id": plan_response.json()["id"]},
    )
    assert draft_response.status_code == 201
    return plan_response.json(), draft_response.json()


def test_review_version_approval_and_export_workflow():
    client, _, _, _, job = build_fixture()
    _, first = create_plan_and_draft(client, job.id)

    repeated = client.post(
        "/api/v1/tailored-resumes",
        json={"plan_id": first["plan_id"]},
    )
    assert repeated.json()["id"] == first["id"]
    assert first["version"] == 1
    assert first["accepted"]["experience"][0] == "Built Excel inventory reports."
    assert first["verification_status"] == "pending_review"

    blocked_export = client.get(f"/api/v1/tailored-resumes/{first['id']}/export?format=pdf")
    assert blocked_export.status_code == 409
    assert blocked_export.json()["code"] == "tailored_resume_review_required"

    revision = client.post(
        f"/api/v1/tailored-resumes/{first['id']}/revisions",
        json={
            "skills": "suggested",
            "experience": "original",
            "projects": "suggested",
        },
    )
    assert revision.status_code == 201
    second = revision.json()
    assert second["version"] == 2
    assert second["accepted"]["experience"][0] == "Coordinated meetings."

    stale = client.post(
        f"/api/v1/tailored-resumes/{first['id']}/revisions",
        json={"skills": "original", "experience": "original", "projects": "original"},
    )
    assert stale.status_code == 409

    versions = client.get(f"/api/v1/tailored-resumes/{second['id']}/versions")
    assert versions.status_code == 200
    assert [item["version"] for item in versions.json()["items"]] == [2, 1]

    invalid_confirmation = client.post(
        f"/api/v1/tailored-resumes/{second['id']}/approve",
        json={"confirm_factual_accuracy": False},
    )
    assert invalid_confirmation.status_code == 422

    approved = client.post(
        f"/api/v1/tailored-resumes/{second['id']}/approve",
        json={"confirm_factual_accuracy": True},
    )
    assert approved.status_code == 200
    assert approved.json()["verification_status"] == "user_verified"
    assert approved.json()["user_review_required"] is False

    pdf = client.get(f"/api/v1/tailored-resumes/{second['id']}/export?format=pdf")
    docx = client.get(f"/api/v1/tailored-resumes/{second['id']}/export?format=docx")
    assert pdf.status_code == 200
    assert pdf.content.startswith(b"%PDF")
    assert pdf.headers["content-disposition"].endswith('.pdf"')
    assert docx.status_code == 200
    assert docx.content.startswith(b"PK")
    assert docx.headers["content-disposition"].endswith('.docx"')


def test_tailored_resume_versions_are_owner_scoped():
    client, application, _, other, job = build_fixture()
    _, draft = create_plan_and_draft(client, job.id)
    application.dependency_overrides[get_required_principal] = lambda: principal_for(other)

    response = client.get(f"/api/v1/tailored-resumes/{draft['id']}")

    assert response.status_code == 404
    assert response.json()["code"] == "tailored_resume_not_found"

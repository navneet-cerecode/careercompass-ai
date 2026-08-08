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


def build_fixture(*, pro: bool):
    database = Database("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(database.engine)
    with database.session() as session:
        users = UserRepository(session)
        owner = users.create(email="owner@example.com", name="Owner")
        other = users.create(email="other@example.com", name="Other")
        resume = (
            ResumeRepository(session)
            .save_version(
                user_id=owner.id,
                resume=Resume(
                    name="Owner",
                    raw_text="Excel operations coordinator",
                    skills=[Skill(name="Communication"), Skill(name="Excel")],
                    experience=[
                        "Coordinated team meetings.",
                        "Built Excel inventory reports.",
                    ],
                ),
            )
            .resume
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
        if pro:
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
    return TestClient(application), application, owner, other, resume, job


def test_pro_account_creates_and_reads_idempotent_factual_plan():
    client, _, _, _, resume, job = build_fixture(pro=True)

    created = client.post("/api/v1/tailoring-plans", json={"job_id": str(job.id)})
    repeated = client.post("/api/v1/tailoring-plans", json={"job_id": str(job.id)})

    assert created.status_code == 201
    assert repeated.status_code == 201
    payload = created.json()
    assert repeated.json()["id"] == payload["id"]
    assert payload["source_resume_id"] == str(resume.id)
    assert [skill["name"] for skill in payload["skills"]] == ["Excel", "Communication"]
    assert [skill["name"] for skill in payload["missing_skills"]] == ["Inventory Planning"]
    assert "Inventory Planning" not in [skill["name"] for skill in payload["skills"]]
    assert payload["experience"][0] == "Built Excel inventory reports."
    assert payload["user_review_required"] is True

    loaded = client.get(f"/api/v1/tailoring-plans/{payload['id']}")
    assert loaded.status_code == 200
    assert loaded.json() == payload


def test_free_beta_account_can_create_tailoring_plan():
    client, _, _, _, _, job = build_fixture(pro=False)

    response = client.post("/api/v1/tailoring-plans", json={"job_id": str(job.id)})

    assert response.status_code == 201
    assert response.json()["job_id"] == str(job.id)


def test_tailoring_plan_is_not_visible_to_another_account():
    client, application, _, other, _, job = build_fixture(pro=True)
    created = client.post("/api/v1/tailoring-plans", json={"job_id": str(job.id)})
    plan_id = created.json()["id"]
    application.dependency_overrides[get_required_principal] = lambda: principal_for(other)

    response = client.get(f"/api/v1/tailoring-plans/{plan_id}")

    assert response.status_code == 404
    assert response.json()["code"] == "tailoring_plan_not_found"


def test_tailoring_plan_requires_authentication():
    client = TestClient(create_app(Settings(_env_file=None)))

    response = client.post(
        "/api/v1/tailoring-plans",
        json={"job_id": "00000000-0000-0000-0000-000000000000"},
    )

    assert response.status_code == 401
    assert response.json()["code"] == "authentication_required"

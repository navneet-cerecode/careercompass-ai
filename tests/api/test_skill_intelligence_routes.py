from fastapi.testclient import TestClient

from api.application import create_app
from api.dependencies import get_required_principal
from core.config import Settings
from database.base import Base
from database.repositories.applications import ApplicationRepository, SavedJobRepository
from database.repositories.jobs import JobRepository
from database.repositories.resumes import ResumeRepository
from database.repositories.users import UserRepository
from database.session import Database
from models.enums import ApplicationStatus
from models.identity import AuthenticatedPrincipal
from models.job import Job
from models.resume import Resume
from models.skill import Skill


def _principal(user) -> AuthenticatedPrincipal:
    return AuthenticatedPrincipal(
        user_id=user.id,
        issuer="https://identity.example.test/",
        subject=f"subject-{user.id}",
        email=user.email,
        name=user.name,
    )


def _client():
    database = Database("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(database.engine)
    with database.session() as session:
        owner = UserRepository(session).create(email="owner@example.com", name="Owner")
        other = UserRepository(session).create(email="other@example.com", name="Other")
        resume = ResumeRepository(session).save_version(
            user_id=owner.id,
            resume=Resume(
                name="Owner",
                raw_text="Operations leader with communication and inventory experience.",
                skills=[
                    Skill(name="Communication", category="People"),
                    Skill(name="Inventory management", category="Operations"),
                    Skill(name="MS Excel", category="Tools"),
                ],
            ),
        )
        jobs = JobRepository(session)
        operations = jobs.upsert(
            Job(
                title="Operations Manager",
                company="Northstar Foods",
                location="Pune",
                description="Lead warehouse operations and suppliers.",
                required_skills=[
                    Skill(name="Communication", category="People"),
                    Skill(name="Vendor relations", category="Operations"),
                ],
                url="https://example.com/operations",
            )
        )
        supply = jobs.upsert(
            Job(
                title="Supply Coordinator",
                company="Fieldstone Retail",
                location="Mumbai",
                description="Coordinate inventory and supplier relationships.",
                required_skills=[
                    Skill(name="Inventory management", category="Operations"),
                    Skill(name="Microsoft Excel", category="Tools"),
                    Skill(name="Vendor relations", category="Operations"),
                ],
                url="https://example.com/supply",
            )
        )
        unrelated = jobs.upsert(
            Job(
                title="Software Engineer",
                company="Outside History",
                location="Remote",
                description="Build software.",
                required_skills=[Skill(name="Python", category="Technology")],
                url="https://example.com/software",
            )
        )
        ApplicationRepository(session).create(
            user_id=owner.id,
            job_id=operations.id,
            status=ApplicationStatus.PREPARING,
            resume_id=resume.resume.id,
        )
        SavedJobRepository(session).save(user_id=owner.id, job_id=supply.id)

    app = create_app(Settings(_env_file=None))
    app.state.database = database
    app.dependency_overrides[get_required_principal] = lambda: _principal(owner)
    return app, TestClient(app), owner, other, unrelated


def test_skill_intelligence_is_cross_industry_evidence_only_and_owner_scoped():
    app, client, owner, other, _ = _client()

    response = client.get("/api/v1/skill-intelligence")

    assert response.status_code == 200
    payload = response.json()
    assert payload["roles_analyzed"] == 2
    assert payload["roles_with_skill_data"] == 2
    assert payload["saved_roles"] == 1
    assert payload["application_roles"] == 1
    assert payload["history_window"]["first_observed_at"] is not None
    assert payload["history_window"]["last_observed_at"] is not None
    assert payload["history_window"]["observed_last_7_days"] == 2
    assert payload["history_window"]["observed_8_to_30_days"] == 0
    assert payload["history_window"]["observed_over_30_days"] == 0
    assert {cluster["label"] for cluster in payload["role_clusters"]} == {
        "Operations Manager",
        "Supply Coordinator",
    }
    assert {cluster["basis"] for cluster in payload["role_clusters"]} == {"role_title"}
    by_name = {item["name"]: item for item in payload["skills"]}
    assert by_name["Communication"]["status"] == "supported"
    assert by_name["Communication"]["match_confidence"] == "exact"
    assert by_name["Inventory Management"]["status"] == "supported"
    assert by_name["MS Excel"]["status"] == "supported"
    assert by_name["MS Excel"]["match_confidence"] == "curated_high"
    assert by_name["MS Excel"]["matched_terms"] == ["MS Excel", "Microsoft Excel"]
    assert by_name["Vendor Relations"]["status"] == "develop"
    assert by_name["Vendor Relations"]["observed_role_count"] == 2
    assert "Python" not in by_name

    app.dependency_overrides[get_required_principal] = lambda: _principal(other)
    hidden = client.get("/api/v1/skill-intelligence")
    assert hidden.status_code == 200
    assert hidden.json()["roles_analyzed"] == 0
    assert hidden.json()["resume_id"] is None
    assert hidden.json()["role_clusters"] == []
    assert hidden.json()["history_window"]["last_observed_at"] is None

    app.dependency_overrides[get_required_principal] = lambda: _principal(owner)


def test_skill_intelligence_requires_authentication():
    app = create_app(Settings(_env_file=None))

    response = TestClient(app).get("/api/v1/skill-intelligence")

    assert response.status_code == 401
    assert response.json()["code"] == "authentication_required"

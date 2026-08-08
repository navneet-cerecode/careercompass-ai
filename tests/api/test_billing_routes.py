from fastapi.testclient import TestClient

from api.application import create_app
from api.dependencies import get_required_principal
from core.config import Settings
from database.base import Base
from database.repositories.users import UserRepository
from database.session import Database
from models.identity import AuthenticatedPrincipal


def test_billing_summary_is_authenticated_and_owner_scoped():
    database = Database("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(database.engine)
    with database.session() as session:
        user = UserRepository(session).create(email="owner@example.com", name="Owner")
    principal = AuthenticatedPrincipal(
        user_id=user.id,
        issuer="https://identity.example.test/",
        subject="owner-subject",
        email=user.email,
        name=user.name,
    )
    application = create_app(Settings(_env_file=None))
    application.state.database = database
    application.dependency_overrides[get_required_principal] = lambda: principal

    response = TestClient(application).get("/api/v1/billing/summary")

    assert response.status_code == 200
    assert response.json() == {
        "plan": "free",
        "status": "active",
        "provider": None,
        "current_period_end": None,
        "cancel_at_period_end": False,
        "entitlements": {
            "job_discovery": True,
            "explainable_recommendations": True,
            "tailored_documents": False,
            "application_tracking": True,
            "reminders": True,
        },
        "checkout_available": False,
    }


def test_billing_summary_requires_authentication():
    response = TestClient(create_app(Settings(_env_file=None))).get("/api/v1/billing/summary")

    assert response.status_code == 401
    assert response.json()["code"] == "authentication_required"

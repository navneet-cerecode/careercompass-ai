from uuid import uuid4

from fastapi.testclient import TestClient

from api.application import create_app
from api.dependencies import get_required_principal
from core.config import Settings
from database.base import Base
from database.session import Database
from models.identity import AuthenticatedPrincipal
from models.identity import VerifiedIdentity
from services.auth.oidc import IdentityProviderUnavailableError, TokenValidationError


def test_current_account_requires_authentication():
    application = create_app(Settings(_env_file=None))

    response = TestClient(application).get("/api/v1/auth/me")

    assert response.status_code == 401
    assert response.json()["code"] == "authentication_required"
    assert response.headers["www-authenticate"] == "Bearer"


def test_current_account_returns_only_safe_profile_fields():
    application = create_app(Settings(_env_file=None))
    principal = AuthenticatedPrincipal(
        user_id=uuid4(),
        issuer="https://identity.example.test/",
        subject="provider-subject",
        email="ada@example.com",
        name="Ada Lovelace",
    )
    application.dependency_overrides[get_required_principal] = lambda: principal

    response = TestClient(application).get("/api/v1/auth/me")

    assert response.status_code == 200
    assert response.json() == {
        "id": str(principal.user_id),
        "email": "ada@example.com",
        "name": "Ada Lovelace",
    }


def test_bearer_token_fails_closed_when_authentication_is_unconfigured():
    application = create_app(Settings(_env_file=None))

    response = TestClient(application).get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer opaque-token"},
    )

    assert response.status_code == 503
    assert response.json()["code"] == "authentication_not_configured"


def test_verified_bearer_identity_is_provisioned_idempotently(tmp_path):
    database_url = f"sqlite+pysqlite:///{tmp_path / 'auth.db'}"
    database = Database(database_url)
    Base.metadata.create_all(database.engine)
    application = create_app(
        Settings(
            _env_file=None,
            database_url=database_url,
            auth_issuer="https://identity.example.test/",
            auth_audience="careercompass-api",
            auth_jwks_url="https://identity.example.test/jwks.json",
        )
    )

    class StubVerifier:
        def verify(self, token):
            assert token == "verified-token"
            return VerifiedIdentity(
                issuer="https://identity.example.test/",
                subject="verified-subject",
                email="ada@example.com",
                name="Ada Lovelace",
            )

    application.state.oidc_verifier = StubVerifier()
    client = TestClient(application)
    headers = {"Authorization": "Bearer verified-token"}

    first = client.get("/api/v1/auth/me", headers=headers)
    repeated = client.get("/api/v1/auth/me", headers=headers)

    assert first.status_code == 200
    assert repeated.status_code == 200
    assert repeated.json()["id"] == first.json()["id"]


def test_invalid_bearer_token_uses_generic_challenge(tmp_path):
    database_url = f"sqlite+pysqlite:///{tmp_path / 'invalid-auth.db'}"
    database = Database(database_url)
    Base.metadata.create_all(database.engine)
    application = create_app(
        Settings(
            _env_file=None,
            database_url=database_url,
            auth_issuer="https://identity.example.test/",
            auth_audience="careercompass-api",
            auth_jwks_url="https://identity.example.test/jwks.json",
        )
    )

    class RejectingVerifier:
        def verify(self, _token):
            raise TokenValidationError("sensitive validation detail")

    application.state.oidc_verifier = RejectingVerifier()
    response = TestClient(application).get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer invalid-token"},
    )

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"
    assert response.json()["code"] == "invalid_access_token"
    assert "sensitive" not in response.text


def test_identity_provider_outage_is_retryable_not_an_invalid_session(tmp_path):
    database_url = f"sqlite+pysqlite:///{tmp_path / 'unavailable-auth.db'}"
    database = Database(database_url)
    Base.metadata.create_all(database.engine)
    application = create_app(
        Settings(
            _env_file=None,
            database_url=database_url,
            auth_issuer="https://identity.example.test/",
            auth_audience="careercompass-api",
            auth_jwks_url="https://identity.example.test/jwks.json",
        )
    )

    class UnavailableVerifier:
        def verify(self, _token):
            raise IdentityProviderUnavailableError("sensitive outage detail")

    application.state.oidc_verifier = UnavailableVerifier()
    response = TestClient(application).get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer valid-looking-token"},
    )

    assert response.status_code == 503
    assert response.headers["retry-after"] == "5"
    assert response.json() == {
        "code": "identity_provider_unavailable",
        "message": "Sign-in verification is temporarily unavailable. Try again shortly.",
    }
    assert "sensitive" not in response.text

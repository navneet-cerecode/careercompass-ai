from fastapi.testclient import TestClient

from api.application import create_app
from api.dependencies import get_optional_principal, get_required_principal
from core.config import Settings
from database.base import Base
from database.repositories.users import UserRepository
from database.session import Database
from models.identity import AuthenticatedPrincipal


def make_client(max_bytes: int = 1024) -> TestClient:
    settings = Settings(max_resume_upload_bytes=max_bytes, _env_file=None)
    return TestClient(create_app(settings))


def test_parse_text_resume_returns_typed_profile_and_source_text():
    response = make_client().post(
        "/api/v1/resumes/parse",
        files={
            "file": (
                "ada.txt",
                b"Ada Lovelace\nada@example.com\nPython and SQL",
                "text/plain",
            )
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["resume"]["name"] == "Ada Lovelace"
    assert payload["resume"]["email"] == "ada@example.com"
    assert [skill["name"] for skill in payload["resume"]["skills"]] == [
        "Python",
        "SQL",
    ]
    assert payload["raw_text"].startswith("Ada Lovelace")


def test_parse_resume_rejects_unsupported_extension():
    response = make_client().post(
        "/api/v1/resumes/parse",
        files={"file": ("resume.rtf", b"resume", "application/rtf")},
    )

    assert response.status_code == 415
    assert response.json()["code"] == "unsupported_resume_type"


def test_parse_resume_rejects_content_type_mismatch():
    response = make_client().post(
        "/api/v1/resumes/parse",
        files={"file": ("resume.pdf", b"%PDF-data", "text/plain")},
    )

    assert response.status_code == 415
    assert response.json()["code"] == "resume_type_mismatch"


def test_parse_resume_rejects_oversized_upload():
    response = make_client(max_bytes=4).post(
        "/api/v1/resumes/parse",
        files={"file": ("resume.txt", b"Ada Lovelace", "text/plain")},
    )

    assert response.status_code == 413
    assert response.json() == {
        "code": "resume_too_large",
        "message": "Resume files cannot exceed 4 bytes.",
    }


def test_parse_resume_rejects_binary_text():
    response = make_client().post(
        "/api/v1/resumes/parse",
        files={"file": ("resume.txt", b"Ada\x00Lovelace", "text/plain")},
    )

    assert response.status_code == 422
    assert response.json()["code"] == "invalid_resume"


def test_authenticated_parse_persists_only_the_owners_current_profile(tmp_path):
    database_url = f"sqlite+pysqlite:///{tmp_path / 'profiles.db'}"
    database = Database(database_url)
    Base.metadata.create_all(database.engine)
    with database.session() as session:
        users = UserRepository(session)
        owner = users.create(email="owner@example.com", name="Owner")
        other = users.create(email="other@example.com", name="Other")

    def principal_for(user):
        return AuthenticatedPrincipal(
            user_id=user.id,
            issuer="https://identity.example.test/",
            subject=f"subject-{user.id}",
            email=user.email,
            name=user.name,
        )

    application = create_app(
        Settings(
            _env_file=None,
            database_url=database_url,
            max_resume_upload_bytes=1024,
        )
    )
    owner_principal = principal_for(owner)
    application.dependency_overrides[get_optional_principal] = lambda: owner_principal
    application.dependency_overrides[get_required_principal] = lambda: owner_principal
    client = TestClient(application)

    parsed = client.post(
        "/api/v1/resumes/parse",
        files={
            "file": (
                "../ada.txt",
                b"Ada Lovelace\nada@example.com\nPython and SQL",
                "text/plain",
            )
        },
    )
    current = client.get("/api/v1/resumes/current")

    assert parsed.status_code == 200
    assert current.status_code == 200
    assert current.json()["id"] == parsed.json()["resume"]["id"]
    assert current.json()["name"] == "Ada Lovelace"
    assert "raw_text" not in current.json()

    other_principal = principal_for(other)
    application.dependency_overrides[get_required_principal] = lambda: other_principal
    assert client.get("/api/v1/resumes/current").status_code == 404

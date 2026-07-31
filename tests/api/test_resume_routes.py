from fastapi.testclient import TestClient

from api.application import create_app
from core.config import Settings


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

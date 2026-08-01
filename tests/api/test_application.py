from fastapi.testclient import TestClient

from api.application import create_app
from core.config import Settings


def make_client() -> TestClient:
    test_settings = Settings(
        app_name="CareerCompass Test API",
        version="2.0-test",
        _env_file=None,
    )
    return TestClient(create_app(test_settings))


def test_application_factory_exposes_versioned_openapi_contract():
    client = make_client()

    response = client.get("/openapi.json")

    assert response.status_code == 200
    document = response.json()
    assert document["info"]["title"] == "CareerCompass Test API"
    assert document["info"]["version"] == "2.0-test"
    assert "/api/v1/health/live" in document["paths"]
    assert "/api/v1/health/ready" in document["paths"]


def test_liveness_endpoint_does_not_require_external_credentials():
    response = make_client().get("/api/v1/health/live")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "CareerCompass Test API",
        "version": "2.0-test",
        "checks": {},
    }


def test_readiness_endpoint_reports_missing_required_dependencies():
    response = make_client().get("/api/v1/health/ready")

    assert response.status_code == 503
    assert response.json() == {
        "status": "not_ready",
        "service": "CareerCompass Test API",
        "version": "2.0-test",
        "checks": {
            "database": "not_configured",
            "broker": "not_configured",
            "task_capability": "ephemeral",
            "authentication": "optional_anonymous",
        },
    }


def test_unversioned_health_path_is_not_part_of_public_contract():
    response = make_client().get("/health")

    assert response.status_code == 404


def test_validation_errors_use_stable_contract_without_echoing_input():
    client = make_client()
    sensitive_value = "private resume content"

    response = client.post(
        f"/api/v1/resumes/parse?context={sensitive_value}",
    )

    assert response.status_code == 422
    payload = response.json()
    assert payload["code"] == "request_validation_failed"
    assert payload["details"][0]["location"] == ["body", "file"]
    assert sensitive_value not in response.text

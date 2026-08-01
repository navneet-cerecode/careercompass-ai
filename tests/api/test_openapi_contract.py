import json

from scripts.export_openapi import export_openapi


def test_exported_openapi_contract_contains_frontend_health_path(tmp_path):
    output_path = tmp_path / "openapi.json"

    export_openapi(output_path)

    contract = json.loads(output_path.read_text(encoding="utf-8"))
    assert "/api/v1/health/live" in contract["paths"]
    assert contract["paths"]["/api/v1/auth/me"]["get"]["security"] == [{"HTTPBearer": []}]
    assert contract["paths"]["/api/v1/jobs/search-tasks"]["post"]["security"] == [
        {},
        {"HTTPBearer": []},
    ]
    assert contract["info"]["title"] == "CareerCompass AI"
    assert "GROQ_API_KEY" not in output_path.read_text(encoding="utf-8")

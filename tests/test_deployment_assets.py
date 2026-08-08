from pathlib import Path

import yaml


def test_production_compose_uses_migration_gate_and_hardened_app_services():
    document = yaml.safe_load(Path("compose.production.yaml").read_text(encoding="utf-8"))
    services = document["services"]

    assert {"migrate", "api", "worker", "frontend"} <= set(services)
    assert services["api"]["depends_on"]["migrate"]["condition"] == (
        "service_completed_successfully"
    )
    assert services["worker"]["depends_on"]["migrate"]["condition"] == (
        "service_completed_successfully"
    )
    for name in ("api", "worker", "frontend"):
        assert services[name]["read_only"] is True
        assert "no-new-privileges:true" in services[name]["security_opt"]


def test_runtime_images_are_non_root_and_health_checked():
    api_dockerfile = Path("Dockerfile.api").read_text(encoding="utf-8")
    frontend_dockerfile = Path("frontend/Dockerfile").read_text(encoding="utf-8")

    assert "USER solarahire" in api_dockerfile
    assert "HEALTHCHECK" in api_dockerfile
    assert "HF_HOME=/tmp/huggingface" in api_dockerfile
    assert "SENTENCE_TRANSFORMERS_HOME=/tmp/sentence-transformers" in api_dockerfile
    assert "USER nextjs" in frontend_dockerfile
    assert "HEALTHCHECK" in frontend_dockerfile
    assert 'CMD ["node", "server.js"]' in frontend_dockerfile


def test_production_environment_template_contains_placeholders_not_live_credentials():
    template = Path(".env.production.example").read_text(encoding="utf-8")

    assert "APP_ENVIRONMENT=production" in template
    assert "replace-with-auth0-client-secret" in template
    assert "replace-with-groq-api-key" in template
    assert "solara-hire.example.auth0.com" in template

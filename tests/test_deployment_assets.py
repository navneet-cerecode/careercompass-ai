from pathlib import Path

import yaml


def test_production_compose_uses_migration_gate_and_hardened_app_services():
    document = yaml.safe_load(Path("compose.production.yaml").read_text(encoding="utf-8"))
    services = document["services"]

    assert {"migrate", "api", "worker", "frontend", "maintenance"} <= set(services)
    assert services["api"]["depends_on"]["migrate"]["condition"] == (
        "service_completed_successfully"
    )
    assert services["worker"]["depends_on"]["migrate"]["condition"] == (
        "service_completed_successfully"
    )
    assert services["frontend"]["environment"]["SOLARAHIRE_API_URL"] == "http://api:8000"
    assert services["maintenance"]["profiles"] == ["operations"]
    assert services["maintenance"]["restart"] == "no"
    assert services["worker"]["healthcheck"]["test"] == [
        "CMD",
        "python",
        "-m",
        "workers.healthcheck",
    ]
    for name in ("api", "worker", "frontend", "maintenance"):
        assert services[name]["read_only"] is True
        assert "no-new-privileges:true" in services[name]["security_opt"]
        assert services[name]["init"] is True


def test_runtime_images_are_non_root_and_health_checked():
    api_dockerfile = Path("Dockerfile.api").read_text(encoding="utf-8")
    frontend_dockerfile = Path("frontend/Dockerfile").read_text(encoding="utf-8")

    assert "USER solarahire" in api_dockerfile
    assert "HEALTHCHECK" in api_dockerfile
    assert "/api/v1/health/ready" in api_dockerfile
    assert "HF_HOME=/opt/huggingface" in api_dockerfile
    assert "SENTENCE_TRANSFORMERS_HOME=/opt/sentence-transformers" in api_dockerfile
    assert "EmbeddingService; EmbeddingService()" in api_dockerfile
    assert "HF_HUB_OFFLINE=1" in api_dockerfile
    assert "USER nextjs" in frontend_dockerfile
    assert "HEALTHCHECK" in frontend_dockerfile
    assert "ARG NODE_VERSION=24.12.0" in frontend_dockerfile
    assert 'CMD ["node", "server.js"]' in frontend_dockerfile


def test_production_image_uses_scoped_cpu_runtime_dependencies():
    api_dockerfile = Path("Dockerfile.api").read_text(encoding="utf-8")
    api_requirements = Path("requirements-api.txt").read_text(encoding="utf-8")
    production_requirements = Path("requirements-production.txt").read_text(encoding="utf-8")
    workflow = Path(".github/workflows/ci.yml").read_text(encoding="utf-8")

    assert "COPY requirements.txt requirements-production.txt" in api_dockerfile
    assert "-r requirements-production.txt" in api_requirements
    assert "-r requirements.txt" not in api_requirements
    assert "-c requirements.txt" in production_requirements
    assert "torch==2.12.1+cpu" in production_requirements
    assert "https://download.pytorch.org/whl/cpu" in production_requirements
    assert workflow.index("pip install -r requirements-worker.txt") < workflow.index(
        "pip install -r requirements.txt"
    )


def test_production_environment_template_contains_placeholders_not_live_credentials():
    template = Path(".env.production.example").read_text(encoding="utf-8")

    assert "APP_ENVIRONMENT=production" in template
    assert "SOLARAHIRE_API_URL=http://api:8000" in template
    assert "replace-with-auth0-client-secret" in template
    assert "replace-with-groq-api-key" in template
    assert "solara-hire.example.auth0.com" in template


def test_frontend_self_hosts_the_editorial_font():
    layout = Path("frontend/src/app/layout.tsx").read_text(encoding="utf-8")
    package = Path("frontend/package.json").read_text(encoding="utf-8")

    assert "@fontsource-variable/source-serif-4/wght.css" in layout
    assert "next/font/google" not in layout
    assert '"@fontsource-variable/source-serif-4": "5.3.0"' in package

from pathlib import Path


def test_settings_load_without_credentials(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    monkeypatch.delenv("RAPIDAPI_KEY", raising=False)
    from core.config import Settings

    settings = Settings(_env_file=None)

    assert settings.groq_api_key is None
    assert settings.rapidapi_key is None
    assert settings.groq_model == "llama-3.3-70b-versatile"
    assert settings.temperature == 0.2
    assert settings.max_tokens == 1024
    assert settings.max_jobs == 50
    assert settings.default_location == "India"


def test_settings_load_prefixed_llm_configuration(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "test-groq-key")
    monkeypatch.setenv("RAPIDAPI_KEY", "test-rapidapi-key")
    monkeypatch.setenv("GROQ_TEMPERATURE", "0.35")
    monkeypatch.setenv("GROQ_MAX_TOKENS", "2048")

    from core.config import Settings

    settings = Settings(_env_file=None)

    assert settings.groq_api_key is not None
    assert settings.groq_api_key.get_secret_value() == "test-groq-key"
    assert settings.rapidapi_key is not None
    assert settings.rapidapi_key.get_secret_value() == "test-rapidapi-key"
    assert settings.temperature == 0.35
    assert settings.max_tokens == 2048
    assert "test-groq-key" not in repr(settings)
    assert "test-rapidapi-key" not in repr(settings)


def test_environment_example_documents_required_credentials():
    content = Path(".env.example").read_text(encoding="utf-8")

    assert "GROQ_API_KEY=" in content
    assert "RAPIDAPI_KEY=" in content
    assert "GROQ_MODEL=" in content

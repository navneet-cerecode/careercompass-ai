import pytest


def test_groq_client_requires_key_only_when_constructed(monkeypatch):
    from services.llm import groq_client

    monkeypatch.setattr(
        groq_client.settings,
        "groq_api_key",
        None,
    )

    with pytest.raises(RuntimeError, match="Missing GROQ_API_KEY"):
        groq_client.GroqClient()

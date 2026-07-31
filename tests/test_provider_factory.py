import pytest
from pydantic import SecretStr

from services.job_discovery.providers.api_provider import APIProvider
from services.job_discovery.providers.jsearch_provider import JSearchProvider
from services.job_discovery.providers.provider_factory import ProviderFactory
from services.job_discovery.providers.workday_provider import WorkdayProvider


def test_provider_factory_creates_workday_provider():
    company = {
        "name": "Example",
        "platform": "workday",
        "api_url": "https://example.com/workday/jobs",
        "careers_url": "https://example.com/careers",
    }

    provider = ProviderFactory.create(company)

    assert isinstance(provider, WorkdayProvider)
    assert provider.company is company


def test_provider_factory_creates_api_provider_without_network(monkeypatch):
    from services.job_discovery.providers import jsearch_provider

    monkeypatch.setattr(
        jsearch_provider.settings,
        "rapidapi_key",
        SecretStr("test-rapidapi-key"),
    )
    company = {
        "name": "JSearch",
        "platform": "jsearch",
    }

    provider = ProviderFactory.create(company)

    assert isinstance(provider, APIProvider)
    assert isinstance(provider, JSearchProvider)
    assert provider.company is company


def test_provider_factory_keeps_legacy_api_platform_alias(monkeypatch):
    from services.job_discovery.providers import jsearch_provider

    monkeypatch.setattr(
        jsearch_provider.settings,
        "rapidapi_key",
        SecretStr("test-rapidapi-key"),
    )

    provider = ProviderFactory.create(
        {
            "name": "JSearch",
            "platform": "api",
        }
    )

    assert isinstance(provider, JSearchProvider)


def test_provider_factory_rejects_unknown_platform():
    with pytest.raises(ValueError, match="Unsupported platform"):
        ProviderFactory.create(
            {
                "name": "Unknown",
                "platform": "unknown",
            }
        )

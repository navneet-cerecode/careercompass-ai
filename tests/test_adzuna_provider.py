import pytest

from models.enums import EmploymentType, JobSource
from services.job_discovery.providers.adzuna_provider import AdzunaProvider
from services.job_discovery.providers.contracts import DatePosted, JobSearchQuery
from services.job_discovery.providers.errors import ProviderPayloadError


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload
        self.raise_called = False

    def raise_for_status(self):
        self.raise_called = True

    def json(self):
        return self.payload


def test_adzuna_search_normalizes_fixture_without_live_network(monkeypatch):
    response = FakeResponse(
        {
            "results": [
                {
                    "id": "123",
                    "title": "Operations Manager",
                    "company": {"display_name": "Example Ltd"},
                    "location": {"display_name": "Mumbai, India"},
                    "description": "Lead a regional operations team.",
                    "redirect_url": "https://www.adzuna.in/jobs/details/123",
                    "contract_time": "full_time",
                }
            ]
        }
    )
    captured = {}

    def fake_get(url, *, params, timeout):
        captured.update({"url": url, "params": params, "timeout": timeout})
        return response

    monkeypatch.setattr(
        "services.job_discovery.providers.adzuna_provider.requests.get",
        fake_get,
    )
    provider = AdzunaProvider(
        {"id": "adzuna", "name": "Adzuna", "platform": "adzuna", "country": "in"},
        app_id="test-id",
        app_key="test-key",
    )

    jobs = provider.search_jobs(
        JobSearchQuery(
            role="Operations Manager",
            location="Mumbai",
            country="IN",
            page=2,
            employment_types=[EmploymentType.FULL_TIME],
            date_posted=DatePosted.WEEK,
        )
    )

    assert response.raise_called is True
    assert captured["url"].endswith("/in/search/2")
    assert captured["params"]["app_id"] == "test-id"
    assert captured["params"]["app_key"] == "test-key"
    assert captured["params"]["max_days_old"] == 7
    assert captured["params"]["full_time"] == 1
    assert captured["timeout"] == 30
    assert jobs[0].source == JobSource.ADZUNA
    assert jobs[0].company == "Example Ltd"
    assert jobs[0].employment_type == EmploymentType.FULL_TIME


def test_adzuna_rejects_invalid_jobs_collection(monkeypatch):
    monkeypatch.setattr(
        "services.job_discovery.providers.adzuna_provider.requests.get",
        lambda *args, **kwargs: FakeResponse({"results": {}}),
    )
    provider = AdzunaProvider(
        {"id": "adzuna", "name": "Adzuna", "platform": "adzuna", "country": "in"},
        app_id="test-id",
        app_key="test-key",
    )

    with pytest.raises(ProviderPayloadError, match="invalid jobs collection"):
        provider.search_jobs(JobSearchQuery(role="Chef", location="India"))


def test_adzuna_rejects_job_without_redirect_url():
    provider = AdzunaProvider(
        {"id": "adzuna", "name": "Adzuna", "platform": "adzuna", "country": "in"},
        app_id="test-id",
        app_key="test-key",
    )

    with pytest.raises(ProviderPayloadError, match="application URL"):
        provider.normalize_job({"title": "Chef"})

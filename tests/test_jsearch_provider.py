import pytest

from models.enums import JobSource
from services.job_discovery.providers.contracts import DatePosted, JobSearchQuery
from services.job_discovery.providers.errors import ProviderPayloadError
from services.job_discovery.providers.jsearch_provider import JSearchProvider


class FakeResponse:
    def __init__(self, payload, status_code=200):
        self.payload = payload
        self.status_code = status_code
        self.raise_called = False

    def raise_for_status(self):
        self.raise_called = True

    def json(self):
        return self.payload


def test_jsearch_search_normalizes_fixture_without_live_network(monkeypatch):
    response = FakeResponse(
        {
            "data": {
                "jobs": [
                    {
                        "job_title": "Data Engineer",
                        "employer_name": "Example Corp",
                        "job_location": "Bengaluru, India",
                        "job_description": "Python and SQL",
                        "job_apply_link": "https://example.com/jobs/1",
                        "job_id": "search-specific-id",
                        "job_uid": "stable-job-uid",
                    }
                ]
            }
        }
    )
    captured = {}

    def fake_get(url, *, headers, params, timeout):
        captured.update(
            {
                "url": url,
                "headers": headers,
                "params": params,
                "timeout": timeout,
            }
        )
        return response

    monkeypatch.setattr(
        "services.job_discovery.providers.jsearch_provider.requests.get",
        fake_get,
    )
    provider = JSearchProvider(
        {
            "name": "JSearch",
            "country": "in",
        },
        api_key="test-key",
    )
    query = JobSearchQuery(
        role="Data Engineer",
        location="Bengaluru",
        country="US",
        page=2,
        date_posted=DatePosted.WEEK,
    )

    jobs = provider.search_jobs(query)

    assert response.raise_called is True
    assert captured["params"]["page"] == "2"
    assert captured["params"]["country"] == "us"
    assert captured["params"]["date_posted"] == "week"
    assert captured["timeout"] == 30
    assert len(jobs) == 1
    assert jobs[0].title == "Data Engineer"
    assert jobs[0].source == JobSource.JSEARCH
    assert jobs[0].external_id == "stable-job-uid"
    assert str(jobs[0].url) == "https://example.com/jobs/1"


def test_jsearch_rejects_invalid_jobs_collection(monkeypatch):
    monkeypatch.setattr(
        "services.job_discovery.providers.jsearch_provider.requests.get",
        lambda *args, **kwargs: FakeResponse({"data": {"jobs": {}}}),
    )
    provider = JSearchProvider({"name": "JSearch"}, api_key="test-key")

    with pytest.raises(ProviderPayloadError, match="invalid jobs collection"):
        provider.search_jobs(
            JobSearchQuery(
                role="Data Engineer",
                location="India",
            )
        )


def test_jsearch_rejects_invalid_data_object(monkeypatch):
    monkeypatch.setattr(
        "services.job_discovery.providers.jsearch_provider.requests.get",
        lambda *args, **kwargs: FakeResponse({"data": []}),
    )
    provider = JSearchProvider({"name": "JSearch"}, api_key="test-key")

    with pytest.raises(ProviderPayloadError, match="invalid data object"):
        provider.search_jobs(
            JobSearchQuery(
                role="Data Engineer",
                location="India",
            )
        )


def test_jsearch_rejects_job_without_apply_url():
    provider = JSearchProvider({"name": "JSearch"}, api_key="test-key")

    with pytest.raises(ProviderPayloadError, match="application URL"):
        provider.normalize_job(
            {
                "job_title": "Data Engineer",
            }
        )

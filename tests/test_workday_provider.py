import pytest

from models.enums import JobSource
from services.job_discovery.providers.contracts import JobSearchQuery
from services.job_discovery.providers.errors import ProviderPayloadError
from services.job_discovery.providers.workday_provider import WorkdayProvider


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload
        self.raise_called = False

    def raise_for_status(self):
        self.raise_called = True

    def json(self):
        return self.payload


def test_workday_search_normalizes_fixture_without_live_network(monkeypatch):
    response = FakeResponse(
        {
            "jobPostings": [
                {
                    "title": "Senior Data Engineer",
                    "locationsText": "India",
                    "externalPath": "/job/123",
                }
            ]
        }
    )
    captured = {}

    def fake_post(url, *, json, timeout):
        captured.update(
            {
                "url": url,
                "json": json,
                "timeout": timeout,
            }
        )
        return response

    monkeypatch.setattr(
        "services.job_discovery.providers.workday_provider.requests.post",
        fake_post,
    )
    provider = WorkdayProvider(
        {
            "id": "example",
            "name": "Example Corp",
            "api_url": "https://example.com/workday/jobs",
            "careers_url": "https://example.com/careers/",
        }
    )

    jobs = provider.search_jobs(
        JobSearchQuery(
            role="Data Engineer",
            location="India",
            page=2,
            page_size=10,
        )
    )

    assert response.raise_called is True
    assert captured["json"] == {
        "limit": 10,
        "offset": 10,
        "searchText": "Data Engineer",
    }
    assert captured["timeout"] == 30
    assert len(jobs) == 1
    assert jobs[0].company == "Example Corp"
    assert jobs[0].source == JobSource.WORKDAY
    assert str(jobs[0].url) == "https://example.com/careers/job/123"
    assert provider.provider_name == "workday:example"
    assert provider.capabilities.pagination is True


def test_workday_rejects_invalid_jobs_collection(monkeypatch):
    monkeypatch.setattr(
        "services.job_discovery.providers.workday_provider.requests.post",
        lambda *args, **kwargs: FakeResponse({"jobPostings": {}}),
    )
    provider = WorkdayProvider(
        {
            "id": "example",
            "name": "Example Corp",
            "api_url": "https://example.com/workday/jobs",
            "careers_url": "https://example.com/careers",
        }
    )

    with pytest.raises(ProviderPayloadError, match="invalid jobs collection"):
        provider.search_jobs(
            JobSearchQuery(
                role="Data Engineer",
                location="India",
            )
        )


def test_workday_excludes_jobs_outside_requested_location(monkeypatch):
    monkeypatch.setattr(
        "services.job_discovery.providers.workday_provider.requests.post",
        lambda *args, **kwargs: FakeResponse(
            {
                "jobPostings": [
                    {
                        "title": "Operations Manager",
                        "locationsText": "India, Bengaluru",
                        "externalPath": "/job/india/1",
                    },
                    {
                        "title": "Operations Manager",
                        "locationsText": "US, CA, Santa Clara",
                        "externalPath": "/job/us/2",
                    },
                ]
            }
        ),
    )
    provider = WorkdayProvider(
        {
            "id": "example",
            "name": "Example Corp",
            "api_url": "https://example.com/workday/jobs",
            "careers_url": "https://example.com/careers",
        }
    )

    jobs = provider.search_jobs(
        JobSearchQuery(role="Operations Manager", location="India", country="IN")
    )

    assert [job.location for job in jobs] == ["India, Bengaluru"]

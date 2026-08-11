import pytest

from models.enums import EmploymentType, ExperienceLevel, JobSource
from services.job_discovery.providers.contracts import JobSearchQuery
from services.job_discovery.providers.errors import ProviderPayloadError
from services.job_discovery.providers.greenhouse_provider import GreenhouseProvider


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload
        self.raise_called = False

    def raise_for_status(self):
        self.raise_called = True

    def json(self):
        return self.payload


def _job(job_id, title, location):
    return {
        "id": job_id,
        "title": title,
        "location": {"name": location},
        "content": "&lt;p&gt;Support customers &amp;amp; improve operations.&lt;/p&gt;",
        "absolute_url": f"https://job-boards.greenhouse.io/example/jobs/{job_id}",
    }


def _provider():
    return GreenhouseProvider(
        {
            "id": "example",
            "name": "Example Company",
            "platform": "greenhouse",
            "board_token": "example",
        }
    )


def test_greenhouse_filters_and_normalizes_public_board_jobs(monkeypatch):
    response = FakeResponse(
        {
            "jobs": [
                _job(1, "Senior Customer Success Manager", "Chennai, India"),
                _job(2, "Customer Success Manager", "New York, USA"),
                _job(3, "Software Engineer", "Chennai, India"),
            ]
        }
    )
    captured = {}

    def fake_get(url, *, params, timeout):
        captured.update(url=url, params=params, timeout=timeout)
        return response

    monkeypatch.setattr(
        "services.job_discovery.providers.greenhouse_provider.requests.get",
        fake_get,
    )

    jobs = _provider().search_jobs(
        JobSearchQuery(role="Customer Success Manager", location="India")
    )

    assert response.raise_called is True
    assert captured == {
        "url": "https://boards-api.greenhouse.io/v1/boards/example/jobs",
        "params": {"content": "true"},
        "timeout": 30,
    }
    assert len(jobs) == 1
    assert jobs[0].description == "Support customers & improve operations."
    assert jobs[0].experience_level == ExperienceLevel.SENIOR
    assert jobs[0].source == JobSource.GREENHOUSE
    assert jobs[0].source_name == "Greenhouse"


def test_greenhouse_accepts_remote_jobs_only_when_requested(monkeypatch):
    monkeypatch.setattr(
        "services.job_discovery.providers.greenhouse_provider.requests.get",
        lambda *args, **kwargs: FakeResponse(
            {"jobs": [_job(1, "Finance Associate", "India, Remote")]}
        ),
    )

    jobs = _provider().search_jobs(
        JobSearchQuery(role="Finance Associate", location="Remote", remote_only=True)
    )

    assert len(jobs) == 1
    assert jobs[0].employment_type == EmploymentType.REMOTE


def test_greenhouse_rejects_invalid_jobs_collection(monkeypatch):
    monkeypatch.setattr(
        "services.job_discovery.providers.greenhouse_provider.requests.get",
        lambda *args, **kwargs: FakeResponse({"jobs": {}}),
    )

    with pytest.raises(ProviderPayloadError, match="invalid jobs collection"):
        _provider().search_jobs(JobSearchQuery(role="Finance", location="India"))

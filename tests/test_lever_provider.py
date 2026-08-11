import pytest

from models.enums import EmploymentType, ExperienceLevel, JobSource
from services.job_discovery.providers.contracts import JobSearchQuery
from services.job_discovery.providers.errors import ProviderPayloadError
from services.job_discovery.providers.lever_provider import LeverProvider


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self.payload


def _job(
    job_id,
    title,
    location="Bengaluru, India",
    *,
    country="IN",
    workplace="onsite",
    commitment="Employee: Full Time",
):
    return {
        "id": job_id,
        "text": title,
        "country": country,
        "workplaceType": workplace,
        "categories": {
            "location": location,
            "allLocations": [location],
            "commitment": commitment,
        },
        "descriptionPlain": "Support customers & resolve payment issues.",
        "lists": [{"text": "Requirements", "content": "<li>Clear communication</li>"}],
        "additionalPlain": "Health insurance.",
        "hostedUrl": f"https://jobs.lever.co/example/{job_id}",
        "applyUrl": f"https://jobs.lever.co/example/{job_id}/apply",
    }


def _provider():
    return LeverProvider(
        {
            "id": "example",
            "name": "Example",
            "platform": "lever",
            "site_name": "example",
        }
    )


def test_lever_filters_irrelevant_and_out_of_location_jobs(monkeypatch):
    response = FakeResponse(
        [
            _job("1", "Senior Finance Analyst"),
            _job("2", "Software Engineer"),
            _job("3", "Finance Analyst", location="London", country="GB"),
        ]
    )
    calls = []

    def fake_get(url, *, params, timeout):
        calls.append((url, params, timeout))
        return response

    monkeypatch.setattr(
        "services.job_discovery.providers.lever_provider.requests.get",
        fake_get,
    )

    jobs = _provider().search_jobs(JobSearchQuery(role="Senior Finance Analyst", location="India"))

    assert calls == [
        (
            "https://api.lever.co/v0/postings/example",
            {"mode": "json"},
            30,
        )
    ]
    assert len(jobs) == 1
    assert jobs[0].title == "Senior Finance Analyst"
    assert jobs[0].company == "Example"
    assert jobs[0].description == (
        "Support customers & resolve payment issues. Requirements Clear communication "
        "Health insurance."
    )
    assert jobs[0].experience_level == ExperienceLevel.SENIOR
    assert jobs[0].employment_type == EmploymentType.FULL_TIME
    assert jobs[0].source == JobSource.LEVER
    assert jobs[0].external_id == "1"
    assert str(jobs[0].url) == "https://jobs.lever.co/example/1"


def test_lever_accepts_only_explicit_remote_jobs_for_remote_search(monkeypatch):
    response = FakeResponse(
        [
            _job("1", "Finance Analyst", location="India", workplace="remote"),
            _job("2", "Finance Analyst", location="India", workplace="hybrid"),
        ]
    )
    monkeypatch.setattr(
        "services.job_discovery.providers.lever_provider.requests.get",
        lambda *args, **kwargs: response,
    )

    jobs = _provider().search_jobs(
        JobSearchQuery(role="Finance Analyst", location="Remote", remote_only=True)
    )

    assert [job.external_id for job in jobs] == ["1"]
    assert jobs[0].employment_type == EmploymentType.REMOTE


def test_lever_maps_internship_and_paginates_after_filtering(monkeypatch):
    response = FakeResponse(
        [
            _job("1", "Finance Analyst", commitment="Intern: Full Time"),
            _job("2", "Finance Analyst", commitment="Apprentice"),
        ]
    )
    monkeypatch.setattr(
        "services.job_discovery.providers.lever_provider.requests.get",
        lambda *args, **kwargs: response,
    )

    jobs = _provider().search_jobs(
        JobSearchQuery(role="Finance Analyst", location="India", page=2, page_size=1)
    )

    assert [job.external_id for job in jobs] == ["2"]
    assert jobs[0].employment_type == EmploymentType.INTERNSHIP


def test_lever_rejects_invalid_jobs_collection(monkeypatch):
    monkeypatch.setattr(
        "services.job_discovery.providers.lever_provider.requests.get",
        lambda *args, **kwargs: FakeResponse({"jobs": []}),
    )

    with pytest.raises(ProviderPayloadError, match="invalid jobs collection"):
        _provider().search_jobs(JobSearchQuery(role="Finance", location="India"))

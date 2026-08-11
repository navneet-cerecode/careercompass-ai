import pytest

from models.enums import EmploymentType, ExperienceLevel, JobSource
from services.job_discovery.providers.ashby_provider import AshbyProvider
from services.job_discovery.providers.contracts import JobSearchQuery
from services.job_discovery.providers.errors import ProviderPayloadError


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
    location="Bangalore",
    *,
    listed=True,
    remote=False,
    country="India",
):
    return {
        "id": job_id,
        "title": title,
        "location": location,
        "isListed": listed,
        "isRemote": remote,
        "workplaceType": "Remote" if remote else "OnSite",
        "employmentType": "FullTime",
        "address": {"postalAddress": {"addressCountry": country}},
        "descriptionPlain": "Support customers & resolve payment issues.",
        "jobUrl": f"https://jobs.ashbyhq.com/Example/{job_id}",
        "applyUrl": f"https://jobs.ashbyhq.com/Example/{job_id}/application",
    }


def _provider():
    return AshbyProvider(
        {
            "id": "example",
            "name": "Example",
            "platform": "ashby",
            "job_board_name": "Example",
        }
    )


def test_ashby_filters_unlisted_irrelevant_and_out_of_location_jobs(monkeypatch):
    response = FakeResponse(
        {
            "jobs": [
                _job("1", "Senior Finance Analyst"),
                _job("2", "Software Engineer"),
                _job("3", "Finance Analyst", listed=False),
                _job("4", "Finance Analyst", location="London", country="UK"),
            ]
        }
    )
    calls = []

    def fake_get(url, *, params, timeout):
        calls.append((url, params, timeout))
        return response

    monkeypatch.setattr(
        "services.job_discovery.providers.ashby_provider.requests.get",
        fake_get,
    )

    jobs = _provider().search_jobs(JobSearchQuery(role="Senior Finance Analyst", location="India"))

    assert calls == [
        (
            "https://api.ashbyhq.com/posting-api/job-board/Example",
            {"includeCompensation": "false"},
            30,
        )
    ]
    assert len(jobs) == 1
    assert jobs[0].title == "Senior Finance Analyst"
    assert jobs[0].company == "Example"
    assert jobs[0].description == "Support customers & resolve payment issues."
    assert jobs[0].experience_level == ExperienceLevel.SENIOR
    assert jobs[0].employment_type == EmploymentType.FULL_TIME
    assert jobs[0].source == JobSource.ASHBY
    assert jobs[0].external_id == "1"
    assert str(jobs[0].url) == "https://jobs.ashbyhq.com/Example/1"


def test_ashby_accepts_only_explicit_remote_jobs_for_remote_search(monkeypatch):
    response = FakeResponse(
        {
            "jobs": [
                _job("1", "Finance Analyst", location="India", remote=True),
                _job("2", "Finance Analyst", location="India", remote=False),
            ]
        }
    )
    monkeypatch.setattr(
        "services.job_discovery.providers.ashby_provider.requests.get",
        lambda *args, **kwargs: response,
    )

    jobs = _provider().search_jobs(
        JobSearchQuery(role="Finance Analyst", location="Remote", remote_only=True)
    )

    assert [job.external_id for job in jobs] == ["1"]
    assert jobs[0].employment_type == EmploymentType.REMOTE


def test_ashby_paginates_after_filtering(monkeypatch):
    response = FakeResponse({"jobs": [_job("1", "Finance Analyst"), _job("2", "Finance Analyst")]})
    monkeypatch.setattr(
        "services.job_discovery.providers.ashby_provider.requests.get",
        lambda *args, **kwargs: response,
    )

    jobs = _provider().search_jobs(
        JobSearchQuery(role="Finance Analyst", location="India", page=2, page_size=1)
    )

    assert [job.external_id for job in jobs] == ["2"]


def test_ashby_rejects_invalid_jobs_collection(monkeypatch):
    monkeypatch.setattr(
        "services.job_discovery.providers.ashby_provider.requests.get",
        lambda *args, **kwargs: FakeResponse({"jobs": {}}),
    )

    with pytest.raises(ProviderPayloadError, match="invalid jobs collection"):
        _provider().search_jobs(JobSearchQuery(role="Finance", location="India"))

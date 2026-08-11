import pytest

from models.enums import EmploymentType, ExperienceLevel, JobSource
from services.job_discovery.providers.contracts import JobSearchQuery
from services.job_discovery.providers.errors import ProviderPayloadError
from services.job_discovery.providers.smartrecruiters_provider import SmartRecruitersProvider


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload
        self.raise_called = False

    def raise_for_status(self):
        self.raise_called = True

    def json(self):
        return self.payload


def _summary(job_id, title, location="Mumbai, MH, India", *, remote=False):
    return {
        "id": job_id,
        "name": title,
        "location": {"fullLocation": location, "country": "in", "remote": remote},
    }


def _detail(job_id, title, *, remote=False):
    return {
        **_summary(job_id, title, remote=remote),
        "uuid": f"uuid-{job_id}",
        "applyUrl": f"https://jobs.smartrecruiters.com/Example/{job_id}",
        "experienceLevel": {"id": "mid_senior_level"},
        "typeOfEmployment": {"id": "permanent"},
        "jobAd": {
            "sections": {
                "jobDescription": {"text": "<p>Lead sales &amp; partnerships.</p>"},
                "qualifications": {"text": "<p>Five years of experience.</p>"},
            }
        },
    }


def _provider():
    return SmartRecruitersProvider(
        {
            "id": "example",
            "name": "Example",
            "platform": "smartrecruiters",
            "company_identifier": "Example",
            "country": "in",
        }
    )


def test_smartrecruiters_filters_then_fetches_known_host_details(monkeypatch):
    listing = FakeResponse(
        {
            "content": [
                _summary("1", "Senior Sales Manager"),
                _summary("2", "Software Engineer"),
            ]
        }
    )
    detail = FakeResponse(_detail("1", "Senior Sales Manager"))
    calls = []

    def fake_get(url, *, params=None, timeout):
        calls.append((url, params, timeout))
        return listing if params is not None else detail

    monkeypatch.setattr(
        "services.job_discovery.providers.smartrecruiters_provider.requests.get",
        fake_get,
    )

    jobs = _provider().search_jobs(
        JobSearchQuery(role="Sales Manager", location="India", page=2, page_size=10)
    )

    assert calls == [
        (
            "https://api.smartrecruiters.com/v1/companies/Example/postings",
            {
                "q": "Sales Manager",
                "country": "in",
                "destination": "PUBLIC",
                "limit": 10,
                "offset": 10,
            },
            30,
        ),
        (
            "https://api.smartrecruiters.com/v1/companies/Example/postings/1",
            None,
            30,
        ),
    ]
    assert len(jobs) == 1
    assert jobs[0].description == "Lead sales & partnerships. Five years of experience."
    assert jobs[0].experience_level == ExperienceLevel.SENIOR
    assert jobs[0].employment_type == EmploymentType.FULL_TIME
    assert jobs[0].source == JobSource.SMARTRECRUITERS


def test_smartrecruiters_accepts_remote_only_when_requested(monkeypatch):
    listing = FakeResponse({"content": [_summary("1", "Finance Analyst", "Remote", remote=True)]})
    detail = FakeResponse(_detail("1", "Finance Analyst", remote=True))
    monkeypatch.setattr(
        "services.job_discovery.providers.smartrecruiters_provider.requests.get",
        lambda url, **kwargs: listing if kwargs.get("params") is not None else detail,
    )

    jobs = _provider().search_jobs(
        JobSearchQuery(role="Finance Analyst", location="Remote", remote_only=True)
    )

    assert len(jobs) == 1
    assert jobs[0].employment_type == EmploymentType.REMOTE


def test_smartrecruiters_rejects_invalid_jobs_collection(monkeypatch):
    monkeypatch.setattr(
        "services.job_discovery.providers.smartrecruiters_provider.requests.get",
        lambda *args, **kwargs: FakeResponse({"content": {}}),
    )

    with pytest.raises(ProviderPayloadError, match="invalid jobs collection"):
        _provider().search_jobs(JobSearchQuery(role="Finance", location="India"))

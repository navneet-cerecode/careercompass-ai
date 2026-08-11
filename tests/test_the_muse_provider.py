import pytest

from models.enums import EmploymentType, ExperienceLevel, JobSource
from services.job_discovery.providers.contracts import JobSearchQuery
from services.job_discovery.providers.the_muse_provider import TheMuseProvider


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload
        self.raise_called = False

    def raise_for_status(self):
        self.raise_called = True

    def json(self):
        return self.payload


def _job(*, job_id, name, locations):
    return {
        "id": job_id,
        "name": name,
        "contents": "<p>Coordinate operations &amp; suppliers.</p>",
        "company": {"name": "Northstar Foods"},
        "locations": [{"name": location} for location in locations],
        "levels": [{"name": "Mid Level"}],
        "refs": {"landing_page": f"https://www.themuse.com/jobs/northstar/{job_id}"},
    }


def test_the_muse_keeps_only_title_and_location_relevant_jobs(monkeypatch):
    response = FakeResponse(
        {
            "results": [
                _job(job_id=1, name="Operations Manager", locations=["Mumbai, India"]),
                _job(job_id=2, name="Benefits Analyst", locations=["Flexible / Remote"]),
                _job(job_id=3, name="Software Engineer", locations=["Mumbai, India"]),
            ]
        }
    )
    captured = {}

    def fake_get(url, *, params, timeout):
        captured.update({"url": url, "params": params, "timeout": timeout})
        return response

    monkeypatch.setattr(
        "services.job_discovery.providers.the_muse_provider.requests.get",
        fake_get,
    )
    provider = TheMuseProvider(
        {"id": "the_muse", "name": "The Muse", "platform": "the_muse"},
        api_key="test-key",
    )

    jobs = provider.search_jobs(JobSearchQuery(role="Operations Manager", location="India"))

    assert response.raise_called is True
    assert captured == {
        "url": "https://www.themuse.com/api/public/jobs",
        "params": {
            "api_key": "test-key",
            "category": "Business Operations",
            "location": "India",
            "page": 0,
        },
        "timeout": 30,
    }
    assert len(jobs) == 1
    assert jobs[0].title == "Operations Manager"
    assert jobs[0].description == "Coordinate operations & suppliers."
    assert jobs[0].source == JobSource.THE_MUSE
    assert jobs[0].employment_type == EmploymentType.FULL_TIME
    assert jobs[0].experience_level == ExperienceLevel.MID


def test_the_muse_accepts_remote_jobs_only_when_requested(monkeypatch):
    response = FakeResponse(
        {"results": [_job(job_id=1, name="Care Coordinator", locations=["Flexible / Remote"])]}
    )
    monkeypatch.setattr(
        "services.job_discovery.providers.the_muse_provider.requests.get",
        lambda *args, **kwargs: response,
    )
    provider = TheMuseProvider(
        {"id": "the_muse", "name": "The Muse", "platform": "the_muse"},
        api_key="test-key",
    )

    jobs = provider.search_jobs(
        JobSearchQuery(role="Patient Care Coordinator", location="Remote", remote_only=True)
    )

    assert len(jobs) == 1
    assert jobs[0].employment_type == EmploymentType.REMOTE


def test_the_muse_skips_unmapped_roles_without_network(monkeypatch):
    monkeypatch.setattr(
        "services.job_discovery.providers.the_muse_provider.requests.get",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("network called")),
    )
    provider = TheMuseProvider(
        {"id": "the_muse", "name": "The Muse", "platform": "the_muse"},
        api_key="test-key",
    )

    assert provider.search_jobs(JobSearchQuery(role="Marine Biologist", location="India")) == []


@pytest.mark.parametrize(
    ("role", "category"),
    [
        ("Nurse", "Nurses"),
        ("Restaurant Manager", "Food and Hospitality Services"),
        ("Warehouse Supervisor", "Manufacturing and Warehouse"),
        ("Social Worker", "Social Services"),
        ("Mechanical Engineer", "Science and Engineering"),
        ("Frontend Developer", "Software Engineering"),
    ],
)
def test_the_muse_maps_cross_industry_roles_to_documented_categories(role, category):
    assert TheMuseProvider._category_for(role) == category

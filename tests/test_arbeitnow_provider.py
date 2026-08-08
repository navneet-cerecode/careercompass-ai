from models.enums import EmploymentType, JobSource
from services.job_discovery.providers.arbeitnow_provider import ArbeitnowProvider
from services.job_discovery.providers.contracts import JobSearchQuery


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload
        self.raise_called = False

    def raise_for_status(self):
        self.raise_called = True

    def json(self):
        return self.payload


def test_arbeitnow_filters_and_normalizes_non_technical_jobs(monkeypatch):
    response = FakeResponse(
        {
            "data": [
                {
                    "slug": "care-coordinator-1",
                    "company_name": "Example Health",
                    "title": "Care Coordinator",
                    "description": "<p>Coordinate patient care.</p>",
                    "remote": False,
                    "location": "Berlin",
                    "tags": ["Patient care", "Scheduling"],
                    "job_types": ["full_time"],
                    "url": "https://www.arbeitnow.com/jobs/care-coordinator-1",
                },
                {
                    "slug": "engineer-1",
                    "company_name": "Example Tech",
                    "title": "Software Engineer",
                    "description": "Build software.",
                    "remote": True,
                    "location": "Berlin",
                    "tags": ["Python"],
                    "job_types": ["full_time"],
                    "url": "https://www.arbeitnow.com/jobs/engineer-1",
                },
            ]
        }
    )
    captured = {}

    def fake_get(url, *, params, timeout):
        captured.update({"url": url, "params": params, "timeout": timeout})
        return response

    monkeypatch.setattr(
        "services.job_discovery.providers.arbeitnow_provider.requests.get",
        fake_get,
    )
    provider = ArbeitnowProvider({"id": "arbeitnow", "name": "Arbeitnow"})

    jobs = provider.search_jobs(
        JobSearchQuery(role="Care Coordinator", location="Germany", country="DE")
    )

    assert response.raise_called is True
    assert captured["url"] == "https://www.arbeitnow.com/api/job-board-api"
    assert captured["params"] == {"page": 1}
    assert captured["timeout"] == 30
    assert len(jobs) == 1
    assert jobs[0].title == "Care Coordinator"
    assert jobs[0].description == "Coordinate patient care."
    assert jobs[0].employment_type == EmploymentType.FULL_TIME
    assert jobs[0].source == JobSource.ARBEITNOW
    assert [skill.name for skill in jobs[0].required_skills] == [
        "Patient Care",
        "Scheduling",
    ]


def test_arbeitnow_skips_unsupported_countries_without_network(monkeypatch):
    monkeypatch.setattr(
        "services.job_discovery.providers.arbeitnow_provider.requests.get",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("network called")),
    )
    provider = ArbeitnowProvider({"id": "arbeitnow", "name": "Arbeitnow"})

    jobs = provider.search_jobs(JobSearchQuery(role="Nurse", location="India", country="IN"))

    assert jobs == []

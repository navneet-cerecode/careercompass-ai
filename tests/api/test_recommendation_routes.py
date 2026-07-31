import sys

from fastapi.testclient import TestClient

from api.application import create_app
from api.dependencies import get_recommendation_service
from core.config import Settings
from models.job import Job
from models.match_assessment import MatchAssessment
from services.recommendation.recommendation_service import RecommendationService


def make_job(title: str, score: float) -> tuple[Job, float]:
    return (
        Job(
            title=title,
            company="Example Corp",
            location="India",
            description="Python and SQL",
            url=f"https://example.com/jobs/{title.lower().replace(' ', '-')}",
        ),
        score,
    )


def make_client() -> tuple[TestClient, list[Job]]:
    lower, lower_score = make_job("Lower Match", 40)
    higher, higher_score = make_job("Higher Match", 90)
    scores = {lower.id: lower_score, higher.id: higher_score}

    class StubEngine:
        def evaluate(self, resume, job):
            assert resume.raw_text == "Ada Lovelace\nPython engineer"
            return MatchAssessment(
                job=job,
                score=scores[job.id],
                algorithm_version="test-v1",
            )

    application = create_app(Settings(_env_file=None))
    application.state.job_catalog.add_many((lower, higher))
    application.dependency_overrides[get_recommendation_service] = lambda: RecommendationService(
        engine=StubEngine()
    )
    return TestClient(application), [lower, higher]


def test_recommendation_endpoint_reuses_ranked_application_service():
    client, jobs = make_client()

    response = client.post(
        "/api/v1/recommendations",
        json={
            "resume": {
                "name": "Ada Lovelace",
                "raw_text": "Ada Lovelace\nPython engineer",
                "skills": [{"name": "Python"}],
            },
            "job_ids": [str(job.id) for job in jobs],
        },
    )

    assert response.status_code == 200
    recommendations = response.json()["recommendations"]
    assert [item["assessment"]["score"] for item in recommendations] == [90, 40]
    assert [item["rank"] for item in recommendations] == [1, 2]
    assert all(item["assessment"]["algorithm_version"] == "test-v1" for item in recommendations)


def test_recommendation_endpoint_rejects_unknown_job_ids():
    client, _ = make_client()

    response = client.post(
        "/api/v1/recommendations",
        json={
            "resume": {
                "name": "Ada Lovelace",
                "raw_text": "Ada Lovelace\nPython engineer",
            },
            "job_ids": ["00000000-0000-0000-0000-000000000000"],
        },
    )

    assert response.status_code == 404
    assert response.json()["code"] == "jobs_not_found"


def test_api_creation_does_not_construct_embedding_engine():
    sys.modules.pop("services.recommendation.recommendation_engine", None)

    application = create_app(Settings(_env_file=None))

    assert not hasattr(application.state, "recommendation_service")
    assert "services.recommendation.recommendation_engine" not in sys.modules

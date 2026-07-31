from models.job import Job
from models.match_assessment import MatchAssessment
from models.resume import Resume
from services.recommendation.recommendation_service import RecommendationService


def make_job(title: str) -> Job:
    return Job(
        title=title,
        company="Example Corp",
        location="India",
        description="Example description",
        url=f"https://example.com/jobs/{title.lower().replace(' ', '-')}",
    )


class ScoreByTitleEngine:
    def __init__(self, scores):
        self.scores = scores
        self.calls = []

    def evaluate(self, resume, job):
        self.calls.append((resume, job))
        return MatchAssessment(
            job=job,
            score=self.scores[job.title],
            algorithm_version="test-v1",
        )


def test_recommendation_service_sorts_assessments_and_assigns_ranks():
    resume = Resume(name="Ada Lovelace", raw_text="Python engineer")
    lower = make_job("Lower Match")
    higher = make_job("Higher Match")
    engine = ScoreByTitleEngine(
        {
            "Lower Match": 40,
            "Higher Match": 90,
        }
    )
    service = RecommendationService(engine=engine)

    recommendations = service.recommend_jobs(
        resume,
        [lower, higher],
    )

    assert [recommendation.job for recommendation in recommendations] == [
        higher,
        lower,
    ]
    assert [recommendation.score for recommendation in recommendations] == [90, 40]
    assert [recommendation.rank for recommendation in recommendations] == [1, 2]
    assert [call[1] for call in engine.calls] == [lower, higher]


def test_recommendation_service_handles_empty_job_batch():
    service = RecommendationService(engine=ScoreByTitleEngine({}))
    resume = Resume(name="Ada Lovelace", raw_text="Python engineer")

    assert service.assess_jobs(resume, []) == []
    assert service.recommend_jobs(resume, []) == []

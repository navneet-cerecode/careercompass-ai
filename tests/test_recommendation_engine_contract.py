from models.job import Job
from models.score_component import ScoreComponent
from models.skill import Skill
from services.recommendation.recommendation_engine import RecommendationEngine


class StaticSignal:
    def __init__(self, component):
        self.component = component

    def evaluate(self, resume, job):
        return self.component


def test_recommendation_engine_returns_versioned_match_assessment():
    job = Job(
        title="Data Engineer",
        company="Example Corp",
        location="India",
        description="Python and SQL",
        url="https://example.com/jobs/1",
    )
    python = Skill(name="Python")
    sql = Skill(name="SQL")
    signals = [
        StaticSignal(
            ScoreComponent(
                name="Skill Signal",
                score=80,
                matched_skills=[python],
                missing_skills=[sql],
            )
        ),
        StaticSignal(
            ScoreComponent(
                name="Semantic Signal",
                score=50,
            )
        ),
    ]
    engine = RecommendationEngine(signals=signals)

    assessment = engine.evaluate(object(), job)

    assert assessment.job == job
    assert assessment.score == 62
    assert assessment.algorithm_version == "hybrid-v1"
    assert assessment.components == [signal.component for signal in signals]
    assert assessment.matched_skills == [python]
    assert assessment.missing_skills == [sql]

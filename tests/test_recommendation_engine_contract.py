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
    assert assessment.algorithm_version == "hybrid-v2"
    assert assessment.confidence == 1
    assert assessment.components == [signal.component for signal in signals]
    assert assessment.matched_skills == [python]
    assert assessment.missing_skills == [sql]
    assert assessment.recruiter_summary == (
        "The reviewed resume supports 1 of 2 listed skills; 1 still needs evidence."
    )
    assert assessment.recommendations == [
        "Verify whether your experience demonstrates SQL; only add it to application materials "
        "if factual."
    ]


def test_recommendation_engine_removes_duplicate_and_contradictory_skill_evidence():
    job = Job(
        title="Operations Manager",
        company="Example Corp",
        location="India",
        description="Lead inventory operations.",
        url="https://example.com/jobs/2",
    )
    inventory = Skill(name="Inventory Planning")
    signals = [
        StaticSignal(
            ScoreComponent(
                name="Skill Signal",
                score=50,
                matched_skills=[inventory, Skill(name="inventory planning")],
                missing_skills=[inventory],
            )
        ),
        StaticSignal(ScoreComponent(name="Semantic Signal", score=50)),
    ]

    assessment = RecommendationEngine(signals=signals).evaluate(object(), job)

    assert [skill.name for skill in assessment.matched_skills] == ["Inventory Planning"]
    assert assessment.missing_skills == []

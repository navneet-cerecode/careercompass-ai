import pytest
from pydantic import ValidationError

from models.job import Job
from models.job_recommendation import JobRecommendation
from models.match import MatchResult
from models.match_assessment import MatchAssessment
from models.recommendation_result import RecommendationResult
from models.score_component import ScoreComponent
from services.recommendation.models.signal_result import SignalResult


def make_job() -> Job:
    return Job(
        title="Data Engineer",
        company="Example Corp",
        location="India",
        description="Python and SQL",
        url="https://example.com/jobs/1",
    )


def test_legacy_result_imports_resolve_to_canonical_models():
    assert MatchResult is MatchAssessment
    assert RecommendationResult is MatchAssessment
    assert SignalResult is ScoreComponent


def test_score_component_accepts_legacy_field_names():
    component = SignalResult(
        signal_name="Skill Signal",
        score=80,
        reason="Matched four of five skills.",
    )

    assert component.name == "Skill Signal"
    assert component.signal_name == "Skill Signal"
    assert component.explanation == "Matched four of five skills."
    assert component.reason == "Matched four of five skills."


@pytest.mark.parametrize("score", [-0.1, 100.1])
def test_score_component_rejects_out_of_range_scores(score):
    with pytest.raises(ValidationError):
        ScoreComponent(
            name="Invalid",
            score=score,
        )


def test_match_assessment_accepts_legacy_score_and_component_names():
    component = ScoreComponent(name="Skill Signal", score=80)

    assessment = MatchResult(
        job=make_job(),
        match_score=80,
        signal_results=[component],
        recruiter_summary="Good fit.",
    )

    assert assessment.score == 80
    assert assessment.match_score == 80
    assert assessment.components == [component]
    assert assessment.signal_results == [component]


def test_job_recommendation_delegates_to_its_assessment():
    assessment = MatchAssessment(
        job=make_job(),
        score=75,
        components=[ScoreComponent(name="Skill Signal", score=75)],
        recruiter_summary="Good fit.",
        recommendations=["Highlight Python projects."],
        algorithm_version="hybrid-v1",
    )

    recommendation = JobRecommendation(
        assessment=assessment,
        rank=1,
    )

    assert recommendation.job == assessment.job
    assert recommendation.score == 75
    assert recommendation.signal_results == assessment.components
    assert recommendation.recruiter_summary == "Good fit."
    assert recommendation.recommendations == ["Highlight Python projects."]
    assert recommendation.model_dump()["assessment"]["algorithm_version"] == "hybrid-v1"


def test_job_recommendation_adapts_legacy_flat_constructor():
    recommendation = JobRecommendation(
        job=make_job(),
        score=70,
        signal_results=[
            ScoreComponent(
                name="Semantic Signal",
                score=70,
            )
        ],
        recruiter_summary="Relevant background.",
    )

    assert recommendation.score == 70
    assert recommendation.assessment.algorithm_version == "legacy"
    assert recommendation.signal_results[0].name == "Semantic Signal"


def test_match_assessment_rejects_invalid_overall_score():
    with pytest.raises(ValidationError):
        MatchAssessment(
            job=make_job(),
            score=101,
        )

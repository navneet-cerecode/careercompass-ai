from models.job import Job
from models.job_recommendation import JobRecommendation
from models.match_assessment import MatchAssessment
from models.resume import Resume
from models.score_component import ScoreComponent
from models.skill import Skill

from api.mappers import map_parsed_resume, map_recommendation, map_resume


def test_resume_summary_does_not_expose_raw_text():
    resume = Resume(
        name="Ada Lovelace",
        email="ada@example.com",
        raw_text="Sensitive source resume text",
        skills=[Skill(name="python")],
    )

    response = map_resume(resume)

    assert response.name == "Ada Lovelace"
    assert response.skills[0].name == "Python"
    assert "raw_text" not in response.model_dump()


def test_parsed_resume_returns_source_text_only_in_explicit_contract():
    resume = Resume(
        name="Ada Lovelace",
        raw_text="Ada Lovelace\nPython engineer",
    )

    response = map_parsed_resume(resume)

    assert response.resume.name == "Ada Lovelace"
    assert response.raw_text == resume.raw_text


def test_recommendation_mapping_preserves_explainable_versioned_score():
    job = Job(
        title="Data Engineer",
        company="Example Corp",
        location="India",
        description="Python and SQL",
        required_skills=[Skill(name="sql")],
        url="https://example.com/jobs/1",
    )
    assessment = MatchAssessment(
        job=job,
        score=82,
        components=[
            ScoreComponent(
                name="Skill Signal",
                score=90,
                explanation="Strong overlap.",
                matched_skills=[Skill(name="sql")],
            )
        ],
        confidence=0.8,
        algorithm_version="hybrid-v1",
    )
    recommendation = JobRecommendation(
        assessment=assessment,
        rank=1,
    )

    response = map_recommendation(recommendation)

    assert response.rank == 1
    assert response.assessment.job.url.unicode_string() == "https://example.com/jobs/1"
    assert response.assessment.score == 82
    assert response.assessment.components[0].name == "Skill Signal"
    assert response.assessment.algorithm_version == "hybrid-v1"

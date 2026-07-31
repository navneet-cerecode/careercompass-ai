from core.career_compass import CareerCompass
from models.job import Job
from models.match_assessment import MatchAssessment
from models.score_component import ScoreComponent
from models.skill import Skill


def make_job() -> Job:
    return Job(
        title="Machine Learning Engineer",
        company="Example Corp",
        location="India",
        description="Python, SQL, and Docker",
        url="https://example.com/jobs/1",
    )


class StubAssessmentService:
    def __init__(self, assessment):
        self.assessment = assessment

    def evaluate(self, resume, job):
        assert job == self.assessment.job
        return self.assessment


def test_recommend_job_wraps_the_engine_assessment():
    job = make_job()
    assessment = MatchAssessment(
        job=job,
        score=62,
        components=[ScoreComponent(name="Skill Signal", score=80)],
        algorithm_version="hybrid-v1",
    )
    compass = CareerCompass()
    compass.__dict__["recommendation_engine"] = StubAssessmentService(assessment)

    recommendation = compass.recommend_job(object(), job)

    assert recommendation.assessment is assessment
    assert recommendation.job == job
    assert recommendation.score == 62


def test_recommend_jobs_delegates_batch_sorting_to_application_service():
    lower = make_job()
    higher = lower.model_copy(
        update={
            "title": "Senior Machine Learning Engineer",
            "url": "https://example.com/jobs/2",
        }
    )
    lower_assessment = MatchAssessment(
        job=lower,
        score=40,
        algorithm_version="hybrid-v1",
    )
    higher_assessment = MatchAssessment(
        job=higher,
        score=90,
        algorithm_version="hybrid-v1",
    )

    class StubBatchService:
        def recommend_jobs(self, resume, jobs):
            assert jobs == [lower, higher]
            return [
                JobRecommendation(assessment=higher_assessment, rank=1),
                JobRecommendation(assessment=lower_assessment, rank=2),
            ]

    from models.job_recommendation import JobRecommendation

    compass = CareerCompass()
    compass.__dict__["recommendation_service"] = StubBatchService()

    recommendations = compass.recommend_jobs(object(), [lower, higher])

    assert [recommendation.score for recommendation in recommendations] == [90, 40]
    assert [recommendation.rank for recommendation in recommendations] == [1, 2]


def test_ai_analysis_enriches_explanation_without_replacing_rank_score(capsys):
    job = make_job()
    base_assessment = MatchAssessment(
        job=job,
        score=62,
        components=[ScoreComponent(name="Skill Signal", score=80)],
        matched_skills=[Skill(name="Python")],
        algorithm_version="hybrid-v1",
    )
    ai_assessment = MatchAssessment(
        job=job,
        score=91,
        components=[ScoreComponent(name="LLM Recruiter Review", score=91)],
        matched_skills=[Skill(name="Python"), Skill(name="SQL")],
        missing_skills=[Skill(name="Docker")],
        recruiter_summary="Strong relevant foundation.",
        recommendations=["Highlight Docker experience if factual."],
        algorithm_version="groq:test-model",
    )
    compass = CareerCompass()
    compass.__dict__["recommendation_engine"] = StubAssessmentService(base_assessment)
    compass.__dict__["evaluator"] = StubAssessmentService(ai_assessment)

    recommendation = compass.analyze_resume(object(), job)

    assert recommendation.score == 62
    assert recommendation.assessment.algorithm_version == "hybrid-v1"
    assert recommendation.signal_results == base_assessment.components
    assert [skill.name for skill in recommendation.matched_skills] == ["Python", "SQL"]
    assert [skill.name for skill in recommendation.missing_skills] == ["Docker"]
    assert recommendation.recruiter_summary == "Strong relevant foundation."
    assert recommendation.recommendations == ["Highlight Docker experience if factual."]
    assert capsys.readouterr().out == ""

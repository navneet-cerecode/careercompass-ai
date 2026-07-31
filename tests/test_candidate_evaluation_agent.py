from agents.candidate_evaluation_agent import CandidateEvaluationAgent
from models.job import Job
from models.match_assessment import MatchAssessment
from models.resume import Resume


def make_job() -> Job:
    return Job(
        title="Data Engineer",
        company="Example Corp",
        location="India",
        description="Python and SQL",
        url="https://example.com/jobs/1",
    )


class StubRecommendationService:
    def __init__(self, assessments):
        self.assessments = assessments
        self.calls = []

    def assess_jobs(self, resume, jobs):
        self.calls.append((resume, jobs))
        return self.assessments


def test_candidate_agent_skips_evaluation_without_resume():
    service = StubRecommendationService([])
    agent = CandidateEvaluationAgent(recommendation_service=service)
    state = {
        "role": "Data Engineer",
        "location": "India",
        "resume": None,
        "jobs": [make_job()],
        "match_results": [object()],
    }

    result = agent.run(state)

    assert result["match_results"] == []
    assert service.calls == []


def test_candidate_agent_assesses_every_discovered_job():
    resume = Resume(name="Ada Lovelace", raw_text="Python engineer")
    job = make_job()
    assessment = MatchAssessment(
        job=job,
        score=80,
        algorithm_version="test-v1",
    )
    service = StubRecommendationService([assessment])
    agent = CandidateEvaluationAgent(recommendation_service=service)
    state = {
        "role": "Data Engineer",
        "location": "India",
        "resume": resume,
        "jobs": [job],
        "match_results": [],
    }

    result = agent.run(state)

    assert result["match_results"] == [assessment]
    assert service.calls == [(resume, [job])]

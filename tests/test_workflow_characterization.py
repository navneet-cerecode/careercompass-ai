from models.job import Job
from models.match_assessment import MatchAssessment
from models.resume import Resume


def make_job():
    return Job(
        title="Data Scientist",
        company="Example Corp",
        location="India",
        description="Python and SQL",
        url="https://example.com/jobs/1",
    )


class StubJobAgent:
    def __init__(self, job):
        self.job = job

    def run(self, state):
        state["jobs"] = [self.job]
        return state


def test_current_workflow_is_discovery_only(monkeypatch):
    from graph import nodes
    from graph.workflow import build_workflow

    job = make_job()
    monkeypatch.setattr(nodes, "get_job_agent", lambda: StubJobAgent(job))
    monkeypatch.setattr(
        nodes,
        "get_evaluation_agent",
        lambda: (_ for _ in ()).throw(
            AssertionError("Discovery workflow invoked candidate evaluation")
        ),
    )

    result = build_workflow().invoke(
        {
            "role": "Data Scientist",
            "location": "India",
            "resume": None,
            "jobs": [],
            "match_results": [],
        }
    )

    assert result["jobs"] == [job]
    assert result["match_results"] == []


def test_full_recommendation_workflow_runs_real_evaluation_node(monkeypatch):
    from graph import nodes
    from graph.workflow import build_recommendation_workflow

    resume = Resume(name="Ada Lovelace", raw_text="Python engineer")
    job = make_job()
    assessment = MatchAssessment(
        job=job,
        score=80,
        algorithm_version="test-v1",
    )

    class StubEvaluationAgent:
        def run(self, state):
            assert state["resume"] == resume
            state["match_results"] = [assessment]
            return state

    monkeypatch.setattr(nodes, "get_job_agent", lambda: StubJobAgent(job))
    monkeypatch.setattr(
        nodes,
        "get_evaluation_agent",
        lambda: StubEvaluationAgent(),
    )

    result = build_recommendation_workflow().invoke(
        {
            "role": "Data Scientist",
            "location": "India",
            "resume": resume,
            "jobs": [],
            "match_results": [],
        }
    )

    assert result["jobs"] == [job]
    assert result["match_results"] == [assessment]

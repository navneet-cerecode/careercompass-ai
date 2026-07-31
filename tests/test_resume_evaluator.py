from models.job import Job
from models.resume import Resume
from services.llm.evaluator import ResumeEvaluator


class StubGroqClient:
    model = "test-model"

    def chat(self, prompt):
        assert "Ada Lovelace" in prompt
        return {
            "match_score": 0.86,
            "matched_skills": ["Python", "SQL"],
            "missing_skills": ["Docker"],
            "recruiter_summary": "Strong relevant foundation.",
            "recommendations": ["Highlight Docker experience if factual."],
        }


def test_resume_evaluator_returns_versioned_match_assessment_without_logging(capsys):
    resume = Resume(
        name="Ada Lovelace",
        raw_text="Ada Lovelace\nPython and SQL",
    )
    job = Job(
        title="Data Engineer",
        company="Example Corp",
        location="India",
        description="Python, SQL, and Docker",
        url="https://example.com/jobs/1",
    )
    evaluator = ResumeEvaluator.__new__(ResumeEvaluator)
    evaluator.client = StubGroqClient()

    assessment = evaluator.evaluate(resume, job)

    assert assessment.score == 86
    assert assessment.algorithm_version == "groq:test-model"
    assert assessment.components[0].name == "LLM Recruiter Review"
    assert assessment.components[0].score == 86
    assert [skill.name for skill in assessment.matched_skills] == ["Python", "SQL"]
    assert [skill.name for skill in assessment.missing_skills] == ["Docker"]
    assert capsys.readouterr().out == ""

"""
Groq Resume Evaluator.
"""

from models.match_assessment import MatchAssessment
from models.score_component import ScoreComponent
from models.skill import Skill

from services.llm.groq_client import GroqClient
from services.llm.prompts import build_match_prompt


class ResumeEvaluator:
    def __init__(self):

        self.client = GroqClient()

    def evaluate(
        self,
        resume,
        job,
    ) -> MatchAssessment:

        prompt = build_match_prompt(
            resume,
            job,
        )

        result = self.client.chat(prompt)

        score = result.get(
            "match_score",
            0,
        )

        # Groq sometimes returns 0-1 instead of 0-100
        if isinstance(score, (int, float)) and score <= 1:
            score *= 100

        recruiter_summary = result.get(
            "recruiter_summary",
            "",
        )

        return MatchAssessment(
            job=job,
            score=score,
            matched_skills=[
                Skill(name=s)
                for s in result.get(
                    "matched_skills",
                    [],
                )
            ],
            missing_skills=[
                Skill(name=s)
                for s in result.get(
                    "missing_skills",
                    [],
                )
            ],
            recruiter_summary=recruiter_summary,
            recommendations=result.get(
                "recommendations",
                [],
            ),
            components=[
                ScoreComponent(
                    name="LLM Recruiter Review",
                    score=score,
                    explanation=recruiter_summary,
                )
            ],
            algorithm_version=f"groq:{self.client.model}",
        )

"""
Groq Resume Evaluator.
"""

from models.match import MatchResult
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
    ) -> MatchResult:

        prompt = build_match_prompt(
            resume,
            job,
        )

        result = self.client.chat(
            prompt
        )

        # -----------------------------
        # DEBUG
        # -----------------------------
        print("\n========== GROQ RESPONSE ==========")
        print(result)
        print("===================================\n")

        score = result.get(
            "match_score",
            0,
        )

        # Groq sometimes returns 0-1 instead of 0-100
        if isinstance(score, (int, float)) and score <= 1:

            score *= 100

        return MatchResult(

            job=job,

            match_score=score,

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

            recruiter_summary=result.get(
                "recruiter_summary",
                "",
            ),

            recommendations=result.get(
                "recommendations",
                [],
            ),

        )
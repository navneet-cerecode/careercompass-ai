"""
CareerCompass Facade.

Acts as the bridge between the UI and all backend services.
"""

from graph.workflow import build_workflow

from services.resume.parser_service import ResumeParserService
from services.resume.extractor import ResumeExtractor

from services.llm.evaluator import ResumeEvaluator

from services.recommendation.recommendation_engine import (
    RecommendationEngine,
)


class CareerCompass:

    def __init__(self):

        self.workflow = build_workflow()

        self.parser = ResumeParserService()

        self.extractor = ResumeExtractor()

        self.evaluator = ResumeEvaluator()

        self.recommendation_engine = RecommendationEngine()

    # ---------------------------------------------------------
    # Job Search
    # ---------------------------------------------------------

    def search_jobs(
        self,
        role: str,
        location: str,
    ):

        state = {
            "role": role,
            "location": location,
            "resume": None,
            "jobs": [],
            "match_results": [],
        }

        result = self.workflow.invoke(state)

        return result["jobs"]

    # ---------------------------------------------------------
    # Resume
    # ---------------------------------------------------------

    def load_resume(
        self,
        resume_path: str,
    ):

        text = self.parser.parse(
            resume_path
        )

        return self.extractor.extract(
            text
        )

    # ---------------------------------------------------------
    # Recommendation Engine
    # ---------------------------------------------------------

    def recommend_job(
        self,
        resume,
        job,
    ):

        return self.recommendation_engine.evaluate(
            resume,
            job,
        )

    # ---------------------------------------------------------
    # AI Explanation
    # ---------------------------------------------------------

        # ---------------------------------------------------------
    # AI Explanation
    # ---------------------------------------------------------

    def analyze_resume(
        self,
        resume,
        job,
    ):

        match = self.evaluator.evaluate(
            resume,
            job,
        )

        print("\n================ MATCH FROM GROQ ================")
        print(match)
        print("=================================================\n")

        recommendation = self.recommendation_engine.evaluate(
            resume,
            job,
        )

        print("\n================ BEFORE MERGE ===================")
        print(recommendation.matched_skills)
        print(recommendation.missing_skills)
        print("=================================================\n")

        recommendation.matched_skills = match.matched_skills

        recommendation.missing_skills = match.missing_skills

        recommendation.recruiter_summary = (
            match.recruiter_summary
        )

        recommendation.recommendations = (
            match.recommendations
        )

        print("\n================ AFTER MERGE ====================")
        print(recommendation.matched_skills)
        print(recommendation.missing_skills)
        print("=================================================\n")

        return recommendation
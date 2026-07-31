"""
CareerCompass Facade.

Acts as the bridge between the UI and all backend services.
"""

from __future__ import annotations

from functools import cached_property
from typing import TYPE_CHECKING

from graph.workflow import build_workflow
from models.job import Job
from models.job_recommendation import JobRecommendation
from models.resume import Resume

from services.resume.extractor import ResumeExtractor
from services.resume.parser_service import ResumeParserService

if TYPE_CHECKING:
    from services.llm.evaluator import ResumeEvaluator
    from services.recommendation.recommendation_engine import RecommendationEngine
    from services.recommendation.recommendation_service import RecommendationService


class CareerCompass:
    def __init__(self):

        self.workflow = build_workflow()

        self.parser = ResumeParserService()

        self.extractor = ResumeExtractor()

    @cached_property
    def evaluator(self) -> ResumeEvaluator:
        """
        Construct the Groq-backed evaluator only for AI analysis.
        """
        from services.llm.evaluator import ResumeEvaluator

        return ResumeEvaluator()

    @cached_property
    def recommendation_engine(self) -> RecommendationEngine:
        """
        Load the embedding-backed engine only when ranking begins.
        """
        from services.recommendation.recommendation_engine import RecommendationEngine

        return RecommendationEngine()

    @cached_property
    def recommendation_service(self) -> RecommendationService:
        """Construct batch recommendation orchestration only when requested."""
        from services.recommendation.recommendation_service import (
            RecommendationService,
        )

        return RecommendationService(
            engine=self.recommendation_engine,
        )

    # ---------------------------------------------------------
    # Job Search
    # ---------------------------------------------------------

    def search_jobs(
        self,
        role: str,
        location: str,
    ) -> list[Job]:

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
    ) -> Resume:

        text = self.parser.parse(resume_path)

        return self.extractor.extract(text)

    # ---------------------------------------------------------
    # Recommendation Engine
    # ---------------------------------------------------------

    def recommend_job(
        self,
        resume: Resume,
        job: Job,
    ) -> JobRecommendation:

        return self.recommendation_service.recommend_job(
            resume,
            job,
        )

    def recommend_jobs(
        self,
        resume: Resume,
        jobs: list[Job],
    ) -> list[JobRecommendation]:
        return self.recommendation_service.recommend_jobs(
            resume,
            jobs,
        )

    # ---------------------------------------------------------
    # AI Explanation
    # ---------------------------------------------------------

    def analyze_resume(
        self,
        resume: Resume,
        job: Job,
    ) -> JobRecommendation:

        ai_assessment = self.evaluator.evaluate(
            resume,
            job,
        )

        base_assessment = self.recommendation_service.assess_job(
            resume,
            job,
        )

        enriched_assessment = base_assessment.model_copy(
            update={
                "matched_skills": ai_assessment.matched_skills,
                "missing_skills": ai_assessment.missing_skills,
                "recruiter_summary": ai_assessment.recruiter_summary,
                "recommendations": ai_assessment.recommendations,
            }
        )

        return JobRecommendation(
            assessment=enriched_assessment,
        )

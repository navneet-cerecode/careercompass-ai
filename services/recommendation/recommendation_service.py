"""Application service for evaluating and ranking batches of jobs."""

from typing import Protocol

from models.job import Job
from models.job_recommendation import JobRecommendation
from models.match_assessment import MatchAssessment
from models.resume import Resume


class AssessmentEngine(Protocol):
    """Structural contract implemented by recommendation engines."""

    def evaluate(
        self,
        resume: Resume,
        job: Job,
    ) -> MatchAssessment: ...


class RecommendationService:
    """Coordinate deterministic assessments and ranked recommendations."""

    def __init__(
        self,
        engine: AssessmentEngine | None = None,
    ):
        if engine is None:
            from services.recommendation.recommendation_engine import (
                RecommendationEngine,
            )

            engine = RecommendationEngine()

        self.engine = engine

    def assess_job(
        self,
        resume: Resume,
        job: Job,
    ) -> MatchAssessment:
        return self.engine.evaluate(resume, job)

    def assess_jobs(
        self,
        resume: Resume,
        jobs: list[Job],
    ) -> list[MatchAssessment]:
        assessments = [
            self.assess_job(
                resume,
                job,
            )
            for job in jobs
        ]
        return sorted(
            assessments,
            key=lambda assessment: assessment.score,
            reverse=True,
        )

    def recommend_job(
        self,
        resume: Resume,
        job: Job,
    ) -> JobRecommendation:
        return JobRecommendation(
            assessment=self.assess_job(resume, job),
        )

    def recommend_jobs(
        self,
        resume: Resume,
        jobs: list[Job],
    ) -> list[JobRecommendation]:
        return [
            JobRecommendation(
                assessment=assessment,
                rank=rank,
            )
            for rank, assessment in enumerate(
                self.assess_jobs(resume, jobs),
                start=1,
            )
        ]

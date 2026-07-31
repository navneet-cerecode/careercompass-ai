"""Owner-scoped search and recommendation history repositories."""

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from database.models.recommendations import (
    RecommendationRecord,
    SearchRecord,
    SearchResultRecord,
)
from database.repositories.jobs import JobRepository
from models.job import Job
from models.job_recommendation import JobRecommendation
from models.match_assessment import MatchAssessment
from models.score_component import ScoreComponent
from models.skill import Skill
from services.job_discovery.providers.contracts import JobSearchQuery


@dataclass(frozen=True)
class SearchHistory:
    id: UUID
    user_id: UUID
    resume_id: UUID | None
    query: JobSearchQuery
    status: str
    providers_attempted: int
    providers_succeeded: int
    jobs: tuple[Job, ...]


class SearchHistoryRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(
        self,
        *,
        user_id: UUID,
        resume_id: UUID | None,
        query: JobSearchQuery,
        status: str,
        providers_attempted: int,
        providers_succeeded: int,
        jobs: tuple[Job, ...],
    ) -> SearchHistory:
        filters = query.model_dump(
            mode="json",
            exclude={"role", "location"},
        )
        record = SearchRecord(
            user_id=user_id,
            resume_id=resume_id,
            role=query.role,
            location=query.location,
            filters=filters,
            status=status,
            providers_attempted=providers_attempted,
            providers_succeeded=providers_succeeded,
        )
        self.session.add(record)
        self.session.flush()
        self.session.add_all(
            SearchResultRecord(
                search_id=record.id,
                job_id=job.id,
                position=position,
            )
            for position, job in enumerate(jobs, start=1)
        )
        return SearchHistory(
            id=record.id,
            user_id=user_id,
            resume_id=resume_id,
            query=query,
            status=status,
            providers_attempted=providers_attempted,
            providers_succeeded=providers_succeeded,
            jobs=jobs,
        )

    def get(self, *, user_id: UUID, search_id: UUID) -> SearchHistory | None:
        record = self.session.scalar(
            select(SearchRecord).where(
                SearchRecord.id == search_id,
                SearchRecord.user_id == user_id,
            )
        )
        if record is None:
            return None

        result_rows = self.session.scalars(
            select(SearchResultRecord)
            .where(SearchResultRecord.search_id == search_id)
            .order_by(SearchResultRecord.position)
        ).all()
        jobs = JobRepository(self.session).get_many(tuple(row.job_id for row in result_rows))
        query = JobSearchQuery(
            role=record.role,
            location=record.location,
            **record.filters,
        )
        return SearchHistory(
            id=record.id,
            user_id=record.user_id,
            resume_id=record.resume_id,
            query=query,
            status=record.status,
            providers_attempted=record.providers_attempted,
            providers_succeeded=record.providers_succeeded,
            jobs=jobs or (),
        )


class RecommendationHistoryRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def save_many(
        self,
        *,
        user_id: UUID,
        resume_id: UUID,
        recommendations: list[JobRecommendation],
        search_id: UUID | None = None,
    ) -> tuple[JobRecommendation, ...]:
        for recommendation in recommendations:
            assessment = recommendation.assessment
            self.session.add(
                RecommendationRecord(
                    id=recommendation.id,
                    assessment_id=assessment.id,
                    user_id=user_id,
                    resume_id=resume_id,
                    job_id=assessment.job.id,
                    search_id=search_id,
                    score=assessment.score,
                    rank=recommendation.rank,
                    components=[item.model_dump(mode="json") for item in assessment.components],
                    matched_skills=[
                        item.model_dump(mode="json") for item in assessment.matched_skills
                    ],
                    missing_skills=[
                        item.model_dump(mode="json") for item in assessment.missing_skills
                    ],
                    recruiter_summary=assessment.recruiter_summary,
                    next_steps=list(assessment.recommendations),
                    confidence=assessment.confidence,
                    algorithm_version=assessment.algorithm_version,
                )
            )
        self.session.flush()
        return tuple(recommendations)

    def get(
        self,
        *,
        user_id: UUID,
        recommendation_id: UUID,
    ) -> JobRecommendation | None:
        record = self.session.scalar(
            select(RecommendationRecord).where(
                RecommendationRecord.id == recommendation_id,
                RecommendationRecord.user_id == user_id,
            )
        )
        if record is None:
            return None
        job = JobRepository(self.session).get(record.job_id)
        if job is None:
            return None

        assessment = MatchAssessment(
            id=record.assessment_id,
            job=job,
            score=record.score,
            components=[ScoreComponent.model_validate(item) for item in record.components],
            matched_skills=[Skill.model_validate(item) for item in record.matched_skills],
            missing_skills=[Skill.model_validate(item) for item in record.missing_skills],
            recruiter_summary=record.recruiter_summary,
            recommendations=list(record.next_steps),
            confidence=record.confidence,
            algorithm_version=record.algorithm_version,
        )
        return JobRecommendation(
            id=record.id,
            assessment=assessment,
            rank=record.rank,
        )

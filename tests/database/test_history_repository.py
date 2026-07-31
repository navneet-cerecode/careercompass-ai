from database.base import Base
from database.repositories.history import (
    RecommendationHistoryRepository,
    SearchHistoryRepository,
)
from database.repositories.jobs import JobRepository
from database.repositories.resumes import ResumeRepository
from database.repositories.users import UserRepository
from database.session import Database
from models.job import Job
from models.job_recommendation import JobRecommendation
from models.match_assessment import MatchAssessment
from models.resume import Resume
from models.score_component import ScoreComponent
from models.skill import Skill
from services.job_discovery.providers.contracts import DatePosted, JobSearchQuery


def make_database() -> Database:
    database = Database("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(database.engine)
    return database


def test_search_and_recommendation_history_are_reproducible_and_owner_scoped():
    database = make_database()
    with database.session() as session:
        users = UserRepository(session)
        owner = users.create(email="owner@example.com", name="Owner")
        other = users.create(email="other@example.com", name="Other")
        resume = ResumeRepository(session).save_version(
            user_id=owner.id,
            resume=Resume(
                name="Owner",
                raw_text="Owner\nPython engineer",
                skills=[Skill(name="Python")],
            ),
        )
        job = JobRepository(session).upsert(
            Job(
                title="Data Engineer",
                company="Example Corp",
                location="India",
                description="Python and SQL",
                url="https://example.com/jobs/1",
            )
        )
        query = JobSearchQuery(
            role="Data Engineer",
            location="India",
            date_posted=DatePosted.WEEK,
        )
        search = SearchHistoryRepository(session).create(
            user_id=owner.id,
            resume_id=resume.resume.id,
            query=query,
            status="complete",
            providers_attempted=2,
            providers_succeeded=2,
            jobs=(job,),
        )
        recommendation = JobRecommendation(
            assessment=MatchAssessment(
                job=job,
                score=84,
                components=[
                    ScoreComponent(
                        name="Skill Signal",
                        score=90,
                        explanation="Strong overlap",
                    )
                ],
                matched_skills=[Skill(name="Python")],
                missing_skills=[Skill(name="SQL")],
                confidence=0.8,
                algorithm_version="hybrid-v1",
            ),
            rank=1,
        )
        RecommendationHistoryRepository(session).save_many(
            user_id=owner.id,
            resume_id=resume.resume.id,
            search_id=search.id,
            recommendations=[recommendation],
        )

    with database.session() as session:
        search_repository = SearchHistoryRepository(session)
        loaded_search = search_repository.get(
            user_id=owner.id,
            search_id=search.id,
        )
        assert search_repository.get(user_id=other.id, search_id=search.id) is None

        recommendation_repository = RecommendationHistoryRepository(session)
        loaded_recommendation = recommendation_repository.get(
            user_id=owner.id,
            recommendation_id=recommendation.id,
        )
        assert (
            recommendation_repository.get(
                user_id=other.id,
                recommendation_id=recommendation.id,
            )
            is None
        )

    assert loaded_search is not None
    assert loaded_search.query.date_posted == DatePosted.WEEK
    assert loaded_search.jobs[0].id == job.id
    assert loaded_recommendation is not None
    assert loaded_recommendation.assessment.id == recommendation.assessment.id
    assert loaded_recommendation.score == 84
    assert loaded_recommendation.assessment.algorithm_version == "hybrid-v1"
    assert loaded_recommendation.signal_results[0].explanation == "Strong overlap"

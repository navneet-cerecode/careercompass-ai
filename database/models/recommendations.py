"""Persistent search and recommendation history."""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Float, ForeignKey, Integer, JSON, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base


class SearchRecord(Base):
    __tablename__ = "searches"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    resume_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("resumes.id", ondelete="SET NULL"),
        index=True,
    )
    role: Mapped[str] = mapped_column(String(300))
    location: Mapped[str] = mapped_column(String(300))
    filters: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String(30))
    providers_attempted: Mapped[int] = mapped_column(Integer)
    providers_succeeded: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )


class SearchResultRecord(Base):
    __tablename__ = "search_results"

    search_id: Mapped[UUID] = mapped_column(
        ForeignKey("searches.id", ondelete="CASCADE"),
        primary_key=True,
    )
    job_id: Mapped[UUID] = mapped_column(
        ForeignKey("jobs.id", ondelete="CASCADE"),
        primary_key=True,
    )
    position: Mapped[int] = mapped_column(Integer)

    __table_args__ = (UniqueConstraint("search_id", "position", name="uq_search_results_position"),)


class RecommendationRecord(Base):
    __tablename__ = "recommendations"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    assessment_id: Mapped[UUID] = mapped_column()
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    resume_id: Mapped[UUID] = mapped_column(
        ForeignKey("resumes.id", ondelete="CASCADE"),
        index=True,
    )
    job_id: Mapped[UUID] = mapped_column(ForeignKey("jobs.id", ondelete="CASCADE"), index=True)
    search_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("searches.id", ondelete="SET NULL"),
        index=True,
    )
    score: Mapped[float] = mapped_column(Float)
    rank: Mapped[int | None] = mapped_column(Integer)
    components: Mapped[list[dict[str, object]]] = mapped_column(JSON, default=list)
    matched_skills: Mapped[list[dict[str, object]]] = mapped_column(JSON, default=list)
    missing_skills: Mapped[list[dict[str, object]]] = mapped_column(JSON, default=list)
    recruiter_summary: Mapped[str | None] = mapped_column(String(4000))
    next_steps: Mapped[list[str]] = mapped_column(JSON, default=list)
    confidence: Mapped[float | None] = mapped_column(Float)
    algorithm_version: Mapped[str] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

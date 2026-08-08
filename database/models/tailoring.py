"""Durable factual tailoring plans."""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, JSON, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base


class TailoringPlanRecord(Base):
    __tablename__ = "tailoring_plans"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
    )
    resume_id: Mapped[UUID] = mapped_column(
        ForeignKey("resumes.id", ondelete="CASCADE"),
        index=True,
    )
    job_id: Mapped[UUID] = mapped_column(
        ForeignKey("jobs.id", ondelete="CASCADE"),
        index=True,
    )
    skills: Mapped[list[dict]] = mapped_column(JSON, default=list)
    experience: Mapped[list[str]] = mapped_column(JSON, default=list)
    projects: Mapped[list[str]] = mapped_column(JSON, default=list)
    matched_skills: Mapped[list[dict]] = mapped_column(JSON, default=list)
    missing_skills: Mapped[list[dict]] = mapped_column(JSON, default=list)
    evidence: Mapped[list[dict]] = mapped_column(JSON, default=list)
    user_review_required: Mapped[bool] = mapped_column(Boolean, default=True)
    algorithm_version: Mapped[str] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "resume_id",
            "job_id",
            "algorithm_version",
            name="uq_tailoring_plans_owner_source_job_algorithm",
        ),
    )


class TailoredResumeRecord(Base):
    __tablename__ = "tailored_resumes"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
    )
    plan_id: Mapped[UUID] = mapped_column(
        ForeignKey("tailoring_plans.id", ondelete="CASCADE"),
        index=True,
    )
    source_resume_id: Mapped[UUID] = mapped_column(
        ForeignKey("resumes.id", ondelete="CASCADE"),
        index=True,
    )
    job_id: Mapped[UUID] = mapped_column(
        ForeignKey("jobs.id", ondelete="CASCADE"),
        index=True,
    )
    version: Mapped[int] = mapped_column(Integer)
    original_content: Mapped[dict] = mapped_column(JSON)
    suggested_content: Mapped[dict] = mapped_column(JSON)
    accepted_content: Mapped[dict] = mapped_column(JSON)
    selections: Mapped[dict] = mapped_column(JSON)
    verification_status: Mapped[str] = mapped_column(String(50), default="pending_review")
    user_review_required: Mapped[bool] = mapped_column(Boolean, default=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "plan_id",
            "version",
            name="uq_tailored_resumes_owner_plan_version",
        ),
    )


class CoverLetterRecord(Base):
    __tablename__ = "cover_letters"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
    )
    plan_id: Mapped[UUID] = mapped_column(
        ForeignKey("tailoring_plans.id", ondelete="CASCADE"),
        index=True,
    )
    source_resume_id: Mapped[UUID] = mapped_column(
        ForeignKey("resumes.id", ondelete="CASCADE"),
        index=True,
    )
    job_id: Mapped[UUID] = mapped_column(
        ForeignKey("jobs.id", ondelete="CASCADE"),
        index=True,
    )
    version: Mapped[int] = mapped_column(Integer)
    suggested_content: Mapped[dict] = mapped_column(JSON)
    accepted_content: Mapped[dict] = mapped_column(JSON)
    evidence: Mapped[list[dict]] = mapped_column(JSON, default=list)
    verification_status: Mapped[str] = mapped_column(String(50), default="pending_review")
    user_review_required: Mapped[bool] = mapped_column(Boolean, default=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "plan_id",
            "version",
            name="uq_cover_letters_owner_plan_version",
        ),
    )

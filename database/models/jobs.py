"""Persistent job and provider-source records."""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base


class JobRecord(Base):
    __tablename__ = "jobs"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    fingerprint: Mapped[str] = mapped_column(String(64), unique=True)
    title: Mapped[str] = mapped_column(String(300))
    normalized_title: Mapped[str] = mapped_column(String(300))
    company: Mapped[str] = mapped_column(String(300))
    normalized_company: Mapped[str] = mapped_column(String(300))
    location: Mapped[str] = mapped_column(String(300))
    normalized_location: Mapped[str] = mapped_column(String(300))
    description: Mapped[str] = mapped_column(Text, default="")
    experience_level: Mapped[str] = mapped_column(String(50))
    employment_type: Mapped[str] = mapped_column(String(50))
    primary_source: Mapped[str] = mapped_column(String(50))
    apply_url: Mapped[str] = mapped_column(String(2048))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    first_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    sources: Mapped[list["JobSourceRecord"]] = relationship(
        back_populates="job",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index(
            "ix_jobs_normalized_identity",
            "normalized_company",
            "normalized_title",
            "normalized_location",
        ),
    )


class JobSourceRecord(Base):
    __tablename__ = "job_sources"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    job_id: Mapped[UUID] = mapped_column(
        ForeignKey("jobs.id", ondelete="CASCADE"),
        index=True,
    )
    provider_name: Mapped[str] = mapped_column(String(100))
    external_id: Mapped[str | None] = mapped_column(String(500))
    source_url: Mapped[str] = mapped_column(String(2048))
    first_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    job: Mapped[JobRecord] = relationship(back_populates="sources")

    __table_args__ = (
        UniqueConstraint(
            "provider_name",
            "source_url",
            name="uq_job_sources_provider_url",
        ),
        Index(
            "ix_job_sources_provider_external_id",
            "provider_name",
            "external_id",
        ),
    )

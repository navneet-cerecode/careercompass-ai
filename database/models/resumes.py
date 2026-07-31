"""Versioned resume and normalized skill records."""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base


class ResumeRecord(Base):
    __tablename__ = "resumes"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
    )
    version: Mapped[int] = mapped_column(Integer)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    original_filename: Mapped[str | None] = mapped_column(String(500))
    name: Mapped[str] = mapped_column(String(200))
    email: Mapped[str | None] = mapped_column(String(320))
    phone: Mapped[str | None] = mapped_column(String(100))
    linkedin: Mapped[str | None] = mapped_column(String(2048))
    github: Mapped[str | None] = mapped_column(String(2048))
    raw_text: Mapped[str] = mapped_column(Text)
    content_sha256: Mapped[str] = mapped_column(String(64), index=True)
    education: Mapped[list[str]] = mapped_column(JSON, default=list)
    experience: Mapped[list[str]] = mapped_column(JSON, default=list)
    projects: Mapped[list[str]] = mapped_column(JSON, default=list)
    certifications: Mapped[list[str]] = mapped_column(JSON, default=list)
    achievements: Mapped[list[str]] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    user: Mapped["UserRecord"] = relationship(back_populates="resumes")
    skill_links: Mapped[list["ResumeSkillRecord"]] = relationship(
        back_populates="resume",
        cascade="all, delete-orphan",
        order_by="ResumeSkillRecord.position",
    )

    __table_args__ = (
        UniqueConstraint("user_id", "version", name="uq_resumes_user_version"),
        Index("ix_resumes_user_active", "user_id", "is_active"),
    )


class SkillRecord(Base):
    __tablename__ = "skills"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    normalized_name: Mapped[str] = mapped_column(String(200), unique=True)
    display_name: Mapped[str] = mapped_column(String(200))
    category: Mapped[str | None] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    resume_links: Mapped[list["ResumeSkillRecord"]] = relationship(
        back_populates="skill",
        cascade="all, delete-orphan",
    )


class ResumeSkillRecord(Base):
    __tablename__ = "resume_skills"

    resume_id: Mapped[UUID] = mapped_column(
        ForeignKey("resumes.id", ondelete="CASCADE"),
        primary_key=True,
    )
    skill_id: Mapped[UUID] = mapped_column(
        ForeignKey("skills.id", ondelete="CASCADE"),
        primary_key=True,
    )
    position: Mapped[int] = mapped_column(Integer)

    resume: Mapped[ResumeRecord] = relationship(back_populates="skill_links")
    skill: Mapped[SkillRecord] = relationship(back_populates="resume_links")


from database.models.users import UserRecord  # noqa: E402

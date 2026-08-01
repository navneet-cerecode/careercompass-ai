"""Durable background-task lifecycle records."""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base


class BackgroundTaskRecord(Base):
    __tablename__ = "background_tasks"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
    )
    task_type: Mapped[str] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(String(20))
    resource_id: Mapped[UUID | None] = mapped_column(index=True)
    idempotency_fingerprint: Mapped[str] = mapped_column(String(64))
    attempt_count: Mapped[int] = mapped_column(Integer, default=0)
    max_attempts: Mapped[int] = mapped_column(Integer)
    error_code: Mapped[str | None] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    __table_args__ = (
        CheckConstraint(
            "status IN ('queued', 'running', 'succeeded', 'failed', 'cancelled')",
            name="status",
        ),
        CheckConstraint(
            "attempt_count >= 0",
            name="attempt_count_nonnegative",
        ),
        CheckConstraint(
            "max_attempts BETWEEN 1 AND 11",
            name="max_attempts_bounds",
        ),
        CheckConstraint(
            "attempt_count <= max_attempts",
            name="attempt_count_within_limit",
        ),
        UniqueConstraint(
            "idempotency_fingerprint",
            name="uq_background_tasks_idempotency_fingerprint",
        ),
        Index(
            "ix_background_tasks_status_created",
            "status",
            "created_at",
        ),
        Index(
            "ix_background_tasks_user_status",
            "user_id",
            "status",
        ),
    )

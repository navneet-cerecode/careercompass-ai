"""Purpose-built durable records for asynchronous job discovery."""

from uuid import UUID

from sqlalchemy import Boolean, ForeignKey, Integer, JSON, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base


class JobDiscoveryTaskRecord(Base):
    __tablename__ = "job_discovery_tasks"

    task_id: Mapped[UUID] = mapped_column(
        ForeignKey("background_tasks.id", ondelete="CASCADE"),
        primary_key=True,
    )
    role: Mapped[str] = mapped_column(String(300))
    location: Mapped[str] = mapped_column(String(300))
    country: Mapped[str | None] = mapped_column(String(2))
    page: Mapped[int] = mapped_column(Integer)
    page_size: Mapped[int] = mapped_column(Integer)
    remote_only: Mapped[bool | None] = mapped_column(Boolean)
    employment_types: Mapped[list[str]] = mapped_column(JSON, default=list)
    date_posted: Mapped[str] = mapped_column(String(20))
    result_status: Mapped[str | None] = mapped_column(String(20))
    provider_names_failed: Mapped[list[str]] = mapped_column(JSON, default=list)
    providers_attempted: Mapped[int | None] = mapped_column(Integer)
    providers_succeeded: Mapped[int | None] = mapped_column(Integer)


class JobDiscoveryTaskResultRecord(Base):
    __tablename__ = "job_discovery_task_results"

    task_id: Mapped[UUID] = mapped_column(
        ForeignKey("job_discovery_tasks.task_id", ondelete="CASCADE"),
        primary_key=True,
    )
    job_id: Mapped[UUID] = mapped_column(
        ForeignKey("jobs.id", ondelete="CASCADE"),
        primary_key=True,
    )
    position: Mapped[int] = mapped_column(Integer)

    __table_args__ = (
        UniqueConstraint(
            "task_id",
            "position",
            name="uq_job_discovery_task_results_position",
        ),
    )

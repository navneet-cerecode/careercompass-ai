"""Create durable asynchronous job-discovery inputs and results.

Revision ID: 0007
Revises: 0006
Create Date: 2026-08-02
"""

import sqlalchemy as sa
from alembic import op

revision: str = "0007"
down_revision: str | None = "0006"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.create_table(
        "job_discovery_tasks",
        sa.Column("task_id", sa.Uuid(), nullable=False),
        sa.Column("role", sa.String(length=300), nullable=False),
        sa.Column("location", sa.String(length=300), nullable=False),
        sa.Column("country", sa.String(length=2), nullable=True),
        sa.Column("page", sa.Integer(), nullable=False),
        sa.Column("page_size", sa.Integer(), nullable=False),
        sa.Column("remote_only", sa.Boolean(), nullable=True),
        sa.Column("employment_types", sa.JSON(), nullable=False),
        sa.Column("date_posted", sa.String(length=20), nullable=False),
        sa.Column("result_status", sa.String(length=20), nullable=True),
        sa.Column("provider_names_failed", sa.JSON(), nullable=False),
        sa.Column("providers_attempted", sa.Integer(), nullable=True),
        sa.Column("providers_succeeded", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ["task_id"],
            ["background_tasks.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("task_id", name=op.f("pk_job_discovery_tasks")),
    )
    op.create_table(
        "job_discovery_task_results",
        sa.Column("task_id", sa.Uuid(), nullable=False),
        sa.Column("job_id", sa.Uuid(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["job_id"],
            ["jobs.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["task_id"],
            ["job_discovery_tasks.task_id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint(
            "task_id",
            "job_id",
            name=op.f("pk_job_discovery_task_results"),
        ),
        sa.UniqueConstraint(
            "task_id",
            "position",
            name="uq_job_discovery_task_results_position",
        ),
    )
    op.create_index(
        op.f("ix_job_discovery_task_results_job_id"),
        "job_discovery_task_results",
        ["job_id"],
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_job_discovery_task_results_job_id"),
        table_name="job_discovery_task_results",
    )
    op.drop_table("job_discovery_task_results")
    op.drop_table("job_discovery_tasks")

"""Create durable background task lifecycle records.

Revision ID: 0006
Revises: 0005
Create Date: 2026-08-02
"""

import sqlalchemy as sa
from alembic import op

revision: str = "0006"
down_revision: str | None = "0005"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.create_table(
        "background_tasks",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=True),
        sa.Column("task_type", sa.String(length=100), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("resource_id", sa.Uuid(), nullable=True),
        sa.Column("idempotency_fingerprint", sa.String(length=64), nullable=False),
        sa.Column("attempt_count", sa.Integer(), nullable=False),
        sa.Column("max_attempts", sa.Integer(), nullable=False),
        sa.Column("error_code", sa.String(length=100), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "attempt_count >= 0",
            name=op.f("ck_background_tasks_attempt_count_nonnegative"),
        ),
        sa.CheckConstraint(
            "attempt_count <= max_attempts",
            name=op.f("ck_background_tasks_attempt_count_within_limit"),
        ),
        sa.CheckConstraint(
            "max_attempts BETWEEN 1 AND 11",
            name=op.f("ck_background_tasks_max_attempts_bounds"),
        ),
        sa.CheckConstraint(
            "status IN ('queued', 'running', 'succeeded', 'failed', 'cancelled')",
            name=op.f("ck_background_tasks_status"),
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_background_tasks")),
        sa.UniqueConstraint(
            "idempotency_fingerprint",
            name="uq_background_tasks_idempotency_fingerprint",
        ),
    )
    op.create_index(
        op.f("ix_background_tasks_resource_id"),
        "background_tasks",
        ["resource_id"],
    )
    op.create_index(
        "ix_background_tasks_status_created",
        "background_tasks",
        ["status", "created_at"],
    )
    op.create_index(
        op.f("ix_background_tasks_user_id"),
        "background_tasks",
        ["user_id"],
    )
    op.create_index(
        "ix_background_tasks_user_status",
        "background_tasks",
        ["user_id", "status"],
    )


def downgrade() -> None:
    op.drop_index("ix_background_tasks_user_status", table_name="background_tasks")
    op.drop_index(op.f("ix_background_tasks_user_id"), table_name="background_tasks")
    op.drop_index("ix_background_tasks_status_created", table_name="background_tasks")
    op.drop_index(op.f("ix_background_tasks_resource_id"), table_name="background_tasks")
    op.drop_table("background_tasks")

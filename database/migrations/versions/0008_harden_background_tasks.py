"""Add task recovery metadata and a transactional publication outbox.

Revision ID: 0008
Revises: 0007
Create Date: 2026-08-02
"""

import sqlalchemy as sa
from alembic import op

revision: str = "0008"
down_revision: str | None = "0007"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    with op.batch_alter_table("background_tasks") as batch:
        batch.add_column(sa.Column("heartbeat_at", sa.DateTime(timezone=True)))
        batch.add_column(sa.Column("cancel_requested_at", sa.DateTime(timezone=True)))
        batch.create_index(
            "ix_background_tasks_status_heartbeat",
            ["status", "heartbeat_at"],
        )

    op.create_table(
        "task_outbox",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("task_id", sa.Uuid(), nullable=False),
        sa.Column("actor_name", sa.String(length=100), nullable=False),
        sa.Column("attempt_count", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.Column("last_attempt_at", sa.DateTime(timezone=True)),
        sa.Column("published_at", sa.DateTime(timezone=True)),
        sa.CheckConstraint(
            "attempt_count >= 0",
            name=op.f("ck_task_outbox_attempt_count_nonnegative"),
        ),
        sa.ForeignKeyConstraint(
            ["task_id"],
            ["background_tasks.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_task_outbox")),
        sa.UniqueConstraint("task_id", name=op.f("uq_task_outbox_task_id")),
    )
    op.create_index(
        "ix_task_outbox_unpublished",
        "task_outbox",
        ["published_at", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_task_outbox_unpublished", table_name="task_outbox")
    op.drop_table("task_outbox")
    with op.batch_alter_table("background_tasks") as batch:
        batch.drop_index("ix_background_tasks_status_heartbeat")
        batch.drop_column("cancel_requested_at")
        batch.drop_column("heartbeat_at")

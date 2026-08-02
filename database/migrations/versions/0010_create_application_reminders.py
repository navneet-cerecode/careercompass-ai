"""Create durable application reminders.

Revision ID: 0010
Revises: 0009
Create Date: 2026-08-02
"""

import sqlalchemy as sa
from alembic import op

revision: str = "0010"
down_revision: str | None = "0009"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.create_table(
        "application_reminders",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("application_id", sa.Uuid(), nullable=False),
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("next_action", sa.String(length=500), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("dismissed_at", sa.DateTime(timezone=True), nullable=True),
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
        sa.ForeignKeyConstraint(["application_id"], ["applications.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_application_reminders")),
        sa.UniqueConstraint(
            "application_id",
            "due_at",
            name="uq_application_reminders_application_due",
        ),
    )
    op.create_index(
        op.f("ix_application_reminders_application_id"),
        "application_reminders",
        ["application_id"],
    )
    op.create_index(
        op.f("ix_application_reminders_user_id"),
        "application_reminders",
        ["user_id"],
    )
    op.create_index(
        "ix_application_reminders_user_status_due",
        "application_reminders",
        ["user_id", "status", "due_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_application_reminders_user_status_due",
        table_name="application_reminders",
    )
    op.drop_index(
        op.f("ix_application_reminders_user_id"),
        table_name="application_reminders",
    )
    op.drop_index(
        op.f("ix_application_reminders_application_id"),
        table_name="application_reminders",
    )
    op.drop_table("application_reminders")

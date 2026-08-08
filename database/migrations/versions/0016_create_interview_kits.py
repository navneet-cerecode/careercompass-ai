"""Create evidence-grounded interview kits.

Revision ID: 0016
Revises: 0015
Create Date: 2026-08-09
"""

import sqlalchemy as sa
from alembic import op

revision: str = "0016"
down_revision: str | None = "0015"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.create_table(
        "interview_kits",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("application_id", sa.Uuid(), nullable=False),
        sa.Column("resume_id", sa.Uuid(), nullable=False),
        sa.Column("questions", sa.JSON(), nullable=False),
        sa.Column("responses", sa.JSON(), nullable=False),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
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
        sa.ForeignKeyConstraint(
            ["application_id"],
            ["applications.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(["resume_id"], ["resumes.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_interview_kits")),
        sa.UniqueConstraint(
            "application_id",
            name=op.f("uq_interview_kits_application_id"),
        ),
    )
    for column in ("application_id", "resume_id", "user_id"):
        op.create_index(
            op.f(f"ix_interview_kits_{column}"),
            "interview_kits",
            [column],
        )


def downgrade() -> None:
    for column in ("user_id", "resume_id", "application_id"):
        op.drop_index(op.f(f"ix_interview_kits_{column}"), table_name="interview_kits")
    op.drop_table("interview_kits")

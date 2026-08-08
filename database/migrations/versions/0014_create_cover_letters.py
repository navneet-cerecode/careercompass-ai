"""Create versioned cover letters.

Revision ID: 0014
Revises: 0013
Create Date: 2026-08-08
"""

import sqlalchemy as sa
from alembic import op

revision: str = "0014"
down_revision: str | None = "0013"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.create_table(
        "cover_letters",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("plan_id", sa.Uuid(), nullable=False),
        sa.Column("source_resume_id", sa.Uuid(), nullable=False),
        sa.Column("job_id", sa.Uuid(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("suggested_content", sa.JSON(), nullable=False),
        sa.Column("accepted_content", sa.JSON(), nullable=False),
        sa.Column("evidence", sa.JSON(), nullable=False),
        sa.Column("verification_status", sa.String(length=50), nullable=False),
        sa.Column("user_review_required", sa.Boolean(), nullable=False),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
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
        sa.ForeignKeyConstraint(["job_id"], ["jobs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["plan_id"], ["tailoring_plans.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["source_resume_id"], ["resumes.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_cover_letters")),
        sa.UniqueConstraint(
            "user_id",
            "plan_id",
            "version",
            name="uq_cover_letters_owner_plan_version",
        ),
    )
    op.create_index(op.f("ix_cover_letters_job_id"), "cover_letters", ["job_id"])
    op.create_index(op.f("ix_cover_letters_plan_id"), "cover_letters", ["plan_id"])
    op.create_index(
        op.f("ix_cover_letters_source_resume_id"),
        "cover_letters",
        ["source_resume_id"],
    )
    op.create_index(op.f("ix_cover_letters_user_id"), "cover_letters", ["user_id"])


def downgrade() -> None:
    op.drop_index(op.f("ix_cover_letters_user_id"), table_name="cover_letters")
    op.drop_index(op.f("ix_cover_letters_source_resume_id"), table_name="cover_letters")
    op.drop_index(op.f("ix_cover_letters_plan_id"), table_name="cover_letters")
    op.drop_index(op.f("ix_cover_letters_job_id"), table_name="cover_letters")
    op.drop_table("cover_letters")

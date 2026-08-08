"""Create versioned tailored resumes.

Revision ID: 0013
Revises: 0012
Create Date: 2026-08-08
"""

import sqlalchemy as sa
from alembic import op

revision: str = "0013"
down_revision: str | None = "0012"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.create_table(
        "tailored_resumes",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("plan_id", sa.Uuid(), nullable=False),
        sa.Column("source_resume_id", sa.Uuid(), nullable=False),
        sa.Column("job_id", sa.Uuid(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("original_content", sa.JSON(), nullable=False),
        sa.Column("suggested_content", sa.JSON(), nullable=False),
        sa.Column("accepted_content", sa.JSON(), nullable=False),
        sa.Column("selections", sa.JSON(), nullable=False),
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
        sa.ForeignKeyConstraint(
            ["source_resume_id"],
            ["resumes.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_tailored_resumes")),
        sa.UniqueConstraint(
            "user_id",
            "plan_id",
            "version",
            name="uq_tailored_resumes_owner_plan_version",
        ),
    )
    op.create_index(op.f("ix_tailored_resumes_job_id"), "tailored_resumes", ["job_id"])
    op.create_index(op.f("ix_tailored_resumes_plan_id"), "tailored_resumes", ["plan_id"])
    op.create_index(
        op.f("ix_tailored_resumes_source_resume_id"),
        "tailored_resumes",
        ["source_resume_id"],
    )
    op.create_index(op.f("ix_tailored_resumes_user_id"), "tailored_resumes", ["user_id"])


def downgrade() -> None:
    op.drop_index(op.f("ix_tailored_resumes_user_id"), table_name="tailored_resumes")
    op.drop_index(
        op.f("ix_tailored_resumes_source_resume_id"),
        table_name="tailored_resumes",
    )
    op.drop_index(op.f("ix_tailored_resumes_plan_id"), table_name="tailored_resumes")
    op.drop_index(op.f("ix_tailored_resumes_job_id"), table_name="tailored_resumes")
    op.drop_table("tailored_resumes")

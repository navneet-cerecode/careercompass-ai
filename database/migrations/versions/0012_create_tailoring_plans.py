"""Create factual tailoring plans.

Revision ID: 0012
Revises: 0011
Create Date: 2026-08-08
"""

import sqlalchemy as sa
from alembic import op

revision: str = "0012"
down_revision: str | None = "0011"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.add_column(
        "jobs",
        sa.Column(
            "required_skills",
            sa.JSON(),
            server_default=sa.text("'[]'"),
            nullable=False,
        ),
    )
    op.create_table(
        "tailoring_plans",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("resume_id", sa.Uuid(), nullable=False),
        sa.Column("job_id", sa.Uuid(), nullable=False),
        sa.Column("skills", sa.JSON(), nullable=False),
        sa.Column("experience", sa.JSON(), nullable=False),
        sa.Column("projects", sa.JSON(), nullable=False),
        sa.Column("matched_skills", sa.JSON(), nullable=False),
        sa.Column("missing_skills", sa.JSON(), nullable=False),
        sa.Column("evidence", sa.JSON(), nullable=False),
        sa.Column("user_review_required", sa.Boolean(), nullable=False),
        sa.Column("algorithm_version", sa.String(length=100), nullable=False),
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
        sa.ForeignKeyConstraint(["resume_id"], ["resumes.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_tailoring_plans")),
        sa.UniqueConstraint(
            "user_id",
            "resume_id",
            "job_id",
            "algorithm_version",
            name="uq_tailoring_plans_owner_source_job_algorithm",
        ),
    )
    op.create_index(op.f("ix_tailoring_plans_job_id"), "tailoring_plans", ["job_id"])
    op.create_index(
        op.f("ix_tailoring_plans_resume_id"),
        "tailoring_plans",
        ["resume_id"],
    )
    op.create_index(op.f("ix_tailoring_plans_user_id"), "tailoring_plans", ["user_id"])


def downgrade() -> None:
    op.drop_index(op.f("ix_tailoring_plans_user_id"), table_name="tailoring_plans")
    op.drop_index(op.f("ix_tailoring_plans_resume_id"), table_name="tailoring_plans")
    op.drop_index(op.f("ix_tailoring_plans_job_id"), table_name="tailoring_plans")
    op.drop_table("tailoring_plans")
    op.drop_column("jobs", "required_skills")

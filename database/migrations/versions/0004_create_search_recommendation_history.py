"""Create search and recommendation history.

Revision ID: 0004
Revises: 0003
Create Date: 2026-08-01
"""

import sqlalchemy as sa
from alembic import op

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.create_table(
        "searches",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("resume_id", sa.Uuid(), nullable=True),
        sa.Column("role", sa.String(length=300), nullable=False),
        sa.Column("location", sa.String(length=300), nullable=False),
        sa.Column("filters", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("providers_attempted", sa.Integer(), nullable=False),
        sa.Column("providers_succeeded", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["resume_id"], ["resumes.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_searches")),
    )
    op.create_index(op.f("ix_searches_resume_id"), "searches", ["resume_id"])
    op.create_index(op.f("ix_searches_user_id"), "searches", ["user_id"])
    op.create_table(
        "search_results",
        sa.Column("search_id", sa.Uuid(), nullable=False),
        sa.Column("job_id", sa.Uuid(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["job_id"], ["jobs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["search_id"], ["searches.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("search_id", "job_id", name=op.f("pk_search_results")),
        sa.UniqueConstraint(
            "search_id",
            "position",
            name="uq_search_results_position",
        ),
    )
    op.create_table(
        "recommendations",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("assessment_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("resume_id", sa.Uuid(), nullable=False),
        sa.Column("job_id", sa.Uuid(), nullable=False),
        sa.Column("search_id", sa.Uuid(), nullable=True),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column("rank", sa.Integer(), nullable=True),
        sa.Column("components", sa.JSON(), nullable=False),
        sa.Column("matched_skills", sa.JSON(), nullable=False),
        sa.Column("missing_skills", sa.JSON(), nullable=False),
        sa.Column("recruiter_summary", sa.String(length=4000), nullable=True),
        sa.Column("next_steps", sa.JSON(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("algorithm_version", sa.String(length=100), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["job_id"], ["jobs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["resume_id"], ["resumes.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["search_id"], ["searches.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_recommendations")),
    )
    op.create_index(
        op.f("ix_recommendations_job_id"),
        "recommendations",
        ["job_id"],
    )
    op.create_index(
        op.f("ix_recommendations_resume_id"),
        "recommendations",
        ["resume_id"],
    )
    op.create_index(
        op.f("ix_recommendations_search_id"),
        "recommendations",
        ["search_id"],
    )
    op.create_index(
        op.f("ix_recommendations_user_id"),
        "recommendations",
        ["user_id"],
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_recommendations_user_id"), table_name="recommendations")
    op.drop_index(op.f("ix_recommendations_search_id"), table_name="recommendations")
    op.drop_index(op.f("ix_recommendations_resume_id"), table_name="recommendations")
    op.drop_index(op.f("ix_recommendations_job_id"), table_name="recommendations")
    op.drop_table("recommendations")
    op.drop_table("search_results")
    op.drop_index(op.f("ix_searches_user_id"), table_name="searches")
    op.drop_index(op.f("ix_searches_resume_id"), table_name="searches")
    op.drop_table("searches")

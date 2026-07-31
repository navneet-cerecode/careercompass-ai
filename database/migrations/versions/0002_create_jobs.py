"""Create durable jobs and source attribution.

Revision ID: 0002
Revises: 0001
Create Date: 2026-08-01
"""

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.create_table(
        "jobs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("fingerprint", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=300), nullable=False),
        sa.Column("normalized_title", sa.String(length=300), nullable=False),
        sa.Column("company", sa.String(length=300), nullable=False),
        sa.Column("normalized_company", sa.String(length=300), nullable=False),
        sa.Column("location", sa.String(length=300), nullable=False),
        sa.Column("normalized_location", sa.String(length=300), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("experience_level", sa.String(length=50), nullable=False),
        sa.Column("employment_type", sa.String(length=50), nullable=False),
        sa.Column("primary_source", sa.String(length=50), nullable=False),
        sa.Column("apply_url", sa.String(length=2048), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column(
            "first_seen_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.Column(
            "last_seen_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
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
        sa.PrimaryKeyConstraint("id", name=op.f("pk_jobs")),
        sa.UniqueConstraint("fingerprint", name=op.f("uq_jobs_fingerprint")),
    )
    op.create_index(
        "ix_jobs_normalized_identity",
        "jobs",
        ["normalized_company", "normalized_title", "normalized_location"],
        unique=False,
    )
    op.create_table(
        "job_sources",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("job_id", sa.Uuid(), nullable=False),
        sa.Column("provider_name", sa.String(length=100), nullable=False),
        sa.Column("external_id", sa.String(length=500), nullable=True),
        sa.Column("source_url", sa.String(length=2048), nullable=False),
        sa.Column(
            "first_seen_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.Column(
            "last_seen_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["job_id"],
            ["jobs.id"],
            name=op.f("fk_job_sources_job_id_jobs"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_job_sources")),
        sa.UniqueConstraint(
            "provider_name",
            "source_url",
            name="uq_job_sources_provider_url",
        ),
    )
    op.create_index(
        op.f("ix_job_sources_job_id"),
        "job_sources",
        ["job_id"],
        unique=False,
    )
    op.create_index(
        "ix_job_sources_provider_external_id",
        "job_sources",
        ["provider_name", "external_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_job_sources_provider_external_id", table_name="job_sources")
    op.drop_index(op.f("ix_job_sources_job_id"), table_name="job_sources")
    op.drop_table("job_sources")
    op.drop_index("ix_jobs_normalized_identity", table_name="jobs")
    op.drop_table("jobs")

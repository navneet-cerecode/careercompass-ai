"""Create review-first application packets.

Revision ID: 0015
Revises: 0014
Create Date: 2026-08-09
"""

import sqlalchemy as sa
from alembic import op

revision: str = "0015"
down_revision: str | None = "0014"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.create_table(
        "application_packets",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("application_id", sa.Uuid(), nullable=False),
        sa.Column("source_resume_id", sa.Uuid(), nullable=True),
        sa.Column("tailored_resume_id", sa.Uuid(), nullable=True),
        sa.Column("cover_letter_id", sa.Uuid(), nullable=True),
        sa.Column("job_details_reviewed", sa.Boolean(), nullable=False),
        sa.Column("resume_reviewed", sa.Boolean(), nullable=False),
        sa.Column("cover_letter_reviewed", sa.Boolean(), nullable=False),
        sa.Column("employer_questions_reviewed", sa.Boolean(), nullable=False),
        sa.Column("ready_at", sa.DateTime(timezone=True), nullable=True),
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
        sa.ForeignKeyConstraint(
            ["cover_letter_id"],
            ["cover_letters.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["source_resume_id"],
            ["resumes.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["tailored_resume_id"],
            ["tailored_resumes.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_application_packets")),
        sa.UniqueConstraint("application_id", name=op.f("uq_application_packets_application_id")),
    )
    for column in (
        "application_id",
        "cover_letter_id",
        "source_resume_id",
        "tailored_resume_id",
        "user_id",
    ):
        op.create_index(
            op.f(f"ix_application_packets_{column}"),
            "application_packets",
            [column],
        )


def downgrade() -> None:
    for column in (
        "user_id",
        "tailored_resume_id",
        "source_resume_id",
        "cover_letter_id",
        "application_id",
    ):
        op.drop_index(
            op.f(f"ix_application_packets_{column}"),
            table_name="application_packets",
        )
    op.drop_table("application_packets")

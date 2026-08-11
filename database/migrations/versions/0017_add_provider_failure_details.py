"""Add sanitized provider failure details.

Revision ID: 0017
Revises: 0016
Create Date: 2026-08-12
"""

import sqlalchemy as sa
from alembic import op

revision: str = "0017"
down_revision: str | None = "0016"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.add_column(
        "job_discovery_tasks",
        sa.Column(
            "provider_failures",
            sa.JSON(),
            server_default=sa.text("'[]'"),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_column("job_discovery_tasks", "provider_failures")

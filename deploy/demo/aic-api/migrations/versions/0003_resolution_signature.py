"""Add structured incident signature to approved resolutions."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003_resolution_signature"
down_revision: str | None = "0002_resolutions"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("resolutions", sa.Column("incident_type", sa.String(length=100), nullable=True))
    op.add_column("resolutions", sa.Column("failure_reason", sa.String(length=100), nullable=True))
    op.add_column("resolutions", sa.Column("resource_kind", sa.String(length=100), nullable=True))


def downgrade() -> None:
    op.drop_column("resolutions", "resource_kind")
    op.drop_column("resolutions", "failure_reason")
    op.drop_column("resolutions", "incident_type")

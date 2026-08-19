"""Persist HolmesGPT human tool approvals."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0004_tool_approvals"
down_revision: str | None = "0003_resolution_signature"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "tool_approvals",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("conversation_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("request_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("requests.request_id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("pending_calls_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("conversation_history_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("approved_by", sa.String(length=255), nullable=True),
        sa.Column("decisions_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("final_response_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_tool_approvals_status_expires", "tool_approvals", ["status", "expires_at"])


def downgrade() -> None:
    op.drop_index("ix_tool_approvals_status_expires", table_name="tool_approvals")
    op.drop_table("tool_approvals")

"""Audit System extensions: before/after state, tenant scoping, session activity.

Revision ID: 013
Revises: 012
Create Date: 2026-04-12

Extends the existing audit_logs table rather than creating a parallel
audit_events table:
- adds action_type (granular enum values)
- adds before_state / after_state JSONB for change tracking
- adds tenant_id FK + session_id FK for scoping
- adds duration_ms for performance observability

Creates user_session_activity table for per-session page tracking
(distinct from the auth user_sessions table -- session here means
a single JWT session's browsing activity).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID


revision: str = "013"
down_revision: str = "012"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Extend audit_logs
    op.add_column("audit_logs", sa.Column("tenant_id", UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=True))
    op.add_column("audit_logs", sa.Column("session_id", UUID(as_uuid=True), sa.ForeignKey("user_sessions.id", ondelete="SET NULL"), nullable=True))
    op.add_column("audit_logs", sa.Column("action_type", sa.String(50), nullable=True))  # enum values as strings
    op.add_column("audit_logs", sa.Column("before_state", JSONB, nullable=True))
    op.add_column("audit_logs", sa.Column("after_state", JSONB, nullable=True))
    op.add_column("audit_logs", sa.Column("duration_ms", sa.Float, nullable=True))
    op.add_column("audit_logs", sa.Column("request_id", sa.String(50), nullable=True))

    op.create_index("ix_audit_logs_tenant_created", "audit_logs", ["tenant_id", "created_at"])
    op.create_index("ix_audit_logs_action_type", "audit_logs", ["action_type"])
    op.create_index("ix_audit_logs_request", "audit_logs", ["request_id"])

    # user_session_activity: page-view and action tracking within a session
    op.create_table(
        "user_session_activity",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        # session_id is nullable because linking a request back to the
        # originating UserSession row requires a session cache that is
        # deferred to a later iteration. Populated as soon as available.
        sa.Column("session_id", UUID(as_uuid=True), sa.ForeignKey("user_sessions.id", ondelete="SET NULL"), nullable=True),
        sa.Column("tenant_id", UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("path", sa.String(500), nullable=False),
        sa.Column("method", sa.String(10), nullable=False),
        sa.Column("status_code", sa.Integer, nullable=True),
        sa.Column("duration_ms", sa.Float, nullable=True),
        sa.Column("request_id", sa.String(50), nullable=True),
        sa.Column("occurred_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_user_session_activity_session", "user_session_activity", ["session_id"])
    op.create_index("ix_user_session_activity_user_time", "user_session_activity", ["user_id", "occurred_at"])
    op.create_index("ix_user_session_activity_request", "user_session_activity", ["request_id"])


def downgrade() -> None:
    op.drop_index("ix_user_session_activity_request", table_name="user_session_activity")
    op.drop_index("ix_user_session_activity_user_time", table_name="user_session_activity")
    op.drop_index("ix_user_session_activity_session", table_name="user_session_activity")
    op.drop_table("user_session_activity")

    op.drop_index("ix_audit_logs_request", table_name="audit_logs")
    op.drop_index("ix_audit_logs_action_type", table_name="audit_logs")
    op.drop_index("ix_audit_logs_tenant_created", table_name="audit_logs")
    op.drop_column("audit_logs", "request_id")
    op.drop_column("audit_logs", "duration_ms")
    op.drop_column("audit_logs", "after_state")
    op.drop_column("audit_logs", "before_state")
    op.drop_column("audit_logs", "action_type")
    op.drop_column("audit_logs", "session_id")
    op.drop_column("audit_logs", "tenant_id")

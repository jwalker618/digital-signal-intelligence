"""Push notifications (A-4).

Revision ID: 020
Revises: 019
Create Date: 2026-04-12

Adds:
- push_subscriptions: Web Push endpoints registered by a user on a
  device. A user may have multiple (one per browser/device).
- notification_preferences: per-user, per-category push/in-app/email
  toggles. Missing rows default to enabled (handled in service code).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


revision: str = "020"
down_revision: str = "019"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "push_subscriptions",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "user_id",
            UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "tenant_id",
            UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("endpoint", sa.Text, nullable=False),
        sa.Column("p256dh_key", sa.Text, nullable=False),
        sa.Column("auth_key", sa.Text, nullable=False),
        sa.Column("user_agent", sa.String(512), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "last_used_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.UniqueConstraint("user_id", "endpoint", name="uq_push_subs_user_endpoint"),
    )
    op.create_index(
        "ix_push_subs_user_id", "push_subscriptions", ["user_id"]
    )
    op.create_index(
        "ix_push_subs_tenant_id", "push_subscriptions", ["tenant_id"]
    )

    op.create_table(
        "notification_preferences",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "user_id",
            UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "tenant_id",
            UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("category", sa.String(64), nullable=False),
        sa.Column(
            "push_enabled", sa.Boolean, nullable=False, server_default=sa.text("true")
        ),
        sa.Column(
            "in_app_enabled",
            sa.Boolean,
            nullable=False,
            server_default=sa.text("true"),
        ),
        sa.Column(
            "email_enabled", sa.Boolean, nullable=False, server_default=sa.text("false")
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("user_id", "category", name="uq_notif_pref_user_category"),
    )
    op.create_index(
        "ix_notif_pref_user_id", "notification_preferences", ["user_id"]
    )


def downgrade() -> None:
    op.drop_index("ix_notif_pref_user_id", table_name="notification_preferences")
    op.drop_table("notification_preferences")
    op.drop_index("ix_push_subs_tenant_id", table_name="push_subscriptions")
    op.drop_index("ix_push_subs_user_id", table_name="push_subscriptions")
    op.drop_table("push_subscriptions")

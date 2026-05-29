"""auth wiring: propagate broker_id from invitation -> user.

Revision ID: 033
Revises: 032
Create Date: 2026-05-29

BROKER-role users invited or admin-created against the platform came
into the system with `users.broker_id = NULL`. Every broker-portal
endpoint (`/portal/overview`, `/portal/book-health`, `/portal/client-health`,
etc.) then 403s with "Broker identity not configured for this user"
because the join `Submission.broker_id == user.broker_id` never matches.

This migration adds a `broker_id` column to `user_invitations` so the
admin can stamp a broker on the invite at creation, and the existing
`users.broker_id` column gets populated when the invitee accepts.

The matching service-layer change (UserService.create_user +
InvitationService.create_invitation / accept) lives in the same change
set.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


revision: str = "033"
down_revision: str = "032"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "user_invitations",
        sa.Column(
            "broker_id",
            UUID(as_uuid=True),
            sa.ForeignKey("brokers.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.create_index(
        "ix_user_invitations_broker_id",
        "user_invitations",
        ["broker_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_user_invitations_broker_id", table_name="user_invitations")
    op.drop_column("user_invitations", "broker_id")

"""v8 Phase 5: broker query/reply on referrals.

Revision ID: 032
Revises: 031
Create Date: 2026-05-21

Adds the broker-underwriter message thread that drives the demo
storyboard's Acts 4-6 (underwriter raises query -> broker replies with
signal evidence -> re-assessment improves the quote).

Schema:
  - referralstatus: new enum value `awaiting_broker`
  - referrals.awaiting_party: nullable string ("broker" when query
    pending) -- redundant with status but enables cheap queue
    queries without unfolding the enum
  - referral_messages: new table holding the bi-directional thread
    between underwriter and broker. Optional signal_value_update JSONB
    payload on broker replies carries the direct-query value update
    that triggers re-assessment.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID


# revision identifiers, used by Alembic.
revision: str = "032"
down_revision: str = "031"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # Extend referralstatus enum: add `awaiting_broker`
    # ------------------------------------------------------------------
    # ALTER TYPE ... ADD VALUE cannot run inside a transaction in older
    # postgres, but alembic handles the autocommit boundary for us when
    # the migration is executed standalone. With_autocommit_block keeps
    # this safe.
    with op.get_context().autocommit_block():
        op.execute(
            "ALTER TYPE referralstatus ADD VALUE IF NOT EXISTS 'awaiting_broker'"
        )

    # ------------------------------------------------------------------
    # referrals.awaiting_party
    # ------------------------------------------------------------------
    op.add_column(
        "referrals",
        sa.Column("awaiting_party", sa.String(16), nullable=True),
    )

    # ------------------------------------------------------------------
    # referral_messages
    # ------------------------------------------------------------------
    op.create_table(
        "referral_messages",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column(
            "referral_id",
            UUID(as_uuid=True),
            sa.ForeignKey("referrals.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("direction", sa.String(4), nullable=False),  # "u2b" | "b2u"
        sa.Column(
            "author_user_id",
            UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("body", sa.Text, nullable=False),
        # Optional: when broker reply carries a signal value update,
        # this captures it so the re-assessment is auditable.
        sa.Column("signal_value_update", JSONB, nullable=True),
        sa.Column("triggered_reassessment", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column(
            "new_quote_id",
            UUID(as_uuid=True),
            sa.ForeignKey("quotes.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "request_signal_evidence",
            sa.String(128),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_referral_messages_referral", "referral_messages", ["referral_id", "created_at"])
    op.create_index("ix_referral_messages_quote", "referral_messages", ["new_quote_id"])


def downgrade() -> None:
    op.drop_index("ix_referral_messages_quote", table_name="referral_messages")
    op.drop_index("ix_referral_messages_referral", table_name="referral_messages")
    op.drop_table("referral_messages")
    op.drop_column("referrals", "awaiting_party")
    # Note: postgres does not support removing an enum value cleanly.
    # The `awaiting_broker` value remains in the type after downgrade.
    # This is acceptable -- it's a no-op for existing rows.

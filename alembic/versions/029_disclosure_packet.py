"""V7 Phase 14 — referrals.disclosure_packet column for cached packets.

Revision ID: 029
Revises: 028
Create Date: 2026-05-13

When a grade-driven referral fires, the workflow generates a templated
underwriter disclosure packet (Markdown + JSON payload) and caches it on
the referral row. Subsequent GET requests prefer the cached payload over
re-generating — disclosure packets are deterministic for a given
model_version_id, so the cached copy is always valid.

Nullable for backward compatibility — pre-V7-Phase-14 referrals carry
NULL until the next workflow run generates one on demand.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB


revision: str = "029"
down_revision: str = "028"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "referrals",
        sa.Column("disclosure_packet", JSONB, nullable=True),
    )


def downgrade() -> None:
    op.drop_column("referrals", "disclosure_packet")

"""Drift-alert → referral-queue wiring (V6/E6).

Revision ID: 022
Revises: 021
Create Date: 2026-04-17

Adds two columns to the `referrals` table so drift-detector alerts
can land in the same queue as manual referrals:

- `referral_type` VARCHAR — "MANUAL" | "DRIFT" | "CONFIDENCE_MISCALIBRATED".
  Indexed so `/api/v1/referrals?type=DRIFT` is cheap.
- `drift_alert_id` UUID (nullable) — FK into drift_alerts when
  referral_type = "DRIFT". Null otherwise.

Existing rows default to referral_type = "MANUAL".
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


revision: str = "022"
down_revision: str = "021"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "referrals",
        sa.Column(
            "referral_type",
            sa.String(length=32),
            nullable=False,
            server_default=sa.text("'MANUAL'"),
        ),
    )
    op.add_column(
        "referrals",
        sa.Column(
            "drift_alert_id",
            UUID(as_uuid=True),
            nullable=True,
        ),
    )
    # Optional FK to drift_alerts — tolerated as SQL if the drift_alerts
    # table exists; skipped silently otherwise so this migration is
    # forward-compatible with partially-bootstrapped databases.
    try:
        op.create_foreign_key(
            "fk_referrals_drift_alert",
            "referrals",
            "drift_alerts",
            ["drift_alert_id"],
            ["id"],
            ondelete="SET NULL",
        )
    except Exception:
        # drift_alerts may not exist yet in some deployments; the FK
        # is best-effort and non-blocking.
        pass

    op.create_index(
        "ix_referrals_referral_type",
        "referrals",
        ["referral_type"],
    )
    op.create_index(
        "ix_referrals_drift_alert",
        "referrals",
        ["drift_alert_id"],
        postgresql_where=sa.text("drift_alert_id IS NOT NULL"),
    )


def downgrade() -> None:
    op.drop_index("ix_referrals_drift_alert", table_name="referrals")
    op.drop_index("ix_referrals_referral_type", table_name="referrals")
    try:
        op.drop_constraint("fk_referrals_drift_alert", "referrals", type_="foreignkey")
    except Exception:
        pass
    op.drop_column("referrals", "drift_alert_id")
    op.drop_column("referrals", "referral_type")

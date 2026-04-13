"""CAF columns on model_versions (WE-4).

Revision ID: 015
Revises: 014
Create Date: 2026-04-12

Adds the Causal Adjustment Factor audit trail columns to model_versions.
The full CAF payload (precursors, trajectory, constraint regime) lives in
we_causal_adjustments; these columns on model_versions are the at-a-glance
audit summary so every ModelVersionRecord captures its CAF state without
requiring a join.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "015"
down_revision: str = "014"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "model_versions",
        sa.Column("caf_value", sa.Float, nullable=False, server_default="1.0"),
    )
    op.add_column(
        "model_versions",
        sa.Column("caf_confidence", sa.Float, nullable=True),
    )
    op.add_column(
        "model_versions",
        sa.Column("caf_constrained", sa.Boolean, nullable=False, server_default=sa.false()),
    )
    op.add_column(
        "model_versions",
        sa.Column("static_premium", sa.Float, nullable=True),
    )
    # Index on caf_value not expected to be used for filters -- skip


def downgrade() -> None:
    op.drop_column("model_versions", "static_premium")
    op.drop_column("model_versions", "caf_constrained")
    op.drop_column("model_versions", "caf_confidence")
    op.drop_column("model_versions", "caf_value")

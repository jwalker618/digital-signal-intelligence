"""Add config snapshot JSONB columns for client-side scenario recalculation

Revision ID: 008
Revises: 007
Create Date: 2026-03-25

Changes:
1. loss_correlation_config — loss correlation groups, weights, band thresholds, multiplier maps
2. ilf_curve_config — ILF curve type, parametric coefficients, anchor limit
3. deductible_factor_table — deductible-to-factor mapping per product type
4. exposure_modifier_config — size curve lookup table, growth/concentration thresholds
5. guardrails_config — modifier floor/cap, premium ratio caps
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


# revision identifiers, used by Alembic.
revision: str = "008"
down_revision: str = "007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("model_versions", sa.Column("loss_correlation_config", JSONB, nullable=True))
    op.add_column("model_versions", sa.Column("ilf_curve_config", JSONB, nullable=True))
    op.add_column("model_versions", sa.Column("deductible_factor_table", JSONB, nullable=True))
    op.add_column("model_versions", sa.Column("exposure_modifier_config", JSONB, nullable=True))
    op.add_column("model_versions", sa.Column("guardrails_config", JSONB, nullable=True))


def downgrade() -> None:
    op.drop_column("model_versions", "guardrails_config")
    op.drop_column("model_versions", "exposure_modifier_config")
    op.drop_column("model_versions", "deductible_factor_table")
    op.drop_column("model_versions", "ilf_curve_config")
    op.drop_column("model_versions", "loss_correlation_config")

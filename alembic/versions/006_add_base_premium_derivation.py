"""Add base_premium_derivation JSONB column to model_versions

Revision ID: 006
Revises: 005a
Create Date: 2026-03-20

Changes:
1. Add base_premium_derivation (JSONB) — audit trail capturing how base premium
   was derived: method, basis_field, basis_value, rate, tier, tier_label, result.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


# revision identifiers, used by Alembic.
revision: str = "006"
down_revision: str = "005a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("model_versions", sa.Column("base_premium_derivation", JSONB, nullable=True))


def downgrade() -> None:
    op.drop_column("model_versions", "base_premium_derivation")

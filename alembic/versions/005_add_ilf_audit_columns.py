"""Add ILF audit columns to model_versions

Revision ID: 005
Revises: 004
Create Date: 2026-03-18

Changes:
1. Add ilf_factor (Float) — the ILF multiplier applied at the requested limit
2. Add ilf_method (VARCHAR(50)) — table, interpolated, or extrapolated
3. Add ilf_anchor_limit (Float) — the limit where ILF = 1.0
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "005"
down_revision: str = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("model_versions", sa.Column("ilf_factor", sa.Float(), nullable=True))
    op.add_column("model_versions", sa.Column("ilf_method", sa.String(50), nullable=True))
    op.add_column("model_versions", sa.Column("ilf_anchor_limit", sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column("model_versions", "ilf_anchor_limit")
    op.drop_column("model_versions", "ilf_method")
    op.drop_column("model_versions", "ilf_factor")

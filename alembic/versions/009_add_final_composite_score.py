"""Add final_composite_score column to model_versions

Revision ID: 009
Revises: 008
Create Date: 2026-03-30

The tier margin / distance columns were calculated against the score-based
tier band, but should reflect the final tier (after overrides).  Persisting
``final_composite_score`` alongside ``pure_composite_score`` makes the
tier-margin derivation fully auditable from the DB alone.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "009"
down_revision: str = "008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "model_versions",
        sa.Column("final_composite_score", sa.Float, nullable=True),
    )
    # Backfill: for existing rows, final_composite_score = pure_composite_score
    op.execute(
        "UPDATE model_versions SET final_composite_score = pure_composite_score "
        "WHERE final_composite_score IS NULL"
    )


def downgrade() -> None:
    op.drop_column("model_versions", "final_composite_score")

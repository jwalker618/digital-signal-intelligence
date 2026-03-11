"""Add group_weight, loss_group_scores, and exposure_band_boundaries

Revision ID: 005
Revises: 004
Create Date: 2026-03-11

Changes:
1. model_version_signals: add group_weight FLOAT column
   - Records the group-level risk weight from config at execution time
   - Combined with signal weight and score, enables full composite reconstruction
2. model_versions: add loss_group_scores JSONB column
   - Stores per-group frequency/severity scores for loss propensity reconstructability
3. model_versions: add exposure_band_boundaries JSONB column
   - Snapshots the matched band's min_value, max_value, modifier at execution time
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


# revision identifiers, used by Alembic.
revision: str = "005"
down_revision: str = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "model_version_signals",
        sa.Column("group_weight", sa.Float(), nullable=True),
    )
    op.add_column(
        "model_versions",
        sa.Column("loss_group_scores", JSONB(), nullable=True),
    )
    op.add_column(
        "model_versions",
        sa.Column("exposure_band_boundaries", JSONB(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("model_versions", "exposure_band_boundaries")
    op.drop_column("model_versions", "loss_group_scores")
    op.drop_column("model_version_signals", "group_weight")

"""V7 Phase 9 — primitive_type column on signal rows.

Revision ID: 027
Revises: 026
Create Date: 2026-05-13

Adds the risk-primitive classification column to model_version_signals
and signal_history, with indexes so "grade distribution by primitive"
queries are cheap.

Nullable for backward compatibility — pre-V7-Phase-9 rows carry NULL.
The scorer populates it on every new cycle; no backfill (the value is a
pure function of signal_id + coverage and can be recomputed on read if
ever needed).
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "027"
down_revision: str = "026"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "model_version_signals",
        sa.Column("primitive_type", sa.String(32), nullable=True),
    )
    op.add_column(
        "signal_history",
        sa.Column("primitive_type", sa.String(32), nullable=True),
    )
    op.create_index("ix_mvs_primitive", "model_version_signals", ["primitive_type"])
    op.create_index("ix_history_primitive", "signal_history", ["primitive_type"])


def downgrade() -> None:
    op.drop_index("ix_history_primitive", table_name="signal_history")
    op.drop_index("ix_mvs_primitive", table_name="model_version_signals")
    op.drop_column("signal_history", "primitive_type")
    op.drop_column("model_version_signals", "primitive_type")

"""V7 Phase 6 — validator_verdicts + NOT NULL on evidence_grade.

Revision ID: 024
Revises: 023
Create Date: 2026-05-13

Lands:
  1. `validator_verdicts` table (unique per model_version_id + signal_id).
  2. NOT NULL on `model_version_signals.evidence_grade`.
     The NOT NULL flip is preceded by a backfill UPDATE that gives any
     remaining nulls the conservative `inferred` rung.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID


revision: str = "024"
down_revision: str = "023"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- validator_verdicts ----------------------------------------------
    op.create_table(
        "validator_verdicts",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("model_version_id", UUID(as_uuid=True), sa.ForeignKey("model_versions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("signal_id", sa.String(128), nullable=False),
        sa.Column("mode", sa.String(16), nullable=False),
        sa.Column("advance", sa.Boolean, nullable=False),
        sa.Column("grade_before", sa.String(32), nullable=True),
        sa.Column("grade_after", sa.String(32), nullable=True),
        sa.Column("axes", JSONB, server_default=sa.text("'{}'::jsonb")),
        sa.Column("pro_argument", sa.Text, nullable=False, server_default=sa.text("''")),
        sa.Column("counter_argument", sa.Text, nullable=False, server_default=sa.text("''")),
        sa.Column("tie_breaker", sa.Text, nullable=False, server_default=sa.text("''")),
        sa.Column("raw_response", sa.Text, nullable=True),
        sa.Column("elapsed_seconds", sa.Numeric(8, 3), nullable=True),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_unique_constraint(
        "uq_validator_verdict_per_mv_signal",
        "validator_verdicts",
        ["model_version_id", "signal_id"],
    )
    op.create_index("ix_validator_verdicts_advance", "validator_verdicts", ["advance"])
    op.create_index("ix_validator_verdicts_signal", "validator_verdicts", ["signal_id"])

    # --- Backfill any remaining nulls before tightening NOT NULL ----------
    # Conservative default: legacy or escape-hatch rows get `inferred`.
    op.execute(
        "UPDATE model_version_signals SET evidence_grade='inferred' "
        "WHERE evidence_grade IS NULL"
    )
    op.alter_column(
        "model_version_signals",
        "evidence_grade",
        nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        "model_version_signals",
        "evidence_grade",
        nullable=True,
    )
    op.drop_index("ix_validator_verdicts_signal", table_name="validator_verdicts")
    op.drop_index("ix_validator_verdicts_advance", table_name="validator_verdicts")
    op.drop_constraint(
        "uq_validator_verdict_per_mv_signal",
        "validator_verdicts",
        type_="unique",
    )
    op.drop_table("validator_verdicts")

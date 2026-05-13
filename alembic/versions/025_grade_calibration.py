"""V7 Phase 7 — grade-calibration store: samples + human decisions.

Revision ID: 025
Revises: 024
Create Date: 2026-05-13

Lands:
  1. grade_calibration_samples: one row per (model_version_id, signal_id)
     selected for human review. Sampling reasons:
       high_weight_referred  — weight>=0.10 in a submission where any
                                grade referral fired
       stratified_random     — 5% stratified by (coverage, extractor_grade)
                                across weight>=0.05 signals
  2. grade_calibration_decisions: one row per sample once an underwriter
     submits a human_grade verdict. Stores precomputed match flags so
     stats aggregation is cheap.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID


revision: str = "025"
down_revision: str = "024"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "grade_calibration_samples",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("model_version_id", UUID(as_uuid=True), sa.ForeignKey("model_versions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("submission_id", UUID(as_uuid=True), sa.ForeignKey("submissions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("coverage", sa.String(64), nullable=False),
        sa.Column("signal_id", sa.String(128), nullable=False),
        sa.Column("signal_weight", sa.Float, nullable=False),
        sa.Column("extractor_grade", sa.String(32), nullable=False),
        sa.Column("validator_grade", sa.String(32), nullable=True),
        sa.Column("sampling_reason", sa.String(64), nullable=False),
        sa.Column("state", sa.String(16), nullable=False, server_default=sa.text("'pending'")),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_unique_constraint(
        "uq_calibration_sample_per_mv_signal",
        "grade_calibration_samples",
        ["model_version_id", "signal_id"],
    )
    op.create_index("ix_calibration_state", "grade_calibration_samples", ["state"])
    op.create_index("ix_calibration_coverage_grade", "grade_calibration_samples", ["coverage", "extractor_grade"])

    op.create_table(
        "grade_calibration_decisions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("sample_id", UUID(as_uuid=True), sa.ForeignKey("grade_calibration_samples.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("human_grade", sa.String(32), nullable=False),
        sa.Column("note", sa.Text, nullable=True),
        sa.Column("decided_by", UUID(as_uuid=True), nullable=False),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("exact_match_extractor", sa.Boolean, nullable=False),
        sa.Column("exact_match_validator", sa.Boolean, nullable=True),
        sa.Column("within_one_extractor", sa.Boolean, nullable=False),
    )
    op.create_index("ix_calibration_decision_match", "grade_calibration_decisions", ["exact_match_extractor", "decided_at"])


def downgrade() -> None:
    op.drop_index("ix_calibration_decision_match", table_name="grade_calibration_decisions")
    op.drop_table("grade_calibration_decisions")
    op.drop_index("ix_calibration_coverage_grade", table_name="grade_calibration_samples")
    op.drop_index("ix_calibration_state", table_name="grade_calibration_samples")
    op.drop_constraint("uq_calibration_sample_per_mv_signal", "grade_calibration_samples", type_="unique")
    op.drop_table("grade_calibration_samples")

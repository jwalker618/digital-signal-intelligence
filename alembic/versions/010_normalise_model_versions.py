"""Normalise model_versions: move static/redundant columns to proper homes

Revision ID: 010
Revises: 009
Create Date: 2026-04-02

Changes:
1. Move discovery_output from model_versions to submissions (one-time per submission)
2. Create submission_notes table (replaces notes JSONB array on model_versions)
3. Create config_snapshots table keyed by config_hash (replaces 10 static config
   snapshot columns that were duplicated across every model version using the same config)
4. Drop signal_outputs from model_versions (fully covered by the join:
   model_version_signals → signal_cache → signals → signal_sources)
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID


# revision identifiers, used by Alembic.
revision: str = "010"
down_revision: str = "009"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Move discovery_output to submissions
    op.add_column("submissions", sa.Column("discovery_output", JSONB, nullable=True))
    op.drop_column("model_versions", "discovery_output")

    # 2. Create submission_notes table
    op.create_table(
        "submission_notes",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("submission_id", UUID(as_uuid=True), sa.ForeignKey("submissions.id"), nullable=False),
        sa.Column("note", sa.Text, nullable=False),
        sa.Column("source", sa.String(100), nullable=False),  # workflow, underwriter, system, etc.
        sa.Column("created_by", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_submission_notes_submission", "submission_notes", ["submission_id"])
    op.drop_column("model_versions", "notes")

    # 3. Create config_snapshots table
    op.create_table(
        "config_snapshots",
        sa.Column("config_hash", sa.String(64), primary_key=True),
        sa.Column("coverage", sa.String(50), nullable=False),
        sa.Column("configuration_name", sa.String(100), nullable=False),
        sa.Column("tier_band_interpretation", JSONB, nullable=True),
        sa.Column("loss_band_interpretation", JSONB, nullable=True),
        sa.Column("correlation_matrix_version", sa.String(100), nullable=True),
        sa.Column("exposure_assessment_method", sa.String(50), nullable=True),
        sa.Column("exposure_band_interpretation", JSONB, nullable=True),
        sa.Column("loss_correlation_config", JSONB, nullable=True),
        sa.Column("ilf_curve_config", JSONB, nullable=True),
        sa.Column("deductible_factor_table", JSONB, nullable=True),
        sa.Column("exposure_modifier_config", JSONB, nullable=True),
        sa.Column("guardrails_config", JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    # Drop from model_versions
    op.drop_column("model_versions", "tier_band_interpretation")
    op.drop_column("model_versions", "loss_band_interpretation")
    op.drop_column("model_versions", "correlation_matrix_version")
    op.drop_column("model_versions", "exposure_assessment_method")
    op.drop_column("model_versions", "exposure_band_interpretation")
    op.drop_column("model_versions", "loss_correlation_config")
    op.drop_column("model_versions", "ilf_curve_config")
    op.drop_column("model_versions", "deductible_factor_table")
    op.drop_column("model_versions", "exposure_modifier_config")
    op.drop_column("model_versions", "guardrails_config")

    # 4. Drop signal_outputs (fully covered by model_version_signals join)
    op.drop_column("model_versions", "signal_outputs")


def downgrade() -> None:
    # 4. Restore signal_outputs
    op.add_column("model_versions", sa.Column("signal_outputs", JSONB, server_default="[]"))

    # 3. Restore config snapshot columns and drop table
    op.add_column("model_versions", sa.Column("guardrails_config", JSONB, nullable=True))
    op.add_column("model_versions", sa.Column("exposure_modifier_config", JSONB, nullable=True))
    op.add_column("model_versions", sa.Column("deductible_factor_table", JSONB, nullable=True))
    op.add_column("model_versions", sa.Column("ilf_curve_config", JSONB, nullable=True))
    op.add_column("model_versions", sa.Column("loss_correlation_config", JSONB, nullable=True))
    op.add_column("model_versions", sa.Column("exposure_band_interpretation", JSONB, nullable=True))
    op.add_column("model_versions", sa.Column("exposure_assessment_method", sa.String(50), nullable=True))
    op.add_column("model_versions", sa.Column("correlation_matrix_version", sa.String(100), nullable=True))
    op.add_column("model_versions", sa.Column("loss_band_interpretation", JSONB, nullable=True))
    op.add_column("model_versions", sa.Column("tier_band_interpretation", JSONB, nullable=True))
    op.drop_table("config_snapshots")

    # 2. Restore notes and drop submission_notes
    op.add_column("model_versions", sa.Column("notes", JSONB, server_default="[]"))
    op.drop_index("ix_submission_notes_submission", table_name="submission_notes")
    op.drop_table("submission_notes")

    # 1. Restore discovery_output
    op.add_column("model_versions", sa.Column("discovery_output", JSONB, nullable=True))
    op.drop_column("submissions", "discovery_output")

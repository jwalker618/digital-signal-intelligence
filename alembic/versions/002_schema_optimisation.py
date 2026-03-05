"""Schema optimisation: de-duplicate quotes, add loss/exposure columns, add is_latest flag

Revision ID: 002
Revises: 001
Create Date: 2026-03-05

Changes:
- model_versions: Add is_latest boolean with partial unique index
- model_versions: Add 16 loss propensity columns (Phase 16 three-pillar)
- model_versions: Add 6 exposure assessment columns (three-pillar)
- quotes: Remove duplicated scoring/pricing columns (composite_score, confidence,
  tier, tier_label, decision, auto_approve, referral_reasons, base_premium)
  that now live exclusively on model_versions
- quotes: Make model_version_id NOT NULL (was nullable)
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers, used by Alembic.
revision: str = "002"
down_revision: str = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # =========================================================================
    # model_versions: add is_latest flag
    # =========================================================================
    op.add_column("model_versions", sa.Column("is_latest", sa.Boolean, nullable=False, server_default=sa.text("true")))
    op.create_index(
        "ix_model_versions_latest",
        "model_versions",
        ["submission_id"],
        unique=True,
        postgresql_where=sa.text("is_latest IS TRUE"),
    )

    # =========================================================================
    # model_versions: add loss propensity columns (Phase 16)
    # =========================================================================
    op.add_column("model_versions", sa.Column("loss_propensity_score", sa.Float))
    op.add_column("model_versions", sa.Column("severity_propensity_score", sa.Float))
    op.add_column("model_versions", sa.Column("loss_propensity_band", sa.String(50)))
    op.add_column("model_versions", sa.Column("severity_propensity_band", sa.String(50)))
    op.add_column("model_versions", sa.Column("loss_confidence", sa.Float))
    op.add_column("model_versions", sa.Column("loss_cohort_id", sa.String(100)))
    op.add_column("model_versions", sa.Column("loss_cohort_name", sa.String(255)))
    op.add_column("model_versions", sa.Column("loss_cohort_confidence", sa.Float))
    op.add_column("model_versions", sa.Column("loss_frequency_multiplier", sa.Float))
    op.add_column("model_versions", sa.Column("loss_severity_multiplier", sa.Float))
    op.add_column("model_versions", sa.Column("loss_combined_modifier", sa.Float))
    op.add_column("model_versions", sa.Column("loss_trend_direction", sa.String(50)))
    op.add_column("model_versions", sa.Column("loss_previous_score", sa.Float))
    op.add_column("model_versions", sa.Column("loss_score_velocity", sa.Float))
    op.add_column("model_versions", sa.Column("loss_last_refresh", sa.DateTime(timezone=True)))
    op.add_column("model_versions", sa.Column("correlation_matrix_version", sa.String(100)))

    # =========================================================================
    # model_versions: add exposure assessment columns
    # =========================================================================
    op.add_column("model_versions", sa.Column("exposure_value", sa.Float))
    op.add_column("model_versions", sa.Column("exposure_band_id", sa.Integer))
    op.add_column("model_versions", sa.Column("exposure_band_label", sa.String(100)))
    op.add_column("model_versions", sa.Column("exposure_magnitude_score", sa.Float))
    op.add_column("model_versions", sa.Column("exposure_modifier", sa.Float))
    op.add_column("model_versions", sa.Column("exposure_assessment_method", sa.String(50)))

    # =========================================================================
    # quotes: remove duplicated columns (data lives on model_versions)
    # =========================================================================
    op.drop_column("quotes", "composite_score")
    op.drop_column("quotes", "confidence")
    op.drop_column("quotes", "tier")
    op.drop_column("quotes", "tier_label")
    op.drop_column("quotes", "decision")
    op.drop_column("quotes", "auto_approve")
    op.drop_column("quotes", "referral_reasons")
    op.drop_column("quotes", "base_premium")

    # quotes: make model_version_id non-nullable
    op.alter_column("quotes", "model_version_id", nullable=False)


def downgrade() -> None:
    # quotes: restore nullable model_version_id
    op.alter_column("quotes", "model_version_id", nullable=True)

    # quotes: restore removed columns
    op.add_column("quotes", sa.Column("base_premium", sa.Float))
    op.add_column("quotes", sa.Column("referral_reasons", JSONB, server_default=sa.text("'[]'::jsonb")))
    op.add_column("quotes", sa.Column("auto_approve", sa.Boolean, server_default=sa.text("false")))
    op.add_column("quotes", sa.Column("decision", sa.Enum("approve", "refer", "decline", name="decisiontype")))
    op.add_column("quotes", sa.Column("tier_label", sa.String(50)))
    op.add_column("quotes", sa.Column("tier", sa.Integer))
    op.add_column("quotes", sa.Column("confidence", sa.Float))
    op.add_column("quotes", sa.Column("composite_score", sa.Float))

    # model_versions: drop exposure columns
    op.drop_column("model_versions", "exposure_assessment_method")
    op.drop_column("model_versions", "exposure_modifier")
    op.drop_column("model_versions", "exposure_magnitude_score")
    op.drop_column("model_versions", "exposure_band_label")
    op.drop_column("model_versions", "exposure_band_id")
    op.drop_column("model_versions", "exposure_value")

    # model_versions: drop loss propensity columns
    op.drop_column("model_versions", "correlation_matrix_version")
    op.drop_column("model_versions", "loss_last_refresh")
    op.drop_column("model_versions", "loss_score_velocity")
    op.drop_column("model_versions", "loss_previous_score")
    op.drop_column("model_versions", "loss_trend_direction")
    op.drop_column("model_versions", "loss_combined_modifier")
    op.drop_column("model_versions", "loss_severity_multiplier")
    op.drop_column("model_versions", "loss_frequency_multiplier")
    op.drop_column("model_versions", "loss_cohort_confidence")
    op.drop_column("model_versions", "loss_cohort_name")
    op.drop_column("model_versions", "loss_cohort_id")
    op.drop_column("model_versions", "loss_confidence")
    op.drop_column("model_versions", "severity_propensity_band")
    op.drop_column("model_versions", "loss_propensity_band")
    op.drop_column("model_versions", "severity_propensity_score")
    op.drop_column("model_versions", "loss_propensity_score")

    # model_versions: drop is_latest
    op.drop_index("ix_model_versions_latest", "model_versions")
    op.drop_column("model_versions", "is_latest")

"""World Engine foundation tables (Phase WE-1).

Revision ID: 011
Revises: 010
Create Date: 2026-04-12

Creates the complete set of World Engine tables used by phases WE-1 through WE-5.
Tables are created up-front so later phases don't need additional migrations for
their data model. All tables use the we_ prefix for namespace isolation.

Tables:
- we_relationships: Discovered causal relationships
- we_state_transitions: Lifecycle audit trail
- we_consistency_scores: Per-assessment consistency
- we_population_consistency: Population-level aggregates
- we_causal_adjustments: Per-assessment CAF
- we_portfolio_concentrations: Portfolio concentration alerts
- we_drift_alerts: Drift and regime change alerts
- we_scan_runs: Batch discovery cycle audit trail
- we_constraint_history: CAF constraint regime changes
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID


# revision identifiers, used by Alembic.
revision: str = "011"
down_revision: str = "010"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # we_relationships
    # ------------------------------------------------------------------
    op.create_table(
        "we_relationships",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("source_signal", sa.String(200), nullable=False),
        sa.Column("target_signal", sa.String(200), nullable=False),
        sa.Column("direction", sa.String(30), nullable=False),
        sa.Column("lag_months", sa.Float, nullable=True),
        sa.Column("correlation_rho", sa.Float, nullable=False),
        sa.Column("granger_f_statistic", sa.Float, nullable=True),
        sa.Column("granger_p_value", sa.Float, nullable=True),
        sa.Column("effect_size", sa.Float, nullable=False),
        sa.Column("confounders_tested", JSONB, nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("holdout_rho", sa.Float, nullable=True),
        sa.Column("holdout_p_value", sa.Float, nullable=True),
        sa.Column("predictive_hit_rate", sa.Float, nullable=True),
        sa.Column("population_size", sa.Integer, nullable=False),
        sa.Column("coverage_scope", JSONB, nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("lifecycle_state", sa.String(30), nullable=False),
        sa.Column("state_entered_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("influence_weight", sa.Float, nullable=False, server_default="0.0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index(
        "ix_we_relationships_state_signals",
        "we_relationships",
        ["lifecycle_state", "source_signal", "target_signal"],
    )
    op.create_index("ix_we_relationships_lifecycle", "we_relationships", ["lifecycle_state"])

    # ------------------------------------------------------------------
    # we_state_transitions
    # ------------------------------------------------------------------
    op.create_table(
        "we_state_transitions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column(
            "relationship_id",
            UUID(as_uuid=True),
            sa.ForeignKey("we_relationships.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("from_state", sa.String(30), nullable=False),
        sa.Column("to_state", sa.String(30), nullable=False),
        sa.Column("transitioned_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("reason", sa.Text, nullable=False),
        sa.Column("evidence", JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index(
        "ix_we_state_transitions_relationship", "we_state_transitions", ["relationship_id"]
    )

    # ------------------------------------------------------------------
    # we_consistency_scores
    # ------------------------------------------------------------------
    op.create_table(
        "we_consistency_scores",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("entity_id", sa.String(200), nullable=False),
        sa.Column("assessment_id", sa.String(200), nullable=False),
        sa.Column("overall_consistency", sa.Float, nullable=False),
        sa.Column("signal_pair_scores", JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("cross_group_scores", JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("cross_layer_divergence", JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("divergent_pairs", JSONB, nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("computed_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_we_consistency_scores_entity",
        "we_consistency_scores",
        ["entity_id", "computed_at"],
    )
    op.create_index(
        "ix_we_consistency_scores_assessment",
        "we_consistency_scores",
        ["assessment_id"],
    )

    # ------------------------------------------------------------------
    # we_population_consistency
    # ------------------------------------------------------------------
    op.create_table(
        "we_population_consistency",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("coverage", sa.String(50), nullable=True),
        sa.Column("period", sa.String(50), nullable=True),  # e.g. "2026-04" or "all"
        sa.Column("mean_consistency", sa.Float, nullable=True),
        sa.Column("median_consistency", sa.Float, nullable=True),
        sa.Column("p10_consistency", sa.Float, nullable=True),
        sa.Column("p90_consistency", sa.Float, nullable=True),
        sa.Column("sample_size", sa.Integer, nullable=False),
        sa.Column("metrics", JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("computed_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index(
        "ix_we_population_consistency_period",
        "we_population_consistency",
        ["coverage", "period"],
    )

    # ------------------------------------------------------------------
    # we_causal_adjustments
    # ------------------------------------------------------------------
    op.create_table(
        "we_causal_adjustments",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("entity_id", sa.String(200), nullable=False),
        sa.Column("assessment_id", sa.String(200), nullable=False),
        sa.Column("caf_value", sa.Float, nullable=False),
        sa.Column("confidence", sa.Float, nullable=False),
        sa.Column("active_precursors", JSONB, nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("trajectory", JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("relationships_evaluated", sa.Integer, nullable=False, server_default="0"),
        sa.Column("constrained", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("raw_caf", sa.Float, nullable=False, server_default="1.0"),
        sa.Column("constraint_regime", sa.String(50), nullable=False, server_default="initial"),
        sa.Column("computed_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_we_causal_adjustments_assessment",
        "we_causal_adjustments",
        ["assessment_id"],
    )
    op.create_index(
        "ix_we_causal_adjustments_entity",
        "we_causal_adjustments",
        ["entity_id", "computed_at"],
    )

    # ------------------------------------------------------------------
    # we_portfolio_concentrations
    # ------------------------------------------------------------------
    op.create_table(
        "we_portfolio_concentrations",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("entity_id", sa.String(200), nullable=False),  # Commercial entity
        sa.Column("dimension", sa.String(50), nullable=False),  # node | pathway | derivative | cohort
        sa.Column("detail", sa.Text, nullable=False),
        sa.Column("severity", sa.Float, nullable=False),
        sa.Column("affected_entities", JSONB, nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("computed_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_we_portfolio_concentrations_entity_dim",
        "we_portfolio_concentrations",
        ["entity_id", "dimension"],
    )

    # ------------------------------------------------------------------
    # we_drift_alerts
    # ------------------------------------------------------------------
    op.create_table(
        "we_drift_alerts",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("alert_type", sa.String(50), nullable=False),
        sa.Column("severity", sa.String(20), nullable=False),
        sa.Column("source_signal", sa.String(200), nullable=True),
        sa.Column("target_signal", sa.String(200), nullable=True),
        sa.Column(
            "relationship_id",
            UUID(as_uuid=True),
            sa.ForeignKey("we_relationships.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("evidence", JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("detected_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("acknowledged", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("acknowledged_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_we_drift_alerts_severity_detected",
        "we_drift_alerts",
        ["severity", "detected_at"],
    )
    op.create_index("ix_we_drift_alerts_relationship", "we_drift_alerts", ["relationship_id"])

    # ------------------------------------------------------------------
    # we_scan_runs
    # ------------------------------------------------------------------
    op.create_table(
        "we_scan_runs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("run_id", sa.String(100), unique=True, nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("maturity_stage", sa.String(30), nullable=False),
        sa.Column("entities_scanned", sa.Integer, nullable=False, server_default="0"),
        sa.Column("pairs_tested", sa.Integer, nullable=False, server_default="0"),
        sa.Column("candidates_found", sa.Integer, nullable=False, server_default="0"),
        sa.Column("candidates_after_inference", sa.Integer, nullable=False, server_default="0"),
        sa.Column("candidates_after_confound", sa.Integer, nullable=False, server_default="0"),
        sa.Column("candidates_after_holdout", sa.Integer, nullable=False, server_default="0"),
        sa.Column("new_registrations", sa.Integer, nullable=False, server_default="0"),
        sa.Column("drift_alerts_raised", sa.Integer, nullable=False, server_default="0"),
        sa.Column("stats", JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("errors", JSONB, nullable=False, server_default=sa.text("'[]'::jsonb")),
    )
    op.create_index("ix_we_scan_runs_started", "we_scan_runs", ["started_at"])

    # ------------------------------------------------------------------
    # we_constraint_history
    # ------------------------------------------------------------------
    # Tracks CAF constraint regime changes. WE-4 inserts rows here when
    # ConstraintCalibrator autonomously widens bounds (within absolute guardrails).
    op.create_table(
        "we_constraint_history",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("regime_name", sa.String(50), nullable=False),
        sa.Column("caf_floor", sa.Float, nullable=False),
        sa.Column("caf_cap", sa.Float, nullable=False),
        sa.Column("confidence_gate", sa.Float, nullable=False),
        sa.Column("min_relationships", sa.Integer, nullable=False),
        sa.Column("effective_from", sa.DateTime(timezone=True), nullable=False),
        sa.Column("effective_to", sa.DateTime(timezone=True), nullable=True),
        sa.Column("evidence", JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index(
        "ix_we_constraint_history_effective",
        "we_constraint_history",
        ["effective_from"],
    )

    # Seed initial constraint regime
    op.execute(
        """
        INSERT INTO we_constraint_history
            (regime_name, caf_floor, caf_cap, confidence_gate, min_relationships, effective_from, evidence)
        VALUES
            ('initial', 0.80, 1.50, 0.6, 2, NOW(), '{"note": "Initial constraints at launch"}'::jsonb)
        """
    )


def downgrade() -> None:
    op.drop_table("we_constraint_history")
    op.drop_table("we_scan_runs")
    op.drop_table("we_drift_alerts")
    op.drop_table("we_portfolio_concentrations")
    op.drop_table("we_causal_adjustments")
    op.drop_table("we_population_consistency")
    op.drop_table("we_consistency_scores")
    op.drop_table("we_state_transitions")
    op.drop_table("we_relationships")

"""V7 Phase 5 — evidence-grade persistence.

Revision ID: 023
Revises: 022
Create Date: 2026-05-13

Lands the persistence layer for V7 evidence grades:

1. Evidence columns on `model_version_signals` and `model_versions`.
2. Append-only `signal_history` table — one row per (model_version, signal)
   stamped at cycle commit. Reconstructs the longitudinal grade trail.
3. `signal_commitments` — SHA3-224 digests over canonical-JSON payloads
   at three scopes (full_payload, value_and_grade, pro_counter, composite).
   Defensible "we knew this before we priced it" record.
4. `compliance_audit_logs` — separate audit lane from operational
   `audit_logs`. Carries grade-policy decisions, validator verdicts
   (Phase 6), and calibration samples (Phase 7).

Backfill: existing `model_version_signals` rows get
`evidence_basis='Pre-V7 record; grade not captured'`.

Note: alembic 024 (Phase 6) will tighten model_version_signals.evidence_grade
to NOT NULL once the validator has guaranteed a grade on every committed
row.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID


revision: str = "023"
down_revision: str = "022"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- Columns on model_version_signals --------------------------------
    op.add_column("model_version_signals", sa.Column("evidence_grade", sa.String(32), nullable=True))
    op.add_column("model_version_signals", sa.Column("evidence_basis", sa.String(500), nullable=True))
    op.add_column("model_version_signals", sa.Column("evidence_sources", JSONB, server_default=sa.text("'[]'::jsonb")))
    op.add_column("model_version_signals", sa.Column("evidence_pro", sa.Text(), nullable=True))
    op.add_column("model_version_signals", sa.Column("evidence_counter", sa.Text(), nullable=True))
    op.add_column("model_version_signals", sa.Column("evidence_tie_breaker", sa.Text(), nullable=True))
    op.add_column("model_version_signals", sa.Column("absence_sub_type", sa.String(32), nullable=True))
    op.create_index("ix_mvs_evidence_grade", "model_version_signals", ["evidence_grade"])

    # --- Columns on model_versions ---------------------------------------
    op.add_column("model_versions", sa.Column("composite_min_grade", sa.String(32), nullable=True))
    op.add_column("model_versions", sa.Column("composite_weighted_mean_grade", sa.Numeric(4, 2), nullable=True))
    op.add_column("model_versions", sa.Column("composite_grade_distribution", JSONB, server_default=sa.text("'{}'::jsonb")))

    # --- signal_history (append-only) ------------------------------------
    op.create_table(
        "signal_history",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("model_version_id", UUID(as_uuid=True), sa.ForeignKey("model_versions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("submission_id", UUID(as_uuid=True), sa.ForeignKey("submissions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("signal_id", sa.String(128), nullable=False),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("score", sa.Float(), nullable=True),
        sa.Column("category", sa.String(128), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("evidence_grade", sa.String(32), nullable=True),
        sa.Column("evidence_basis", sa.String(500), nullable=True),
        sa.Column("evidence_sources", JSONB, server_default=sa.text("'[]'::jsonb")),
        sa.Column("evidence_pro", sa.Text(), nullable=True),
        sa.Column("evidence_counter", sa.Text(), nullable=True),
        sa.Column("evidence_tie_breaker", sa.Text(), nullable=True),
        sa.Column("absence_sub_type", sa.String(32), nullable=True),
        sa.Column("history_metadata", JSONB, server_default=sa.text("'{}'::jsonb")),
    )
    op.create_index("ix_signal_history_submission_signal", "signal_history", ["submission_id", "signal_id"])
    op.create_index("ix_signal_history_recorded_at", "signal_history", ["recorded_at"])
    op.create_unique_constraint(
        "uq_signal_history_per_mv_signal",
        "signal_history",
        ["model_version_id", "signal_id", "recorded_at"],
    )

    # --- signal_commitments ----------------------------------------------
    op.create_table(
        "signal_commitments",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("model_version_id", UUID(as_uuid=True), sa.ForeignKey("model_versions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("signal_id", sa.String(128), nullable=True),  # null for composite-scoped commitment
        sa.Column("scope", sa.String(32), nullable=False),       # full_payload | value_and_grade | pro_counter | composite
        sa.Column("algorithm", sa.String(16), nullable=False, server_default=sa.text("'sha3_224'")),
        sa.Column("digest", sa.String(64), nullable=False),
        sa.Column("committed_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("canonical_keys", JSONB, server_default=sa.text("'[]'::jsonb")),
    )
    op.create_index("ix_commitments_mv", "signal_commitments", ["model_version_id"])
    op.create_unique_constraint(
        "uq_commitment_per_mv_signal_scope",
        "signal_commitments",
        ["model_version_id", "signal_id", "scope"],
    )

    # --- compliance_audit_logs -------------------------------------------
    op.create_table(
        "compliance_audit_logs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("event_type", sa.String(64), nullable=False),
        sa.Column("event_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("model_version_id", UUID(as_uuid=True), nullable=True),
        sa.Column("submission_id", UUID(as_uuid=True), nullable=True),
        sa.Column("signal_id", sa.String(128), nullable=True),
        sa.Column("actor", sa.String(128), nullable=True),  # "system", user uuid str, validator-llm-id
        sa.Column("payload", JSONB, server_default=sa.text("'{}'::jsonb")),
    )
    op.create_index("ix_comp_audit_event_type", "compliance_audit_logs", ["event_type"])
    op.create_index("ix_comp_audit_submission", "compliance_audit_logs", ["submission_id"])

    # --- Backfill existing model_version_signals --------------------------
    op.execute(
        "UPDATE model_version_signals "
        "SET evidence_basis = 'Pre-V7 record; grade not captured' "
        "WHERE evidence_basis IS NULL"
    )


def downgrade() -> None:
    op.drop_index("ix_comp_audit_submission", table_name="compliance_audit_logs")
    op.drop_index("ix_comp_audit_event_type", table_name="compliance_audit_logs")
    op.drop_table("compliance_audit_logs")

    op.drop_constraint("uq_commitment_per_mv_signal_scope", "signal_commitments", type_="unique")
    op.drop_index("ix_commitments_mv", table_name="signal_commitments")
    op.drop_table("signal_commitments")

    op.drop_constraint("uq_signal_history_per_mv_signal", "signal_history", type_="unique")
    op.drop_index("ix_signal_history_recorded_at", table_name="signal_history")
    op.drop_index("ix_signal_history_submission_signal", table_name="signal_history")
    op.drop_table("signal_history")

    op.drop_column("model_versions", "composite_grade_distribution")
    op.drop_column("model_versions", "composite_weighted_mean_grade")
    op.drop_column("model_versions", "composite_min_grade")

    op.drop_index("ix_mvs_evidence_grade", table_name="model_version_signals")
    op.drop_column("model_version_signals", "absence_sub_type")
    op.drop_column("model_version_signals", "evidence_tie_breaker")
    op.drop_column("model_version_signals", "evidence_counter")
    op.drop_column("model_version_signals", "evidence_pro")
    op.drop_column("model_version_signals", "evidence_sources")
    op.drop_column("model_version_signals", "evidence_basis")
    op.drop_column("model_version_signals", "evidence_grade")

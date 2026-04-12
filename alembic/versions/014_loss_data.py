"""Loss data ingestion: loss_events and signal_loss_pairs.

Revision ID: 014
Revises: 013
Create Date: 2026-04-12

Creates the data foundation for experience-based recalibration (C-2).
Every loss event is linked to the ModelVersionRecord that was active at
bind time, and the signal scores at that time are snapshotted into
signal_loss_pairs so the recalibration engine can analyse which signals
predicted actual losses.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID


revision: str = "014"
down_revision: str = "013"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # loss_events
    # ------------------------------------------------------------------
    op.create_table(
        "loss_events",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),

        # Entity identification (entity_name matches Submission.entity_name)
        sa.Column("entity_name", sa.String(500), nullable=False),

        # Policy linkage -- quote_id is the internal policy when available,
        # policy_reference is the external policy id (for imported data).
        sa.Column("quote_id", UUID(as_uuid=True), sa.ForeignKey("quotes.id", ondelete="SET NULL"), nullable=True),
        sa.Column("policy_reference", sa.String(100), nullable=True),
        sa.Column("claim_reference", sa.String(100), nullable=True),

        # Timeline
        sa.Column("loss_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("notification_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("closed_date", sa.DateTime(timezone=True), nullable=True),

        # Classification
        sa.Column("loss_type", sa.String(100), nullable=False),
        sa.Column("coverage", sa.String(50), nullable=False),
        sa.Column("config_name", sa.String(100), nullable=True),

        # Financial (decimal fixed precision for money)
        sa.Column("incurred_amount", sa.Numeric(15, 2), nullable=False, server_default="0"),
        sa.Column("paid_amount", sa.Numeric(15, 2), nullable=False, server_default="0"),
        sa.Column("reserved_amount", sa.Numeric(15, 2), nullable=False, server_default="0"),
        sa.Column("currency", sa.String(3), nullable=False, server_default="USD"),

        # Status and cause
        sa.Column("status", sa.String(20), nullable=False, server_default="OPEN"),  # OPEN | CLOSED | REOPENED
        sa.Column("cause_description", sa.Text, nullable=True),
        sa.Column("metadata", JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")),

        # Link to the model version at bind time (populated by linker)
        sa.Column("linked_assessment_id", UUID(as_uuid=True), sa.ForeignKey("model_versions.id", ondelete="SET NULL"), nullable=True),
        sa.Column("linker_run_at", sa.DateTime(timezone=True), nullable=True),

        # Audit fields
        sa.Column("created_by", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_index("ix_loss_events_tenant", "loss_events", ["tenant_id"])
    op.create_index("ix_loss_events_entity_date", "loss_events", ["entity_name", "loss_date"])
    op.create_index("ix_loss_events_coverage_status", "loss_events", ["coverage", "status"])
    op.create_index("ix_loss_events_quote", "loss_events", ["quote_id"])
    op.create_index("ix_loss_events_linked_assessment", "loss_events", ["linked_assessment_id"])

    # ------------------------------------------------------------------
    # signal_loss_pairs
    # ------------------------------------------------------------------
    # Snapshot of the signal profile at bind time, paired with the actual
    # loss outcome. This is the primary input to C-2's recalibration engine.
    op.create_table(
        "signal_loss_pairs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("assessment_id", UUID(as_uuid=True), sa.ForeignKey("model_versions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("loss_event_id", UUID(as_uuid=True), sa.ForeignKey("loss_events.id", ondelete="CASCADE"), nullable=False),

        # Signal snapshot (all raw scores from ModelVersionSignal at bind time)
        sa.Column("signal_scores_at_bind", JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")),

        # Composite metrics at bind time
        sa.Column("composite_score_at_bind", sa.Float, nullable=True),
        sa.Column("tier_at_bind", sa.Integer, nullable=True),
        sa.Column("loss_propensity_at_bind", sa.Float, nullable=True),
        sa.Column("confidence_at_bind", sa.Float, nullable=True),

        # Temporal
        sa.Column("bind_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("time_to_loss_days", sa.Integer, nullable=True),

        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),

        sa.UniqueConstraint("assessment_id", "loss_event_id", name="uq_signal_loss_pair"),
    )

    op.create_index("ix_signal_loss_pairs_tenant", "signal_loss_pairs", ["tenant_id"])
    op.create_index("ix_signal_loss_pairs_assessment", "signal_loss_pairs", ["assessment_id"])
    op.create_index("ix_signal_loss_pairs_loss", "signal_loss_pairs", ["loss_event_id"])


def downgrade() -> None:
    op.drop_index("ix_signal_loss_pairs_loss", table_name="signal_loss_pairs")
    op.drop_index("ix_signal_loss_pairs_assessment", table_name="signal_loss_pairs")
    op.drop_index("ix_signal_loss_pairs_tenant", table_name="signal_loss_pairs")
    op.drop_table("signal_loss_pairs")

    op.drop_index("ix_loss_events_linked_assessment", table_name="loss_events")
    op.drop_index("ix_loss_events_quote", table_name="loss_events")
    op.drop_index("ix_loss_events_coverage_status", table_name="loss_events")
    op.drop_index("ix_loss_events_entity_date", table_name="loss_events")
    op.drop_index("ix_loss_events_tenant", table_name="loss_events")
    op.drop_table("loss_events")

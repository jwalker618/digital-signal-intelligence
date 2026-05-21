"""V7 Phase 13 — entity_events table for delta-aware recompute.

Revision ID: 028
Revises: 027
Create Date: 2026-05-13

External events (SEC filing, Companies House change, OFAC update, calibration
disagreement, manual recompute) land in this table. A background dispatcher
reads undispatched rows, computes a per-event blast radius (which signals
plausibly changed), and runs a targeted recompute that re-extracts only
that signal subset.

Indexes:
  (entity_id, received_at) — for entity-scoped activity views
  (event_type, received_at) — for type-scoped activity views
  dispatched_at — partial scan for the dispatcher worker
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID


revision: str = "028"
down_revision: str = "027"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "entity_events",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("event_type", sa.String(64), nullable=False),
        sa.Column("entity_id", sa.String(128), nullable=False),
        sa.Column("submission_id", UUID(as_uuid=True), nullable=True),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("source_feed", sa.String(64), nullable=False),
        sa.Column("dedup_key", sa.String(128), nullable=True, unique=True),
        sa.Column("payload", JSONB, server_default=sa.text("'{}'::jsonb")),
        sa.Column("dispatched_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("blast_radius", JSONB, server_default=sa.text("'[]'::jsonb")),
        sa.Column("resulting_model_version_id", UUID(as_uuid=True), nullable=True),
    )
    op.create_index("ix_entity_events_entity_received", "entity_events", ["entity_id", "received_at"])
    op.create_index("ix_entity_events_type_received", "entity_events", ["event_type", "received_at"])
    op.create_index("ix_entity_events_dispatched", "entity_events", ["dispatched_at"])


def downgrade() -> None:
    op.drop_index("ix_entity_events_dispatched", table_name="entity_events")
    op.drop_index("ix_entity_events_type_received", table_name="entity_events")
    op.drop_index("ix_entity_events_entity_received", table_name="entity_events")
    op.drop_table("entity_events")

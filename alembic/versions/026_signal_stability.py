"""V7 Phase 8 — signal stability observations + reproducibility classification.

Revision ID: 026
Revises: 025
Create Date: 2026-05-13

Lands:
  1. signal_stability_observations — append-only. One row per pull of a
     (source_id, signal_id, entity_id) triple. The value is hashed
     (quantised) so repeat pulls that agree hash identically.
  2. signal_stability_classification — materialised view aggregating the
     last 90 days of observations into a reproducibility class per triple:
        unknown   n < 3
        stable    distinct_values/n <= 0.10 (0.30 for race-sensitive)
        flaky     distinct_values/n <= 0.50
        unstable  otherwise
     Refreshed daily (CONCURRENTLY). The unique index on the view is what
     makes CONCURRENTLY refresh possible.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID


revision: str = "026"
down_revision: str = "025"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "signal_stability_observations",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("source_id", sa.String(64), nullable=False),
        sa.Column("signal_id", sa.String(128), nullable=False),
        sa.Column("entity_id", sa.String(128), nullable=False),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("value_score", sa.Float, nullable=True),
        sa.Column("value_category", sa.String(128), nullable=True),
        sa.Column("value_hash", sa.String(64), nullable=False),
        sa.Column("response_hash", sa.String(64), nullable=True),
        sa.Column("race_sensitive", sa.Boolean, nullable=False, server_default=sa.text("false")),
    )
    op.create_index(
        "ix_stability_obs_triple",
        "signal_stability_observations",
        ["source_id", "signal_id", "entity_id"],
    )
    op.create_index(
        "ix_stability_obs_observed",
        "signal_stability_observations",
        ["observed_at"],
    )

    # Materialised view: 90-day reproducibility classification per triple.
    op.execute(
        """
        CREATE MATERIALIZED VIEW signal_stability_classification AS
        WITH windowed AS (
            SELECT source_id, signal_id, entity_id,
                   bool_or(race_sensitive) AS race_sensitive,
                   COUNT(*) AS n,
                   COUNT(DISTINCT value_hash) AS distinct_values
            FROM signal_stability_observations
            WHERE observed_at > now() - INTERVAL '90 days'
            GROUP BY source_id, signal_id, entity_id
        )
        SELECT
            source_id, signal_id, entity_id, race_sensitive, n,
            CASE
                WHEN n < 3 THEN 'unknown'
                WHEN race_sensitive
                     AND distinct_values::float / n <= 0.30 THEN 'stable'
                WHEN NOT race_sensitive
                     AND distinct_values::float / n <= 0.10 THEN 'stable'
                WHEN distinct_values::float / n <= 0.50 THEN 'flaky'
                ELSE 'unstable'
            END AS class
        FROM windowed
        """
    )
    op.execute(
        "CREATE UNIQUE INDEX ix_stability_class_triple "
        "ON signal_stability_classification (source_id, signal_id, entity_id)"
    )


def downgrade() -> None:
    op.execute("DROP MATERIALIZED VIEW IF EXISTS signal_stability_classification")
    op.drop_index("ix_stability_obs_observed", table_name="signal_stability_observations")
    op.drop_index("ix_stability_obs_triple", table_name="signal_stability_observations")
    op.drop_table("signal_stability_observations")

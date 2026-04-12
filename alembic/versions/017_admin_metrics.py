"""Admin metrics tables (B-1).

Revision ID: 017
Revises: 016
Create Date: 2026-04-12

- extractor_health: per-extractor success/error counters + last-seen timestamps.
  Updated on every signal extraction via ExtractorTracker.record_extraction().
- metric_snapshots: hourly pipeline metric rollups (throughput, latency
  percentiles, failure rates) persisted for trend analysis in the admin
  dashboard. 7 days of hourly granular + 90 days of daily aggregates.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID


revision: str = "017"
down_revision: str = "016"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "extractor_health",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("extractor_id", sa.String(200), nullable=False),
        sa.Column("coverage", sa.String(50), nullable=True),
        sa.Column("signal_type", sa.String(100), nullable=True),

        # Rolling window counters (last 24h)
        sa.Column("success_count_24h", sa.Integer, nullable=False, server_default="0"),
        sa.Column("error_count_24h", sa.Integer, nullable=False, server_default="0"),
        sa.Column("avg_latency_ms", sa.Float, nullable=True),

        # Timestamps
        sa.Column("last_success_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error_message", sa.Text, nullable=True),

        # Freshness / TTL
        sa.Column("ttl_seconds", sa.Integer, nullable=True),
        sa.Column("data_freshness_score", sa.Float, nullable=True),  # 0-1

        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),

        sa.UniqueConstraint("extractor_id", "coverage", name="uq_extractor_health_id_coverage"),
    )
    op.create_index("ix_extractor_health_extractor", "extractor_health", ["extractor_id"])
    op.create_index("ix_extractor_health_coverage", "extractor_health", ["coverage"])

    op.create_table(
        "metric_snapshots",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("snapshot_type", sa.String(20), nullable=False),  # hourly | daily
        sa.Column("captured_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("coverage", sa.String(50), nullable=True),  # null = aggregate across all coverages
        sa.Column("metrics", JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")),
    )
    op.create_index("ix_metric_snapshots_type_time", "metric_snapshots", ["snapshot_type", "captured_at"])
    op.create_index("ix_metric_snapshots_coverage_time", "metric_snapshots", ["coverage", "captured_at"])


def downgrade() -> None:
    op.drop_index("ix_metric_snapshots_coverage_time", table_name="metric_snapshots")
    op.drop_index("ix_metric_snapshots_type_time", table_name="metric_snapshots")
    op.drop_table("metric_snapshots")

    op.drop_index("ix_extractor_health_coverage", table_name="extractor_health")
    op.drop_index("ix_extractor_health_extractor", table_name="extractor_health")
    op.drop_table("extractor_health")

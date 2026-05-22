"""v8 Phase 2: Peer cohort engine.

Revision ID: 031
Revises: 030
Create Date: 2026-05-21

Adds the peer-comparison cohort engine that powers the /portal/peers
view: percentile rank of an entity's composite score within its peer
cohort (defined as coverage_line x NAICS section x revenue band).

Schema:
  - model_versions: 5 new nullable columns -- peer_cohort_id,
    peer_cohort_size, peer_percentile_rank, peer_cohort_mean_score,
    peer_cohort_median_score. Populated at persistence time by the
    cohort service (layers/cohort/queries.py). Existing rows stay
    NULL; only freshly persisted model versions populate them.
  - cohort_membership: new denormalised table holding one row per
    (entity_key, coverage) -- the latest score and cohort
    classification for each real-world entity. Driven by upsert on
    each new ModelVersionRecord; powers the percentile computation
    without scanning model_versions.

The peer_cohort_* prefix avoids collision with loss_cohort_code /
loss_cohort_name on model_versions which describe a different
concept (loss-similarity grouping, not peer comparison).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision: str = "031"
down_revision: str = "030"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # model_versions: peer cohort columns
    # ------------------------------------------------------------------
    op.add_column("model_versions", sa.Column("peer_cohort_id", sa.String(64), nullable=True))
    op.add_column("model_versions", sa.Column("peer_cohort_size", sa.Integer, nullable=True))
    op.add_column("model_versions", sa.Column("peer_percentile_rank", sa.Float, nullable=True))
    op.add_column("model_versions", sa.Column("peer_cohort_mean_score", sa.Float, nullable=True))
    op.add_column("model_versions", sa.Column("peer_cohort_median_score", sa.Float, nullable=True))
    op.create_index("ix_model_versions_peer_cohort", "model_versions", ["peer_cohort_id"])

    # ------------------------------------------------------------------
    # cohort_membership: one row per (entity_key, coverage)
    # ------------------------------------------------------------------
    op.create_table(
        "cohort_membership",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("entity_key", sa.String(255), nullable=False),
        sa.Column("coverage", sa.String(64), nullable=False),
        sa.Column("cohort_id", sa.String(64), nullable=False),
        sa.Column("composite_score", sa.Float, nullable=False),
        sa.Column("naics_section", sa.String(8), nullable=False),
        sa.Column("revenue_band", sa.String(16), nullable=False),
        sa.Column(
            "model_version_id",
            UUID(as_uuid=True),
            sa.ForeignKey("model_versions.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("last_assessed_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("entity_key", "coverage", name="uq_cohort_membership_entity_coverage"),
    )
    op.create_index("ix_cohort_membership_cohort", "cohort_membership", ["cohort_id", "composite_score"])
    op.create_index("ix_cohort_membership_model_version", "cohort_membership", ["model_version_id"])


def downgrade() -> None:
    op.drop_index("ix_cohort_membership_model_version", table_name="cohort_membership")
    op.drop_index("ix_cohort_membership_cohort", table_name="cohort_membership")
    op.drop_table("cohort_membership")

    op.drop_index("ix_model_versions_peer_cohort", table_name="model_versions")
    op.drop_column("model_versions", "peer_cohort_median_score")
    op.drop_column("model_versions", "peer_cohort_mean_score")
    op.drop_column("model_versions", "peer_percentile_rank")
    op.drop_column("model_versions", "peer_cohort_size")
    op.drop_column("model_versions", "peer_cohort_id")

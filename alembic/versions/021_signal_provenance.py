"""Signal-lineage chain-of-custody (V6/E2).

Revision ID: 021
Revises: 020
Create Date: 2026-04-17

Adds two tables so every signal contributing to a quote traces back
through a Merkle-style hash chain to the raw extractor response.

- signal_provenance: one row per (assessment, signal) extraction.
  The ``provenance`` JSONB column carries the dataclass payload emitted
  by ``signal_architecture.signals.provenance.build_provenance``; the
  ``self_hash`` column is indexed + unique so chain verification is
  O(1) per node.
- provenance_chain: child_hash → parent_hash edges. Because one child
  may be derived from multiple parents (cross-source reconciliation),
  this is a join table keyed on ``assessment_id`` so the chain is
  reproducible per quote.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID


revision: str = "021"
down_revision: str = "020"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "signal_provenance",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "model_version_id",
            UUID(as_uuid=True),
            sa.ForeignKey("model_version_records.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "assessment_id",
            UUID(as_uuid=True),
            nullable=True,
            comment="FK into quotes/submissions once the link table lands.",
        ),
        sa.Column("signal_id", sa.String(length=128), nullable=False),
        sa.Column("source_name", sa.String(length=128), nullable=False),
        sa.Column("extractor_version", sa.String(length=32), nullable=False),
        sa.Column("cache_hit", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("response_status_code", sa.Integer(), nullable=False),
        sa.Column("response_hash", sa.String(length=64), nullable=False),
        sa.Column("self_hash", sa.String(length=64), nullable=False, unique=True),
        sa.Column("provenance", JSONB, nullable=False),
        sa.Column(
            "request_timestamp",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index(
        "ix_signal_provenance_model_version_signal",
        "signal_provenance",
        ["model_version_id", "signal_id"],
    )
    op.create_index(
        "ix_signal_provenance_response_hash",
        "signal_provenance",
        ["response_hash"],
    )
    op.create_index(
        "ix_signal_provenance_assessment",
        "signal_provenance",
        ["assessment_id"],
        postgresql_where=sa.text("assessment_id IS NOT NULL"),
    )

    op.create_table(
        "provenance_chain",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "assessment_id",
            UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column("parent_hash", sa.String(length=64), nullable=False),
        sa.Column("child_hash", sa.String(length=64), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.UniqueConstraint(
            "assessment_id", "parent_hash", "child_hash",
            name="uq_provenance_chain_edge",
        ),
    )
    op.create_index(
        "ix_provenance_chain_assessment",
        "provenance_chain",
        ["assessment_id"],
    )
    op.create_index(
        "ix_provenance_chain_child_hash",
        "provenance_chain",
        ["child_hash"],
    )


def downgrade() -> None:
    op.drop_index("ix_provenance_chain_child_hash", table_name="provenance_chain")
    op.drop_index("ix_provenance_chain_assessment", table_name="provenance_chain")
    op.drop_table("provenance_chain")
    op.drop_index("ix_signal_provenance_assessment", table_name="signal_provenance")
    op.drop_index("ix_signal_provenance_response_hash", table_name="signal_provenance")
    op.drop_index("ix_signal_provenance_model_version_signal", table_name="signal_provenance")
    op.drop_table("signal_provenance")

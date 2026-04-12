"""Config versions + deployments (B-2).

Revision ID: 018
Revises: 017
Create Date: 2026-04-12

Stores every coverage config edit as an immutable version row. A config
is identified by (coverage, config_name, version_number). The latest
DEPLOYED row is the "active" version. Draft -> Validated -> Calibrated
-> Deployed lifecycle.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID


revision: str = "018"
down_revision: str = "017"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "config_versions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("coverage", sa.String(50), nullable=False),
        sa.Column("config_name", sa.String(100), nullable=False),
        sa.Column("version_number", sa.Integer, nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("config_hash", sa.String(64), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="DRAFT"),
        sa.Column("validation_report", JSONB, nullable=True),
        sa.Column("calibration_report", JSONB, nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("author_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("coverage", "config_name", "version_number", name="uq_config_versions_coverage_config_version"),
    )
    op.create_index("ix_config_versions_coverage_config", "config_versions", ["coverage", "config_name"])
    op.create_index("ix_config_versions_status", "config_versions", ["status"])
    op.create_index("ix_config_versions_hash", "config_versions", ["config_hash"])

    op.create_table(
        "config_deployments",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("config_version_id", UUID(as_uuid=True), sa.ForeignKey("config_versions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("deployed_by", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("deployed_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("calibration_result", JSONB, nullable=True),
        sa.Column("rolled_back_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("rolled_back_by", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
    )
    op.create_index("ix_config_deployments_config_version", "config_deployments", ["config_version_id"])
    op.create_index("ix_config_deployments_deployed_at", "config_deployments", ["deployed_at"])


def downgrade() -> None:
    op.drop_index("ix_config_deployments_deployed_at", table_name="config_deployments")
    op.drop_index("ix_config_deployments_config_version", table_name="config_deployments")
    op.drop_table("config_deployments")
    op.drop_index("ix_config_versions_hash", table_name="config_versions")
    op.drop_index("ix_config_versions_status", table_name="config_versions")
    op.drop_index("ix_config_versions_coverage_config", table_name="config_versions")
    op.drop_table("config_versions")

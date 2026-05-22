"""v8 Phase 1: Broker data model + portal roles.

Revision ID: 030
Revises: 029
Create Date: 2026-05-21

Introduces broker as a first-class entity for the v8 client portal and
seeds the BROKER and CLIENT portal roles into every existing tenant.

Schema changes:
  - brokers: new table for broker organisations
  - users.broker_id: optional FK so BROKER-role users link to a broker
  - submissions.broker_id: optional FK so submissions placed via the
    client portal can be attributed to their broker

Seed data:
  - For each existing tenant, INSERT two new system roles:
      BROKER  -> portal:broker:read, portal:broker:reply, portal:client:read
      CLIENT  -> portal:client:read, portal:client:submit
    Permissions are intentionally portal-scoped only; portal users must
    not gain underwriter surfaces. See
    infrastructure/api/auth/permissions.py DEFAULT_ROLES.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID


# revision identifiers, used by Alembic.
revision: str = "030"
down_revision: str = "029"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # brokers
    # ------------------------------------------------------------------
    op.create_table(
        "brokers",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(64), unique=True, nullable=False),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_brokers_tenant", "brokers", ["tenant_id"])
    op.create_index("ix_brokers_slug", "brokers", ["slug"])

    # ------------------------------------------------------------------
    # users.broker_id
    # ------------------------------------------------------------------
    op.add_column(
        "users",
        sa.Column(
            "broker_id",
            UUID(as_uuid=True),
            sa.ForeignKey("brokers.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.create_index("ix_users_broker", "users", ["broker_id"])

    # ------------------------------------------------------------------
    # submissions.broker_id
    # ------------------------------------------------------------------
    op.add_column(
        "submissions",
        sa.Column(
            "broker_id",
            UUID(as_uuid=True),
            sa.ForeignKey("brokers.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.create_index("ix_submissions_broker", "submissions", ["broker_id"])

    # ==================================================================
    # SEED: BROKER + CLIENT portal roles into every existing tenant.
    #
    # Permissions are portal-scoped only -- portal users must not gain
    # underwriter surfaces. The DEFAULT_ROLES dict in
    # infrastructure/api/auth/permissions.py is the source of truth and
    # is also applied by seed/v5.py on re-seed.
    # ==================================================================
    op.execute(
        """
        INSERT INTO roles (tenant_id, name, permissions, is_system_role, description)
        SELECT
            t.id,
            'BROKER',
            '["portal:broker:read", "portal:broker:reply", "portal:client:read"]'::jsonb,
            true,
            'Broker (e.g. Marsh) -- views own book of clients and replies to underwriter queries via the client portal'
        FROM tenants t
        WHERE NOT EXISTS (
            SELECT 1 FROM roles r
            WHERE r.tenant_id = t.id AND r.name = 'BROKER'
        )
        """
    )
    op.execute(
        """
        INSERT INTO roles (tenant_id, name, permissions, is_system_role, description)
        SELECT
            t.id,
            'CLIENT',
            '["portal:client:read", "portal:client:submit"]'::jsonb,
            true,
            'Insured client -- views own signal score, peers, actions, and submissions via the client portal'
        FROM tenants t
        WHERE NOT EXISTS (
            SELECT 1 FROM roles r
            WHERE r.tenant_id = t.id AND r.name = 'CLIENT'
        )
        """
    )


def downgrade() -> None:
    # Remove seeded portal roles first (FK cascades handle role-bound users,
    # but the SET NULL on users.role_id keeps records intact).
    op.execute("DELETE FROM roles WHERE name IN ('BROKER', 'CLIENT') AND is_system_role = true")

    # Drop submissions.broker_id
    op.drop_index("ix_submissions_broker", table_name="submissions")
    op.drop_column("submissions", "broker_id")

    # Drop users.broker_id
    op.drop_index("ix_users_broker", table_name="users")
    op.drop_column("users", "broker_id")

    # Drop brokers table
    op.drop_index("ix_brokers_slug", table_name="brokers")
    op.drop_index("ix_brokers_tenant", table_name="brokers")
    op.drop_table("brokers")

"""Auth Foundation: tenants, roles, sessions, user extensions.

Revision ID: 012
Revises: 011
Create Date: 2026-04-12

Introduces enterprise-grade multi-tenant authentication:
- tenants: isolated customer organisations with optional SSO config
- roles: tenant-scoped permission sets
- user_sessions: active JWT session tracking with refresh rotation
- users extended with: tenant_id, role_id, MFA fields, is_locked

A default 'dsi-system' tenant is created and all existing users are
assigned to it with the ADMIN role. Existing API key auth continues to
work unchanged for backwards-compatibility.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID


# revision identifiers, used by Alembic.
revision: str = "012"
down_revision: str = "011"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # tenants
    # ------------------------------------------------------------------
    op.create_table(
        "tenants",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(100), unique=True, nullable=False),
        sa.Column("sso_provider", sa.String(20), nullable=False, server_default="NONE"),  # NONE | SAML | OIDC
        sa.Column("sso_metadata", JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("settings", JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_tenants_slug", "tenants", ["slug"])

    # ------------------------------------------------------------------
    # roles
    # ------------------------------------------------------------------
    op.create_table(
        "roles",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("permissions", JSONB, nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("is_system_role", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("tenant_id", "name", name="uq_roles_tenant_name"),
    )

    # ------------------------------------------------------------------
    # users -- add columns, keep existing hashed_password for backwards compat
    # ------------------------------------------------------------------
    op.add_column("users", sa.Column("tenant_id", UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="RESTRICT"), nullable=True))
    op.add_column("users", sa.Column("role_id", UUID(as_uuid=True), sa.ForeignKey("roles.id", ondelete="RESTRICT"), nullable=True))
    op.add_column("users", sa.Column("mfa_secret", sa.String(255), nullable=True))
    op.add_column("users", sa.Column("mfa_backup_codes", JSONB, nullable=True))
    op.add_column("users", sa.Column("mfa_enabled", sa.Boolean, nullable=False, server_default=sa.false()))
    op.add_column("users", sa.Column("is_locked", sa.Boolean, nullable=False, server_default=sa.false()))
    op.add_column("users", sa.Column("failed_login_attempts", sa.Integer, nullable=False, server_default="0"))
    op.add_column("users", sa.Column("password_reset_token_hash", sa.String(255), nullable=True))
    op.add_column("users", sa.Column("password_reset_expires_at", sa.DateTime(timezone=True), nullable=True))

    op.create_index("ix_users_tenant", "users", ["tenant_id"])

    # ------------------------------------------------------------------
    # user_sessions
    # ------------------------------------------------------------------
    op.create_table(
        "user_sessions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("tenant_id", UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("refresh_token_hash", sa.String(255), unique=True, nullable=False),
        sa.Column("user_agent", sa.Text, nullable=True),
        sa.Column("ip_address", sa.String(45), nullable=True),  # IPv6 max 45 chars
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_activity_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_user_sessions_user", "user_sessions", ["user_id"])
    op.create_index("ix_user_sessions_refresh_hash", "user_sessions", ["refresh_token_hash"])
    op.create_index("ix_user_sessions_expires", "user_sessions", ["expires_at"])

    # ==================================================================
    # SEED DATA: default tenant + default roles + assign existing users
    # ==================================================================
    op.execute(
        """
        INSERT INTO tenants (id, name, slug, sso_provider, settings, is_active)
        VALUES (
            '00000000-0000-0000-0000-000000000001',
            'DSI System',
            'dsi-system',
            'NONE',
            '{"session_duration_minutes": 15, "refresh_duration_days": 7, "mfa_required": false}'::jsonb,
            true
        )
        """
    )

    # Default roles -- permissions are granular, see infrastructure/api/auth/permissions.py
    _default_roles = [
        ("UNDERWRITER", [
            "assessment:read", "assessment:write", "assessment:refer",
            "entity:read", "world_engine:view",
        ], "Standard underwriter -- can create and process assessments, raise referrals"),
        ("SENIOR_UNDERWRITER", [
            "assessment:read", "assessment:write", "assessment:refer",
            "entity:read", "config:read", "world_engine:view", "portfolio:view",
        ], "Senior underwriter -- includes config read and portfolio view"),
        ("ACTUARIAL", [
            "assessment:read", "assessment:write", "assessment:refer",
            "entity:read", "config:read", "config:write",
            "recalibration:view", "recalibration:approve",
            "world_engine:view", "portfolio:view",
        ], "Actuarial -- can propose and approve recalibration"),
        ("ADMIN", [
            "assessment:read", "assessment:write", "assessment:refer",
            "entity:read", "entity:write",
            "config:read", "config:write", "config:deploy",
            "admin:users", "admin:system", "admin:audit",
            "recalibration:view", "recalibration:approve",
            "world_engine:view", "portfolio:view", "portfolio:simulate",
        ], "Full administrative access"),
        ("READ_ONLY", [
            "assessment:read", "entity:read", "config:read",
            "world_engine:view", "portfolio:view",
        ], "Read-only across all resources"),
    ]

    import json
    for name, perms, desc in _default_roles:
        op.execute(
            f"""
            INSERT INTO roles (tenant_id, name, permissions, is_system_role, description)
            VALUES (
                '00000000-0000-0000-0000-000000000001',
                '{name}',
                '{json.dumps(perms)}'::jsonb,
                true,
                '{desc}'
            )
            """
        )

    # Backfill existing users to default tenant + ADMIN role (they are the
    # seed/system users and currently have permissions=[] so they need
    # something). Real tenant assignment happens post-migration.
    op.execute(
        """
        UPDATE users
        SET tenant_id = '00000000-0000-0000-0000-000000000001',
            role_id = (
                SELECT id FROM roles
                WHERE tenant_id = '00000000-0000-0000-0000-000000000001' AND name = 'ADMIN'
                LIMIT 1
            )
        WHERE tenant_id IS NULL
        """
    )

    # After backfill, tenant_id should be NOT NULL. But we keep it nullable
    # for now so new user creation flows can be incremental. The auth
    # middleware enforces that authenticated requests have a tenant_id.


def downgrade() -> None:
    op.drop_index("ix_user_sessions_expires", table_name="user_sessions")
    op.drop_index("ix_user_sessions_refresh_hash", table_name="user_sessions")
    op.drop_index("ix_user_sessions_user", table_name="user_sessions")
    op.drop_table("user_sessions")

    op.drop_index("ix_users_tenant", table_name="users")
    op.drop_column("users", "password_reset_expires_at")
    op.drop_column("users", "password_reset_token_hash")
    op.drop_column("users", "failed_login_attempts")
    op.drop_column("users", "is_locked")
    op.drop_column("users", "mfa_enabled")
    op.drop_column("users", "mfa_backup_codes")
    op.drop_column("users", "mfa_secret")
    op.drop_column("users", "role_id")
    op.drop_column("users", "tenant_id")

    op.drop_table("roles")
    op.drop_index("ix_tenants_slug", table_name="tenants")
    op.drop_table("tenants")

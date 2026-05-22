"""v8 Phase 1 — portal roles & permissions.

Verifies that:
  - The four portal:* permissions are present on the Permission enum
  - DEFAULT_ROLES contains BROKER and CLIENT entries with the correct
    portal-scoped permissions
  - Carrier-side roles (UNDERWRITER, etc.) do NOT pick up portal
    permissions through the development blanket assignment
  - The Broker SQLAlchemy model and its relationships are wired
"""
from __future__ import annotations

import pytest

from infrastructure.api.auth.permissions import (
    DEFAULT_ROLES,
    Permission,
)


class TestPermissionEnum:
    def test_portal_broker_read(self):
        assert Permission.PORTAL_BROKER_READ.value == "portal:broker:read"

    def test_portal_broker_reply(self):
        assert Permission.PORTAL_BROKER_REPLY.value == "portal:broker:reply"

    def test_portal_client_read(self):
        assert Permission.PORTAL_CLIENT_READ.value == "portal:client:read"

    def test_portal_client_submit(self):
        assert Permission.PORTAL_CLIENT_SUBMIT.value == "portal:client:submit"

    def test_no_other_portal_permissions(self):
        portal_perms = [p for p in Permission if p.value.startswith("portal:")]
        assert len(portal_perms) == 4


class TestDefaultRolesBroker:
    def test_broker_role_present(self):
        assert "BROKER" in DEFAULT_ROLES

    def test_broker_has_broker_read(self):
        assert Permission.PORTAL_BROKER_READ in DEFAULT_ROLES["BROKER"]

    def test_broker_has_broker_reply(self):
        assert Permission.PORTAL_BROKER_REPLY in DEFAULT_ROLES["BROKER"]

    def test_broker_has_client_read(self):
        # Brokers see their clients' portal-side view too
        assert Permission.PORTAL_CLIENT_READ in DEFAULT_ROLES["BROKER"]

    def test_broker_lacks_carrier_permissions(self):
        carrier_perms = {
            Permission.ASSESSMENT_WRITE,
            Permission.CONFIG_WRITE,
            Permission.ADMIN_SYSTEM,
            Permission.ADMIN_USERS,
            Permission.RECALIBRATION_APPROVE,
        }
        broker_perms = set(DEFAULT_ROLES["BROKER"])
        leaked = carrier_perms & broker_perms
        assert not leaked, f"BROKER must not hold carrier permissions: {leaked}"

    def test_broker_lacks_client_submit(self):
        # Brokers don't initiate submissions on behalf of clients in v8
        assert Permission.PORTAL_CLIENT_SUBMIT not in DEFAULT_ROLES["BROKER"]


class TestDefaultRolesClient:
    def test_client_role_present(self):
        assert "CLIENT" in DEFAULT_ROLES

    def test_client_has_client_read(self):
        assert Permission.PORTAL_CLIENT_READ in DEFAULT_ROLES["CLIENT"]

    def test_client_has_client_submit(self):
        assert Permission.PORTAL_CLIENT_SUBMIT in DEFAULT_ROLES["CLIENT"]

    def test_client_lacks_broker_permissions(self):
        assert Permission.PORTAL_BROKER_READ not in DEFAULT_ROLES["CLIENT"]
        assert Permission.PORTAL_BROKER_REPLY not in DEFAULT_ROLES["CLIENT"]

    def test_client_lacks_carrier_permissions(self):
        carrier_perms = {
            Permission.ASSESSMENT_READ,
            Permission.ASSESSMENT_WRITE,
            Permission.CONFIG_READ,
            Permission.ADMIN_SYSTEM,
        }
        client_perms = set(DEFAULT_ROLES["CLIENT"])
        leaked = carrier_perms & client_perms
        assert not leaked, f"CLIENT must not hold carrier permissions: {leaked}"


class TestCarrierRolesUnaffected:
    """The dev shortcut for carrier roles must not leak portal permissions."""

    @pytest.mark.parametrize(
        "role_name",
        ["UNDERWRITER", "SENIOR_UNDERWRITER", "ACTUARIAL", "ADMIN", "READ_ONLY"],
    )
    def test_carrier_role_has_no_portal_perms(self, role_name):
        perms = DEFAULT_ROLES[role_name]
        portal_perms = [p for p in perms if p.value.startswith("portal:")]
        assert not portal_perms, (
            f"{role_name} should not carry portal:* permissions; found {portal_perms}"
        )


class TestBrokerModel:
    """The Broker SQLAlchemy model is wired correctly."""

    def test_broker_model_importable(self):
        from infrastructure.db.models import Broker
        assert Broker.__tablename__ == "brokers"

    def test_broker_has_tenant_relationship(self):
        from infrastructure.db.models import Broker
        rel = Broker.__mapper__.relationships
        assert "tenant" in rel
        assert "users" in rel
        assert "submissions" in rel

    def test_broker_has_slug_and_name(self):
        from infrastructure.db.models import Broker
        cols = {c.name for c in Broker.__table__.columns}
        assert "slug" in cols
        assert "name" in cols
        assert "tenant_id" in cols
        assert "is_active" in cols

    def test_user_has_broker_fk(self):
        from infrastructure.db.models import User
        cols = {c.name for c in User.__table__.columns}
        assert "broker_id" in cols

    def test_submission_has_broker_fk(self):
        from infrastructure.db.models import Submission
        cols = {c.name for c in Submission.__table__.columns}
        assert "broker_id" in cols

    def test_tenant_has_brokers_relationship(self):
        from infrastructure.db.models import Tenant
        assert "brokers" in Tenant.__mapper__.relationships

"""A-2c: AuditService pure-functional tests (no DB session required)."""

from datetime import datetime, timezone

import pytest

from infrastructure.api.audit import AuditActionType, AuditEvent
from infrastructure.api.audit.service import _summarise, _as_uuid


class TestAuditActionTypeEnum:
    def test_all_values_are_uppercase(self):
        for at in AuditActionType:
            assert at.value == at.value.upper(), f"{at} value should be uppercase"

    def test_coverage(self):
        """Sanity: confirm the enum covers the core categories."""
        values = {at.value for at in AuditActionType}
        # Authentication
        assert "LOGIN" in values
        assert "LOGOUT" in values
        # Assessment lifecycle
        assert "REFERRAL_DECISION" in values
        assert "SIGNAL_OVERRIDE" in values
        # Config
        assert "CONFIG_EDIT" in values
        assert "CONFIG_DEPLOY" in values
        # Recalibration
        assert "RECALIBRATION_APPROVE" in values


class TestAuditEvent:
    def test_minimal_construction(self):
        e = AuditEvent(action_type=AuditActionType.LOGIN)
        assert e.action_type == AuditActionType.LOGIN
        assert e.tenant_id is None
        assert e.details == {}

    def test_full_construction(self):
        e = AuditEvent(
            action_type=AuditActionType.CONFIG_EDIT,
            tenant_id="t1",
            user_id="u1",
            resource_type="coverage_config",
            resource_id="cyber_general",
            before_state={"weight": 0.1},
            after_state={"weight": 0.15},
            details={"reason": "tune"},
            ip_address="10.0.0.1",
            user_agent="curl",
        )
        assert e.before_state == {"weight": 0.1}
        assert e.after_state == {"weight": 0.15}
        assert e.details == {"reason": "tune"}


class TestSummarise:
    def test_minimal(self):
        e = AuditEvent(action_type=AuditActionType.LOGIN)
        assert _summarise(e) == "LOGIN"

    def test_with_resource(self):
        e = AuditEvent(
            action_type=AuditActionType.CONFIG_EDIT,
            resource_type="coverage_config",
            resource_id="cyber_general",
        )
        assert _summarise(e) == "CONFIG_EDIT coverage_config cyber_general"

    def test_resource_type_only(self):
        e = AuditEvent(action_type=AuditActionType.USER_CREATE, resource_type="user")
        assert _summarise(e) == "USER_CREATE user"


class TestAsUuid:
    def test_none(self):
        assert _as_uuid(None) is None

    def test_invalid(self):
        assert _as_uuid("not-a-uuid") is None

    def test_valid(self):
        import uuid
        u = uuid.uuid4()
        result = _as_uuid(str(u))
        assert result == u

    def test_already_uuid(self):
        import uuid
        u = uuid.uuid4()
        assert _as_uuid(u) == u

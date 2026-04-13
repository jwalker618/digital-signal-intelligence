"""A-1b: Permission system tests."""

import pytest
from fastapi import HTTPException

from infrastructure.api.auth.permissions import (
    DEFAULT_ROLES,
    AuthContext,
    Permission,
    get_permission_domains,
    require_any_permission,
    require_permission,
)


class TestPermissionEnum:
    def test_all_permissions_have_domain(self):
        for p in Permission:
            assert ":" in p.value, f"{p} lacks domain prefix"

    def test_domains_grouping(self):
        domains = get_permission_domains()
        assert "assessment" in domains
        assert "config" in domains
        assert "admin" in domains
        assert "recalibration" in domains
        assert "portfolio" in domains
        assert "world_engine" in domains


class TestDefaultRoles:
    def test_admin_has_all_permissions(self):
        admin_perms = set(DEFAULT_ROLES["ADMIN"])
        all_perms = set(Permission)
        assert admin_perms == all_perms

    def test_underwriter_cannot_deploy_config(self):
        assert Permission.CONFIG_DEPLOY not in DEFAULT_ROLES["UNDERWRITER"]

    def test_actuarial_can_recalibrate(self):
        assert Permission.RECALIBRATION_APPROVE in DEFAULT_ROLES["ACTUARIAL"]

    def test_read_only_cannot_write(self):
        for p in DEFAULT_ROLES["READ_ONLY"]:
            assert p.value.endswith(":read") or p.value.endswith(":view")


class TestAuthContext:
    def test_has_permission(self):
        ctx = AuthContext(
            user_id="u1",
            tenant_id="t1",
            permissions=["admin:system", "assessment:read"],
        )
        assert ctx.has_permission(Permission.ADMIN_SYSTEM)
        assert ctx.has_permission(Permission.ASSESSMENT_READ)
        assert not ctx.has_permission(Permission.CONFIG_WRITE)

    def test_has_any(self):
        ctx = AuthContext(user_id="u1", tenant_id="t1", permissions=["assessment:read"])
        assert ctx.has_any(Permission.ASSESSMENT_READ, Permission.CONFIG_WRITE)
        assert not ctx.has_any(Permission.CONFIG_WRITE, Permission.ADMIN_SYSTEM)

    def test_has_all(self):
        ctx = AuthContext(
            user_id="u1",
            tenant_id="t1",
            permissions=["assessment:read", "assessment:write"],
        )
        assert ctx.has_all(Permission.ASSESSMENT_READ, Permission.ASSESSMENT_WRITE)
        assert not ctx.has_all(Permission.ASSESSMENT_READ, Permission.CONFIG_WRITE)


class TestRequirePermission:
    def test_require_permission_allows(self):
        ctx = AuthContext(user_id="u1", tenant_id="t1", permissions=["admin:system"])
        checker = require_permission(Permission.ADMIN_SYSTEM)
        result = checker(ctx=ctx)
        assert result is ctx

    def test_require_permission_denies(self):
        ctx = AuthContext(user_id="u1", tenant_id="t1", permissions=["assessment:read"])
        checker = require_permission(Permission.ADMIN_SYSTEM)
        with pytest.raises(HTTPException) as exc_info:
            checker(ctx=ctx)
        assert exc_info.value.status_code == 403

    def test_require_any_permission(self):
        ctx = AuthContext(user_id="u1", tenant_id="t1", permissions=["assessment:read"])
        checker = require_any_permission(Permission.ASSESSMENT_READ, Permission.ADMIN_SYSTEM)
        assert checker(ctx=ctx) is ctx

    def test_require_any_denies_when_none_match(self):
        ctx = AuthContext(user_id="u1", tenant_id="t1", permissions=["config:read"])
        checker = require_any_permission(Permission.ASSESSMENT_READ, Permission.ADMIN_SYSTEM)
        with pytest.raises(HTTPException) as exc_info:
            checker(ctx=ctx)
        assert exc_info.value.status_code == 403

"""
A-1b: Permission System

Granular permissions covering all DSI capabilities. Organised by domain:
assessment, config, entity, admin, recalibration, portfolio, world_engine.

Permissions are strings stored in Role.permissions (JSONB array) and checked
via `require_permission()` FastAPI dependency.
"""

from __future__ import annotations

from enum import Enum
from typing import Optional

from fastapi import Depends, HTTPException, Request, status


class Permission(str, Enum):
    """All DSI permissions (granular, domain-prefixed)."""

    # Assessment lifecycle
    ASSESSMENT_READ = "assessment:read"
    ASSESSMENT_WRITE = "assessment:write"
    ASSESSMENT_REFER = "assessment:refer"

    # Coverage configuration
    CONFIG_READ = "config:read"
    CONFIG_WRITE = "config:write"
    CONFIG_DEPLOY = "config:deploy"

    # Commercial entity management
    ENTITY_READ = "entity:read"
    ENTITY_WRITE = "entity:write"

    # Admin backend
    ADMIN_USERS = "admin:users"
    ADMIN_SYSTEM = "admin:system"
    ADMIN_AUDIT = "admin:audit"

    # Experience-based recalibration
    RECALIBRATION_VIEW = "recalibration:view"
    RECALIBRATION_APPROVE = "recalibration:approve"

    # Portfolio intelligence
    PORTFOLIO_VIEW = "portfolio:view"
    PORTFOLIO_SIMULATE = "portfolio:simulate"

    # World Engine
    WORLD_ENGINE_VIEW = "world_engine:view"

    # v8 Client Portal -- broker and client surfaces
    PORTAL_BROKER_READ = "portal:broker:read"
    PORTAL_BROKER_REPLY = "portal:broker:reply"
    PORTAL_CLIENT_READ = "portal:client:read"
    PORTAL_CLIENT_SUBMIT = "portal:client:submit"


# Default role templates. Seeded by migration 012 (carrier roles) and
# migration 030 (v8 portal roles), and re-applied by seed_v5.py.
#
# Carrier-side roles temporarily carry the full carrier permission set so
# the whole application is exercisable without permission-gated UI hiding
# features during development. Tailor these back role-by-role once the
# product boundaries stabilise.
#
# Portal roles (BROKER, CLIENT) are intentionally scoped to portal:*
# permissions only -- they must not see underwriter surfaces.
_CARRIER_PERMISSIONS: list[Permission] = [
    p for p in Permission if not p.value.startswith("portal:")
]
_PORTAL_BROKER_PERMISSIONS: list[Permission] = [
    Permission.PORTAL_BROKER_READ,
    Permission.PORTAL_BROKER_REPLY,
    Permission.PORTAL_CLIENT_READ,
]
_PORTAL_CLIENT_PERMISSIONS: list[Permission] = [
    Permission.PORTAL_CLIENT_READ,
    Permission.PORTAL_CLIENT_SUBMIT,
]
DEFAULT_ROLES: dict[str, list[Permission]] = {
    "UNDERWRITER": list(_CARRIER_PERMISSIONS),
    "SENIOR_UNDERWRITER": list(_CARRIER_PERMISSIONS),
    "ACTUARIAL": list(_CARRIER_PERMISSIONS),
    "ADMIN": list(_CARRIER_PERMISSIONS),
    "READ_ONLY": list(_CARRIER_PERMISSIONS),
    "BROKER": list(_PORTAL_BROKER_PERMISSIONS),
    "CLIENT": list(_PORTAL_CLIENT_PERMISSIONS),
}


def get_permission_domains() -> dict[str, list[str]]:
    """Return permissions grouped by domain for the UI / role editor."""
    domains: dict[str, list[str]] = {}
    for perm in Permission:
        domain, _ = perm.value.split(":", 1)
        domains.setdefault(domain, []).append(perm.value)
    return domains


# =============================================================================
# FastAPI dependency for permission enforcement
# =============================================================================


class AuthContext:
    """Authenticated request context. Populated by tenant_middleware."""

    def __init__(
        self,
        user_id: str,
        tenant_id: str,
        role: Optional[str] = None,
        permissions: Optional[list[str]] = None,
        email: Optional[str] = None,
    ):
        self.user_id = user_id
        self.tenant_id = tenant_id
        self.role = role
        self.permissions = set(permissions or [])
        self.email = email

    def has_permission(self, perm: Permission) -> bool:
        """Check whether the authenticated user holds a specific permission."""
        return perm.value in self.permissions

    def has_any(self, *perms: Permission) -> bool:
        return any(self.has_permission(p) for p in perms)

    def has_all(self, *perms: Permission) -> bool:
        return all(self.has_permission(p) for p in perms)


def get_auth_context(request: Request) -> AuthContext:
    """Extract AuthContext from request.state (set by TenantMiddleware).

    Raises 401 if no auth context is present.
    """
    ctx = getattr(request.state, "auth", None)
    if ctx is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return ctx


def require_permission(*permissions: Permission):
    """Return a FastAPI dependency that enforces all listed permissions.

    Usage:
        @router.get("/admin/health", dependencies=[Depends(require_permission(Permission.ADMIN_SYSTEM))])
        async def health(): ...
    """
    required = list(permissions)

    def checker(ctx: AuthContext = Depends(get_auth_context)) -> AuthContext:
        missing = [p for p in required if not ctx.has_permission(p)]
        if missing:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: requires {[p.value for p in missing]}",
            )
        return ctx

    return checker


def require_any_permission(*permissions: Permission):
    """FastAPI dependency requiring at least one of the listed permissions."""
    required = list(permissions)

    def checker(ctx: AuthContext = Depends(get_auth_context)) -> AuthContext:
        if not ctx.has_any(*required):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: requires any of {[p.value for p in required]}",
            )
        return ctx

    return checker

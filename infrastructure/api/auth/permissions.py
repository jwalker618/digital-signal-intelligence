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


# Default role templates. Seeded by migration 012. Kept here as the source
# of truth -- the migration references these strings literally.
DEFAULT_ROLES: dict[str, list[Permission]] = {
    "UNDERWRITER": [
        Permission.ASSESSMENT_READ,
        Permission.ASSESSMENT_WRITE,
        Permission.ASSESSMENT_REFER,
        Permission.ENTITY_READ,
        Permission.WORLD_ENGINE_VIEW,
    ],
    "SENIOR_UNDERWRITER": [
        Permission.ASSESSMENT_READ,
        Permission.ASSESSMENT_WRITE,
        Permission.ASSESSMENT_REFER,
        Permission.ENTITY_READ,
        Permission.CONFIG_READ,
        Permission.WORLD_ENGINE_VIEW,
        Permission.PORTFOLIO_VIEW,
    ],
    "ACTUARIAL": [
        Permission.ASSESSMENT_READ,
        Permission.ASSESSMENT_WRITE,
        Permission.ASSESSMENT_REFER,
        Permission.ENTITY_READ,
        Permission.CONFIG_READ,
        Permission.CONFIG_WRITE,
        Permission.RECALIBRATION_VIEW,
        Permission.RECALIBRATION_APPROVE,
        Permission.WORLD_ENGINE_VIEW,
        Permission.PORTFOLIO_VIEW,
    ],
    "ADMIN": [p for p in Permission],  # all permissions
    "READ_ONLY": [
        Permission.ASSESSMENT_READ,
        Permission.ENTITY_READ,
        Permission.CONFIG_READ,
        Permission.WORLD_ENGINE_VIEW,
        Permission.PORTFOLIO_VIEW,
    ],
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

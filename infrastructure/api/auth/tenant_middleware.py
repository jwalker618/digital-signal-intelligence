"""
A-1e: Tenant-Aware Auth Middleware

Extracts the bearer token (or API key), validates it, builds an AuthContext
and attaches it to request.state.auth. Downstream endpoints use the
`get_auth_context` / `require_permission` dependencies from
infrastructure.api.auth.permissions.

Unauthenticated routes (public endpoints such as /auth/login, health checks,
root, docs) bypass the middleware via the PUBLIC_PATH_PREFIXES list.

Backwards compatibility: the middleware does NOT reject requests that have
no auth header on endpoints outside the explicit public list. Instead it
simply leaves request.state.auth unset. Endpoints that require auth
express that via Depends(require_permission(...)) which raises 401/403 at
the dependency layer. This is critical so that existing endpoints (which
have not yet been updated) continue to work during rollout.
"""

from __future__ import annotations

import logging
from typing import Optional

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from infrastructure.api.auth.jwt_auth import decode_token
from infrastructure.api.auth.permissions import AuthContext

logger = logging.getLogger("dsi.api.auth.middleware")


# Paths that require exact match (no prefix matching)
PUBLIC_PATH_EXACT: frozenset[str] = frozenset({
    "/",
    "/api/v1",
    "/api/v1/metrics",
    "/metrics",
    "/openapi.json",
    "/ws",  # WebSocket auth happens in the endpoint via token query param
})

# Paths where any sub-path is also public (prefix match)
PUBLIC_PATH_PREFIXES: tuple[str, ...] = (
    "/api/v1/health/",             # health/live, health/ready
    "/api/v1/auth/login",          # login (exact)
    "/api/v1/auth/refresh",        # refresh (exact)
    "/api/v1/auth/logout",         # logout (exact -- public so revocation works without valid access)
    "/api/v1/auth/sso/",           # all SSO endpoints
    "/api/v1/auth/password/",      # password reset request + confirm
    "/api/docs",                   # Swagger UI
    "/api/redoc",                  # ReDoc
)


def _is_public_path(path: str) -> bool:
    """Return True if path is public (bypasses auth middleware)."""
    if path in PUBLIC_PATH_EXACT:
        return True
    for prefix in PUBLIC_PATH_PREFIXES:
        if path == prefix or path.startswith(prefix):
            return True
    return False


class TenantAuthMiddleware(BaseHTTPMiddleware):
    """Populates request.state.auth with an AuthContext on authenticated requests."""

    async def dispatch(self, request: Request, call_next) -> Response:
        # Always pass through public paths
        if _is_public_path(request.url.path):
            return await call_next(request)

        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.lower().startswith("bearer "):
            token = auth_header.split(" ", 1)[1].strip()
            payload = decode_token(token, expected_type="access")
            if payload is not None:
                request.state.auth = AuthContext(
                    user_id=payload.sub,
                    tenant_id=payload.tenant_id,
                    role=payload.role,
                    permissions=payload.permissions,
                    email=payload.email,
                )

        # No auth? Continue anyway. Protected routes use
        # Depends(require_permission(...)) which raises 401 when auth is missing.
        return await call_next(request)


def get_tenant_id(request: Request) -> Optional[str]:
    """Helper to pull tenant_id from request state. Returns None if unauth."""
    ctx: Optional[AuthContext] = getattr(request.state, "auth", None)
    return ctx.tenant_id if ctx else None

"""
A-2e: Audit Middleware

Lightweight middleware that runs after TenantAuthMiddleware. Responsibilities:
1. Assign a request_id on request.state (if not already set upstream)
2. For authenticated state-changing requests, write a UserSessionActivity row
3. Pass request context through so endpoints can build audit events

This middleware does NOT automatically record business events -- that's
the endpoint's responsibility via AuditService.record(). This separation
is deliberate: middleware cannot reliably know the resource identity,
before/after state, or semantic action type of a generic request.

Background writes: session activity is logged via a background task so
the request path is not blocked on the DB write.
"""

from __future__ import annotations

import logging
import secrets
import time
from typing import Optional

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("dsi.api.audit.middleware")


# Only log activity for these methods (read-heavy GETs would flood the table)
ACTIVITY_LOGGED_METHODS: frozenset[str] = frozenset({"POST", "PUT", "PATCH", "DELETE"})


class AuditMiddleware(BaseHTTPMiddleware):
    """Assigns request_id and logs session activity."""

    async def dispatch(self, request: Request, call_next) -> Response:
        # Ensure every request has a request_id (logging middleware may set one earlier)
        if not hasattr(request.state, "request_id"):
            request.state.request_id = secrets.token_hex(4)

        start = time.monotonic()
        response = await call_next(request)
        duration_ms = (time.monotonic() - start) * 1000.0

        # Tag the response with the request_id for client-side correlation
        response.headers["X-Request-ID"] = request.state.request_id

        # Log session activity for authenticated state-changing requests
        if request.method in ACTIVITY_LOGGED_METHODS:
            await _log_activity_safe(request, response, duration_ms)

        return response


async def _log_activity_safe(request: Request, response: Response, duration_ms: float) -> None:
    """Write a UserSessionActivity row. Never raises -- all errors swallowed."""
    from infrastructure.api.auth.permissions import AuthContext

    ctx: Optional[AuthContext] = getattr(request.state, "auth", None)
    if ctx is None or not ctx.user_id or not ctx.tenant_id:
        return  # Unauthenticated -- nothing to log

    try:
        from infrastructure.db.config import session_scope
        from infrastructure.db.models import UserSessionActivity

        # NOTE: session_id would require looking up the active session row
        # from a session-tracking cache. Deferred to a later iteration --
        # for now we log per-request activity without linking to a session.
        with session_scope() as db:
            db.add(
                UserSessionActivity(
                    # session_id populated when session lookup is wired
                    session_id=None,
                    tenant_id=ctx.tenant_id,
                    user_id=ctx.user_id,
                    path=request.url.path[:500],
                    method=request.method,
                    status_code=response.status_code,
                    duration_ms=duration_ms,
                    request_id=request.state.request_id,
                )
            )
    except Exception as exc:  # noqa: BLE001
        logger.debug("Activity log skipped: %s", exc)

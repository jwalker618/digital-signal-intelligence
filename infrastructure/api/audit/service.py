"""
A-2c: Audit Service

Central service for recording business-level audit events and querying
them with rich filtering and cursor-based pagination.

Endpoints call `AuditService.record(...)` to log any state change. The
service persists to audit_logs and broadcasts a summary via WebSocket to
all connected clients in the same tenant.

Recording is sync and in-transaction -- the audit row is part of the same
commit as the business change. This ensures audit integrity: no business
change persists without its audit entry, and vice versa.
"""

from __future__ import annotations

import logging
import os
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

from fastapi import Request
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from infrastructure.db.models import AuditLog

logger = logging.getLogger("dsi.api.audit")


# =============================================================================
# Action type enum
# =============================================================================


class AuditActionType(str, Enum):
    """Granular, business-level audit action types.

    Values are strings (stored in audit_logs.action_type as a plain string)
    so new values don't require migration.
    """

    # Authentication
    LOGIN = "LOGIN"
    LOGIN_FAILED = "LOGIN_FAILED"
    LOGOUT = "LOGOUT"
    MFA_ENABLED = "MFA_ENABLED"
    PASSWORD_RESET = "PASSWORD_RESET"

    # Assessment lifecycle
    ASSESSMENT_VIEW = "ASSESSMENT_VIEW"
    ASSESSMENT_CREATE = "ASSESSMENT_CREATE"
    ASSESSMENT_UPDATE = "ASSESSMENT_UPDATE"
    REFERRAL_DECISION = "REFERRAL_DECISION"
    SIGNAL_OVERRIDE = "SIGNAL_OVERRIDE"
    PREMIUM_DISCRETION = "PREMIUM_DISCRETION"

    # Configuration
    CONFIG_VIEW = "CONFIG_VIEW"
    CONFIG_EDIT = "CONFIG_EDIT"
    CONFIG_DEPLOY = "CONFIG_DEPLOY"
    CONFIG_ROLLBACK = "CONFIG_ROLLBACK"

    # User / role admin
    USER_CREATE = "USER_CREATE"
    USER_EDIT = "USER_EDIT"
    USER_DEACTIVATE = "USER_DEACTIVATE"
    ROLE_CREATE = "ROLE_CREATE"
    ROLE_EDIT = "ROLE_EDIT"
    PERMISSION_CHANGE = "PERMISSION_CHANGE"

    # Commercial entity
    ENTITY_EDIT = "ENTITY_EDIT"

    # Recalibration
    RECALIBRATION_PROPOSE = "RECALIBRATION_PROPOSE"
    RECALIBRATION_APPROVE = "RECALIBRATION_APPROVE"
    RECALIBRATION_REJECT = "RECALIBRATION_REJECT"
    RECALIBRATION_DEPLOY = "RECALIBRATION_DEPLOY"

    # System
    SYSTEM_SETTING_CHANGE = "SYSTEM_SETTING_CHANGE"


# =============================================================================
# Event model
# =============================================================================


class AuditEvent(BaseModel):
    """Pydantic model of an audit event payload.

    Service-internal type -- external API responses use separate schemas
    (defined in the admin routes for B-4).
    """

    action_type: AuditActionType
    tenant_id: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    request_id: Optional[str] = None
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    before_state: Optional[dict] = None
    after_state: Optional[dict] = None
    details: dict = {}
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    duration_ms: Optional[float] = None


# =============================================================================
# Helper: build an AuditEvent from the FastAPI Request state
# =============================================================================


def audit_from_request(
    request: Request,
    action_type: AuditActionType,
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    before_state: Optional[dict] = None,
    after_state: Optional[dict] = None,
    details: Optional[dict] = None,
) -> AuditEvent:
    """Construct an AuditEvent pre-populated with request context.

    Endpoints typically use this helper rather than building AuditEvent
    by hand, so all HTTP metadata is captured consistently.
    """
    from infrastructure.api.auth.permissions import AuthContext

    ctx: Optional[AuthContext] = getattr(request.state, "auth", None)
    request_id = getattr(request.state, "request_id", None)

    return AuditEvent(
        action_type=action_type,
        tenant_id=ctx.tenant_id if ctx else None,
        user_id=ctx.user_id if ctx else None,
        request_id=request_id,
        resource_type=resource_type,
        resource_id=resource_id,
        before_state=before_state,
        after_state=after_state,
        details=details or {},
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )


# =============================================================================
# Push dispatch (A-4e)
# =============================================================================


def push_enabled() -> bool:
    """Push is enabled when the VAPID private key + claims email are set.

    Call sites that construct AuditService can do:

        AuditService(db, broadcaster=..., push_enabled=push_enabled())

    to opt their mutations into push fan-out without hardcoding the toggle.
    """
    return bool(os.getenv("VAPID_PRIVATE_KEY")) and bool(os.getenv("VAPID_CLAIMS_EMAIL"))


def _dispatch_push(
    *,
    tenant_id: str,
    actor_id: Optional[str],
    action_type: str,
    resource_type: Optional[str],
    ws_broadcaster: Any,
) -> None:
    """Send push notifications to tenant members who are offline + opted-in.

    Uses a fresh DB session (the triggering commit has already happened).
    Kept at module level for testability and so AuditService stays lean.
    """
    from infrastructure.api.push.categories import category_for_action
    from infrastructure.api.push.service import PushService
    from infrastructure.db.config import session_scope
    from infrastructure.db.models import User

    category = category_for_action(action_type)
    if category is None:
        return

    title = action_type.replace("_", " ").title()
    body = f"A {resource_type or 'resource'} was updated in your tenant."

    try:
        with session_scope() as db:
            rows = db.execute(
                select(User.id).where(
                    User.tenant_id == tenant_id,
                    User.is_active == True,  # noqa: E712
                )
            ).all()
            recipient_ids = [str(r[0]) for r in rows]
            if not recipient_ids:
                return
            service = PushService(db, connection_manager=ws_broadcaster)
            service.notify_event(
                action_type=action_type,
                tenant_id=tenant_id,
                actor_id=actor_id,
                recipient_ids=recipient_ids,
                title=title,
                body=body,
                url="/",
            )
    except Exception as exc:  # noqa: BLE001
        logger.debug("Push dispatch failed: %s", exc)


# =============================================================================
# AuditService
# =============================================================================


class AuditService:
    """Records business-level audit events and queries the audit trail."""

    def __init__(
        self,
        db: Session,
        broadcaster: Optional[Any] = None,
        push_enabled: bool = False,
    ):
        """
        Args:
            db: SQLAlchemy sync session. Events are added to this session
                and committed by the caller (so audit + business change
                are atomic).
            broadcaster: Optional object with `.broadcast_to_tenant_sync(tenant_id, message)`.
                         When provided, a WebSocket message is queued after
                         the session commits. If None, no broadcast.
            push_enabled: If True, after the WebSocket broadcast fires a
                push notification is dispatched to offline, opted-in
                tenant members via A-4's PushService. The dispatch uses
                a fresh DB session (the commit has already happened).
        """
        self.db = db
        self.broadcaster = broadcaster
        self.push_enabled = push_enabled

    def record(self, event: AuditEvent) -> str:
        """Persist an audit event. Returns the created audit_log id (UUID str).

        Does NOT commit -- the caller owns the transaction. A post-commit
        broadcast is scheduled via self._after_commit (if broadcaster set).
        """
        audit_id = uuid.uuid4()
        self.db.add(
            AuditLog(
                id=audit_id,
                event_type=event.action_type.value.split("_", 1)[0].lower(),
                event_action=event.action_type.value.lower(),
                action_type=event.action_type.value,
                tenant_id=_as_uuid(event.tenant_id),
                user_id=_as_uuid(event.user_id),
                session_id=_as_uuid(event.session_id),
                request_id=event.request_id,
                resource_type=event.resource_type,
                resource_code=event.resource_id,
                ip_address=event.ip_address,
                user_agent=event.user_agent,
                before_state=event.before_state,
                after_state=event.after_state,
                details=event.details or {},
                duration_ms=event.duration_ms,
                created_at=datetime.now(timezone.utc),
            )
        )
        self._schedule_broadcast(event, audit_id)
        return str(audit_id)

    def _schedule_broadcast(self, event: AuditEvent, audit_id: uuid.UUID) -> None:
        """Broadcast via WebSocket after session commit.

        Uses SQLAlchemy's after_commit event so we never broadcast an event
        that was rolled back. The `once=True` flag auto-removes the listener
        after it fires, so each event registers its own single-shot handler.
        """
        if self.broadcaster is None or not event.tenant_id:
            return

        from sqlalchemy import event as sa_event

        broadcaster = self.broadcaster
        payload = {
            "event_type": "audit",
            "action_type": event.action_type.value,
            "resource_type": event.resource_type,
            "resource_id": event.resource_id,
            "user_id": event.user_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "audit_id": str(audit_id),
            "summary": _summarise(event),
        }
        tenant_id = event.tenant_id

        push_enabled = self.push_enabled
        actor_id = event.user_id
        action_type_value = event.action_type.value
        resource_type = event.resource_type
        ws_broadcaster = self.broadcaster

        def _emit(session):
            try:
                broadcaster.broadcast_to_tenant_sync(tenant_id, payload)
            except Exception as exc:  # noqa: BLE001
                logger.warning("WebSocket broadcast failed: %s", exc)
            # A-4e: After the WS broadcast, fan out to offline subscribers.
            if not push_enabled:
                return
            try:
                _dispatch_push(
                    tenant_id=tenant_id,
                    actor_id=actor_id,
                    action_type=action_type_value,
                    resource_type=resource_type,
                    ws_broadcaster=ws_broadcaster,
                )
            except Exception as exc:  # noqa: BLE001
                logger.warning("Push dispatch failed: %s", exc)

        # once=True: SA removes the listener automatically after firing.
        # Do NOT call sa_event.remove() inside the handler -- that double-removes.
        sa_event.listen(self.db, "after_commit", _emit, once=True)

    # ------------------------------------------------------------------
    # Querying
    # ------------------------------------------------------------------

    def query(
        self,
        tenant_id: str,
        user_id: Optional[str] = None,
        action_type: Optional[AuditActionType] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        cursor: Optional[str] = None,
        limit: int = 50,
    ) -> tuple[list[AuditLog], Optional[str]]:
        """Paginated audit log query. Returns (items, next_cursor).

        Cursor is the opaque pagination token (an ISO timestamp of the last
        item in the previous page, base64-encoded).
        """
        import base64

        stmt = select(AuditLog).where(AuditLog.tenant_id == _as_uuid(tenant_id))

        if user_id:
            stmt = stmt.where(AuditLog.user_id == _as_uuid(user_id))
        if action_type:
            stmt = stmt.where(AuditLog.action_type == action_type.value)
        if resource_type:
            stmt = stmt.where(AuditLog.resource_type == resource_type)
        if resource_id:
            stmt = stmt.where(AuditLog.resource_code == resource_id)
        if date_from:
            stmt = stmt.where(AuditLog.created_at >= date_from)
        if date_to:
            stmt = stmt.where(AuditLog.created_at <= date_to)

        if cursor:
            try:
                cursor_ts = datetime.fromisoformat(base64.urlsafe_b64decode(cursor.encode()).decode())
                stmt = stmt.where(AuditLog.created_at < cursor_ts)
            except Exception:
                pass  # Invalid cursor -- ignore, return from start

        stmt = stmt.order_by(AuditLog.created_at.desc()).limit(limit + 1)

        rows = self.db.execute(stmt).scalars().all()
        has_more = len(rows) > limit
        items = list(rows[:limit])

        next_cursor: Optional[str] = None
        if has_more and items:
            last_ts = items[-1].created_at
            next_cursor = base64.urlsafe_b64encode(last_ts.isoformat().encode()).decode()

        return items, next_cursor

    def get(self, event_id: str) -> Optional[AuditLog]:
        return self.db.execute(
            select(AuditLog).where(AuditLog.id == _as_uuid(event_id))
        ).scalar_one_or_none()


# =============================================================================
# Utilities
# =============================================================================


def _as_uuid(value: Optional[str]) -> Optional[uuid.UUID]:
    if value is None:
        return None
    if isinstance(value, uuid.UUID):
        return value
    try:
        return uuid.UUID(str(value))
    except (ValueError, AttributeError):
        return None


def _summarise(event: AuditEvent) -> str:
    """Build a short human-readable summary for WebSocket broadcast."""
    parts = [event.action_type.value]
    if event.resource_type:
        parts.append(event.resource_type)
        if event.resource_id:
            parts.append(str(event.resource_id))
    return " ".join(parts)

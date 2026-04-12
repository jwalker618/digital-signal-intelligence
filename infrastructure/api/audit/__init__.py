"""A-2: Activity Audit System.

Provides:
- AuditActionType enum of all business events
- AuditService for recording events (sync) and querying them
- AuditMiddleware for enriching request context + passive activity logging
- StateCapture helpers for before/after snapshots

The WebSocket broadcasting layer lives in infrastructure.api.websocket.
"""

from infrastructure.api.audit.service import (
    AuditActionType,
    AuditEvent,
    AuditService,
    audit_from_request,
    push_enabled,
)
from infrastructure.api.audit.state_capture import (
    StateCapture,
    capture_model,
)

__all__ = [
    "AuditActionType",
    "AuditEvent",
    "AuditService",
    "StateCapture",
    "audit_from_request",
    "capture_model",
    "push_enabled",
]

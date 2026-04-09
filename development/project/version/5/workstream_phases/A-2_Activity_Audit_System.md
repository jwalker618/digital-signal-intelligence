# Phase A-2: Activity Audit System

| Item | Value |
|------|-------|
| Version | 1.0 |
| Depends on | A-1 (user/tenant model) |

---

## Overview

Comprehensive audit trail capturing every user action with before/after state, plus WebSocket-based real-time sync so all connected clients see changes immediately. This is the infrastructure that all subsequent admin and governance features depend on.

## Current State

- `infrastructure/db/models.py` -- `AuditLog` model exists with basic fields (`event_type`, `event_action`, `resource_type`, `user_id`). It captures compliance events but not before/after state diffs.
- `infrastructure/api/main.py` -- Request logging middleware tracks request ID and timing, but not state changes.
- No WebSocket infrastructure. No real-time sync. No session tracking.

## Target State

- Every state-changing API call produces an audit entry with before/after state
- WebSocket server broadcasts changes to all connected clients in the same tenant
- Session activity tracking (duration, pages, actions)

---

## Implementation Plan

### A-2a: Audit Log Model Enhancement

**Migration**: `alembic/versions/013_audit_system.py`

Extend or replace `AuditLog`:

| Table | Key Columns |
|-------|-------------|
| `audit_events` | `id` (UUID), `tenant_id` FK, `user_id` FK, `action_type` (enum), `resource_type`, `resource_id`, `before_state` (JSONB), `after_state` (JSONB), `metadata` (JSONB -- IP, user agent, session_id), `timestamp` |
| `user_sessions_activity` | `session_id` FK, `page_path`, `entered_at`, `exited_at`, `actions_count` |

**Action types enum**:
```python
class AuditActionType(str, Enum):
    LOGIN = "LOGIN"
    LOGOUT = "LOGOUT"
    ASSESSMENT_VIEW = "ASSESSMENT_VIEW"
    ASSESSMENT_CREATE = "ASSESSMENT_CREATE"
    REFERRAL_DECISION = "REFERRAL_DECISION"
    SIGNAL_OVERRIDE = "SIGNAL_OVERRIDE"
    PREMIUM_DISCRETION = "PREMIUM_DISCRETION"
    CONFIG_VIEW = "CONFIG_VIEW"
    CONFIG_EDIT = "CONFIG_EDIT"
    CONFIG_DEPLOY = "CONFIG_DEPLOY"
    USER_CREATE = "USER_CREATE"
    USER_EDIT = "USER_EDIT"
    PERMISSION_CHANGE = "PERMISSION_CHANGE"
    ENTITY_EDIT = "ENTITY_EDIT"
    RECALIBRATION_PROPOSE = "RECALIBRATION_PROPOSE"
    RECALIBRATION_APPROVE = "RECALIBRATION_APPROVE"
    RECALIBRATION_REJECT = "RECALIBRATION_REJECT"
    SYSTEM_SETTING_CHANGE = "SYSTEM_SETTING_CHANGE"
```

**Indexes**: composite on (`tenant_id`, `timestamp`); on (`user_id`, `timestamp`); on (`resource_type`, `resource_id`).

### A-2b: Audit Middleware

**New file**: `infrastructure/api/audit/middleware.py`

```python
class AuditMiddleware:
    """Intercepts state-changing API requests, captures before/after state."""

    AUDITED_METHODS = {"POST", "PUT", "PATCH", "DELETE"}

    async def __call__(self, request: Request, call_next):
        """
        1. If method in AUDITED_METHODS, snapshot resource state before
        2. Execute request
        3. Snapshot resource state after
        4. Store audit_event with both states
        5. Broadcast via WebSocket manager
        """
```

**New file**: `infrastructure/api/audit/state_capture.py`

```python
class StateCapture:
    """Captures resource state for audit before/after comparison."""

    def capture(self, resource_type: str, resource_id: str) -> dict | None:
        """Load current state of a resource as a JSON-serialisable dict."""
```

### A-2c: WebSocket Server

**New file**: `infrastructure/api/websocket/manager.py`

```python
class ConnectionManager:
    """Manages WebSocket connections grouped by tenant."""

    async def connect(self, websocket: WebSocket, tenant_id: str, user_id: str): ...
    async def disconnect(self, websocket: WebSocket): ...
    async def broadcast_to_tenant(self, tenant_id: str, message: dict): ...
    async def get_active_users(self, tenant_id: str) -> list[dict]: ...
```

**New file**: `infrastructure/api/websocket/routes.py`

```python
@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    Authenticate via token query param.
    Join tenant channel.
    Receive broadcast messages: {event_type, resource_type, resource_id, user_id, timestamp, summary}
    Heartbeat every 30s to track active sessions.
    """
```

**File to modify**: `infrastructure/api/main.py` -- Mount WebSocket route, add AuditMiddleware.

### A-2d: Audit Service

**New file**: `infrastructure/api/audit/service.py`

```python
class AuditService:
    """Central service for recording and querying audit events."""

    def record(self, event: AuditEvent) -> None:
        """Persist to DB and broadcast via WebSocket."""

    def query(
        self,
        tenant_id: str,
        user_id: str | None = None,
        action_type: AuditActionType | None = None,
        resource_type: str | None = None,
        resource_id: str | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        cursor: str | None = None,
        limit: int = 50,
    ) -> tuple[list[AuditEvent], str | None]:
        """Paginated query with cursor-based scrolling."""
```

---

## Constraints

1. Audit writes must not block the API response -- use background task or async write
2. WebSocket broadcasts must reach clients within 500ms
3. Audit data is append-only -- no updates or deletes
4. Before/after state capture must handle missing resources gracefully (create = no before, delete = no after)

## Success Criteria

1. Every state-changing API call produces an audit log entry with before/after state
2. WebSocket broadcasts reach all connected clients in same tenant within 500ms
3. Audit log is queryable by user, action type, resource, and date range
4. Session duration and page views are tracked
5. All existing API functionality works unchanged

"""
B-4: Audit Log Viewer API

Searchable, filterable access to the audit trail written by A-2. All
endpoints tenant-scoped + gated by admin:audit.

Endpoints:
    GET  /admin/audit                  Paginated query with filters
    GET  /admin/audit/{event_id}       Single event with full before/after
    GET  /admin/audit/export           CSV or JSON download (streamed)
    GET  /admin/audit/timeline/resource/{type}/{id}
    GET  /admin/audit/timeline/user/{user_id}
"""

from __future__ import annotations

import csv
import io
import json
import logging
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from infrastructure.api.audit import AuditActionType, AuditService
from infrastructure.api.auth.permissions import (
    AuthContext,
    Permission,
    get_auth_context,
    require_permission,
)
from infrastructure.db.config import get_db
from infrastructure.db.models import AuditLog

logger = logging.getLogger("dsi.api.admin.audit")
router = APIRouter()


# =============================================================================
# Helpers
# =============================================================================


def _event_to_dict(ev: AuditLog) -> dict:
    """Flatten an AuditLog row into a JSON-safe dict."""
    return {
        "id": str(ev.id),
        "tenant_id": str(ev.tenant_id) if ev.tenant_id else None,
        "user_id": str(ev.user_id) if ev.user_id else None,
        "session_id": str(ev.session_id) if ev.session_id else None,
        "request_id": ev.request_id,
        "action_type": ev.action_type,
        "event_type": ev.event_type,
        "event_action": ev.event_action,
        "resource_type": ev.resource_type,
        "resource_id": ev.resource_code,
        "before_state": ev.before_state,
        "after_state": ev.after_state,
        "details": ev.details or {},
        "ip_address": ev.ip_address,
        "user_agent": ev.user_agent,
        "duration_ms": ev.duration_ms,
        "created_at": ev.created_at.isoformat() if ev.created_at else None,
    }


# =============================================================================
# Paginated query
# =============================================================================


@router.get(
    "/admin/audit",
    dependencies=[Depends(require_permission(Permission.ADMIN_AUDIT))],
)
def list_audit_events(
    user_id: Optional[str] = None,
    action_type: Optional[AuditActionType] = None,
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    cursor: Optional[str] = None,
    limit: int = Query(default=50, ge=1, le=500),
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> dict:
    """Paginated audit log with rich filters + cursor-based next-page token."""
    items, next_cursor = AuditService(db).query(
        tenant_id=ctx.tenant_id,
        user_id=user_id,
        action_type=action_type,
        resource_type=resource_type,
        resource_id=resource_id,
        date_from=date_from,
        date_to=date_to,
        cursor=cursor,
        limit=limit,
    )
    return {
        "events": [_event_to_dict(e) for e in items],
        "next_cursor": next_cursor,
        "count": len(items),
    }


# =============================================================================
# Single event detail -- namespaced under /events/ so it doesn't collide
# with /export and /timeline path literals.
# =============================================================================


@router.get(
    "/admin/audit/events/{event_id}",
    dependencies=[Depends(require_permission(Permission.ADMIN_AUDIT))],
)
def get_audit_event(
    event_id: str,
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> dict:
    """Full audit event including before/after state diffs."""
    try:
        ev = AuditService(db).get(event_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Audit event not found")
    if ev is None:
        raise HTTPException(status_code=404, detail="Audit event not found")
    if ev.tenant_id is not None and str(ev.tenant_id) != ctx.tenant_id:
        # Don't leak cross-tenant rows
        raise HTTPException(status_code=404, detail="Audit event not found")
    return _event_to_dict(ev)


# =============================================================================
# Export (streaming)
# =============================================================================


@router.get(
    "/admin/audit/export",
    dependencies=[Depends(require_permission(Permission.ADMIN_AUDIT))],
)
def export_audit(
    format: str = Query(default="json", pattern="^(csv|json)$"),
    user_id: Optional[str] = None,
    action_type: Optional[AuditActionType] = None,
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    max_rows: int = Query(default=10_000, ge=1, le=100_000),
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
):
    """Download filtered audit events as CSV or JSON.

    Streams the results in chunks of 1000 rows so large exports don't
    require the entire set in memory.
    """
    svc = AuditService(db)
    filename_base = f"audit_{ctx.tenant_id[:8]}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"

    if format == "csv":
        headers = {
            "Content-Disposition": f'attachment; filename="{filename_base}.csv"',
        }
        return StreamingResponse(
            _stream_csv(
                svc, ctx.tenant_id,
                user_id, action_type, resource_type, resource_id,
                date_from, date_to, max_rows,
            ),
            media_type="text/csv",
            headers=headers,
        )

    headers = {
        "Content-Disposition": f'attachment; filename="{filename_base}.json"',
    }
    return StreamingResponse(
        _stream_json(
            svc, ctx.tenant_id,
            user_id, action_type, resource_type, resource_id,
            date_from, date_to, max_rows,
        ),
        media_type="application/json",
        headers=headers,
    )


def _iter_pages(
    svc: AuditService,
    tenant_id: str,
    user_id: Optional[str],
    action_type: Optional[AuditActionType],
    resource_type: Optional[str],
    resource_id: Optional[str],
    date_from: Optional[datetime],
    date_to: Optional[datetime],
    max_rows: int,
    page_size: int = 1000,
):
    """Yield pages of audit events until max_rows is reached or data runs out."""
    cursor: Optional[str] = None
    yielded = 0
    while yielded < max_rows:
        remaining = max_rows - yielded
        page_limit = min(page_size, remaining)
        items, next_cursor = svc.query(
            tenant_id=tenant_id,
            user_id=user_id,
            action_type=action_type,
            resource_type=resource_type,
            resource_id=resource_id,
            date_from=date_from,
            date_to=date_to,
            cursor=cursor,
            limit=page_limit,
        )
        if not items:
            return
        for ev in items:
            yield ev
            yielded += 1
            if yielded >= max_rows:
                return
        if next_cursor is None:
            return
        cursor = next_cursor


def _stream_csv(
    svc: AuditService,
    tenant_id: str,
    user_id: Optional[str],
    action_type: Optional[AuditActionType],
    resource_type: Optional[str],
    resource_id: Optional[str],
    date_from: Optional[datetime],
    date_to: Optional[datetime],
    max_rows: int,
):
    """Streaming CSV generator."""
    columns = [
        "id", "created_at", "action_type", "user_id", "tenant_id",
        "resource_type", "resource_id", "request_id",
        "ip_address", "user_agent", "duration_ms",
        "before_state", "after_state", "details",
    ]
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=columns, extrasaction="ignore")
    writer.writeheader()
    yield buf.getvalue()

    for ev in _iter_pages(
        svc, tenant_id, user_id, action_type, resource_type, resource_id,
        date_from, date_to, max_rows,
    ):
        buf.seek(0)
        buf.truncate()
        d = _event_to_dict(ev)
        # JSON-encode complex fields to keep each CSV cell scalar
        for key in ("before_state", "after_state", "details"):
            if d.get(key) is not None:
                d[key] = json.dumps(d[key], default=str)
        writer.writerow(d)
        yield buf.getvalue()


def _stream_json(
    svc: AuditService,
    tenant_id: str,
    user_id: Optional[str],
    action_type: Optional[AuditActionType],
    resource_type: Optional[str],
    resource_id: Optional[str],
    date_from: Optional[datetime],
    date_to: Optional[datetime],
    max_rows: int,
):
    """Streaming JSON array generator."""
    yield "["
    first = True
    for ev in _iter_pages(
        svc, tenant_id, user_id, action_type, resource_type, resource_id,
        date_from, date_to, max_rows,
    ):
        if not first:
            yield ","
        first = False
        yield json.dumps(_event_to_dict(ev), default=str)
    yield "]"


# =============================================================================
# Timelines
# =============================================================================


@router.get(
    "/admin/audit/timeline/resource/{resource_type}/{resource_id}",
    dependencies=[Depends(require_permission(Permission.ADMIN_AUDIT))],
)
def resource_timeline(
    resource_type: str,
    resource_id: str,
    limit: int = Query(default=200, ge=1, le=1000),
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> dict:
    """All audit events for a single resource, chronological."""
    stmt = (
        select(AuditLog)
        .where(
            AuditLog.tenant_id == UUID(ctx.tenant_id),
            AuditLog.resource_type == resource_type,
            AuditLog.resource_code == resource_id,
        )
        .order_by(AuditLog.created_at.asc())
        .limit(limit)
    )
    rows = db.execute(stmt).scalars().all()
    return {
        "resource_type": resource_type,
        "resource_id": resource_id,
        "events": [_event_to_dict(e) for e in rows],
        "count": len(rows),
    }


@router.get(
    "/admin/audit/timeline/user/{user_id}",
    dependencies=[Depends(require_permission(Permission.ADMIN_AUDIT))],
)
def user_timeline(
    user_id: str,
    limit: int = Query(default=500, ge=1, le=2000),
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> dict:
    """All audit events by a single user, newest first."""
    try:
        uid = UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user_id")

    stmt = (
        select(AuditLog)
        .where(
            AuditLog.tenant_id == UUID(ctx.tenant_id),
            AuditLog.user_id == uid,
        )
        .order_by(AuditLog.created_at.desc())
        .limit(limit)
    )
    rows = db.execute(stmt).scalars().all()
    return {
        "user_id": user_id,
        "events": [_event_to_dict(e) for e in rows],
        "count": len(rows),
    }

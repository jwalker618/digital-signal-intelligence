# Phase B-4: Audit Log Viewer

| Item | Value |
|------|-------|
| Version | 1.0 |
| Depends on | A-2 (audit log data) |

---

## Overview

Searchable, filterable UI for the audit trail produced by Phase A-2. Provides compliance visibility with before/after state diffs, timeline views, and export capabilities.

## Current State

- A-2 creates `audit_events` table with before/after state, action types, metadata.
- A-2 provides `AuditService.query()` with cursor-based pagination and filtering.
- No UI to visualise or search audit data.

## Target State

Admin page with rich filtering, expandable state diffs, timeline views, and CSV/JSON export.

---

## Implementation Plan

### B-4a: Audit Query API Extension

**New file**: `infrastructure/api/admin/audit_routes.py`

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/admin/audit` | GET | Paginated audit log with filters (user, action, resource, date range) |
| `/admin/audit/{id}` | GET | Single audit event with full before/after |
| `/admin/audit/export` | GET | Download filtered results as CSV or JSON |
| `/admin/audit/timeline/{resource_type}/{resource_id}` | GET | Per-resource chronological timeline |
| `/admin/audit/user/{user_id}/timeline` | GET | Per-user activity timeline |

All endpoints require `admin:audit` permission.

### B-4b: Frontend -- Audit Log UI

**New file**: `frontend/src/app/admin/audit/page.tsx`

- Table: timestamp, user, action, resource, summary
- Expandable rows showing JSON diff of before/after state
- Filter bar: user selector, action type dropdown, resource type dropdown, date range picker
- Quick filters: "My actions today", "Config changes this week", "Referral decisions this month"

**New file**: `frontend/src/components/admin/AuditTimeline.tsx`
- Chronological timeline view for per-entity or per-user activity
- Linked from entity detail pages and user management

**New file**: `frontend/src/components/admin/StateDiffViewer.tsx`
- JSON diff renderer: added (green), removed (red), changed (amber)
- Handles nested JSONB structures from before/after state

**New file**: `frontend/src/components/admin/AuditExport.tsx`
- Export button: applies current filters, downloads CSV or JSON

---

## Constraints

1. Audit data is read-only in the viewer -- no edit/delete capability
2. Export must handle large datasets via streaming (not load all into memory)
3. Pagination must be cursor-based for consistent results during concurrent writes

## Success Criteria

1. All audit log entries are queryable and filterable
2. Before/after state diffs render correctly for all resource types
3. Timeline view shows chronological activity
4. Export produces valid CSV/JSON
5. Performance: 10,000+ audit entries load and paginate smoothly

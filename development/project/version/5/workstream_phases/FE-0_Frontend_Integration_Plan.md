# Frontend Integration Plan

| Item | Value |
|------|-------|
| Version | 1.0 |
| Date | April 2026 |
| Classification | Cross-Phase Integration Plan |

---

## Overview

Unified plan for integrating all v5 features into the frontend. Covers navigation architecture changes, new top-level routes, workbench extensions, shared patterns, state management, and TypeScript type additions.

## Current State

- `frontend/src/app/layout.tsx` -- App shell with collapsible sidebar. Top-level: Submissions (Referral Pipeline, Full Pipeline, Performance Metrics) + World Engine. Drill-down mode: Summary, Commercial Terms, Risk Terms, Technical Assessment categories.
- `frontend/src/store/dsiStore.ts` -- Zustand store managing `activeMenu`, `activeSubmission`, navigation, categories.
- `frontend/src/context/UserContext.tsx` -- Basic user context (not auth-aware).
- `frontend/src/types/dsi.ts` -- DSI TypeScript types.
- No auth gating, no admin section, no portfolio route, no login page.

---

## Navigation Architecture

### Before (current)

```
Sidebar (top-level):
├── Submissions
│   ├── Referral Pipeline
│   ├── Full Pipeline
│   └── Performance Metrics
└── World Engine
```

### After (v5)

```
Sidebar (top-level, permission-gated):
├── Submissions                          [assessment:read]
│   ├── Referral Pipeline
│   ├── Full Pipeline
│   └── Performance Metrics
├── Portfolio                            [portfolio:view]       (WE-5)
├── World Engine                         [world_engine:view]    (WE-1+)
├── Admin                                [admin:system]         (B-1+)
│   ├── System Health                    (B-1)
│   ├── Pipeline Monitor                 (B-1)
│   ├── Config Management                (B-2)
│   ├── Users & Roles                    (B-3)
│   ├── Audit Log                        (B-4)
│   ├── Loss Register                    (C-1)
│   └── Recalibration                    (C-3)
└── Profile (bottom bar)                 (A-3)
```

### Implementation

**File to modify**: `frontend/src/app/layout.tsx`

1. Wrap entire app with `<AuthGuard>` (A-3) -- redirects to `/login` if not authenticated
2. Add permission-gated sidebar items using `authStore.hasPermission()`
3. Add Admin expandable group with sub-items
4. Add Portfolio top-level item
5. Bottom bar: replace placeholder user icon with profile link showing user name/avatar

**File to modify**: `frontend/src/store/dsiStore.ts`

Add to store:
- `activeAdminSection: string | null` -- tracks admin sub-navigation
- `portfolioEntityId: string | null` -- active portfolio entity

---

## New Routes

| Route | Phase | Component | Access |
|-------|-------|-----------|--------|
| `/login` | A-3 | `app/login/page.tsx` | Public |
| `/reset-password` | A-3 | `app/reset-password/page.tsx` | Public |
| `/profile` | A-3 | `app/profile/page.tsx` | Authenticated |
| `/admin` | B-1 | `app/admin/page.tsx` (System Health dashboard) | `admin:system` |
| `/admin/pipeline` | B-1 | `app/admin/pipeline/page.tsx` | `admin:system` |
| `/admin/configs` | B-2 | `app/admin/configs/page.tsx` | `config:read` |
| `/admin/users` | B-3 | `app/admin/users/page.tsx` | `admin:users` |
| `/admin/roles` | B-3 | `app/admin/roles/page.tsx` | `admin:users` |
| `/admin/audit` | B-4 | `app/admin/audit/page.tsx` | `admin:audit` |
| `/admin/losses` | C-1 | `app/admin/losses/page.tsx` | `assessment:write` |
| `/admin/recalibration` | C-3 | `app/admin/recalibration/page.tsx` | `recalibration:view` |
| `/admin/recalibration/[id]` | C-3 | `app/admin/recalibration/[id]/page.tsx` | `recalibration:view` |
| `/portfolio/[entityId]` | WE-5 | `app/portfolio/[entityId]/page.tsx` | `portfolio:view` |

---

## Workbench Extensions (Drill-Down Mode)

New components added to existing submission workbench tabs:

| Tab | New Component | Phase | Content |
|-----|--------------|-------|---------|
| Summary | `ConsistencyCard.tsx` | WE-2 | Consistency gauge, divergent pairs, cross-layer summary |
| Pricing Anatomy | `CausalAdjustmentCard.tsx` | WE-4 | CAF value, trajectory chart, precursors, static vs causal comparison |
| Premium Assembly | CAF waterfall line item | WE-4 | CAF as line item between modifiers and final premium |

These integrate into existing tabs via composition -- the existing tab components gain new card sections, they are not replaced.

---

## New Stores

| Store | Phase | Purpose |
|-------|-------|---------|
| `frontend/src/stores/authStore.ts` | A-3 | User, tenant, permissions, login/logout, MFA, token refresh |
| `frontend/src/stores/adminStore.ts` | B-1 | Admin section state, health data, alert configs |
| `frontend/src/stores/portfolioStore.ts` | WE-5 | Portfolio graph data, simulation state |

Extend existing `dsiStore.ts` with: `consistencyScore`, `cafResult`, `worldEngineStats`.

---

## Shared Components

| Component | Used By | Purpose |
|-----------|---------|---------|
| `components/shared/PermissionGate.tsx` | All | Wraps children, renders only if user has required permission |
| `components/shared/NotificationToast.tsx` | A-2 | WebSocket-driven toast for real-time changes |
| `components/shared/StateDiffViewer.tsx` | B-4, B-2, C-3 | JSON before/after diff renderer |
| `components/shared/StatusBadge.tsx` | B-1, C-3 | Coloured status badges (green/amber/red, status enums) |
| `components/shared/DateRangePicker.tsx` | B-1, B-4, C-3 | Date range filter used across admin pages |
| `components/shared/CursorPagination.tsx` | B-4, C-1 | Cursor-based pagination for large lists |

---

## TypeScript Types

**New file**: `frontend/src/types/auth.ts` (A-3)
- `User`, `Tenant`, `Role`, `Permission`, `Session`

**New file**: `frontend/src/types/admin.ts` (B-1+)
- `SystemHealth`, `ExtractorHealth`, `PipelineMetrics`, `ConfigVersion`, `AuditEvent`

**New file**: `frontend/src/types/worldEngine.ts` (WE-1+)
- `MaturityState`, `ConsistencyScore`, `CausalAdjustmentFactor`, `PortfolioGraph`, `SimulationResult`, `DriftAlert`

**New file**: `frontend/src/types/recalibration.ts` (C-1+)
- `LossEvent`, `RecalibrationProposal`, `SignalReportCard`, `ImpactAssessment`

---

## WebSocket Integration

**New file**: `frontend/src/lib/websocket.ts` (A-2)

```typescript
class DSIWebSocket {
  private ws: WebSocket | null = null;
  private handlers: Map<string, Function[]> = new Map();

  connect(token: string): void { /* ws://host/ws?token=... */ }
  onEvent(eventType: string, handler: (data: any) => void): void { ... }
  disconnect(): void { ... }
}

export const wsClient = new DSIWebSocket();
```

Connected on login (A-3). Events trigger:
- Toast notifications via `NotificationToast`
- Store invalidation: when event matches currently viewed resource, store refetches data
- Admin dashboard auto-refresh for health/pipeline data

---

## Build Order

Frontend work is phased alongside backend:

| Order | Frontend Work | Backend Dependency |
|-------|-------------|-------------------|
| 1 | Login page, auth store, AuthGuard, session management | A-1 complete |
| 2 | WebSocket client, NotificationToast, PermissionGate | A-2 complete |
| 3 | Role-based nav in layout.tsx, profile page, MFA flow, **PWA setup** (manifest, icons, next-pwa config, meta tags) | A-1 + A-2 |
| 4 | Admin shell + System Health dashboard | B-1 API |
| 5 | Config Management UI | B-2 API |
| 6 | User/Role Management pages | B-3 API |
| 7 | Audit Log Viewer | B-4 API |
| 8 | ConsistencyCard in workbench | WE-2 complete |
| 9 | CausalAdjustmentCard in workbench | WE-4 complete |
| 10 | Loss Register + bulk import | C-1 API |
| 11 | Recalibration dashboard + governance UI | C-3 API |
| 12 | **Push notifications**: subscription UI, preferences on profile page, service worker push handler | A-4 backend complete |
| 13 | Portfolio Dashboard (last -- most complex) | WE-5 complete |

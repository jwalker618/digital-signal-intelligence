# Workstreams A, B, C: Integration Summary & Dependency Chain

| Item | Value |
|------|-------|
| Version | 1.0 |
| Date | April 2026 |
| Classification | Master Reference |

---

## Dependency Chain

```
A-1 (Auth Foundation) ──────────────────────────────────────────┐
  │                                                              │
  ├──> A-2 (Audit System) ──> A-3 (Auth Frontend)               │
  │      │                                                       │
  │      └──> B-4 (Audit Log Viewer)                             │
  │                                                              │
  ├──> B-1 (System Health)  ─── can run in parallel ───┐         │
  ├──> B-2 (Config Management) ── can run in parallel ──┤         │
  └──> B-3 (User Management)  ── can run in parallel ──┘         │
                                                                 │
C-1 (Loss Ingestion) ─── no auth dependency ──────┐              │
  │                                                │              │
  └──> C-2 (Recalibration Engine) ────────────────┤              │
                                                   │              │
       C-3 (Governance UI) <── requires ───────────┴──────────────┘
       (needs A-1 auth + A-2 audit + B-2 config pipeline + C-2 engine)
```

## Recommended Build Sequence

| Order | Phase | Rationale | Parallel? |
|-------|-------|-----------|-----------|
| 1 | A-1 | Gates everything -- auth must come first | No |
| 2 | C-1 | Backend only, no auth dependency, enables C-2 | Yes (with A-2) |
| 3 | A-2 | Audit system needed for all subsequent phases | Yes (with C-1) |
| 4 | C-2 | Backend only, needs C-1, enables C-3 | Yes (with B-1, B-2) |
| 5 | B-1 | System health -- immediate operational value | Yes (with C-2, B-2) |
| 6 | B-2 | Config management -- needed for C-3 deployment | Yes (with B-1) |
| 7 | A-3 | Auth frontend -- can defer until backend stable | After A-1, A-2 |
| 8 | B-3 | User management -- admin convenience, not blocking | After A-1 |
| 9 | B-4 | Audit viewer -- consumes A-2 data | After A-2 |
| 10 | C-3 | Governance UI -- integration point, requires everything | Last |

## Migration Sequence

| Migration | Phase | Tables |
|-----------|-------|--------|
| `011_world_engine_tables.py` | WE-1 | `we_*` tables (9 tables) |
| `012_auth_foundation.py` | A-1 | `tenants`, `roles`, alter `users`, `user_sessions` |
| `013_audit_system.py` | A-2 | `audit_events`, `user_sessions_activity` |
| `014_admin_metrics.py` | B-1 | `extractor_health`, `metric_snapshots` |
| `015_config_versions.py` | B-2 | `config_versions`, `config_deployments` |
| `016_loss_data.py` | C-1 | `loss_events`, `signal_loss_pairs` |
| `017_recalibration.py` | C-2 | `recalibration_proposals` |

## New Directories

```
infrastructure/
├── api/
│   ├── admin/                    # B-1, B-2, B-3, B-4
│   │   ├── routes.py             # System health endpoints
│   │   ├── config_routes.py      # Config management endpoints
│   │   ├── user_routes.py        # User management endpoints
│   │   ├── role_routes.py        # Role management endpoints
│   │   └── audit_routes.py       # Audit log viewer endpoints
│   ├── audit/                    # A-2
│   │   ├── middleware.py
│   │   ├── service.py
│   │   └── state_capture.py
│   ├── auth/                     # A-1 (extends existing)
│   │   ├── permissions.py
│   │   ├── sso.py
│   │   ├── tenant_middleware.py
│   │   └── routes.py
│   ├── loss/                     # C-1
│   │   └── routes.py
│   ├── recalibration/            # C-3
│   │   └── routes.py
│   └── websocket/                # A-2
│       ├── manager.py
│       └── routes.py
├── admin/                        # B-1, B-2
│   ├── health.py
│   ├── extractor_tracker.py
│   ├── pipeline_metrics.py
│   ├── config_service.py
│   ├── config_diff.py
│   └── invitation_service.py     # B-3
└── recalibration/                # C-1, C-2
    ├── linker.py
    ├── engine.py
    ├── signal_analysis.py
    ├── weight_optimiser.py
    ├── tier_analysis.py
    ├── proposal.py
    ├── impact.py
    └── deployer.py               # C-3
```

## Frontend Routes

| Route | Phase | Access |
|-------|-------|--------|
| `/login` | A-3 | Public |
| `/reset-password` | A-3 | Public |
| `/profile` | A-3 | Authenticated |
| `/admin` | B-1 | `admin:system` |
| `/admin/configs` | B-2 | `config:read` (edit requires `config:write`) |
| `/admin/users` | B-3 | `admin:users` |
| `/admin/roles` | B-3 | `admin:users` |
| `/admin/audit` | B-4 | `admin:audit` |
| `/admin/losses` | C-1 | `assessment:write` |
| `/admin/recalibration` | C-3 | `recalibration:view` (approve requires `recalibration:approve`) |

## Cross-Workstream Integration Points

| From | To | Integration |
|------|----|-------------|
| A-1 | All | Permission system gates every admin/recalibration endpoint |
| A-2 | B-4 | Audit events -> viewer |
| A-2 | C-3 | Audit trail for approval/deployment chain |
| B-2 | C-3 | Config deployment pipeline used by proposal deployer |
| C-1 | C-2 | Signal-loss pairs feed recalibration engine |
| C-2 | C-3 | Proposals feed governance UI |
| WE-4 | C-2 | CAF accuracy data could feed recalibration analysis (future) |

## Effort Estimates

| Workstream | Phases | Backend | Frontend | Total |
|------------|--------|---------|----------|-------|
| A: Auth & Audit | 3 | 4-5 weeks | 3-4 weeks | 7-9 weeks |
| B: Admin Backend | 4 | 5-6 weeks | 6-8 weeks | 11-14 weeks |
| C: Recalibration | 3 | 4-5 weeks | 3-4 weeks | 7-9 weeks |
| **Total** | **10** | | | **25-32 weeks** |

With parallelisation (per the build sequence above), the critical path is approximately 16-20 weeks.

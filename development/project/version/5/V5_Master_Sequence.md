# DSI Version 5: Master Build Sequence

| Item | Value |
|------|-------|
| Version | 1.0 |
| Date | April 2026 |
| Classification | Master Execution Plan |

---

## Purpose

Single authoritative document for build sequencing across all 4 workstreams (WE, A, B, C), the frontend integration, and the consolidated seed phase. Designed to minimise rework -- each file is touched once, in the right order.

---

## Sequencing Principles

1. **Backend before frontend** -- all backend phases for a capability complete before its frontend work starts
2. **Schema before logic** -- database migrations land early, logic built on stable tables
3. **No file touched twice** -- if `workflow.py` needs changes from WE-2 and WE-4, sequence them so WE-2 goes first and WE-4 extends (not replaces) those changes
4. **Seed script is a final phase** -- individual phases do NOT modify the seed script. A single consolidated seed phase runs last, exercising all production code paths.
5. **Frontend is a final integration pass** -- individual phases define component specs. Frontend build runs as a cohesive pass after backend is stable.

---

## Master Build Sequence

### Track 1: Foundation (Sequential)

| Step | Phase | What | Modifies |
|------|-------|------|----------|
| 1 | **WE-1** | World Engine types, schema, registry, maturity evaluator | New: `world_engine/`, `alembic 011`. Modify: `infrastructure/api/main.py` |
| 2 | **A-1** | Auth models, permissions, SSO, tenant middleware | New: `infrastructure/api/auth/{permissions,sso,tenant_middleware,routes}.py`, `alembic 012`. Modify: `infrastructure/api/main.py`, `infrastructure/db/models.py` |

Both must complete before anything else. WE-1 first (no dependencies), then A-1 (or parallel if different developers -- no file conflicts).

### Track 2: Parallel Backend (after Track 1)

Three independent streams that can run simultaneously:

**Stream A: Audit + Loss**

| Step | Phase | What |
|------|-------|------|
| 3a | **A-2** | Audit middleware, WebSocket server, audit service. `alembic 013` |
| 3b | **C-1** | Loss event schema, ingestion API, signal-loss linker. `alembic 016` |

**Stream B: World Engine Intelligence**

| Step | Phase | What |
|------|-------|------|
| 3c | **WE-2** | Consistency scorer (inline + population). Modifies: `layers/risk/workflow.py` (add consistency step), `layers/risk/types.py` (add consistency fields) |
| 3d | **WE-3** | Discovery, validation, lifecycle, drift, population intelligence. New: scanner, inferencer, validator, lifecycle, drift, population, scheduler |

WE-2 and WE-3 are parallel after WE-1. WE-2 modifies `workflow.py` first; WE-3 does not touch `workflow.py`.

**Stream C: Admin Backend**

| Step | Phase | What |
|------|-------|------|
| 3e | **B-1** | System health aggregator, extractor tracking, pipeline metrics. `alembic 014` |
| 3f | **B-2** | Config versioning, diff engine, config service. `alembic 015` |
| 3g | **B-3** | User/role CRUD, invitation service |

B-1, B-2, B-3 are parallel after A-1. No file conflicts between them.

### Track 3: Dependent Backend (after Track 2)

| Step | Phase | What | Depends On |
|------|-------|------|------------|
| 4 | **WE-4** | CAF engine, trajectory, constraints. Modifies: `layers/risk/workflow.py` (add CAF step -- extends WE-2's changes), `layers/risk/pricer.py` (add CAF multiplier), `layers/risk/types.py` (add CAF fields -- extends WE-2's changes), `infrastructure/db/models.py` (add CAF columns) | WE-3 (active relationships needed) |
| 5 | **C-2** | Recalibration engine, signal analysis, weight optimiser, tier analysis, proposal generator. `alembic 017` | C-1 (loss data needed) |
| 6 | **WE-5** | Portfolio graph, concentration, simulation, marginal impact, CAF enrichment. Modifies: `infrastructure/models/commercial_schema.py` (appetite integration), `layers/risk/workflow.py` (portfolio CAF enrichment -- extends WE-4's changes) | WE-3 + WE-4 |

**Critical sequencing for `workflow.py`**: WE-2 adds consistency step -> WE-4 adds CAF step (after consistency, before pricing) -> WE-5 adds portfolio CAF enrichment (after CAF). Each extends the previous, never replaces.

**Critical sequencing for `types.py`**: WE-2 adds consistency fields -> WE-4 adds CAF fields. Each extends.

### Track 4: Frontend Integration Pass

After all backend phases are stable:

| Step | Phase | What |
|------|-------|------|
| 7a | **A-3** | Login, MFA, auth store, AuthGuard, session management, role-based navigation in `layout.tsx` |
| 7b | **FE-WE** | ConsistencyCard (WE-2), CausalAdjustmentCard (WE-4), CAF waterfall line item |
| 7c | **FE-Admin** | Admin shell, System Health (B-1), Config Management (B-2), User Management (B-3), Audit Log (B-4) |
| 7d | **FE-Loss** | Loss Register, bulk import (C-1) |
| 7e | **FE-Recal** | Recalibration dashboard, proposal detail, governance UI (C-3) |
| 7f | **FE-Portfolio** | Portfolio Dashboard, concentration panel, systemic nodes, scenario simulation (WE-5) |

7a must come first (auth gating). 7b-7f can run in parallel.

### Track 5: Seed & Validation (Final)

| Step | Phase | What |
|------|-------|------|
| 8 | **SEED** | Consolidated seed script rewrite. Exercises every production code path. Details in `SEED-0_Seed_Script_Plan.md` |

---

## File Modification Sequence

Files touched by multiple phases, showing the correct order:

### `layers/risk/workflow.py`
1. **WE-2**: Add consistency scoring step (after three-layer assessment, before pricing)
2. **WE-4**: Add CAF computation step (after consistency, before pricing)
3. **WE-5**: Add portfolio CAF enrichment (after CAF computation)

### `layers/risk/types.py`
1. **WE-2**: Add `consistency_score: float | None`, `divergent_pairs: list[str] | None`
2. **WE-4**: Add `caf_value: float | None`, `caf_confidence: float | None`, `caf_detail: dict | None`, `static_premium: float | None`

### `layers/risk/pricer.py`
1. **WE-4**: Add `caf_value: float = 1.0` parameter, multiply into final premium

### `infrastructure/db/models.py`
1. **A-1**: Add `tenant_id`, `role_id` to `User`; relationship to tenant/role
2. **WE-4**: Add `caf_value`, `caf_confidence`, `caf_constrained` to `ModelVersionRecord`

### `infrastructure/api/main.py`
1. **WE-1**: Mount world engine router
2. **A-1**: Replace auth middleware with tenant-aware version
3. **A-2**: Add audit middleware, mount WebSocket route
4. **B-1/B-2/B-3/B-4**: Mount admin router
5. **C-1**: Mount loss router
6. **C-3**: Mount recalibration router

### `infrastructure/models/commercial_schema.py`
1. **WE-5**: Add portfolio concentration check to appetite evaluation

### `frontend/src/app/layout.tsx`
1. **A-3**: Wrap with AuthGuard, add permission-gated navigation, add admin section, add portfolio item

### `seed_dsi_bench.py`
1. **SEED**: Single comprehensive rewrite (final phase)

---

## Migration Sequence

All migrations are independent (no inter-migration dependencies beyond sequential numbering):

| Migration | Phase | Tables Created |
|-----------|-------|---------------|
| `011` | WE-1 | 9 `we_*` tables |
| `012` | A-1 | `tenants`, `roles`, `user_sessions`, alter `users` + existing tables for `tenant_id` |
| `013` | A-2 | `audit_events`, `user_sessions_activity` |
| `014` | B-1 | `extractor_health`, `metric_snapshots` |
| `015` | B-2 | `config_versions`, `config_deployments` |
| `016` | C-1 | `loss_events`, `signal_loss_pairs` |
| `017` | C-2 | `recalibration_proposals` |

---

## Critical Path

```
WE-1 (1-2w) -> WE-2 (2w) -> WE-4 (3-4w) -> WE-5 (6-7w) -> SEED (1w)
                    \-> WE-3 (3-4w) -/
```

With A/B/C running in parallel on the WE backbone, the critical path is approximately **14-16 weeks backend + 4-5 weeks frontend + 1 week seed = 19-22 weeks**.

---

## What Each Phase Does NOT Do

To prevent rework, each phase explicitly excludes:

| Phase | Does NOT |
|-------|----------|
| WE-1 | Does not touch workflow.py, pricer.py, types.py, seed script, frontend |
| WE-2 | Does not touch pricer.py, seed script. Frontend deferred to Track 4 |
| WE-3 | Does not touch workflow.py, pricer.py, types.py, seed script, frontend |
| WE-4 | Does not touch seed script. Frontend deferred to Track 4 |
| WE-5 | Does not touch seed script. Frontend deferred to Track 4 |
| A-1 | Does not touch seed script, frontend |
| A-2 | Does not touch seed script, frontend |
| B-1/B-2/B-3/B-4 | Does not touch seed script. Frontend deferred to Track 4 |
| C-1/C-2 | Does not touch seed script, frontend |
| C-3 | Frontend only (governance UI). Backend API is thin wrapper around C-2 |
| SEED | Modifies seed_dsi_bench.py only. No logic changes anywhere else |

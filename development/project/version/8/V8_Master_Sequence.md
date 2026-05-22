# DSI Version 8: Master Build Sequence

| Item | Value |
|------|-------|
| Version | 1.0 |
| Date | May 2026 |
| Classification | Master Execution Plan |
| Branch | `claude/client-portal-v8-G2V8I` |

---

## Purpose

Single authoritative document for v8 build sequencing. v8 introduces the **Client Portal** — a separate front end for brokers and clients alongside the existing carrier UI — and the **closed-loop demo narrative** required for the Marsh pitch.

This document defines the eight phases, the dependency graph between them, the files each phase is allowed to touch, and the order those touches must happen in to avoid rework.

Optimised for execution by a coding agent: every phase doc is self-contained, every file path is explicit, every schema is locked, every endpoint contract is defined. The agent should not need to "explore" mid-phase — it should be able to open a phase doc and execute.

---

## v8 Scope (Locked)

Three deliverables, in priority order:

1. **Client portal frontend** — separate route group with role-aware shells for `BROKER` and `CLIENT` users. Both audiences get parity (decision: "Both, equally" per planning conversation).
2. **Peer comparison + signal impact + remediation engines** — backend services that power the portal's differentiating views. Real cohort percentiles from seed data (decision: "Real cohort from seed").
3. **Closed-loop demo** — live click-through, seven acts, deterministic reset. Demonstrates a client → carrier referral → broker query/response → premium reduction → client visibility loop. (Decision: "Live click-through".)

**Out of scope for v8**, tracked separately:
- Evidence Grade Ladder (v7 Phase 1, separate work stream — may ship before or after v8; this doc is neutral).
- Real broker SSO/identity federation (v8 uses local credentials per tenant).
- Email/webhook notifications for portal events (UI surfaces only; notifications are v8.1).
- Multi-broker support per client (v8 assumes one broker per client; schema permits but UI/business logic single-broker).
- Embedded payments / binding (out of scope — portal shows quotes, does not transact).

---

## Sequencing Principles

These are the rules each phase doc inherits. Violating any of these is a planning error.

1. **Backend before frontend.** All backend phases (1–7) complete before Phase 8 (frontend) starts.
2. **Schema before logic.** Each backend phase that needs new columns ships its Alembic migration first, then the logic that uses those columns. Migrations land in numbered order, never edited.
3. **No file touched twice within v8** unless explicitly sequenced in the "File Modification Sequence" table below. When a file is touched twice, the second touch must **extend** the first, never replace it.
4. **Seed script is touched once** — Phase 7. No backend phase modifies seed data. Phases that add data shapes must work against the existing seed until Phase 7 enriches it.
5. **Frontend is touched once** — Phase 8. No backend phase modifies anything under `frontend/`. Phase 8 is a single cohesive integration pass.
6. **Each phase ships green tests.** No phase is "done" until `pytest tests/ -v` passes locally. Phases 1–7 must not regress the existing test suite.
7. **No premature endpoint exposure.** Phases 2–5 build services and define API contracts but mount endpoints under `/api/v1/portal/*` only in Phase 6. This keeps the API surface coherent and prevents per-phase auth drift.

---

## Phase Overview

| Phase | Title | Type | Modifies | Migration |
|-------|-------|------|----------|-----------|
| 1 | Data Model & Roles | Foundation | `infrastructure/db/models.py`, `frontend/src/types/auth.ts` (types only — no UI), new auth module | Yes |
| 2 | Peer Cohort Engine | Backend service | new `layers/cohort/`, `layers/risk/workflow.py` (extends) | Yes |
| 3 | Signal Impact Breakdown | Backend service | new `layers/risk/impact_breakdown.py`, `layers/risk/workflow.py` (extends) | No |
| 4 | Remediation Engine | Backend service + config | new `layers/risk/remediation.py`, `coverages/master_config_layout.yaml`, all `coverages/*/config.yaml` | No |
| 5 | Broker Query/Reply | Backend feature | new `infrastructure/api/routes/referral_messages.py`, `infrastructure/db/models.py` (extends), `infrastructure/api/main.py` (extends) | Yes |
| 6 | Portal API Surface | Backend integration | new `infrastructure/api/routes/portal/`, `infrastructure/api/main.py` (extends) | No |
| 7 | Demo Seed & Reset | Seed | `seed/` only | No |
| 8 | Frontend Integration | Frontend | `frontend/` (single cohesive pass) | No |

---

## Dependency Graph

```
Phase 1 (data model)
  ├── Phase 2 (peer cohort)
  │     └── Phase 6 (API surface)
  ├── Phase 3 (signal impact)
  │     └── Phase 6
  ├── Phase 4 (remediation)
  │     └── Phase 6
  └── Phase 5 (query/reply)
        └── Phase 6
                └── Phase 7 (seed/reset)
                      └── Phase 8 (frontend)
```

Phases 2, 3, 4, 5 are parallelisable after Phase 1 completes. If executed by a single agent in sequence, the recommended order is **1 → 2 → 3 → 4 → 5 → 6 → 7 → 8** because earlier phases produce data that later phases consume (e.g. Phase 2's percentile rank feeds Phase 7's demo realism).

---

## File Modification Sequence

Files touched by multiple phases, in the order they must be modified. Each subsequent touch **extends** what the prior phase added — never restructures.

### `infrastructure/db/models.py`

1. **Phase 1**: Add `Broker` model. Add `broker_id: int | None` FK column on `Entity`. Add `BROKER` and `CLIENT` to the role enum.
2. **Phase 5**: Add `ReferralMessage` model. Add `messages: relationship` on the existing `Referral` model.

No other phase touches this file.

### `infrastructure/db/migrations/` (Alembic)

Migrations land in numbered order. The current latest must be confirmed at the start of Phase 1 — every subsequent migration number is `latest + N`.

| Migration | Phase | Contents |
|-----------|-------|----------|
| `latest + 1` | 1 | `brokers` table, `entities.broker_id` column, roles enum values |
| `latest + 2` | 2 | `cohort_membership` table, `quotes.percentile_rank` + `quotes.cohort_id` + `quotes.cohort_size` columns |
| `latest + 3` | 5 | `referral_messages` table, `referrals.awaiting_party` column |

Phases 3, 4, 6, 7, 8 add no migrations.

### `layers/risk/workflow.py`

1. **Phase 2**: Add `compute_cohort_percentile()` step **after** scoring is complete and **before** the final response is returned. Populates `quote.percentile_rank` and `quote.cohort_id`.
2. **Phase 3**: Add `compute_impact_breakdown()` step **after** pricing is complete (modifier-before/after data is available). Populates `quote.signal_impact` (in-memory; not persisted in v8 — recomputable from existing data).

Both touches are pure extensions — add a step at a defined point in the workflow, do not reorder existing steps.

### `coverages/master_config_layout.yaml`

1. **Phase 4**: Bump version to **2.5** (assumes v7 Phase 1 ships first and lands 2.4; if v7 Phase 1 has not shipped, bump to 2.4 instead). Add the `signal_remediation` schema block.

Single touch.

### `coverages/*/config.yaml` (all 7 coverages: cyber, casualty, fi, energy, pvt, captive, event, reinsurance)

1. **Phase 4**: Add a `signal_remediation` block per signal that warrants remediation guidance. Permissive default: signals without an entry get an inferred generic remediation hint at runtime; no per-config breakage.

Single touch.

### `infrastructure/api/main.py`

1. **Phase 5**: Mount referral messages router (`/api/v1/referrals/{id}/messages`).
2. **Phase 6**: Mount portal router (`/api/v1/portal/*`).

Two additive touches. Routers are independent — order between Phase 5 and Phase 6 mounts does not matter, but **both must come after every other middleware that exists today**.

### `seed/` package

1. **Phase 7**: Single comprehensive pass — Marsh broker tenant, demo client tenants, cohort bulk-up to ≥50 per (coverage × revenue band) cohort for cyber, pre-staged mid-renewal submission, pre-staged referral query. Adds `seed/demo_reset.py` and a `python -m seed demo-reset` command.

Single touch. Backend phases 1–6 must work against the **existing** seed; Phase 7 enriches it without changing any backend code.

### `frontend/` (entire tree)

1. **Phase 8**: Single cohesive pass. Adds `frontend/src/app/(portal)/` route group, broker and client views for the five portal pages, role-aware login routing, carrier-side affordances for raising queries on referrals.

Single touch. No backend phase modifies any file under `frontend/` except `frontend/src/types/auth.ts` (Phase 1 extends the role enum on the type side — this is a single line, treated as a type-system necessity, not frontend work proper).

---

## What Each Phase Does NOT Do

| Phase | Does NOT |
|-------|----------|
| 1 | Does not add API endpoints. Does not modify workflow. Does not touch seed. Does not touch frontend (except `auth.ts` role enum). |
| 2 | Does not expose endpoints (Phase 6 mounts). Does not modify pricer or scorer logic — only adds a post-scoring percentile step in workflow. Does not modify seed. |
| 3 | Does not persist data — impact breakdown is recomputed from existing modifier tracking on each request. Does not modify pricer logic. Does not expose endpoints (Phase 6). Does not modify seed. |
| 4 | Does not change scoring or pricing — remediation is informational only. Does not expose endpoints (Phase 6). Does not modify seed. |
| 5 | Does not modify scoring or pricing logic — broker reply triggers a **re-assessment** by re-invoking the existing workflow, not a new pricing path. Does not modify seed. |
| 6 | Adds no new business logic. Pure API plumbing + role guards. Does not modify seed. |
| 7 | Modifies `seed/` only. No logic changes anywhere else. Does not touch frontend. |
| 8 | Single touch on frontend. Does not modify backend logic, endpoints, or schemas. If backend gaps surface during 8, they are tracked as v8.1 — do not patch in Phase 8. |

---

## Acceptance Gates Between Phases

A phase is "done" when:

1. All success criteria in its phase doc are met.
2. `pytest tests/ -v` passes on the v8 branch.
3. Any new migration applies and rolls back cleanly.
4. `python coverages/doc_generator.py` runs without error (relevant for Phase 4).
5. The "What this phase does NOT do" list has been honoured (no scope leakage into other files).
6. A single commit (or small commit series) on `claude/client-portal-v8-G2V8I` containing the phase's work.

The next phase starts only after the prior phase's gate is met.

---

## Demo Storyboard (Phase 7 + 8 Output)

The demo runs against the seed state produced by `python -m seed demo-reset`. Seven acts, three personas, deterministic.

| Act | Persona | Surface | What happens |
|-----|---------|---------|--------------|
| 1 | Client | Portal `/portal` + `/portal/score` + `/portal/peers` | Logs in. Sees score (~685), peer cohort average (~720), bottom drivers (MFA absent, no security training, weak DR) with $ impact each. |
| 2 | Client | Portal `/portal/submissions` | Clicks "Request renewal". Submission created. |
| 3 | Underwriter | Carrier UI referral queue | Submission appears at REFER tier with "MFA absent" flagged. |
| 4 | Underwriter | Carrier UI referral detail | Raises query: "Confirm MFA status." |
| 5 | Broker (Marsh) | Portal `/portal/queries` inbox | Query appears. Marsh replies with evidence: "MFA deployed Q1." |
| 6 | System + Underwriter | Carrier UI | Re-assessment triggers. Score 685 → 745. Tier moves to AUTO-APPROVE. Premium drops ~12%. Underwriter binds. |
| 7 | Client | Portal `/portal/submissions/{id}` | Sees the new premium with delta narrative: "Marsh saved you $X by submitting MFA evidence. Next priority: security training." |

The reset command returns state to Act 1 in <5 seconds.

---

## Risk Register (Cross-Phase)

| Risk | Phase exposed | Mitigation |
|------|---------------|------------|
| Phase 2 cohort percentiles uninformative due to thin data | 2 | Phase 7 bulks cohort to ≥50 per (cyber × revenue band); Phase 2 tests against bulked seed. |
| Phase 5 re-assessment loop expensive on large entities | 5 | Re-use existing workflow; no new heavy compute. Phase 5 tests time bound on re-assessment. |
| Phase 4 YAML changes break existing config validation | 4 | Permissive defaults — signals without remediation block get a generic runtime hint. No required field added. |
| Phase 8 surfaces backend gaps mid-build | 8 | All backend phases ship their own integration tests with the exact contract Phase 8 will call. Gaps caught at Phase 6 acceptance. |
| Demo seed drifts from production behaviour | 7 | Phase 7 reset script must use only public API endpoints — no DB shortcuts. If a state can't be produced via API, that's a Phase 5/6 gap, not a Phase 7 hack. |
| v7 Phase 1 (Evidence Grade) ships mid-v8 and creates merge conflicts | All | Phase docs flag every file touched. Evidence Grade lives in `signal_architecture/signals/types.py` and YAML — v8 touches neither in conflicting ways. Merge cleanly. |

---

## Critical Path

```
P1 (1w) → P2 (1w) → P3 (0.5w) → P4 (1w) → P5 (1w) → P6 (0.5w) → P7 (1w) → P8 (2-3w)
```

Approximately **8–9 weeks** to demo-ready end-to-end. Faster if Phases 2–5 run in parallel (~6–7 weeks).

---

## Reference: Inputs to This Plan

- **Recon notes**: v7 codebase survey (May 2026) — Next.js 14 App Router frontend, three-layer scoring (`layers/risk/`, `layers/loss/`, `layers/exposure/`), referral state machine in `infrastructure/api/routes/referrals.py`, seed CLI at `seed/__main__.py`.
- **Phase A modifier tracking** (v0.4.0) — already in place via `layers/risk/pricer.py`. Phase 3 of v8 consumes this directly.
- **Existing referral states** — `PENDING`, `IN_REVIEW`, `APPROVED`, `DECLINED`, `MODIFIED`. Phase 5 adds `AWAITING_BROKER`.
- **Existing roles** — `ADMIN`, `ACTUARIAL`, `SENIOR_UNDERWRITER`, `UNDERWRITER`, `READ_ONLY`. Phase 1 adds `BROKER`, `CLIENT`.
- **Master config layout version** — currently 2.3. v7 Phase 1 bumps to 2.4. v8 Phase 4 bumps to 2.5 (or 2.4 if v7 Phase 1 has not shipped).

---

## Branch & Commit Discipline

- All work on `claude/client-portal-v8-G2V8I`.
- One commit per phase minimum, no more than ~5 commits per phase. Commit message format: `v8 phase N: <short summary>`.
- Do not merge to `main` until Phase 8 acceptance gate is met.
- Do not create a PR until explicitly requested.

# Version 8 Phase 7: Demo Seed & Reset

## Overview

Single comprehensive pass on the `seed/` package to produce **deterministic demo state**: Marsh as a broker, three diverse client tenants linked to Marsh, cohort bulk-up to ≥50 entities per (cyber × revenue band) cohort, a mid-renewal cyber submission pre-staged at the right tier for Act 3, and an open underwriter query pre-staged for Act 4.

Adds `python -m seed demo-reset` — a single command that returns state to **Act 1** in <5 seconds.

This is the final backend phase before frontend integration. Phase 8 (frontend) consumes this state.

## Rationale

The demo must be repeatable and fast. A live click-through demo (the planning decision) requires:

- The state at any point in the seven acts to be reachable deterministically.
- No mid-demo "let me refresh" or "let me re-seed" delays.
- Realistic-enough peer cohorts that percentiles are non-trivial.
- No data shortcuts that bypass production code paths — if the demo can't reach the state via API calls, that's a bug in Phases 1–6, not a seed hack.

Per the master sequence principle: **the seed script is touched once, at the end of backend work**. Phases 1–6 must function against the existing seed; Phase 7 enriches.

## Decisions (locked, do not relitigate)

| Decision | Choice | Implication |
|-|-|-|
| Demo tenants | Marsh (broker) + three client tenants (Acme Industries, Northwind Health, Pioneer Manufacturing) | Diverse NAICS for cohort variety: 51 Information, 62 Healthcare, 31-33 Manufacturing |
| Demo coverage | Cyber only | Phase 4 only authored complete remediation for cyber; demo doesn't touch other coverages |
| Cohort bulk | ≥50 entities per (cyber × NAICS_section × revenue_band) cohort for the three demo bands | Realistic percentiles |
| Demo reset implementation | Truncate + reseed using existing seed building blocks | No DB shortcuts; everything via the seed API |
| Demo state target | "Act 1" — client logs in, sees their initial score and peer comparison | The narrative starts here |
| Act 3+ state | Reachable by API calls (initiate submission, raise query). The seed sets Act 1; user actions drive forward. | Live click-through |
| User credentials | Demo users with well-known passwords (configurable via env var `DSI_DEMO_PASSWORD`) | Predictable login |
| Reset speed | <5 seconds wall clock | Live demo gates this |
| Determinism | Same seed inputs → same DB state (entity IDs, quote scores) | Use a fixed RNG seed |
| Smoke test | Phase 7 ships a smoke test that walks all seven acts via API | Validates entire backend is demo-ready |

## Current State

- `seed/` package with `bench.py`, `v5.py`, `synthetic.py`, `__main__.py` (per recon).
- `python -m seed init --tenant dsi-demo --entities 1000` already exists.
- No broker seeding (Phase 1 added the table; no seed function uses it yet).
- Synthetic seed produces varied entities but probably thin per-cohort.
- No "demo reset" concept.

## Target State

### Demo state composition

```
Tenant: marsh-demo (broker-side)
  Brokers:
    Marsh (slug: marsh)
  Users:
    marsh.admin@demo.dsi  (role: BROKER)

Tenant: acme-demo (client-side)
  Entity: Acme Industries
    naics_code: 5112 (parent section: 51 Information)
    annual_revenue: 180M (band: 50-250M)
    broker_id: <Marsh>
  Users:
    client.acme@demo.dsi  (role: CLIENT)

Tenant: northwind-demo
  Entity: Northwind Health
    naics_code: 6221 (parent section: 62)
    annual_revenue: 95M (band: 50-250M)
    broker_id: <Marsh>
  Users:
    client.northwind@demo.dsi  (role: CLIENT)

Tenant: pioneer-demo
  Entity: Pioneer Manufacturing
    naics_code: 3261 (parent section: 31)
    annual_revenue: 320M (band: 250M-1B)
    broker_id: <Marsh>
  Users:
    client.pioneer@demo.dsi  (role: CLIENT)

Tenant: carrier-demo
  Users:
    underwriter.demo@demo.dsi  (role: UNDERWRITER)
    senior.demo@demo.dsi       (role: SENIOR_UNDERWRITER)
```

Passwords for all demo users = `os.environ["DSI_DEMO_PASSWORD"]` (default `demo-pass-2026` for local dev).

### Cohort bulk-up

For the demo to show meaningful peer comparison, each cohort the three demo clients fall into needs ≥50 members:

- `cyber:51:50-250M` (Acme's cohort) — bulk to 60+ entities
- `cyber:62:50-250M` (Northwind's cohort) — bulk to 60+ entities
- `cyber:31:250M-1B` (Pioneer's cohort) — bulk to 60+ entities

The cohort members are seeded into a fourth-party tenant (e.g. `dsi-cohort-pool`) — they exist purely as peer-comparison fodder, not as demo personas. Their signals are varied so the cohort distribution spans a realistic spread.

**Score distribution per cohort**: roughly N(720, 50) — mean 720, stddev 50. Acme is hand-positioned at ~685 (below mean by ~0.7 stddev → ~25th percentile-ish, room to improve via Act 5's MFA reply).

### Pre-staged Act 3 state for Acme

The seed places Acme at:

- Latest cyber quote: composite score ~685, tier 4 (REFER), premium ~$165k.
- Open referral in `IN_REVIEW` state.
- Underwriter has raised a query: "Please confirm MFA status across admin accounts." (`request_signal_evidence: "mfa_enabled"`).
- Referral state: `AWAITING_BROKER`.

This is the state Marsh sees when logging in for Act 4 → 5. Northwind and Pioneer are at clean states (no open queries, normal recent quotes) so the demo can show "book of clients" with one item flagged.

### Reset script

`seed/demo_reset.py`:

```python
def reset_demo_state(session: Session, *, password: str) -> None:
    """
    Return the demo to Act 1 in <5 seconds.

    Steps:
    1. Delete all demo tenants (marsh-demo, acme-demo, northwind-demo, pioneer-demo, carrier-demo).
    2. Delete cohort pool tenant.
    3. Reseed tenants, users, brokers.
    4. Seed cohort pool entities (180 entities across 3 cohorts).
    5. Run assessment on the three demo client entities — this triggers Phase 2 (cohort percentile),
       Phase 3 (impact breakdown), and writes quotes.
    6. For Acme: raise the underwriter query via the Phase 5 API path. This puts the referral in AWAITING_BROKER.

    Determinism: uses fixed RNG seed (DSI_DEMO_RNG_SEED env var, default 42).
    """
```

CLI binding:

```python
# seed/__main__.py — add subcommand

if cmd == "demo-reset":
    reset_demo_state(session, password=os.environ.get("DSI_DEMO_PASSWORD", "demo-pass-2026"))
```

Invocation: `python -m seed demo-reset`.

**No DB shortcuts.** The reset uses public API calls (or the same internal service functions the API uses) to produce state. If a state can't be reached without manual SQL, that's a backend gap — escalate, do not hack the seed.

### Cohort pool seeding

Implementation note: use `seed/synthetic.py`'s generator for the 180 cohort-pool entities, but with constraints:

- Force NAICS code by cohort target (sample 60 cyber entities at NAICS 51, 60 at 62, 60 at 31/33).
- Force revenue into the target band (uniform within band).
- Vary signals to produce a realistic score distribution.
- Run assessment on each → populates `cohort_membership`.

The pool tenant `dsi-cohort-pool` is excluded from all portal queries — it's invisible to portal users. Add a `tenant.flags` field if it doesn't exist (or use tenant slug filter) — confirm during implementation.

If adding a tenant flag, that's a small Phase 1 followup; otherwise filter by slug pattern.

### Demo password env var

Document in `.env.example`:

```
DSI_DEMO_PASSWORD=demo-pass-2026
DSI_DEMO_RNG_SEED=42
```

### Smoke test

`tests/integration/test_demo_seven_acts.py`:

End-to-end script that:

1. Runs `reset_demo_state`.
2. **Act 1**: Log in as `client.acme@demo.dsi`. GET `/portal/overview`. Assert active cyber coverage at score ~685, tier 4. GET `/portal/entities/{acme}/peers`. Assert cohort_size ≥ 50, percentile_rank < 50 (Acme is below cohort mean).
3. **Act 2**: POST `/portal/entities/{acme}/submissions` with coverage_line=cyber. Assert submission created.
4. **Act 3**: Log in as `underwriter.demo@demo.dsi`. GET `/api/v1/referrals?state=AWAITING_BROKER`. Assert the Acme referral is in the queue.
5. **Act 4**: POST `/api/v1/referrals/{acme_referral}/messages` with query body and `request_signal_evidence=mfa_enabled`. Assert state stays `AWAITING_BROKER` (already there from seed; a second query is allowed but only one is "open" at a time — confirm Phase 5 semantics).
6. **Act 5**: Log in as `marsh.admin@demo.dsi`. GET `/portal/queries`. Assert Acme's open query appears. POST `/portal/queries/{acme_referral}/reply` with `signal_value_update: {signal_id: "mfa_enabled", new_value: true}`. Assert response: `triggered_reassessment=True`, `new_quote_id` populated.
7. **Act 6**: Re-fetch Acme's quote. Assert new composite_score > 685, new tier ≤ 3, premium dropped.
8. **Act 7**: Log in as `client.acme@demo.dsi`. GET `/portal/entities/{acme}/submissions`. Assert the submission shows the new quote with the improved premium. Assert delta narrative information is available (i.e. the new quote's impact_breakdown shows mfa_enabled as no longer a drag).

If any step fails, the demo doesn't work. This test is the **demo readiness gate**.

## Implementation Plan

### Step 1: Discovery

Confirm:
1. Existing `seed/__main__.py` CLI structure.
2. Existing `seed/synthetic.py` generator signature.
3. Whether `Tenant` has a flag or category field; if not, use slug pattern for cohort-pool filtering.
4. Whether the existing `seed init` accepts a tenant slug param; reuse if so.
5. How users are seeded today (likely a helper in `seed/`); confirm hashing approach for password.

### Step 2: Add broker seeding

Add a `seed_brokers(session, tenant_id, brokers: list[dict])` helper in `seed/` (or extend an existing one). Used by demo_reset to insert Marsh.

### Step 3: Demo tenant + entity seeding

Helper to seed the demo tenants, users, entities. Hardcode the four entity profiles (Acme, Northwind, Pioneer + Marsh broker). Set NAICS, revenue, broker_id.

### Step 4: Cohort pool seeding

Helper to generate the 180 cohort-pool entities into `dsi-cohort-pool` tenant, distributed across the three target cohorts.

### Step 5: Assessment loop

After seeding entities, run the standard assessment workflow on each one. This is the **only** way to populate scores, cohort memberships, impact breakdowns, etc. — no shortcut. Reuse the workflow; do not bypass it.

### Step 6: Pre-stage Acme's referral query

After Acme's assessment completes and a referral exists, invoke the Phase 5 endpoint (or its underlying service function) to raise the MFA query. This puts the referral in `AWAITING_BROKER`.

### Step 7: Bind reset CLI

Wire `python -m seed demo-reset` to the reset function.

### Step 8: Smoke test

Implement `tests/integration/test_demo_seven_acts.py` per the **Smoke test** spec.

### Step 9: Time the reset

`python -m seed demo-reset` should complete in <5 seconds on a developer laptop. If it doesn't, optimise the assessment loop (parallelise the 180-entity cohort pool seed) — but **do not skip steps**.

### Step 10: Update `.env.example`

Add `DSI_DEMO_PASSWORD` and `DSI_DEMO_RNG_SEED` with defaults.

## Constraints & Principles

1. **No DB shortcuts.** Everything via the workflow and Phase 5 API path. Production code is exercised.
2. **Deterministic.** Same RNG seed → identical IDs, scores, percentiles. The smoke test depends on this.
3. **Idempotent.** Running `demo-reset` twice produces the same state. Truncates first.
4. **Fast.** <5 seconds for the live demo.
5. **Realistic data.** Names, NAICS codes, revenue bands all plausible. No "Test User 123" or `revenue: 1`.
6. **Cohort pool invisible.** Portal queries never surface cohort-pool entities or users.
7. **Self-validating.** Smoke test runs the seven acts; if it passes, demo works.
8. **No code outside `seed/`.** Phase 7 modifies the seed package only.

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Reset takes >5 seconds | Parallelise 180-entity cohort pool assessment. If still slow, profile the workflow — don't skip steps. |
| Smoke test flaky due to non-determinism | Pin RNG seed via env var. Tests should be deterministic. |
| Cohort pool leaks into portal queries | Tenant filter in `scoped_entity` dependency (Phase 6) excludes cohort-pool tenant. Confirm — if not in Phase 6, add a slug-based filter here as a seed-side guard. |
| Production code path needed for state can't be reached via API | Escalate as a backend gap — Phases 1–6 should be complete enough. Do not hack. |
| Demo password is in plaintext in code | Read from env. Default is for local dev only. README documents production should override. |
| Postgres truncate slow on a large DB | Cohort pool is the largest data — 180 entities + assessments. Truncate cascades cleanly via the existing alembic schema. |
| Marsh has no user yet when reset starts (chicken/egg) | Reset order: tenants → brokers → users → entities → assessments → query. Bootstrap is in `demo_reset.py`. |

## Dependencies

- **Phases 1–6 complete.** Phase 7 exercises the full backend stack.
- Existing seed infrastructure (`seed/__main__.py`, `seed/synthetic.py`).

## Success Criteria

1. `python -m seed demo-reset` runs in <5 seconds.
2. After reset:
   - Marsh broker exists in `marsh-demo` tenant.
   - Three client tenants exist with one entity each, all linked to Marsh.
   - Cohort pool tenant exists with 180 entities distributed across three target cohorts.
   - Each demo client entity has a current cyber quote with populated cohort percentile and impact breakdown.
   - Acme's quote is in REFER tier (~685, tier 4), with an open `AWAITING_BROKER` referral and underwriter MFA query.
   - Northwind and Pioneer have clean recent quotes, no open queries.
3. Demo users can log in with `DSI_DEMO_PASSWORD`.
4. Smoke test `tests/integration/test_demo_seven_acts.py` passes all seven acts.
5. Reset is idempotent — running it twice produces identical state.
6. Cohort pool tenant invisible to portal queries.
7. `.env.example` documents `DSI_DEMO_PASSWORD` and `DSI_DEMO_RNG_SEED`.
8. Full `pytest tests/ -v` green.
9. No code changes outside `seed/` package.

## Out of Scope (Phase 7)

- Multi-coverage demo seeds — cyber only for v8.
- Production-grade tenant onboarding — demo-only.
- Email/SMTP setup for "real" notifications — out of v8 scope.
- Admin UI for seeding from the browser — CLI only.
- Performance benchmarks beyond the 5-second reset gate — v8.1+ if needed.
- Persistent demo (between container restarts) — reset is fast enough that demo is re-run as needed.

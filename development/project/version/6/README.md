# DSI Version 6 — Maturation, Expansion, Deployment

| Item | Value |
|------|-------|
| Version | 1.0 |
| Date | April 2026 |
| Classification | Master Plan Index |
| Status | Planned |

---

## Purpose

Version 6 takes DSI from "framework with mature flagship coverages" to "framework where every coverage is mature, every major line is represented, deployment is production-grade, and every viable signal source is wired." Stubs are acknowledged as a separate, ongoing workstream and are out of scope here — the goal is to make everything around the signal substrate production-complete so that replacing stubs becomes a mechanical swap.

## Definition of Done

1. **Every existing coverage is Mature.** ≥6 sub-configs, ≥22 unique signal IDs, ≥60 coverage-specific inference functions, ≥40 signals in the primary config, `expectation_level` on every scored signal, multiplexer `routing_constraints` on every non-general sub-config, parametric ILF curves per `product_type`, guardrails populated, `logic.md` regenerated, regression harness green.
2. **Twelve new coverages shipped** at the same Mature bar, each with its own expansion spec under `development/project/version/6/coverage_specs/`.
3. **CI deploys to real staging and production clusters** via canary rollout with automated rollback, secrets sourced from External Secrets Operator, observability wired via OpenTelemetry.
4. **Seed is a single `python -m seed` CLI** — `seed_dsi_bench.py`, `seed_v5.py`, `synthetic_generator.py` removed from repo root.
5. **Every suggested signal source is implemented** as a `ProductionExtractor` subclass with cost tier, cached TTL, kill-switch env var, and free/cached fallback. Paid sources are behind env-var gates so the framework runs without them.
6. **Regulatory artefact kit** (Lloyd's MU&G, NAIC MRM, FCA FG21/3, GDPR DPIA, EU AI Act classification, SERFF rate-filing template) drafted under `docs/regulatory/`.
7. **Golden-entity regression suite** (10 real public entities per coverage, 22 coverages × 10 = 220 entities) enforced in CI.
8. **Evidence dashboard** publishing per-config real-signal-%, last-calibration time, last-drift-alert time, last-golden-check time.

## Workstreams

| Letter | Name | Phases | Owner Doc |
|--------|------|--------|-----------|
| **A** | Coverage Maturation | A1–A8 (raise all existing coverages to Mature) | `workstream_phases/A_Coverage_Maturation.md` |
| **B** | New Coverages | B1–B12 (twelve new coverages in three waves) | `workstream_phases/B_New_Coverages.md` |
| **C** | Deployment Readiness | C1–C7 (CI, secrets, observability, seed consolidation, load/chaos, regulatory, config gate) | `workstream_phases/C_Deployment_Readiness.md` |
| **D** | Signal Source Integration | D1–D8 (all suggested free + paid sources) | `workstream_phases/D_Signal_Sources.md` |
| **E** | Cross-Cutting | E1–E10 (rust core, provenance, confidence calibration, tenant overlays, golden entities, drift-to-referral, rate-filing kit, evidence dashboard, taxonomy unification, stub retirement) | `workstream_phases/E_Cross_Cutting.md` |

## Sequencing Rules (carried from V5)

1. **Backend before frontend.** Frontend integration is the final pass, not per-phase work.
2. **Schema before logic.** All migrations in each workstream land first.
3. **No file touched twice.** The master sequence is the arbitrator — if two phases both modify the same file, they are explicitly ordered.
4. **Seed is a final phase.** Individual phases do not modify `seed/` — C4 is the single consolidated seed phase.
5. **Config gate blocks PR merges.** E2 (config health gate) lands early; subsequent coverage work must pass it.

## Relationship to prior versions

- **Version 3 (V3, Phases A–E)**: established transparency, ROL engine, tower/subscription.
- **Version 4 (Phases 1–13)**: delivered multiplexer, coverage expansion pipeline, Cyber/PI depth.
- **Version 5 (Phases 1–8 + WE + ABC)**: added Property/Casualty/FPR coverage, expanded Marine/Aero/D&O/FI, introduced World Engine, auth, audit, config versioning, loss ingestion, recalibration.
- **Version 6 (this plan)**: closes every remaining gap against the whitepaper + vision paper, making DSI commercially bindable (subject to stub replacement, which is the parallel workstream tracked in `development/extractor_implementation_plan.md`).

## Documents in this tree

- `README.md` — this file.
- `V6_Master_Sequence.md` — ordered build plan across workstreams.
- `workstream_phases/A_Coverage_Maturation.md` — A1–A8.
- `workstream_phases/B_New_Coverages.md` — B1–B12.
- `workstream_phases/C_Deployment_Readiness.md` — C1–C7.
- `workstream_phases/D_Signal_Sources.md` — D1–D8.
- `workstream_phases/E_Cross_Cutting.md` — E1–E10.
- `coverage_specs/` — one expansion-spec YAML per new coverage (populated during Workstream B execution).

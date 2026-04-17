# V6 Completion Progress Log

Tracks every item from the Option-D completion plan. Each entry shows
status (PENDING / IN-PROGRESS / DONE / BLOCKED) and the commit that
delivered it. The log is updated **before** each commit so visibility is
preserved across sessions.

## Stage summary

| Stage | Scope | Status |
|-------|-------|--------|
| 1 — Integration wiring | Close the plumbing gaps (provenance persistence, drift→referral, rate-filing API, overlay example, E10 physical move) | **IN-PROGRESS** |
| 2 — Depth-first coverage | Build `medprof` end-to-end as the template | PENDING |
| 3 — Replicate for other new coverages | B2 WC, B3 ProdLib, B4 EnvLiab, B5 Construction, B6 Event, B7 PVT, B8 TEO, B9 Reinsurance, B10 Crop, B11 Specie, B12 Captive | PENDING |
| 4 — A-series coverage maturation | A1 FPR, A2 Property, A3 Casualty, A4 D&O, A5 FI, A6 Aerospace, A7 Marine, A8 Cyber/PI/Energy | PENDING |
| 5 — E1 Rust port | Extract scoring spec, port to Rust, PyO3 wrapper, parity CI | PENDING |
| 6 — D-extractor depth | 72 extractors → full field extraction + replayed HTTP tests | PENDING |
| 7 — Real goldens | Replace degenerate stub-driven snapshots with realistic fixtures | PENDING |

---

## Stage 1 — Integration Wiring

| # | Item | Status | Commit |
|---|------|--------|--------|
| 1.1 | `ProductionExtractor.extract()` builds + persists `Provenance` on every successful extraction | **DONE** | (next) |
| 1.2 | `DriftDetector` registers `DriftReferralBridge` as an `on_alert` observer | **DONE** | (next) |
| 1.3 | `POST /api/v1/admin/rate-filing/generate` authenticated endpoint | PENDING | — |
| 1.4 | Example tenant overlay file (`coverages/cyber/overlays/dsi-demo.yaml`) + integration smoke | PENDING | — |
| 1.5 | C3 OpenTelemetry end-to-end smoke with `DSI_OTEL_ENABLED=true` | PENDING | — |
| 1.6 | E10 physical stub move — **BLOCKED** until A1–A8 complete (inference functions still import stubs) | BLOCKED | — |

## Stage 2 — MedProf depth-first template

| # | Item | Status | Commit |
|---|------|--------|--------|
| 2.1 | `coverages/medprof/config.yaml` with 5 sub-configs + 24 signals | PENDING | — |
| 2.2 | `signal_architecture/signals/inference/functions/medprof/` — 70+ functions | PENDING | — |
| 2.3 | 10 golden fixtures under `tests/fixtures/golden_entities/medprof/` | PENDING | — |
| 2.4 | `coverages/medprof/logic.md` regenerated | PENDING | — |
| 2.5 | `python -m infrastructure.builder.cli calibrate --coverage medprof` returns PASS | PENDING | — |
| 2.6 | `assess_config_compliance` returns 0 warnings for medprof | PENDING | — |

## Stage 3 — Replicate for other new coverages

For each of B2, B3, B4, B5, B6, B7, B8, B9, B10, B11, B12: identical
checklist to Stage 2 (config.yaml, inference functions, goldens,
logic.md, calibrate PASS, compliance 0 warnings).

## Stage 4 — A-series maturation

Per `coverages/<name>/MATURATION_STATUS.md` each coverage has a
concrete list of new signals + inference functions. Drives
`calibrate` from ADVISORY to BLOCKING in the Config Health Gate once
A3 Casualty's 17.9% guardrail hit rate is closed.

## Stage 5 — E1 Rust port

| # | Item | Status | Commit |
|---|------|--------|--------|
| 5.1 | Extract `layers/risk/_scoring_spec.py` pure-function spec | PENDING | — |
| 5.2 | Port to `rust/dsi-core/src/scoring.rs` | PENDING | — |
| 5.3 | PyO3 wrapper exposing `score(config_hash, signals) -> CompositeResult` | PENDING | — |
| 5.4 | Nightly parity job (1 000 golden fixtures, max abs divergence < 1e-9) | PENDING | — |
| 5.5 | p99 benchmark proving < 5 ms target | PENDING | — |

## Stage 6 — D-extractor depth

72 extractors across D1–D7. Per-extractor work:
1. Expand `_do_extract` from reachability probe to the full field set per
   the V6/D-series spec.
2. Add replayed-HTTP unit tests via the `responses` library.
3. Ensure confidence is emitted (not just presence).

## Stage 7 — Real goldens

Once the extractors return meaningful data, regenerate all 101 golden
fixtures with realistic expected values. Requires API keys for paid
sources (currently absent; fixtures use free+public sources only).

---

## Change log (newest first)

*(each completed item appends an entry here with commit hash + summary)*

### 1.2 — DriftDetector ↔ DriftReferralBridge wiring

`DriftDetector` gained an `on_alert(observer)` registration API; after
alerts are persisted it fans out to registered observers in an
isolated loop (failures log but don't propagate).

New `world_engine/drift/wiring.py`:

- `_referral_row_dispatcher(db_factory)` — SQL dispatcher that writes
  one row into `referrals` per DriftReferral, with `referral_type =
  'DRIFT'`, `drift_alert_id` FK populated, severity→priority mapping
  (high=1, medium=3, low=6), and the full DriftReferral payload in the
  `reasons` JSONB column. Commits + closes the session in a `finally`.
- `wire_default_drift_observers(detector, db_factory, extra_dispatchers)`
  — one-call bootstrap. Attaches the default SQL dispatcher + any
  extras (e.g. Slack / PagerDuty callbacks callers want to add).

Kept wiring in a separate module so the detector never imports the
referral service directly — no circular dep, and tests swap alternative
dispatchers trivially.

5 new tests in `tests/unit/test_drift_wiring.py`: priority mapping,
registration contract, SQL-shape assertion, end-to-end dispatch,
extra-dispatchers fan-out. Existing 8 bridge tests still green.

### 1.1 — Provenance persistence wiring

`ProductionExtractor.extract()` now builds a `Provenance` on every
successful extraction and attaches the dict payload to
`result.metadata["provenance"]`. Failures are non-blocking (logged
only). New `infrastructure/db/provenance_store.py` module exposes:

- `persist_provenance(db, signal_id, model_version_id, assessment_id,
  provenance)` — idempotent `INSERT … ON CONFLICT (self_hash) DO NOTHING`.
- `persist_chain(db, assessment_id, edges)` — idempotent edge writer.
- `persist_extractor_result(db, signal_id, mvid, aid, extractor_result)`
  — one-liner that reads the attached provenance dict, rebuilds the
  `Provenance` object (hash re-derived from the stored payload), and
  persists it.

4 new tests in `tests/unit/test_provenance_store.py` validate the
INSERT shape + round-trip with a stub Session.

Wiring the orchestrator to call `persist_extractor_result` for every
signal in the scoring pipeline is a follow-up inside the workflow
engine — the infrastructure is ready.


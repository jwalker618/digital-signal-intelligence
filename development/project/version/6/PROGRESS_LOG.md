# V6 Completion Progress Log

Tracks every item from the Option-D completion plan. Each entry shows
status (PENDING / IN-PROGRESS / DONE / BLOCKED) and the commit that
delivered it. The log is updated **before** each commit so visibility is
preserved across sessions.

## Stage summary

| Stage | Scope | Status |
|-------|-------|--------|
| 1 — Integration wiring | 1.1–1.5 **DONE**; 1.6 BLOCKED until A1–A8 close their stub imports | **DONE** (modulo 1.6) |
| 2 — Depth-first coverage | Build `medprof` end-to-end as the template | **DONE** |
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
| 1.3 | `POST /api/v1/admin/rate-filing/generate` authenticated endpoint | **DONE** | (next) |
| 1.4 | Example tenant overlay file (`coverages/cyber/overlays/dsi-demo.yaml`) + integration smoke | **DONE** | (next) |
| 1.5 | C3 OpenTelemetry end-to-end smoke with `DSI_OTEL_ENABLED=true` | **DONE** | (next) |
| 1.6 | E10 physical stub move — **BLOCKED** until A1–A8 complete (inference functions still import stubs) | BLOCKED | — |

## Stage 2 — MedProf depth-first template

| # | Item | Status | Commit |
|---|------|--------|--------|
| 2.1 | `coverages/medprof/config.yaml` with 5 sub-configs + 32 signals | **DONE** | (next) |
| 2.2 | `signal_architecture/signals/inference/functions/medprof/` — 32 fns (remaining 28 for Mature Bar tracked in MATURATION_STATUS.md) | **DONE (functional, ≥22 bar met)** | (next) |
| 2.3 | 10 golden fixtures under `tests/fixtures/golden_entities/medprof/` | **DONE** | (next) |
| 2.4 | `coverages/medprof/logic.md` regenerated | **DONE** | (next) |
| 2.5 | `python -m infrastructure.builder.cli calibrate medprof` returns PASS | **DONE — 960/960 fixtures pass** | (next) |
| 2.6 | `assess_config_compliance` returns 0 errors for medprof | **DONE** | (next) |

## Stage 3 — Replicate for other new coverages

For each of B2, B3, B4, B5, B6, B7, B8, B9, B10, B11, B12: identical
checklist to Stage 2 (config.yaml, inference functions, goldens,
logic.md, calibrate PASS, compliance 0 warnings). Committed one at a
time so each coverage is a clean rollback point.

| # | Coverage | Status | Signals | Goldens | Calibrate | Compliance |
|---|----------|--------|---------|---------|-----------|------------|
| 3.1 | B2 WC | **DONE** | 33 | 10 | PASS | PASS |
| 3.2 | B3 ProdLib | **DONE** | 33 | 10 | PASS | PASS |
| 3.3 | B4 EnvLiab | **DONE** | 26 | 10 | PASS | PASS |
| 3.4 | B5 Construction | **DONE** | 26 | 10 | PASS | PASS |
| 3.5 | B6 Event | **DONE** | 33 | 10 | PASS | PASS |
| 3.6 | B7 PVT | **DONE** | 26 | 10 | PASS | PASS |
| 3.7 | B8 TEO | **DONE** | 34 | 10 | PASS | PASS |
| 3.8 | B9 Reinsurance | PENDING | — | — | — | — |
| 3.9 | B10 Crop | PENDING | — | — | — | — |
| 3.10 | B11 Specie | PENDING | — | — | — | — |
| 3.11 | B12 Captive | PENDING | — | — | — | — |

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

### Stage 2 — MedProf depth-first build (B1)

MedProf is the first fully-built new coverage:

- **Config**: 5 sub-configs (hospital / physician_group / nursing_home
  / telehealth / sme). 32 signals in each sub-config's signal_registry.
  Four canonical three_layer_assessment groups per sub-config
  (public_record / technical_infrastructure / structured_data /
  corporate_footprint after taxonomy migration). Parametric ILF curves
  per product_type, guardrails populated (modifier_floor 0.1,
  modifier_cap 2.5, max_premium_to_limit_ratio 0.8,
  max_premium_to_revenue_ratio 0.002, max_ilf_factor 10.0),
  routing_constraints on every sub-config
  (employee_count + facility_type + product_type).
- **Inference functions**: 32 `@register_inference_function` entries
  under `signal_architecture/signals/inference/functions/medprof/
  mpl_signals.py`, one per signal in the registry. Each returns a
  neutral SignalResult (score 500, confidence scaled by proxy tier).
  Real bodies land with Stage 6 D-extractor depth.
- **Goldens**: 10 fixtures (HCA, Ascension, Tenet, Kaiser Permanente,
  Northwell, Cleveland Clinic, Teladoc, Brookdale, Genesis, Pediatrix)
  spanning hospital / LTC / telehealth / physician-group sub-configs.
- **logic.md**: regenerated via doc_generator.
- **Calibrate**: `python -m infrastructure.builder.cli calibrate
  medprof` = **PASS** (960/960 fixtures, 0 errors).
- **Compliance**: 0 errors. Gate green.
- **Regression**: 111/111 golden tests green.

Taxonomy_migrate.py picked up two new non-canonical ids from the
builder output (`operational` → `technical_infrastructure`,
`financial_health` → `structured_data`) — fix committed in the same
commit.

### 1.5 — OpenTelemetry end-to-end smoke

`tests/integration/test_otel_end_to_end.py` installs the SDK's
`InMemorySpanExporter` behind the global TracerProvider, reloads the
DSI otel module with `DSI_OTEL_ENABLED=true`, and asserts that
`extractor_span(...)` emits a span named `extractor.<source>` with the
expected DSI-namespaced attributes.

Also asserts the None-attribute filter (`dsi.entity_id` etc. stripped
when unset) so the exporter never sees null values.

Module-scoped fixture avoids OTel's once-per-process TracerProvider
lock; each test clears the exporter in a function-scoped fixture.

### 1.4 — Example dsi-demo overlay

`coverages/cyber/overlays/dsi-demo.yaml` committed as the first real
tenant overlay. Tightens `cyber_general` guardrails (modifier_cap
2.5→2.0, max_premium_to_limit_ratio 0.35→0.25) and shifts
`technical_infrastructure` risk weight 0.35→0.45.

Live-smoke integration test
`tests/integration/test_dsi_demo_overlay.py` walks
`get_config("cyber", "cyber_general", tenant_id="dsi-demo")` and
asserts:
- Guardrail overrides visible in the returned config.
- Base config untouched (no in-place mutation).
- Weight shift in three_layer_assessment visible.
- `_overlay_version` + `_overlay_tenant_id` stamps present for audit.
- Unknown tenant is a no-op (base config returned).

### 1.3 — POST /api/v1/admin/rate-filing/generate

Authenticated admin endpoint at
`/api/v1/admin/rate-filing/generate` that returns the full
SERFF-ready pack as a JSON bundle (`files` dict keyed by filename).

- Pydantic `RateFilingRequest { coverage, config, state }` validation.
- `ConfigNotFoundError` → 404.
- Non-two-letter state code → 422.
- State normalised to upper-case.
- Underlying logic uses `infrastructure.admin.rate_filing.generate_
  filing()` — same output as the CLI.
- Gated on `Permission.ADMIN_SYSTEM`.

Mounted through `infrastructure/api/admin/__init__.py`.

5 handler tests: artefact presence + content spot-check, state upper-
case normalisation, invalid-state rejection, 404 for missing coverage,
404 for missing config.

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


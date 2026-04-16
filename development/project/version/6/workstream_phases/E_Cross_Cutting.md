# Workstream E — Cross-Cutting

| Item | Value |
|------|-------|
| Version | 1.0 |
| Depends on | Spans the whole of V6 — individual phases have their own ordering (see V6_Master_Sequence.md) |
| Phases | E1–E10 |

---

## Overview

Ten cross-cutting items that don't belong to a single coverage or workstream but materially lift DSI from "framework" to "standard-grade platform." Each phase is independently deployable.

---

## E1 — Rust `dsi-core` Role Decision

**Decision required**: adopt or retire.

The CI pipeline currently builds `rust/dsi-core` via `cargo build --release --lib` and uploads artefacts, but there's no documented consumer. Two options — pick one and execute it. Ambient unused code is a liability.

### Option A — Adopt (recommended)

Move the scoring hot-path into Rust:
- Weighted aggregation (signal × weight → group composite).
- Tier resolution (banded threshold lookup).
- Deterministic modifier application.
- Loss/exposure composite calculation.

**Interface**: PyO3-exposed `score(config_hash: str, signals: Vec<SignalScore>) -> CompositeResult`.

**Expected win**: p99 scoring latency from ~40ms → <5ms, enabling much larger multiplex races without HPA pressure.

**Implementation**:
1. Extract pure scoring logic from `layers/risk/scorer.py` into a pure-function spec.
2. Port to Rust under `rust/dsi-core/src/scoring.rs`.
3. Add Python wrapper `signal_architecture/signals/rust_bindings.py`.
4. Keep the Python scorer as the reference implementation, used in tests as a ground truth.
5. Nightly parity check: run 1000 golden fixtures through both; fail CI on divergence >1e-9.

### Option B — Retire

Remove `rust/` and the `rust-build` CI job. Delete `libdsi_core.*` artefact upload. Update README to remove the Rust reference.

**Acceptance** (whichever chosen):
- Decision documented in `docs/overview/Rust_Core_Decision.md`.
- If adopted: parity suite green, p99 benchmark captured.
- If retired: CI clean, README updated.

---

## E2 — Signal-Lineage Chain-of-Custody

**File**: `signal_architecture/signals/types.py` — extend `ExtractorResult`.

```python
@dataclass
class Provenance:
    source_name: str
    source_url: str
    request_timestamp: datetime
    response_etag: Optional[str]
    response_hash: str              # sha256 of normalised response body
    response_status_code: int
    cache_hit: bool
    extractor_version: str
    chain_of_trust: List[str]       # list of parent_hash | self_hash

@dataclass
class ExtractorResult:
    ...existing fields...
    provenance: Provenance
```

**DB tables** (new alembic migration `021_signal_provenance.py`):
| Table | Columns |
|-------|---------|
| `signal_provenance` | `id`, `model_version_id` FK, `signal_id`, `provenance` (JSONB), `hash` (unique), `created_at` |
| `provenance_chain` | `parent_hash`, `child_hash`, `assessment_id` FK |

**API**: `/api/v1/quotes/{id}/provenance` returns the full chain for every signal that contributed to a quote.

**Audit value**: this is the artefact regulators and reinsurers will demand. Every premium traces back through a verifiable Merkle-style chain to the raw extracted response.

**Acceptance**:
- Every successful assessment writes ≥ N `signal_provenance` rows (N = signal count).
- The chain for a given quote is reproducible and verifiable (re-hash, match stored hash).
- API endpoint live and documented.

---

## E3 — Confidence Calibration Harness

**New file**: `infrastructure/validation/confidence_calibration.py`

Fits a reliability curve: **expected confidence** (model output) vs. **observed availability** (did the extraction actually succeed?) across the golden-entity corpus. Configs whose declared confidence systematically over- or under-states reality are flagged.

**Diagnostic output**:
- Per-signal reliability plot (PNG + JSON).
- Per-config brier score.
- Per-coverage expected calibration error (ECE).
- Flags: any signal with |ECE| > 0.1 triggers a `CONFIDENCE_MISCALIBRATED` referral.

**CI integration**: nightly job over the golden-entity corpus. Calibration report uploaded as an artefact. PR comment posted if a PR causes ECE to worsen by >0.02 on any coverage.

**Acceptance**:
- Reliability curves for all 22 coverages generated nightly.
- ECE < 0.1 on every coverage at V6 sign-off.
- `CONFIDENCE_MISCALIBRATED` referral reaches the referral queue.

---

## E4 — Per-Tenant Config Overlays

**Directory convention**: `coverages/{name}/overlays/{tenant_id}.yaml`

**Overlay YAML** contains only fields that differ from the base:
```yaml
cyber:
  cyber_general:
    groups:
      three_layer_assessment:
        - id: technical_infrastructure
          risk: { weight: 0.45 }   # tenant X over-weights tech infra
```

**Merge logic**: deep-merge at config-load time, scoped by `tenant_id` from request context. Overlay versions are snapshotted into the audit table so every premium trace records which overlay was active.

**Enforcement**:
- Overlays cannot change signal-registry structure (only weights, modifiers, guardrails, ILF curve params, routing_constraints).
- Overlays go through the same `config_health_gate` job as base configs.
- Tenant admin UI (admin router) exposes overlay CRUD — out-of-scope for V6 backend, frontend-integrated in V7.

**Acceptance**:
- `tests/integration/test_overlay_merge.py` green.
- Overlay version recorded in `model_version_records` for every quote.
- A tenant-specific overlay is end-to-end traceable from request to audit.

---

## E5 — Golden-Entity Registry

**Directory**: `tests/fixtures/golden_entities/{coverage}/`

**Per coverage, 10 entities** stored as YAML with:
- Entity ID, name, domain, corporate registry identifier.
- Minimum viable input.
- Expected assessment outcome (composite score band, tier, decision, ILF-anchored premium range).
- Tolerance (± score points, ± basis points on premium).

**Regression test**: `tests/integration/test_golden_entities.py` parameterised over every golden entity across every coverage (22 × 10 = 220 tests). Runs on every PR touching `coverages/`, `signal_architecture/`, `layers/`, `world_engine/`.

**Refresh cadence**: quarterly human review of tolerances. Any tightening of a tolerance requires a signed-off PR.

**Acceptance**:
- 220 golden entities committed.
- Regression test green on `main`.
- PR breaking a golden entity fails CI with a readable diff (score/tier/premium delta).

---

## E6 — Drift-Alert → Referral Queue

**Existing**: `world_engine/drift/detector.py` produces `DriftAlert` objects.
**Gap**: alerts have no consumer — they sit in a DB table.

**New**: wire alerts into the referral workflow.

**Files**:
- `infrastructure/api/routes/referrals.py` — extend `POST /api/v1/referrals` to accept `type: DRIFT`.
- `world_engine/drift/detector.py` — on alert persist, dispatch to `ReferralService.create(type="DRIFT", ...)`.
- `infrastructure/db/models.py` — add `ReferralRecord.drift_alert_id` FK.
- `alembic/versions/022_drift_referrals.py`.

**UI hook**: frontend (out-of-scope this workstream) will display DRIFT referrals in the underwriter inbox alongside manual referrals.

**Acceptance**:
- A simulated drift alert (change point injection) produces a referral row visible via `/api/v1/referrals?type=DRIFT`.
- Drift alerts contain: entity ID, coverage, config, drift type (relationship shift / correlation inversion / regime change / emergence burst / velocity), severity.

---

## E7 — Rate-Filing Kit

**New file**: `infrastructure/admin/rate_filing.py`

**API**: `python -m infrastructure.admin.rate_filing --coverage cyber --config cyber_general --state IL --out filings/IL_cyber_2026Q2/`

**Outputs**:
- `filing_memo.md` — narrative explaining the pricing methodology (auto-populated from `logic.md`).
- `actuarial_justification.md` — maps every signal → rate impact with citations to the whitepaper.
- `rate_exhibit.csv` — illustrative premium matrix (exposure × limit × deductible).
- `model_governance_statement.md` — Lloyd's MU&G-aligned governance text.
- `filing_cover.pdf` — SERFF-ready cover page.

**Integration**: `infrastructure/admin/` exposes an authenticated `POST /api/v1/admin/rate-filing/generate` endpoint for tenant admins.

**Acceptance**:
- A CLI invocation produces a filing pack for Cyber in IL and it renders cleanly.
- External counsel review scheduled (out-of-scope here).

---

## E8 — Evidence Dashboard

**New file**: `infrastructure/admin/evidence.py`

**Endpoint**: `GET /api/v1/admin/evidence` (admin role only).

**Payload** (per coverage × config):
```json
{
  "coverage": "cyber",
  "config": "cyber_general",
  "real_signal_pct": 0.62,
  "stub_signal_pct": 0.38,
  "last_calibration_at": "2026-04-15T09:00:00Z",
  "last_calibration_status": "PASS",
  "last_drift_alert_at": "2026-04-12T22:30:00Z",
  "last_golden_check_at": "2026-04-16T02:00:00Z",
  "last_golden_check_status": "PASS",
  "avg_confidence_p50": 0.78,
  "avg_confidence_p95": 0.95,
  "ece": 0.04,
  "monthly_extractor_cost_usd": 4120.50,
  "active_quote_count_30d": 1284,
  "referral_rate_30d": 0.14
}
```

**Grafana dashboard**: `deploy/monitoring/grafana/evidence.json` rendering the same data live.

**Why this matters**: it is the single most important artefact for commercial conversations — it is DSI's public honesty about what's real versus what's simulated. It gates sales conversations ("here is exactly what we have today").

**Acceptance**:
- Endpoint live and gated to admin role.
- Grafana dashboard populated.
- `real_signal_pct` computed from (production extractors actually executed) / (total signals required by config) per assessment, averaged over the last 30 days.

---

## E9 — Taxonomy Unification

**Problem**: the 7 canonical categories are described slightly differently across the whitepaper, README, `master_config_layout.yaml`, `logic.md` templates, and `SKILL.md`.

**Canonical list (to be enforced)**:
1. Network Authority
2. Technical Infrastructure
3. Corporate Digital Footprint
4. Behavioural
5. Public Record
6. Structured Data
7. Direct Inquiry

**Changes**:
- Update `master_config_layout.yaml` comments to match.
- Update `README.md`, `SKILL.md`, `docs/overview/Foundational Principles.md`.
- Update `docs/overview/Whitepaper_*.pdf` source (Markdown/Word master) so future renders are consistent.
- Enforce in `development/project/assessments/scripts/assess_config_compliance.py` — any signal referencing a category outside this list fails.
- Add `infrastructure/builder/signal_library.py` check: each signal's canonical category declared explicitly.

**Migration**: existing signals mapped to the canonical list via a one-time script `infrastructure/admin/taxonomy_migrate.py`. Any signal that doesn't fit (there will be a handful) is raised as a referral for reclassification.

**Acceptance**:
- `assess_config_compliance.py` enforces the canonical list.
- All coverages pass with the canonical categories only.
- All docs updated.

---

## E10 — Stub Retirement

**Problem**: `signal_architecture/signals/extractors/stubs/` is ~600 stub classes returning synthetic data. Today they live alongside production extractors under the production package tree, which is a latent import-path hazard — a future refactor could accidentally re-enable them.

**Action**:
1. Move `signal_architecture/signals/extractors/stubs/` → `tests/fixtures/stub_extractors/`.
2. Update imports in tests that currently reference `signal_architecture...stubs`.
3. Add a CI guard: static analyser that fails build if any non-test module imports from `tests/fixtures/stub_extractors/`.
4. Add a `DSI_ALLOW_STUBS=1` env flag for local dev that re-enables stubs via a pytest shim (never available in production images).

**Why now**: not because the stubs are wrong (they're intentional scaffolding), but because once C1–C3 land and production traffic arrives, the blast radius of an accidental stub import is unbounded — it produces plausible-looking premiums that are fabricated. Moving the stubs into `tests/` makes the production image structurally incapable of hitting a stub path.

**Acceptance**:
- No import from `tests/fixtures/stub_extractors/` outside `tests/`.
- CI guard blocks PRs that try.
- Production Docker image does not ship `tests/` (validated via `docker image inspect`).

---

## Acceptance for Workstream E

- E1 decision made and executed.
- E2 provenance chain reproducible on every quote.
- E3 confidence reliability curves within ECE < 0.1 on every coverage.
- E4 tenant overlays merging cleanly with audit trace.
- E5 220 golden entities green on every PR.
- E6 drift alerts reaching the referral queue.
- E7 rate-filing kit generating IL Cyber filing end-to-end.
- E8 evidence dashboard live.
- E9 taxonomy unified and enforced.
- E10 stubs relocated; production image stub-free.

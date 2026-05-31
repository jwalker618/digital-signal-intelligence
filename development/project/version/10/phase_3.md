# V10 Phase 3 — Carrier Assurance: Validator · Stability · Calibration · Commitments

**Status:** Planning
**Depends on:** Phase 1, Phase 2 (evidence drawer is where validator/stability dock)
**Audience:** carrier only (deliberately not client/broker — see §B)
**Backend precondition:** ✅ add a **validator-verdict GET endpoint** (DTO exists; route does not).

The four capabilities that let an underwriter trust the evidence engine itself: the adversarial validator, stability/reproducibility, triple-source calibration, and integrity commitments. Strictly internal.

---

## A. What has been built (backend)

### A.1 Adversarial validator — ⚠️ DTO only, needs a route
`signal_architecture/validation/` + `schemas/validator.py:ValidatorVerdictDTO`:
`{ signal_id, mode:"quick_pass|full_pass", advance:bool, grade_before, grade_after, axes:{ MATERIAL|CORRECT_ENTITY|OPERATIONALLY_PLAUSIBLE|GENERALISES_AT_RENEWAL : {passed, confidence:"high|medium|low", rationale} }, pro_argument, counter_argument, tie_breaker, elapsed_seconds, decided_at }`.
Verdicts are produced + persisted in the workflow but **not exposed via GET**.
**Add:** `GET /api/v1/model-versions/{mv}/validator-verdicts -> ValidatorVerdictDTO[]` (auth `assessment:read`), reading the verdict store. Test against the validator fixtures.

### A.2 Stability / reproducibility (live)
`signal_architecture/signals/stability.py` + `signal_stability_classification` matview. Classes `stable|flaky|unstable|unknown`. Already inline on `SignalEvidenceDTO.reproducibility` (Phase 2 fetches it). No new endpoint needed.

### A.3 Triple-source calibration (live)
`infrastructure/api/routes/grade_calibration.py` (auth `assessment:refer`):
```
GET  /api/v1/calibration/pending  -> PendingSampleOut[]  { id, submission_id, coverage, signal_id, signal_weight, extractor_grade, validator_grade, sampling_reason, created_at }
POST /api/v1/calibration/decision  body { sample_id, human_grade, note? } -> { ok }
GET  /api/v1/calibration/stats?coverage&window_days -> { window_days, decided, exact_match_extractor_rate, exact_match_validator_rate, within_one_extractor_rate }
```

### A.4 Integrity commitment (live)
`infrastructure/api/routes/commitments.py` (auth `assessment:read`):
```
POST /api/v1/model-versions/{mv}/verify-commitment  body { signal_id?, scope:"full_payload|value_and_grade|pro_counter|composite", candidate_payload } -> { ok, digest_computed }
```

---

## B. What it augments & why
Augments the carrier workbench: the **Phase 2 evidence drawer** (inline validator + stability), plus two new carrier destinations — a **calibration console** and an **assurance roll-up**. **Excluded from client/broker** because validator axes, calibration disagreement, and digest internals expose the model's own uncertainty in a way that informs an underwriter but misleads or arms an outside party. Every endpoint here is already carrier-permissioned; the FE must simply not build client/broker entry points.

Why each matters to the carrier: **validator** = adversarial second opinion (where `advance=false`, look before binding); **stability** = `flaky/unstable` signals are reasons to discount or re-pull; **calibration** = proves grades mean what they claim (extractor/validator/human agreement); **commitment** = tamper-evident digest for audit/dispute.

---

## C. Frontend implementation (carrier)

### C.1 API + store
Extend `store/dsiStore.ts` / `lib/api.ts`: `fetchValidatorVerdicts(mvId)`, `fetchCalibrationPending(coverage?)`, `submitCalibrationDecision(...)`, `fetchCalibrationStats(...)`, `verifyCommitment(mvId, body)`.

### C.2 Inline (in the Phase 2 evidence drawer)
- **Validator strip** — `advance` pill (pos/neg) + a 4-axis mini grid (each axis: pass/fail + confidence dot + rationale tooltip) + grade_before→after. Reuse `ui/chip` + a small grid.
- **Stability badge** — `reproducibility` chip with distinct-value-ratio tooltip.
- **Integrity action** — "Verify integrity" button → `verify-commitment` (scope `value_and_grade`), shows ✓/✗ from `ok` + the computed digest.

### C.3 Calibration console — new carrier route
`frontend/src/app/(app)/carrier/calibration/page.tsx` (add to `navConfig.ts:PORTAL_CARRIER_CHILDREN`, gated by `assessment:refer`):
- **Sample queue** — `admin-table` from `/calibration/pending`: extractor vs validator grade side by side, `sampling_reason`, `signal_weight`; a "grade" action posts `/calibration/decision` with a `human_grade` picker (the 5 grades).
- **Accuracy panel** — from `/calibration/stats`: `kpi-tile`s for `exact_match_extractor_rate`, `within_one_extractor_rate`, `exact_match_validator_rate`, `decided`; a window selector (7/30/90d) + coverage filter.

### C.4 Optional: Assurance roll-up
Add an **Assurance** sub-view to the workbench — either a new `assurance` tab in the carrier submission tab set (alongside `risk`/`pricing`/`versions`) or a section on the `versions` tab — aggregating, for the current MV: validator advance/hold counts, stability-class distribution, last commitment digest.

### C.5 Per-audience matrix
| | Client | Broker | Carrier |
|---|---|---|---|
| anything in this phase | ❌ | ❌ | ✅ |

---

## D. States
- No validator verdicts: "Validator has not run for this version."
- `reproducibility==="unknown"`: muted "insufficient observations".
- Calibration queue empty: "No signals need human grading."

## E. Definition of done
- `GET /model-versions/{mv}/validator-verdicts` added + tested.
- Evidence drawer shows validator axes + stability + integrity verify.
- `/carrier/calibration` lists pending samples, accepts a human grade (POST round-trips), shows accuracy stats.
- Negative test: no client/broker route or component reaches any §A endpoint.

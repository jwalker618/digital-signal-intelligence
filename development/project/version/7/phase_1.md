# Version 6 Phase 1: Evidence-Grade Ladder

## Overview

Augment DSI with an explicit **evidence-grade taxonomy** alongside the existing confidence score. Every `SignalResult` will carry an `evidence_grade` (5-level hardcoded enum) and an `evidence_basis` (free-text justification). Grade propagates upward to group-level and composite-level aggregates. Low grades on high-weight signals can trigger referral via YAML-configured rules.

This is **not** a replacement for confidence. Confidence answers "how sure are we of this value?" (availability × source reliability × temporal decay). Evidence grade answers "what *kind* of evidence supports this value?" — a categorical, ordered taxonomy of corroboration strength. The two are orthogonal: a signal can be high-confidence/low-grade (e.g. a single inferred guess we're sure of) or low-confidence/high-grade (e.g. a regulatory filing we couldn't fully parse).

Inspired by Clearwing's evidence-level ladder (`suspicion → static_corroboration → crash_reproduced → root_cause_explained → exploit_demonstrated → patch_validated`). DSI's adaptation reframes this for risk-signal evidence, not vulnerability evidence.

## Rationale

Three drivers:

1. **Audit trail strengthening.** Today every signal traces back to a score and a confidence number. Adding evidence grade gives carriers/reinsurers a categorical answer to "what *kind* of evidence is this built on?" without forcing them to parse confidence semantics.
2. **Differentiation against SOV-based pricing.** Aligns with the "Precision Illusion" intellectual position: DSI's signals carry explicit evidentiary integrity, where SOV granularity has none.
3. **Foundational Principle alignment.** Reinforces Principle 4 (Behavioural Inference Over Self-Reporting) and Principle 6 (Structured Data Utilisation) by making the *provenance class* of each signal a first-class scoring attribute.

## Decisions (locked, do not relitigate)

| Decision | Choice | Implication |
|-|-|-|
| Location in data model | `SignalResult` + group + composite (full propagation) | All three levels need new fields and aggregation logic |
| Scoring impact | Audit + can trigger referral at low grades | No multiplicative effect on scores; uses existing referral mechanism |
| Taxonomy definition | Hardcoded enum + YAML mapping rules per signal | Enum lives in `types.py`; per-signal `expected_grade` lives in YAML |

## Taxonomy

Five-level ordered enum (ascending evidentiary strength):

| Grade | Name | Definition | Examples |
|-|-|-|-|
| 1 | `INFERRED` | Single weak observation; reasoned guess from indirect cues | Tech stack guessed from one HTTP header; jurisdiction guessed from TLD |
| 2 | `OBSERVED` | Direct extraction from an authoritative source, single source | Security headers fetched from `https://entity.com`; subdomain enumeration |
| 3 | `CORROBORATED` | Multiple independent sources agree on the same value | Office locations confirmed by both Companies House and regulatory filing |
| 4 | `STRUCTURED_ATTESTED` | From a designated authoritative structured feed | S&P credit rating; classification society register entry; SEC filing |
| 5 | `BEHAVIOURALLY_VALIDATED` | Signal confirmed by observed action over time (≥2 observations across a defined window) | Patch cadence observed over 90 days; certificate rotation pattern over 12 months |

**Ordering invariant**: `INFERRED < OBSERVED < CORROBORATED < STRUCTURED_ATTESTED < BEHAVIOURALLY_VALIDATED`. The enum must be `IntEnum` so comparisons work natively.

**Grade vs. confidence (must hold at code review):**
- Grade is categorical (about evidence *kind*).
- Confidence is continuous (about value *certainty*).
- Neither implies the other. Do not compute one from the other.
- Both must be set independently by every extractor.

## Current State

### Files that currently touch confidence (reference points)

- `signal_architecture/signals/types.py` — `SignalResult` dataclass with `confidence: float`
- `signal_architecture/signals/inference/` — extractors that build `SignalResult` instances
- `signal_architecture/signals/aggregators/` — aggregates signals into groups (confidence currently weighted-averaged)
- `layers/risk/scorer.py` (or wherever `ModelScorer` lives) — composite confidence calculation
- `coverages/<cov>/config.yaml` — `signal_registry` entries
- `coverages/master_config_layout.yaml` — VERSION 2.3, current schema reference
- `infrastructure/models/` — ORM models for persisted model versions
- `infrastructure/db/migrations/` — current latest migration
- `infrastructure/api/routes/` — API surfaces that return signal/score data

**Confirm exact paths during Phase 9a discovery** before writing code; do not assume.

## Target State

### Data model additions

```python
# signal_architecture/signals/types.py

from enum import IntEnum
from dataclasses import dataclass, field
from typing import Optional

class EvidenceGrade(IntEnum):
    """Ordered evidentiary strength. Higher = stronger evidence."""
    INFERRED = 1
    OBSERVED = 2
    CORROBORATED = 3
    STRUCTURED_ATTESTED = 4
    BEHAVIOURALLY_VALIDATED = 5

@dataclass
class SignalResult:
    # ... existing fields (value, confidence, etc.) ...
    evidence_grade: EvidenceGrade
    evidence_basis: str  # free-text, required, max 500 chars
    evidence_sources: list[str] = field(default_factory=list)  # source identifiers used
```

`evidence_basis` is **required** (not Optional). An extractor that cannot articulate the basis must not return a result — it should return absence (which is itself a signal per Foundational Principle 5).

### Group-level aggregation

Add to whatever object represents a group aggregation (likely `GroupResult` or similar in `aggregators/`):

```python
@dataclass
class GroupResult:
    # ... existing fields ...
    min_evidence_grade: EvidenceGrade       # weakest grade in group
    weighted_evidence_grade: float          # signal-weight-weighted mean grade (1.0-5.0)
    grade_distribution: dict[EvidenceGrade, float]  # weight share at each grade
```

**Aggregation rules:**
- `min_evidence_grade` = `min(signal.evidence_grade for signal in group if signal has value)`. Absence signals are excluded from `min` (they cannot have a grade — their *absence* is the signal). Track absences separately via existing absence-signal handling.
- `weighted_evidence_grade` = `sum(grade.value × signal.weight) / sum(signal.weight)` over signals with values.
- `grade_distribution` = `{grade: sum(weight for signal at this grade) / total_weight}`.

### Composite-level aggregation

The composite score object (likely `CompositeScore` or model version output) gets:

```python
composite_min_grade: EvidenceGrade
composite_weighted_grade: float
composite_grade_distribution: dict[EvidenceGrade, float]
referral_triggered_by_grade: bool
grade_referral_reasons: list[str]
```

Same aggregation logic applied across all groups, weighted by group weight in the three_layer_assessment.

### Referral integration

Reuse the existing `score_conditions` REFER mechanism. Add a new condition class: `evidence_grade_floor`.

**YAML shape (config-level, in three_layer_assessment or signal_registry entry):**

```yaml
evidence_grade_policy:
  # Per-signal expected minimum grade
  expected_grades:
    sanctions_screening_result: STRUCTURED_ATTESTED
    director_litigation_history: CORROBORATED
    security_headers: OBSERVED
    # signals not listed default to INFERRED (no floor)

  # Composite-level referral trigger
  composite_referral:
    enabled: true
    rules:
      - condition: weighted_evidence_grade_below
        threshold: 2.5
        note: "Composite evidence basis is predominantly inferred"
      - condition: high_weight_signal_below_expected
        weight_threshold: 0.10  # signals contributing >10% weight
        note: "High-weight signal {signal_id} has grade {actual} below expected {expected}"
```

**Resolution order** when grade triggers a referral:
1. Per-signal violations (signal below its `expected_grade`) are collected.
2. Composite-level rules are evaluated.
3. If any fire, a referral is added via existing `REFER` machinery. **No tier override** — grade does not override tier. Grade-driven referrals are *informational referrals* that surface in the underwriter UI.
4. Referral reasons populate `grade_referral_reasons` and feed into the standard referral output.

**Critical:** Grade does **not** modify scores, tier bands, or pricing modifiers. Audit + referral only.

### Persistence

New columns on the model version / signal result tables (exact table names TBC during Phase 9a discovery):

- `signal_results.evidence_grade` — SMALLINT NOT NULL
- `signal_results.evidence_basis` — VARCHAR(500) NOT NULL
- `signal_results.evidence_sources` — JSONB DEFAULT '[]'
- `model_versions.composite_min_grade` — SMALLINT
- `model_versions.composite_weighted_grade` — NUMERIC(3,2)
- `model_versions.composite_grade_distribution` — JSONB
- `model_versions.grade_referral_reasons` — JSONB DEFAULT '[]'

New migration: increment from current latest. Backfill strategy in Phase 9f.

### API surface

Existing signal/model-version endpoints must include the new fields in their response schemas. No new endpoints required for V1. Update Pydantic schemas in `infrastructure/api/schemas/` (or equivalent) to expose `evidence_grade`, `evidence_basis`, `composite_min_grade`, `composite_weighted_grade`, `grade_referral_reasons`.

## Implementation Plan

### Phase 9a: Discovery and Path Confirmation

**Scope**: Before any code changes, confirm exact file paths in the current codebase.

**Actions:**
1. Locate `SignalResult` dataclass — confirm path in `signal_architecture/signals/types.py`.
2. Locate group aggregation object — find file in `signal_architecture/signals/aggregators/`.
3. Locate composite score construction — likely `layers/risk/scorer.py` or `ModelScorer`.
4. Locate existing referral wiring — `score_conditions` evaluator (likely in `layers/risk/` or `signal_architecture/signals/`).
5. Locate latest DB migration number in `infrastructure/db/migrations/`.
6. Locate API response schemas for signal results and model versions.
7. Locate `seed_dsi_bench.py` signal-profile data structure.

**Output**: A short discovery note at the top of the implementation PR confirming every path used in subsequent phases. **Do not skip this step.** Paths in this doc are illustrative — the codebase is authoritative.

### Phase 9b: Core Types and Enum

**Scope**: Add `EvidenceGrade` enum and extend `SignalResult`.

**Files to modify:**
- `signal_architecture/signals/types.py`

**Changes:**
1. Add `EvidenceGrade(IntEnum)` with five values.
2. Add `evidence_grade`, `evidence_basis`, `evidence_sources` fields to `SignalResult`.
3. `evidence_grade` and `evidence_basis` are required (no defaults). `evidence_sources` defaults to empty list.
4. Update `__post_init__` (or equivalent validation) to enforce `len(evidence_basis) <= 500` and `len(evidence_basis) > 0`.

**Tests:**
- `tests/signal_architecture/test_types.py`: enum ordering, `SignalResult` validation (basis required, basis length cap, grade is IntEnum), grade comparison semantics.

**Backward compatibility**: This is a breaking change for `SignalResult` construction. Phase 9c handles every call site.

### Phase 9c: Extractor Updates

**Scope**: Update every extractor (production and stub) to set `evidence_grade` and `evidence_basis`.

**Files to modify:**
- All files under `signal_architecture/signals/inference/` (or wherever extractors live)
- All files under `signal_architecture/signals/extractors/`

**Grade assignment rules (the default grade for each common extractor pattern):**

| Pattern | Default grade |
|-|-|
| Stub extractor (returns canned value) | `INFERRED` |
| Single HTTP fetch from entity-owned domain | `OBSERVED` |
| Multi-source agreement (≥2 independent sources verified) | `CORROBORATED` |
| Pull from credit rating agency / classification society / SEC EDGAR / Companies House / etc. | `STRUCTURED_ATTESTED` |
| Time-series observation across ≥2 captures with ≥30 day separation | `BEHAVIOURALLY_VALIDATED` |

**`evidence_basis` requirements:**
- Must name the source(s) used (e.g. "S&P RatingsDirect", "https://example.com/security.txt fetched 2026-03-04").
- Must state why this grade applies (e.g. "single authoritative structured source").
- Max 500 chars. Be terse, not narrative.

**Per-extractor work:**
1. Read each extractor.
2. Determine which grade pattern fits.
3. Add `evidence_grade=` and `evidence_basis=` to the `SignalResult` construction.
4. Populate `evidence_sources` with source identifiers (URLs, dataset names, API endpoints).
5. If the extractor cannot articulate a basis, the signal is absence — handle via existing absence machinery, do not return a graded result.

**Stub extractors specifically:** must use `INFERRED` and `evidence_basis="Stub extractor: deterministic synthetic value"`. This is intentional — it makes it trivial to see which signals are still on stubs in the audit trail. Aligns with `development/extractor_implementation_plan.md`.

**Tests:**
- For each extractor, add a unit test asserting it produces a valid grade and non-empty basis.
- Add a single integration test that builds a full model cycle and asserts every produced `SignalResult` has a grade and basis.

### Phase 9d: Group and Composite Aggregation

**Scope**: Propagate grade to group and composite levels.

**Files to modify:**
- `signal_architecture/signals/aggregators/` — group aggregator
- `layers/risk/scorer.py` (or wherever composite is built) — composite aggregation
- Output dataclasses for both levels

**Changes:**
1. Add `min_evidence_grade`, `weighted_evidence_grade`, `grade_distribution` to group result object.
2. Add `composite_min_grade`, `composite_weighted_grade`, `composite_grade_distribution` to composite/model-version object.
3. Implement aggregation per the rules in the **Target State** section.
4. Absence signals: excluded from `min` and weighted mean. The fact that absence exists is already a signal via existing absence handling — do not double-count.
5. Empty group (all absence): `min_evidence_grade = None`, `weighted_evidence_grade = None`, `grade_distribution = {}`.

**Tests:**
- `tests/signal_architecture/test_aggregators.py`: grade aggregation with mixed grades, all-same grades, all-absence, weighted mean with non-uniform weights.
- `tests/layers/risk/test_scorer.py`: composite grade aggregation across multiple groups with non-uniform group weights.

### Phase 9e: YAML Schema and Referral Wiring

**Scope**: Add `evidence_grade_policy` block to coverage configs and wire to existing referral machinery.

**Files to modify:**
- `coverages/master_config_layout.yaml` — bump to VERSION 2.4, add `evidence_grade_policy` schema
- `infrastructure/builder/` — validation logic for the new schema block
- Score conditions evaluator (whichever file handles `REFER` today) — add `evidence_grade_floor` and `weighted_evidence_grade_below` and `high_weight_signal_below_expected` conditions
- All 76 existing configs under `coverages/<cov>/config.yaml` — add `evidence_grade_policy` block

**YAML schema (to add to master_config_layout.yaml):**

```yaml
evidence_grade_policy:
  expected_grades:           # map[signal_id -> grade_name]
    type: dict
    optional: true
    description: "Per-signal expected minimum evidence grade. Signals not listed default to no floor."
  composite_referral:
    enabled: bool
    rules:
      - condition: enum[weighted_evidence_grade_below, high_weight_signal_below_expected, min_grade_below]
        threshold: number  # context-dependent
        weight_threshold: number  # only for high_weight_signal_below_expected
        note: string
```

**Config rollout to existing 76 configs:**
1. Add a permissive default `evidence_grade_policy` block: `enabled: true`, `weighted_evidence_grade_below: 2.0` (very forgiving — referral only if average is essentially all inferred), no per-signal `expected_grades` set initially.
2. This means **no calibration disruption in Phase 9e**. Per-signal expected grades and tighter thresholds are tuned per-coverage in Phase 9g.

**Referral evaluator changes:**
- Implement three new condition types.
- They emit referrals via the existing `REFER` path with `override=None` (no tier override).
- Notes use `.format()` interpolation with `{signal_id}`, `{actual}`, `{expected}`.

**Tests:**
- `tests/coverages/test_master_config_layout.py`: schema validation
- `tests/builder/`: validation of `evidence_grade_policy` block accepts/rejects correct/incorrect shapes
- Referral evaluator tests covering each of the three condition types

### Phase 9f: Database Migration and Persistence

**Scope**: Persist evidence-grade data.

**Files to add/modify:**
- New migration file under `infrastructure/db/migrations/` (next sequential number)
- ORM models for signal results and model versions in `infrastructure/models/`

**Migration:**
1. Add the columns listed in **Persistence** section to the relevant tables.
2. New columns are NOT NULL for new rows. **Backfill strategy:** set existing rows to `evidence_grade=1 (INFERRED)` and `evidence_basis='Legacy: pre-Phase-9 record, grade unknown'`. This is honest — old records genuinely don't carry the new evidence basis.
3. Make the backfill part of the migration `up()`.

**ORM updates:**
- Add fields to the relevant ORM model classes.
- Update any serialisation methods.

**Tests:**
- Migration up/down test.
- ORM round-trip test (write SignalResult with grade, read back, assert preservation).

### Phase 9g: API and Frontend Exposure

**Scope**: Make grade visible in API responses and the workbench UI.

**Backend:**
- Update Pydantic response schemas for signal results, group results, model versions.
- Include all new fields in JSON output.

**Frontend (Next.js workbench):**
- Add an "Evidence Grade" column to the Signal Ledger view.
- Add a "Composite Evidence" panel to the Summary tab showing `composite_weighted_grade` and `composite_min_grade` with the grade-distribution bar.
- Surface `grade_referral_reasons` in the Referral Actions tab alongside existing referral reasons.

**Frontend files (illustrative; confirm in 9a):**
- `frontend/src/components/submissions/Workbench/RiskTab.tsx` or signal ledger component
- `frontend/src/components/submissions/Workbench/SummaryTab.tsx`
- `frontend/src/components/submissions/Workbench/ReferralTab.tsx`
- TypeScript types in `frontend/src/types/`

**Tests:**
- API contract tests asserting new fields appear
- Frontend component tests for the new UI elements

### Phase 9h: Seed Data and Calibration

**Scope**: Ensure seed and calibration work end-to-end with the new field.

**Files to modify:**
- `seed_dsi_bench.py` — every signal profile now needs a grade and basis. Use realistic grades per the patterns above. Make the seed data demonstrate every grade level across the dataset.
- Run calibration harness for every coverage: `python -m layers.risk.calibration_harness <coverage>`. All 10 coverages, 76 configs must still pass <15% guardrail hit rate. Because Phase 9e default thresholds are permissive, this should pass without retuning — if it doesn't, investigate before tightening.

**Validation steps (run in order):**
1. `python coverages/doc_generator.py` — regenerate all logic.md files.
2. `python development/project/assessments/scripts/assess_project.py` — full assessment must pass.
3. `python -m layers.risk.calibration_harness <each coverage>` — all must pass.
4. `python seed_dsi_bench.py` — seeds without error.
5. `pytest tests/ -v` — full suite green.

### Phase 9i: Per-Coverage Grade Tuning (Deferred)

**Scope**: Tune `expected_grades` and `composite_referral` thresholds per coverage and per configuration.

**Out of scope for the V1 phase implementation.** Phase 9 ships with permissive defaults that produce no calibration disruption. Per-coverage tuning is a separate piece of work owned by the coverage subject-matter pass — track as Phase 10 or as part of next coverage refresh.

**Document this clearly in the PR description** so it isn't mistaken for incomplete work.

## Constraints & Principles

1. **No subjective adjustments**: Grade does not modify prices. It informs audit and triggers referrals via existing mechanisms only. (Foundational Principle alignment, Referral Methodology Section 2.)
2. **YAML is truth**: Per-signal `expected_grades` and referral thresholds live in YAML. Never hardcode them in Python.
3. **Confidence stays orthogonal**: Do not let grade leak into confidence calculations or vice versa. They are independent metrics.
4. **Absence stays absence**: Absence signals do not have grades. The existing absence-as-signal mechanism handles them. Do not retrofit grade onto absence.
5. **Auditability**: Every signal must trace value → grade → basis → sources. Every referral triggered by grade must trace back to the specific rule that fired.
6. **Backward read compatibility**: API consumers that don't know about grade fields must still receive valid responses. Add fields, don't reshape existing ones.
7. **Calibration must not break**: Phase 9e ships permissive thresholds. If any config's calibration hit rate moves materially, the threshold defaults are too tight — do not adjust calibration to compensate.
8. **No new tier overrides**: Grade-driven referrals never override tier. They are informational referrals only.
9. **Stub honesty**: Stub extractors must declare themselves stubs via `INFERRED` + explicit basis text. This is a feature, not a bug — it surfaces stub debt in audit output.

## Risks & Mitigations

| Risk | Mitigation |
|-|-|
| Extractor updates miss a signal, runtime error on construction | Pytest collection step that imports every inference module and asserts the test for grade/basis exists; CI gate |
| Permissive defaults still cause referral spam on some coverage | Pilot with `composite_referral.enabled: false` initially; flip on per-coverage after observing distribution |
| Confidence and grade get conflated by frontend or downstream consumers | Documentation in API schemas explicitly contrasts the two; UI labels them distinctly |
| Backfill grade=INFERRED makes legacy records look uniformly weak | Acceptable and honest — they genuinely lack the new evidence basis. Underwriters can re-run cycle to get fresh grades |
| Per-coverage tuning never gets done (Phase 9i stays deferred forever) | Track as concrete next-phase work; permissive defaults don't break anything if it slips |
| Grade aggregation interacts badly with re-cycling after signal override (Referral Path A) | New model version recalculates grade alongside score — verify in Phase 9d tests |
| Frontend changes risk regression of existing tabs | Frontend changes are additive (new column, new panel); existing tabs untouched |

## Dependencies

- Version 5 Phases 1-8 complete (all coverage expansions done, calibration passing).
- Current latest DB migration committed and applied.
- `seed_dsi_bench.py` currently passing end-to-end.
- Calibration harness currently green across all 10 coverages / 76 configs.

## Success Criteria

1. `EvidenceGrade` enum present in `signal_architecture/signals/types.py` with five values, IntEnum ordering, all comparisons work.
2. `SignalResult` requires `evidence_grade` and `evidence_basis` at construction. Construction without them raises.
3. Every extractor in `signal_architecture/signals/inference/` and `signal_architecture/signals/extractors/` populates both fields.
4. Group and composite aggregators produce `min_evidence_grade`, `weighted_evidence_grade`, `grade_distribution`.
5. `evidence_grade_policy` block parseable in every config under `coverages/`, validated by builder.
6. Three new score-condition types (`weighted_evidence_grade_below`, `high_weight_signal_below_expected`, `min_grade_below`) evaluate correctly and emit referrals via existing `REFER` machinery.
7. Grade-driven referrals never modify tier or premium.
8. New migration applies cleanly. Backfill sets legacy rows to `INFERRED` + standard basis text.
9. API responses include all new fields. Frontend Signal Ledger shows grade column; Summary shows composite grade panel; Referral Actions surfaces grade-driven referrals.
10. `seed_dsi_bench.py` runs successfully and demonstrates all five grade levels across the dataset.
11. `python coverages/doc_generator.py` regenerates all logic.md without error.
12. `python -m layers.risk.calibration_harness <coverage>` passes for every coverage; no config exceeds the 15% guardrail hit rate.
13. Full `pytest tests/ -v` green.
14. `python development/project/assessments/scripts/assess_project.py` passes.
15. Phase 9i (per-coverage tuning) is explicitly tracked as follow-on work.

## Reference: Where the Inspiration Came From

Clearwing (`https://github.com/Lazarus-AI/clearwing`) uses an ordered evidence-level ladder in its source-hunter pipeline: `suspicion → static_corroboration → crash_reproduced → root_cause_explained → exploit_demonstrated → patch_validated`. Each rung requires stricter corroboration than the last. The structural idea — explicit, ordered, categorical evidence taxonomy distinct from confidence — transplants cleanly to DSI signal extraction. The Clearwing taxonomy itself is vulnerability-specific and is **not** what DSI adopts; DSI defines its own five-level taxonomy fit for risk-signal evidence. No Clearwing code is imported or vendored.

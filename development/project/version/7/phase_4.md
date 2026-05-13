# V7 Phase 4: YAML Policy + Referral Conditions

## Depends on
- Phase 3 complete. `ScoringResult` carries `composite_min_grade`, `composite_grade_distribution`, per-group `GroupGradeRollup`.

## Blocks
- Phase 5 (persistence stores referral reasons including grade-driven ones).
- Phase 7 (calibration store wants per-signal `expected_grade` from policy).
- Phase 14 (frontend exposes grade referrals).

## Scope

Add an `evidence_grade_policy` block to `master_config_layout.yaml`, validate it via the builder, wire three new referral conditions into the scorer, and **script** the rollout across all 24 `coverages/*/*.yaml` configs. Defaults are permissive — no calibration disruption.

Three new condition types:
1. `min_grade_below` — composite-level min grade is below threshold.
2. `distribution_share_below_grade` — share of composite weight at-or-above a grade is under a threshold (e.g. <30% of weight is at `structured_attested` or higher).
3. `high_weight_signal_below_expected` — any signal contributing >X% of weight has actual grade below its `expected_grades` floor.

Critically: **no** `weighted_evidence_grade_below` condition. The scalar mean is not a threshold (Phase 3 D5). The Phase 1 original doc's `weighted_evidence_grade_below: 2.5` is replaced by `distribution_share_below_grade`.

## Decisions (locked)

| # | Decision | Choice |
|---|----------|--------|
| D1 | Conditions | `min_grade_below`, `distribution_share_below_grade`, `high_weight_signal_below_expected` — no scalar-mean condition |
| D2 | Per-signal floor | `expected_grades: {<signal_id>: <grade_name>}` map; signals not listed default to no floor |
| D3 | Default policy block | `enabled: true`, no `expected_grades`, one composite rule: `distribution_share_below_grade` with floor=`observed`, share=`0.5` (referral only if <50% of weight is at observed-or-above) |
| D4 | Action | `REFER` only. No tier override, no DECLINE, no modifier from grade rules. Informational referrals |
| D5 | Per-condition validation | Builder rejects malformed shapes per-condition (e.g. `threshold` required for `min_grade_below`; `share` and `floor` required for `distribution_share_below_grade`; `weight_threshold` required for `high_weight_signal_below_expected`) |
| D6 | Rollout | Scripted: `scripts/add_evidence_grade_policy.py` injects the default block idempotently into each config |
| D7 | Master schema version | `master_config_layout.yaml` bumps to next version per its own versioning rule |
| D8 | Referral note format | `.format()` interpolation with `{signal_id}`, `{actual}`, `{expected}`, `{floor}`, `{share}`, `{weight}` — fields not used in a given condition's template are ignored |
| D9 | Scalar mean tripwire | If any evaluator code attempts to threshold `composite_weighted_mean_grade`, it must call `warn_if_thresholded()` from Phase 3. Tests assert no such call site exists in production code |

## Files

### Create
- `scripts/add_evidence_grade_policy.py` — config-rewrite script
- `tests/unit/test_evidence_grade_policy_schema.py` — Pydantic validation tests
- `tests/unit/test_grade_referral_conditions.py` — evaluator tests
- `tests/unit/test_master_config_layout_v7.py` — master schema doc consistency

### Modify
- `coverages/master_config_layout.yaml` — add `evidence_grade_policy` documented section
- `infrastructure/models/config_schema.py` — add `EvidenceGradePolicy`, `ExpectedGradeMap`, `CompositeGradeRule` Pydantic models; attach to `CoverageConfig` top-level
- `infrastructure/builder/validator.py` — enforce per-condition required fields
- `layers/risk/scorer.py` — after composite rollup, evaluate `evidence_grade_policy` and append grade referrals to `triggered_conditions` / `referral_reasons`
- `layers/risk/types.py` — extend `TriggeredCondition` with a `condition_class: Literal["score", "evidence_grade"]` field so grade-driven referrals are typed
- All 24 `coverages/<cov>/*.yaml` — via the rewrite script

## Types

`infrastructure/models/config_schema.py` additions:

```python
from typing import Literal

EvidenceGradeName = Literal[
    "inferred",
    "observed",
    "corroborated",
    "structured_attested",
    "behaviourally_validated",
]


class ExpectedGradeMap(StrictModel):
    """Per-signal expected minimum evidence grade.

    Signals listed here trigger a referral when their actual grade
    is below the value here. Signals not listed have no floor.
    """
    grades: Dict[str, EvidenceGradeName] = Field(default_factory=dict)


class MinGradeBelowRule(StrictModel):
    condition: Literal["min_grade_below"]
    threshold: EvidenceGradeName
    note: str = "Composite min grade {actual} below threshold {threshold}"


class DistributionShareBelowGradeRule(StrictModel):
    condition: Literal["distribution_share_below_grade"]
    floor: EvidenceGradeName
    share: float = Field(ge=0.0, le=1.0)
    note: str = "Only {actual_share:.0%} of weight is at {floor} or above (target {share:.0%})"


class HighWeightSignalBelowExpectedRule(StrictModel):
    condition: Literal["high_weight_signal_below_expected"]
    weight_threshold: float = Field(gt=0.0, le=1.0)
    note: str = (
        "Signal {signal_id} (weight {weight:.0%}) has grade {actual} "
        "below expected {expected}"
    )


CompositeGradeRule = Union[
    MinGradeBelowRule,
    DistributionShareBelowGradeRule,
    HighWeightSignalBelowExpectedRule,
]


class CompositeReferral(StrictModel):
    enabled: bool = True
    rules: List[CompositeGradeRule] = Field(default_factory=list)


class EvidenceGradePolicy(StrictModel):
    enabled: bool = True
    expected_grades: ExpectedGradeMap = Field(default_factory=ExpectedGradeMap)
    composite_referral: CompositeReferral = Field(default_factory=CompositeReferral)


# Attach to CoverageConfig:
class CoverageConfig(StrictModel):
    # ... existing fields ...
    evidence_grade_policy: EvidenceGradePolicy = Field(default_factory=EvidenceGradePolicy)
```

`layers/risk/types.py` additions:

```python
@dataclass
class TriggeredCondition:
    # ... existing fields ...
    condition_class: Literal["score", "evidence_grade"] = "score"
```

## Default policy block (injected into every coverage)

```yaml
evidence_grade_policy:
  enabled: true
  expected_grades:
    grades: {}            # tightened per-coverage in V8 by coverage SMEs
  composite_referral:
    enabled: true
    rules:
      - condition: distribution_share_below_grade
        floor: observed
        share: 0.5
        note: "Only {actual_share:.0%} of weight is at OBSERVED or above (target 50%)"
```

This is permissive: virtually every well-extractored config will have ≥50% of weight at OBSERVED+ because Phase 2 graded every production extractor at OBSERVED at minimum.

## `scripts/add_evidence_grade_policy.py`

```python
"""V7 Phase 4 — inject the default evidence_grade_policy block into every
coverage config. Idempotent: re-running on an already-injected config is a
no-op (block presence detected by top-level key).

Usage:
    python scripts/add_evidence_grade_policy.py            # all configs
    python scripts/add_evidence_grade_policy.py --check    # dry-run, exit 1 if any config needs the block
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from ruamel.yaml import YAML

COVERAGES = Path("coverages")
DEFAULT_POLICY = """
evidence_grade_policy:
  enabled: true
  expected_grades:
    grades: {}
  composite_referral:
    enabled: true
    rules:
      - condition: distribution_share_below_grade
        floor: observed
        share: 0.5
        note: "Only {actual_share:.0%} of weight is at OBSERVED or above (target 50%)"
"""


def inject(path: Path, check: bool = False) -> bool:
    """Return True if file was modified (or would be in check mode)."""
    yaml = YAML()
    yaml.preserve_quotes = True
    yaml.indent(mapping=2, sequence=4, offset=2)
    data = yaml.load(path)
    if data is None:
        data = {}
    if "evidence_grade_policy" in data:
        return False
    policy = yaml.load(DEFAULT_POLICY)
    data["evidence_grade_policy"] = policy["evidence_grade_policy"]
    if check:
        return True
    with path.open("w", encoding="utf-8") as f:
        yaml.dump(data, f)
    return True


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    targets = list(COVERAGES.rglob("*.yaml"))
    # exclude master_config_layout.yaml
    targets = [t for t in targets if t.name != "master_config_layout.yaml"]
    changed = []
    for t in targets:
        if inject(t, check=args.check):
            changed.append(t)
    if args.check:
        if changed:
            print(f"missing evidence_grade_policy in: {len(changed)} files")
            for c in changed:
                print(f"  {c}")
            return 1
        print("all configs carry evidence_grade_policy")
        return 0
    print(f"injected into {len(changed)} configs")
    for c in changed:
        print(f"  {c}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

## Referral evaluator additions

In `layers/risk/scorer.py`, after composite rollup (Phase 3 hooks):

```python
from signal_architecture.signals.aggregators.grade_rollup import warn_if_thresholded


def _evaluate_evidence_grade_policy(
    self,
    scoring_result: ScoringResult,
    config: CoverageConfig,
) -> list[TriggeredCondition]:
    """V7 Phase 4 — evaluate evidence_grade_policy rules.

    Emits TriggeredCondition with condition_class="evidence_grade" and
    action=REFER for each rule that fires. Never produces tier override
    or DECLINE.
    """
    policy = config.evidence_grade_policy
    if not policy.enabled or not policy.composite_referral.enabled:
        return []

    triggered: list[TriggeredCondition] = []

    # Per-signal expected_grade violations come first
    for signal_id, expected in policy.expected_grades.grades.items():
        actual = self._find_signal_grade(scoring_result, signal_id)
        if actual is None:
            continue
        if evidence_rank(actual) < evidence_rank(expected):
            triggered.append(TriggeredCondition(
                source_type="signal",
                source_id=signal_id,
                action=ConditionAction.REFER,
                condition_class="evidence_grade",
                note=(
                    f"Signal {signal_id} grade {actual} below expected {expected}"
                ),
            ))

    # Composite-level rules
    composite_dist = scoring_result.composite_grade_distribution or {}
    composite_min = scoring_result.composite_min_grade

    for rule in policy.composite_referral.rules:
        if rule.condition == "min_grade_below":
            if composite_min is None:
                continue
            if evidence_rank(composite_min) < evidence_rank(rule.threshold):
                triggered.append(TriggeredCondition(
                    source_type="composite",
                    source_id="composite",
                    action=ConditionAction.REFER,
                    condition_class="evidence_grade",
                    note=rule.note.format(actual=composite_min, threshold=rule.threshold),
                ))
        elif rule.condition == "distribution_share_below_grade":
            share = sum(
                w for g, w in composite_dist.items()
                if evidence_rank(g) >= evidence_rank(rule.floor)
            )
            if share < rule.share:
                triggered.append(TriggeredCondition(
                    source_type="composite",
                    source_id="composite",
                    action=ConditionAction.REFER,
                    condition_class="evidence_grade",
                    note=rule.note.format(
                        actual_share=share, share=rule.share, floor=rule.floor,
                    ),
                ))
        elif rule.condition == "high_weight_signal_below_expected":
            for sig_id, sig_weight, sig_grade in self._iter_signal_weights(scoring_result):
                if sig_weight < rule.weight_threshold:
                    continue
                expected = policy.expected_grades.grades.get(sig_id)
                if expected is None or sig_grade is None:
                    continue
                if evidence_rank(sig_grade) < evidence_rank(expected):
                    triggered.append(TriggeredCondition(
                        source_type="signal",
                        source_id=sig_id,
                        action=ConditionAction.REFER,
                        condition_class="evidence_grade",
                        note=rule.note.format(
                            signal_id=sig_id, weight=sig_weight,
                            actual=sig_grade, expected=expected,
                        ),
                    ))

    return triggered
```

## Steps

### 4.1 — Pydantic models
**Files**: `infrastructure/models/config_schema.py`.
**Action**: Add the four new `StrictModel` classes and attach to `CoverageConfig`. Run existing builder unit tests; default factory should mean every previously-valid config still parses.

### 4.2 — Master config layout doc
**Files**: `coverages/master_config_layout.yaml`.
**Action**: Add a documented `evidence_grade_policy:` section explaining each condition and the default values. Bump the layout version per the file's own convention.

### 4.3 — Builder per-condition validation
**Files**: `infrastructure/builder/validator.py`.
**Action**: For each rule type, assert the required fields are present and well-formed. Reject `weight_threshold` outside (0, 1], `share` outside [0, 1], unknown grades, unknown conditions.

### 4.4 — Script the rollout
**Files**: `scripts/add_evidence_grade_policy.py` (create), then run it.
**Action**: `python scripts/add_evidence_grade_policy.py` then `python scripts/add_evidence_grade_policy.py --check` exits 0.

### 4.5 — Evaluator wiring
**Files**: `layers/risk/scorer.py`, `layers/risk/types.py`.
**Action**: Add `condition_class` to `TriggeredCondition`. Implement `_evaluate_evidence_grade_policy`. Call it in the scorer after composite rollup. Append the resulting conditions to `triggered_conditions` and matching `referral_reasons`.

### 4.6 — Wire `warn_if_thresholded` tripwire
**Files**: any evaluator code that touches `composite_weighted_mean_grade`.
**Action**: Should be none. Add a CI grep:
```bash
! grep -rn "composite_weighted_mean_grade\s*[<>]" layers/ infrastructure/ signal_architecture/
```
fails CI if anyone thresholds the scalar mean.

### 4.7 — Tests
**Files**: `tests/unit/test_evidence_grade_policy_schema.py`, `tests/unit/test_grade_referral_conditions.py`.
**Action**:
- Schema validation accepts default, rejects unknown condition, rejects malformed per-condition fields.
- Evaluator emits no referrals when composite is all-OBSERVED-or-above with default policy.
- Evaluator emits one referral when distribution-share at OBSERVED+ is below the configured share.
- Evaluator emits one referral when a high-weight signal is below its expected grade.
- Grade referrals carry `action=REFER` and `condition_class="evidence_grade"` — never tier override.

### 4.8 — Calibration regression check
**Files**: none modified.
**Action**: Run calibration harness for every coverage. Permissive defaults must produce **zero** referrals on the seed data; calibration metrics unchanged.
**Test**:
```bash
python -m seed bench
python -m layers.risk.calibration_harness aerospace cyber casualty fi fpr energy property marine pi do
```

## Test gates

```bash
# Schema validation
pytest tests/unit/test_evidence_grade_policy_schema.py -v

# Evaluator
pytest tests/unit/test_grade_referral_conditions.py -v

# Config rollout
python scripts/add_evidence_grade_policy.py --check  # exits 0

# No scalar-mean thresholding
! grep -rn "composite_weighted_mean_grade\s*[<>]" layers/ infrastructure/ signal_architecture/

# Full suite
pytest tests/ -x -q

# Calibration unchanged
python -m layers.risk.calibration_harness aerospace cyber casualty fi fpr energy property marine pi do
```

## Done when

- [ ] Every config under `coverages/` carries an `evidence_grade_policy` block (script `--check` exits 0).
- [ ] `CoverageConfig` parses with default policy; existing configs still validate.
- [ ] Three new condition types implemented; tests green.
- [ ] Grade-driven referrals always `action=REFER` and `condition_class="evidence_grade"`.
- [ ] No code thresholds `composite_weighted_mean_grade`.
- [ ] Calibration unchanged across all 24 configs.
- [ ] Full pytest green.

## Out of scope

- Per-coverage tuning of `expected_grades` or `share` thresholds. → V8 (Phase 1 of next major).
- Persisting grade referrals into the `referrals` ORM table. → Phase 5.
- Frontend rendering of grade referrals. → Phase 14.
- Adversarial validation. → Phase 6.

## Invariants

1. No grade-driven condition emits anything other than `REFER`.
2. The scalar mean is never thresholded.
3. Default policy produces zero referrals on seed data.
4. Config schema is forward-compatible: configs without `evidence_grade_policy` are rejected by the builder *only after* the rollout script has run.

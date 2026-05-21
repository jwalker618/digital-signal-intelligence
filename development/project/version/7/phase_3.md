# V7 Phase 3: Promotion-Aware Aggregation + Absence Sub-Typing

## Depends on
- Phase 1 (taxonomy, `bump_evidence`).
- Phase 2 (every produced `SignalResult` carries a grade; role binding is raise-mode).

## Blocks
- Phase 4 (referral conditions key on group/composite rollup outputs).
- Phase 5 (persistence stores rollup outputs).
- Phase 15 (frontend renders rollup outputs).

## Scope

Make aggregation promotion-aware. When two extractors independently produce the same signal value, merge them into one result at the higher grade rather than treating them as separate rows. Compute group-level and composite-level rollups using `(min_grade, distribution)` as primary, scalar weighted mean for display only. Introduce **absence sub-typing**: distinguish `absence_failed_fetch` (we couldn't get a value) from `absence_authoritative_empty` (the source authoritatively said there is nothing — a *signal*, sometimes the strongest one).

## Decisions (locked)

| # | Decision | Choice |
|---|----------|--------|
| D1 | Promotion-merge | When ≥2 `SignalResult` instances share the same `signal_id` and equivalent `score`/`category` (within tolerance), aggregator emits one merged result at `bump_evidence` of the contributors' grades |
| D2 | Equivalence tolerance | Numeric: `abs(a-b) <= max(1.0, 0.05 * max(abs(a), abs(b)))`. Categorical: exact match |
| D3 | Disagreement | If contributors disagree on value, no promotion. Emit one result at `min_grade`, populate `evidence_basis` with disagreement description, set `evidence_counter` to the losing case (Phase 6 fills this properly) |
| D4 | Rollup primary | `(min_grade, distribution)` — both at group and composite level |
| D5 | Rollup scalar | `weighted_mean_grade: float | None` computed but flagged "display only; do not threshold" via field-doc and a runtime warning if used by a condition evaluator |
| D6 | Absence sub-types | `absence_failed_fetch`, `absence_authoritative_empty`. Stored on `SignalResult.absence_sub_type: Optional[str]`. Returns from extractors via the `EvidenceSource(kind="absence")` pattern |
| D7 | Authoritatively-empty has a grade | Yes. `absence_authoritative_empty` carries the grade of the source that confirmed emptiness (typically `structured_attested`) |
| D8 | Failed-fetch has no grade | Yes. `absence_failed_fetch` carries `evidence_grade=None` and is excluded from all rollups |
| D9 | Composite weighting | Group weights from `three_layer_assessment.layer_weight` × `signal_registry.signal_weight`. No change to existing weights |
| D10 | Empty group | `min_grade=None`, `distribution={}`, `weighted_mean_grade=None`; downstream consumers must handle `None` |

## Files

### Create
- `signal_architecture/signals/aggregators/grade_rollup.py` — pure functions for merge, min/distribution rollup
- `tests/unit/test_grade_rollup.py`
- `tests/unit/test_aggregator_promotion_merge.py`

### Modify
- `signal_architecture/signals/types.py` — add `absence_sub_type: Optional[Literal["absence_failed_fetch", "absence_authoritative_empty"]] = None` to `SignalResult`. Add new `GroupResult` and `CompositeGradeRollup` dataclasses
- `signal_architecture/signals/base.py` — fill in `aggregate_evidence` body (Phase 1 left it as stub)
- `signal_architecture/signals/aggregators/implementations/` — every concrete aggregator gains a hook to call the rollup helpers. Most aggregators do not need behavioural changes — the rollup is computed by the framework on the contributing signals
- `layers/risk/scorer.py` — composite-level rollup on top of group rollups
- `layers/risk/types.py` — extend `ScoringResult` to carry `composite_min_grade`, `composite_distribution`, `composite_weighted_mean_grade`, per-group `min_grade` / `distribution`

## Types

`signal_architecture/signals/aggregators/grade_rollup.py`:

```python
"""V7 Phase 3 — promotion-merge and grade rollup helpers.

Pure functions. No I/O. No DB. Aggregator and scorer code calls these.
"""
from __future__ import annotations

import math
import warnings
from collections import Counter
from dataclasses import dataclass
from typing import Iterable, Optional, Sequence

from signal_architecture.signals.evidence import (
    EVIDENCE_GRADES,
    EvidenceGrade,
    EvidenceSource,
    bump_evidence,
    evidence_rank,
)
from signal_architecture.signals.types import SignalResult


# ---------------------------------------------------------------------------
# Value equivalence
# ---------------------------------------------------------------------------

def _values_equivalent(a: SignalResult, b: SignalResult) -> bool:
    """Two SignalResults agree on the value they assert (within tolerance)."""
    if a.score is not None and b.score is not None:
        diff = abs(a.score - b.score)
        tol = max(1.0, 0.05 * max(abs(a.score), abs(b.score)))
        return diff <= tol
    if a.category is not None and b.category is not None:
        return a.category == b.category
    return False


# ---------------------------------------------------------------------------
# Promotion-merge over a list of contributors that share a signal_id
# ---------------------------------------------------------------------------

@dataclass
class MergedSignal:
    """One signal_id, possibly assembled from multiple contributors."""
    result: SignalResult
    contributor_count: int
    disagreement: bool


def merge_contributors(contributors: Sequence[SignalResult]) -> MergedSignal:
    """Promotion-merge over contributors that all share the same signal_id.

    Rules:
        - All agree on value → one merged result at the max grade among them.
        - Disagree → one merged result at the MIN grade among graded contributors,
          with evidence_basis describing the disagreement and evidence_counter
          referencing the dissenting source. Score takes the median.
        - Mix of graded + ungraded (error/skipped) → graded contributors win.
        - All ungraded → emit the first ungraded result unchanged.
    """
    if not contributors:
        raise ValueError("merge_contributors called with empty contributors")
    graded = [c for c in contributors if c.evidence_grade is not None and c.score is not None or c.category is not None]
    if not graded:
        return MergedSignal(result=contributors[0], contributor_count=len(contributors), disagreement=False)

    pivot = graded[0]
    all_agree = all(_values_equivalent(pivot, c) for c in graded[1:])

    merged_grade: Optional[EvidenceGrade] = None
    merged_sources: list[EvidenceSource] = []
    for c in graded:
        if c.evidence_grade is not None:
            merged_grade = bump_evidence(merged_grade, c.evidence_grade) if all_agree else _take_min(merged_grade, c.evidence_grade)
        merged_sources.extend(c.evidence_sources or [])

    if all_agree:
        # Pick the contributor with the strongest grade as the "base"; promote its grade.
        base = max(graded, key=lambda c: evidence_rank(c.evidence_grade))  # type: ignore[arg-type]
        basis = (
            f"Agreement across {len(graded)} sources; "
            f"promoted to {merged_grade}"
        )
        result = SignalResult(
            signal_id=base.signal_id,
            score=base.score,
            category=base.category,
            confidence=max(c.confidence for c in graded),
            evidence_grade=merged_grade,
            evidence_basis=basis[:500],
            evidence_sources=merged_sources,
            metadata={"contributor_count": len(graded), "merged": True},
        )
        return MergedSignal(result=result, contributor_count=len(graded), disagreement=False)

    # Disagreement path
    scores = [c.score for c in graded if c.score is not None]
    cats = [c.category for c in graded if c.category is not None]
    if scores:
        median = sorted(scores)[len(scores) // 2]
    else:
        median = None
    if cats:
        # Most common category
        chosen_cat = Counter(cats).most_common(1)[0][0]
        outvoted = [c for c in cats if c != chosen_cat]
    else:
        chosen_cat = None
        outvoted = []

    basis = (
        f"Disagreement across {len(graded)} sources; "
        f"took median/majority. Min grade applied."
    )[:500]
    counter = (
        f"Outvoted: {outvoted}" if outvoted
        else f"Score spread {min(scores)}..{max(scores)} (n={len(scores)})"
        if scores else "no consensus"
    )[:500]

    result = SignalResult(
        signal_id=graded[0].signal_id,
        score=median,
        category=chosen_cat,
        confidence=min(c.confidence for c in graded),  # disagreement lowers confidence
        evidence_grade=merged_grade,
        evidence_basis=basis,
        evidence_sources=merged_sources,
        evidence_counter=counter,
        metadata={"contributor_count": len(graded), "merged": True, "disagreement": True},
    )
    return MergedSignal(result=result, contributor_count=len(graded), disagreement=True)


def _take_min(current: Optional[EvidenceGrade], candidate: EvidenceGrade) -> EvidenceGrade:
    """Inverse of bump_evidence — used only in the disagreement branch."""
    if current is None:
        return candidate
    return candidate if evidence_rank(candidate) < evidence_rank(current) else current


# ---------------------------------------------------------------------------
# Group-level and composite-level rollup
# ---------------------------------------------------------------------------

@dataclass
class GradeRollup:
    """Group- or composite-level grade summary."""
    min_grade: Optional[EvidenceGrade]
    weighted_mean_grade: Optional[float]   # display only; do not threshold
    distribution: dict[EvidenceGrade, float]  # weight-share at each grade

    def is_empty(self) -> bool:
        return self.min_grade is None


def rollup(
    contributions: Iterable[tuple[SignalResult, float]],
) -> GradeRollup:
    """Roll up a set of (signal, weight) tuples to a GradeRollup.

    Excluded from rollup:
        - `absence_failed_fetch` signals (no grade).
        - Signals with `evidence_grade is None`.
        - Signals with `skipped=True` or `error is not None`.

    Included:
        - `absence_authoritative_empty` signals — they carry a grade.
        - Every other graded signal.
    """
    items = [(s, w) for s, w in contributions
             if s.evidence_grade is not None
             and not s.skipped
             and s.error is None
             and s.absence_sub_type != "absence_failed_fetch"]
    if not items:
        return GradeRollup(min_grade=None, weighted_mean_grade=None, distribution={})

    min_grade = items[0][0].evidence_grade
    total_weight = 0.0
    weighted_sum = 0.0
    dist_weights: dict[EvidenceGrade, float] = {g: 0.0 for g in EVIDENCE_GRADES}

    for sig, weight in items:
        g = sig.evidence_grade
        assert g is not None  # filtered above
        if evidence_rank(g) < evidence_rank(min_grade):
            min_grade = g
        weighted_sum += evidence_rank(g) * weight
        total_weight += weight
        dist_weights[g] += weight

    mean_rank = weighted_sum / total_weight if total_weight > 0 else None
    distribution = {g: w / total_weight for g, w in dist_weights.items() if w > 0}
    # rank → 1.0..5.0-style display value (rank 0 → 1.0, rank 4 → 5.0)
    weighted_mean_grade = mean_rank + 1.0 if mean_rank is not None else None

    return GradeRollup(
        min_grade=min_grade,
        weighted_mean_grade=weighted_mean_grade,
        distribution=distribution,
    )


def composite_rollup(group_rollups: Iterable[tuple[GradeRollup, float]]) -> GradeRollup:
    """Roll up multiple GroupRollup by group weight to a composite-level rollup."""
    # Decompose each group into its (grade, group_weight × intra-group_share)
    contributions: list[tuple[EvidenceGrade, float]] = []
    for gr, gw in group_rollups:
        if gr.is_empty():
            continue
        for grade, share in gr.distribution.items():
            contributions.append((grade, gw * share))
    if not contributions:
        return GradeRollup(min_grade=None, weighted_mean_grade=None, distribution={})

    min_grade = min(contributions, key=lambda x: evidence_rank(x[0]))[0]
    total = sum(w for _, w in contributions)
    weighted_sum = sum(evidence_rank(g) * w for g, w in contributions)
    distribution: dict[EvidenceGrade, float] = {}
    for g, w in contributions:
        distribution[g] = distribution.get(g, 0.0) + w / total
    return GradeRollup(
        min_grade=min_grade,
        weighted_mean_grade=(weighted_sum / total) + 1.0,
        distribution=distribution,
    )


def warn_if_thresholded(weighted_mean_grade: Optional[float], context: str) -> None:
    """Called by referral evaluators that try to threshold the scalar.

    Phase 4 wires this in. Any condition that compares weighted_mean_grade
    to a number must call this first — it surfaces the ordinal-vs-cardinal
    pitfall in logs without blocking the comparison.
    """
    warnings.warn(
        f"{context}: thresholding weighted_mean_grade ({weighted_mean_grade}) "
        "uses cardinal arithmetic on an ordinal taxonomy. "
        "Prefer min_grade or distribution-share rules.",
        stacklevel=2,
    )
```

`signal_architecture/signals/types.py` — additions:

```python
# Append to SignalResult:
absence_sub_type: Optional[Literal["absence_failed_fetch", "absence_authoritative_empty"]] = None

# New dataclasses (after SignalResult):

@dataclass
class GroupResult:
    """V7 Phase 3 — per-group rollup."""
    group_id: str
    weighted_score: float
    confidence: float
    signal_results: Dict[str, SignalResult]
    min_grade: Optional[str] = None              # EvidenceGrade literal
    weighted_mean_grade: Optional[float] = None  # display only
    grade_distribution: Dict[str, float] = field(default_factory=dict)


@dataclass
class CompositeGradeRollup:
    """V7 Phase 3 — coverage-level grade summary."""
    min_grade: Optional[str] = None
    weighted_mean_grade: Optional[float] = None
    grade_distribution: Dict[str, float] = field(default_factory=dict)
```

`layers/risk/types.py` — extend `ScoringResult`:

```python
# Add to ScoringResult:
composite_min_grade: Optional[str] = None              # EvidenceGrade literal
composite_weighted_mean_grade: Optional[float] = None  # display only
composite_grade_distribution: Dict[str, float] = field(default_factory=dict)
group_grade_rollups: Dict[str, "GroupGradeRollup"] = field(default_factory=dict)


@dataclass
class GroupGradeRollup:
    group_id: str
    min_grade: Optional[str]
    weighted_mean_grade: Optional[float]
    distribution: Dict[str, float]
```

## Steps

### 3.1 — Land `grade_rollup.py` + tests
**Files**: `signal_architecture/signals/aggregators/grade_rollup.py` (create), `tests/unit/test_grade_rollup.py` (create).
**Action**: Drop in the code above. Test covers: merge with agreement, merge with disagreement, rollup over mixed grades, rollup with absence-authoritative-empty included, rollup with absence-failed-fetch excluded, composite rollup with non-uniform group weights.

### 3.2 — Extend `SignalResult` and add result dataclasses
**Files**: `signal_architecture/signals/types.py`.
**Action**: Add `absence_sub_type` field. Add `GroupResult` and `CompositeGradeRollup` dataclasses.

### 3.3 — Wire promotion-merge into aggregators
**Files**: `signal_architecture/signals/aggregators/base.py`, every implementation under `signal_architecture/signals/aggregators/implementations/`.
**Action**: Add a `merge_contributing_signals(self, signal_id, contributors) -> SignalResult` method on `BaseAggregator` that delegates to `merge_contributors` from the rollup module. Implementations call it whenever they're handed >1 result with the same `signal_id`. Most coverage-specific aggregators inherit it without overriding.

### 3.4 — Group-level rollup
**Files**: `layers/risk/scorer.py`.
**Action**: After computing per-group `weighted_score`, call `rollup(...)` with `(signal_result, signal_weight)` for each signal in the group. Persist the `GradeRollup` into a new `GroupGradeRollup` field on `ScoringResult.group_grade_rollups[group_id]`.

### 3.5 — Composite-level rollup
**Files**: `layers/risk/scorer.py`.
**Action**: After all groups are scored, call `composite_rollup(...)` with `(GradeRollup, group_weight)` tuples. Set `composite_min_grade`, `composite_weighted_mean_grade`, `composite_grade_distribution` on `ScoringResult`.

### 3.6 — Absence sub-typing in extractors
**Files**: extractors that today return absence/empty. Find via:
```bash
grep -rln "SignalResult(.*skipped=True\|SignalResult(.*error=\|return None" signal_architecture/signals/extractors/
```
**Action**: Differentiate:
- Source returned an authoritative empty (e.g. sanctions screen returned "no matches"): construct `SignalResult` with `absence_sub_type="absence_authoritative_empty"`, the appropriate grade (typically `structured_attested`), a real `EvidenceSource(kind="absence", ref="ofac:no_match")`, and a value indicating cleanliness (e.g. `score=100`, `category="CLEAN"`).
- Source failed: `absence_sub_type="absence_failed_fetch"`, `evidence_grade=None`, `error="..."` (existing pattern).

### 3.7 — Extend ScoringResult and pipe through
**Files**: `layers/risk/types.py`, `layers/risk/scorer.py`, `layers/risk/workflow.py` if it propagates `ScoringResult`.
**Action**: Add the new fields to `ScoringResult`. Ensure downstream serialisers either pass through unchanged or are updated (Phase 14 handles API exposure).

## Test gates

```python
# tests/unit/test_grade_rollup.py (essentials)

from signal_architecture.signals.aggregators.grade_rollup import (
    rollup, composite_rollup, merge_contributors,
)
from signal_architecture.signals.types import SignalResult


def sr(sid, score, grade, basis="x", **kw):
    return SignalResult(
        signal_id=sid, score=score, confidence=1.0,
        evidence_grade=grade, evidence_basis=basis, **kw,
    )


def test_merge_agreement_promotes():
    a = sr("s", 50, "observed")
    b = sr("s", 51, "structured_attested")  # within 5% of 50 → equivalent
    merged = merge_contributors([a, b])
    assert merged.result.evidence_grade == "structured_attested"
    assert merged.disagreement is False


def test_merge_disagreement_takes_min():
    a = sr("s", 50, "observed")
    b = sr("s", 90, "structured_attested")  # > 5% disagreement
    merged = merge_contributors([a, b])
    assert merged.result.evidence_grade == "observed"
    assert merged.disagreement is True
    assert merged.result.evidence_counter


def test_rollup_excludes_failed_fetch():
    a = sr("a", 50, "observed")
    b = SignalResult(signal_id="b", evidence_grade=None,
                     absence_sub_type="absence_failed_fetch")
    r = rollup([(a, 1.0), (b, 1.0)])
    assert r.min_grade == "observed"
    assert "observed" in r.distribution
    assert len(r.distribution) == 1


def test_rollup_includes_authoritative_empty():
    a = sr("a", 50, "observed")
    b = sr("b", 100, "structured_attested",
           absence_sub_type="absence_authoritative_empty")
    r = rollup([(a, 1.0), (b, 1.0)])
    assert r.min_grade == "observed"
    assert "structured_attested" in r.distribution


def test_composite_rollup_non_uniform_weights():
    a_rollup = rollup([(sr("a", 50, "observed"), 1.0)])
    b_rollup = rollup([(sr("b", 50, "structured_attested"), 1.0)])
    c = composite_rollup([(a_rollup, 0.2), (b_rollup, 0.8)])
    assert c.min_grade == "observed"
    # 0.8 of weight is at structured_attested → bias in mean
    assert c.weighted_mean_grade > 3.5


def test_empty_group():
    r = rollup([])
    assert r.is_empty()
    assert r.min_grade is None
```

```bash
pytest tests/unit/test_grade_rollup.py tests/unit/test_aggregator_promotion_merge.py -v
pytest tests/ -x -q
python scripts/lint_evidence_completeness.py  # still clean
```

## Done when

- [ ] `grade_rollup.py` module + unit tests green.
- [ ] `SignalResult.absence_sub_type` populated by every extractor that today returns absence.
- [ ] `ScoringResult` carries composite grade fields + per-group rollups.
- [ ] No extractor returns `SignalResult(skipped=True)` for an authoritatively-empty source — all such sites converted to `absence_authoritative_empty` with a real grade.
- [ ] Full pytest green.
- [ ] Calibration unchanged across all 24 configs.

## Out of scope

- YAML policy block, referral wiring. → Phase 4.
- DB columns for rollups. → Phase 5.
- Pro/counter populated by the validator. → Phase 6 (Phase 3 sets `evidence_counter` only on disagreement merges as a side-effect — that's fine).
- Frontend rendering of distribution bar. → Phase 15.

## Invariants

1. `rollup` and `composite_rollup` never include `absence_failed_fetch` or ungraded signals.
2. `weighted_mean_grade` is never used as a threshold by any code in this phase. Phase 4 wires `warn_if_thresholded` as a tripwire.
3. Promotion-merge is order-independent: `merge_contributors([a, b, c]) == merge_contributors([c, b, a])` for grade and value (modulo `evidence_sources` ordering).
4. Pricing outputs unchanged within rounding tolerance.

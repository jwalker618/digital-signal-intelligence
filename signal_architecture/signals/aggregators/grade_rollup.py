"""V7 Phase 3 — promotion-merge and grade rollup helpers.

Pure functions. No I/O. No DB. Aggregator and scorer code calls these.

Two operations:

- `merge_contributors`: collapse multiple SignalResult instances that share
  a signal_id into one. Agreement promotes (max grade), disagreement
  takes min grade and records the dissenting case.

- `rollup` / `composite_rollup`: produce a `(min_grade, distribution,
  weighted_mean_grade)` summary at group or composite level. The
  weighted mean is display-only — `warn_if_thresholded()` exists to
  surface the cardinal-on-ordinal mistake when something tries to
  compare against it.
"""
from __future__ import annotations

import math
import warnings
from collections import Counter
from dataclasses import dataclass, field
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
    """Two SignalResults agree on the value they assert (within tolerance).

    Numeric: |a-b| <= max(1.0, 0.05 * max(|a|, |b|)).
    Categorical: exact match.
    """
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
        - All agree on value -> one merged result at the max grade among them.
        - Disagree -> one merged result at the MIN grade among graded contributors,
          with evidence_basis describing the disagreement and evidence_counter
          referencing the dissenting source. Score takes the median.
        - Mix of graded + ungraded (error/skipped) -> graded contributors win.
        - All ungraded -> emit the first contributor unchanged.
    """
    if not contributors:
        raise ValueError("merge_contributors called with empty contributors")

    graded = [
        c for c in contributors
        if c.evidence_grade is not None
        and (c.score is not None or c.category is not None)
    ]
    if not graded:
        return MergedSignal(
            result=contributors[0],
            contributor_count=len(contributors),
            disagreement=False,
        )

    pivot = graded[0]
    all_agree = all(_values_equivalent(pivot, c) for c in graded[1:])

    merged_sources: list[EvidenceSource] = []
    for c in graded:
        merged_sources.extend(c.evidence_sources or [])

    if all_agree:
        # Agreement -> promote to the max grade among contributors via bump_evidence.
        merged_grade: Optional[EvidenceGrade] = None
        for c in graded:
            if c.evidence_grade is not None:
                merged_grade = bump_evidence(merged_grade, c.evidence_grade)
        # Pick the contributor with the strongest grade as the value carrier.
        base = max(graded, key=lambda c: evidence_rank(c.evidence_grade))  # type: ignore[arg-type]
        basis = (
            f"Agreement across {len(graded)} sources; promoted to {merged_grade}"
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
        return MergedSignal(
            result=result,
            contributor_count=len(graded),
            disagreement=False,
        )

    # Disagreement path: take the MIN grade across graded contributors.
    min_grade = graded[0].evidence_grade
    for c in graded[1:]:
        if c.evidence_grade is not None and evidence_rank(c.evidence_grade) < evidence_rank(min_grade):  # type: ignore[arg-type]
            min_grade = c.evidence_grade

    scores = [c.score for c in graded if c.score is not None]
    cats = [c.category for c in graded if c.category is not None]
    median = sorted(scores)[len(scores) // 2] if scores else None

    if cats:
        chosen_cat = Counter(cats).most_common(1)[0][0]
        outvoted = [c for c in cats if c != chosen_cat]
    else:
        chosen_cat = None
        outvoted = []

    basis = (
        f"Disagreement across {len(graded)} sources; "
        f"took median/majority. Min grade applied."
    )[:500]
    if outvoted:
        counter = f"Outvoted: {outvoted}"[:500]
    elif scores:
        counter = f"Score spread {min(scores)}..{max(scores)} (n={len(scores)})"[:500]
    else:
        counter = "no consensus"

    result = SignalResult(
        signal_id=graded[0].signal_id,
        score=median,
        category=chosen_cat,
        confidence=min(c.confidence for c in graded),  # disagreement lowers confidence
        evidence_grade=min_grade,
        evidence_basis=basis,
        evidence_sources=merged_sources,
        evidence_counter=counter,
        metadata={
            "contributor_count": len(graded),
            "merged": True,
            "disagreement": True,
        },
    )
    return MergedSignal(
        result=result,
        contributor_count=len(graded),
        disagreement=True,
    )


# ---------------------------------------------------------------------------
# Group-level and composite-level rollup
# ---------------------------------------------------------------------------

@dataclass
class GradeRollup:
    """Group- or composite-level grade summary."""
    min_grade: Optional[EvidenceGrade]
    weighted_mean_grade: Optional[float]   # display only; do not threshold
    distribution: dict[EvidenceGrade, float] = field(default_factory=dict)  # weight-share at each grade

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
        - `absence_authoritative_empty` signals -- they carry a grade.
        - Every other graded signal.

    weighted_mean_grade is rendered as a 1.0..5.0 display value (rank+1).
    """
    items = [
        (s, w) for s, w in contributions
        if s.evidence_grade is not None
        and not s.skipped
        and s.error is None
        and getattr(s, "absence_sub_type", None) != "absence_failed_fetch"
    ]
    if not items:
        return GradeRollup(min_grade=None, weighted_mean_grade=None, distribution={})

    min_grade = items[0][0].evidence_grade
    total_weight = 0.0
    weighted_sum = 0.0
    dist_weights: dict[EvidenceGrade, float] = {g: 0.0 for g in EVIDENCE_GRADES}

    for sig, weight in items:
        g = sig.evidence_grade
        assert g is not None  # filtered above
        if evidence_rank(g) < evidence_rank(min_grade):  # type: ignore[arg-type]
            min_grade = g
        weighted_sum += evidence_rank(g) * weight
        total_weight += weight
        dist_weights[g] += weight

    mean_rank = weighted_sum / total_weight if total_weight > 0 else None
    distribution = {g: w / total_weight for g, w in dist_weights.items() if w > 0}
    # rank -> 1.0..5.0-style display value (rank 0 -> 1.0, rank 4 -> 5.0)
    weighted_mean_grade = mean_rank + 1.0 if mean_rank is not None else None

    return GradeRollup(
        min_grade=min_grade,
        weighted_mean_grade=weighted_mean_grade,
        distribution=distribution,
    )


def composite_rollup(group_rollups: Iterable[tuple[GradeRollup, float]]) -> GradeRollup:
    """Roll up multiple GroupRollups by group weight to a composite-level rollup."""
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
    """Tripwire for code that tries to threshold the scalar mean.

    Phase 4's referral evaluator calls this whenever something compares
    weighted_mean_grade to a number. Logs the cardinal-vs-ordinal pitfall
    without blocking the comparison; tests assert no production code path
    actually invokes it.
    """
    warnings.warn(
        f"{context}: thresholding weighted_mean_grade ({weighted_mean_grade}) "
        "uses cardinal arithmetic on an ordinal taxonomy. "
        "Prefer min_grade or distribution-share rules.",
        stacklevel=2,
    )

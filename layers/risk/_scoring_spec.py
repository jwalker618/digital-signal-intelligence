"""V6/E1 Stage 5.1 — Pure-function scoring spec.

This module isolates the mathematical core of composite scoring from
the I/O + extraction pipeline. The algorithm described here is the
reference specification for the Rust port (`rust/dsi-core/src/scoring.rs`
— Stage 5.2+).

Parity contract (Stage 5.4): for every golden fixture, the value
returned by `compute_composite` here MUST equal the value returned by
the Rust port to within 1e-9 absolute error. The parity CI job replays
1,000 fixtures and fails on any divergence exceeding that bound.

Design rules:
- Zero I/O. All inputs are plain dataclasses. Output is a plain
  dataclass. No logging, no network, no file reads, no Pydantic.
- Deterministic. Given identical inputs, output is identical across
  runs and across platforms. No time, no randomness, no dict-order
  dependence.
- Translatable. Every line maps 1:1 to a Rust statement. `for` loops
  iterate sorted keys; `float` is f64; integer counts are u32.

The Python reference below is the canonical definition. Any
disagreement between this file and `scorer.py:calculate_composite`
is a bug — `scorer.py` is expected to delegate to this module once
Stage 5.3's PyO3 wrapper lands.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


# --------------------------------------------------------------------
# Pure-function input / output dataclasses
# --------------------------------------------------------------------


@dataclass(frozen=True)
class SignalInput:
    """One scored signal feeding into the composite."""
    signal_id: str
    group_id: str
    raw_score: float           # [0, 100] — already clamped / validated upstream
    weight: float              # group-relative weight
    confidence: float          # [0, 1]
    populated: bool            # True iff the inference function succeeded


@dataclass(frozen=True)
class GroupWeight:
    """Group-level weight for one dimension (risk / loss / exposure)."""
    group_id: str
    risk_weight: float         # weight of this group in the risk dimension
    expected_signal_count: int # count of signals in signal_registry for this group


@dataclass(frozen=True)
class GroupScore:
    """Pure-function output per group."""
    group_id: str
    group_score: float         # weighted average of signal raw_scores
    risk_weight: float
    risk_contribution: float   # group_score * risk_weight * 10
    signal_count: int          # actual (after extraction)
    expected_signal_count: int
    coverage_ratio: float      # populated / expected


@dataclass(frozen=True)
class CompositeResult:
    """Pure-function output of `compute_composite`."""
    composite_score: float     # 0..1000
    group_scores: List[GroupScore]
    overall_confidence: float
    signal_coverage: float


# --------------------------------------------------------------------
# Configuration knobs (must match scorer.ModelScorer defaults)
# --------------------------------------------------------------------


DEFAULT_SCORE: float = 50.0         # neutral score for absent groups (matches scorer.ModelScorer)
DEFAULT_CONFIDENCE: float = 0.5
COMPOSITE_SCALE: float = 10.0       # group_score × weight × scale -> 0-1000 window


# --------------------------------------------------------------------
# Pure scoring function
# --------------------------------------------------------------------


def compute_composite(
    signals: List[SignalInput],
    group_weights: List[GroupWeight],
    default_score: float = DEFAULT_SCORE,
    default_confidence: float = DEFAULT_CONFIDENCE,
) -> CompositeResult:
    """Compute the pure composite score for one entity × coverage.

    Algorithm (must match `scorer.py::calculate_composite`):

      1. Bucket `signals` by `group_id`.
      2. For each group in `group_weights`:
         a. If group has at least one signal:
             group_score = Σ(s.raw_score × s.weight) / Σ(s.weight)
         b. Else:
             group_score = default_score
         c. risk_contribution = group_score × risk_weight × COMPOSITE_SCALE
      3. composite_score = Σ group_contributions.
      4. overall_confidence = Σ(group_avg_confidence × actual_count)
                              / Σ expected_count    (fallback default_confidence)
      5. signal_coverage    = Σ populated_count / Σ expected_count    (fallback 0.0)

    Iteration order: `group_weights` in-order (caller sorts if needed).
    Within-group order: signals in input order (caller sorts if needed).

    The `default_score` + `default_confidence` parameters mirror
    `ModelScorer.__init__` keyword arguments so PyO3 bindings can
    accept configurable defaults from Python callers.
    """
    # 1. bucket
    grouped: Dict[str, List[SignalInput]] = {}
    for s in signals:
        grouped.setdefault(s.group_id, []).append(s)

    out_groups: List[GroupScore] = []
    total_expected: int = 0
    total_populated: int = 0
    confidence_accumulator: float = 0.0

    for gw in group_weights:
        bucket = grouped.get(gw.group_id, [])
        actual_count = len(bucket)
        total_expected += gw.expected_signal_count

        if bucket:
            total_weighted = sum(s.raw_score * s.weight for s in bucket)
            total_weight = sum(s.weight for s in bucket)
            if total_weight > 0:
                group_score = total_weighted / total_weight
            else:
                group_score = default_score
            group_conf_avg = sum(s.confidence for s in bucket) / actual_count
            confidence_accumulator += group_conf_avg * actual_count
            populated_in_group = sum(1 for s in bucket if s.populated)
            total_populated += populated_in_group
        else:
            group_score = default_score
            populated_in_group = 0

        risk_contribution = group_score * gw.risk_weight * COMPOSITE_SCALE

        coverage_ratio = (
            populated_in_group / gw.expected_signal_count
            if gw.expected_signal_count > 0
            else 0.0
        )

        out_groups.append(GroupScore(
            group_id=gw.group_id,
            group_score=group_score,
            risk_weight=gw.risk_weight,
            risk_contribution=risk_contribution,
            signal_count=actual_count,
            expected_signal_count=gw.expected_signal_count,
            coverage_ratio=coverage_ratio,
        ))

    composite = sum(g.risk_contribution for g in out_groups)

    if total_expected > 0:
        overall_conf = confidence_accumulator / total_expected
        coverage = total_populated / total_expected
    else:
        overall_conf = default_confidence
        coverage = 0.0

    return CompositeResult(
        composite_score=composite,
        group_scores=out_groups,
        overall_confidence=overall_conf,
        signal_coverage=coverage,
    )


__all__ = [
    "SignalInput",
    "GroupWeight",
    "GroupScore",
    "CompositeResult",
    "compute_composite",
    "DEFAULT_SCORE",
    "DEFAULT_CONFIDENCE",
    "COMPOSITE_SCALE",
]

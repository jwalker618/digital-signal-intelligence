"""
WE-2a: Consistency Scorer

Computes cross-signal and cross-layer consistency for a single assessment.
Three components with weighted aggregation (phase WE-2 spec):

1. Signal-pair consistency (weight 0.3): pairwise score agreement within
   each signal group. Signals in the same group share a design intent;
   disagreement beyond a threshold is informative.
2. Cross-group consistency  (weight 0.4): agreement between group-level
   composites. Independent groups agreeing is strong evidence of
   correctness -- this carries the highest weight.
3. Cross-layer consistency  (weight 0.3): do risk / loss / exposure
   tiers tell a coherent story? Divergence can be legitimate (current
   state vs. forward trajectory) but it must be surfaced.

Implementation is fully vectorised via numpy -- target latency is well
under the <50ms budget even for 400+ signals.

The scorer is decoupled from the workflow types: callers construct a
ConsistencyInputs object from whatever data sources they have. This
makes the scorer trivial to unit-test and independent of workflow
refactors.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

import numpy as np

from world_engine.types import ConsistencyScore


# Score normalisation: internal signal scores are 0-100.
_SCORE_SCALE = 100.0

# Pair-level consistency threshold -- below this the pair is "divergent".
# Expressed in 0-1 consistency space where 1 = perfect agreement.
_DIVERGENT_THRESHOLD = 0.5

# Weights per phase doc (must sum to 1.0)
WEIGHTS = {"signal_pair": 0.3, "cross_group": 0.4, "cross_layer": 0.3}


# =============================================================================
# Input types
# =============================================================================


@dataclass
class SignalScore:
    """A single signal's score and its group membership."""

    signal_id: str
    group_id: str
    raw_score: float  # 0-100


@dataclass
class ConsistencyInputs:
    """All inputs required to compute consistency for an assessment.

    Callers (the workflow, tests, the seed script) construct this explicitly
    from whatever data they have.  Any missing fields simply skip that
    component -- overall consistency is recalculated with renormalised
    weights so partial data still yields a useful score.
    """

    entity_id: str
    assessment_id: str
    signals: list[SignalScore] = field(default_factory=list)
    group_composites: dict[str, float] = field(default_factory=dict)
    risk_tier: Optional[int] = None
    loss_tier: Optional[int] = None
    exposure_tier: Optional[int] = None
    max_tier: int = 5  # tier count; used to normalise cross-layer gaps


# =============================================================================
# ConsistencyScorer
# =============================================================================


class ConsistencyScorer:
    """Computes intra-assessment consistency metrics.

    Construction is zero-cost; call score() per assessment.
    """

    def __init__(self, divergent_threshold: float = _DIVERGENT_THRESHOLD):
        self.divergent_threshold = divergent_threshold

    def score(self, inputs: ConsistencyInputs) -> ConsistencyScore:
        """Compute a ConsistencyScore for the given inputs."""
        signal_pair_scores, divergent_pairs, signal_pair_component = self._signal_pair(inputs.signals)
        cross_group_scores, cross_group_component = self._cross_group(inputs.group_composites)
        cross_layer_divergence, cross_layer_component = self._cross_layer(
            inputs.risk_tier, inputs.loss_tier, inputs.exposure_tier, inputs.max_tier
        )

        # Dynamic weight renormalisation: drop components that could not be
        # computed (None) so the final score stays in [0, 1].
        parts: dict[str, float] = {}
        if signal_pair_component is not None:
            parts["signal_pair"] = signal_pair_component
        if cross_group_component is not None:
            parts["cross_group"] = cross_group_component
        if cross_layer_component is not None:
            parts["cross_layer"] = cross_layer_component

        if parts:
            w_total = sum(WEIGHTS[k] for k in parts)
            overall = sum(WEIGHTS[k] * v for k, v in parts.items()) / w_total
        else:
            overall = 1.0  # No data -> nothing to disagree with

        return ConsistencyScore(
            entity_id=inputs.entity_id,
            assessment_id=inputs.assessment_id,
            overall_consistency=float(np.clip(overall, 0.0, 1.0)),
            signal_pair_scores=signal_pair_scores,
            cross_group_scores=cross_group_scores,
            cross_layer_divergence=cross_layer_divergence,
            divergent_pairs=divergent_pairs,
            computed_at=datetime.now(timezone.utc),
        )

    # ------------------------------------------------------------------
    # Component 1: signal-pair consistency (within group)
    # ------------------------------------------------------------------

    def _signal_pair(
        self, signals: list[SignalScore]
    ) -> tuple[dict[str, float], list[str], Optional[float]]:
        """Pairwise agreement within each signal group.

        For each group, compute the average pairwise consistency:
            consistency(a, b) = 1 - |score_a - score_b| / 100
        Overall component = unweighted mean across all in-group pairs.
        Returns per-pair map, divergent-pair list, and the component score.
        """
        # Group signals by group_id
        grouped: dict[str, list[SignalScore]] = {}
        for s in signals:
            grouped.setdefault(s.group_id, []).append(s)

        pair_scores: dict[str, float] = {}
        divergent: list[str] = []
        component_values: list[float] = []

        for group_id, group_signals in grouped.items():
            if len(group_signals) < 2:
                continue  # need at least 2 signals to compute a pair

            # Vectorised pairwise distance matrix
            scores = np.array([s.raw_score for s in group_signals], dtype=float)
            # Upper triangle indices (exclude diagonal)
            n = len(scores)
            i, j = np.triu_indices(n, k=1)
            distances = np.abs(scores[i] - scores[j]) / _SCORE_SCALE
            pair_consistencies = 1.0 - distances

            for idx, consistency in zip(range(len(i)), pair_consistencies):
                a = group_signals[int(i[idx])].signal_id
                b = group_signals[int(j[idx])].signal_id
                # Stable key (sorted)
                key = "|".join(sorted([a, b]))
                pair_scores[key] = float(consistency)
                if consistency < self.divergent_threshold:
                    divergent.append(key)
                component_values.append(float(consistency))

        if not component_values:
            return pair_scores, divergent, None

        return pair_scores, divergent, float(np.mean(component_values))

    # ------------------------------------------------------------------
    # Component 2: cross-group consistency (between independent groups)
    # ------------------------------------------------------------------

    def _cross_group(
        self, group_composites: dict[str, float]
    ) -> tuple[dict[str, float], Optional[float]]:
        """Agreement between group-level composite scores.

        Higher consistency = groups with independent data sources tell
        the same story. This is the highest-weighted component because
        agreement across independent groups is very strong evidence.

        We compute all pairwise group-composite consistencies.
        """
        if len(group_composites) < 2:
            return {}, None

        keys = sorted(group_composites.keys())
        values = np.array([group_composites[k] for k in keys], dtype=float)

        # Normalise: if values are 0-1000 composite scores, rescale to 0-100.
        # Heuristic: if any value exceeds 100 we assume the 0-1000 scale.
        if values.max() > 100.0:
            values = values / 10.0

        n = len(values)
        i, j = np.triu_indices(n, k=1)
        distances = np.abs(values[i] - values[j]) / _SCORE_SCALE
        pair_consistencies = 1.0 - distances

        pair_map: dict[str, float] = {}
        for idx, consistency in zip(range(len(i)), pair_consistencies):
            key = f"{keys[int(i[idx])]}|{keys[int(j[idx])]}"
            pair_map[key] = float(consistency)

        return pair_map, float(np.mean(pair_consistencies))

    # ------------------------------------------------------------------
    # Component 3: cross-layer consistency (risk vs loss vs exposure)
    # ------------------------------------------------------------------

    def _cross_layer(
        self,
        risk_tier: Optional[int],
        loss_tier: Optional[int],
        exposure_tier: Optional[int],
        max_tier: int,
    ) -> tuple[dict, Optional[float]]:
        """Divergence between the three-layer tier assignments.

        For each pair we compute:
            consistency = 1 - |tier_a - tier_b| / max_tier
        An entity that is Tier 1 on risk but Tier 4 on loss has a large
        cross-layer gap -- informative, not necessarily wrong.

        Output fields mirror the phase spec:
            risk_vs_loss, risk_vs_exposure, loss_vs_exposure
        """
        pairs: dict[str, tuple[Optional[int], Optional[int]]] = {
            "risk_vs_loss": (risk_tier, loss_tier),
            "risk_vs_exposure": (risk_tier, exposure_tier),
            "loss_vs_exposure": (loss_tier, exposure_tier),
        }

        divergence: dict[str, float] = {}
        consistencies: list[float] = []
        scale = max(1, max_tier)

        for key, (a, b) in pairs.items():
            if a is None or b is None:
                continue
            gap = abs(a - b) / scale
            consistency = float(np.clip(1.0 - gap, 0.0, 1.0))
            divergence[key] = consistency
            consistencies.append(consistency)

        if not consistencies:
            return {}, None

        return divergence, float(np.mean(consistencies))

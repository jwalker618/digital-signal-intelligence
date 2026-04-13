"""
WE-4a (part 2): TrajectoryEngine

Synthesises forward risk trajectory from precursor evaluations. Each
active precursor contributes an implied probability that the entity's
composite score will degrade; the trajectory engine combines these
contributions into a probability distribution over tier migrations.

Method (deterministic, no ML training):

1. Each PrecursorEvaluation says: "signal X is in the precursor state,
   which implies a P(y) probability that signal Y will degrade by some
   amount within `lag_months`."

2. We aggregate across all active precursors using probability-union
   logic (assumption: precursors are conditionally independent -- this
   is the assumption of the lifecycle manager when admitting multiple
   simultaneous relationships).

    P(any_target_degrades) = 1 - Π(1 - P_i)

3. Map P(degradation) to tier migration probabilities using a simple
   monotone function anchored to the current tier. Deeper degradation
   = more likely to migrate one or more tiers. We assume a smooth
   distribution: the probability of migrating k tiers decays
   geometrically.

4. The TierMigrationDistribution is normalised to sum to 1 and has a
   clear "expected_tier" (probability-weighted mean tier).

This is intentionally a simple, auditable model. More sophisticated
learned mappings can replace it without changing the interface.
"""

from __future__ import annotations

import logging
from typing import Iterable

import numpy as np

from world_engine.types import PrecursorEvaluation, TierMigrationDistribution

logger = logging.getLogger("dsi.world_engine.causal_pricing.trajectory")


# Geometric decay for multi-tier migration probability given aggregate degradation.
# probability(migrate k tiers) ∝ MIGRATION_DECAY ** k
MIGRATION_DECAY: float = 0.35

# At aggregate probability of 1.0 (certain degradation), how much of the mass
# moves to the WORSE tier(s) vs staying? At 1.0 we commit at most this fraction.
# Keeps the engine conservative even under overwhelming precursor evidence.
MAX_MOVE_FRACTION: float = 0.90


class TrajectoryEngine:
    """Synthesises tier migration probabilities from precursor evaluations."""

    def compute_trajectory(
        self,
        precursors: Iterable[PrecursorEvaluation],
        current_tier: int,
        tier_rates: dict[int, float],
        policy_period_months: int = 12,
    ) -> TierMigrationDistribution:
        """Combine precursor evaluations into a tier migration distribution.

        Args:
            precursors: iterable of PrecursorEvaluation.
            current_tier: the entity's score-derived tier (1 = best).
            tier_rates: {tier_id: rate} for CAF calculation downstream.
            policy_period_months: the trajectory horizon.

        Returns:
            TierMigrationDistribution with `probabilities` summing to 1.0.
        """
        precursors = list(precursors)

        if not tier_rates:
            # No tier structure available -- return a neutral trajectory
            return TierMigrationDistribution(
                current_tier=current_tier,
                probabilities={current_tier: 1.0},
                expected_tier=float(current_tier),
                policy_period_months=policy_period_months,
            )

        # Aggregate precursor-implied degradation probability
        aggregate_p = self._aggregate_probability(precursors)
        aggregate_p = min(aggregate_p * MAX_MOVE_FRACTION, MAX_MOVE_FRACTION)

        # Distribute probability mass across accessible tiers
        probabilities = self._distribute_mass(
            aggregate_p=aggregate_p,
            current_tier=current_tier,
            tier_ids=sorted(tier_rates.keys()),
        )

        expected = sum(t * p for t, p in probabilities.items())

        return TierMigrationDistribution(
            current_tier=current_tier,
            probabilities=probabilities,
            expected_tier=float(expected),
            policy_period_months=policy_period_months,
        )

    # ------------------------------------------------------------------
    # Aggregate implied degradation probability
    # ------------------------------------------------------------------

    def _aggregate_probability(self, precursors: list[PrecursorEvaluation]) -> float:
        """Combine individual precursor probabilities via probability union."""
        if not precursors:
            return 0.0

        # Weighted by how far into the precursor state the entity is.
        # distance_from_threshold is in the same units as the signal score;
        # we map it into [0, 1] via a saturating function.
        weights: list[float] = []
        for p in precursors:
            distance = max(0.0, float(p.distance_from_threshold))
            # saturating logistic-style weight
            w = 1.0 - np.exp(-distance / 20.0)
            weights.append(float(np.clip(w, 0.0, 1.0)))

        effective_probs = [
            float(p.implied_probability) * w for p, w in zip(precursors, weights)
        ]

        # 1 - Π(1 - p_i)  (assumes conditional independence)
        product = 1.0
        for p in effective_probs:
            product *= max(0.0, min(1.0, 1.0 - p))
        return 1.0 - product

    # ------------------------------------------------------------------
    # Distribute probability mass across tiers
    # ------------------------------------------------------------------

    def _distribute_mass(
        self,
        aggregate_p: float,
        current_tier: int,
        tier_ids: list[int],
    ) -> dict[int, float]:
        """Probability-weighted distribution over accessible tiers.

        The staying probability = 1 - aggregate_p.
        The moving probability = aggregate_p, distributed geometrically
        over worse tiers (higher tier number = worse in DSI convention).

        Note: a small amount of mass may also spread to BETTER tiers when
        aggregate_p is very small, to recognise that the causal graph
        occasionally finds reasons to upgrade. This is gated by the
        absence of precursors (no precursors -> aggregate_p=0 -> all
        mass stays at current_tier).
        """
        if current_tier not in tier_ids:
            # Edge case: current tier not in the known tier list. Keep all
            # mass on the current tier so we never invent probabilities for
            # tiers we can't price.
            return {current_tier: 1.0}

        worse_tiers = [t for t in tier_ids if t > current_tier]
        better_tiers = [t for t in tier_ids if t < current_tier]

        staying = max(0.0, 1.0 - aggregate_p)
        moving = aggregate_p

        probabilities: dict[int, float] = {current_tier: staying}

        # Geometric allocation to worse tiers: first hop gets most mass
        if worse_tiers and moving > 0:
            weights = np.array([MIGRATION_DECAY ** i for i in range(len(worse_tiers))])
            weights /= weights.sum()
            for tier, w in zip(worse_tiers, weights):
                probabilities[tier] = float(moving * w)

        # If no precursors (moving == 0), we stay at current_tier with p=1.
        # We don't redistribute mass to better tiers without positive evidence.
        for t in better_tiers:
            probabilities[t] = 0.0

        # Normalise in case of floating-point drift
        total = sum(probabilities.values())
        if total > 0:
            for t in probabilities:
                probabilities[t] = probabilities[t] / total

        return probabilities

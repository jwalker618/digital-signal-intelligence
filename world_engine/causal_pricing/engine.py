"""
WE-4a: CausalPricingEngine

Computes the Causal Adjustment Factor (CAF) for an entity assessment.

Flow:
1. Check maturity gate -- at SEED/LEARN, always neutral (CAF=1.0).
2. Query registry for active relationships touching the entity's signals.
3. Evaluate precursor state per relationship (entity's value vs threshold).
4. If fewer than min_relationships match or aggregate confidence < gate,
   return neutral CAF.
5. Synthesise tier migration trajectory via TrajectoryEngine.
6. Compute raw CAF as the probability-weighted rate ratio.
7. Apply the active ConstraintRegime (floor/cap) -- record whether the
   constraint bound was hit.

The engine is stateless and side-effect-free -- it only reads the registry
and returns a CausalAdjustmentFactor. Persistence is the caller's
responsibility (the workflow calls `registry.store_caf(...)`).

Defaults to `CausalAdjustmentFactor.neutral(...)` on any exception.
"""

from __future__ import annotations

import logging
import statistics
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import text

from world_engine.causal_pricing.constraints import (
    ABSOLUTE_CONFIDENCE_MIN,
    ConstraintCalibrator,
    ConstraintRegime,
)
from world_engine.causal_pricing.trajectory import TrajectoryEngine
from world_engine.maturity import MaturityEvaluator
from world_engine.registry import IntelligenceRegistry
from world_engine.types import (
    CausalAdjustmentFactor,
    DiscoveredRelationship,
    MaturityStage,
    PrecursorEvaluation,
)

logger = logging.getLogger("dsi.world_engine.causal_pricing.engine")


class CausalPricingEngine:
    """Computes the Causal Adjustment Factor for an entity assessment."""

    def __init__(
        self,
        registry: IntelligenceRegistry,
        trajectory_engine: Optional[TrajectoryEngine] = None,
        maturity_evaluator: Optional[MaturityEvaluator] = None,
    ):
        self.registry = registry
        self.db = registry.db
        self.trajectory_engine = trajectory_engine or TrajectoryEngine()
        self.maturity_evaluator = maturity_evaluator or MaturityEvaluator()
        self._regime_cache: Optional[ConstraintRegime] = None

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    def compute_caf(
        self,
        entity_id: str,
        assessment_id: str,
        signal_scores: dict[str, float],
        current_tier: int,
        tier_rates: dict[int, float],
        policy_period_months: int = 12,
    ) -> CausalAdjustmentFactor:
        """Compute CAF for a single assessment.

        Returns a CausalAdjustmentFactor; neutral (CAF=1.0) when maturity,
        matching relationships, or confidence gates fail.
        """
        try:
            # 1. Maturity gate
            maturity = self.maturity_evaluator.evaluate(self.db)
            if not maturity.capabilities.get("caf", False):
                logger.debug(
                    "CAF neutral: maturity %s does not unlock CAF", maturity.stage.value
                )
                return CausalAdjustmentFactor.neutral(
                    entity_id=entity_id,
                    assessment_id=assessment_id,
                    current_tier=current_tier,
                    policy_period_months=policy_period_months,
                )

            # 2. Read active constraint regime
            regime = self._active_regime()

            # 3. Find matching active relationships
            active = self.registry.get_active_relationships(
                signal_ids=list(signal_scores.keys())
            )
            if not active:
                return CausalAdjustmentFactor.neutral(
                    entity_id=entity_id,
                    assessment_id=assessment_id,
                    current_tier=current_tier,
                    policy_period_months=policy_period_months,
                )

            # 4. Evaluate precursor state for each active relationship
            precursors = self._evaluate_precursors(active, signal_scores)

            # 5. Relationship count gate
            if len(precursors) < regime.min_relationships:
                return CausalAdjustmentFactor.neutral(
                    entity_id=entity_id,
                    assessment_id=assessment_id,
                    current_tier=current_tier,
                    policy_period_months=policy_period_months,
                )

            # 6. Aggregate confidence = weighted mean of (influence_weight * predictive_hit_rate)
            confidence = self._aggregate_confidence(active, precursors)
            if confidence < max(regime.confidence_gate, ABSOLUTE_CONFIDENCE_MIN):
                logger.debug(
                    "CAF neutral: confidence %.2f below gate %.2f",
                    confidence,
                    regime.confidence_gate,
                )
                return CausalAdjustmentFactor.neutral(
                    entity_id=entity_id,
                    assessment_id=assessment_id,
                    current_tier=current_tier,
                    policy_period_months=policy_period_months,
                )

            # 7. Synthesise trajectory
            trajectory = self.trajectory_engine.compute_trajectory(
                precursors=precursors,
                current_tier=current_tier,
                tier_rates=tier_rates,
                policy_period_months=policy_period_months,
            )

            # 8. Compute raw CAF = Σ P(tier) * (Rate_tier / Rate_current)
            current_rate = tier_rates.get(current_tier, 0.0)
            if current_rate <= 0:
                return CausalAdjustmentFactor.neutral(
                    entity_id=entity_id,
                    assessment_id=assessment_id,
                    current_tier=current_tier,
                    policy_period_months=policy_period_months,
                )

            raw_caf = 0.0
            for tier, prob in trajectory.probabilities.items():
                rate = tier_rates.get(tier, current_rate)
                raw_caf += prob * (rate / current_rate)

            # 9. Apply constraint regime
            final_caf, constrained = regime.clamp(raw_caf)

            return CausalAdjustmentFactor(
                entity_id=entity_id,
                assessment_id=assessment_id,
                caf_value=float(final_caf),
                confidence=float(confidence),
                active_precursors=precursors,
                trajectory=trajectory,
                relationships_evaluated=len(precursors),
                constrained=bool(constrained),
                raw_caf=float(raw_caf),
                constraint_regime=regime.regime_name,
                computed_at=datetime.now(timezone.utc),
            )

        except Exception as exc:  # noqa: BLE001
            logger.exception("CAF computation failed -- returning neutral: %s", exc)
            return CausalAdjustmentFactor.neutral(
                entity_id=entity_id,
                assessment_id=assessment_id,
                current_tier=current_tier,
                policy_period_months=policy_period_months,
            )

    # ------------------------------------------------------------------
    # Precursor evaluation
    # ------------------------------------------------------------------

    def _evaluate_precursors(
        self,
        active: list[DiscoveredRelationship],
        signal_scores: dict[str, float],
    ) -> list[PrecursorEvaluation]:
        """For each matching active relationship, evaluate whether the
        entity is in a precursor state.

        Precursor threshold = population 25th percentile of the source signal.
        This is the same quantile used by PredictiveValidator. We load these
        thresholds lazily from the assessment database.
        """
        evaluations: list[PrecursorEvaluation] = []

        # Collect unique source signals we actually need thresholds for
        source_signals_needed = {
            rel.source_signal for rel in active if rel.source_signal in signal_scores
        }
        thresholds = self._load_precursor_thresholds(list(source_signals_needed))

        for rel in active:
            src_value = signal_scores.get(rel.source_signal)
            if src_value is None:
                continue
            threshold = thresholds.get(rel.source_signal)
            if threshold is None:
                continue

            # Precursor = source signal BELOW the low quantile
            if src_value > threshold:
                continue

            distance = threshold - src_value  # positive = deeper into precursor
            # Implied probability = relationship's predictive hit rate,
            # scaled by how deep into precursor the entity is. If the
            # relationship lacks a recorded hit rate (e.g. PROVISIONAL),
            # fall back to its correlation magnitude as a weaker proxy.
            base_p = (
                rel.predictive_hit_rate
                if rel.predictive_hit_rate is not None
                else abs(rel.correlation_rho) * 0.7
            )
            implied_p = max(0.0, min(1.0, float(base_p)))

            evaluations.append(
                PrecursorEvaluation(
                    relationship_id=rel.id,
                    precursor_signal=rel.source_signal,
                    entity_value=float(src_value),
                    threshold=float(threshold),
                    distance_from_threshold=float(distance),
                    implied_probability=implied_p,
                    lag_months=float(rel.lag_months or 0.0),
                )
            )

        return evaluations

    def _load_precursor_thresholds(
        self, signal_codes: list[str]
    ) -> dict[str, float]:
        """For each signal, compute the 25th percentile of observed scores."""
        if not signal_codes:
            return {}

        sql = """
            SELECT sig.code AS signal_code,
                   PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY mvs.score) AS threshold
            FROM model_version_signals mvs
            JOIN signals sig ON sig.id = mvs.signal_id
            WHERE sig.code = ANY(:codes) AND mvs.score IS NOT NULL
            GROUP BY sig.code
        """
        try:
            rows = self.db.execute(text(sql), {"codes": signal_codes}).mappings().all()
            return {
                row["signal_code"]: float(row["threshold"])
                for row in rows
                if row["threshold"] is not None
            }
        except Exception:
            return {}

    # ------------------------------------------------------------------
    # Confidence aggregation
    # ------------------------------------------------------------------

    def _aggregate_confidence(
        self,
        active: list[DiscoveredRelationship],
        precursors: list[PrecursorEvaluation],
    ) -> float:
        """Aggregate confidence = weighted mean of influence_weight across
        the relationships that matched a precursor."""
        if not precursors:
            return 0.0
        rel_by_id = {r.id: r for r in active}
        weights: list[float] = []
        for p in precursors:
            rel = rel_by_id.get(p.relationship_id)
            if rel is None:
                continue
            # Use hit rate if available, otherwise influence_weight
            if rel.predictive_hit_rate is not None:
                weights.append(float(rel.predictive_hit_rate))
            else:
                weights.append(float(rel.influence_weight or 0.5))

        if not weights:
            return 0.0
        return statistics.mean(weights)

    # ------------------------------------------------------------------
    # Regime caching
    # ------------------------------------------------------------------

    def _active_regime(self) -> ConstraintRegime:
        """Read the active regime once per engine lifetime (or until reset).

        Workflows create a fresh engine per request, so this effectively
        reads once per assessment and is cheap.
        """
        if self._regime_cache is None:
            self._regime_cache = ConstraintCalibrator(self.db).get_active_regime()
        return self._regime_cache

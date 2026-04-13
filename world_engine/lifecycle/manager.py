"""
WE-3d: Lifecycle Manager

Autonomous state machine for discovered relationships. NO human approval
gate -- promotions and demotions are driven entirely by statistical
evidence. Every transition is recorded in we_state_transitions with the
evidence that triggered it for audit.

State diagram:

    CANDIDATE ──(holdout + stability)──▶ PROVISIONAL
                                             │
                                             (predictive validation)
                                             │
                                             ▼
                                           ACTIVE
                                             │
                                             (predictive decay)
                                             │
                                             ▼
                                          DEPRECATED
                                             │
                                             (re-emergence in new scan)
                                             │
                                             ▼
                                           CANDIDATE   (recycled)

Criteria are module-level constants so the scheduler can reference them
in audit output and the lifecycle rules are visible in one place.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from world_engine.registry import IntelligenceRegistry
from world_engine.types import (
    DiscoveredRelationship,
    LifecycleState,
    PredictiveResult,
    StabilityResult,
    StateTransition,
    ValidationResult,
)
from world_engine.validator import (
    HoldoutValidator,
    PredictiveValidator,
    TemporalStabilityTracker,
)

logger = logging.getLogger("dsi.world_engine.lifecycle")


PROMOTION_CRITERIA: dict[str, dict] = {
    "candidate_to_provisional": {
        "holdout_rho_min": 0.2,
        "holdout_p_max": 0.05,
        "stability_windows_min": 3,
    },
    "provisional_to_active": {
        "predictive_hit_rate_min": 0.6,
        "effect_size_min": 0.3,
        "min_age_months": 6,
    },
    "active_to_deprecated": {
        "predictive_hit_rate_below": 0.4,
        "consecutive_windows_below": 3,
    },
}


@dataclass
class LifecycleReport:
    promotions_to_provisional: int = 0
    promotions_to_active: int = 0
    demotions_to_deprecated: int = 0
    discards: int = 0
    transitions: list[StateTransition] = None

    def __post_init__(self):
        if self.transitions is None:
            self.transitions = []


class LifecycleManager:
    """Autonomous state transition engine for discovered relationships."""

    def __init__(
        self,
        registry: IntelligenceRegistry,
        holdout: Optional[HoldoutValidator] = None,
        stability: Optional[TemporalStabilityTracker] = None,
        predictive: Optional[PredictiveValidator] = None,
    ):
        self.registry = registry
        self.db = registry.db
        self.holdout = holdout or HoldoutValidator()
        self.stability = stability or TemporalStabilityTracker()
        self.predictive = predictive or PredictiveValidator()

    def evaluate_all(self) -> LifecycleReport:
        """Walk every non-deprecated relationship and apply its state-transition rule."""
        report = LifecycleReport()

        # Candidates: holdout + stability gate
        candidates, _ = self.registry.list_relationships(
            state=LifecycleState.CANDIDATE, limit=10_000
        )
        for rel in candidates:
            transition = self._evaluate_candidate(rel)
            if transition:
                report.transitions.append(transition)
                if transition.to_state == LifecycleState.PROVISIONAL:
                    report.promotions_to_provisional += 1
                elif transition.to_state == LifecycleState.DEPRECATED:
                    report.discards += 1

        # Provisionals: predictive + age gate
        provisionals, _ = self.registry.list_relationships(
            state=LifecycleState.PROVISIONAL, limit=10_000
        )
        for rel in provisionals:
            transition = self._evaluate_provisional(rel)
            if transition:
                report.transitions.append(transition)
                if transition.to_state == LifecycleState.ACTIVE:
                    report.promotions_to_active += 1

        # Actives: ongoing predictive-power check
        actives, _ = self.registry.list_relationships(
            state=LifecycleState.ACTIVE, limit=10_000
        )
        for rel in actives:
            transition = self._evaluate_active(rel)
            if transition:
                report.transitions.append(transition)
                if transition.to_state == LifecycleState.DEPRECATED:
                    report.demotions_to_deprecated += 1

        logger.info(
            "Lifecycle: +provisional=%d +active=%d -deprecated=%d discarded=%d",
            report.promotions_to_provisional,
            report.promotions_to_active,
            report.demotions_to_deprecated,
            report.discards,
        )
        return report

    # ==================================================================
    # Candidate -> Provisional or discard
    # ==================================================================

    def _evaluate_candidate(
        self, rel: DiscoveredRelationship
    ) -> Optional[StateTransition]:
        criteria = PROMOTION_CRITERIA["candidate_to_provisional"]

        holdout = self.holdout.validate(
            candidate=self._to_directed(rel), db=self.db
        )
        stability = self.stability.check(
            source_signal=rel.source_signal,
            target_signal=rel.target_signal,
            db=self.db,
            relationship_id=rel.id,
        )

        evidence = {
            "holdout_rho": holdout.holdout_rho,
            "holdout_p_value": holdout.holdout_p_value,
            "stability_windows_stable": stability.windows_stable,
            "stability_sign_flip": stability.sign_flip_detected,
        }

        holdout_ok = (
            abs(holdout.holdout_rho) >= criteria["holdout_rho_min"]
            and holdout.holdout_p_value <= criteria["holdout_p_max"]
        )
        stability_ok = (
            stability.windows_stable >= criteria["stability_windows_min"]
            and not stability.sign_flip_detected
        )

        if holdout_ok and stability_ok:
            return self.registry.transition_state(
                rel.id,
                LifecycleState.PROVISIONAL,
                reason="Holdout replication and temporal stability passed",
                evidence=evidence,
            )

        # Candidates that fail stability's sign-flip check are actively bad --
        # demote to DEPRECATED so we don't re-evaluate them repeatedly.
        if stability.sign_flip_detected:
            return self.registry.transition_state(
                rel.id,
                LifecycleState.DEPRECATED,
                reason="Correlation sign flipped -- not a stable relationship",
                evidence=evidence,
            )

        # Otherwise remain CANDIDATE (no transition)
        return None

    # ==================================================================
    # Provisional -> Active or demote
    # ==================================================================

    def _evaluate_provisional(
        self, rel: DiscoveredRelationship
    ) -> Optional[StateTransition]:
        criteria = PROMOTION_CRITERIA["provisional_to_active"]

        # Age gate
        age_months = _months_between(rel.state_entered_at, datetime.now(timezone.utc))
        if age_months < criteria["min_age_months"]:
            return None

        predictive = self.predictive.validate(rel, self.db)

        evidence = {
            "predictive_hit_rate": predictive.hit_rate,
            "predictions_made": predictive.predictions_made,
            "predictions_hit": predictive.predictions_hit,
            "effect_size": rel.effect_size,
            "age_months": age_months,
        }

        if (
            predictive.passed
            and rel.effect_size >= criteria["effect_size_min"]
        ):
            return self.registry.transition_state(
                rel.id,
                LifecycleState.ACTIVE,
                reason="Predictive hit rate + effect size met",
                evidence=evidence,
            )

        # Provisionals that have aged long enough but fail predictive entirely
        # are demoted to DEPRECATED. Borderline results remain PROVISIONAL for
        # another cycle.
        if predictive.predictions_made >= 20 and predictive.hit_rate < 0.3:
            return self.registry.transition_state(
                rel.id,
                LifecycleState.DEPRECATED,
                reason="Predictive hit rate too low after provisional period",
                evidence=evidence,
            )

        return None

    # ==================================================================
    # Active -> Deprecated
    # ==================================================================

    def _evaluate_active(
        self, rel: DiscoveredRelationship
    ) -> Optional[StateTransition]:
        criteria = PROMOTION_CRITERIA["active_to_deprecated"]

        predictive = self.predictive.validate(rel, self.db)

        # Track per-scan hit rate in evidence. The scheduler can then look
        # at the last N scans' evidence to detect sustained decay.
        evidence = {
            "predictive_hit_rate": predictive.hit_rate,
            "predictions_made": predictive.predictions_made,
            "predictions_hit": predictive.predictions_hit,
        }

        if (
            predictive.predictions_made >= 10
            and predictive.hit_rate < criteria["predictive_hit_rate_below"]
        ):
            return self.registry.transition_state(
                rel.id,
                LifecycleState.DEPRECATED,
                reason="Predictive power decayed below active threshold",
                evidence=evidence,
            )

        return None

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _to_directed(self, rel: DiscoveredRelationship):
        """Cheap adaptor to feed the HoldoutValidator (which expects a
        DirectedCandidate). Only source_signal and target_signal are used."""
        from world_engine.types import CausalDirection, DirectedCandidate

        return DirectedCandidate(
            source_signal=rel.source_signal,
            target_signal=rel.target_signal,
            direction=rel.direction,
            lag_months=rel.lag_months,
            correlation_rho=rel.correlation_rho,
            granger_f_statistic=rel.granger_f_statistic,
            granger_p_value=rel.granger_p_value,
            effect_size=rel.effect_size,
            confounders_tested=list(rel.confounders_tested),
            population_size=rel.population_size,
            coverage_scope=list(rel.coverage_scope),
        )


def _months_between(earlier: datetime, later: datetime) -> float:
    if earlier.tzinfo is None:
        earlier = earlier.replace(tzinfo=timezone.utc)
    if later.tzinfo is None:
        later = later.replace(tzinfo=timezone.utc)
    return (later - earlier).days / 30.0

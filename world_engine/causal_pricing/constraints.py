"""
WE-4b: CAF Constraint Regime + Calibrator

Hard guardrails that CANNOT be breached by any autonomous process:

    ABSOLUTE_FLOOR         = 0.60   # max 40% credit
    ABSOLUTE_CAP           = 2.00   # max 100% loading
    ABSOLUTE_CONFIDENCE_MIN = 0.4   # minimum confidence to apply any CAF

These are code constants. They are immutable. The autonomous
ConstraintCalibrator can widen the *active* constraints within these
bounds as predictive accuracy accumulates, but never beyond them.

Active constraints are read from we_constraint_history (effective_to IS NULL
= currently active). Migration 011 seeds the initial regime:
    floor=0.80, cap=1.50, confidence_gate=0.6, min_relationships=2

Widening is gradual and backtested. Every change is recorded with the
evidence that triggered it.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

logger = logging.getLogger("dsi.world_engine.causal_pricing.constraints")


# Hard guardrails -- immutable, never breached by any autonomous process.
ABSOLUTE_FLOOR: float = 0.60
ABSOLUTE_CAP: float = 2.00
ABSOLUTE_CONFIDENCE_MIN: float = 0.4


# Initial constraint values at launch (seeded by migration 011).
INITIAL_FLOOR: float = 0.80
INITIAL_CAP: float = 1.50
INITIAL_CONFIDENCE_GATE: float = 0.6
INITIAL_MIN_RELATIONSHIPS: int = 2


# Widening step sizes -- gradual, reversible.
FLOOR_STEP: float = 0.05
CAP_STEP: float = 0.10


# Widening criteria -- every threshold must be met to propose widening.
WIDENING_CRITERIA: dict = {
    "min_active_relationships": 10,
    "min_predictive_accuracy": 0.70,
    "min_evaluation_months": 12,
    "min_caf_evaluations": 500,
    "max_constraint_hit_rate": 0.25,
}


@dataclass
class ConstraintRegime:
    """Snapshot of the currently-active constraint set."""

    regime_name: str
    caf_floor: float
    caf_cap: float
    confidence_gate: float
    min_relationships: int
    effective_from: datetime
    evidence: dict = field(default_factory=dict)

    def clamp(self, caf: float) -> tuple[float, bool]:
        """Apply floor/cap. Returns (clamped_value, was_constrained)."""
        if caf < self.caf_floor:
            return self.caf_floor, True
        if caf > self.caf_cap:
            return self.caf_cap, True
        return caf, False

    def within_absolute_bounds(self) -> bool:
        return (
            ABSOLUTE_FLOOR <= self.caf_floor <= 1.0
            and 1.0 <= self.caf_cap <= ABSOLUTE_CAP
            and self.confidence_gate >= ABSOLUTE_CONFIDENCE_MIN
        )


@dataclass
class WideningProposal:
    current: ConstraintRegime
    proposed: ConstraintRegime
    evidence: dict
    backtest_passed: bool


class ConstraintCalibrator:
    """Reads active regime, proposes widened regimes when criteria are met."""

    def __init__(self, db: Session):
        self.db = db

    # ------------------------------------------------------------------
    # Read the active regime
    # ------------------------------------------------------------------

    def get_active_regime(self) -> ConstraintRegime:
        """Fetch the currently-active constraint regime. Falls back to
        initial constants if the table is empty or inaccessible."""
        try:
            row = self.db.execute(
                text(
                    """
                    SELECT regime_name, caf_floor, caf_cap, confidence_gate,
                           min_relationships, effective_from, evidence
                    FROM we_constraint_history
                    WHERE effective_to IS NULL
                    ORDER BY effective_from DESC
                    LIMIT 1
                    """
                )
            ).mappings().first()
        except Exception:
            row = None

        if row is None:
            return ConstraintRegime(
                regime_name="initial_fallback",
                caf_floor=INITIAL_FLOOR,
                caf_cap=INITIAL_CAP,
                confidence_gate=INITIAL_CONFIDENCE_GATE,
                min_relationships=INITIAL_MIN_RELATIONSHIPS,
                effective_from=datetime.now(timezone.utc),
                evidence={"note": "initial fallback"},
            )

        return ConstraintRegime(
            regime_name=row["regime_name"],
            caf_floor=float(row["caf_floor"]),
            caf_cap=float(row["caf_cap"]),
            confidence_gate=float(row["confidence_gate"]),
            min_relationships=int(row["min_relationships"]),
            effective_from=row["effective_from"],
            evidence=row["evidence"] or {},
        )

    # ------------------------------------------------------------------
    # Propose widening
    # ------------------------------------------------------------------

    def evaluate_widening(self) -> Optional[WideningProposal]:
        """If criteria are met, return a proposed widened regime, else None."""
        current = self.get_active_regime()

        at_floor_bound = current.caf_floor <= ABSOLUTE_FLOOR + 1e-9
        at_cap_bound = current.caf_cap >= ABSOLUTE_CAP - 1e-9
        if at_floor_bound and at_cap_bound:
            return None

        evidence = self._gather_evidence(current)
        criteria_met, unmet = self._check_criteria(evidence)
        if not criteria_met:
            logger.debug("Widening criteria not met: %s", unmet)
            return None

        new_floor = max(ABSOLUTE_FLOOR, current.caf_floor - FLOOR_STEP)
        new_cap = min(ABSOLUTE_CAP, current.caf_cap + CAP_STEP)
        proposed = ConstraintRegime(
            regime_name=f"widened_{datetime.now(timezone.utc).strftime('%Y%m%d')}",
            caf_floor=new_floor,
            caf_cap=new_cap,
            confidence_gate=current.confidence_gate,
            min_relationships=current.min_relationships,
            effective_from=datetime.now(timezone.utc),
            evidence=evidence,
        )

        backtest_passed = self._backtest(current, proposed)
        return WideningProposal(
            current=current,
            proposed=proposed,
            evidence=evidence,
            backtest_passed=backtest_passed,
        )

    # ------------------------------------------------------------------
    # Apply a proposal
    # ------------------------------------------------------------------

    def activate_proposal(self, proposal: WideningProposal) -> None:
        """Record the current regime's effective_to and insert the new one."""
        if not proposal.backtest_passed:
            raise ValueError("Cannot activate a proposal that failed backtest")

        if not proposal.proposed.within_absolute_bounds():
            raise ValueError(
                f"Proposed regime breaches absolute bounds: "
                f"floor={proposal.proposed.caf_floor}, cap={proposal.proposed.caf_cap}"
            )

        now = datetime.now(timezone.utc)
        self.db.execute(
            text("UPDATE we_constraint_history SET effective_to = :now WHERE effective_to IS NULL"),
            {"now": now},
        )
        self.db.execute(
            text(
                """
                INSERT INTO we_constraint_history (
                    regime_name, caf_floor, caf_cap, confidence_gate,
                    min_relationships, effective_from, evidence
                ) VALUES (
                    :regime_name, :caf_floor, :caf_cap, :confidence_gate,
                    :min_relationships, :effective_from, CAST(:evidence AS jsonb)
                )
                """
            ),
            {
                "regime_name": proposal.proposed.regime_name,
                "caf_floor": proposal.proposed.caf_floor,
                "caf_cap": proposal.proposed.caf_cap,
                "confidence_gate": proposal.proposed.confidence_gate,
                "min_relationships": proposal.proposed.min_relationships,
                "effective_from": proposal.proposed.effective_from,
                "evidence": json.dumps(proposal.evidence, default=str),
            },
        )
        logger.info(
            "ConstraintCalibrator: activated regime %s (floor=%.2f cap=%.2f)",
            proposal.proposed.regime_name,
            proposal.proposed.caf_floor,
            proposal.proposed.caf_cap,
        )

    # ------------------------------------------------------------------
    # Evidence gathering
    # ------------------------------------------------------------------

    def _gather_evidence(self, current: ConstraintRegime) -> dict:
        evidence: dict = {}
        try:
            evidence["active_relationships"] = int(self.db.execute(
                text("SELECT COUNT(*) FROM we_relationships WHERE lifecycle_state='active'")
            ).scalar() or 0)
        except Exception:
            evidence["active_relationships"] = 0

        try:
            avg_hit = self.db.execute(
                text(
                    "SELECT AVG(predictive_hit_rate) FROM we_relationships "
                    "WHERE lifecycle_state='active' AND predictive_hit_rate IS NOT NULL"
                )
            ).scalar()
            evidence["predictive_accuracy"] = float(avg_hit) if avg_hit else 0.0
        except Exception:
            evidence["predictive_accuracy"] = 0.0

        effective_from = current.effective_from
        if effective_from.tzinfo is None:
            effective_from = effective_from.replace(tzinfo=timezone.utc)
        months = (datetime.now(timezone.utc) - effective_from).days / 30.0
        evidence["evaluation_months"] = max(0.0, months)

        try:
            row = self.db.execute(
                text(
                    """
                    SELECT
                        COUNT(*) AS total,
                        SUM(CASE WHEN constrained THEN 1 ELSE 0 END) AS hits
                    FROM we_causal_adjustments
                    WHERE computed_at >= :since
                    """
                ),
                {"since": effective_from},
            ).mappings().first()
            total = int(row["total"] or 0)
            hits = int(row["hits"] or 0)
            evidence["caf_evaluations"] = total
            evidence["constraint_hit_rate"] = hits / total if total > 0 else 0.0
        except Exception:
            evidence["caf_evaluations"] = 0
            evidence["constraint_hit_rate"] = 0.0

        return evidence

    def _check_criteria(self, evidence: dict) -> tuple[bool, list[str]]:
        unmet: list[str] = []
        c = WIDENING_CRITERIA

        if evidence["active_relationships"] < c["min_active_relationships"]:
            unmet.append(f"active_relationships={evidence['active_relationships']} < {c['min_active_relationships']}")
        if evidence["predictive_accuracy"] < c["min_predictive_accuracy"]:
            unmet.append(f"predictive_accuracy={evidence['predictive_accuracy']:.2f} < {c['min_predictive_accuracy']}")
        if evidence["evaluation_months"] < c["min_evaluation_months"]:
            unmet.append(f"evaluation_months={evidence['evaluation_months']:.1f} < {c['min_evaluation_months']}")
        if evidence["caf_evaluations"] < c["min_caf_evaluations"]:
            unmet.append(f"caf_evaluations={evidence['caf_evaluations']} < {c['min_caf_evaluations']}")
        if evidence["constraint_hit_rate"] < c["max_constraint_hit_rate"]:
            unmet.append(
                f"constraint_hit_rate={evidence['constraint_hit_rate']:.2f} < "
                f"{c['max_constraint_hit_rate']} (too few hits -- no need to widen)"
            )

        return len(unmet) == 0, unmet

    # ------------------------------------------------------------------
    # Backtesting
    # ------------------------------------------------------------------

    def _backtest(self, current: ConstraintRegime, proposed: ConstraintRegime) -> bool:
        """Rerun historical raw CAFs under the proposed constraints and
        reject if we'd produce pathological outcomes."""
        try:
            rows = self.db.execute(
                text(
                    """
                    SELECT caf_value, raw_caf, constrained
                    FROM we_causal_adjustments
                    WHERE computed_at >= :since
                    LIMIT 10000
                    """
                ),
                {"since": current.effective_from},
            ).mappings().all()
        except Exception:
            return False

        if not rows:
            return False

        large_shifts = 0
        out_of_absolute = 0
        for row in rows:
            raw = float(row["raw_caf"] or row["caf_value"] or 1.0)
            old_clamped, _ = current.clamp(raw)
            new_clamped, _ = proposed.clamp(raw)

            if abs(old_clamped - new_clamped) > 0.05:
                large_shifts += 1

            if new_clamped < ABSOLUTE_FLOOR or new_clamped > ABSOLUTE_CAP:
                out_of_absolute += 1

        if out_of_absolute > 0:
            logger.warning("Backtest FAILED: %d CAFs would fall outside absolute bounds", out_of_absolute)
            return False

        shift_ratio = large_shifts / len(rows)
        if shift_ratio > 0.5:
            logger.warning("Backtest FAILED: %.0f%% of CAFs would shift > 0.05", shift_ratio * 100)
            return False

        return True

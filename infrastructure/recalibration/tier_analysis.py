"""
C-2e: TierAnalyser

Evaluates whether current tier boundaries optimally separate loss frequency.

Method:
1. For every bound assessment in scope, pull (composite_score, has_loss).
2. For each pair of adjacent tier boundaries, compute loss frequency.
3. If adjacent tiers' loss frequencies are statistically similar (chi-square
   test), the boundary is providing no discrimination -- propose shifting
   it toward the position that MAXIMISES frequency separation.
4. If a proposed shift is > MIN_SHIFT_POINTS, emit a TierThresholdChange.

We deliberately keep this conservative -- tier boundaries have cross-
coverage implications and are frequently hand-tuned by actuarial. This
analyser surfaces problems (adjacent tiers with no frequency separation);
human review decides the shift.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

import numpy as np
from scipy import stats
from sqlalchemy import text
from sqlalchemy.orm import Session

from infrastructure.recalibration.types import TierThresholdChange

logger = logging.getLogger("dsi.recalibration.tier_analysis")


MIN_SHIFT_POINTS = 5.0
"""Don't propose a boundary shift smaller than this (composite score points)."""

CHI_SQUARE_P_THRESHOLD = 0.05
"""Adjacent tiers with chi-square p > this have no significant frequency
separation and are candidates for boundary adjustment."""


@dataclass
class TierAnalyserConfig:
    min_shift_points: float = MIN_SHIFT_POINTS
    chi_square_p_threshold: float = CHI_SQUARE_P_THRESHOLD
    min_obs_per_tier: int = 20


class TierAnalyser:
    """Proposes tier boundary shifts when adjacent tiers lack frequency separation."""

    def __init__(self, db: Session, config: Optional[TierAnalyserConfig] = None):
        self.db = db
        self.config = config or TierAnalyserConfig()

    def analyse(
        self,
        coverage: str,
        config_name: str,
        current_tier_boundaries: list[tuple[int, float, float]],
    ) -> list[TierThresholdChange]:
        """Propose shifts for tier boundaries that don't discriminate.

        current_tier_boundaries: list of (tier_id, min_score, max_score)
        for each tier band in the current config.
        """
        if len(current_tier_boundaries) < 2:
            return []

        pairs = self._load_score_loss_pairs(coverage, config_name)
        if not pairs:
            return []

        scores = np.array([s for s, _ in pairs])
        has_loss = np.array([hl for _, hl in pairs])

        changes: list[TierThresholdChange] = []

        # For each adjacent tier pair, test separation
        sorted_tiers = sorted(current_tier_boundaries, key=lambda t: t[1])
        for i in range(len(sorted_tiers) - 1):
            tier_a_id, a_min, a_max = sorted_tiers[i]
            tier_b_id, b_min, b_max = sorted_tiers[i + 1]

            # Use the boundary value (tier_a's max == tier_b's min, typically)
            boundary = a_max

            mask_a = (scores >= a_min) & (scores <= a_max)
            mask_b = (scores >= b_min) & (scores <= b_max)
            n_a = int(mask_a.sum())
            n_b = int(mask_b.sum())

            if n_a < self.config.min_obs_per_tier or n_b < self.config.min_obs_per_tier:
                continue

            losses_a = int(has_loss[mask_a].sum())
            losses_b = int(has_loss[mask_b].sum())

            # 2x2 contingency table: tier x loss_indicator
            table = [[losses_a, n_a - losses_a], [losses_b, n_b - losses_b]]
            try:
                _, p, _, _ = stats.chi2_contingency(table)
            except ValueError:
                continue  # zero cells

            if p < self.config.chi_square_p_threshold:
                continue  # good separation -- leave the boundary alone

            # Find a better boundary: scan a +/- window around the current
            # boundary and pick the position that MINIMISES chi-square p
            # (maximum separation).
            window = (b_max - a_min) * 0.1  # 10% of the combined tier width
            candidates = np.linspace(boundary - window, boundary + window, 11)
            best_p = p
            best_boundary = boundary
            for candidate in candidates:
                if candidate <= a_min or candidate >= b_max:
                    continue
                mask_new_a = (scores >= a_min) & (scores <= candidate)
                mask_new_b = (scores > candidate) & (scores <= b_max)
                n_new_a = int(mask_new_a.sum())
                n_new_b = int(mask_new_b.sum())
                if n_new_a < 10 or n_new_b < 10:
                    continue
                losses_new_a = int(has_loss[mask_new_a].sum())
                losses_new_b = int(has_loss[mask_new_b].sum())
                t2 = [[losses_new_a, n_new_a - losses_new_a],
                      [losses_new_b, n_new_b - losses_new_b]]
                try:
                    _, p_new, _, _ = stats.chi2_contingency(t2)
                except ValueError:
                    continue
                if p_new < best_p:
                    best_p = p_new
                    best_boundary = float(candidate)

            shift = best_boundary - boundary
            if abs(shift) < self.config.min_shift_points:
                continue

            changes.append(TierThresholdChange(
                band_id=tier_a_id,
                boundary="max",
                current_value=round(boundary, 2),
                proposed_value=round(best_boundary, 2),
                delta=round(shift, 2),
                evidence={
                    "chi_square_p_current": float(p),
                    "chi_square_p_proposed": float(best_p),
                    "tier_a_loss_freq": losses_a / n_a,
                    "tier_b_loss_freq": losses_b / n_b,
                    "tier_a_n": n_a,
                    "tier_b_n": n_b,
                },
            ))

        logger.info(
            "TierAnalyser: %d tier boundary changes proposed", len(changes)
        )
        return changes

    # ------------------------------------------------------------------
    # Data loading
    # ------------------------------------------------------------------

    def _load_score_loss_pairs(
        self, coverage: str, config_name: str
    ) -> list[tuple[float, int]]:
        """Return (composite_score, has_loss) for bound assessments."""
        sql = """
            SELECT
                COALESCE(m.final_composite_score, m.pure_composite_score) AS score,
                CASE WHEN EXISTS (
                    SELECT 1 FROM loss_events le WHERE le.entity_name = s.entity_name
                ) THEN 1 ELSE 0 END AS has_loss
            FROM submissions s
            JOIN model_versions m ON m.submission_id = s.id
            WHERE s.coverage = :coverage
              AND (s.configuration = :config_name OR m.configuration_name = :config_name)
              AND COALESCE(m.final_composite_score, m.pure_composite_score) IS NOT NULL
        """
        try:
            rows = self.db.execute(
                text(sql), {"coverage": coverage, "config_name": config_name}
            ).all()
            return [(float(r[0]), int(r[1])) for r in rows]
        except Exception as exc:  # noqa: BLE001
            logger.warning("Tier data load failed: %s", exc)
            return []

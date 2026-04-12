"""
C-2f: ImpactAssessor

Evaluates the real-world impact of applying a proposal's weight changes
and tier threshold changes to the current book of bound assessments.

For every bound assessment:
1. Recompute the composite score under the proposed weights. Because we
   only have access to snapshotted signal scores (from
   signal_loss_pairs.signal_scores_at_bind OR live ModelVersionSignal
   rows), we rebuild the composite as a weighted average on that data.
2. Re-assign tier using the proposed tier boundaries (if any).
3. Aggregate the tier migration counts + premium delta estimates.

Discrimination improvement is estimated by comparing the AUC or IV of
the proposed vs current weight combinations using the same paired
data set used by the SignalAnalyser.

Output: ImpactAssessment ready to attach to a RecalibrationProposal.
"""

from __future__ import annotations

import logging
from collections import defaultdict
from dataclasses import dataclass
from typing import Optional

import numpy as np
from sqlalchemy import text
from sqlalchemy.orm import Session

from infrastructure.recalibration.types import (
    ImpactAssessment,
    TierThresholdChange,
    WeightChange,
)

logger = logging.getLogger("dsi.recalibration.impact")


@dataclass
class ImpactAssessorConfig:
    sample_cap: int = 2000
    """Maximum number of assessments to evaluate (keeps the run bounded)."""


class ImpactAssessor:
    """Rerun the proposal against the current book and summarise impact."""

    def __init__(self, db: Session, config: Optional[ImpactAssessorConfig] = None):
        self.db = db
        self.config = config or ImpactAssessorConfig()

    def assess(
        self,
        coverage: str,
        config_name: str,
        current_weights: dict[str, float],
        weight_changes: list[WeightChange],
        tier_threshold_changes: list[TierThresholdChange],
        tier_boundaries: list[tuple[int, float, float]],
    ) -> ImpactAssessment:
        """Produce an ImpactAssessment for the proposed changes."""
        assessments = self._load_assessments(coverage, config_name)
        if not assessments:
            return ImpactAssessment()

        # Build proposed weight map
        proposed_weights = dict(current_weights)
        for wc in weight_changes:
            proposed_weights[wc.signal_id] = wc.proposed_weight

        # Build current and proposed tier boundaries
        current_boundaries = sorted(tier_boundaries, key=lambda t: t[1])
        proposed_boundaries = self._apply_tier_changes(
            current_boundaries, tier_threshold_changes
        )

        migration: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
        total_current_premium = 0.0
        total_proposed_premium = 0.0
        tier_changed_count = 0

        for record in assessments:
            # Recompute composite under proposed weights
            current_composite = record["composite_score"]
            proposed_composite = self._weighted_score(
                record["signal_scores"], proposed_weights
            )

            current_tier = self._tier_for_score(current_composite, current_boundaries)
            proposed_tier = self._tier_for_score(proposed_composite, proposed_boundaries)

            key_current = str(current_tier)
            key_proposed = str(proposed_tier)
            migration[key_current][key_proposed] += 1
            if current_tier != proposed_tier:
                tier_changed_count += 1

            # Premium delta proxy: if tier changes, premium scales roughly
            # with the tier rate ratio. We don't have live rates here so we
            # assume a linear scale (tier 1 -> 2 = +25% rough). This is
            # illustrative; the real premium recomputation requires the
            # pricer.
            current_premium = record["final_premium"] or 0.0
            total_current_premium += current_premium
            if current_tier == proposed_tier:
                total_proposed_premium += current_premium
            else:
                # Apply a simple ratio -- each tier up = +25%, down = -20%
                delta_tiers = proposed_tier - current_tier
                factor = 1.0 + (0.25 * delta_tiers if delta_tiers >= 0 else 0.20 * delta_tiers)
                total_proposed_premium += current_premium * max(0.0, factor)

        total_delta = total_proposed_premium - total_current_premium
        pct = (total_delta / total_current_premium * 100.0) if total_current_premium > 0 else 0.0

        discrimination_improvement = self._discrimination_delta(
            assessments, current_weights, proposed_weights
        )

        return ImpactAssessment(
            tier_migration={k: dict(v) for k, v in migration.items()},
            total_premium_delta=round(total_delta, 2),
            total_premium_delta_pct=round(pct, 2),
            discrimination_improvement=round(discrimination_improvement, 4),
            assessments_evaluated=len(assessments),
            assessments_tier_changed=tier_changed_count,
        )

    # ------------------------------------------------------------------
    # Data loading
    # ------------------------------------------------------------------

    def _load_assessments(
        self, coverage: str, config_name: str
    ) -> list[dict]:
        """Return list of {composite_score, signal_scores, final_premium, has_loss}."""
        sql = """
            SELECT DISTINCT ON (s.entity_name)
                s.entity_name,
                COALESCE(m.final_composite_score, m.pure_composite_score) AS composite,
                m.final_premium,
                COALESCE(
                    (SELECT jsonb_object_agg(sig.code, mvs.score)
                     FROM model_version_signals mvs
                     JOIN signals sig ON sig.id = mvs.signal_id
                     WHERE mvs.model_version_id = m.id AND mvs.score IS NOT NULL),
                    '{}'::jsonb
                ) AS scores,
                CASE WHEN EXISTS (
                    SELECT 1 FROM loss_events le WHERE le.entity_name = s.entity_name
                ) THEN 1 ELSE 0 END AS has_loss
            FROM submissions s
            JOIN model_versions m ON m.submission_id = s.id
            WHERE s.coverage = :coverage
              AND (s.configuration = :config_name OR m.configuration_name = :config_name)
            ORDER BY s.entity_name, m.created_at DESC
            LIMIT :cap
        """
        try:
            rows = self.db.execute(
                text(sql),
                {"coverage": coverage, "config_name": config_name, "cap": self.config.sample_cap},
            ).mappings().all()
            return [
                {
                    "composite_score": float(r["composite"] or 0.0),
                    "final_premium": float(r["final_premium"] or 0.0),
                    "signal_scores": dict(r["scores"] or {}),
                    "has_loss": int(r["has_loss"]),
                }
                for r in rows
            ]
        except Exception as exc:  # noqa: BLE001
            logger.warning("Impact data load failed: %s", exc)
            return []

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _weighted_score(
        self, signal_scores: dict[str, float], weights: dict[str, float]
    ) -> float:
        """Compute a composite score = Σ(weight * signal_score) for signals
        the assessment actually recorded."""
        total_weight = 0.0
        total = 0.0
        for sig_id, w in weights.items():
            score = signal_scores.get(sig_id)
            if score is None or w <= 0:
                continue
            total += float(score) * float(w)
            total_weight += float(w)
        if total_weight == 0:
            return 0.0
        # Scale to 0-1000 range (standard DSI composite)
        return float(total / total_weight * 10.0)  # assumes signals are 0-100

    def _tier_for_score(
        self, score: float, boundaries: list[tuple[int, float, float]]
    ) -> int:
        for tid, mn, mx in boundaries:
            if mn <= score <= mx:
                return tid
        # Fallback: nearest band
        if boundaries:
            return boundaries[-1][0]
        return 0

    def _apply_tier_changes(
        self,
        boundaries: list[tuple[int, float, float]],
        changes: list[TierThresholdChange],
    ) -> list[tuple[int, float, float]]:
        by_id = {tid: (mn, mx) for tid, mn, mx in boundaries}
        ordered = sorted(boundaries, key=lambda t: t[1])

        for ch in changes:
            mn, mx = by_id.get(ch.band_id, (0.0, 0.0))
            if ch.boundary == "max":
                by_id[ch.band_id] = (mn, ch.proposed_value)
                # adjust adjacent tier's min
                for i, (tid, tmn, tmx) in enumerate(ordered):
                    if tid == ch.band_id and i + 1 < len(ordered):
                        next_id, next_mn, next_mx = ordered[i + 1]
                        by_id[next_id] = (ch.proposed_value, next_mx)
                        break
            elif ch.boundary == "min":
                by_id[ch.band_id] = (ch.proposed_value, mx)
                for i, (tid, tmn, tmx) in enumerate(ordered):
                    if tid == ch.band_id and i > 0:
                        prev_id, prev_mn, prev_mx = ordered[i - 1]
                        by_id[prev_id] = (prev_mn, ch.proposed_value)
                        break

        return sorted([(tid, mn, mx) for tid, (mn, mx) in by_id.items()], key=lambda t: t[1])

    def _discrimination_delta(
        self,
        assessments: list[dict],
        current_weights: dict[str, float],
        proposed_weights: dict[str, float],
    ) -> float:
        """AUC delta = proposed_AUC - current_AUC. Returns 0 if insufficient data."""
        if not assessments:
            return 0.0
        labels = np.array([a["has_loss"] for a in assessments])
        if labels.sum() < 3 or labels.sum() > len(labels) - 3:
            return 0.0  # need both classes

        current = np.array([
            self._weighted_score(a["signal_scores"], current_weights)
            for a in assessments
        ])
        proposed = np.array([
            self._weighted_score(a["signal_scores"], proposed_weights)
            for a in assessments
        ])

        return float(self._auc(proposed, labels) - self._auc(current, labels))

    def _auc(self, scores: np.ndarray, labels: np.ndarray) -> float:
        """AUC via Mann-Whitney-U formulation. Lower scores = higher loss rate,
        so we invert scores for the positive class (loss=1)."""
        pos = scores[labels == 1]
        neg = scores[labels == 0]
        if len(pos) == 0 or len(neg) == 0:
            return 0.5
        from scipy.stats import mannwhitneyu
        try:
            # Lower score -> more likely loss, so:
            u, _ = mannwhitneyu(neg, pos, alternative="greater")
            return float(u / (len(pos) * len(neg)))
        except Exception:
            return 0.5

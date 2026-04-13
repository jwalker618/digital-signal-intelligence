"""
WE-3c (3/3): PredictiveValidator

Tests out-of-sample predictive power. For an established relationship
"source at precursor state predicts target degradation", identify entities
whose source signal recently crossed the precursor threshold, then check
whether the target signal followed within the relationship's lag window.

Hit rate = predictions that materialised / total predictions made.

Strong ACTIVE relationships maintain hit_rate > 0.6; relationships whose
predictive power decays below 0.4 are demoted to DEPRECATED.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import timedelta
from typing import Optional

import numpy as np
from sqlalchemy import text
from sqlalchemy.orm import Session

from world_engine.types import DiscoveredRelationship, PredictiveResult

logger = logging.getLogger("dsi.world_engine.validator.predictive")


@dataclass
class PredictiveConfig:
    # Precursor = source signal in the worst quartile of observed scores.
    precursor_quantile: float = 0.25
    # Consequence = target signal dropping by this many points from prior assessment.
    target_degradation_points: float = 5.0
    # Minimum predictions required for a meaningful hit rate.
    min_predictions: int = 10
    # Grace window either side of the lag for considering the consequence realised.
    window_tolerance_months: float = 2.0


class PredictiveValidator:
    """Tests out-of-sample forward prediction."""

    def __init__(self, config: Optional[PredictiveConfig] = None):
        self.config = config or PredictiveConfig()

    def validate(
        self, relationship: DiscoveredRelationship, db: Session
    ) -> PredictiveResult:
        """Evaluate predictive hit rate for an active relationship.

        For each entity where the source signal recently crossed into the
        precursor state, check whether the target signal degraded within
        the relationship's lag window.
        """
        lag = relationship.lag_months
        if lag is None or lag <= 0:
            # Contemporaneous relationships can't be predictively validated.
            return PredictiveResult(
                relationship_id=relationship.id,
                predictions_made=0,
                predictions_hit=0,
                hit_rate=0.0,
                passed=False,
            )

        series = self._load_series(
            db, relationship.source_signal, relationship.target_signal
        )
        if not series:
            return PredictiveResult(
                relationship_id=relationship.id,
                predictions_made=0,
                predictions_hit=0,
                hit_rate=0.0,
                passed=False,
            )

        # Determine the precursor threshold as the low quantile across
        # all observations of the source signal.
        all_source = [v for entity in series.values() for _, v, _ in entity["pairs"]]
        if not all_source:
            return PredictiveResult(
                relationship_id=relationship.id,
                predictions_made=0,
                predictions_hit=0,
                hit_rate=0.0,
                passed=False,
            )
        threshold = float(np.quantile(all_source, self.config.precursor_quantile))

        predictions = 0
        hits = 0
        for entity, rec in series.items():
            pairs = rec["pairs"]  # [(ts, source, target)] sorted
            for i in range(len(pairs) - 1):
                ts, src, tgt = pairs[i]
                # Precursor trigger: source crosses INTO the low band (drops
                # below threshold) at this timestamp.
                if src > threshold:
                    continue
                # Previous source score above threshold (transition), or first
                # observation where source is already below.
                if i > 0 and pairs[i - 1][1] <= threshold:
                    # Already in precursor -- don't double-count
                    continue

                # Find the next observation within (lag ± tolerance) months
                lag_low = lag - self.config.window_tolerance_months
                lag_high = lag + self.config.window_tolerance_months

                observed_degradation = False
                for j in range(i + 1, len(pairs)):
                    next_ts, _next_src, next_tgt = pairs[j]
                    months = (next_ts - ts).days / 30.0
                    if months < lag_low:
                        continue
                    if months > lag_high:
                        break  # window past
                    # Did target degrade by the threshold?
                    if tgt - next_tgt >= self.config.target_degradation_points:
                        observed_degradation = True
                    break  # only the first observation in the window counts

                predictions += 1
                if observed_degradation:
                    hits += 1

        hit_rate = hits / predictions if predictions > 0 else 0.0
        passed = (
            predictions >= self.config.min_predictions
            and hit_rate >= 0.6
        )

        return PredictiveResult(
            relationship_id=relationship.id,
            predictions_made=predictions,
            predictions_hit=hits,
            hit_rate=float(hit_rate),
            passed=bool(passed),
        )

    # ------------------------------------------------------------------
    # Data loading
    # ------------------------------------------------------------------

    def _load_series(self, db: Session, source: str, target: str) -> dict:
        """Return {entity_name: {"pairs": [(ts, source_score, target_score), ...]}}.

        Only entities with >= 2 temporally paired observations contribute.
        """
        sql = """
            SELECT
                s.entity_name,
                m.created_at,
                sig.code AS signal_code,
                mvs.score
            FROM submissions s
            JOIN model_versions m         ON m.submission_id = s.id
            JOIN model_version_signals mvs ON mvs.model_version_id = m.id
            JOIN signals sig              ON sig.id = mvs.signal_id
            WHERE sig.code IN (:source, :target)
              AND mvs.score IS NOT NULL
            ORDER BY s.entity_name, m.created_at
        """
        rows = db.execute(
            text(sql), {"source": source, "target": target}
        ).mappings().all()

        per_entity: dict = {}
        for row in rows:
            rec = per_entity.setdefault(
                row["entity_name"], {"observations": {}}
            )
            obs = rec["observations"].setdefault(row["created_at"], {})
            obs[row["signal_code"]] = float(row["score"])

        # Collapse to sorted (ts, source, target) triples where both are present
        for entity, rec in list(per_entity.items()):
            triples: list[tuple] = []
            for ts, signals in sorted(rec["observations"].items()):
                if source in signals and target in signals:
                    triples.append((ts, signals[source], signals[target]))
            if len(triples) < 2:
                del per_entity[entity]
                continue
            rec["pairs"] = triples
            del rec["observations"]

        return per_entity

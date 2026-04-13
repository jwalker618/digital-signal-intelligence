"""
WE-3c (1/3): HoldoutValidator

Tests whether a discovered relationship replicates in unseen data. Splits
the assessed population 70/30 and verifies the Spearman correlation
survives (|rho| > 0.2, p < 0.05) on the holdout fraction.

Splitting strategy: hash the entity_name with a stable hash function so
the same entity falls in the same partition across runs. This means
holdout membership is deterministic given the entity population and does
not drift between scans -- the "holdout" is truly held out.
"""

from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass
from typing import Optional

import numpy as np
from scipy import stats
from sqlalchemy import text
from sqlalchemy.orm import Session

from world_engine.types import DirectedCandidate, ValidationResult

logger = logging.getLogger("dsi.world_engine.validator.holdout")


@dataclass
class HoldoutConfig:
    holdout_fraction: float = 0.3
    min_holdout_observations: int = 15
    rho_threshold: float = 0.2
    p_threshold: float = 0.05


class HoldoutValidator:
    """Tests relationship replication in unseen data."""

    def __init__(self, config: Optional[HoldoutConfig] = None):
        self.config = config or HoldoutConfig()

    def validate(
        self, candidate: DirectedCandidate, db: Session
    ) -> ValidationResult:
        """Run holdout validation for a single candidate. Non-side-effecting."""
        holdout_xs, holdout_ys = self._load_holdout_scores(
            db, candidate.source_signal, candidate.target_signal
        )
        if len(holdout_xs) < self.config.min_holdout_observations:
            return ValidationResult(
                candidate=candidate,
                holdout_rho=0.0,
                holdout_p_value=1.0,
                passed=False,
            )

        rho, p = stats.spearmanr(holdout_xs, holdout_ys)
        if np.isnan(rho) or np.isnan(p):
            return ValidationResult(
                candidate=candidate, holdout_rho=0.0, holdout_p_value=1.0, passed=False
            )

        passed = (
            abs(rho) >= self.config.rho_threshold
            and p < self.config.p_threshold
        )
        return ValidationResult(
            candidate=candidate,
            holdout_rho=float(rho),
            holdout_p_value=float(p),
            passed=bool(passed),
        )

    # ------------------------------------------------------------------
    # Holdout score loading
    # ------------------------------------------------------------------

    def _load_holdout_scores(
        self, db: Session, source: str, target: str
    ) -> tuple[list[float], list[float]]:
        """Return (source_scores, target_scores) for entities in the holdout split.

        Uses latest model version per entity. Only entities with both signals
        observed contribute.
        """
        sql = """
            SELECT
                s.entity_name,
                sig.code AS signal_code,
                mvs.score
            FROM submissions s
            JOIN model_versions m         ON m.submission_id = s.id
            JOIN model_version_signals mvs ON mvs.model_version_id = m.id
            JOIN signals sig              ON sig.id = mvs.signal_id
            WHERE sig.code IN (:source_code, :target_code)
              AND mvs.score IS NOT NULL
              AND m.created_at = (
                  SELECT MAX(m2.created_at)
                  FROM model_versions m2
                  JOIN submissions s2 ON m2.submission_id = s2.id
                  WHERE s2.entity_name = s.entity_name
              )
        """
        rows = db.execute(
            text(sql), {"source_code": source, "target_code": target}
        ).mappings().all()

        # Pivot into per-entity tuples
        per_entity: dict[str, dict[str, float]] = {}
        for row in rows:
            per_entity.setdefault(row["entity_name"], {})[row["signal_code"]] = float(row["score"])

        xs: list[float] = []
        ys: list[float] = []
        for entity_name, signals in per_entity.items():
            if source not in signals or target not in signals:
                continue
            if not self._in_holdout(entity_name):
                continue
            xs.append(signals[source])
            ys.append(signals[target])

        return xs, ys

    def _in_holdout(self, entity_name: str) -> bool:
        """Stable deterministic hash-based partitioning."""
        digest = hashlib.md5(entity_name.encode()).hexdigest()
        bucket = int(digest[:8], 16) / 0xFFFFFFFF
        return bucket < self.config.holdout_fraction

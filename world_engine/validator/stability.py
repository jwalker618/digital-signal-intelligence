"""
WE-3c (2/3): TemporalStabilityTracker

Tracks whether a relationship's correlation remains stable over rolling
time windows. A relationship that appeared in month 6 but vanished by
month 9 is not a durable pattern -- it fails stability.

Window strategy: split the assessment database into N equal time windows
(by assessment created_at). For each window, compute the pair's Spearman
correlation. Require persistence across at least `min_stable_windows`
consecutive windows. Sign flips between windows trigger an explicit flag
(the relationship has inverted).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

import numpy as np
from scipy import stats
from sqlalchemy import text
from sqlalchemy.orm import Session

from world_engine.types import StabilityResult

logger = logging.getLogger("dsi.world_engine.validator.stability")


@dataclass
class StabilityConfig:
    num_windows: int = 4
    min_stable_windows: int = 3
    min_obs_per_window: int = 15
    rho_threshold: float = 0.2
    # Below this |rho| a window is considered "unstable"


class TemporalStabilityTracker:
    """Tracks relationship stability over rolling observation windows."""

    def __init__(self, config: Optional[StabilityConfig] = None):
        self.config = config or StabilityConfig()

    def check(
        self, source_signal: str, target_signal: str, db: Session, relationship_id: str = ""
    ) -> StabilityResult:
        """Compute per-window correlations and assess stability."""
        window_rhos = self._compute_windows(source_signal, target_signal, db)

        if not window_rhos:
            return StabilityResult(
                relationship_id=relationship_id,
                windows_checked=0,
                windows_stable=0,
                correlation_trend=[],
                stable=False,
                sign_flip_detected=False,
            )

        stable_count = sum(
            1 for rho in window_rhos if rho is not None and abs(rho) >= self.config.rho_threshold
        )

        # Sign flip detection: compare consecutive non-null rhos
        signs = [np.sign(r) for r in window_rhos if r is not None]
        sign_flip = any(signs[i] != signs[i - 1] and signs[i] != 0 for i in range(1, len(signs)))

        stable = stable_count >= self.config.min_stable_windows and not sign_flip

        return StabilityResult(
            relationship_id=relationship_id,
            windows_checked=len(window_rhos),
            windows_stable=stable_count,
            correlation_trend=[float(r) if r is not None else 0.0 for r in window_rhos],
            stable=bool(stable),
            sign_flip_detected=bool(sign_flip),
        )

    # ------------------------------------------------------------------
    # Rolling window computation
    # ------------------------------------------------------------------

    def _compute_windows(
        self, source: str, target: str, db: Session
    ) -> list[Optional[float]]:
        """For each time window, compute Spearman rho between source and target.

        Returns a list aligned with window order (oldest → newest).
        """
        # Fetch paired observations timestamped by their model_version's created_at
        sql = """
            WITH latest_per_entity AS (
                SELECT DISTINCT ON (s.entity_name)
                    s.entity_name, m.id AS mv_id, m.created_at
                FROM submissions s
                JOIN model_versions m ON m.submission_id = s.id
                ORDER BY s.entity_name, m.created_at DESC
            )
            SELECT
                l.entity_name,
                l.created_at,
                sig.code AS signal_code,
                mvs.score
            FROM latest_per_entity l
            JOIN model_version_signals mvs ON mvs.model_version_id = l.mv_id
            JOIN signals sig ON sig.id = mvs.signal_id
            WHERE sig.code IN (:source, :target)
              AND mvs.score IS NOT NULL
        """
        rows = db.execute(
            text(sql), {"source": source, "target": target}
        ).mappings().all()

        # Pivot into per-entity (ts, source_score, target_score)
        per_entity: dict[str, dict] = {}
        for row in rows:
            rec = per_entity.setdefault(row["entity_name"], {"ts": row["created_at"]})
            rec[row["signal_code"]] = float(row["score"])
            rec["ts"] = row["created_at"]

        tuples: list[tuple] = []
        for entity, rec in per_entity.items():
            if source in rec and target in rec:
                tuples.append((rec["ts"], rec[source], rec[target]))

        if len(tuples) < self.config.num_windows * self.config.min_obs_per_window:
            return []

        tuples.sort(key=lambda t: t[0])

        # Equal-count windowing (quantile-based) rather than equal-time
        n = len(tuples)
        per_win = max(self.config.min_obs_per_window, n // self.config.num_windows)
        rhos: list[Optional[float]] = []
        for i in range(self.config.num_windows):
            start = i * per_win
            end = (i + 1) * per_win if i < self.config.num_windows - 1 else n
            if end - start < self.config.min_obs_per_window:
                rhos.append(None)
                continue
            window = tuples[start:end]
            xs = np.array([t[1] for t in window], dtype=float)
            ys = np.array([t[2] for t in window], dtype=float)
            if np.std(xs) < 1e-10 or np.std(ys) < 1e-10:
                rhos.append(None)
                continue
            rho, _ = stats.spearmanr(xs, ys)
            rhos.append(None if np.isnan(rho) else float(rho))

        return rhos

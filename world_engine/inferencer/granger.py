"""
WE-3b: Causal Inferencer (Granger causality)

Determines causal direction for correlated signal pairs using the pooled-panel
Granger causality approach: pool first-differences of each signal across all
entities, then test whether lagged source values improve the prediction of
target values beyond what target's own lags explain.

Why pooled panel: at LEARN maturity stage entities typically have only 2-3
assessments each, which is insufficient for per-entity time-series Granger.
Pooling across 50+ entities yields enough first-difference observations for
a meaningful test.

Output for each candidate: direction (a_causes_b, b_causes_a, bidirectional,
or contemporaneous), lag in months, and the F-statistic / p-value.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

import numpy as np
from scipy import stats
from sqlalchemy import text
from sqlalchemy.orm import Session

from world_engine.types import (
    CandidateRelationship,
    CausalDirection,
    DirectedCandidate,
)

logger = logging.getLogger("dsi.world_engine.inferencer.granger")


@dataclass
class GrangerConfig:
    """Tunable parameters for causal inference."""

    max_lag_months: int = 12
    """Consider lags up to this many months."""

    min_assessments_per_entity: int = 2
    """Entities need at least this many assessments to provide temporal data."""

    p_threshold: float = 0.05
    """Granger p-value threshold to accept directionality."""

    min_pooled_observations: int = 100
    """Minimum pooled first-difference observations across the population."""


class CausalInferencer:
    """Determines causal direction for correlated signal pairs."""

    def __init__(self, config: Optional[GrangerConfig] = None):
        self.config = config or GrangerConfig()

    def infer(
        self, candidates: list[CandidateRelationship], db: Session
    ) -> list[DirectedCandidate]:
        """Enrich each candidate with direction + lag.

        Candidates that cannot be tested (insufficient temporal data) are
        returned as CONTEMPORANEOUS with lag=None. The scanner already
        established correlation, so contemporaneous is the conservative
        default.
        """
        if not candidates:
            return []

        # Load temporal signal data once -- signal_code -> list of
        # (entity_name, timestamp, score) tuples, sorted by (entity, timestamp).
        temporal_data = self._load_temporal_data(db, [
            s for c in candidates for s in (c.source_signal, c.target_signal)
        ])

        directed: list[DirectedCandidate] = []
        for cand in candidates:
            direction, lag, f_stat, p_val = self._test_pair(
                temporal_data, cand.source_signal, cand.target_signal
            )
            effect_size = self._effect_size(cand.correlation_rho)
            directed.append(
                DirectedCandidate(
                    source_signal=cand.source_signal,
                    target_signal=cand.target_signal,
                    direction=direction,
                    lag_months=lag,
                    correlation_rho=cand.correlation_rho,
                    granger_f_statistic=f_stat,
                    granger_p_value=p_val,
                    effect_size=effect_size,
                    confounders_tested=[],
                    population_size=cand.population_size,
                    coverage_scope=cand.coverage_scope,
                )
            )

        logger.info("Inferencer: directed %d candidates", len(directed))
        return directed

    # ------------------------------------------------------------------
    # Temporal data loading
    # ------------------------------------------------------------------

    def _load_temporal_data(
        self, db: Session, signal_codes: list[str]
    ) -> dict[str, list[tuple[str, datetime, float]]]:
        """For each signal, return a list of (entity_name, timestamp, score)
        sorted by entity then timestamp. Only entities with >= 2 assessments
        are included."""
        if not signal_codes:
            return {}

        # DISTINCT signal codes to reduce the query footprint
        distinct_codes = list(set(signal_codes))

        # First, find entities with >= N assessments
        entity_filter_sql = """
            SELECT s.entity_name
            FROM submissions s
            JOIN model_versions m ON m.submission_id = s.id
            GROUP BY s.entity_name
            HAVING COUNT(m.id) >= :min_count
        """
        entity_rows = db.execute(
            text(entity_filter_sql),
            {"min_count": self.config.min_assessments_per_entity},
        ).scalars().all()
        if not entity_rows:
            return {code: [] for code in distinct_codes}

        # Load all signal scores for those entities, ordered
        sql = """
            SELECT
                s.entity_name,
                m.created_at,
                sig.code AS signal_code,
                mvs.score
            FROM submissions s
            JOIN model_versions m    ON m.submission_id = s.id
            JOIN model_version_signals mvs ON mvs.model_version_id = m.id
            JOIN signals sig         ON sig.id = mvs.signal_id
            WHERE s.entity_name = ANY(:entity_names)
              AND sig.code = ANY(:codes)
              AND mvs.score IS NOT NULL
            ORDER BY s.entity_name, m.created_at
        """
        rows = db.execute(
            text(sql),
            {"entity_names": list(entity_rows), "codes": distinct_codes},
        ).mappings().all()

        data: dict[str, list[tuple[str, datetime, float]]] = {}
        for row in rows:
            data.setdefault(row["signal_code"], []).append(
                (row["entity_name"], row["created_at"], float(row["score"]))
            )
        for code in distinct_codes:
            data.setdefault(code, [])
        return data

    # ------------------------------------------------------------------
    # Granger test
    # ------------------------------------------------------------------

    def _test_pair(
        self,
        data: dict[str, list[tuple[str, datetime, float]]],
        source: str,
        target: str,
    ) -> tuple[CausalDirection, Optional[float], Optional[float], Optional[float]]:
        """Run Granger causality in both directions. Returns the best-fit
        direction + lag + F/p.

        Pooled panel approach:
        - For each entity with >= 2 observations of both source and target,
          take the first-differences (delta_source, delta_target).
        - Regress delta_target on lagged delta_source and lagged delta_target.
        - An F-test compares this to the restricted model (lags of target only).
        """
        source_series = data.get(source, [])
        target_series = data.get(target, [])

        # Build per-entity series
        by_entity: dict[str, dict[str, list[tuple[datetime, float]]]] = {}
        for entity, ts, val in source_series:
            by_entity.setdefault(entity, {}).setdefault("s", []).append((ts, val))
        for entity, ts, val in target_series:
            by_entity.setdefault(entity, {}).setdefault("t", []).append((ts, val))

        # Pool first-differences (lag-1) from every entity
        # Observation: (delta_target_t, delta_source_{t-1}, delta_target_{t-1})
        pooled_deltas: list[tuple[float, float, float]] = []
        pooled_delta_months: list[float] = []
        for series in by_entity.values():
            s_list = sorted(series.get("s", []), key=lambda x: x[0])
            t_list = sorted(series.get("t", []), key=lambda x: x[0])
            if len(s_list) < 2 or len(t_list) < 2:
                continue
            # Align by timestamp: take pairs at same index
            for i in range(1, min(len(s_list), len(t_list))):
                prev_s_ts, prev_s = s_list[i - 1]
                cur_s_ts, cur_s = s_list[i]
                prev_t_ts, prev_t = t_list[i - 1]
                cur_t_ts, cur_t = t_list[i]
                delta_s = cur_s - prev_s
                delta_t = cur_t - prev_t
                # Prior delta (for endogenous lag)
                if i >= 2:
                    prev_delta_t = t_list[i - 1][1] - t_list[i - 2][1]
                else:
                    prev_delta_t = 0.0
                pooled_deltas.append((delta_t, delta_s, prev_delta_t))
                # Average month gap
                avg_gap_days = (
                    (cur_s_ts - prev_s_ts).days + (cur_t_ts - prev_t_ts).days
                ) / 2.0
                pooled_delta_months.append(avg_gap_days / 30.0)

        if len(pooled_deltas) < self.config.min_pooled_observations:
            return CausalDirection.CONTEMPORANEOUS, None, None, None

        # Direction A->B: does delta_source predict delta_target?
        f_ab, p_ab = self._pooled_f_test(
            [(dt, ds, dt_prev) for dt, ds, dt_prev in pooled_deltas]
        )
        # Direction B->A: does delta_target predict delta_source?
        swapped = [(ds, dt, ds) for dt, ds, _ in pooled_deltas]
        f_ba, p_ba = self._pooled_f_test(swapped)

        # Average lag (months) between consecutive observations
        avg_lag = float(np.mean(pooled_delta_months)) if pooled_delta_months else None

        a_causes_b = p_ab is not None and p_ab < self.config.p_threshold
        b_causes_a = p_ba is not None and p_ba < self.config.p_threshold

        if a_causes_b and b_causes_a:
            return CausalDirection.BIDIRECTIONAL, avg_lag, float(max(f_ab, f_ba)), float(min(p_ab, p_ba))
        if a_causes_b:
            return CausalDirection.A_CAUSES_B, avg_lag, float(f_ab), float(p_ab)
        if b_causes_a:
            return CausalDirection.B_CAUSES_A, avg_lag, float(f_ba), float(p_ba)
        return CausalDirection.CONTEMPORANEOUS, None, None, None

    def _pooled_f_test(
        self, observations: list[tuple[float, float, float]]
    ) -> tuple[Optional[float], Optional[float]]:
        """F-test: does lagged source improve delta_target prediction?

        observations: list of (delta_target, lagged_delta_source, lagged_delta_target)

        Unrestricted: delta_target ~ lag_source + lag_target
        Restricted:   delta_target ~ lag_target
        """
        if len(observations) < 5:
            return None, None

        y = np.array([o[0] for o in observations], dtype=float)
        lag_s = np.array([o[1] for o in observations], dtype=float)
        lag_t = np.array([o[2] for o in observations], dtype=float)

        # Guard against zero variance (constant series)
        if np.std(y) < 1e-10 or np.std(lag_s) < 1e-10:
            return None, None

        # Unrestricted: [1, lag_s, lag_t]
        X_u = np.column_stack([np.ones_like(y), lag_s, lag_t])
        # Restricted: [1, lag_t]
        X_r = np.column_stack([np.ones_like(y), lag_t])

        try:
            beta_u, _, _, _ = np.linalg.lstsq(X_u, y, rcond=None)
            beta_r, _, _, _ = np.linalg.lstsq(X_r, y, rcond=None)
        except np.linalg.LinAlgError:
            return None, None

        resid_u = y - X_u @ beta_u
        resid_r = y - X_r @ beta_r
        rss_u = float(resid_u @ resid_u)
        rss_r = float(resid_r @ resid_r)

        if rss_u <= 0:
            return None, None

        n = len(y)
        q = 1  # number of restrictions (one extra parameter)
        k_u = X_u.shape[1]  # parameters in unrestricted
        df_num = q
        df_den = n - k_u
        if df_den <= 0:
            return None, None

        f_stat = ((rss_r - rss_u) / df_num) / (rss_u / df_den)
        if f_stat < 0:
            return None, None

        p_value = 1.0 - stats.f.cdf(f_stat, df_num, df_den)
        return float(f_stat), float(p_value)

    def _effect_size(self, rho: float) -> float:
        """Convert Spearman's rho to a conservative Cohen's d-equivalent.

        Rough heuristic: rho 0.1/0.3/0.5 maps to d ~ 0.2/0.6/1.15.
        Using r-to-d: d = 2r / sqrt(1 - r^2).
        """
        r = abs(rho)
        if r >= 0.999:
            return 5.0
        return float(2.0 * r / np.sqrt(1.0 - r * r))

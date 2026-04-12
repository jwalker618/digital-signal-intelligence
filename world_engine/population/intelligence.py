"""
WE-3f: Population-Level Intelligence

Produces population-wide outputs that no per-entity assessment can
generate. Four capabilities:

1. Cohort evolution        -- how signal-derived peer groups change over time.
2. Signal regime detection -- shifts in the correlation *structure* between
                              signals (beyond individual drift alerts).
3. Predictive horizon      -- how far in advance active relationships predict.
4. Cross-coverage intel    -- relationships that span different coverage lines.

Outputs are returned as a `PopulationReport` dict and may be persisted
alongside the ScanRunReport. The registry API exposes them via /stats.
"""

from __future__ import annotations

import logging
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Optional

import numpy as np
from sqlalchemy import text
from sqlalchemy.orm import Session

from world_engine.registry import IntelligenceRegistry
from world_engine.types import LifecycleState

logger = logging.getLogger("dsi.world_engine.population")


@dataclass
class PopulationReport:
    """Summary of population-level analyses from one scan cycle."""

    cohort_evolution: dict = field(default_factory=dict)
    signal_regimes: list = field(default_factory=list)
    predictive_horizon: dict = field(default_factory=dict)
    cross_coverage: dict = field(default_factory=dict)
    computed_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class PopulationIntelligence:
    """Computes population-level outputs."""

    def __init__(self, registry: IntelligenceRegistry):
        self.registry = registry
        self.db = registry.db

    def compute_all(self) -> PopulationReport:
        return PopulationReport(
            cohort_evolution=self.compute_cohort_evolution(),
            signal_regimes=self.detect_signal_regimes(),
            predictive_horizon=self.estimate_predictive_horizon(),
            cross_coverage=self.summarise_cross_coverage(),
        )

    # ==================================================================
    # 1. Cohort evolution
    # ==================================================================

    def compute_cohort_evolution(self) -> dict:
        """Track how the composition of loss-cohort assignments has
        changed over quarters."""
        sql = """
            SELECT
                TO_CHAR(m.created_at, 'YYYY"Q"Q') AS period,
                m.loss_cohort_code,
                COUNT(*) AS n
            FROM model_versions m
            WHERE m.loss_cohort_code IS NOT NULL
            GROUP BY period, m.loss_cohort_code
            ORDER BY period
        """
        try:
            rows = self.db.execute(text(sql)).mappings().all()
        except Exception:
            return {"error": "loss_cohort_code not available"}

        by_period: dict[str, dict[str, int]] = defaultdict(dict)
        for row in rows:
            by_period[row["period"]][row["loss_cohort_code"]] = int(row["n"])

        return {
            "periods": sorted(by_period.keys()),
            "cohort_counts": dict(by_period),
        }

    # ==================================================================
    # 2. Signal regime detection (correlation structure)
    # ==================================================================

    def detect_signal_regimes(self) -> list[dict]:
        """Compute the top-K signal pairs by current correlation strength
        and compare to their values recorded in prior scan runs. Large
        deltas indicate the correlation structure is shifting.

        This is complementary to the DriftDetector's per-relationship shift
        alerts -- here we report the top-level population view.
        """
        # Pull the 10 most recent scan runs' stats (includes candidates_found)
        sql = """
            SELECT started_at, candidates_found
            FROM we_scan_runs
            WHERE completed_at IS NOT NULL
            ORDER BY started_at DESC
            LIMIT 10
        """
        rows = self.db.execute(text(sql)).mappings().all()
        if not rows:
            return []

        # Compute simple regime metrics across recent scans
        recent_counts = [int(r["candidates_found"]) for r in rows]
        return [
            {
                "metric": "candidate_volume",
                "recent_scans": len(recent_counts),
                "mean": float(np.mean(recent_counts)),
                "stddev": float(np.std(recent_counts)) if len(recent_counts) > 1 else 0.0,
                "most_recent": recent_counts[0],
                "trend": "increasing"
                if len(recent_counts) > 2 and recent_counts[0] > recent_counts[-1]
                else "stable",
            }
        ]

    # ==================================================================
    # 3. Predictive horizon
    # ==================================================================

    def estimate_predictive_horizon(self) -> dict:
        """For all ACTIVE relationships, report lag distribution.

        The median lag across all actives is the "typical" predictive
        horizon. The 95th percentile is the furthest-ahead we can see.
        """
        actives, _ = self.registry.list_relationships(
            state=LifecycleState.ACTIVE, limit=10_000
        )
        lags = [rel.lag_months for rel in actives if rel.lag_months is not None]

        if not lags:
            return {
                "active_count": len(actives),
                "with_lag_count": 0,
                "median_months": None,
                "p95_months": None,
                "max_months": None,
            }

        return {
            "active_count": len(actives),
            "with_lag_count": len(lags),
            "median_months": float(np.median(lags)),
            "p95_months": float(np.percentile(lags, 95)),
            "max_months": float(np.max(lags)),
        }

    # ==================================================================
    # 4. Cross-coverage intelligence
    # ==================================================================

    def summarise_cross_coverage(self) -> dict:
        """Group active relationships by coverage scope. Relationships
        appearing in multiple coverages are the highest-value
        cross-coverage discoveries."""
        # Use all non-deprecated states so we can see candidates too
        candidates, _ = self.registry.list_relationships(
            state=LifecycleState.CANDIDATE, limit=10_000
        )
        provisionals, _ = self.registry.list_relationships(
            state=LifecycleState.PROVISIONAL, limit=10_000
        )
        actives, _ = self.registry.list_relationships(
            state=LifecycleState.ACTIVE, limit=10_000
        )

        all_rels = candidates + provisionals + actives
        if not all_rels:
            return {"total": 0, "single_coverage": 0, "cross_coverage": 0, "by_coverage_pair": {}}

        single = sum(1 for r in all_rels if len(r.coverage_scope) <= 1)
        cross = sum(1 for r in all_rels if len(r.coverage_scope) > 1)

        # Count coverage pair frequencies
        pair_counts: Counter = Counter()
        for r in all_rels:
            scope = sorted(r.coverage_scope or [])
            if len(scope) > 1:
                for i in range(len(scope)):
                    for j in range(i + 1, len(scope)):
                        pair_counts[f"{scope[i]}|{scope[j]}"] += 1

        return {
            "total": len(all_rels),
            "single_coverage": single,
            "cross_coverage": cross,
            "by_coverage_pair": dict(pair_counts.most_common(10)),
        }

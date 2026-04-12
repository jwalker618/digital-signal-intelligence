"""
WE-2b: Population-Level Consistency Aggregator

Batch process that rolls per-assessment consistency scores up to
population-level statistics and persists them in we_population_consistency.

Runs on-demand or scheduled (e.g. nightly). Cheap -- pure SQL aggregation
over we_consistency_scores.
"""

from __future__ import annotations

import logging
from collections import Counter
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

logger = logging.getLogger("dsi.world_engine.consistency.population")


class PopulationConsistencyAggregator:
    """Computes population-level consistency aggregates.

    Reads we_consistency_scores, aggregates, writes to we_population_consistency.
    """

    def __init__(self, db: Session):
        self.db = db

    def aggregate(
        self,
        coverage: Optional[str] = None,
        period: Optional[str] = None,
    ) -> dict:
        """Run an aggregation pass.

        Args:
            coverage: Limit to a single coverage line's assessments. If None,
                      aggregate all assessments.
            period: A period label (e.g. "2026-04" or "all"). Persisted as-is
                    on the output row -- used for trend queries.

        Returns a summary dict of the metrics that were persisted.
        """
        filters: list[str] = []
        params: dict = {}

        if coverage:
            # coverage lives on model_versions; join is expensive, so we
            # denormalise via assessment_id look-up per row -- or accept the
            # join. For the population-level query we do a subquery join.
            filters.append(
                "assessment_id IN (SELECT CAST(id AS TEXT) FROM model_versions WHERE coverage = :coverage)"
            )
            params["coverage"] = coverage

        where = (" WHERE " + " AND ".join(filters)) if filters else ""

        # Distributional summary (single query, five statistics)
        stats_sql = f"""
            SELECT
                COUNT(*)                                                 AS sample_size,
                AVG(overall_consistency)                                 AS mean,
                PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY overall_consistency) AS median,
                PERCENTILE_CONT(0.1) WITHIN GROUP (ORDER BY overall_consistency) AS p10,
                PERCENTILE_CONT(0.9) WITHIN GROUP (ORDER BY overall_consistency) AS p90,
                STDDEV_POP(overall_consistency)                          AS stddev
            FROM we_consistency_scores{where}
        """
        row = self.db.execute(text(stats_sql), params).mappings().first()

        sample_size = int(row["sample_size"] or 0)
        if sample_size == 0:
            # Still persist a row with sample_size=0 so period gaps are visible
            return self._persist(coverage, period, None, None, None, None, 0, {})

        # Most common divergent pairs (top 10) across population
        divergent_sql = f"""
            SELECT jsonb_array_elements_text(divergent_pairs) AS pair
            FROM we_consistency_scores{where}
        """
        divergent_rows = self.db.execute(text(divergent_sql), params).scalars().all()
        top_divergent = Counter(divergent_rows).most_common(10)

        # Cross-layer disagreement frequency
        cross_layer_sql = f"""
            SELECT cross_layer_divergence FROM we_consistency_scores{where}
        """
        cross_layer_rows = self.db.execute(text(cross_layer_sql), params).scalars().all()
        cross_layer_agg = self._summarise_cross_layer(cross_layer_rows)

        extra_metrics = {
            "stddev": float(row["stddev"]) if row["stddev"] is not None else 0.0,
            "top_divergent_pairs": [{"pair": p, "count": c} for p, c in top_divergent],
            "cross_layer": cross_layer_agg,
        }

        return self._persist(
            coverage=coverage,
            period=period,
            mean=float(row["mean"]) if row["mean"] is not None else None,
            median=float(row["median"]) if row["median"] is not None else None,
            p10=float(row["p10"]) if row["p10"] is not None else None,
            p90=float(row["p90"]) if row["p90"] is not None else None,
            sample_size=sample_size,
            metrics=extra_metrics,
        )

    def _persist(
        self,
        coverage: Optional[str],
        period: Optional[str],
        mean: Optional[float],
        median: Optional[float],
        p10: Optional[float],
        p90: Optional[float],
        sample_size: int,
        metrics: dict,
    ) -> dict:
        import json

        self.db.execute(
            text(
                """
                INSERT INTO we_population_consistency (
                    coverage, period,
                    mean_consistency, median_consistency,
                    p10_consistency, p90_consistency,
                    sample_size, metrics, computed_at
                ) VALUES (
                    :coverage, :period,
                    :mean, :median, :p10, :p90,
                    :sample_size, CAST(:metrics AS jsonb), :at
                )
                """
            ),
            {
                "coverage": coverage,
                "period": period or "all",
                "mean": mean,
                "median": median,
                "p10": p10,
                "p90": p90,
                "sample_size": sample_size,
                "metrics": json.dumps(metrics, default=str),
                "at": datetime.now(timezone.utc),
            },
        )

        return {
            "coverage": coverage,
            "period": period or "all",
            "mean": mean,
            "median": median,
            "p10": p10,
            "p90": p90,
            "sample_size": sample_size,
            "metrics": metrics,
        }

    def _summarise_cross_layer(self, rows: list[dict]) -> dict:
        """Average cross-layer consistency across the population."""
        if not rows:
            return {}

        # Each row is a dict like {"risk_vs_loss": 0.8, ...}. Aggregate
        # across all rows.
        keys: set[str] = set()
        for r in rows:
            if isinstance(r, dict):
                keys.update(r.keys())

        summary: dict[str, float] = {}
        for k in keys:
            vals = [r[k] for r in rows if isinstance(r, dict) and k in r]
            if vals:
                summary[k] = sum(vals) / len(vals)
        return summary

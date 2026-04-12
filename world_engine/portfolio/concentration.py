"""
WE-5b: ConcentrationDetector

Identifies hidden concentration risk across four dimensions:

1. Node concentration:
   A single shared external node connected to > threshold entities.
   E.g. "47 portfolio entities depend on AWS us-east-1".

2. Pathway concentration:
   Multiple entities sharing an active causal precursor pattern. When the
   precursor fires, correlated losses follow.

3. Derivative correlation:
   Portfolio-wide derivative trends (systemic drift) -- when the aggregate
   mean score is shifting or variance is collapsing across entities.

4. Cohort concentration:
   Over-representation of a single signal-derived cohort. Adverse-selection
   risk.

Each concentration produces a PortfolioConcentration row with severity
(0-1), affected entities, and a human-readable detail string. Persisted
via the registry so the appetite evaluator + commercial layer can consume it.
"""

from __future__ import annotations

import logging
from collections import Counter, defaultdict
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

from world_engine.portfolio.types import PortfolioGraph
from world_engine.types import PortfolioConcentration

logger = logging.getLogger("dsi.world_engine.portfolio.concentration")


# Thresholds (tunable). Fractions of the portfolio entity count.
NODE_CONCENTRATION_FRACTION = 0.30       # > 30% of entities sharing a node = concentration
PATHWAY_CONCENTRATION_FRACTION = 0.20
COHORT_CONCENTRATION_FRACTION = 0.50
DERIVATIVE_Z_THRESHOLD = 2.0              # std devs


class ConcentrationDetector:
    """Identifies hidden concentration risk in the Portfolio Graph."""

    def __init__(self, db: Optional[Session] = None):
        self.db = db

    def detect(self, portfolio: PortfolioGraph) -> list[PortfolioConcentration]:
        """Run all four detection dimensions. Returns a list of
        PortfolioConcentration (not persisted -- caller persists)."""
        if portfolio.entity_count < 2:
            return []

        alerts: list[PortfolioConcentration] = []
        alerts.extend(self._detect_node_concentration(portfolio))
        alerts.extend(self._detect_pathway_concentration(portfolio))
        alerts.extend(self._detect_cohort_concentration(portfolio))
        alerts.extend(self._detect_derivative_correlation(portfolio))

        logger.info(
            "ConcentrationDetector: %d alerts across %d entities",
            len(alerts),
            portfolio.entity_count,
        )
        return alerts

    # ==================================================================
    # 1. Node concentration
    # ==================================================================

    def _detect_node_concentration(
        self, portfolio: PortfolioGraph
    ) -> list[PortfolioConcentration]:
        """Shared nodes connected to more than NODE_CONCENTRATION_FRACTION of entities."""
        alerts: list[PortfolioConcentration] = []
        threshold_count = max(
            2, int(portfolio.entity_count * NODE_CONCENTRATION_FRACTION)
        )

        # Use the pre-computed systemic_nodes from the graph
        for node in portfolio.systemic_nodes:
            if len(node.connected_entities) < threshold_count:
                continue

            # Severity: linear in fraction of entities affected
            severity = len(node.connected_entities) / portfolio.entity_count
            severity = min(1.0, severity)

            alerts.append(PortfolioConcentration(
                entity_id=portfolio.commercial_entity_id,
                dimension="node",
                detail=(
                    f"{len(node.connected_entities)} of {portfolio.entity_count} "
                    f"entities depend on {node.node_type} '{node.label}'"
                ),
                severity=float(severity),
                affected_entities=list(node.connected_entities),
                computed_at=datetime.now(timezone.utc),
            ))

        return alerts

    # ==================================================================
    # 2. Pathway concentration
    # ==================================================================

    def _detect_pathway_concentration(
        self, portfolio: PortfolioGraph
    ) -> list[PortfolioConcentration]:
        """Count entities sharing each causal pathway edge.

        A pathway edge connects two entities that both sit in a precursor
        state for the SAME active relationship. If many entities share the
        same pathway, a single precursor firing produces correlated losses.
        """
        alerts: list[PortfolioConcentration] = []

        # Group causal_pathway_correlation edges by the weight (which encodes
        # the relationship's rho; same rel -> same rho). Build connected
        # components.
        from collections import defaultdict

        # Group edges by approximately equal weight (+/- 0.01), treating
        # them as coming from the same relationship.
        grouped: dict[str, set[str]] = defaultdict(set)
        for edge in portfolio.edges:
            if edge.edge_type != "causal_pathway_correlation":
                continue
            # Bucket by rounded weight to approximate "same relationship"
            bucket = f"pathway_{edge.weight:.2f}"
            grouped[bucket].update(edge.entities)

        threshold_count = max(
            2, int(portfolio.entity_count * PATHWAY_CONCENTRATION_FRACTION)
        )

        for bucket, entities in grouped.items():
            if len(entities) < threshold_count:
                continue
            severity = min(1.0, len(entities) / portfolio.entity_count)
            alerts.append(PortfolioConcentration(
                entity_id=portfolio.commercial_entity_id,
                dimension="pathway",
                detail=(
                    f"{len(entities)} entities share causal pathway pattern "
                    f"(bucket {bucket})"
                ),
                severity=float(severity),
                affected_entities=sorted(entities),
                computed_at=datetime.now(timezone.utc),
            ))
        return alerts

    # ==================================================================
    # 3. Cohort concentration
    # ==================================================================

    def _detect_cohort_concentration(
        self, portfolio: PortfolioGraph
    ) -> list[PortfolioConcentration]:
        """Over-representation of a single loss-cohort. Requires DB access
        to pull cohort codes from model_versions."""
        if self.db is None or not portfolio.entity_names:
            return []

        sql = """
            SELECT DISTINCT ON (s.entity_name)
                s.entity_name, m.loss_cohort_code, m.loss_cohort_name
            FROM submissions s
            JOIN model_versions m ON m.submission_id = s.id
            WHERE s.entity_name = ANY(:names) AND m.loss_cohort_code IS NOT NULL
            ORDER BY s.entity_name, m.created_at DESC
        """
        try:
            rows = self.db.execute(
                text(sql), {"names": portfolio.entity_names}
            ).mappings().all()
        except Exception:
            return []

        if not rows:
            return []

        cohort_to_entities: dict[str, list[str]] = defaultdict(list)
        for row in rows:
            cohort_to_entities[row["loss_cohort_code"]].append(row["entity_name"])

        alerts: list[PortfolioConcentration] = []
        threshold_count = max(
            2, int(portfolio.entity_count * COHORT_CONCENTRATION_FRACTION)
        )
        for cohort, entities in cohort_to_entities.items():
            if len(entities) < threshold_count:
                continue
            severity = len(entities) / portfolio.entity_count
            alerts.append(PortfolioConcentration(
                entity_id=portfolio.commercial_entity_id,
                dimension="cohort",
                detail=(
                    f"{len(entities)} of {portfolio.entity_count} entities in "
                    f"loss cohort '{cohort}' (adverse-selection risk)"
                ),
                severity=float(min(1.0, severity)),
                affected_entities=sorted(entities),
                computed_at=datetime.now(timezone.utc),
            ))
        return alerts

    # ==================================================================
    # 4. Derivative correlation (systemic drift)
    # ==================================================================

    def _detect_derivative_correlation(
        self, portfolio: PortfolioGraph
    ) -> list[PortfolioConcentration]:
        """Fires when aggregate derivative metrics cross concerning thresholds.

        Simple trigger: variance collapse (all entities scoring similarly =
        everyone exposed to the same state). Another trigger would be
        historical drift (current mean vs. 90-day back mean), but we need
        time-indexed snapshots for that -- deferred.
        """
        agg = portfolio.aggregate_derivatives or {}
        variance = agg.get("aggregate_score_variance")
        if variance is None:
            return []

        # Heuristic: variance < 50 across the portfolio = signals are
        # collapsing to the mean (limited diversification in signal profile).
        # Values are on a 0-100 scale so typical variance is 100-400.
        if variance > 50.0:
            return []

        severity = max(0.0, 1.0 - variance / 50.0)  # 0.0 at var=50, 1.0 at var=0
        return [PortfolioConcentration(
            entity_id=portfolio.commercial_entity_id,
            dimension="derivative",
            detail=(
                f"Portfolio signal variance collapsed to {variance:.1f} "
                f"(entities converging on shared profile)"
            ),
            severity=float(min(1.0, severity)),
            affected_entities=list(portfolio.entity_names),
            computed_at=datetime.now(timezone.utc),
        )]

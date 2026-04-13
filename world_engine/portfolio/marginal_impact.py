"""
WE-5e: Marginal Impact Analyser

Evaluates the portfolio impact of accepting a prospective submission.

Process:
1. Build the current Portfolio Graph (without the prospective entity).
2. Build a hypothetical Portfolio Graph including the prospective entity.
3. Run concentration detection on both.
4. Compare: which dimensions are newly flagged or worsened?
5. Identify systemic-node overlap (prospective entity's signals that
   connect to existing systemic nodes).

Output is advisory (flag / warning / accept). Pricing and appetite remain
the authoritative decision points; marginal impact is an early-warning
signal the underwriter reviews.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from world_engine.portfolio.concentration import ConcentrationDetector
from world_engine.portfolio.graph_builder import (
    PortfolioGraphBuilder,
    SHARED_JURISDICTION_SIGNAL_PATTERNS,
    SHARED_PARTNER_SIGNAL_PATTERNS,
    SHARED_TECHNOLOGY_SIGNAL_PATTERNS,
)
from world_engine.portfolio.types import MarginalImpactResult, PortfolioGraph

logger = logging.getLogger("dsi.world_engine.portfolio.marginal_impact")


class MarginalImpactAnalyser:
    """Scores the marginal impact of adding an entity to a portfolio."""

    def __init__(self, db: Session):
        self.db = db
        self.builder = PortfolioGraphBuilder(db)
        self.detector = ConcentrationDetector(db)

    def analyse(
        self,
        prospective_entity_name: str,
        prospective_signals: dict[str, float],
        commercial_entity_id: str,
    ) -> MarginalImpactResult:
        """Return a MarginalImpactResult for the prospective submission.

        The prospective entity does not need to exist in the database --
        we synthesise a graph row for it and add it to the current
        portfolio in-memory.
        """
        current = self.builder.build(commercial_entity_id)
        hypothetical = self._add_prospective(
            current, prospective_entity_name, prospective_signals
        )

        current_alerts = {
            self._alert_key(a): a for a in self.detector.detect(current)
        }
        new_alerts = {
            self._alert_key(a): a for a in self.detector.detect(hypothetical)
        }

        created: list[dict] = []
        worsened: list[dict] = []

        for key, alert in new_alerts.items():
            if key not in current_alerts:
                created.append({
                    "dimension": alert.dimension,
                    "detail": alert.detail,
                    "before_severity": 0.0,
                    "after_severity": alert.severity,
                })
                continue
            prior = current_alerts[key]
            if alert.severity > prior.severity + 1e-6:
                worsened.append({
                    "dimension": alert.dimension,
                    "detail": alert.detail,
                    "before_severity": prior.severity,
                    "after_severity": alert.severity,
                })

        # Identify systemic nodes the prospective entity touches
        systemic_overlap = self._compute_systemic_overlap(
            current, prospective_signals
        )

        # Recommendation policy
        reasoning: list[str] = []
        recommendation = "accept"
        if created:
            recommendation = "flag"
            reasoning.append(
                f"{len(created)} new concentration(s) would be created"
            )
        elif worsened:
            recommendation = "accept_with_warning"
            reasoning.append(
                f"{len(worsened)} existing concentration(s) would worsen"
            )
        elif len(systemic_overlap) >= 3:
            recommendation = "accept_with_warning"
            reasoning.append(
                f"Entity shares {len(systemic_overlap)} systemic nodes with existing portfolio"
            )

        return MarginalImpactResult(
            would_create_concentration=bool(created),
            would_worsen_concentration=bool(worsened),
            affected_dimensions=created + worsened,
            systemic_node_overlap=systemic_overlap,
            recommendation=recommendation,
            reasoning=reasoning,
        )

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _add_prospective(
        self,
        current: PortfolioGraph,
        prospective_entity_name: str,
        prospective_signals: dict[str, float],
    ) -> PortfolioGraph:
        """Return a copy of `current` with the prospective entity added.

        We mirror the logic from PortfolioGraphBuilder -- add an organisation
        node, then add edges to any shared-dependency node that already
        exists OR create a new shared node that the prospective entity is
        the first connected to (which won't trip concentration on its own).
        """
        import copy
        import uuid

        from world_engine.portfolio.types import PortfolioEdge, PortfolioNode

        new_graph = copy.deepcopy(current)
        new_graph.entity_count += 1
        new_graph.entity_names = list(new_graph.entity_names) + [prospective_entity_name]
        new_graph.built_at = datetime.now(timezone.utc)

        # Organisation node for prospective entity
        prospective_org_id = f"org:{prospective_entity_name}"
        new_graph.nodes.append(PortfolioNode(
            id=prospective_org_id,
            node_type="organisation",
            label=prospective_entity_name,
            entity_name=prospective_entity_name,
            is_shared=False,
        ))

        # Classify each signal as a possible shared dependency
        existing_shared_ids = {n.id: n for n in new_graph.nodes if n.is_shared}
        for signal_code in prospective_signals.keys():
            node_type, edge_type = self._classify_shared_signal(signal_code)
            if node_type is None:
                continue

            shared_node_id = f"shared:{signal_code}"
            if shared_node_id not in existing_shared_ids:
                # Prospective entity is the FIRST to depend on this signal --
                # create the node but there's no concentration yet.
                new_graph.nodes.append(PortfolioNode(
                    id=shared_node_id,
                    node_type=node_type,
                    label=signal_code,
                    entity_name=None,
                    is_shared=True,
                ))

            new_graph.edges.append(PortfolioEdge(
                id=str(uuid.uuid4()),
                source_id=prospective_org_id,
                target_id=shared_node_id,
                edge_type=edge_type,
                weight=0.5,
                is_inter_entity=True,
                entities=[prospective_entity_name],
            ))

        # Recompute systemic nodes so concentration detection sees the
        # updated connectivity.
        new_graph.systemic_nodes = self.builder._compute_systemic_nodes(
            new_graph.nodes, new_graph.edges
        )

        return new_graph

    def _classify_shared_signal(self, signal_code: str):
        code_lower = signal_code.lower()
        if any(p in code_lower for p in SHARED_TECHNOLOGY_SIGNAL_PATTERNS):
            return "asset", "shared_technology"
        if any(p in code_lower for p in SHARED_PARTNER_SIGNAL_PATTERNS):
            return "partner", "shared_partner"
        if any(p in code_lower for p in SHARED_JURISDICTION_SIGNAL_PATTERNS):
            return "jurisdiction", "shared_jurisdiction"
        return None, None

    def _compute_systemic_overlap(
        self,
        current: PortfolioGraph,
        prospective_signals: dict[str, float],
    ) -> list[str]:
        """Systemic nodes the prospective entity would connect to."""
        overlap: list[str] = []
        for node in current.systemic_nodes:
            # Shared node id is "shared:{signal_code}"
            if node.node_id.startswith("shared:"):
                code = node.node_id[len("shared:"):]
                if code in prospective_signals:
                    overlap.append(node.label)
        return overlap

    def _alert_key(self, alert) -> str:
        """Stable identity for a concentration alert (used for diffing)."""
        # Sort affected_entities to stabilise across runs
        affected_key = "|".join(sorted(alert.affected_entities or []))
        return f"{alert.dimension}:{alert.detail[:80]}:{affected_key}"

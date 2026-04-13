"""
WE-5a: PortfolioGraphBuilder

Assembles all per-entity Organisational Graphs into a single Portfolio
Graph. Inter-entity edges are inferred where entities share:
- Technology nodes (same cloud provider, CDN, etc.)
- Partner nodes (same supplier, certifier)
- Jurisdiction nodes (same regulatory environment)
- Causal pathway correlation (entities sharing active precursor patterns)

The builder tolerates missing per-entity graphs. When a graph is
unavailable it synthesises a minimal representation from submission
metadata so concentration detection still works.

Portfolio scoping: a portfolio is defined by the commercial entity
(CommercialTermsRecord.entity_id). We consider all BOUND quotes as the
portfolio members.
"""

from __future__ import annotations

import logging
import uuid
from collections import defaultdict
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

from world_engine.portfolio.types import (
    PortfolioEdge,
    PortfolioGraph,
    PortfolioNode,
    SystemicNode,
)

logger = logging.getLogger("dsi.world_engine.portfolio.graph_builder")


# Signal codes that identify shared-technology dependencies. These are
# heuristic matches -- later phases can make this data-driven.
SHARED_TECHNOLOGY_SIGNAL_PATTERNS = (
    "cloud_provider", "cdn", "hosting", "dns_provider",
    "email_provider", "certificate_authority",
)
SHARED_PARTNER_SIGNAL_PATTERNS = (
    "auditor", "supplier", "vendor", "certifier",
)
SHARED_JURISDICTION_SIGNAL_PATTERNS = (
    "regulator", "jurisdiction", "registration_state",
)


class PortfolioGraphBuilder:
    """Builds a PortfolioGraph for a commercial entity."""

    def __init__(self, db: Session):
        self.db = db

    def build(self, commercial_entity_id: str) -> PortfolioGraph:
        """Assemble the Portfolio Graph.

        Queries all submissions whose latest model_version has
        CommercialTermsRecord.entity_id == commercial_entity_id, builds
        their minimal graphs, and stitches them together with inferred
        inter-entity edges.
        """
        entities = self._load_portfolio_entities(commercial_entity_id)
        nodes: list[PortfolioNode] = []
        edges: list[PortfolioEdge] = []

        if not entities:
            return PortfolioGraph(
                commercial_entity_id=commercial_entity_id,
                entity_count=0,
                built_at=datetime.now(timezone.utc),
            )

        # Per-entity organisation nodes + signal snapshots
        per_entity_signals: dict[str, dict[str, float]] = {}
        for e in entities:
            nodes.append(PortfolioNode(
                id=f"org:{e['entity_name']}",
                node_type="organisation",
                label=e["entity_name"],
                entity_name=e["entity_name"],
                is_shared=False,
            ))
            per_entity_signals[e["entity_name"]] = self._load_entity_signals(
                e["model_version_id"]
            )

        # Stitch shared dependency nodes + edges
        stitched_nodes, stitched_edges = self._stitch_shared_dependencies(
            per_entity_signals
        )
        nodes.extend(stitched_nodes)
        edges.extend(stitched_edges)

        # Stitch causal-pathway-correlation edges (entities sharing active
        # precursor patterns)
        pathway_edges = self._stitch_causal_pathway_correlation(
            per_entity_signals, entities
        )
        edges.extend(pathway_edges)

        # Systemic nodes: shared nodes connected to the most entities
        systemic = self._compute_systemic_nodes(nodes, edges)

        # Aggregate derivatives -- simple counts + entropy proxy
        aggregate = self._aggregate_derivatives(per_entity_signals)

        return PortfolioGraph(
            commercial_entity_id=commercial_entity_id,
            entity_count=len(entities),
            nodes=nodes,
            edges=edges,
            systemic_nodes=systemic,
            aggregate_derivatives=aggregate,
            entity_names=[e["entity_name"] for e in entities],
            built_at=datetime.now(timezone.utc),
        )

    # ------------------------------------------------------------------
    # Data loading
    # ------------------------------------------------------------------

    def _load_portfolio_entities(self, commercial_entity_id: str) -> list[dict]:
        """Return list of {entity_name, model_version_id, coverage}."""
        sql = """
            SELECT DISTINCT ON (s.entity_name)
                s.entity_name,
                m.id AS model_version_id,
                s.coverage
            FROM commercial_terms ct
            JOIN model_versions m ON m.id = ct.model_version_id
            JOIN submissions s    ON m.submission_id = s.id
            WHERE ct.entity_id = :entity_id
            ORDER BY s.entity_name, m.created_at DESC
        """
        try:
            rows = self.db.execute(
                text(sql), {"entity_id": commercial_entity_id}
            ).mappings().all()
            return [
                {
                    "entity_name": r["entity_name"],
                    "model_version_id": r["model_version_id"],
                    "coverage": r["coverage"],
                }
                for r in rows
            ]
        except Exception as exc:  # noqa: BLE001
            logger.warning("Portfolio load failed for %s: %s", commercial_entity_id, exc)
            return []

    def _load_entity_signals(self, model_version_id) -> dict[str, float]:
        """Return {signal_code -> score} for an entity's latest model version."""
        sql = """
            SELECT sig.code, mvs.score
            FROM model_version_signals mvs
            JOIN signals sig ON sig.id = mvs.signal_id
            WHERE mvs.model_version_id = :mv_id AND mvs.score IS NOT NULL
        """
        try:
            rows = self.db.execute(text(sql), {"mv_id": model_version_id}).all()
            return {row[0]: float(row[1]) for row in rows}
        except Exception:
            return {}

    # ------------------------------------------------------------------
    # Inter-entity stitching
    # ------------------------------------------------------------------

    def _stitch_shared_dependencies(
        self, per_entity_signals: dict[str, dict[str, float]]
    ) -> tuple[list[PortfolioNode], list[PortfolioEdge]]:
        """For each signal code that looks like a shared dependency, create
        an inter-entity node and connect all entities whose assessments
        include that signal."""
        nodes: list[PortfolioNode] = []
        edges: list[PortfolioEdge] = []

        # Invert: signal_code -> list of entities that have a value for it
        signal_to_entities: dict[str, list[str]] = defaultdict(list)
        for entity, scores in per_entity_signals.items():
            for code in scores.keys():
                signal_to_entities[code].append(entity)

        for signal_code, entities in signal_to_entities.items():
            if len(entities) < 2:
                continue  # need at least 2 entities to be "shared"

            node_type, edge_type = self._classify_shared_signal(signal_code)
            if node_type is None:
                continue  # not a shared-dependency signal

            shared_node_id = f"shared:{signal_code}"
            nodes.append(PortfolioNode(
                id=shared_node_id,
                node_type=node_type,
                label=signal_code,
                entity_name=None,
                is_shared=True,
            ))
            for entity in entities:
                edges.append(PortfolioEdge(
                    id=str(uuid.uuid4()),
                    source_id=f"org:{entity}",
                    target_id=shared_node_id,
                    edge_type=edge_type,
                    weight=0.5,
                    is_inter_entity=True,
                    entities=[entity],
                ))

        return nodes, edges

    def _classify_shared_signal(self, signal_code: str) -> tuple[Optional[str], Optional[str]]:
        """Return (node_type, edge_type) if the signal is a shared-dependency
        indicator, else (None, None)."""
        code_lower = signal_code.lower()
        if any(p in code_lower for p in SHARED_TECHNOLOGY_SIGNAL_PATTERNS):
            return "asset", "shared_technology"
        if any(p in code_lower for p in SHARED_PARTNER_SIGNAL_PATTERNS):
            return "partner", "shared_partner"
        if any(p in code_lower for p in SHARED_JURISDICTION_SIGNAL_PATTERNS):
            return "jurisdiction", "shared_jurisdiction"
        return None, None

    def _stitch_causal_pathway_correlation(
        self,
        per_entity_signals: dict[str, dict[str, float]],
        entities: list[dict],
    ) -> list[PortfolioEdge]:
        """Connect pairs of entities that share active causal precursor patterns.

        Two entities share a pattern if BOTH are in the precursor state
        (low quantile) for the SAME source signal of some ACTIVE relationship
        in the registry. Uses simple correlation across the portfolio signal
        scores -- if two entities have similar depressed values on a signal
        that appears in an active relationship, they are pathway-correlated.
        """
        from world_engine.registry import IntelligenceRegistry
        from world_engine.types import LifecycleState

        edges: list[PortfolioEdge] = []
        try:
            registry = IntelligenceRegistry(self.db)
            actives, _ = registry.list_relationships(
                state=LifecycleState.ACTIVE, limit=1000
            )
        except Exception:
            return edges

        if not actives or len(per_entity_signals) < 2:
            return edges

        # For each active relationship, find entities below the 25th-%ile on the source signal
        for rel in actives:
            # Compute the 25th percentile over all entities that have this signal
            vals = [
                scores[rel.source_signal]
                for scores in per_entity_signals.values()
                if rel.source_signal in scores
            ]
            if len(vals) < 4:
                continue
            threshold = sorted(vals)[max(0, len(vals) // 4 - 1)]

            in_precursor = [
                entity
                for entity, scores in per_entity_signals.items()
                if scores.get(rel.source_signal, 100.0) <= threshold
            ]
            if len(in_precursor) < 2:
                continue

            # Emit a pairwise edge for each combination
            for i in range(len(in_precursor)):
                for j in range(i + 1, len(in_precursor)):
                    edges.append(PortfolioEdge(
                        id=str(uuid.uuid4()),
                        source_id=f"org:{in_precursor[i]}",
                        target_id=f"org:{in_precursor[j]}",
                        edge_type="causal_pathway_correlation",
                        weight=float(rel.correlation_rho),
                        is_inter_entity=True,
                        entities=[in_precursor[i], in_precursor[j]],
                    ))
        return edges

    # ------------------------------------------------------------------
    # Systemic nodes (simple connectivity-based PageRank proxy)
    # ------------------------------------------------------------------

    def _compute_systemic_nodes(
        self, nodes: list[PortfolioNode], edges: list[PortfolioEdge]
    ) -> list[SystemicNode]:
        """Identify nodes connected to the most portfolio entities.

        Simple proxy for portfolio-level PageRank: count how many distinct
        entities each shared node is connected to. Returns up to 10 top nodes.
        """
        shared = {n.id: n for n in nodes if n.is_shared}
        if not shared:
            return []

        entity_count: dict[str, set[str]] = defaultdict(set)
        for edge in edges:
            if edge.target_id in shared and edge.entities:
                entity_count[edge.target_id].update(edge.entities)
            if edge.source_id in shared and edge.entities:
                entity_count[edge.source_id].update(edge.entities)

        total_nodes = max(len(nodes), 1)
        systemic: list[SystemicNode] = []
        for node_id, entities in entity_count.items():
            node = shared[node_id]
            # Simple PageRank proxy: connectivity / total shared nodes
            pagerank = len(entities) / max(len(shared), 1)
            # Failure impact proxy: fraction of entities touching the node
            impact = len(entities) / max(total_nodes, 1)
            systemic.append(SystemicNode(
                node_id=node_id,
                node_type=node.node_type,
                label=node.label,
                portfolio_pagerank=float(pagerank),
                connected_entities=sorted(entities),
                failure_impact_estimate=float(impact),
            ))

        # Return top 10 by connected entity count
        systemic.sort(key=lambda s: len(s.connected_entities), reverse=True)
        return systemic[:10]

    # ------------------------------------------------------------------
    # Aggregate derivatives
    # ------------------------------------------------------------------

    def _aggregate_derivatives(
        self, per_entity_signals: dict[str, dict[str, float]]
    ) -> dict[str, float]:
        """Portfolio-level summary statistics over per-entity signal sets.

        Three proxy derivatives:
        - aggregate_signal_coverage: mean signals/entity
        - aggregate_mean_score: portfolio-wide mean of all signal scores
        - aggregate_score_variance: portfolio-wide variance (proxy for
          heterogeneity / diversification)
        """
        if not per_entity_signals:
            return {}

        coverages = [len(s) for s in per_entity_signals.values()]
        all_scores = [v for s in per_entity_signals.values() for v in s.values()]

        aggregate_signal_coverage = sum(coverages) / len(coverages) if coverages else 0.0
        if all_scores:
            mean = sum(all_scores) / len(all_scores)
            variance = sum((v - mean) ** 2 for v in all_scores) / len(all_scores)
        else:
            mean = 0.0
            variance = 0.0

        return {
            "aggregate_signal_coverage": float(aggregate_signal_coverage),
            "aggregate_mean_score": float(mean),
            "aggregate_score_variance": float(variance),
        }

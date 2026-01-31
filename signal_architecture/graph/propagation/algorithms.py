"""
Graph Propagation Algorithms

Implements the four graph operations from schemas/organisational_graph.yaml:

1. Authority Propagation (PageRank) - trust/ownership edges
2. Risk Propagation - dependency/data_flow edges
3. Exposure Aggregation - operates_in/ownership edges
4. Cohort Comparison - z-score peer comparison
"""

import logging
import math
from typing import Any, Dict, List, Optional, Set

from ..types import (
    Edge,
    EdgeType,
    Graph,
    Node,
    NodeType,
    PropagationResult,
)

logger = logging.getLogger("dsi.graph.propagation")


class PropagationEngine:
    """
    Executes graph propagation algorithms.

    All algorithms operate on the graph in-place, storing results
    in graph.propagation_results.
    """

    def run_all(self, graph: Graph) -> Dict[str, PropagationResult]:
        """Run all propagation algorithms on the graph."""
        results = {}
        results["authority"] = self.authority_propagation(graph)
        results["risk"] = self.risk_propagation(graph)
        results["exposure"] = self.exposure_aggregation(graph)
        return results

    def authority_propagation(
        self,
        graph: Graph,
        damping_factor: float = 0.85,
        max_iterations: int = 100,
        convergence_threshold: float = 0.0001,
    ) -> PropagationResult:
        """
        PageRank-style authority flow through trust and ownership edges.

        Authority propagates bidirectionally through trust edges and
        downstream through ownership edges. Entities with more high-quality
        trust relationships accumulate higher authority scores.

        Parameters from schema:
          damping_factor: 0.85
          max_iterations: 100
          convergence_threshold: 0.0001
        """
        # Build adjacency for trust and ownership edges
        applicable_edges = [
            e for e in graph.edges.values()
            if e.edge_type in (EdgeType.TRUST, EdgeType.OWNERSHIP)
        ]

        if not applicable_edges:
            return PropagationResult(
                algorithm="pagerank",
                scores={nid: 1.0 / max(graph.node_count, 1)
                        for nid in graph.nodes},
                iterations=0,
                converged=True,
            )

        node_ids = list(graph.nodes.keys())
        n = len(node_ids)
        if n == 0:
            return PropagationResult(algorithm="pagerank", converged=True)

        # Initialize scores uniformly
        scores = {nid: 1.0 / n for nid in node_ids}

        # Build incoming edge map (node_id → list of (source_id, weight))
        incoming: Dict[str, List[tuple]] = {nid: [] for nid in node_ids}
        outgoing_count: Dict[str, int] = {nid: 0 for nid in node_ids}

        for edge in applicable_edges:
            if edge.source_id in graph.nodes and edge.target_id in graph.nodes:
                w = edge.weight or 0.85
                incoming[edge.target_id].append((edge.source_id, w))
                outgoing_count[edge.source_id] = (
                    outgoing_count.get(edge.source_id, 0) + 1
                )

                # Bidirectional for trust edges
                if edge.edge_type == EdgeType.TRUST:
                    incoming[edge.source_id].append((edge.target_id, w))
                    outgoing_count[edge.target_id] = (
                        outgoing_count.get(edge.target_id, 0) + 1
                    )

        # Iterate PageRank
        converged = False
        iterations = 0
        delta = 0.0

        for iteration in range(max_iterations):
            iterations = iteration + 1
            new_scores = {}

            for nid in node_ids:
                rank_sum = 0.0
                for source_id, weight in incoming[nid]:
                    out_count = max(outgoing_count.get(source_id, 1), 1)
                    rank_sum += (scores[source_id] / out_count) * weight

                new_scores[nid] = (1 - damping_factor) / n + damping_factor * rank_sum

            # Check convergence
            delta = sum(
                abs(new_scores[nid] - scores[nid]) for nid in node_ids
            )

            scores = new_scores

            if delta < convergence_threshold:
                converged = True
                break

        logger.debug(
            f"PageRank completed: {iterations} iterations, "
            f"converged={converged}, delta={delta:.6f}"
        )

        return PropagationResult(
            algorithm="pagerank",
            scores=scores,
            iterations=iterations,
            converged=converged,
            convergence_delta=delta,
        )

    def risk_propagation(
        self,
        graph: Graph,
        max_hops: int = 3,
    ) -> PropagationResult:
        """
        Risk flow through dependency and data_flow edges.

        Risk propagates downstream: if a dependency fails, risk flows
        to the dependent entity. Weighted by edge criticality and
        decayed by hop distance.

        Parameters from schema:
          max_hops: 3
        """
        applicable_edges = [
            e for e in graph.edges.values()
            if e.edge_type in (EdgeType.DEPENDENCY, EdgeType.DATA_FLOW)
        ]

        if not applicable_edges:
            return PropagationResult(
                algorithm="risk_propagation",
                scores={nid: 0.0 for nid in graph.nodes},
                converged=True,
            )

        # Initialize risk scores from node signals
        risk_scores: Dict[str, float] = {}
        for nid, node in graph.nodes.items():
            if node.signals:
                # Invert: low signal scores = high risk
                avg = node.signal_mean()
                risk_scores[nid] = max(0, 100.0 - avg)
            else:
                risk_scores[nid] = 0.0

        # Build downstream adjacency (target → sources that depend on it)
        # If target fails, risk flows to sources
        downstream: Dict[str, List[tuple]] = {
            nid: [] for nid in graph.nodes
        }
        for edge in applicable_edges:
            if edge.source_id in graph.nodes and edge.target_id in graph.nodes:
                w = edge.weight or 0.70
                # Source depends on target → target failure impacts source
                downstream[edge.target_id].append((edge.source_id, w))

        # Propagate risk through hops
        propagated = dict(risk_scores)
        for hop in range(max_hops):
            decay = 1.0 / (hop + 1)  # Decay by distance
            updates = {}
            for target_id, dependents in downstream.items():
                target_risk = propagated.get(target_id, 0)
                if target_risk > 0:
                    for source_id, weight in dependents:
                        added_risk = target_risk * weight * decay
                        current = updates.get(source_id, 0)
                        updates[source_id] = current + added_risk

            for nid, added in updates.items():
                propagated[nid] = propagated.get(nid, 0) + added

        # Normalize to 0-100
        max_risk = max(propagated.values()) if propagated else 1.0
        if max_risk > 0:
            normalized = {
                nid: min(100.0, (v / max_risk) * 100.0)
                for nid, v in propagated.items()
            }
        else:
            normalized = propagated

        return PropagationResult(
            algorithm="risk_propagation",
            scores=normalized,
            iterations=max_hops,
            converged=True,
        )

    def exposure_aggregation(self, graph: Graph) -> PropagationResult:
        """
        Aggregate exposure across jurisdictions and assets.

        Uses weighted sum across operates_in and ownership edges.
        Jurisdiction complexity weights multiply the base exposure.
        """
        org = graph.get_root_organisation()
        if org is None:
            return PropagationResult(
                algorithm="exposure_aggregation",
                converged=True,
            )

        # Get jurisdiction complexity weights
        jurisdiction_scores: Dict[str, float] = {}
        for edge in graph.get_edges_by_type(EdgeType.OPERATES_IN):
            target = graph.get_node(edge.target_id)
            if target and target.node_type == NodeType.JURISDICTION:
                complexity = target.attributes.get("complexity_weight", 1.0)
                presence = edge.properties.get("presence_type", "branch")

                # Presence type weight
                presence_weights = {
                    "headquarters": 1.0,
                    "subsidiary": 0.8,
                    "branch": 0.5,
                    "remote_workforce": 0.3,
                    "customers_only": 0.1,
                }
                presence_weight = presence_weights.get(presence, 0.5)

                jurisdiction_scores[target.id] = complexity * presence_weight

        # Get asset counts by type
        asset_scores: Dict[str, float] = {}
        for edge in graph.get_edges_by_type(EdgeType.OWNERSHIP):
            target = graph.get_node(edge.target_id)
            if target and target.node_type == NodeType.ASSET:
                # Weight by asset criticality
                subtype = target.attributes.get("asset_subtype", "")
                asset_weights = {
                    "data_store": 1.0,
                    "application": 0.8,
                    "cloud_resource": 0.7,
                    "domain": 0.3,
                    "certificate": 0.2,
                    "ip_address": 0.1,
                }
                asset_scores[target.id] = asset_weights.get(subtype, 0.5)

        # Combine: total exposure = jurisdictions + assets
        all_scores = {**jurisdiction_scores, **asset_scores}

        # Organisation gets aggregate exposure score
        total_exposure = sum(all_scores.values())
        all_scores[org.id] = total_exposure

        return PropagationResult(
            algorithm="exposure_aggregation",
            scores=all_scores,
            iterations=1,
            converged=True,
        )

    def cohort_comparison(
        self,
        graph: Graph,
        cohort_stats: Optional[Dict[str, Dict[str, float]]] = None,
    ) -> PropagationResult:
        """
        Compare entity signals to peer cohort using z-scores.

        Each signal is compared to the cohort mean/stddev for the
        entity's industry/size/geography segment.

        Args:
            cohort_stats: Dict of signal_id → {"mean": float, "stddev": float}
        """
        if cohort_stats is None:
            return PropagationResult(
                algorithm="cohort_comparison",
                scores={},
                converged=True,
            )

        z_scores: Dict[str, float] = {}
        for node in graph.nodes.values():
            for sig in node.signals:
                if sig.signal_id in cohort_stats:
                    stats = cohort_stats[sig.signal_id]
                    mean = stats.get("mean", 50.0)
                    stddev = stats.get("stddev", 10.0)
                    if stddev > 0:
                        z = (sig.value - mean) / stddev
                        z_scores[f"{node.id}:{sig.signal_id}"] = z

        return PropagationResult(
            algorithm="cohort_comparison",
            scores=z_scores,
            iterations=1,
            converged=True,
        )

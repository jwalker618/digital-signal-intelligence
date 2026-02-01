"""
Organisational Graph Builder

Orchestrates the complete graph construction pipeline:
1. Create nodes from submission data
2. Create nodes from signal outputs
3. Infer edges between nodes
4. Compute behavioural derivatives
5. Run authority/risk propagation

Produces a complete Graph instance ready for scoring integration.
"""

import logging
from typing import Any, Dict, List, Optional

from .types import (
    DerivativeResult,
    Edge,
    Graph,
    Node,
    NodeType,
    PropagationResult,
    ProxyTier,
    SignalAttachment,
)
from .node_factory import NodeFactory
from .edge_inferencer import EdgeInferencer
from .derivatives import DerivativeCalculator
from .propagation import PropagationEngine

logger = logging.getLogger("dsi.graph.builder")


class GraphBuilder:
    """
    Builds a complete Organisational Graph from submission data
    and signal extraction outputs.

    Usage:
        builder = GraphBuilder()
        graph = builder.build(
            submission={"company_name": "Acme", "domain": "acme.com"},
            signal_outputs=signal_extraction_results,
        )
    """

    def __init__(self):
        self.node_factory = NodeFactory()
        self.edge_inferencer = EdgeInferencer()
        self.derivative_calculator = DerivativeCalculator()
        self.propagation_engine = PropagationEngine()

    def build(
        self,
        submission: Dict[str, Any],
        signal_outputs: Optional[Dict[str, Any]] = None,
        compute_derivatives: bool = True,
        run_propagation: bool = True,
        cohort_stats: Optional[Dict[str, Dict[str, float]]] = None,
    ) -> Graph:
        """
        Build a complete organisational graph.

        Args:
            submission: Submission data (company_name, domain, etc.)
            signal_outputs: Signal extraction results
            compute_derivatives: Whether to compute behavioural derivatives
            run_propagation: Whether to run propagation algorithms
            cohort_stats: Optional cohort statistics for drift/comparison

        Returns:
            Complete Graph with nodes, edges, derivatives, and propagation results
        """
        entity_id = submission.get(
            "entity_id",
            submission.get("company_name", "unknown"),
        )

        graph = Graph(entity_id=entity_id)

        # Step 1: Create nodes from submission
        submission_nodes = self.node_factory.create_nodes_from_submission(submission)
        for node in submission_nodes:
            graph.add_node(node)

        org = graph.get_root_organisation()

        # Step 2: Create nodes from signals
        if signal_outputs and org:
            signal_nodes = self.node_factory.create_nodes_from_signals(
                signal_outputs, org.id
            )
            for node in signal_nodes:
                if node.id not in graph.nodes:
                    graph.add_node(node)

            # Attach signal scores to nodes
            self._attach_signals_to_nodes(graph, signal_outputs)

        # Step 3: Infer edges
        edges = self.edge_inferencer.infer_edges(graph)
        for edge in edges:
            try:
                graph.add_edge(edge)
            except ValueError as e:
                logger.debug(f"Skipping edge: {e}")

        # Step 4: Compute derivatives
        if compute_derivatives:
            graph.derivatives = self.derivative_calculator.compute_all(graph)

        # Step 5: Run propagation
        if run_propagation:
            graph.propagation_results = self.propagation_engine.run_all(graph)

            # Cohort comparison if stats available
            if cohort_stats:
                graph.propagation_results["cohort"] = (
                    self.propagation_engine.cohort_comparison(graph, cohort_stats)
                )

        logger.info(
            f"Graph built for '{entity_id}': "
            f"{graph.node_count} nodes, {graph.edge_count} edges, "
            f"{len(graph.derivatives)} derivatives, "
            f"{len(graph.propagation_results)} propagations"
        )

        return graph

    def _attach_signals_to_nodes(
        self,
        graph: Graph,
        signal_outputs: Dict[str, Any],
    ) -> None:
        """
        Attach signal scores to appropriate graph nodes.

        Signal outputs are attached to:
        - Organisation node: all aggregate scores
        - Asset nodes: technical infrastructure signals
        - Partner nodes: network authority signals
        """
        org = graph.get_root_organisation()
        if org is None:
            return

        for signal_id, output in signal_outputs.items():
            if not isinstance(output, dict):
                continue

            score = output.get("score", output.get("normalized_score"))
            if score is None:
                continue

            confidence = output.get("confidence", 0.8)
            proxy_str = output.get("proxy_tier", "INFERRED_PROXY")
            try:
                proxy = ProxyTier(proxy_str)
            except (ValueError, KeyError):
                proxy = ProxyTier.INFERRED_PROXY

            attachment = SignalAttachment(
                signal_id=signal_id,
                value=float(score),
                confidence=float(confidence),
                proxy_tier=proxy,
                source=output.get("source", ""),
            )

            # Attach to organisation node (primary)
            org.attach_signal(attachment)

            # Also attach to relevant typed nodes based on signal category
            category = output.get("category", "").lower()
            if "technical" in category or "infrastructure" in category:
                for asset in graph.get_nodes_by_type(NodeType.ASSET):
                    asset.attach_signal(attachment)
                    break  # Attach to first matching asset

    def build_from_workflow_result(
        self,
        workflow_result: Any,
        submission: Dict[str, Any],
    ) -> Graph:
        """
        Build graph from a completed workflow result.

        Extracts signal outputs from the workflow result and builds
        the complete graph.
        """
        signal_outputs = {}

        # Extract signal outputs from workflow result
        if hasattr(workflow_result, "signal_results"):
            for sr in workflow_result.signal_results:
                signal_outputs[sr.signal_id] = {
                    "score": sr.score,
                    "confidence": sr.confidence,
                    "proxy_tier": sr.proxy_tier if hasattr(sr, "proxy_tier") else "INFERRED_PROXY",
                    "raw_data": sr.raw_data if hasattr(sr, "raw_data") else {},
                    "category": sr.group_id if hasattr(sr, "group_id") else "",
                }

        return self.build(
            submission=submission,
            signal_outputs=signal_outputs,
        )

    def get_graph_scoring_inputs(self, graph: Graph) -> Dict[str, Any]:
        """
        Extract scoring-relevant metrics from the graph for
        integration with the risk/loss/exposure layers.

        Returns a dict that can be passed into the scoring pipeline.
        """
        result: Dict[str, Any] = {
            "node_count": graph.node_count,
            "edge_count": graph.edge_count,
        }

        # Authority scores
        authority = graph.propagation_results.get("authority")
        if authority and authority.scores:
            org = graph.get_root_organisation()
            if org:
                result["authority_score"] = authority.scores.get(org.id, 0.0)
            result["authority_converged"] = authority.converged

        # Risk propagation
        risk = graph.propagation_results.get("risk")
        if risk and risk.scores:
            org = graph.get_root_organisation()
            if org:
                result["propagated_risk_score"] = risk.scores.get(org.id, 0.0)

        # Exposure aggregation
        exposure = graph.propagation_results.get("exposure")
        if exposure and exposure.scores:
            org = graph.get_root_organisation()
            if org:
                result["aggregate_exposure"] = exposure.scores.get(org.id, 0.0)

        # Derivative alerts
        derivative_alerts = []
        for name, deriv in graph.derivatives.items():
            if deriv.is_critical:
                derivative_alerts.append(f"CRITICAL:{name}={deriv.value:.3f}")
            elif deriv.is_warning:
                derivative_alerts.append(f"WARNING:{name}={deriv.value:.3f}")

        result["derivative_alerts"] = derivative_alerts
        result["fragility"] = (
            graph.derivatives["fragility"].value
            if "fragility" in graph.derivatives else 0.0
        )

        # Concentration risk
        if "concentration" in graph.derivatives:
            result["concentration_hhi"] = graph.derivatives["concentration"].value

        return result

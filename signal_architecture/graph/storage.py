"""
Organisational Graph - Storage

Persist and retrieve graphs for trend analysis and audit trail.
Serializes graphs to JSON-compatible format for storage in
the model data file or external persistence layer.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from .types import (
    DerivativeResult,
    Edge,
    EdgeType,
    Graph,
    Node,
    NodeType,
    PropagationResult,
    ProxyTier,
    SignalAttachment,
)

logger = logging.getLogger("dsi.graph.storage")


class GraphSerializer:
    """Serializes and deserializes Graph instances to/from dicts."""

    def to_dict(self, graph: Graph) -> Dict[str, Any]:
        """Serialize a Graph to a JSON-compatible dict."""
        return {
            "entity_id": graph.entity_id,
            "version": graph.version,
            "created_at": (
                graph.created_at.isoformat() if graph.created_at else None
            ),
            "nodes": {
                nid: self._node_to_dict(node)
                for nid, node in graph.nodes.items()
            },
            "edges": {
                eid: self._edge_to_dict(edge)
                for eid, edge in graph.edges.items()
            },
            "derivatives": {
                name: self._derivative_to_dict(d)
                for name, d in graph.derivatives.items()
            },
            "propagation_results": {
                name: self._propagation_to_dict(p)
                for name, p in graph.propagation_results.items()
            },
            "summary": graph.summary(),
        }

    def from_dict(self, data: Dict[str, Any]) -> Graph:
        """Deserialize a Graph from a dict."""
        graph = Graph(
            entity_id=data["entity_id"],
            version=data.get("version", "1.0.0"),
        )

        if data.get("created_at"):
            graph.created_at = datetime.fromisoformat(data["created_at"])

        # Restore nodes
        for nid, ndata in data.get("nodes", {}).items():
            node = self._node_from_dict(nid, ndata)
            graph.nodes[nid] = node

        # Restore edges (skip validation since nodes are already loaded)
        for eid, edata in data.get("edges", {}).items():
            edge = self._edge_from_dict(eid, edata)
            graph.edges[eid] = edge

        # Restore derivatives
        for name, ddata in data.get("derivatives", {}).items():
            graph.derivatives[name] = self._derivative_from_dict(name, ddata)

        # Restore propagation results
        for name, pdata in data.get("propagation_results", {}).items():
            graph.propagation_results[name] = self._propagation_from_dict(
                name, pdata
            )

        return graph

    def _node_to_dict(self, node: Node) -> Dict[str, Any]:
        return {
            "node_type": node.node_type.value,
            "subtype": node.subtype,
            "attributes": node.attributes,
            "signals": [
                {
                    "signal_id": s.signal_id,
                    "value": s.value,
                    "confidence": s.confidence,
                    "proxy_tier": s.proxy_tier.value,
                    "source": s.source,
                }
                for s in node.signals
            ],
        }

    def _node_from_dict(self, nid: str, data: Dict) -> Node:
        signals = [
            SignalAttachment(
                signal_id=s["signal_id"],
                value=s["value"],
                confidence=s["confidence"],
                proxy_tier=ProxyTier(s["proxy_tier"]),
                source=s.get("source", ""),
            )
            for s in data.get("signals", [])
        ]

        return Node(
            id=nid,
            node_type=NodeType(data["node_type"]),
            subtype=data.get("subtype"),
            attributes=data.get("attributes", {}),
            signals=signals,
        )

    def _edge_to_dict(self, edge: Edge) -> Dict[str, Any]:
        return {
            "edge_type": edge.edge_type.value,
            "source_id": edge.source_id,
            "target_id": edge.target_id,
            "weight": edge.weight,
            "properties": edge.properties,
        }

    def _edge_from_dict(self, eid: str, data: Dict) -> Edge:
        return Edge(
            id=eid,
            edge_type=EdgeType(data["edge_type"]),
            source_id=data["source_id"],
            target_id=data["target_id"],
            weight=data.get("weight"),
            properties=data.get("properties", {}),
        )

    def _derivative_to_dict(self, d: DerivativeResult) -> Dict[str, Any]:
        return {
            "value": d.value,
            "status": d.status,
            "warning_threshold": d.warning_threshold,
            "critical_threshold": d.critical_threshold,
            "window_days": d.window_days,
            "is_warning": d.is_warning,
            "is_critical": d.is_critical,
            "components": d.components,
        }

    def _derivative_from_dict(
        self, name: str, data: Dict
    ) -> DerivativeResult:
        return DerivativeResult(
            name=name,
            value=data["value"],
            warning_threshold=data["warning_threshold"],
            critical_threshold=data["critical_threshold"],
            window_days=data.get("window_days", 0),
            components=data.get("components", {}),
        )

    def _propagation_to_dict(self, p: PropagationResult) -> Dict[str, Any]:
        return {
            "algorithm": p.algorithm,
            "scores": p.scores,
            "iterations": p.iterations,
            "converged": p.converged,
            "convergence_delta": p.convergence_delta,
        }

    def _propagation_from_dict(
        self, name: str, data: Dict
    ) -> PropagationResult:
        return PropagationResult(
            algorithm=data.get("algorithm", name),
            scores=data.get("scores", {}),
            iterations=data.get("iterations", 0),
            converged=data.get("converged", False),
            convergence_delta=data.get("convergence_delta", 0.0),
        )


class GraphStore:
    """
    Persist and retrieve graphs to/from disk.

    Stores graphs as JSON files in a specified directory,
    keyed by entity_id and timestamp for trend analysis.
    """

    def __init__(self, storage_dir: Optional[Path] = None):
        self.serializer = GraphSerializer()
        self.storage_dir = storage_dir

    def save(self, graph: Graph, path: Optional[Path] = None) -> Path:
        """Save graph to JSON file."""
        if path is None:
            if self.storage_dir is None:
                raise ValueError("No storage_dir configured and no path given")
            self.storage_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            safe_id = graph.entity_id.replace(" ", "_")[:50]
            path = self.storage_dir / f"graph_{safe_id}_{timestamp}.json"

        data = self.serializer.to_dict(graph)
        path.write_text(json.dumps(data, indent=2, default=str))
        logger.info(f"Graph saved to {path}")
        return path

    def load(self, path: Path) -> Graph:
        """Load graph from JSON file."""
        data = json.loads(path.read_text())
        graph = self.serializer.from_dict(data)
        logger.info(
            f"Graph loaded from {path}: "
            f"{graph.node_count} nodes, {graph.edge_count} edges"
        )
        return graph

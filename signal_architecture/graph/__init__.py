"""
DSI Organisational Graph Runtime

Computational representation of entity behaviour described in the DSI
Vision Paper. Transforms continuous digital signals into a coherent,
machine-readable topology enabling:
  - Causal simulation (World Model)
  - PageRank-style authority propagation
  - Behavioural derivative calculation (entropy, velocity, drift)

Based on schema: schemas/organisational_graph.yaml
"""

from .types import (
    Node,
    Edge,
    Graph,
    NodeType,
    EdgeType,
    ProxyTier,
    DerivativeResult,
    PropagationResult,
)
from .node_factory import NodeFactory
from .edge_inferencer import EdgeInferencer
from .graph_builder import GraphBuilder

__all__ = [
    "Node",
    "Edge",
    "Graph",
    "NodeType",
    "EdgeType",
    "ProxyTier",
    "DerivativeResult",
    "PropagationResult",
    "NodeFactory",
    "EdgeInferencer",
    "GraphBuilder",
]

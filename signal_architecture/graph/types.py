"""
Organisational Graph - Core Types

Defines Node, Edge, and Graph types aligned with
schemas/organisational_graph.yaml v1.0.0.

Node types: organisation, asset, partner, person, process, jurisdiction
Edge types: dependency, trust, data_flow, ownership, operates_in, employment
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple


class NodeType(Enum):
    ORGANISATION = "organisation"
    ASSET = "asset"
    PARTNER = "partner"
    PERSON = "person"
    PROCESS = "process"
    JURISDICTION = "jurisdiction"


class AssetSubtype(Enum):
    DOMAIN = "domain"
    IP_ADDRESS = "ip_address"
    CERTIFICATE = "certificate"
    CLOUD_RESOURCE = "cloud_resource"
    APPLICATION = "application"
    DATA_STORE = "data_store"


class PartnerSubtype(Enum):
    VENDOR = "vendor"
    CUSTOMER = "customer"
    CERTIFICATION_BODY = "certification_body"
    FINANCIAL_INSTITUTION = "financial_institution"
    TECHNOLOGY_PARTNER = "technology_partner"


class PersonSubtype(Enum):
    LEADERSHIP = "leadership"
    SECURITY_TEAM = "security_team"
    BOARD_MEMBER = "board_member"


class ProcessSubtype(Enum):
    HIRING = "hiring"
    SECURITY_OPERATIONS = "security_operations"
    COMPLIANCE = "compliance"
    INCIDENT_RESPONSE = "incident_response"


class JurisdictionSubtype(Enum):
    GEOGRAPHIC = "geographic"
    REGULATORY = "regulatory"


class EdgeType(Enum):
    DEPENDENCY = "dependency"
    TRUST = "trust"
    DATA_FLOW = "data_flow"
    OWNERSHIP = "ownership"
    OPERATES_IN = "operates_in"
    EMPLOYMENT = "employment"


class PropagationDirection(Enum):
    DOWNSTREAM = "downstream"
    BIDIRECTIONAL = "bidirectional"
    NONE = "none"


class Criticality(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class TrustType(Enum):
    CERTIFICATION = "certification"
    PARTNERSHIP = "partnership"
    CUSTOMER = "customer"
    ENDORSEMENT = "endorsement"


class DataClassification(Enum):
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"
    PII = "pii"
    PHI = "phi"
    PCI = "pci"


class ControlType(Enum):
    FULL = "full"
    MAJORITY = "majority"
    MINORITY = "minority"
    OPERATIONAL = "operational"


class PresenceType(Enum):
    HEADQUARTERS = "headquarters"
    SUBSIDIARY = "subsidiary"
    BRANCH = "branch"
    REMOTE_WORKFORCE = "remote_workforce"
    CUSTOMERS_ONLY = "customers_only"


class EmploymentType(Enum):
    EMPLOYEE = "employee"
    CONTRACTOR = "contractor"
    BOARD = "board"


class ProxyTier(Enum):
    DIRECT_OBSERVABLE = "DIRECT_OBSERVABLE"
    INFERRED_PROXY = "INFERRED_PROXY"
    COHORT_INFERENCE = "COHORT_INFERENCE"

    @property
    def confidence_weight(self) -> float:
        weights = {
            "DIRECT_OBSERVABLE": 1.0,
            "INFERRED_PROXY": 0.7,
            "COHORT_INFERENCE": 0.4,
        }
        return weights[self.value]


@dataclass
class SignalAttachment:
    """A signal value attached to a node."""
    signal_id: str
    value: float
    confidence: float
    proxy_tier: ProxyTier
    timestamp: Optional[datetime] = None
    source: str = ""


@dataclass
class Node:
    """A node in the organisational graph."""
    id: str
    node_type: NodeType
    attributes: Dict[str, Any] = field(default_factory=dict)
    signals: List[SignalAttachment] = field(default_factory=list)
    subtype: Optional[str] = None
    created_at: Optional[datetime] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()

    def attach_signal(self, signal: SignalAttachment):
        self.signals.append(signal)

    def get_signal(self, signal_id: str) -> Optional[SignalAttachment]:
        for s in self.signals:
            if s.signal_id == signal_id:
                return s
        return None

    def signal_mean(self) -> float:
        if not self.signals:
            return 0.0
        return sum(s.value for s in self.signals) / len(self.signals)

    def weighted_signal_mean(self) -> float:
        if not self.signals:
            return 0.0
        total_weight = sum(s.confidence * s.proxy_tier.confidence_weight
                          for s in self.signals)
        if total_weight == 0:
            return 0.0
        weighted = sum(
            s.value * s.confidence * s.proxy_tier.confidence_weight
            for s in self.signals
        )
        return weighted / total_weight


# Edge property defaults per schema
EDGE_DEFAULTS = {
    EdgeType.DEPENDENCY: {
        "propagation_direction": PropagationDirection.DOWNSTREAM,
        "default_weight": 0.70,
    },
    EdgeType.TRUST: {
        "propagation_direction": PropagationDirection.BIDIRECTIONAL,
        "default_weight": 0.85,
    },
    EdgeType.DATA_FLOW: {
        "propagation_direction": PropagationDirection.DOWNSTREAM,
        "default_weight": 0.60,
    },
    EdgeType.OWNERSHIP: {
        "propagation_direction": PropagationDirection.DOWNSTREAM,
        "default_weight": 0.90,
    },
    EdgeType.OPERATES_IN: {
        "propagation_direction": PropagationDirection.NONE,
        "default_weight": 0.0,
    },
    EdgeType.EMPLOYMENT: {
        "propagation_direction": PropagationDirection.BIDIRECTIONAL,
        "default_weight": 0.50,
    },
}

# Valid source → target types per schema
EDGE_VALID_CONNECTIONS: Dict[EdgeType, Tuple[Set[NodeType], Set[NodeType]]] = {
    EdgeType.DEPENDENCY: (
        {NodeType.ORGANISATION, NodeType.ASSET, NodeType.PROCESS},
        {NodeType.ASSET, NodeType.PARTNER, NodeType.PROCESS},
    ),
    EdgeType.TRUST: (
        {NodeType.ORGANISATION, NodeType.PARTNER},
        {NodeType.ORGANISATION, NodeType.PARTNER},
    ),
    EdgeType.DATA_FLOW: (
        {NodeType.ORGANISATION, NodeType.ASSET, NodeType.PROCESS},
        {NodeType.ASSET, NodeType.PARTNER, NodeType.JURISDICTION},
    ),
    EdgeType.OWNERSHIP: (
        {NodeType.ORGANISATION},
        {NodeType.ORGANISATION, NodeType.ASSET},
    ),
    EdgeType.OPERATES_IN: (
        {NodeType.ORGANISATION},
        {NodeType.JURISDICTION},
    ),
    EdgeType.EMPLOYMENT: (
        {NodeType.ORGANISATION},
        {NodeType.PERSON},
    ),
}


@dataclass
class Edge:
    """An edge in the organisational graph."""
    id: str
    edge_type: EdgeType
    source_id: str
    target_id: str
    properties: Dict[str, Any] = field(default_factory=dict)
    weight: Optional[float] = None
    created_at: Optional[datetime] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.weight is None:
            self.weight = EDGE_DEFAULTS[self.edge_type]["default_weight"]

    @property
    def propagation_direction(self) -> PropagationDirection:
        return EDGE_DEFAULTS[self.edge_type]["propagation_direction"]


@dataclass
class DerivativeResult:
    """Result of a behavioural derivative calculation."""
    name: str
    value: float
    warning_threshold: float
    critical_threshold: float
    window_days: int
    is_warning: bool = False
    is_critical: bool = False
    components: Dict[str, float] = field(default_factory=dict)
    timestamp: Optional[datetime] = None

    def __post_init__(self):
        self.is_warning = self.value >= self.warning_threshold
        self.is_critical = self.value >= self.critical_threshold
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()

    @property
    def status(self) -> str:
        if self.is_critical:
            return "CRITICAL"
        if self.is_warning:
            return "WARNING"
        return "NORMAL"


@dataclass
class PropagationResult:
    """Result of a graph propagation algorithm."""
    algorithm: str
    scores: Dict[str, float] = field(default_factory=dict)
    iterations: int = 0
    converged: bool = False
    convergence_delta: float = 0.0
    timestamp: Optional[datetime] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()


@dataclass
class Graph:
    """
    The Organisational Graph - a complete representation of an entity's
    observable digital behaviour topology.
    """
    entity_id: str
    nodes: Dict[str, Node] = field(default_factory=dict)
    edges: Dict[str, Edge] = field(default_factory=dict)
    derivatives: Dict[str, DerivativeResult] = field(default_factory=dict)
    propagation_results: Dict[str, PropagationResult] = field(default_factory=dict)
    created_at: Optional[datetime] = None
    version: str = "1.0.0"

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()

    def add_node(self, node: Node) -> None:
        self.nodes[node.id] = node

    def add_edge(self, edge: Edge) -> None:
        # Validate source and target exist
        if edge.source_id not in self.nodes:
            raise ValueError(f"Source node '{edge.source_id}' not in graph")
        if edge.target_id not in self.nodes:
            raise ValueError(f"Target node '{edge.target_id}' not in graph")

        # Validate connection types
        valid = EDGE_VALID_CONNECTIONS[edge.edge_type]
        source_type = self.nodes[edge.source_id].node_type
        target_type = self.nodes[edge.target_id].node_type
        if source_type not in valid[0]:
            raise ValueError(
                f"Edge type {edge.edge_type.value} does not allow "
                f"source type {source_type.value}"
            )
        if target_type not in valid[1]:
            raise ValueError(
                f"Edge type {edge.edge_type.value} does not allow "
                f"target type {target_type.value}"
            )

        self.edges[edge.id] = edge

    def get_node(self, node_id: str) -> Optional[Node]:
        return self.nodes.get(node_id)

    def get_edge(self, edge_id: str) -> Optional[Edge]:
        return self.edges.get(edge_id)

    def get_nodes_by_type(self, node_type: NodeType) -> List[Node]:
        return [n for n in self.nodes.values() if n.node_type == node_type]

    def get_edges_by_type(self, edge_type: EdgeType) -> List[Edge]:
        return [e for e in self.edges.values() if e.edge_type == edge_type]

    def get_outgoing_edges(self, node_id: str) -> List[Edge]:
        return [e for e in self.edges.values() if e.source_id == node_id]

    def get_incoming_edges(self, node_id: str) -> List[Edge]:
        return [e for e in self.edges.values() if e.target_id == node_id]

    def get_neighbors(self, node_id: str) -> List[str]:
        """Get all nodes connected to the given node."""
        neighbors = set()
        for e in self.edges.values():
            if e.source_id == node_id:
                neighbors.add(e.target_id)
            if e.target_id == node_id:
                neighbors.add(e.source_id)
        return list(neighbors)

    def get_root_organisation(self) -> Optional[Node]:
        """Get the root organisation node (the insured entity)."""
        orgs = self.get_nodes_by_type(NodeType.ORGANISATION)
        return orgs[0] if orgs else None

    @property
    def node_count(self) -> int:
        return len(self.nodes)

    @property
    def edge_count(self) -> int:
        return len(self.edges)

    def summary(self) -> Dict[str, Any]:
        """Summary statistics of the graph."""
        type_counts = {}
        for n in self.nodes.values():
            key = n.node_type.value
            type_counts[key] = type_counts.get(key, 0) + 1

        edge_counts = {}
        for e in self.edges.values():
            key = e.edge_type.value
            edge_counts[key] = edge_counts.get(key, 0) + 1

        return {
            "entity_id": self.entity_id,
            "total_nodes": self.node_count,
            "total_edges": self.edge_count,
            "node_types": type_counts,
            "edge_types": edge_counts,
            "derivatives_computed": list(self.derivatives.keys()),
            "propagations_run": list(self.propagation_results.keys()),
        }

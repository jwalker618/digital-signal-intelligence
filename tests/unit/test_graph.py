"""
Tests for signal_architecture/graph/ module

Tests the organisational graph runtime: types, node factory,
edge inferencer, derivatives, propagation, and graph builder.
"""

import pytest
import json
import tempfile
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from signal_architecture.graph.types import (
    Node,
    Edge,
    Graph,
    NodeType,
    EdgeType,
    ProxyTier,
    SignalAttachment,
    DerivativeResult,
    PropagationResult,
    EDGE_DEFAULTS,
    EDGE_VALID_CONNECTIONS,
)
from signal_architecture.graph.node_factory import NodeFactory
from signal_architecture.graph.edge_inferencer import EdgeInferencer
from signal_architecture.graph.derivatives.calculator import DerivativeCalculator
from signal_architecture.graph.propagation.algorithms import PropagationEngine
from signal_architecture.graph.graph_builder import GraphBuilder
from signal_architecture.graph.storage import GraphSerializer, GraphStore


# ============ Types Tests ============

class TestProxyTier:
    def test_confidence_weights(self):
        assert ProxyTier.DIRECT_OBSERVABLE.confidence_weight == 1.0
        assert ProxyTier.INFERRED_PROXY.confidence_weight == 0.7
        assert ProxyTier.COHORT_INFERENCE.confidence_weight == 0.4


class TestNode:
    def test_node_creation(self):
        node = Node(id="test", node_type=NodeType.ORGANISATION)
        assert node.id == "test"
        assert node.node_type == NodeType.ORGANISATION
        assert node.created_at is not None

    def test_attach_signal(self):
        node = Node(id="test", node_type=NodeType.ASSET)
        sig = SignalAttachment(
            signal_id="ssl_cert", value=85.0, confidence=0.9,
            proxy_tier=ProxyTier.DIRECT_OBSERVABLE
        )
        node.attach_signal(sig)
        assert len(node.signals) == 1

    def test_get_signal(self):
        node = Node(id="test", node_type=NodeType.ASSET)
        sig = SignalAttachment(
            signal_id="ssl_cert", value=85.0, confidence=0.9,
            proxy_tier=ProxyTier.DIRECT_OBSERVABLE
        )
        node.attach_signal(sig)
        found = node.get_signal("ssl_cert")
        assert found is not None
        assert found.value == 85.0
        assert node.get_signal("nonexistent") is None

    def test_signal_mean(self):
        node = Node(id="test", node_type=NodeType.ORGANISATION)
        node.attach_signal(SignalAttachment(
            signal_id="s1", value=80.0, confidence=1.0,
            proxy_tier=ProxyTier.DIRECT_OBSERVABLE
        ))
        node.attach_signal(SignalAttachment(
            signal_id="s2", value=60.0, confidence=1.0,
            proxy_tier=ProxyTier.DIRECT_OBSERVABLE
        ))
        assert node.signal_mean() == 70.0

    def test_signal_mean_empty(self):
        node = Node(id="test", node_type=NodeType.ORGANISATION)
        assert node.signal_mean() == 0.0

    def test_weighted_signal_mean(self):
        node = Node(id="test", node_type=NodeType.ORGANISATION)
        node.attach_signal(SignalAttachment(
            signal_id="s1", value=100.0, confidence=1.0,
            proxy_tier=ProxyTier.DIRECT_OBSERVABLE  # weight 1.0
        ))
        node.attach_signal(SignalAttachment(
            signal_id="s2", value=0.0, confidence=1.0,
            proxy_tier=ProxyTier.COHORT_INFERENCE  # weight 0.4
        ))
        mean = node.weighted_signal_mean()
        # Expected: (100*1.0*1.0 + 0*1.0*0.4) / (1.0 + 0.4) = 100/1.4
        assert abs(mean - 100.0 / 1.4) < 0.01


class TestEdge:
    def test_edge_creation(self):
        edge = Edge(
            id="e1", edge_type=EdgeType.TRUST,
            source_id="org1", target_id="partner1"
        )
        assert edge.weight == 0.85  # Default for trust
        assert edge.propagation_direction.value == "bidirectional"

    def test_default_weights(self):
        for edge_type in EdgeType:
            assert edge_type in EDGE_DEFAULTS


class TestGraph:
    def test_empty_graph(self):
        g = Graph(entity_id="test")
        assert g.node_count == 0
        assert g.edge_count == 0

    def test_add_node(self):
        g = Graph(entity_id="test")
        g.add_node(Node(id="n1", node_type=NodeType.ORGANISATION))
        assert g.node_count == 1

    def test_add_edge_validates_nodes(self):
        g = Graph(entity_id="test")
        g.add_node(Node(id="org1", node_type=NodeType.ORGANISATION))
        g.add_node(Node(id="partner1", node_type=NodeType.PARTNER))

        edge = Edge(
            id="e1", edge_type=EdgeType.TRUST,
            source_id="org1", target_id="partner1"
        )
        g.add_edge(edge)
        assert g.edge_count == 1

    def test_add_edge_missing_source(self):
        g = Graph(entity_id="test")
        g.add_node(Node(id="n1", node_type=NodeType.ORGANISATION))
        edge = Edge(
            id="e1", edge_type=EdgeType.TRUST,
            source_id="missing", target_id="n1"
        )
        with pytest.raises(ValueError, match="Source node"):
            g.add_edge(edge)

    def test_add_edge_invalid_types(self):
        g = Graph(entity_id="test")
        g.add_node(Node(id="p1", node_type=NodeType.PERSON))
        g.add_node(Node(id="j1", node_type=NodeType.JURISDICTION))
        # TRUST only allows org/partner → org/partner
        edge = Edge(
            id="e1", edge_type=EdgeType.TRUST,
            source_id="p1", target_id="j1"
        )
        with pytest.raises(ValueError):
            g.add_edge(edge)

    def test_get_nodes_by_type(self):
        g = Graph(entity_id="test")
        g.add_node(Node(id="a1", node_type=NodeType.ASSET))
        g.add_node(Node(id="a2", node_type=NodeType.ASSET))
        g.add_node(Node(id="o1", node_type=NodeType.ORGANISATION))
        assets = g.get_nodes_by_type(NodeType.ASSET)
        assert len(assets) == 2

    def test_get_outgoing_incoming_edges(self):
        g = Graph(entity_id="test")
        g.add_node(Node(id="o1", node_type=NodeType.ORGANISATION))
        g.add_node(Node(id="a1", node_type=NodeType.ASSET))
        g.add_edge(Edge(
            id="e1", edge_type=EdgeType.OWNERSHIP,
            source_id="o1", target_id="a1"
        ))
        assert len(g.get_outgoing_edges("o1")) == 1
        assert len(g.get_incoming_edges("a1")) == 1

    def test_get_neighbors(self):
        g = Graph(entity_id="test")
        g.add_node(Node(id="o1", node_type=NodeType.ORGANISATION))
        g.add_node(Node(id="a1", node_type=NodeType.ASSET))
        g.add_edge(Edge(
            id="e1", edge_type=EdgeType.OWNERSHIP,
            source_id="o1", target_id="a1"
        ))
        neighbors = g.get_neighbors("o1")
        assert "a1" in neighbors

    def test_summary(self):
        g = Graph(entity_id="test")
        g.add_node(Node(id="o1", node_type=NodeType.ORGANISATION))
        s = g.summary()
        assert s["total_nodes"] == 1
        assert s["entity_id"] == "test"


# ============ Node Factory Tests ============

class TestNodeFactory:
    @pytest.fixture
    def factory(self):
        return NodeFactory()

    def test_create_organisation(self, factory):
        node = factory.create_organisation(
            entity_id="acme", legal_name="Acme Corp",
            primary_domain="acme.com"
        )
        assert node.node_type == NodeType.ORGANISATION
        assert node.attributes["legal_name"] == "Acme Corp"

    def test_create_asset(self, factory):
        node = factory.create_asset("example.com", "domain")
        assert node.node_type == NodeType.ASSET
        assert node.subtype == "domain"

    def test_create_partner(self, factory):
        node = factory.create_partner("ISO", "certification_body", "tier_1")
        assert node.node_type == NodeType.PARTNER
        assert node.attributes["tier"] == "tier_1"

    def test_create_person(self, factory):
        node = factory.create_person("Jane CEO", "leadership", "CEO")
        assert node.node_type == NodeType.PERSON
        assert node.attributes["role_title"] == "CEO"

    def test_create_process(self, factory):
        node = factory.create_process("SecOps", "security_operations")
        assert node.node_type == NodeType.PROCESS

    def test_create_jurisdiction(self, factory):
        node = factory.create_jurisdiction("US", "geographic", 1.0)
        assert node.node_type == NodeType.JURISDICTION

    def test_create_nodes_from_submission(self, factory):
        submission = {
            "company_name": "Test Corp",
            "domain": "test.com",
            "country": "US",
        }
        nodes = factory.create_nodes_from_submission(submission)
        types = {n.node_type for n in nodes}
        assert NodeType.ORGANISATION in types
        assert NodeType.ASSET in types
        assert NodeType.JURISDICTION in types

    def test_create_nodes_from_signals(self, factory):
        signals = {
            "test_signal": {
                "score": 75,
                "raw_data": {
                    "subdomains": ["sub1.test.com", "sub2.test.com"],
                    "vendors": ["AWS"],
                    "leadership": [{"name": "Jane", "title": "CEO"}],
                }
            }
        }
        nodes = factory.create_nodes_from_signals(signals, "org:test")
        assert len(nodes) > 0


# ============ Edge Inferencer Tests ============

class TestEdgeInferencer:
    @pytest.fixture
    def inferencer(self):
        return EdgeInferencer()

    def test_infer_edges_basic(self, inferencer):
        g = Graph(entity_id="test")
        g.add_node(Node(id="org:test", node_type=NodeType.ORGANISATION))
        g.add_node(Node(id="asset:domain", node_type=NodeType.ASSET))
        g.add_node(Node(id="partner:iso", node_type=NodeType.PARTNER,
                        attributes={"partner_subtype": "certification_body"}))

        edges = inferencer.infer_edges(g)
        edge_types = {e.edge_type for e in edges}
        assert EdgeType.OWNERSHIP in edge_types
        assert EdgeType.TRUST in edge_types

    def test_infer_employment_edges(self, inferencer):
        g = Graph(entity_id="test")
        g.add_node(Node(id="org:test", node_type=NodeType.ORGANISATION))
        g.add_node(Node(id="person:jane", node_type=NodeType.PERSON,
                        attributes={"role_type": "leadership"}))

        edges = inferencer.infer_edges(g)
        emp_edges = [e for e in edges if e.edge_type == EdgeType.EMPLOYMENT]
        assert len(emp_edges) == 1

    def test_infer_operates_in(self, inferencer):
        g = Graph(entity_id="test")
        g.add_node(Node(id="org:test", node_type=NodeType.ORGANISATION,
                        attributes={"incorporation_jurisdiction": "US"}))
        g.add_node(Node(id="jur:us", node_type=NodeType.JURISDICTION,
                        attributes={"name": "US"}))

        edges = inferencer.infer_edges(g)
        ops = [e for e in edges if e.edge_type == EdgeType.OPERATES_IN]
        assert len(ops) == 1
        assert ops[0].properties["presence_type"] == "headquarters"

    def test_no_org_returns_empty(self, inferencer):
        g = Graph(entity_id="test")
        g.add_node(Node(id="asset:test", node_type=NodeType.ASSET))
        edges = inferencer.infer_edges(g)
        assert len(edges) == 0


# ============ Derivative Tests ============

class TestDerivativeCalculator:
    @pytest.fixture
    def calculator(self):
        return DerivativeCalculator()

    def _make_graph_with_signals(self, signal_values):
        g = Graph(entity_id="test")
        org = Node(id="org:test", node_type=NodeType.ORGANISATION)
        for i, val in enumerate(signal_values):
            org.attach_signal(SignalAttachment(
                signal_id=f"technical_signal_{i}",
                value=val, confidence=0.8,
                proxy_tier=ProxyTier.INFERRED_PROXY,
            ))
        g.add_node(org)
        return g

    def test_entropy_stable(self, calculator):
        g = self._make_graph_with_signals([50.0, 50.0, 50.0])
        result = calculator.compute_entropy(g)
        assert result.name == "entropy"
        assert result.value == 0.0
        assert result.status == "NORMAL"

    def test_entropy_chaotic(self, calculator):
        g = self._make_graph_with_signals([10.0, 90.0, 20.0, 80.0])
        result = calculator.compute_entropy(g)
        assert result.value > 0.0

    def test_velocity(self, calculator):
        g = Graph(entity_id="test")
        org = Node(id="org:test", node_type=NodeType.ORGANISATION)
        # Add growth signals
        org.attach_signal(SignalAttachment(
            signal_id="hiring_velocity", value=80.0,
            confidence=0.9, proxy_tier=ProxyTier.DIRECT_OBSERVABLE
        ))
        # Add governance signals
        org.attach_signal(SignalAttachment(
            signal_id="compliance_framework", value=60.0,
            confidence=0.9, proxy_tier=ProxyTier.DIRECT_OBSERVABLE
        ))
        g.add_node(org)
        result = calculator.compute_velocity(g)
        assert result.name == "velocity"

    def test_concentration_empty(self, calculator):
        g = Graph(entity_id="test")
        result = calculator.compute_concentration(g)
        assert result.value == 0.0

    def test_concentration_with_deps(self, calculator):
        g = Graph(entity_id="test")
        g.add_node(Node(id="org:test", node_type=NodeType.ORGANISATION))
        g.add_node(Node(id="a1", node_type=NodeType.ASSET))
        g.add_node(Node(id="p1", node_type=NodeType.PARTNER))
        # 3 deps all pointing to same target
        for i in range(3):
            g.edges[f"dep_{i}"] = Edge(
                id=f"dep_{i}", edge_type=EdgeType.DEPENDENCY,
                source_id="org:test", target_id="a1"
            )
        result = calculator.compute_concentration(g)
        assert result.value == 1.0  # All same target = HHI 1.0

    def test_fragility_composite(self, calculator):
        g = self._make_graph_with_signals([50.0, 50.0, 50.0])
        result = calculator.compute_fragility(g)
        assert result.name == "fragility"
        assert 0.0 <= result.value <= 1.0

    def test_compute_all(self, calculator):
        g = self._make_graph_with_signals([60.0, 70.0, 80.0])
        results = calculator.compute_all(g)
        assert "entropy" in results
        assert "velocity" in results
        assert "drift" in results
        assert "concentration" in results
        assert "fragility" in results

    def test_derivative_thresholds(self):
        d = DerivativeResult(
            name="test", value=0.20,
            warning_threshold=0.15, critical_threshold=0.30,
            window_days=90
        )
        assert d.is_warning is True
        assert d.is_critical is False
        assert d.status == "WARNING"


# ============ Propagation Tests ============

class TestPropagationEngine:
    @pytest.fixture
    def engine(self):
        return PropagationEngine()

    def test_pagerank_empty(self, engine):
        g = Graph(entity_id="test")
        result = engine.authority_propagation(g)
        assert result.converged is True

    def test_pagerank_simple(self, engine):
        g = Graph(entity_id="test")
        g.add_node(Node(id="o1", node_type=NodeType.ORGANISATION))
        g.add_node(Node(id="p1", node_type=NodeType.PARTNER))
        g.add_edge(Edge(
            id="e1", edge_type=EdgeType.TRUST,
            source_id="o1", target_id="p1"
        ))
        result = engine.authority_propagation(g)
        assert result.converged is True
        assert len(result.scores) == 2

    def test_risk_propagation(self, engine):
        g = Graph(entity_id="test")
        org = Node(id="o1", node_type=NodeType.ORGANISATION)
        org.attach_signal(SignalAttachment(
            signal_id="s1", value=80.0, confidence=1.0,
            proxy_tier=ProxyTier.DIRECT_OBSERVABLE
        ))
        g.add_node(org)
        asset = Node(id="a1", node_type=NodeType.ASSET)
        asset.attach_signal(SignalAttachment(
            signal_id="s2", value=30.0, confidence=1.0,
            proxy_tier=ProxyTier.DIRECT_OBSERVABLE
        ))
        g.add_node(asset)
        g.add_edge(Edge(
            id="e1", edge_type=EdgeType.DEPENDENCY,
            source_id="o1", target_id="a1"
        ))
        result = engine.risk_propagation(g)
        assert result.converged is True

    def test_exposure_aggregation(self, engine):
        g = Graph(entity_id="test")
        g.add_node(Node(id="o1", node_type=NodeType.ORGANISATION))
        g.add_node(Node(id="j1", node_type=NodeType.JURISDICTION,
                        attributes={"complexity_weight": 1.5}))
        g.add_edge(Edge(
            id="e1", edge_type=EdgeType.OPERATES_IN,
            source_id="o1", target_id="j1",
            properties={"presence_type": "headquarters"}
        ))
        result = engine.exposure_aggregation(g)
        assert "o1" in result.scores

    def test_cohort_comparison_no_stats(self, engine):
        g = Graph(entity_id="test")
        result = engine.cohort_comparison(g)
        assert result.converged is True

    def test_run_all(self, engine):
        g = Graph(entity_id="test")
        g.add_node(Node(id="o1", node_type=NodeType.ORGANISATION))
        results = engine.run_all(g)
        assert "authority" in results
        assert "risk" in results
        assert "exposure" in results


# ============ Graph Builder Tests ============

class TestGraphBuilder:
    @pytest.fixture
    def builder(self):
        return GraphBuilder()

    def test_build_basic(self, builder):
        submission = {
            "company_name": "Test Corp",
            "domain": "test.com",
            "country": "US",
        }
        graph = builder.build(submission)
        assert graph.node_count >= 1
        assert graph.entity_id == "Test Corp"

    def test_build_with_signals(self, builder):
        submission = {"company_name": "Acme", "domain": "acme.com"}
        signals = {
            "ssl_quality": {
                "score": 85, "confidence": 0.9,
                "proxy_tier": "DIRECT_OBSERVABLE",
                "category": "technical_infrastructure",
                "raw_data": {"subdomains": ["sub.acme.com"]}
            }
        }
        graph = builder.build(submission, signal_outputs=signals)
        assert graph.node_count >= 2
        assert graph.edge_count >= 0
        assert len(graph.derivatives) == 5
        assert len(graph.propagation_results) >= 1

    def test_build_without_derivatives(self, builder):
        submission = {"company_name": "Test"}
        graph = builder.build(
            submission, compute_derivatives=False, run_propagation=False
        )
        assert len(graph.derivatives) == 0
        assert len(graph.propagation_results) == 0

    def test_get_graph_scoring_inputs(self, builder):
        submission = {"company_name": "Test", "domain": "test.com"}
        graph = builder.build(submission)
        inputs = builder.get_graph_scoring_inputs(graph)
        assert "node_count" in inputs
        assert "derivative_alerts" in inputs
        assert "fragility" in inputs


# ============ Storage Tests ============

class TestGraphSerializer:
    @pytest.fixture
    def serializer(self):
        return GraphSerializer()

    def test_roundtrip(self, serializer):
        g = Graph(entity_id="test")
        g.add_node(Node(id="o1", node_type=NodeType.ORGANISATION))
        g.add_node(Node(id="a1", node_type=NodeType.ASSET, subtype="domain"))
        g.add_edge(Edge(
            id="e1", edge_type=EdgeType.OWNERSHIP,
            source_id="o1", target_id="a1"
        ))
        g.derivatives["entropy"] = DerivativeResult(
            name="entropy", value=0.1,
            warning_threshold=0.15, critical_threshold=0.30,
            window_days=90
        )

        data = serializer.to_dict(g)
        restored = serializer.from_dict(data)

        assert restored.entity_id == g.entity_id
        assert restored.node_count == g.node_count
        assert restored.edge_count == g.edge_count
        assert "entropy" in restored.derivatives

    def test_serialization_json_compatible(self, serializer):
        g = Graph(entity_id="test")
        g.add_node(Node(id="o1", node_type=NodeType.ORGANISATION))
        data = serializer.to_dict(g)
        # Should be JSON-serializable
        json_str = json.dumps(data, default=str)
        assert len(json_str) > 0


class TestGraphStore:
    def test_save_and_load(self, tmp_path):
        store = GraphStore(storage_dir=tmp_path)
        g = Graph(entity_id="test_entity")
        g.add_node(Node(id="o1", node_type=NodeType.ORGANISATION))

        path = store.save(g)
        assert path.exists()

        loaded = store.load(path)
        assert loaded.entity_id == "test_entity"
        assert loaded.node_count == 1

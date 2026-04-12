"""WE-5 Portfolio tests -- pure logic (no DB required where possible)."""

from datetime import datetime, timezone

import pytest

from world_engine.portfolio.graph_builder import PortfolioGraphBuilder
from world_engine.portfolio.concentration import ConcentrationDetector
from world_engine.portfolio.simulation import ScenarioSimulator
from world_engine.portfolio.types import (
    PortfolioEdge,
    PortfolioGraph,
    PortfolioNode,
    ScenarioDefinition,
    ScenarioShock,
    SystemicNode,
)


def _make_portfolio(entity_count=5, shared_nodes=0, with_pathway_edges=False):
    """Build a test portfolio graph."""
    entity_names = [f"entity_{i}" for i in range(entity_count)]
    nodes = [
        PortfolioNode(
            id=f"org:{name}",
            node_type="organisation",
            label=name,
            entity_name=name,
        )
        for name in entity_names
    ]
    edges = []
    systemic: list[SystemicNode] = []
    for s in range(shared_nodes):
        shared_id = f"shared:cloud_provider_{s}"
        nodes.append(PortfolioNode(
            id=shared_id,
            node_type="asset",
            label=f"cloud_provider_{s}",
            is_shared=True,
        ))
        # Connect all entities to this shared node
        for name in entity_names:
            edges.append(PortfolioEdge(
                id=f"e_{name}_{s}",
                source_id=f"org:{name}",
                target_id=shared_id,
                edge_type="shared_technology",
                is_inter_entity=True,
                entities=[name],
            ))
        systemic.append(SystemicNode(
            node_id=shared_id,
            node_type="asset",
            label=f"cloud_provider_{s}",
            portfolio_pagerank=1.0,
            connected_entities=list(entity_names),
            failure_impact_estimate=1.0,
        ))

    if with_pathway_edges:
        # Three entities share a causal pathway
        for i, j in [(0, 1), (1, 2), (0, 2)]:
            edges.append(PortfolioEdge(
                id=f"path_{i}_{j}",
                source_id=f"org:{entity_names[i]}",
                target_id=f"org:{entity_names[j]}",
                edge_type="causal_pathway_correlation",
                weight=0.55,
                is_inter_entity=True,
                entities=[entity_names[i], entity_names[j]],
            ))

    return PortfolioGraph(
        commercial_entity_id="test_commercial",
        entity_count=entity_count,
        nodes=nodes,
        edges=edges,
        systemic_nodes=systemic,
        entity_names=entity_names,
        built_at=datetime.now(timezone.utc),
    )


# =============================================================================
# Shared-signal classification
# =============================================================================


class TestSharedSignalClassification:
    def test_cloud_provider_classified_as_technology(self):
        builder = PortfolioGraphBuilder(db=None)
        node_type, edge_type = builder._classify_shared_signal("cloud_provider_aws")
        assert node_type == "asset"
        assert edge_type == "shared_technology"

    def test_auditor_classified_as_partner(self):
        builder = PortfolioGraphBuilder(db=None)
        node_type, edge_type = builder._classify_shared_signal("external_auditor")
        assert node_type == "partner"
        assert edge_type == "shared_partner"

    def test_regulator_classified_as_jurisdiction(self):
        builder = PortfolioGraphBuilder(db=None)
        node_type, edge_type = builder._classify_shared_signal("primary_regulator")
        assert node_type == "jurisdiction"
        assert edge_type == "shared_jurisdiction"

    def test_unrelated_signal_returns_none(self):
        builder = PortfolioGraphBuilder(db=None)
        node_type, edge_type = builder._classify_shared_signal("revenue_growth")
        assert node_type is None
        assert edge_type is None


class TestSystemicNodesComputation:
    def test_shared_node_touching_many_entities_is_systemic(self):
        portfolio = _make_portfolio(entity_count=5, shared_nodes=1)
        builder = PortfolioGraphBuilder(db=None)
        systemic = builder._compute_systemic_nodes(portfolio.nodes, portfolio.edges)
        assert len(systemic) == 1
        assert len(systemic[0].connected_entities) == 5
        assert systemic[0].portfolio_pagerank > 0

    def test_no_shared_nodes_returns_empty(self):
        portfolio = _make_portfolio(entity_count=5, shared_nodes=0)
        builder = PortfolioGraphBuilder(db=None)
        systemic = builder._compute_systemic_nodes(portfolio.nodes, portfolio.edges)
        assert systemic == []


class TestAggregateDerivatives:
    def test_empty_signals(self):
        builder = PortfolioGraphBuilder(db=None)
        assert builder._aggregate_derivatives({}) == {}

    def test_variance_computed(self):
        builder = PortfolioGraphBuilder(db=None)
        signals = {
            "e1": {"s1": 10.0, "s2": 20.0},
            "e2": {"s1": 50.0, "s2": 60.0},
        }
        agg = builder._aggregate_derivatives(signals)
        assert agg["aggregate_signal_coverage"] == 2.0
        assert agg["aggregate_mean_score"] == pytest.approx(35.0)
        assert agg["aggregate_score_variance"] > 0


# =============================================================================
# Concentration detection
# =============================================================================


class TestNodeConcentration:
    def test_fires_when_systemic_node_touches_many_entities(self):
        portfolio = _make_portfolio(entity_count=5, shared_nodes=1)
        detector = ConcentrationDetector(db=None)
        alerts = detector._detect_node_concentration(portfolio)
        assert len(alerts) == 1
        assert alerts[0].dimension == "node"
        assert alerts[0].severity == 1.0  # 5/5 entities

    def test_below_fraction_does_not_fire(self):
        # Only 1 of 10 entities connected
        portfolio = PortfolioGraph(
            commercial_entity_id="t",
            entity_count=10,
            entity_names=[f"e{i}" for i in range(10)],
            systemic_nodes=[SystemicNode(
                node_id="shared:x",
                node_type="asset",
                label="x",
                portfolio_pagerank=0.1,
                connected_entities=["e0"],
                failure_impact_estimate=0.1,
            )],
            built_at=datetime.now(timezone.utc),
        )
        detector = ConcentrationDetector(db=None)
        alerts = detector._detect_node_concentration(portfolio)
        assert alerts == []


class TestPathwayConcentration:
    def test_fires_when_pathway_covers_threshold_entities(self):
        portfolio = _make_portfolio(entity_count=5, shared_nodes=0, with_pathway_edges=True)
        # 3 entities share a pathway; 3/5 = 60% > 20% fraction
        detector = ConcentrationDetector(db=None)
        alerts = detector._detect_pathway_concentration(portfolio)
        assert len(alerts) == 1
        assert alerts[0].dimension == "pathway"


class TestDerivativeCorrelation:
    def test_fires_when_variance_collapses(self):
        portfolio = PortfolioGraph(
            commercial_entity_id="t",
            entity_count=5,
            entity_names=[f"e{i}" for i in range(5)],
            aggregate_derivatives={"aggregate_score_variance": 20.0},
            built_at=datetime.now(timezone.utc),
        )
        detector = ConcentrationDetector(db=None)
        alerts = detector._detect_derivative_correlation(portfolio)
        assert len(alerts) == 1
        assert alerts[0].dimension == "derivative"
        assert alerts[0].severity > 0

    def test_does_not_fire_with_healthy_variance(self):
        portfolio = PortfolioGraph(
            commercial_entity_id="t",
            entity_count=5,
            entity_names=[f"e{i}" for i in range(5)],
            aggregate_derivatives={"aggregate_score_variance": 200.0},
            built_at=datetime.now(timezone.utc),
        )
        detector = ConcentrationDetector(db=None)
        alerts = detector._detect_derivative_correlation(portfolio)
        assert alerts == []


class TestConcentrationIntegration:
    def test_small_portfolio_skipped(self):
        portfolio = _make_portfolio(entity_count=1)
        detector = ConcentrationDetector(db=None)
        assert detector.detect(portfolio) == []


# =============================================================================
# Scenario simulation
# =============================================================================


class TestScenarioSimulation:
    def test_direct_only_shock_hits_only_connected(self):
        portfolio = _make_portfolio(entity_count=3, shared_nodes=1)
        # Only entities connected to shared:cloud_provider_0 are hit
        simulator = ScenarioSimulator()
        scenario = ScenarioDefinition(
            name="Cloud outage",
            shocks=[ScenarioShock(
                target_type="signal",
                target_id="cloud_provider_0",
                magnitude=0.0,
                propagation="direct_only",
            )],
        )
        result = simulator.simulate(scenario, portfolio)
        # All 3 entities are connected to the shared node
        assert len(result.entity_impacts) == 3
        # Severity = 1.0 for complete failure (magnitude=0)
        assert all(i.severity == 1.0 for i in result.entity_impacts)

    def test_empty_portfolio_returns_empty(self):
        portfolio = _make_portfolio(entity_count=0)
        simulator = ScenarioSimulator()
        scenario = ScenarioDefinition(
            name="x",
            shocks=[ScenarioShock(target_type="node", target_id="shared:x", magnitude=-10.0)],
        )
        result = simulator.simulate(scenario, portfolio)
        assert result.entity_impacts == []
        assert result.aggregate_loss_estimate.expected_loss == 0.0

    def test_external_event_affects_all(self):
        portfolio = _make_portfolio(entity_count=3, shared_nodes=0)
        simulator = ScenarioSimulator()
        scenario = ScenarioDefinition(
            name="Market shock",
            shocks=[ScenarioShock(
                target_type="external_event",
                target_id="market_downturn",
                magnitude=-20.0,
                propagation="direct_only",
            )],
        )
        result = simulator.simulate(scenario, portfolio)
        assert len(result.entity_impacts) == 3

    def test_mitigation_paths_ranked_by_severity(self):
        portfolio = _make_portfolio(entity_count=3, shared_nodes=1)
        simulator = ScenarioSimulator()
        scenario = ScenarioDefinition(
            name="Cloud outage",
            shocks=[ScenarioShock(
                target_type="signal", target_id="cloud_provider_0",
                magnitude=0.0, propagation="direct_only",
            )],
        )
        result = simulator.simulate(scenario, portfolio)
        # All entities have severity 1.0, so all get non_renew recommendation
        assert all(m.action == "non_renew" for m in result.mitigation_paths)

    def test_concentration_amplification_above_one_for_shared(self):
        portfolio = _make_portfolio(entity_count=10, shared_nodes=1)
        simulator = ScenarioSimulator()
        scenario = ScenarioDefinition(
            name="Cloud outage",
            shocks=[ScenarioShock(
                target_type="signal", target_id="cloud_provider_0",
                magnitude=0.0, propagation="direct_only",
            )],
        )
        result = simulator.simulate(scenario, portfolio)
        # 10/10 entities affected; 100% vs baseline 10% = 10x amplification
        assert result.concentration_amplification >= 2.0

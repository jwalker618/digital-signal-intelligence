"""
P7: Performance Validation Benchmarks

Measures Python baseline performance and Rust speedups for:
- Graph algorithms (PageRank, risk propagation, exposure aggregation)
- Derivative calculations (entropy, velocity, drift, concentration, fragility)
- Config validation
- End-to-end workflow
"""

import random
import time
import statistics
from typing import Dict, List, Tuple
import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _time_fn(fn, *args, iterations=5, **kwargs) -> Dict:
    """Run a function multiple times and return timing stats."""
    times = []
    result = None
    for _ in range(iterations):
        start = time.perf_counter()
        result = fn(*args, **kwargs)
        elapsed = time.perf_counter() - start
        times.append(elapsed)
    return {
        "min_ms": min(times) * 1000,
        "max_ms": max(times) * 1000,
        "mean_ms": statistics.mean(times) * 1000,
        "median_ms": statistics.median(times) * 1000,
        "iterations": iterations,
        "result": result,
    }


def _make_graph_data(num_nodes: int, edge_density: float = 0.1):
    """Generate graph data for benchmarking."""
    node_ids = [f"node-{i}" for i in range(num_nodes)]
    signal_means = [random.uniform(20, 80) for _ in range(num_nodes)]
    node_types = [random.choice(["organisation", "asset", "person"]) for _ in range(num_nodes)]

    edges = []
    edge_types = ["trust", "dependency", "data_flow", "ownership"]
    for i in range(num_nodes):
        num_edges = max(1, int(num_nodes * edge_density))
        targets = random.sample(range(num_nodes), min(num_edges, num_nodes - 1))
        for t in targets:
            if t != i:
                edges.append((
                    node_ids[i],
                    node_ids[t],
                    random.uniform(0.3, 1.0),
                    random.choice(edge_types),
                ))

    return node_ids, signal_means, node_types, edges


# ---------------------------------------------------------------------------
# Python Baseline: Graph Algorithms
# ---------------------------------------------------------------------------

class TestPythonGraphBaseline:
    """Measure Python graph algorithm performance."""

    @pytest.mark.parametrize("num_nodes", [50, 200, 500])
    def test_python_pagerank(self, num_nodes):
        """Benchmark Python PageRank implementation."""
        from signal_architecture.graph.propagation.algorithms import PropagationEngine
        from signal_architecture.graph.graph_builder import GraphBuilder

        node_ids, signal_means, node_types, edges = _make_graph_data(num_nodes)

        # Build a graph object
        builder = GraphBuilder()
        submission = {
            "entity_id": f"bench-{num_nodes}",
            "entity_name": f"Bench Corp {num_nodes}",
            "assets": [{"name": f"Asset {i}", "type": "digital", "value": 1000}
                       for i in range(min(num_nodes // 5, 20))],
        }
        graph = builder.build(submission)
        engine = PropagationEngine()

        stats = _time_fn(engine.authority_propagation, graph)
        print(f"\nPython PageRank ({num_nodes} nodes): "
              f"median={stats['median_ms']:.2f}ms, min={stats['min_ms']:.2f}ms")
        assert stats["result"] is not None

    @pytest.mark.parametrize("num_nodes", [50, 200, 500])
    def test_python_risk_propagation(self, num_nodes):
        """Benchmark Python risk propagation."""
        from signal_architecture.graph.propagation.algorithms import PropagationEngine
        from signal_architecture.graph.graph_builder import GraphBuilder

        builder = GraphBuilder()
        submission = {
            "entity_id": f"bench-risk-{num_nodes}",
            "entity_name": f"Risk Corp {num_nodes}",
            "assets": [{"name": f"Asset {i}", "type": "digital", "value": 1000}
                       for i in range(min(num_nodes // 5, 20))],
        }
        graph = builder.build(submission)
        engine = PropagationEngine()

        stats = _time_fn(engine.risk_propagation, graph)
        print(f"\nPython RiskProp ({num_nodes} nodes): "
              f"median={stats['median_ms']:.2f}ms, min={stats['min_ms']:.2f}ms")
        assert stats["result"] is not None


# ---------------------------------------------------------------------------
# Python Baseline: Derivatives
# ---------------------------------------------------------------------------

class TestPythonDerivativesBaseline:
    """Measure Python derivative calculation performance."""

    def test_python_all_derivatives(self):
        """Benchmark Python derivative calculator."""
        from signal_architecture.graph.derivatives.calculator import DerivativeCalculator
        from signal_architecture.graph.graph_builder import GraphBuilder

        builder = GraphBuilder()
        submission = {
            "entity_id": "bench-deriv",
            "entity_name": "Derivatives Bench Corp",
            "assets": [
                {"name": f"System {i}", "type": "digital", "value": 1000000}
                for i in range(10)
            ],
        }
        graph = builder.build(submission)
        calc = DerivativeCalculator()

        stats = _time_fn(calc.compute_all, graph)
        print(f"\nPython All Derivatives: "
              f"median={stats['median_ms']:.2f}ms, min={stats['min_ms']:.2f}ms")
        assert stats["result"] is not None


# ---------------------------------------------------------------------------
# Rust Performance (if available)
# ---------------------------------------------------------------------------

class TestRustPerformance:
    """Measure Rust performance when dsi_core is available."""

    @pytest.fixture(autouse=True)
    def _check_rust(self):
        """Skip if Rust module not available."""
        try:
            import dsi_core
            if not dsi_core.RUST_AVAILABLE:
                pytest.skip("Rust dsi_core not compiled")
        except ImportError:
            pytest.skip("dsi_core not installed (run: maturin develop)")

    @pytest.mark.parametrize("num_nodes", [100, 500, 1000])
    def test_rust_pagerank(self, num_nodes):
        """Benchmark Rust PageRank."""
        from dsi_core import graph

        node_ids, signal_means, _, edges = _make_graph_data(num_nodes)
        edge_tuples = [(s, t, w, et) for s, t, w, et in edges]

        stats = _time_fn(
            graph.pagerank,
            node_ids, edge_tuples,
            damping_factor=0.85,
            max_iterations=100,
            convergence_threshold=0.0001,
        )
        print(f"\nRust PageRank ({num_nodes} nodes): "
              f"median={stats['median_ms']:.2f}ms, min={stats['min_ms']:.2f}ms")
        assert isinstance(stats["result"], dict)

    @pytest.mark.parametrize("num_nodes", [100, 500, 1000])
    def test_rust_risk_propagation(self, num_nodes):
        """Benchmark Rust risk propagation."""
        from dsi_core import graph

        node_ids, signal_means, _, edges = _make_graph_data(num_nodes)
        edge_tuples = [(s, t, w, et) for s, t, w, et in edges]

        stats = _time_fn(
            graph.risk_propagation,
            node_ids, signal_means, edge_tuples,
            max_hops=3,
        )
        print(f"\nRust RiskProp ({num_nodes} nodes): "
              f"median={stats['median_ms']:.2f}ms, min={stats['min_ms']:.2f}ms")
        assert isinstance(stats["result"], dict)

    def test_rust_all_derivatives(self):
        """Benchmark Rust derivative calculations."""
        from dsi_core import derivatives

        signal_values = [random.uniform(30, 70) for _ in range(50)]
        change_signals = [random.uniform(50, 80) for _ in range(20)]
        governance_signals = [random.uniform(40, 60) for _ in range(20)]
        signal_map = {f"s{i}": v for i, v in enumerate(signal_values)}
        dependency_targets = [f"target-{i % 5}" for i in range(30)]

        stats = _time_fn(
            derivatives.compute_all_derivatives,
            signal_values, change_signals, governance_signals,
            signal_map, dependency_targets,
            50.0,  # infra_health
        )
        print(f"\nRust All Derivatives: "
              f"median={stats['median_ms']:.2f}ms, min={stats['min_ms']:.2f}ms")
        assert isinstance(stats["result"], dict)

    def test_rust_config_validation(self):
        """Benchmark Rust config validation."""
        from dsi_core import validation
        from pathlib import Path

        config_files = list(Path("coverages").glob("*/config.yaml"))
        if not config_files:
            pytest.skip("No config files found")

        yaml_content = config_files[0].read_text()
        stats = _time_fn(validation.validate_config, yaml_content)
        print(f"\nRust Config Validation: "
              f"median={stats['median_ms']:.2f}ms, min={stats['min_ms']:.2f}ms")
        assert isinstance(stats["result"], dict)


# ---------------------------------------------------------------------------
# End-to-End Workflow Performance
# ---------------------------------------------------------------------------

class TestWorkflowPerformance:
    """Measure full pipeline latency."""

    def test_workflow_latency(self):
        """Benchmark full assessment workflow."""
        from layers.risk.workflow import run_assessment

        stats = _time_fn(
            run_assessment,
            entity_id="bench-workflow",
            coverage="cyber",
            entity_name="Benchmark Corp",
            skip_discovery=True,
            skip_input_validation=True,
            iterations=3,
        )
        print(f"\nFull Workflow (cyber): "
              f"median={stats['median_ms']:.2f}ms, min={stats['min_ms']:.2f}ms")
        assert stats["result"] is not None
        assert stats["median_ms"] < 30000  # Must complete within 30s

    def test_scoring_latency(self):
        """Benchmark scoring pipeline only."""
        from layers.risk.scorer import ModelScorer
        from infrastructure.models.compiler import get_config

        config = get_config("cyber")
        scorer = ModelScorer()

        stats = _time_fn(
            scorer.score_entity,
            entity_id="bench-scorer",
            config=config,
        )
        print(f"\nScoring Pipeline (cyber): "
              f"median={stats['median_ms']:.2f}ms, min={stats['min_ms']:.2f}ms")
        assert stats["result"] is not None

    def test_graph_builder_latency(self):
        """Benchmark graph construction."""
        from signal_architecture.graph.graph_builder import GraphBuilder

        builder = GraphBuilder()
        submission = {
            "entity_id": "bench-graph",
            "entity_name": "Graph Bench Corp",
            "domain": "example.com",
            "revenue": 100000000,
            "assets": [
                {"name": f"System {i}", "type": "digital", "value": 1000000}
                for i in range(20)
            ],
            "partners": [
                {"name": f"Partner {i}", "type": "vendor"}
                for i in range(10)
            ],
        }

        stats = _time_fn(builder.build, submission)
        print(f"\nGraph Builder: "
              f"median={stats['median_ms']:.2f}ms, min={stats['min_ms']:.2f}ms")
        assert stats["result"] is not None

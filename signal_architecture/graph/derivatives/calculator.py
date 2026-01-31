"""
Behavioural Derivative Calculator

Implements the five behavioural derivatives defined in
schemas/organisational_graph.yaml:

1. Entropy - Control decay (weighted stddev of deltas)
2. Velocity - Operational overload (ratio of change rates)
3. Drift - Peer divergence (Mahalanobis distance from cohort)
4. Concentration - Single-point-of-failure (Herfindahl index)
5. Fragility - Composite resilience (weighted combination)
"""

import logging
import math
from typing import Any, Dict, List, Optional

from ..types import (
    DerivativeResult,
    Edge,
    EdgeType,
    Graph,
    Node,
    NodeType,
)

logger = logging.getLogger("dsi.graph.derivatives")


class DerivativeCalculator:
    """
    Calculates behavioural derivatives for an organisational graph.

    All derivatives produce a scalar value that is compared against
    warning and critical thresholds from the schema.
    """

    def compute_all(self, graph: Graph) -> Dict[str, DerivativeResult]:
        """Compute all five derivatives for the graph."""
        results = {}
        results["entropy"] = self.compute_entropy(graph)
        results["velocity"] = self.compute_velocity(graph)
        results["drift"] = self.compute_drift(graph)
        results["concentration"] = self.compute_concentration(graph)
        results["fragility"] = self.compute_fragility(graph, results)
        return results

    def compute_entropy(self, graph: Graph) -> DerivativeResult:
        """
        Entropy: Control decay indicator.

        Measures how chaotic the organisation's digital footprint is
        by computing the weighted standard deviation of signal deltas
        across technical infrastructure and corporate footprint signals.

        High entropy = unmanaged asset proliferation, degrading controls.

        Calculation: weighted_stddev_of_deltas over 90-day window
        Thresholds: warning=0.15, critical=0.30
        """
        # Collect signal values from relevant nodes
        tech_signals = []
        corp_signals = []

        for node in graph.nodes.values():
            for sig in node.signals:
                if "technical" in sig.signal_id or "infrastructure" in sig.signal_id:
                    tech_signals.append(sig.value)
                elif "corporate" in sig.signal_id or "footprint" in sig.signal_id:
                    corp_signals.append(sig.value)

        all_signals = tech_signals + corp_signals
        if len(all_signals) < 2:
            return DerivativeResult(
                name="entropy",
                value=0.0,
                warning_threshold=0.15,
                critical_threshold=0.30,
                window_days=90,
                components={
                    "tech_signal_count": len(tech_signals),
                    "corp_signal_count": len(corp_signals),
                },
            )

        # Compute deltas between consecutive signals
        deltas = [
            abs(all_signals[i] - all_signals[i - 1])
            for i in range(1, len(all_signals))
        ]

        if not deltas:
            return DerivativeResult(
                name="entropy",
                value=0.0,
                warning_threshold=0.15,
                critical_threshold=0.30,
                window_days=90,
            )

        # Weighted stddev of deltas (normalized to 0-1 scale)
        mean_delta = sum(deltas) / len(deltas)
        variance = sum((d - mean_delta) ** 2 for d in deltas) / len(deltas)
        stddev = math.sqrt(variance)

        # Normalize: divide by 100 (signal range) to get 0-1 scale
        entropy_value = stddev / 100.0

        return DerivativeResult(
            name="entropy",
            value=entropy_value,
            warning_threshold=0.15,
            critical_threshold=0.30,
            window_days=90,
            components={
                "mean_delta": mean_delta,
                "stddev": stddev,
                "signal_count": len(all_signals),
            },
        )

    def compute_velocity(self, graph: Graph) -> DerivativeResult:
        """
        Velocity: Operational overload indicator.

        Ratio of change-indicating signals to governance-indicating signals.
        Velocity > 1.0 means change is outpacing governance capacity.

        Numerator: exposure_magnitude signals (growth, expansion)
        Denominator: corporate_footprint signals (governance, compliance)

        Thresholds: warning=1.5, critical=2.5
        """
        # Numerator: signals indicating rapid change
        change_signals = []
        # Denominator: signals indicating governance capacity
        governance_signals = []

        for node in graph.nodes.values():
            for sig in node.signals:
                sid = sig.signal_id.lower()
                if any(kw in sid for kw in (
                    "growth", "expansion", "hiring", "acquisition",
                    "subdomain", "exposure", "magnitude", "revenue"
                )):
                    change_signals.append(sig.value)
                elif any(kw in sid for kw in (
                    "governance", "compliance", "security", "leadership",
                    "certification", "framework", "audit", "policy"
                )):
                    governance_signals.append(sig.value)

        # Calculate average scores
        change_rate = (
            sum(change_signals) / len(change_signals)
            if change_signals else 50.0
        )
        governance_rate = (
            sum(governance_signals) / len(governance_signals)
            if governance_signals else 50.0
        )

        # Ratio (avoid division by zero)
        velocity = change_rate / max(governance_rate, 1.0)

        return DerivativeResult(
            name="velocity",
            value=velocity,
            warning_threshold=1.5,
            critical_threshold=2.5,
            window_days=90,
            components={
                "change_rate": change_rate,
                "governance_rate": governance_rate,
                "change_signal_count": len(change_signals),
                "governance_signal_count": len(governance_signals),
            },
        )

    def compute_drift(
        self,
        graph: Graph,
        cohort_means: Optional[Dict[str, float]] = None,
        cohort_stddevs: Optional[Dict[str, float]] = None,
    ) -> DerivativeResult:
        """
        Drift: Peer divergence indicator.

        Measures how far the entity has diverged from healthy peers
        using Mahalanobis distance (simplified to z-score when
        cohort statistics are available).

        High drift = behaviours becoming anomalous relative to peers.

        Thresholds: warning=2.0 (std devs), critical=3.0
        """
        # Collect all signal values by signal_id
        signal_values: Dict[str, float] = {}
        for node in graph.nodes.values():
            for sig in node.signals:
                signal_values[sig.signal_id] = sig.value

        if not signal_values:
            return DerivativeResult(
                name="drift",
                value=0.0,
                warning_threshold=2.0,
                critical_threshold=3.0,
                window_days=180,
            )

        # If cohort stats provided, compute actual Mahalanobis distance
        if cohort_means and cohort_stddevs:
            z_scores = []
            for sig_id, value in signal_values.items():
                if sig_id in cohort_means and sig_id in cohort_stddevs:
                    std = cohort_stddevs[sig_id]
                    if std > 0:
                        z = abs(value - cohort_means[sig_id]) / std
                        z_scores.append(z)

            if z_scores:
                # Root mean square of z-scores (simplified Mahalanobis)
                drift = math.sqrt(sum(z ** 2 for z in z_scores) / len(z_scores))
            else:
                drift = 0.0
        else:
            # Without cohort data, estimate drift from signal variance
            values = list(signal_values.values())
            mean = sum(values) / len(values)
            variance = sum((v - mean) ** 2 for v in values) / len(values)
            # Normalize: high variance relative to mean = high drift
            drift = math.sqrt(variance) / max(mean, 1.0)

        return DerivativeResult(
            name="drift",
            value=drift,
            warning_threshold=2.0,
            critical_threshold=3.0,
            window_days=180,
            components={
                "signal_count": len(signal_values),
                "cohort_available": cohort_means is not None,
            },
        )

    def compute_concentration(self, graph: Graph) -> DerivativeResult:
        """
        Concentration: Single-point-of-failure indicator.

        Uses Herfindahl-Hirschman Index (HHI) on dependency and
        data_flow edges to measure how concentrated the entity's
        dependencies are.

        HHI = sum of squared market shares. Range: 0 (diverse) to 1 (monopoly).

        Thresholds: warning=0.25, critical=0.50
        """
        # Collect dependency target counts
        dep_edges = [
            e for e in graph.edges.values()
            if e.edge_type in (EdgeType.DEPENDENCY, EdgeType.DATA_FLOW)
        ]

        if not dep_edges:
            return DerivativeResult(
                name="concentration",
                value=0.0,
                warning_threshold=0.25,
                critical_threshold=0.50,
                window_days=0,
                components={"dependency_count": 0},
            )

        # Count edges per target (how many things depend on each target)
        target_counts: Dict[str, int] = {}
        for edge in dep_edges:
            target_counts[edge.target_id] = (
                target_counts.get(edge.target_id, 0) + 1
            )

        total = sum(target_counts.values())
        if total == 0:
            return DerivativeResult(
                name="concentration",
                value=0.0,
                warning_threshold=0.25,
                critical_threshold=0.50,
                window_days=0,
            )

        # HHI = sum of squared shares
        hhi = sum((count / total) ** 2 for count in target_counts.values())

        return DerivativeResult(
            name="concentration",
            value=hhi,
            warning_threshold=0.25,
            critical_threshold=0.50,
            window_days=0,
            components={
                "dependency_count": len(dep_edges),
                "unique_targets": len(target_counts),
                "hhi": hhi,
            },
        )

    def compute_fragility(
        self,
        graph: Graph,
        existing_derivatives: Optional[Dict[str, DerivativeResult]] = None,
    ) -> DerivativeResult:
        """
        Fragility: Composite resilience indicator.

        Weighted combination:
          - 30% entropy
          - 25% velocity
          - 25% concentration
          - 20% technical infrastructure health

        No fixed thresholds in schema - uses composite scale.
        """
        # Get or compute component derivatives
        if existing_derivatives:
            entropy = existing_derivatives.get("entropy")
            velocity = existing_derivatives.get("velocity")
            concentration = existing_derivatives.get("concentration")
        else:
            entropy = self.compute_entropy(graph)
            velocity = self.compute_velocity(graph)
            concentration = self.compute_concentration(graph)

        # Normalize each component to 0-1 scale
        entropy_norm = min(
            (entropy.value / entropy.critical_threshold) if entropy else 0.0,
            1.0,
        )

        velocity_norm = min(
            (velocity.value / velocity.critical_threshold) if velocity else 0.0,
            1.0,
        )

        concentration_norm = (
            concentration.value if concentration else 0.0
        )  # Already 0-1

        # Technical infrastructure health: average signal score of tech nodes
        tech_scores = []
        for node in graph.nodes.values():
            if node.node_type == NodeType.ASSET:
                for sig in node.signals:
                    tech_scores.append(sig.value)

        # Invert: low scores = high fragility
        if tech_scores:
            avg_health = sum(tech_scores) / len(tech_scores)
            infra_fragility = 1.0 - (avg_health / 100.0)
        else:
            infra_fragility = 0.5  # Unknown = moderate fragility

        # Composite
        fragility = (
            0.30 * entropy_norm
            + 0.25 * velocity_norm
            + 0.25 * concentration_norm
            + 0.20 * infra_fragility
        )

        return DerivativeResult(
            name="fragility",
            value=fragility,
            warning_threshold=0.40,
            critical_threshold=0.65,
            window_days=0,
            components={
                "entropy_contribution": 0.30 * entropy_norm,
                "velocity_contribution": 0.25 * velocity_norm,
                "concentration_contribution": 0.25 * concentration_norm,
                "infrastructure_contribution": 0.20 * infra_fragility,
                "entropy_raw": entropy.value if entropy else 0.0,
                "velocity_raw": velocity.value if velocity else 0.0,
                "concentration_raw": concentration.value if concentration else 0.0,
                "infra_health": 1.0 - infra_fragility,
            },
        )

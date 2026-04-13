"""
WE-5f: Scenario Simulator

Propagates a hypothetical shock through the Portfolio Graph to estimate
aggregate impact and identify mitigation paths.

Simulation model (intentionally transparent / deterministic):

1. Apply shock magnitude to the target node/signal across the portfolio.
2. First-order impact: entities directly connected to the shocked node
   experience a signal degradation proportional to the shock magnitude.
3. Cascade (if propagation != direct_only): each subsequent hop multiplies
   by the shock's decay_rate. Deeper entities see less impact.
4. Per-entity impact is mapped to an implied tier shift via a simple
   linear rule (larger signal degradation = more tier shift).
5. Aggregate loss estimate is a placeholder (expected / p10 / p90) derived
   from the count of affected entities and severity distribution -- this
   is intentionally simple; real loss calibration happens later when
   actual incurred values are available.
6. Mitigation paths highlight the entities whose removal would most reduce
   aggregate severity.

For the MVP, simulations are advisory and support the scenario panel UI
in WE-5 frontend. Loss figures are relative / illustrative, not
actuarially calibrated.
"""

from __future__ import annotations

import logging
from collections import defaultdict
from datetime import datetime, timezone

import numpy as np

from world_engine.portfolio.types import (
    EntityImpact,
    LossRange,
    MitigationPath,
    PortfolioGraph,
    ScenarioDefinition,
    ScenarioShock,
    SimulationResult,
)

logger = logging.getLogger("dsi.world_engine.portfolio.simulation")


# Heuristic: the "cost" of a fully-disrupted entity, in relative units.
# Aggregate loss = sum of severity * ENTITY_LOSS_UNIT. The unit is
# illustrative -- frontend renders in USD with a label.
ENTITY_LOSS_UNIT_USD = 100_000.0


class ScenarioSimulator:
    """Propagates scenario shocks through a PortfolioGraph."""

    def simulate(
        self, scenario: ScenarioDefinition, portfolio: PortfolioGraph
    ) -> SimulationResult:
        """Run all shocks in the scenario and aggregate entity impacts."""
        entity_severity: dict[str, float] = defaultdict(float)
        entity_affected_signals: dict[str, set[str]] = defaultdict(set)
        entity_signal_delta: dict[str, dict[str, float]] = defaultdict(dict)

        for shock in scenario.shocks:
            hits = self._propagate_shock(shock, portfolio)
            for entity_name, (severity, affected_sig, delta) in hits.items():
                entity_severity[entity_name] = min(
                    1.0, entity_severity[entity_name] + severity
                )
                entity_affected_signals[entity_name].add(affected_sig)
                if affected_sig:
                    entity_signal_delta[entity_name][affected_sig] = delta

        # Build entity_impacts rows
        entity_impacts: list[EntityImpact] = []
        for entity_name in portfolio.entity_names:
            severity = entity_severity.get(entity_name, 0.0)
            if severity == 0.0:
                continue
            entity_impacts.append(EntityImpact(
                entity_name=entity_name,
                affected_signals=sorted(entity_affected_signals.get(entity_name, set())),
                implied_signal_delta=entity_signal_delta.get(entity_name, {}),
                severity=float(severity),
                # tier_at_bind / implied_tier_after_shock filled in caller
                # when a DB lookup is available. Kept None here for purity.
            ))

        # Aggregate loss estimate (illustrative)
        aggregate = self._aggregate_loss(entity_impacts)

        # Concentration amplification: if many entities are affected via
        # the same shared node, multiply.
        amplification = self._concentration_amplification(
            entity_impacts, portfolio
        )

        # Mitigation paths: rank entities by severity; removing the top
        # contributors reduces aggregate most.
        mitigation = self._mitigation_paths(entity_impacts)

        return SimulationResult(
            scenario=scenario,
            entity_impacts=sorted(entity_impacts, key=lambda e: -e.severity),
            aggregate_loss_estimate=aggregate,
            concentration_amplification=amplification,
            mitigation_paths=mitigation,
            computed_at=datetime.now(timezone.utc),
        )

    # ------------------------------------------------------------------
    # Shock propagation
    # ------------------------------------------------------------------

    def _propagate_shock(
        self, shock: ScenarioShock, portfolio: PortfolioGraph
    ) -> dict[str, tuple[float, str, float]]:
        """Propagate a single shock. Returns {entity: (severity, signal, delta)}.

        The shock targets either a node (id) or a signal (code). For node
        shocks we find all entities connected to it; for signal shocks we
        identify entities whose assessments include that signal via the
        signal code matching a shared node id "shared:<code>".
        """
        # Find directly-affected entities
        first_hop_entities = self._first_hop_entities(shock, portfolio)
        if not first_hop_entities:
            return {}

        # For direct_only, we stop here
        magnitude = shock.magnitude if shock.magnitude >= 0 else abs(shock.magnitude)
        if shock.magnitude == 0.0:
            # Complete failure of the target = full severity
            severity = 1.0
        else:
            # magnitude is a score delta in 0-100 scale -- convert to severity
            severity = min(1.0, abs(shock.magnitude) / 50.0)

        signal_label = (
            shock.target_id
            if shock.target_type in ("signal", "node")
            else "external"
        )
        signal_delta = -abs(shock.magnitude) if shock.magnitude != 0.0 else -100.0

        impacts: dict[str, tuple[float, str, float]] = {}
        for entity in first_hop_entities:
            impacts[entity] = (severity, signal_label, signal_delta)

        if shock.propagation == "direct_only":
            return impacts

        # One-hop or cascade: step through entities connected to the same
        # shared nodes as the first-hop entities.
        if shock.propagation in ("one_hop", "full_cascade"):
            next_layer = self._expand_via_shared_nodes(first_hop_entities, portfolio)
            decayed_severity = severity * max(0.0, min(1.0, shock.decay_rate))
            for entity in next_layer:
                if entity in impacts:
                    continue
                impacts[entity] = (decayed_severity, signal_label, signal_delta * shock.decay_rate)

        if shock.propagation == "full_cascade":
            # One more hop -- diminishing returns after that
            second_layer = self._expand_via_shared_nodes(
                list(impacts.keys()), portfolio
            )
            doubly_decayed = severity * max(0.0, min(1.0, shock.decay_rate)) ** 2
            for entity in second_layer:
                if entity in impacts:
                    continue
                impacts[entity] = (
                    doubly_decayed, signal_label, signal_delta * (shock.decay_rate ** 2)
                )

        return impacts

    def _first_hop_entities(
        self, shock: ScenarioShock, portfolio: PortfolioGraph
    ) -> list[str]:
        """Entities directly connected to the shock target."""
        target_id: str
        if shock.target_type == "signal":
            target_id = f"shared:{shock.target_id}"
        elif shock.target_type == "node":
            target_id = shock.target_id
        else:
            # derivative / external_event -- treat as affecting all entities
            return list(portfolio.entity_names)

        connected: set[str] = set()
        for edge in portfolio.edges:
            if edge.target_id == target_id or edge.source_id == target_id:
                connected.update(edge.entities or [])
        return sorted(connected)

    def _expand_via_shared_nodes(
        self, entities: list[str], portfolio: PortfolioGraph
    ) -> list[str]:
        """Entities reachable through the given entities' shared-node
        connections (one hop)."""
        entity_set = set(entities)
        reachable: set[str] = set()
        # For each shared node any of these entities touches, include all
        # other entities touching the same node.
        node_to_entities: dict[str, set[str]] = defaultdict(set)
        for edge in portfolio.edges:
            if not edge.is_inter_entity:
                continue
            if edge.target_id.startswith("shared:") or edge.source_id.startswith("shared:"):
                shared = edge.target_id if edge.target_id.startswith("shared:") else edge.source_id
                node_to_entities[shared].update(edge.entities or [])

        for node_id, node_entities in node_to_entities.items():
            if entity_set & node_entities:
                reachable.update(node_entities)
        return sorted(reachable - entity_set)

    # ------------------------------------------------------------------
    # Aggregate loss estimate (illustrative)
    # ------------------------------------------------------------------

    def _aggregate_loss(self, impacts: list[EntityImpact]) -> LossRange:
        if not impacts:
            return LossRange(expected_loss=0.0, p10=0.0, p90=0.0)

        # Expected loss = sum of severity × unit
        total = sum(i.severity for i in impacts) * ENTITY_LOSS_UNIT_USD
        # P10/P90 spread derived from impact severity distribution
        severities = np.array([i.severity for i in impacts])
        spread = float(np.std(severities)) * ENTITY_LOSS_UNIT_USD * len(impacts)
        return LossRange(
            expected_loss=float(total),
            p10=float(max(0.0, total - spread)),
            p90=float(total + spread),
        )

    def _concentration_amplification(
        self, impacts: list[EntityImpact], portfolio: PortfolioGraph
    ) -> float:
        """Ratio of affected entities to what would be expected in a
        diversified portfolio of the same size.

        A value > 1.0 means concentration increased the blast radius.
        """
        if not impacts or portfolio.entity_count < 2:
            return 1.0
        affected_fraction = len(impacts) / portfolio.entity_count
        # Diversified baseline: we'd expect maybe 10% of entities affected
        # by a typical shock if the portfolio were perfectly diversified.
        baseline_fraction = 0.10
        return float(affected_fraction / baseline_fraction) if baseline_fraction else 1.0

    # ------------------------------------------------------------------
    # Mitigation paths
    # ------------------------------------------------------------------

    def _mitigation_paths(self, impacts: list[EntityImpact]) -> list[MitigationPath]:
        """Rank entities by severity; the top-N account for the most
        reduction if remediated or non-renewed."""
        if not impacts:
            return []

        ordered = sorted(impacts, key=lambda i: -i.severity)[:5]
        total_sev = sum(i.severity for i in impacts) or 1.0

        paths: list[MitigationPath] = []
        for imp in ordered:
            impact_reduction = imp.severity / total_sev
            if imp.severity >= 0.8:
                action = "non_renew"
                rationale = "High severity; non-renewal removes material portfolio exposure"
            elif imp.severity >= 0.4:
                action = "remediate"
                rationale = "Moderate severity; targeted remediation reduces exposure"
            else:
                action = "monitor"
                rationale = "Low severity; monitor for trend reversal"

            paths.append(MitigationPath(
                entity_name=imp.entity_name,
                action=action,
                rationale=rationale,
                impact_reduction=float(impact_reduction),
            ))
        return paths

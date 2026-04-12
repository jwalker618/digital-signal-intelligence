"""
WE-5 Portfolio types.

These are Pydantic models because the portfolio layer returns structured
data to the API. They are distinct from the per-entity graph types in
signal_architecture/graph -- those are dataclasses with methods; these
are JSON-serialisable value objects.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class PortfolioNode(BaseModel):
    """A node in the Portfolio Graph.

    Either an intra-entity node (belonging to a specific entity's
    Organisational Graph) or an inter-entity node (a shared external
    dependency -- e.g. AWS us-east-1 -- that connects multiple entities).
    """

    id: str
    node_type: str        # organisation | asset | partner | person | process | jurisdiction
    label: str
    entity_name: Optional[str] = None   # None when the node spans multiple entities
    is_shared: bool = False              # True for inter-entity nodes


class PortfolioEdge(BaseModel):
    """An edge in the Portfolio Graph."""

    id: str
    source_id: str
    target_id: str
    edge_type: str         # dependency | trust | data_flow | ownership | operates_in | employment
                           # or inter-entity variants: shared_technology | shared_partner |
                           # shared_jurisdiction | causal_pathway_correlation
    weight: float = 0.0
    is_inter_entity: bool = False
    entities: list[str] = Field(default_factory=list)  # entity names joined by this edge


class SystemicNode(BaseModel):
    """A node with portfolio-wide significance (high PageRank)."""

    node_id: str
    node_type: str
    label: str
    portfolio_pagerank: float
    connected_entities: list[str] = Field(default_factory=list)
    failure_impact_estimate: float = 0.0


class PortfolioGraph(BaseModel):
    """Assembled view of all Organisational Graphs for a commercial entity."""

    commercial_entity_id: str
    entity_count: int
    nodes: list[PortfolioNode] = Field(default_factory=list)
    edges: list[PortfolioEdge] = Field(default_factory=list)
    systemic_nodes: list[SystemicNode] = Field(default_factory=list)
    aggregate_derivatives: dict[str, float] = Field(default_factory=dict)
    entity_names: list[str] = Field(default_factory=list)
    built_at: datetime


class ScenarioShock(BaseModel):
    """A single perturbation in a scenario definition."""

    target_type: str   # signal | node | derivative | external_event
    target_id: str
    magnitude: float   # score delta (negative = degradation); 0.0 = complete failure
    propagation: str = "one_hop"   # direct_only | one_hop | full_cascade
    decay_rate: float = 0.5


class ScenarioDefinition(BaseModel):
    """A scenario for simulation."""

    name: str
    description: Optional[str] = None
    shocks: list[ScenarioShock]


class EntityImpact(BaseModel):
    """Per-entity outcome of a scenario."""

    entity_name: str
    affected_signals: list[str] = Field(default_factory=list)
    implied_signal_delta: dict[str, float] = Field(default_factory=dict)
    tier_at_bind: Optional[int] = None
    implied_tier_after_shock: Optional[int] = None
    severity: float = 0.0   # 0 = unaffected, 1 = fully disrupted


class LossRange(BaseModel):
    """Aggregate loss distribution summary."""

    expected_loss: float
    p10: float
    p90: float
    currency: str = "USD"


class MitigationPath(BaseModel):
    """A remediation or non-renewal option to reduce scenario exposure."""

    entity_name: str
    action: str   # remediate | non_renew | monitor | offset
    rationale: str
    impact_reduction: float   # 0-1, fraction of entity's impact that goes away


class SimulationResult(BaseModel):
    """Full output of a scenario simulation."""

    scenario: ScenarioDefinition
    entity_impacts: list[EntityImpact] = Field(default_factory=list)
    aggregate_loss_estimate: Optional[LossRange] = None
    concentration_amplification: float = 1.0   # 1.0 = no amplification vs diversified
    mitigation_paths: list[MitigationPath] = Field(default_factory=list)
    computed_at: datetime


class MarginalImpactResult(BaseModel):
    """Outcome of analysing the portfolio impact of accepting a new submission."""

    would_create_concentration: bool
    would_worsen_concentration: bool
    affected_dimensions: list[dict] = Field(default_factory=list)
    systemic_node_overlap: list[str] = Field(default_factory=list)
    recommendation: str   # accept | accept_with_warning | flag
    reasoning: list[str] = Field(default_factory=list)

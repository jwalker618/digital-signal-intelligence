# Phase WE-5: Portfolio Intelligence & Simulation

| Item | Value |
|------|-------|
| Version | 1.1 |
| Depends on | WE-1, WE-3, WE-4 |

---

## Overview

Assemble individual Organisational Graphs into a Portfolio Graph. Detect hidden concentration risk. Enable scenario simulation. Feed concentration intelligence back into CAF as a portfolio-aware component. Provide marginal impact analysis for new submissions. This transforms DSI from a risk-level assessment tool into a portfolio-level intelligence platform.

## Current State

The Organisational Graph Runtime (`signal_architecture/graph/`) builds per-entity graphs with 6 node types, 6 edge types, 5 derivatives, PageRank. No system assembles these into a portfolio view. Portfolio analytics (`infrastructure/analytics/portfolio.py`) operates on assessment scores, not graph structures.

## Target State

- Portfolio Graph connecting all entities within a commercial entity's portfolio
- Concentration intelligence published to the registry across 4 dimensions
- Scenario Simulation API for hypothetical shock propagation
- Concentration-aware CAF enrichment
- Marginal impact endpoint for new submission evaluation
- Portfolio Dashboard as a new top-level frontend route

---

## Implementation Plan

### WE-5a: Portfolio Graph Builder

**New file**: `world_engine/portfolio/graph_builder.py`

```python
class PortfolioGraphBuilder:
    """Assembles individual Organisational Graphs into a Portfolio Graph."""

    def build(self, commercial_entity_id: str) -> PortfolioGraph:
        """
        1. Load all assessed entities for this commercial entity
        2. Load each entity's Organisational Graph (from graph storage)
        3. Infer inter-entity edges:
           a. Shared technology nodes (same cloud provider, CDN, etc.)
           b. Shared partner nodes (same supplier, certifier)
           c. Shared jurisdiction nodes (same regulatory environment)
           d. Causal pathway correlation (entities sharing active precursor patterns)
        4. Compute portfolio-level derivatives (aggregate entropy, velocity, drift)
        5. Run portfolio-level PageRank to identify systemic nodes
        """
```

**New file**: `world_engine/portfolio/types.py`

```python
class PortfolioGraph(BaseModel):
    commercial_entity_id: str
    entity_count: int
    nodes: list[PortfolioNode]
    edges: list[PortfolioEdge]
    systemic_nodes: list[SystemicNode]
    aggregate_derivatives: dict[str, float]
    built_at: datetime

class SystemicNode(BaseModel):
    node_id: str
    node_type: str
    label: str
    portfolio_pagerank: float
    connected_entities: list[str]
    failure_impact_estimate: float
```

**Caching strategy**: Portfolio Graphs are pre-computed as a batch process (triggered after new assessments) and cached. API requests serve from cache. Cache invalidated when any constituent entity is re-assessed.

### WE-5b: Concentration Detector

**New file**: `world_engine/portfolio/concentration.py`

```python
class ConcentrationDetector:
    """Identifies hidden concentration risk in the Portfolio Graph."""

    def detect(self, portfolio: PortfolioGraph) -> list[PortfolioConcentration]:
        """
        Four dimensions:
        1. Node concentration: single external nodes connected to > threshold entities
        2. Pathway concentration: entities sharing active causal precursor patterns
        3. Derivative correlation: portfolio-wide derivative trends (systemic drift)
        4. Cohort concentration: over-representation of signal-derived cohorts
        """
```

### WE-5c: Appetite Integration

**File to modify**: `infrastructure/models/commercial_schema.py`

Add registry query to appetite evaluation flow:

```python
def evaluate_appetite(coverage, submission_data, entity):
    # ... existing appetite checks ...

    # Portfolio concentration check
    concentrations = registry.get_portfolio_concentrations(entity.id)
    for conc in concentrations:
        if submission_would_increase(conc, submission_data):
            result.warnings.append(ConcentrationWarning(
                dimension=conc.dimension,
                detail=conc.detail,
                current_severity=conc.severity,
            ))
    return result
```

### WE-5d: Concentration-Aware CAF Enrichment

**New file**: `world_engine/portfolio/caf_enrichment.py`

```python
class PortfolioCafEnricher:
    """Adjusts CAF based on entity's position in portfolio concentration."""

    CONCENTRATION_LOADING_CAP = 1.15  # Max 15% additional loading from concentration

    def enrich(
        self,
        base_caf: CausalAdjustmentFactor,
        entity_id: str,
        commercial_entity_id: str,
        registry: IntelligenceRegistry,
    ) -> CausalAdjustmentFactor:
        """
        Query portfolio concentrations for the commercial entity.
        If this entity contributes to concentration on a flagged dimension:
        1. Compute concentration loading proportional to severity
        2. Cap at CONCENTRATION_LOADING_CAP
        3. Multiply into CAF (still subject to overall CAF constraints)
        4. Record portfolio contribution in CAF provenance

        Entity at centre of concentration cluster receives higher CAF.
        Entity in diversified portfolio receives no adjustment.
        """
```

**File to modify**: `layers/risk/workflow.py` -- After base CAF computation, apply portfolio enrichment if maturity >= SIMULATE.

### WE-5e: Marginal Impact Endpoint

**New file**: `world_engine/portfolio/marginal_impact.py`

```python
class MarginalImpactAnalyser:
    """Evaluates portfolio impact of accepting a prospective submission."""

    def analyse(
        self,
        prospective_entity_id: str,
        prospective_signals: dict[str, float],
        commercial_entity_id: str,
    ) -> MarginalImpactResult:
        """
        1. Build current portfolio graph
        2. Simulate adding the prospective entity
        3. Recompute concentration metrics
        4. Compare before/after: new concentrations created? existing worsened?
        5. Return delta assessment with specific dimensions affected
        """

class MarginalImpactResult(BaseModel):
    would_create_concentration: bool
    would_worsen_concentration: bool
    affected_dimensions: list[dict]      # dimension, before_severity, after_severity
    systemic_node_overlap: list[str]     # shared systemic nodes
    recommendation: str                  # accept | accept_with_warning | flag
```

### WE-5f: Scenario Simulation API

**New file**: `world_engine/portfolio/simulation.py`

```python
class ScenarioSimulator:
    """Propagates hypothetical shocks through the Portfolio Graph."""

    def simulate(
        self, scenario: ScenarioDefinition, portfolio: PortfolioGraph
    ) -> SimulationResult:
        """
        1. Apply shock to specified nodes/signals
        2. Propagate through causal edges (active relationships)
        3. Compute per-entity impact (signal degradation, tier migration)
        4. Aggregate to portfolio level (loss distribution, concentration amplification)
        5. Identify mitigation paths (remediate/non-renew recommendations)
        """

class ScenarioDefinition(BaseModel):
    name: str
    description: str
    shocks: list[Shock]

class Shock(BaseModel):
    target_type: str        # signal | node | derivative | external_event
    target_id: str
    magnitude: float        # Score change, or 0.0 for complete failure
    propagation: str        # direct_only | one_hop | full_cascade
    decay_rate: float       # Strength decay per hop (default 0.5)

class SimulationResult(BaseModel):
    scenario: ScenarioDefinition
    entity_impacts: list[EntityImpact]
    aggregate_loss_estimate: LossRange
    concentration_amplification: float   # 1.0 = no amplification
    mitigation_paths: list[MitigationPath]
    computed_at: datetime
```

**New API routes** (added to world engine router):

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/portfolio/{entity_id}/graph` | GET | Portfolio Graph summary |
| `/portfolio/{entity_id}/graph/systemic-nodes` | GET | Highest-PageRank nodes |
| `/portfolio/{entity_id}/concentrations` | GET | *(already in WE-1)* |
| `/portfolio/{entity_id}/marginal-impact` | POST | Marginal impact of adding a risk |
| `/portfolio/{entity_id}/simulate` | POST | Run scenario simulation |
| `/portfolio/{entity_id}/simulate/presets` | GET | Pre-defined scenario templates |

### WE-5g: Frontend -- Portfolio Dashboard

**New files**:
- `frontend/src/components/portfolio/PortfolioDashboard.tsx` -- Top-level view
- `frontend/src/components/portfolio/ConcentrationPanel.tsx` -- Concentration alerts by dimension
- `frontend/src/components/portfolio/SystemicNodesPanel.tsx` -- Portfolio PageRank leaders
- `frontend/src/components/portfolio/ScenarioPanel.tsx` -- Scenario simulation interface

Portfolio Dashboard is a **new top-level route** (`/portfolio/{entity_id}`), not a tab within the submission workbench. It operates at the commercial entity level.

**ScenarioPanel**: Pre-defined templates (cloud provider outage, regulatory change, supply chain disruption, vulnerability disclosure) plus custom scenario builder. Results: entity impact heatmap, aggregate loss range, mitigation recommendations.

### WE-5h: Seed Script

**File to modify**: `seed_dsi_bench.py`

Seed portfolio data: multiple entities assessed through the same commercial entity, with shared technology dependencies. Run concentration detection and store results. Seed at least one pre-computed simulation result.

---

## Constraints

1. Portfolio Graph is pre-computed and cached, not built on every API request
2. Concentration-aware CAF enrichment only activates at SIMULATE maturity
3. Marginal impact is advisory (flags/warnings), not auto-decline
4. Scenario simulation is computationally bounded (max propagation depth, timeout)
5. No changes to existing per-entity assessment or scoring logic

## Success Criteria

1. Portfolio Graph builds correctly for seeded commercial entities
2. Concentration alerts detect known shared dependencies in seed data
3. Marginal impact correctly identifies when a new risk worsens concentration
4. Scenario simulation propagates shocks through causal edges
5. Portfolio CAF enrichment produces higher CAF for concentration-exposed entities
6. Portfolio Dashboard renders with real data from seed
7. Appetite evaluation includes concentration warnings
8. All existing tests pass unchanged

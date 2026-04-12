# Phase WE-1: Foundation -- Types, Schema, and Intelligence Registry

| Item           | Value                                          |
|----------------|-------------------------------------------------|
| Version        | 1.1                                             |
| Date           | April 2026                                      |
| Classification | Phase Development Plan                          |
| Extends        | World Engine Architecture Specification v1.0    |
| Extends        | World Engine Pricing & Portfolio Addendum v1.0  |
| Supersedes     | World Engine Phase Development Plan v1.0 WE-1   |

---

## Overview

Establish the World Engine's foundational data model: types, database tables, the
intelligence registry, the maturity state evaluator, and the read-only API. Every
subsequent phase writes to or reads from the structures built here. No operational
intelligence is produced in this phase -- it builds the skeleton.

---

## Current State

The World Engine does not exist in the codebase. The `world_engine/` directory does
not exist. The following adjacent systems are relevant:

- **Organisational Graph Runtime**: `signal_architecture/graph/` -- 6 node types
  (`organisation`, `asset`, `partner`, `person`, `process`, `jurisdiction`), 6 edge
  types (`DEPENDENCY`, `TRUST`, `DATA_FLOW`, `OWNERSHIP`, `OPERATES_IN`,
  `EMPLOYMENT`), 5 derivatives (entropy, velocity, drift, concentration, fragility),
  PageRank propagation. Implemented in Python + Rust (`rust/dsi-core/`). Key files:
  `types.py`, `graph_builder.py`, `edge_inferencer.py`,
  `derivatives/calculator.py`, `propagation/algorithms.py`.

- **Assessment Database**: `infrastructure/db/models.py` -- SQLAlchemy models for
  all assessment outputs. `ModelVersionRecord` persists every workflow execution with
  composite scores (0--1000), tier assignments, pricing outputs, loss propensity,
  exposure bands, and full signal-level detail via `ModelVersionSignal`. Every model
  cycle produces a versioned, atomic record.

- **Analytics Module**: `infrastructure/analytics/` -- Performance, portfolio, signal,
  cohort, and workflow analytics. Existing foundation for population-level computation.
  Key files: `portfolio.py`, `cohorts.py`, `signal_analytics.py`.

- **Existing Migrations**: `alembic/versions/` -- 10 migrations (`001` through `010`).
  Next available: `011`.

---

## Target State

A new top-level directory `world_engine/` containing:

1. The complete type system for all 5 WE phases
2. Database tables and migrations for all WE data
3. The intelligence registry with read-only API and internal write API
4. The maturity state evaluator
5. Placeholder directories for subsequent phases

---

## File Structure

```
world_engine/
├── __init__.py
├── types.py                    # Core data types (all phases)
├── maturity.py                 # Maturity stage evaluator
├── registry/
│   ├── __init__.py
│   ├── store.py                # Intelligence registry data store
│   ├── api.py                  # Read-only FastAPI router
│   └── types.py                # Registry request/response types
├── consistency/                # (Phase WE-2)
│   └── __init__.py
├── scanner/                    # (Phase WE-3)
│   └── __init__.py
├── inferencer/                 # (Phase WE-3)
│   └── __init__.py
├── validator/                  # (Phase WE-3)
│   └── __init__.py
├── lifecycle/                  # (Phase WE-3)
│   └── __init__.py
├── drift/                      # (Phase WE-3)
│   └── __init__.py
├── population/                 # (Phase WE-3)
│   └── __init__.py
├── causal_pricing/             # (Phase WE-4)
│   └── __init__.py
├── portfolio/                  # (Phase WE-5)
│   └── __init__.py
└── scheduler.py                # (Phase WE-3 -- placeholder)
```

---

## Implementation Plan

### WE-1a: Core Types

**New file**: `world_engine/types.py`

Define the complete type system using Pydantic models. This file contains types
consumed by all subsequent phases. Types are defined here even if the subsystem
that uses them is built later, so that the type contracts are stable from the start.

#### Enums

```python
class MaturityStage(str, Enum):
    """World Engine maturity, gated by population size and time depth."""
    SEED = "seed"              # < 500 entities, 0-6 months
    LEARN = "learn"            # 500-5K entities, 6-18 months
    EMERGE = "emerge"          # 5K-50K entities, 18-36 months
    SIMULATE = "simulate"      # > 50K entities, 36+ months

class LifecycleState(str, Enum):
    CANDIDATE = "candidate"
    PROVISIONAL = "provisional"
    ACTIVE = "active"
    DEPRECATED = "deprecated"

class CausalDirection(str, Enum):
    A_CAUSES_B = "a_causes_b"
    B_CAUSES_A = "b_causes_a"
    BIDIRECTIONAL = "bidirectional"
    CONTEMPORANEOUS = "contemporaneous"

class DriftSeverity(str, Enum):
    INFO = "info"              # Noteworthy but not actionable
    WARNING = "warning"        # Warrants monitoring
    CRITICAL = "critical"      # Requires attention
```

#### Core Intelligence Types

```python
class StateTransition(BaseModel):
    from_state: LifecycleState
    to_state: LifecycleState
    transitioned_at: datetime
    reason: str                          # Statistical evidence for transition
    evidence: dict                       # Raw metrics at transition time

class DiscoveredRelationship(BaseModel):
    id: str                              # UUID
    source_signal: str                   # Signal feature ID (coverage-agnostic)
    target_signal: str                   # Signal feature ID
    direction: CausalDirection
    lag_months: float | None             # Temporal lag (null for contemporaneous)
    correlation_rho: float               # Spearman's rho at discovery
    granger_f_statistic: float | None    # Granger causality F-stat
    granger_p_value: float | None
    effect_size: float                   # Cohen's d or equivalent
    confounders_tested: list[str]        # Which confounders were controlled for
    holdout_rho: float | None            # Replication correlation in holdout
    holdout_p_value: float | None
    predictive_hit_rate: float | None    # Out-of-sample prediction accuracy
    population_size: int                 # N entities at discovery
    coverage_scope: list[str]            # Which coverages contributed entities
    lifecycle_state: LifecycleState
    state_entered_at: datetime
    state_history: list[StateTransition]
    influence_weight: float              # 0.0-1.0, from evidence strength
    created_at: datetime
    updated_at: datetime
```

#### Consistency Types

```python
class ConsistencyScore(BaseModel):
    entity_id: str
    assessment_id: str
    overall_consistency: float           # 0.0-1.0
    signal_pair_scores: dict[str, float] # {pair_key: consistency}
    cross_group_scores: dict[str, float] # {group_pair_key: consistency}
    cross_layer_divergence: dict         # {risk_vs_loss: float, ...}
    divergent_pairs: list[str]           # Signal pairs with unexpected divergence
    computed_at: datetime
```

#### CAF Types

```python
class PrecursorEvaluation(BaseModel):
    relationship_id: str
    precursor_signal: str
    entity_value: float                  # Entity's current value
    threshold: float                     # Relationship's trigger threshold
    distance_from_threshold: float       # How far into precursor state
    implied_probability: float           # P(consequence) given this precursor
    lag_months: float

class TierMigrationDistribution(BaseModel):
    current_tier: int
    probabilities: dict[int, float]      # {tier: probability}
    expected_tier: float                 # Weighted average
    policy_period_months: int

class CausalAdjustmentFactor(BaseModel):
    entity_id: str
    assessment_id: str
    caf_value: float                     # The multiplicative adjustment
    confidence: float                    # 0.0-1.0
    active_precursors: list[PrecursorEvaluation]
    trajectory: TierMigrationDistribution
    relationships_evaluated: int
    constrained: bool                    # Whether floor/cap was applied
    raw_caf: float                       # Pre-constraint value
    constraint_regime: str               # Which constraint set was active
    computed_at: datetime

    @classmethod
    def neutral(cls, entity_id: str = "", assessment_id: str = "") -> "CausalAdjustmentFactor":
        """Factory for CAF = 1.0 (zero impact)."""
        ...
```

#### Portfolio Types

```python
class PortfolioConcentration(BaseModel):
    entity_id: str                       # Commercial entity (portfolio owner)
    dimension: str                       # node | pathway | derivative | cohort
    detail: str                          # Specific concentration identified
    severity: float                      # 0.0-1.0
    affected_entities: list[str]         # Entity IDs in the cluster
    computed_at: datetime
```

#### Drift Alert Types

```python
class DriftAlert(BaseModel):
    id: str                              # UUID
    alert_type: str                      # relationship_shift | regime_change |
                                         # signal_degradation | correlation_inversion
    severity: DriftSeverity
    source_signal: str | None            # Signal involved (if applicable)
    target_signal: str | None
    relationship_id: str | None          # Related relationship (if applicable)
    description: str                     # Human-readable summary
    evidence: dict                       # Statistical evidence for the drift
    detected_at: datetime
    acknowledged: bool                   # Whether a downstream system consumed it
    acknowledged_at: datetime | None
```

#### Discovery Pipeline Intermediate Types

```python
class CandidateRelationship(BaseModel):
    """Output of CorrelationScanner -- pre-causal-inference."""
    source_signal: str
    target_signal: str
    correlation_rho: float
    p_value: float
    population_size: int
    coverage_scope: list[str]

class DirectedCandidate(BaseModel):
    """Output of CausalInferencer -- has direction and lag."""
    source_signal: str
    target_signal: str
    direction: CausalDirection
    lag_months: float | None
    correlation_rho: float
    granger_f_statistic: float | None
    granger_p_value: float | None
    effect_size: float
    confounders_tested: list[str]
    population_size: int
    coverage_scope: list[str]

class ValidationResult(BaseModel):
    """Output of HoldoutValidator."""
    candidate: DirectedCandidate
    holdout_rho: float
    holdout_p_value: float
    passed: bool

class StabilityResult(BaseModel):
    """Output of TemporalStabilityTracker."""
    relationship_id: str
    windows_checked: int
    windows_stable: int
    correlation_trend: list[float]       # rho per window
    stable: bool
    sign_flip_detected: bool

class PredictiveResult(BaseModel):
    """Output of PredictiveValidator."""
    relationship_id: str
    predictions_made: int
    predictions_hit: int
    hit_rate: float
    passed: bool

class ScanRunReport(BaseModel):
    """Audit record for a complete discovery cycle."""
    run_id: str
    started_at: datetime
    completed_at: datetime
    maturity_stage: MaturityStage
    entities_scanned: int
    pairs_tested: int
    candidates_found: int
    candidates_after_inference: int
    candidates_after_confound: int
    candidates_after_holdout: int
    new_registrations: int
    state_transitions: list[StateTransition]
    drift_alerts_raised: int
    errors: list[str]
```

#### Maturity State Type

```python
class MaturityState(BaseModel):
    """Current maturity assessment of the World Engine."""
    stage: MaturityStage
    assessed_entity_count: int
    entities_with_temporal_data: int     # >= 2 assessments
    earliest_assessment: datetime | None
    time_depth_months: float
    active_relationships: int
    provisional_relationships: int
    candidate_relationships: int
    capabilities: dict[str, bool]        # {consistency: True, discovery: False, ...}
    evaluated_at: datetime
```

### WE-1b: Maturity Evaluator

**New file**: `world_engine/maturity.py`

The maturity evaluator determines the current Engine stage and gates capability
activation. It queries the assessment database for population statistics and the
registry for relationship counts.

```python
class MaturityEvaluator:
    """Determines the World Engine's current maturity stage."""

    STAGE_THRESHOLDS = {
        MaturityStage.SEED:     {"min_entities": 0,     "min_months": 0},
        MaturityStage.LEARN:    {"min_entities": 500,   "min_months": 6},
        MaturityStage.EMERGE:   {"min_entities": 5000,  "min_months": 18},
        MaturityStage.SIMULATE: {"min_entities": 50000, "min_months": 36},
    }

    CAPABILITIES = {
        MaturityStage.SEED:     {"consistency": True,  "discovery": False,
                                 "caf": False,          "simulation": False},
        MaturityStage.LEARN:    {"consistency": True,  "discovery": True,
                                 "caf": False,          "simulation": False},
        MaturityStage.EMERGE:   {"consistency": True,  "discovery": True,
                                 "caf": True,           "simulation": False},
        MaturityStage.SIMULATE: {"consistency": True,  "discovery": True,
                                 "caf": True,           "simulation": True},
    }

    def evaluate(self, db_session) -> MaturityState:
        """
        Query assessment database for:
        1. Total distinct assessed entities
        2. Entities with >= 2 assessment timestamps
        3. Earliest assessment timestamp
        Compute time depth and determine stage.
        """
        ...
```

### WE-1c: Database Schema

**New migration**: `alembic/versions/011_world_engine_tables.py`

| Table                       | Purpose                          | Key Columns                                           |
|-----------------------------|----------------------------------|-------------------------------------------------------|
| `we_relationships`          | Discovered causal relationships  | All fields from `DiscoveredRelationship`              |
| `we_state_transitions`      | Lifecycle audit trail            | `relationship_id` FK, from/to state, evidence JSON    |
| `we_consistency_scores`     | Per-assessment consistency       | `entity_id`, `assessment_id`, scores JSON             |
| `we_population_consistency` | Population-level aggregates      | `coverage`, `period`, aggregate metrics JSON          |
| `we_causal_adjustments`     | Per-assessment CAF               | `entity_id`, `assessment_id`, `caf_value`, trajectory |
| `we_portfolio_concentrations` | Portfolio concentration alerts | `entity_id` (commercial), dimension, severity         |
| `we_drift_alerts`           | Drift and regime change alerts   | `alert_type`, `severity`, evidence JSON               |
| `we_scan_runs`              | Batch run audit trail            | `run_id`, `started_at`, `completed_at`, stats JSON    |
| `we_constraint_history`     | CAF constraint regime changes    | `caf_floor`, `caf_cap`, evidence, `effective_from`    |

**Indexes**:
- `we_relationships`: composite on (`lifecycle_state`, `source_signal`, `target_signal`)
- `we_consistency_scores`: composite on (`entity_id`, `computed_at`); composite on (`assessment_id`)
- `we_causal_adjustments`: on `assessment_id`; composite on (`entity_id`, `computed_at`)
- `we_drift_alerts`: composite on (`severity`, `detected_at`); on `relationship_id`
- `we_portfolio_concentrations`: composite on (`entity_id`, `dimension`)
- `we_scan_runs`: on `started_at`

All tables include `created_at` and `updated_at` with server-side defaults.

### WE-1d: Intelligence Registry Store

**New file**: `world_engine/registry/store.py`

The registry is the single interface through which all DSI components access World
Engine intelligence. It wraps the database with a query-optimised read API and a
write API used only by internal Engine subsystems.

```python
class IntelligenceRegistry:
    """Single point of access for all World Engine intelligence."""

    def __init__(self, db_session):
        ...

    # --- Read API (available to all DSI components) ---

    def get_maturity_state(self) -> MaturityState:
        """Current maturity stage with capability flags."""
        ...

    def get_active_relationships(
        self, signal_ids: list[str] | None = None
    ) -> list[DiscoveredRelationship]:
        """All ACTIVE relationships, optionally filtered by signal."""
        ...

    def get_relationships_for_entity(
        self, signal_scores: dict[str, float]
    ) -> list[DiscoveredRelationship]:
        """Active relationships matching any of the entity's signals."""
        ...

    def get_relationship(self, relationship_id: str) -> DiscoveredRelationship | None:
        """Single relationship with full state history."""
        ...

    def get_consistency_score(
        self, assessment_id: str
    ) -> ConsistencyScore | None:
        ...

    def get_caf(self, assessment_id: str) -> CausalAdjustmentFactor | None:
        ...

    def get_portfolio_concentrations(
        self, commercial_entity_id: str
    ) -> list[PortfolioConcentration]:
        ...

    def get_drift_alerts(
        self,
        severity: DriftSeverity | None = None,
        since: datetime | None = None,
        unacknowledged_only: bool = False,
    ) -> list[DriftAlert]:
        ...

    def get_engine_stats(self) -> dict:
        """Relationship counts by state, scan run history, maturity."""
        ...

    # --- Write API (internal -- used only by Engine subsystems) ---

    def register_candidate(
        self, relationship: DiscoveredRelationship
    ) -> str:
        ...

    def transition_state(
        self, relationship_id: str, to_state: LifecycleState,
        reason: str, evidence: dict
    ) -> StateTransition:
        ...

    def store_consistency_score(self, score: ConsistencyScore) -> None:
        ...

    def store_caf(self, caf: CausalAdjustmentFactor) -> None:
        ...

    def store_concentration(
        self, concentration: PortfolioConcentration
    ) -> None:
        ...

    def store_drift_alert(self, alert: DriftAlert) -> None:
        ...

    def store_scan_run(self, report: ScanRunReport) -> None:
        ...

    def acknowledge_drift_alert(self, alert_id: str) -> None:
        ...
```

### WE-1e: Registry API Routes

**New file**: `world_engine/registry/api.py`

FastAPI router mounted at `/api/v1/world-engine/`:

| Endpoint                                | Method | Description                                         |
|-----------------------------------------|--------|-----------------------------------------------------|
| `/maturity`                             | GET    | Current maturity stage and capabilities              |
| `/relationships`                        | GET    | List relationships, filterable by state/signal/coverage |
| `/relationships/{id}`                   | GET    | Single relationship with full history                |
| `/consistency/{assessment_id}`          | GET    | Consistency score for an assessment                  |
| `/caf/{assessment_id}`                  | GET    | CAF for an assessment                                |
| `/portfolio/{entity_id}/concentrations` | GET    | Portfolio concentrations for a commercial entity     |
| `/drift-alerts`                         | GET    | Drift alerts, filterable by severity/date/status     |
| `/drift-alerts/{id}/acknowledge`        | POST   | Acknowledge a drift alert                            |
| `/stats`                                | GET    | Engine statistics: counts by state, scan history     |

**New file**: `world_engine/registry/types.py`

Request/response Pydantic models for all API endpoints. Pagination support via
cursor-based scrolling for list endpoints. Filter parameters as query params.

### WE-1f: Integration Points

**File to modify**: `infrastructure/api/main.py`

Mount the registry router:

```python
from world_engine.registry.api import router as world_engine_router

app.include_router(
    world_engine_router,
    prefix="/api/v1/world-engine",
    tags=["World Engine"],
)
```

Add Engine health to existing health check at `/api/v1/health/ready`:

```python
# In health check handler, add:
maturity = MaturityEvaluator().evaluate(db_session)
health["world_engine"] = {
    "status": "ok",
    "maturity_stage": maturity.stage.value,
    "active_relationships": maturity.active_relationships,
}
```

---

## Dependencies

- Alembic migration infrastructure (exists)
- FastAPI app (exists -- `infrastructure/api/main.py`)
- SQLAlchemy models (exists -- extend pattern from `infrastructure/db/models.py`)
- Pydantic (exists in project dependencies)

---

## Constraints

1. No changes to existing pricing or commercial code
2. No changes to existing database tables
3. All new tables use the `we_` prefix for namespace isolation
4. Types defined here are the contract for all subsequent phases -- changes after
   WE-1 require migration
5. The registry write API is not exposed via HTTP -- only internal Python access

---

## Success Criteria

1. All database tables created via migration; `alembic upgrade head` succeeds
2. `world_engine/` importable from all other DSI modules
3. Registry store passes unit tests for all read/write operations
4. API routes return correct responses (empty data -- no intelligence yet)
5. Maturity evaluator correctly computes stage from assessment database
6. Health check endpoint includes World Engine status
7. No changes to existing pricing or commercial code
8. All existing tests pass unchanged

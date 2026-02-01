# Phase V3-5: Simulation Engine Foundation

**Status:** Not Started
**Priority:** Medium
**Prerequisites:** V3-2 (Continuous Monitoring)

## Context

The DSI Vision Paper describes three strategic capabilities enabled by world models:

1. **Counterfactual Simulation** — "What happens if this vulnerability propagates?"
2. **Portfolio Optimisation** — "What is the marginal impact of this submission on portfolio volatility?"
3. **Homeostasis** — "Detect drift → trigger intervention before loss occurs"

Currently, DSI has the organisational graph (R8) and derivatives (entropy/velocity/drift), but no simulation engine that can advance the graph state forward in time.

## Objective

Build the foundation for counterfactual simulation: given the current organisational graph state, simulate exogenous shocks and compute probable outcomes.

## Tasks

1. **Graph State Snapshots** — Save and restore graph state for simulation branching
2. **Shock Propagation** — Simulate a signal change propagating through the graph (e.g., vulnerability → all dependent nodes)
3. **Portfolio Impact Calculator** — Given a new submission, calculate marginal impact on portfolio correlation and volatility
4. **Scenario Library** — Pre-built scenarios (vendor compromise, ransomware propagation, regulatory change)
5. **Simulation API** — `/api/v1/simulate` endpoint for what-if queries

## Architecture

```
Simulation Engine
    │
    ├──► Graph State Snapshot (save current state)
    │
    ├──► Shock Application (modify specific signals/nodes)
    │       │
    │       └──► Propagation (PageRank recomputation)
    │               │
    │               └──► Derivative Recalculation
    │
    ├──► Outcome Assessment (re-score all affected entities)
    │
    └──► Impact Report (delta from baseline)
```

## Key Files to Create

- `infrastructure/simulation/engine.py` — Core simulation logic
- `infrastructure/simulation/scenarios.py` — Scenario library
- `infrastructure/simulation/portfolio.py` — Portfolio impact calculations
- `infrastructure/api/routes/simulation.py` — Simulation API endpoints

## Success Criteria

- Can snapshot and restore graph state
- Can simulate single-signal shock and observe propagation
- Portfolio impact calculation for new submissions
- At least 3 pre-built scenarios
- Processing time < 5 seconds per simulation

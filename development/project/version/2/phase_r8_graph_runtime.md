# Phase R8: Organisational Graph Runtime

**Status:** ✅ Complete
**Parent Plan:** `dsi_restructure_plan.md`

## Objective

Implement the organisational graph runtime as described in the Vision Paper — nodes representing entities, edges representing relationships, with PageRank propagation and behavioural derivative calculations.

## Deliverables

- Graph data model: 6 node types (COMPANY, SUBSIDIARY, DOMAIN, PERSON, VENDOR, ASSET)
- 6 edge types (OWNS, OPERATES, EMPLOYS, PARTNERS_WITH, DEPENDS_ON, CERTIFIES)
- NodeFactory for creating typed graph nodes from entity data
- EdgeInferencer for inferring relationship edges from signal data
- PageRank-based risk propagation across graph
- 5 derivative calculations:
  - **Entropy** — control decay metric (stddev of infrastructure scores)
  - **Velocity** — operational overload (change rate / governance rate)
  - **Drift** — emerging fragility (z-score distance from cohort)
  - **Fragility** — structural weakness
  - **Concentration** — dependency concentration risk
- Graph storage backend (in-memory)

## Key Files

- `signal_architecture/graph/types.py` — Node, Edge, Graph types (~410 lines)
- `signal_architecture/graph/node_factory.py` — Node creation
- `signal_architecture/graph/edge_inferencer.py` — Edge inference
- `signal_architecture/graph/graph_builder.py` — Graph construction
- `signal_architecture/graph/propagation/algorithms.py` — PageRank, risk propagation
- `signal_architecture/graph/derivatives/calculator.py` — Entropy, Velocity, Drift
- `signal_architecture/graph/storage.py` — Graph persistence
- `schemas/organisational_graph.yaml` — Graph schema definition

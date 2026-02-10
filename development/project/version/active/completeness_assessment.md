# DSI Completeness Assessment

**Date:** 2026-02-01
**Assessed by:** Claude Code (automated)
**Codebase:** 289 Python files, ~87,000 lines, 7 coverages, 4 Rust source files

---

## Executive Summary

DSI is a **functional prototype** that demonstrates the core thesis of both papers. The 14-step workflow runs end-to-end, producing scored and priced submissions across 7 coverage verticals. The organisational graph and behavioural derivatives are implemented. However, signal extraction uses stubs (not real data), continuous monitoring is absent, and the simulation capabilities described in the vision paper are not yet built.

**Whitepaper promises:** ~70% delivered
**Vision paper promises:** ~35% delivered

---

## Whitepaper Assessment: "A New Information Substrate for Insurance"

### 10 Foundational Principles

| # | Principle | Status | Evidence |
|---|-----------|--------|----------|
| 1 | External Observability | Partially | Signal architecture designed for external data; extractors are stubs |
| 2 | Machine Readability | ✅ Delivered | All signals normalised to 0-100, machine-processed |
| 3 | Network Authority | ✅ Delivered | Graph with PageRank propagation, trust/dependency edges |
| 4 | Behavioural Inference | ✅ Delivered | Three-layer assessment with correlation directions |
| 5 | Absence as Signal | Partially | Config supports it; extraction doesn't yet measure absence |
| 6 | Structured Data Utilisation | ✅ Delivered | Metadata registry, proxy tiers, structured data feeds |
| 7 | Minimal Direct Inquiry | ✅ Delivered | Max 10 direct queries per config, enforced by validator |
| 8 | Organisational Assessment | ✅ Delivered | Entity-level scoring, graph-based org relationships |
| 9 | Simplicity in Scoring | ✅ Delivered | Clear composite → tier → premium flow, auditable |
| 10 | Agentic Readiness | ✅ Delivered | API-driven, deterministic, no human-in-loop required |

**Score: 8/10 principles delivered (2 partially)**

### Signal Architecture

| Capability | Status | Detail |
|------------|--------|--------|
| 7 signal categories | ✅ Delivered | Network, Technical, Footprint, Behavioural, Public Record, Structured Data, Direct Inquiry |
| 200-400 signals per submission | Partially | Config supports 15-40 per coverage; ~50 signals in library; stubs only |
| Signal normalisation (0-100) | ✅ Delivered | All signals scored 0-100 |
| Confidence scoring (0-1) | ✅ Delivered | Data availability, source reliability tracked |
| Proxy tier classification | ✅ Delivered | DIRECT_OBSERVABLE, INFERRED_PROXY, COHORT_INFERENCE in metadata registry |
| Temporal decay (TTL) | ✅ Delivered | TTL per signal in metadata registry |
| Signal metadata registry | ✅ Delivered | 1300-line registry covering all 7 coverages |

### Processing Workflow

| Capability | Status | Detail |
|------------|--------|--------|
| 6-phase, 14-step workflow | ✅ Delivered | Full implementation in `layers/risk/workflow.py` |
| Discovery (Step 0) | ✅ Delivered | `signal_architecture/discovery/website_discovery.py` |
| Config instantiation (Step 1) | ✅ Delivered | Content-addressable storage pattern |
| Signal extraction (Step 4) | Partially | Stub extractors return synthetic data |
| Three-layer assessment (Steps 5a-c) | ✅ Delivered | Risk, Loss, Exposure layers run in parallel |
| Score conditions (Step 6) | ✅ Delivered | FLAG/MODIFIER/REFER with banded thresholds |
| Direct queries (Step 7) | ✅ Delivered | query_condition evaluation |
| Tier override (Step 8) | ✅ Delivered | Maximum worst-case override |
| Pricing (Steps 10-12) | ✅ Delivered | ILF scaling, deductible credits, modifiers |
| Decision (Step 13) | ✅ Delivered | APPROVE/REFER/DECLINE with audit trail |

### Assessment Outputs

| Output | Status | Detail |
|--------|--------|--------|
| Composite risk score (0-1000) | ✅ Delivered | Weighted sum × 10 |
| Risk tier (1-5) | ✅ Delivered | Configurable via risk_tier_bands |
| Risk confidence score (0-1) | ✅ Delivered | Data availability tracking |
| Exposure band | ✅ Delivered | Size + complexity dimensions |
| Loss propensity (0-100) | ✅ Delivered | Frequency + severity scoring |
| Cohort assignment | ✅ Delivered | `infrastructure/analytics/cohorts.py` |
| Final premium | ✅ Delivered | Three-layer multiplicative pricing |
| Decision (Approve/Refer/Decline) | ✅ Delivered | Deterministic decision logic |
| Audit trail | ✅ Delivered | Model versioning, model data files |
| Processing < 60 seconds | ✅ Delivered | Benchmarked at ~80ms per assessment |

### Operational Targets

| Target | Status | Detail |
|--------|--------|--------|
| 60-80% straight-through processing | Cannot verify | Requires production data and real extractors |
| < 60 second time to quote | ✅ Delivered | ~80ms with stub extractors |
| < $10 cost per submission | Architecture supports | Depends on API costs for real extractors |
| Model versioning | ✅ Delivered | Content-addressable config storage |
| Complete audit trail | ✅ Delivered | Model data file captures all dimensions |

---

## Vision Paper Assessment: "World Models for Insurance"

### Organisational Graph

| Capability | Status | Detail |
|------------|--------|--------|
| Graph data structure | ✅ Delivered | Nodes, edges, weights in `graph/types.py` |
| 6 node types | ✅ Delivered | COMPANY, SUBSIDIARY, DOMAIN, PERSON, VENDOR, ASSET |
| 6 edge types | ✅ Delivered | OWNS, OPERATES, EMPLOYS, PARTNERS_WITH, DEPENDS_ON, CERTIFIES |
| PageRank propagation | ✅ Delivered | Python + Rust implementations |
| Risk propagation | ✅ Delivered | Across graph edges |
| Graph construction from signals | ✅ Delivered | `graph_builder.py`, `node_factory.py`, `edge_inferencer.py` |

### Behavioural Derivatives

| Derivative | Status | Detail |
|------------|--------|--------|
| Entropy (control decay) | ✅ Delivered | Stddev-based calculation in `calculator.py` |
| Velocity (operational overload) | ✅ Delivered | change_rate / governance_rate |
| Drift (emerging fragility) | ✅ Delivered | Z-score distance from cohort |
| Fragility | ✅ Delivered | Structural weakness metric |
| Concentration | ✅ Delivered | Dependency concentration risk |
| Time-series deltas | NOT delivered | Derivatives are point-in-time, not tracked over time |

### Continuous Monitoring

| Capability | Status | Detail |
|------------|--------|--------|
| Continuous observation | NOT delivered | Point-in-time assessments only |
| Signal refresh scheduling | NOT delivered | No TTL-based refresh pipeline |
| Nyquist-Shannon compliance | NOT delivered | No continuous sampling implemented |
| Leading indicator detection | Partially | Derivatives exist but no temporal tracking |
| Cohort migration tracking | NOT delivered | Cohorts assigned but not tracked over time |

### Strategic Capabilities

| Capability | Status | Detail |
|------------|--------|--------|
| **Counterfactual Simulation** | NOT delivered | No simulation engine |
| Graph state snapshots | NOT delivered | No snapshot/restore |
| Shock propagation | NOT delivered | No scenario-based propagation |
| **Portfolio Optimisation** | NOT delivered | No portfolio impact calculation |
| Marginal submission impact | NOT delivered | — |
| Dynamic capital allocation | NOT delivered | — |
| **Homeostasis (Closed Loop)** | NOT delivered | No drift → intervention pipeline |
| Automatic intervention triggers | NOT delivered | — |
| Proactive risk management | NOT delivered | — |

### Paradigm Shift Metrics

| Dimension | Whitepaper Target | Current State |
|-----------|-------------------|---------------|
| Data source | Direct observation | Stub extractors (synthetic data) |
| Analysis type | Simulation | Point-in-time assessment |
| Response type | Prevention (homeostasis) | Reactive (assess on submission) |
| Observation frequency | Continuous | One-shot per submission |
| Feature basis | Behavioural derivatives | Derivatives exist, no temporal tracking |
| Decision type | Real-time | Real-time (within assessment) |

---

## Component Completeness Summary

| Component | Completeness | Notes |
|-----------|-------------|-------|
| **Config Architecture (v2.0)** | 95% | All 7 configs, validator, builder, CLI |
| **Signal Architecture** | 75% | Pipeline complete; extractors are stubs |
| **Risk Layer** | 90% | Full 14-step workflow, scorer, pricer |
| **Loss Layer** | 80% | Scorer, config adapter, monitoring; needs production calibration |
| **Exposure Layer** | 80% | Scorer, size/complexity; needs real data validation |
| **Organisational Graph** | 85% | Full graph + 5 derivatives; no time-series |
| **Rust Accelerators** | 80% | 4 source files; not compiled as wheel |
| **API** | 85% | 32 endpoints, auth, observability; some routes untested |
| **Database** | 75% | Models, migrations, repositories; dual storage |
| **Builder** | 90% | v2.0 compliant, CLI, validator, 24 tests |
| **Testing** | 30% | 54 passing; 10 broken files; ~12% coverage |
| **CI/CD** | 70% | Rust build, Docker, deploy stages; not fully validated |
| **Continuous Monitoring** | 5% | Architecture mentioned; not implemented |
| **Simulation Engine** | 0% | Not started |
| **Production Extractors** | 10% | Factory exists; all extractors are stubs |

---

## Gap Analysis: What's Missing

### To Fulfil the Whitepaper (~30% remaining)

1. **Real signal extraction** — Production extractors calling actual APIs (security headers, TLS, DNS, breach databases, regulatory filings). This is the single largest gap. Without real data, DSI cannot demonstrate its core value proposition.

2. **Absence-as-signal measurement** — The config schema supports it, but extraction doesn't currently measure the *absence* of expected signals as a negative indicator.

3. **Signal volume** — The whitepaper describes 200-400 signals per submission. Current configs have 15-40 per coverage. The metadata registry has signals catalogued but many lack implementations.

4. **Test coverage** — 10 broken test files, ~12% coverage. Must reach 60%+ on critical paths before release.

### To Fulfil the Vision Paper (~65% remaining)

5. **Continuous monitoring pipeline** — TTL-based signal refresh, delta detection, derivative time-series, alert pipeline. This is the foundation for everything else in the vision paper.

6. **Temporal derivative tracking** — Entropy, velocity, drift exist as point-in-time calculations. The vision paper requires them as time-series for leading indicator detection (6-12 month advance warning).

7. **Counterfactual simulation** — Graph state snapshots, shock propagation, outcome assessment. The graph infrastructure exists; the simulation engine does not.

8. **Portfolio optimisation** — Marginal submission impact on portfolio volatility, correlation-aware pricing. Analytics module exists but lacks portfolio-level simulation.

9. **Homeostasis (closed-loop carrier)** — Drift detection → automatic intervention (notification, repricing, non-renewal). Requires continuous monitoring as prerequisite.

10. **Cohort migration tracking** — Cohort assignment exists; tracking movement between peer groups over time does not.

---

## Recommendation

The most impactful next steps, in order:

1. **Fix tests (V3-1)** — Prerequisite for everything. Cannot validate any changes without a working test suite.

2. **Production extractors (V3-4)** — Even 5-10 real extractors (free APIs: security headers, TLS, DNS, SPF/DKIM) would demonstrate the whitepaper's core thesis with real data.

3. **Continuous monitoring (V3-2)** — This unlocks the vision paper's promises. Signal refresh + temporal derivatives + alerts.

4. **Release v1.0.0 (V3-6)** — Clean baseline for external demonstration.

5. **Simulation engine (V3-5)** — Counterfactual capabilities that differentiate DSI from traditional models.

These correspond exactly to the V3 active plan phases.

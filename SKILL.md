-----

## name: dsi-framework

description: Digital Signal Intelligence (DSI) insurance pricing framework. Use this skill when working on any aspect of DSI project code.

# DSI Framework Development Guide

## Development Workflow

When starting any DSI work:

1. **Read this SKILL.md first**
1. **Check the active development plan**: `development/project/version/active/README.md`
1. **Do not proceed without a phase plan**: Every task must have one in `development/project/version/active/`
1. **Reference YAML config** for the coverage you're working on
1. **Never hardcode** — if it's in YAML, read it from YAML
1. **Follow the foundational principles**: `docs/overview/Foundational Principles.md`
1. **Follow the 14-step workflow** — don't skip or reorder steps
1. **Use the coverage builder** to create new coverages: `infrastructure/builder/README.md`
1. **Validate configs** before committing: `python -m infrastructure.builder.cli validate coverages/*/config.yaml`

## Project Status

### Development History

| Version | Phases | Description | Location | Status |
|---------|--------|-------------|----------|--------|
| 1 | Phases 1-23 | Foundation through Config Architecture | `development/project/version/1/` | ✅ Complete |
| 2 | R1-R11, P1-P7 | Restructure + Production Readiness | `development/project/version/2/` | ✅ Complete |
| **3** | **V3-1 to V3-6** | **Test recovery, monitoring, extractors, release** | **`development/project/version/active/`** | **Active** |

### Active Work (Version 3)

| Phase | Name | Status | Priority |
|-------|------|--------|----------|
| V3-1 | Test Suite Recovery | Not Started | Critical |
| V3-2 | Continuous Monitoring Pipeline | Not Started | High |
| V3-3 | LLM Integration for Builder | Not Started | Medium |
| V3-4 | Production Signal Extractors | Not Started | Medium |
| V3-5 | Simulation Engine Foundation | Not Started | Medium |
| V3-6 | Release v1.0.0 | Not Started | High |

### Current Metrics

| Metric | Value |
|--------|-------|
| Python files | 289 |
| Total lines | ~87,000 |
| Coverage configs | 7 (aerospace, cyber, D&O, energy, FI, marine, PI) |
| Tests passing | 54 (24 builder + 21 E2E + 9 performance) |
| Tests broken | 10 files (stale imports from restructure) |
| Rust source files | 4 (graph, derivatives, validation, lib) |

---

## What is DSI?

Digital Signal Intelligence (DSI) is an insurance information substrate based on **observable digital signals** rather than self-reported documentation. Core insight: who trusts/partners/certifies an entity reveals risk quality more reliably than what they claim about themselves.

**Key Documents:**
- `docs/overview/Foundational Principles.md` — Mandatory design principles
- `docs/overview/Whitepaper_Digital_Signal_Intelligence.pdf` — Technical whitepaper
- `docs/overview/Visionpaper_Digital_Signal_Intelligence.pdf` — World Model vision

---

## Architecture Overview

```
SUBMISSION INPUT (company name, domain, coverage, limits)
        │
        ▼
┌─────────────────────────────────────────────────────────┐
│  DISCOVERY (Step 0)                                     │
│  Search → Validate → Identify primary website           │
│  Output: URL + confidence + corporate identity          │
└─────────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────┐
│  YAML CONFIG (single source of truth)                   │
│  v2.0 schema: signal_registry, groups, tier bands       │
│  coverages/{coverage}/config.yaml                       │
└─────────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────┐
│  SIGNAL ARCHITECTURE (shared infrastructure)            │
│                                                         │
│  Extractor → Aggregator → Categoriser → Inference       │
│  (raw data)   (normalise)  (score/cat)   (orchestrate)  │
│                                                         │
│  Metadata Registry: proxy_tier, TTL, coverage map       │
└─────────────────────────────────────────────────────────┘
        │
        ├─────────────────┬─────────────────┐
        ▼                 ▼                 ▼
┌─────────────────────────────────────────────────────────┐
│  THREE-LAYER PARALLEL ASSESSMENT                        │
│                                                         │
│  ┌───────────────┐ ┌───────────────┐ ┌───────────────┐  │
│  │ RISK SCORING  │ │ LOSS LAYER    │ │ EXPOSURE      │  │
│  │               │ │               │ │               │  │
│  │ Composite     │ │ Frequency +   │ │ Size band +   │  │
│  │ score (0-1000)│ │ severity      │ │ complexity    │  │
│  │ → Risk Tier   │ │ propensity    │ │ → Exposure    │  │
│  │ (1-5)         │ │ (0-100)       │ │   Band        │  │
│  │               │ │ → Loss        │ │               │  │
│  │               │ │   Modifier    │ │               │  │
│  └───────────────┘ └───────────────┘ └───────────────┘  │
│        │                 │                 │             │
│        └─────────────────┼─────────────────┘             │
│                          │                               │
└─────────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────┐
│  ORGANISATIONAL GRAPH                                   │
│                                                         │
│  6 node types × 6 edge types × PageRank propagation     │
│  Derivatives: Entropy, Velocity, Drift                  │
│  (Rust-accelerated via PyO3 dsi-core crate)             │
└─────────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────┐
│  PRICING ENGINE                                         │
│                                                         │
│  Risk Tier × Exposure Band × Loss Modifier              │
│  → Base Premium → Modifiers → ILF Scaling               │
│  → Decision: APPROVE | REFER | DECLINE                  │
│  → Full audit trail                                     │
└─────────────────────────────────────────────────────────┘
```

### Codebase Organisation

| Area | Purpose | Key Modules |
|------|---------|-------------|
| `signal_architecture/` | Signal processing | signals, discovery, orchestration, graph |
| `infrastructure/` | Support systems | api, db, analytics, builder, observability |
| `layers/` | Assessment layers | risk (14-step workflow), exposure, loss |
| `coverages/` | Configuration | 7 YAML configs (v2.0 schema) |
| `rust/dsi-core/` | Performance | PageRank, derivatives, validation (PyO3) |

---

## 14-Step Workflow

| Step | Name | Description |
|------|------|-------------|
| 0 | Discovery | Entity identification, website discovery |
| 1 | Config Instantiation | Load YAML config, create model version |
| 2 | Model Data Creation | Initialise model data file |
| 3 | Input Verification | Check minimum viable inputs present |
| 4 | Signal Extraction | Run all extractors → aggregators → inference |
| 5a | Risk Scoring | Composite score (0-1000) from risk weights |
| 5b | Exposure Scoring | Size + complexity bands (0-100) |
| 5c | Loss Scoring | Frequency + severity propensity (0-100) |
| 6 | Score Conditions | Evaluate signal-level conditions (FLAG/MODIFIER/REFER) |
| 7 | Direct Queries | Evaluate query responses |
| 8 | Tier Override | Apply maximum (worst) tier override |
| 9 | Layer Capture | Capture final outputs from all three layers |
| 10 | Base Premium | Risk Tier × Exposure Band × Loss Modifier |
| 11 | Modifiers | Apply categorical + query modifiers |
| 12 | Limit Scaling | ILF curve + deductible credits |
| 13 | Decision | APPROVE / REFER / DECLINE + audit trail |

---

## Creating New Coverages

**Full documentation:** `infrastructure/builder/README.md`

### Quick Start

```bash
# Build a new coverage
python -m infrastructure.builder.cli build \
    --name "Cyber Japan" \
    --industry technology \
    --description "Cyber liability for Japanese market" \
    --market jp --strategy conservative --write

# Validate existing config
python -m infrastructure.builder.cli validate coverages/cyber/config.yaml
```

### Programmatic API

```python
from infrastructure.builder.coverage_builder import CoverageBuilder
from infrastructure.builder.types import CoverageSpec

spec = CoverageSpec(
    name="Casualty",
    description="General casualty coverage",
    industry="manufacturing",
    target_market="US mid-market",
)
builder = CoverageBuilder()
result = await builder.create_coverage(spec)
# result.config_yaml contains v2.0 compliant YAML
# result.validation_results confirms schema compliance
```

The builder generates configs matching the canonical v2.0 schema with: `signal_registry`, `groups`, `risk_tier_bands`, `loss_tier_bands`, `exposure`, `pricing`. All configs are validated before output.

---

## v2.0 Config Schema

**Reference:** `coverages/master_config_layout.yaml`

```yaml
coverage_id:
  coverage_id_general:
    metadata:           # name, version, min_premium, markets, minimum_viable_input
    direct_queries:     # Binary questions with query_condition (max 10)
    signal_registry:    # All signals, each with three_layer_assessment or categories
    groups:
      categories:               # Categorical modifier groups
      three_layer_assessment:   # Scoring dimension groups (risk/loss/exposure weights)
    risk_tier_bands:    # 0-1000 → tier (APPROVE/REFER/DECLINE) + base premium
    loss_tier_bands:    # 0-100 → frequency/severity modifiers + constraints
    exposure:
      size:             # 0-100 → size bands with implied thresholds
      complexity:       # 0-100 → complexity bands
    limit_bandings:     # Standard limit/deductible combinations
    pricing:            # ILF curve, deductible credits, taxes
```

### Critical Rules

| Rule | Detail |
|------|--------|
| **score_conditions actions** | `FLAG \| MODIFIER \| REFER` only. **DECLINE is tier-level only.** |
| **score_conditions are banded** | Always a list of multiple threshold conditions |
| **score_conditions scope** | Apply to signal_registry and groups — NOT tier bands |
| **Scores: signals** | 0-100 per signal |
| **Scores: composite risk** | 0-1000 (weighted sum × 10) |
| **Scores: loss/exposure** | 0-100 each |
| **Weights sum to 1.0** | Signal weights within group, group weights across TLA, exposure size+complexity |
| **YAML is truth** | Never hardcode values that exist in config |
| **Audit trail** | Every price traces: signals → scores → tier → premium |

---

## Key Import Paths

```python
# Workflow (main entry point)
from layers.risk.workflow import run_assessment

# Signal Architecture
from signal_architecture.signals.inference.metadata_registry import SIGNAL_METADATA_REGISTRY
from signal_architecture.graph.graph_builder import GraphBuilder
from signal_architecture.graph.derivatives.calculator import DerivativeCalculator
from signal_architecture.discovery.website_discovery import WebsiteDiscoveryEngine

# Infrastructure
from infrastructure.builder.coverage_builder import CoverageBuilder
from infrastructure.builder.validator import ConfigValidator
from infrastructure.api.main import app

# Layers
from layers.risk.scorer import ModelScorer
from layers.risk.pricer import Pricer
from layers.exposure.scorer import ExposureScorer
from layers.loss.scorer import LossScorer
```

---

## Outstanding Work

See `development/project/version/active/README.md` for the full active plan.

### Critical

- **Test Suite Recovery (V3-1):** 10 test files broken by stale imports from restructure
- **Release v1.0.0 (V3-6):** All tests passing, CI green, Docker builds, docs current

### High Priority

- **Continuous Monitoring (V3-2):** Signal refresh scheduler, derivative time-series, alert pipeline
- **Production Extractors (V3-4):** Replace stub extractors with real API integrations

### Medium Priority

- **LLM Builder Integration (V3-3):** Wire LLM client for enhanced signal selection
- **Simulation Engine (V3-5):** Counterfactual simulation, portfolio impact, scenario library
- Compile Rust dsi_core wheel (`maturin develop`)

### Optional

- ML module (gradient boosting, anomaly detection)
- Performance dashboards
- Natural language portfolio search
- LLM prompt templates for coverage building

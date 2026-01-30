-----

## name: dsi-framework

description: Digital Signal Intelligence (DSI) insurance pricing framework. Use this skill when working on any aspect of DSI project code.

# DSI Framework Development Guide

## Development Workflow

When starting any DSI work:

1. **Read this SKILL.md first**
1. **Follow the link to the Development documentation indicated in Implementation Status. If this cannot be found, it must be created first**
1. **Review development/project/ for the relevant phase development plans**: Contains phase development plans
1. **Do not proceed with work without a phase development plan**: These are required
1. **Always seek clarification if a request is unclear** 
1. **Reference YAML config** for the coverage you're working on
1. **Never hardcode** - if it's in YAML, read it from YAML
1. **Ensure the foundational principles are followed at all stages**: `docs/overview/Foundational Principles.md`
1. **Follow the standard patterns** - don't invent new structures
1. **Follow the 14-step workflow** - don't skip or reorder steps
1. **Check technical_pricing/cross_walk/by_coverage.json** for common concepts
1. **For loss correlation work**: Review `loss/correlation_layer/development/` specification documents
1. **For exposure shadow work**: Review `exposure/shadow_layer/development/` specification documents

## Implementation Status

| Phase | Name | Status | Development documentation |
|-|-|-|-|
| 1 | Foundation | ✅ Complete |  `development/project/phase_1.md` |
| 2 | Reusable Categorizer Types | ✅ Complete |  `development/project/phase_2.md` |
| 3 | Coverage Implementations | ✅ Complete | `development/project/phase_3.md` |
| 4 | Config-Driven Model | ✅ Complete |  `development/project/phase_4.md` |
| 5 | Scoring Engine | ✅ Complete |  `development/project/phase_5.md` |
| 6 | Discovery Integration | ✅ Complete |  `development/project/phase_6.md` |
| 7 | Traditional Modifiers | ✅ Complete |  `development/project/phase_7.md` |
| 8 | Analytics Engine | ✅ Complete |  `development/project/phase_8.md` |
| 9 | Test Profiles | ✅ Complete |  `development/project/phase_9.md` |
| 10 | Multi-Coverage | ✅ Complete |  `development/project/phase_10.md` |
| 11 | Production API | ✅ Complete |  `development/project/phase_11.md` |
| 12 | Integration Layer | ✅ Complete |  `development/project/phase_12.md` |
| 13 | LLM Builder | ✅ Complete |  `development/project/phase_13.md` |
| 14 | Examples | ✅ Complete |  `development/project/phase_14.md` |
| 15 | Production Extractors | ✅ Complete |  `development/project/phase_15.md` |
| 16 | Loss Correlation | 🔲 Not Started |  `development/project/phase_16.md` |
| 17 | Exposure Shadow Layer | 🔲 Not Started | `development/project/phase_17.md` |
| 18 | Architecture Restructuring | ✅ Complete | `development/project/phase_18.md` |
| 19 | DSI Demo Production Build | 🔄 In Progress | `development/project/phase_19.md` |
| 20 | Config Architecture & Org Graph | ✅ Complete | `development/project/phase_20.md` |
| 21 | Loss Correlation Implementation | 🔲 Not Started | TBD |
| 22 | Exposure Shadow Implementation | 🔲 Not Started | TBD |
| 23 | Organisational Graph Runtime | 🔲 Not Started | TBD |

### DSI Comprehensive Restructure (Active)

| Phase | Name | Status | Development documentation |
|-|-|-|-|
| R1 | Master Configuration Layout | ✅ Complete | `development/project/dsi_restructure_plan.md` |
| R2 | Signal Architecture Alignment | ✅ Complete | `development/project/dsi_restructure_plan.md` |
| R3 | Coverage Configuration Rebuilds | 🔄 In Progress | `development/project/dsi_restructure_plan.md` |
| R4 | Infrastructure Builder Revision | 🔲 Not Started | `development/project/dsi_restructure_plan.md` |
| R5 | Infrastructure Verification | 🔲 Not Started | `development/project/dsi_restructure_plan.md` |
| R6 | Layer Implementations | 🔲 Not Started | `development/project/dsi_restructure_plan.md` |
| R7 | Model Configuration Validation | 🔲 Not Started | `development/project/dsi_restructure_plan.md` |
| R8 | Organisational Graph Runtime | 🔲 Not Started | `development/project/dsi_restructure_plan.md` |
| R9 | Performance Enhancement (Rust) | 🔲 Not Started | `development/project/dsi_restructure_plan.md` |
| R10 | Documentation & Cleanup | 🔲 Not Started | `development/project/dsi_restructure_plan.md` |
| R11 | Testing | 🔲 Not Started | `development/project/dsi_restructure_plan.md` |

**Validation Status** (January 2026):
- ✅ All core Python imports validated and working
- ✅ Signal analytics module fixed (import order corrected)
- ✅ API schemas complete (country_hint field added)
- ✅ Configuration YAML syntax errors fixed
- ✅ Documentation links validated and corrected
- ✅ 32 API endpoints documented and functional
- ✅ All 7 demo applications validated
- ⚠️ Test coverage at ~12.6% (critical modules need unit tests)
- ✅ 21 inference function name typos fixed across 6 coverage configs
- ✅ Metadata registry created (`signal_architecture/signals/inference/metadata_registry.py`)
- ✅ Signal enhancements stubbed (Marine port state/classification, Aerospace certification/supply chain, Cross-Coverage regulatory)
- ✅ Categoriser audit complete (4 core types + 8 variants implemented, 4 statistical types deferred to Phase 8)

**Next Steps**: See [Outstanding Work](#outstanding-work) section for consolidated pending, planned, and optional items.

---

## What is DSI?

Digital Signal Intelligence (DSI) is a new insurance information substrate based on **observable digital signals** rather than self-reported documentation. Core insight: who trusts/partners/certifies an entity reveals risk quality more reliably than what they claim about themselves.

Foundational Principles, which must be adhered to, can be found here:  `docs/overview/Foundational Principles.md`

The detailed whitepaper can be found here: `docs/overview/Whitepaper_Digital_Signal_Intelligence.pdf`

The detailed visionpaper can be found here: `docs/overview/Visionpaper_Digital_Signal_Intelligence.pdf`

-----

## Architecture Overview

```
┌──────────────────────────────────────────────────────────────────┐
│                     SUBMISSION INPUT                             │
│     Company name, domain hint, coverage, TIV, limits             │
└──────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│                   DISCOVERY MODULE (Step 0)                      │
│                                                                  │
│  ┌──────────┐    ┌──────────┐    ┌───────────┐                   │
│  │SEARCH    │ →  │VALIDATE  │ →  │IDENTIFY   │                   │
│  │          │    │          │    │           │                   │
│  │Find      │    │Corporate │    │Primary    │                   │
│  │candidates│    │website   │    │website    │                   │
│  └──────────┘    └──────────┘    └───────────┘                   │
│                                                                  │
│  Output: Discovered website URL + confidence + identity          │
└──────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│                        YAML CONFIG                               │
│     Single source of truth for coverage model definition         │
│   (weights, modifiers, tiers, direct queries, conditions)        │
└──────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│                    SIGNAL ARCHITECTURE                           │
│                                                                  │
│  ┌──────────┐    ┌──────────┐    ┌───────────┐    ┌──────────┐   │
│  │EXTRACTOR │ →  │AGGREGATOR│ →  │CATEGORIZER│ →  │INFERENCE │   │
│  │          │    │          │    │           │    │          │   │
│  │Raw data  │    │Structure/│    │Score or   │    │Orchestrat│   │
│  │from APIs │    │normalize │    │category   │    │pipeline  │   │
│  └──────────┘    └──────────┘    └───────────┘    └──────────┘   │
│                                                                  │
│  Shared signal infrastructure - feeds all three assessment layers│
└──────────────────────────────────────────────────────────────────┘
                              │
          ┌───────────────────┼───────────────────┐
          │                   │                   │
          ▼                   ▼                   ▼
┌──────────────────────────────────────────────────────────────────┐
│              THREE-LAYER PARALLEL ASSESSMENT                     │
│                                                                  │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐     │
│  │  RISK SCORING   │ │ EXPOSURE SHADOW │ │ LOSS CORRELATION│     │
│  │   (Steps 5-6)   │ │  LAYER (Ph 17)  │ │  LAYER (Ph 16)  │     │
│  │                 │ │                 │ │                 │     │
│  │ Composite score │ │ Exposure band   │ │ Loss propensity │     │
│  │ + conditions    │ │ + complexity    │ │ + cohort        │     │
│  │ → Risk Tier     │ │ → Exposure Band │ │ → Loss Modifier │     │
│  └─────────────────┘ └─────────────────┘ └─────────────────┘     │
│          │                   │                   │               │
│          └───────────────────┼───────────────────┘               │
│                              │                                   │
└──────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│                      PRICING ENGINE                              │
│                                                                  │
│  ┌──────────┐                                                    │
│  │CONFIG    │    Risk Tier × Exposure Band × Loss Modifier       │
│  │MANAGER   │ →                    ↓                             │
│  │Hash/store│    Base Premium → Modifiers → Limits → Decision    │
│  └──────────┘                                                    │ 
│                                                                  │
│  PRICER → WORKFLOW ENGINE → Decision (Approve/Refer/Decline)     │
└──────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│                      MODEL OUTPUT                                │
│                                                                  │
│  Risk Layer:     Score → Tier → Conditions → Referrals           │
│  Exposure Layer: Exposure Band → Complexity Category → Range     │
│  Loss Layer:     Propensity Score → Cohort → Trend → Alerts      │
│                                                                  │
│  Combined:       Final Premium → Decision (Approve/Refer/Decline)│
│                  + Full audit trail across all three layers      │
└──────────────────────────────────────────────────────────────────┘
```

-----

## Model Process Workflow

The complete model execution follows this workflow:

### Step 1: Model Configuration Instantiation

Configuration uses **Content-Addressable Storage (Hybrid)** pattern:

**Stage 1 - Payload Storage:**

- YAML configuration converted to SHA-256 hash
- Hash ensures unique integrity (any change = new hash)
- If hash is new → persist payload to S3 (Azure/AWS/GCP)
- If hash exists → skip (prevents duplication)

**Stage 2 - Metadata Storage:**

- Metadata (user, timestamp, unique ID) saved to structured storage (PostgreSQL)
- More metadata records than payloads (many versions reference same config)

### Step 2: Model Data File Creation

**Stage 1 - Signal Capture:**

- Every item with an ID captured
- Associated returns (signal outputs) persisted against IDs
- Complete autonomous return = one **model version**

**Stage 2 - Interaction Tracking:**

- Subsequent interactions (e.g., referral review) = new model version
- Full audit trail maintained

### Step 3: Minimum Viable Input Verification

- Check required inputs present
- If available → proceed to Step 4
- If missing → return for user to provide missing inputs

### Step 4: Signal Extraction

- Execute all signal pipelines (Extractor → Aggregator → Categorizer → Inference)
- Save all outputs to model data file
- **Signal outputs feed all three assessment layers** (same data, different weighting)

### Step 5: Three-Layer Parallel Assessment

All three assessment layers run **in parallel** using the same signal outputs:

#### Step 5a: Risk Composite Score (Risk Layer)

- Calculate weighted composite score (0-1000) using risk-specific weights
- No conditions applied yet - pure signal-based score
- Output: Risk score for tier determination

#### Step 5b: Exposure Magnitude Score (Exposure Shadow Layer - Phase 17)

- Calculate exposure score (0-100) using exposure-specific weights
- Apply proxy tier hierarchy (direct → inferred → cohort)
- Output: Exposure band + complexity category + confidence

#### Step 5c: Loss Propensity Score (Loss Correlation Layer - Phase 16)

- Calculate loss propensity score (0-100) using loss-correlated weights
- Separate frequency and severity propensity
- Output: Loss propensity band + cohort assignment + trend direction

### Step 6: Signal Conditions Evaluation

Evaluate conditions defined at signal_group and signal_feature levels.

**Possible impacts (conditions CANNOT modify premium):**

- **(a) Tier override** - force to specific tier regardless of score
- **(b) Referral** - set `auto_approve = false`, send for user verification
- **(c) Note** - post note to file for underwriter review

### Step 7: Direct Query Response Evaluation

Evaluate responses to direct queries (boolean questions).

**Possible impacts:**

- **(a) Tier override** - force to specific tier
- **(b) Referral** - set `auto_approve = false`, send for user verification
- **(c) Note** - post note to file
- **(d) Modifier** - define modifier applied after base premium generation

### Step 8: Maximum Tier Override Application

- If multiple tier overrides triggered (from Steps 6 & 7)
- Apply the **maximum** (worst) tier override
- Example: Score says Tier 2, conditions say Tier 3 and Tier 4 → apply Tier 4

### Step 9: Final Layer Outputs Capture

Capture final outputs from all three assessment layers:

#### Step 9a: Final Risk Tier Capture

- Final tier (after all overrides) captured in model data file
- This is the tier used for premium calculation

#### Step 9b: Final Exposure Band Capture (Phase 17)

- Exposure band (micro/small/medium/large/very_large) captured
- Complexity category (simple → extremely_complex) captured
- Implied TIV range recorded for audit

#### Step 9c: Final Loss Propensity Capture (Phase 16)

- Loss propensity band (very_low → high) captured
- Severity propensity band captured
- Cohort assignment and trend direction recorded

### Step 10: Base Premium Generation

Premium calculation uses **all three layer outputs**:

```
Base Premium = f(Risk Tier, Exposure Band, Loss Propensity)
```

**Pattern A - Multiplicative (Recommended):**

```python
tier_premium = tier_thresholds[risk_tier].base_premium
exposure_modifier = exposure_band_modifiers[exposure_band]
loss_modifier = loss_propensity_modifiers[loss_band]  # bounded by caps/floors

base_premium = tier_premium * exposure_modifier * loss_modifier
```

**Pattern B - Grid-Based:**

```yaml
pricing_grid:
  tier_1:
    small_exposure:
      low_loss: 0.0035
      moderate_loss: 0.0040
      high_loss: 0.0050
```

### Step 11: Modifier Application

Apply all modifiers in sequence:

- Categorical feature modifiers
- Direct query modifiers (from Step 7d)
- Experience modifications
- Any other configured modifiers

### Step 12: Limit Band Scaling

Scale premium across all relevant limit bands per configuration:

- Apply ILF (Increased Limit Factor) tables
- Generate premium for each limit option
- Apply deductible credits per limit

### Step 13: Output Decision

Final output for next steps:

- **Approve** - `auto_approve = true`, within appetite, no referrals triggered
- **Decline** - outside appetite (e.g., Tier 5 with decline rule, or hard decline condition)
- **Refer** - `auto_approve = false`, requires underwriter review

**Referral triggers from all three layers:**
- Risk Layer: Tier override conditions, signal conditions
- Exposure Layer: High exposure + low confidence, complexity threshold
- Loss Layer: High loss propensity + high confidence, significant deterioration

-----

## File Structure

```
# Repository Root
digital-signal-intelligence/
├── SKILL.md                         # This document (development guide)
├── README.md                        # Project overview
├── CHANGELOG.md                     # Version history
├── CONTRIBUTING.md                  # Contribution guidelines
├── pyproject.toml                   # Python project configuration
├── requirements.txt                 # Production dependencies
├── requirements-dev.txt             # Development dependencies
├── setup.py                         # Package setup
├── Dockerfile                       # Container definition
├── docker-compose.yml               # Multi-container orchestration
│
├── docs/                            # Documentation
│   ├── overview/
│   │   ├── Configuration Architecture.md    # ✅ PHASE 20 - Config layer documentation
│   │   ├── Foundational Principles.md    # Core DSI principles
│   │   ├── Pitch_deck.pdf    # DSI Executive summary and pitch
│   │   ├── The_PageRank_Precedent.pdf    # DSI grounding in existing principles
│   │   ├── Visionpaper_Digital_Signal_Intelligence.pdf  # World Model vision
│   │   └── Whitepaper_Digital_Signal_Intelligence.pdf   # Detailed whitepaper
|   |
│   ├── agent_interaction/
│   │   └── dsi_specification.md     # Agent integration spec
|   |
│   └── case_studies/                # Loss case studies
│       └── Retrospective_loss_case_studies.pdf   # Detailed retrospective loss analysis
│
├── schemas/                         # ✅ PHASE 20 - Organisation-wide schemas
│   └── organisational_graph.yaml    # Graph schema for World Model
│
├── development/                     # Development documentation
│   ├── project/                     # Phase documents
│   │   ├── phase_1.md ... phase_#.md   # Implementation phases
│   │   └── original.md              # Master SKILL document
│   └── ...                          # Analysis and methodology docs
│
├── signal_architecture/             # All signal-related code
│   ├── __init__.py
│   ├── signals/                     # Core signal extraction pipeline
│   │   ├── __init__.py
│   │   ├── base.py                  ✅ Base classes
│   │   ├── types.py                 ✅ Data structures
│   │   ├── extractors/
│   │   │   ├── base.py              ✅ StubExtractor + utilities
│   │   │   ├── stubs/               ✅ Coverage-specific stub extractors
│   │   │   └── production/          ✅ PHASE 15 - 50 free extractors
│   │   ├── aggregators/             ✅ Signal aggregation + routing bridges
│   │   ├── categorisers/            ✅ Score categorization (British spelling)
│   │   ├── inference/               ✅ Inference functions + registry
│   │   ├── routing/                 ✅ PHASE 15 - Jurisdiction-aware routing
│   │   └── cross_walk/              ✅ Coverage crosswalk mappings
│   │
│   ├── discovery/                   ✅ PHASE 6 - Entity identification (Step 0)
│   │   └── website_discovery.py     ✅ Discovery engine
│   │
│   └── orchestration/               ✅ PHASE 10 - Multi-coverage coordination
│       ├── types.py                 ✅ Orchestration types
│       ├── multi_coverage.py        ✅ Multi-coverage workflow
│       └── locale_detection.py      ✅ Locale detection
│
├── infrastructure/                  # Support systems and integrations
│   ├── __init__.py
│   ├── api/                         ✅ PHASE 11 - FastAPI REST API
│   │   ├── main.py                  ✅ Application entry
│   │   ├── types.py                 ✅ API types
│   │   ├── routes/                  ✅ Endpoint handlers
│   │   ├── auth/                    ✅ JWT & API key auth
│   │   └── middleware/              ✅ Rate limiting, logging
│   │
│   ├── db/                          ✅ Database layer
│   │   ├── models.py                ✅ SQLAlchemy models
│   │   ├── repositories.py          ✅ Data access
│   │   └── config.py                ✅ Database configuration
│   │
│   ├── analytics/                   ✅ PHASE 8-9 - Performance analytics
│   │   ├── types.py                 ✅ Analytics types
│   │   ├── performance.py           ✅ Performance metrics
│   │   ├── portfolio.py             ✅ Portfolio analytics
│   │   └── signal_analytics.py      ✅ Signal performance
│   │
│   ├── builder/                     ✅ PHASE 13 - LLM coverage builder
│   │   ├── coverage_builder.py      ✅ Builder logic
│   │   ├── validator.py             ✅ Config validation
│   │   └── signal_library.py        ✅ Signal library
│   │
│   └── integrations/                ✅ PHASE 12 - External integrations
│       ├── email/                   ✅ Email notifications
│       ├── documents/               ✅ Document generation
│       └── webhooks/                ✅ Webhook handlers
│
├── layers/                          # Assessment layer implementations
│   ├── __init__.py
│   ├── risk/                        ✅ Risk scoring layer (14-step workflow)
│   │   ├── types.py                 ✅ All dataclasses
│   │   ├── config_manager.py        ✅ Config hashing/storage
│   │   ├── model_data.py            ✅ Model data file management
│   │   ├── scorer.py                ✅ Steps 4-6
│   │   ├── query_evaluator.py       ✅ Step 7
│   │   ├── pricer.py                ✅ Steps 8-12
│   │   ├── workflow.py              ✅ Full orchestration + Step 0
│   │   └── modifiers/               ✅ PHASE 7 - Traditional modifiers
│   │
│   ├── exposure/                    🔲 Exposure Shadow Layer (PHASE 17)
│   └── loss/                        🔲 Loss Correlation Layer (PHASE 16)
│
├── coverages/                       # YAML coverage configurations
│   ├── aerospace/config.yaml        ✅ 21 signals
│   └── #other coverages#/config.yaml            
│
├── exposure/                        # Exposure Shadow Layer specs (PHASE 17)
│   └── shadow_layer/development/    ✅ Specification documents
│
├── tests/                           ✅ Test suite
│   ├── unit/
│   ├── integration/
│   └── api/
│
├── demo/                            ✅ Live demos and examples
│   ├── server.py                    ✅ FastAPI demo server
│   ├── examples/                    ✅ Coverage examples + hybrid routing
│   └── html/                        ✅ Interactive HTML demos
│
└── deploy/                          ✅ Deployment configs
    ├── docker/
    ├── kubernetes/
    └── monitoring/
```

Legend: ✅ Complete | 🔲 Not Started

-----

## Architecture (Phase 18.1) - COMPLETE

**STATUS: ✅ COMPLETE** - Architecture refined with logical groupings.

The codebase is now organised into four main areas:

| Area | Purpose | Contents |
|-|-|-|
| `signal_architecture/` | Signal processing | signals, discovery, orchestration |
| `infrastructure/` | Support systems | api, db, analytics, builder, integrations |
| `layers/` | Assessment layers | risk, exposure, loss |
| `coverages/` | Configuration | YAML configs for all 7 coverages |

**Import Paths:**
```python
# Signal Architecture
from signal_architecture.signals import ExtractorResult, SignalResult
from signal_architecture.discovery import WebsiteDiscoveryEngine
from signal_architecture.orchestration import MultiCoverageOrchestrator

# Infrastructure
from infrastructure.api import app
from infrastructure.db import models
from infrastructure.analytics import performance

# Layers
from layers.risk import workflow, scorer, pricer

# Coverages
from coverages import aerospace, cyber
```

**Next Steps:**
- Phases 16 and 17 can now be implemented in `layers/exposure/` and `layers/loss/`
- All three layers share the common `signal_architecture/signals/` infrastructure

-----

## Coverage Crosswalk

Common concepts appear across multiple coverages with different signal paths. Reference `coverage_crosswalk.json` for mappings:

|Common Concept                  |Coverages with Equivalent|
|--------------------------------|-------------------------|
|Credit Rating                   |All 7                    |
|Certification / License Status  |6 (not D&O)              |
|Leadership Stability            |All 7                    |
|Public Reporting / Disclosure   |All 7                    |
|Regulatory Actions / Enforcement|All 7                    |
|Incident / Breach History       |All 7                    |
|Accident / Litigation History   |All 7                    |
|Industry Engagement             |All 7                    |
|Banking Relationship            |5 (not Aerospace, PI)    |

-----

## YAML Config Structure

**CRITICAL: The YAML config is the single source of truth. Never hardcode values that exist in config.**

**Reference:** `coverages/master_config_layout.yaml` - VERSION 2.0

```yaml
coverage:                          # Domain (e.g., aerospace, cyber, marine)
  configuration:                   # Instantiable model (e.g., aerospace_general)
    metadata:                      # Name, version, min premium, markets
      name: str
      version: str
      min_premium: float
      markets: list[str]
      minimum_viable_input:        # IMPORTANT: Must include basis if MULTIPLIER used
        - entity_id
        - tiv                      # Or revenue, payroll, limit, etc.

    direct_queries:                # Boolean questions (Step 7)
      - id: str
        question: str
        query_condition:
          - return: bool           # Trigger on true or false
            action: FLAG | MODIFIER | REFER
            override: int|null     # For REFER - tier override
            applied: float|null    # For MODIFIER - multiplicative
            note: str              # Required for FLAG

    signal_registry:               # All signals defined once
      - id: str
        inference_utility_function: str
        proxy_tier: DIRECT_OBSERVABLE | INFERRED_PROXY | COHORT_INFERENCE
        three_layer_assessment:
          group_id: str            # Links to groups.three_layer_assessment

          # Each dimension can have banded score_conditions
          risk:
            weight: float
            correlation_direction: positive | negative
            score_conditions:      # BANDED - multiple thresholds (OPTIONAL)
              - threshold: int     # e.g., 20
                comparison: "<="   # >=, <=, ==, >, <
                action: MODIFIER
                applied: 0.85      # 15% credit
                note: str
              - threshold: int     # e.g., 80
                comparison: ">="
                action: FLAG
                note: str          # Required for FLAG
              - threshold: int     # e.g., 95
                comparison: ">="
                action: REFER
                override: int|null # Optional tier override

          loss:
            severity:
              weight: float
              correlation_direction: str
              score_conditions: [...]  # Same banded structure
            frequency:
              weight: float
              correlation_direction: str
              score_conditions: [...]

          exposure:
            size:
              weight: float
              correlation_direction: str
              score_conditions: [...]
            complexity:
              weight: float
              correlation_direction: str
              score_conditions: [...]

    groups:
      categories:                  # Categorical modifier groups
        - id: str
          label: str
          impact: MODIFIER | PREMIUM_BASE

      three_layer_assessment:      # Score-contributing groups
        - id: str
          label: str
          risk:
            weight: float          # Sum to 1.0 across all groups
            score_conditions: [...] # Group-level banded conditions
          loss:
            weight: float
            score_conditions: [...]
          exposure:
            weight: float
            score_conditions: [...]

    risk_tier_bands:               # Score → tier → premium
      bands:
        - id: int                  # Tier 1 = best
          label: str
          interpretation:
            bands:
              min: int
              max: int
            action: APPROVE | REFER | DECLINE
            application:
              # METHOD 1: Fixed base premium
              method: PREMIUM_BASE
              value: int
              # METHOD 2: Rate × basis (alternative)
              # method: MULTIPLIER
              # applied: float     # Rate (e.g., 0.0035)
              # basis: str         # Field from minimum_viable_input

    loss_tier_bands:               # Loss score → modifiers
      bands:
        - id: int
          label: str
          interpretation:
            bands: {min: int, max: int}
            application:
              frequency_modifier: float
              severity_modifier: float
      constraints:
        floor: float               # e.g., 0.75
        cap: float                 # e.g., 1.50

    exposure:                      # Exposure score → modifiers
      size:
        weight: float
        bands:
          - id: int
            label: str
            interpretation:
              bands: {min: int, max: int}
              application:
                method: MODIFIER | MULTIPLIER
                applied: float
                basis: str|null    # For MULTIPLIER
      complexity:
        weight: float
        bands: [...]
```

### score_conditions Evaluation Rules

1. **Applies to:** signal_registry signals and groups ONLY (NOT tier bands)
2. **MODIFIER:** ALL matching conditions apply multiplicatively
3. **FLAG:** ALL matching conditions captured
4. **REFER:** FIRST matching triggers referral
5. **Required fields:**
   - MODIFIER: `applied` (float)
   - FLAG: `note` (string)
   - REFER: `override` optional (tier)

-----

## Critical Rules

### Core Framework Rules

1. **YAML is truth**: Never hardcode weights, thresholds, modifiers, or tier definitions
1. **Extractors are stubs**: Randomized but structurally realistic, with TTL caching
1. **Aggregators are production**: Must handle real data when extractors upgraded
1. **Categorizers are reusable**: Use the 12 parameterized types
1. **Inference functions are glue**: One per YAML `inference_utility_function`
1. **Model layer is coverage-agnostic**: Same code handles all seven coverages
1. **Consistent structure**: All coverages follow identical file organization
1. **Scores are 0-100**: Individual signals
1. **Composite is 0-1000**: Weighted sum × 10
1. **Confidence matters**: Track data availability throughout pipeline
1. **TTL varies by source**: Set appropriate `DEFAULT_TTL_SECONDS` per extractor
1. **Auditability**: Every price must trace back to signals → scores → tier → premium

### Workflow Rules

1. **score_conditions can use MODIFIER action**: Applies multiplicatively to final premium (Step 6)
1. **Direct queries can use MODIFIER action**: Via modifiers applied after base premium (Step 7)
1. **All matching MODIFIER conditions stack**: Multiplicatively combined
1. **Maximum tier override wins**: When multiple overrides, apply worst tier (Step 8)
1. **Every interaction is versioned**: Full audit trail via model versions (Step 2)
1. **MULTIPLIER method requires basis**: basis field must be in minimum_viable_input

### Three-Layer Assessment Rules

1. **Signals are shared infrastructure**: Same signal outputs feed all three assessment layers
1. **Three layers run in parallel**: Risk, Exposure, Loss - not in sequence (Steps 5a/5b/5c)
1. **Different weights per layer**: Same signals, layer-specific weighting schemes
1. **All layers captured before pricing**: Steps 9a/9b/9c must complete before Step 10
1. **Pricing uses all three outputs**: Risk Tier × Exposure Band × Loss Modifier → Premium

### Loss Correlation Layer Rules (Phase 16)

1. **Loss propensity has caps/floors**: Pricing impact bounded to prevent extreme adjustments
1. **Cohorts are signal-derived**: Not industry codes - behavioral patterns define peer groups
1. **Correlation direction matters**: Negative correlations inverted before scoring
1. **Confidence gates pricing**: Low confidence prevents automatic pricing adjustments
1. **Deterioration triggers action**: Trend monitoring is continuous, not just at renewal

### Exposure Shadow Layer Rules (Phase 17)

1. **Proxy tier determines confidence**: Direct observable > inferred > cohort > unknown
1. **Output ranges, not points**: Acknowledge uncertainty with bounded estimates
1. **High exposure + low confidence = referral**: Prevent auto-pricing uncertain large risks
1. **Complexity multiplies exposure**: More complex structures require higher pricing adjustment

-----

## Outstanding Work

This section consolidates all pending, optional, and planned work items. Completed items are tracked in their respective phase documents.

### Mandatory Pending Items

| Item | Phase | Priority | Notes |
|-|-|-|-|
| ~~Restructure: Extract signals to root level~~ | 18 | ~~Critical~~ ✅ | **COMPLETE** - See `development/project/phase_18.md` |
| ~~Config architecture unification~~ | 20 | ~~Critical~~ ✅ | **COMPLETE** - Unified signal definitions for risk/loss/exposure |
| Complete DSI Demo Production Build | 19 | High | In Progress - partitioned development approach |
| Implement Loss Correlation Runtime | 21 | High | Config ready (Phase 20). Implement scorer, monitoring, integration |
| Implement Exposure Shadow Runtime | 22 | High | Config ready (Phase 20). Implement magnitude, complexity calculators |
| Implement Organisational Graph Runtime | 23 | Medium | Schema ready (Phase 20). Implement node/edge creation, derivatives |
| Tag v1.0.0 release | 14 | Medium | Awaiting Phase 19 demo completion |
| Add unit tests for critical modules | - | Medium | Test coverage at ~12.6% |
| Implement paid extractors (Shodan, VirusTotal, D&B) | 15 | Low | See `development/extractor_implementation_plan.md` |
| Fix remaining config typos (inference_utility_function) | - | Low | 23 function name typos |

### Architecture & Configuration Status

#### Phase 18 (Architecture Restructuring) - COMPLETE ✅

Signals are now a **shared infrastructure** at repository root:
- ✅ Extracted `signals/` to repository root
- ✅ Created `layers/` directory for assessment layer implementations
- ✅ Updated all imports and references

#### Phase 20 (Configuration Architecture) - COMPLETE ✅

Configuration now supports unified signal architecture:
- ✅ Signals defined once with `risk:`, `loss:`, `exposure:` subsections
- ✅ 27 new exposure signals with inference functions
- ✅ Banding-based pricing integration (loss and exposure consistent)
- ✅ Organisational Graph schema created (`schemas/organisational_graph.yaml`)
- ✅ Configuration Architecture documentation (`docs/Configuration Architecture.md`)
- ✅ Analysis layer separation (empirical parameters external to config)

**Key Files**:
- `coverages/cyber/config.yaml` - Unified signal architecture (renamed from config_rework_v2.yaml)
- `coverages/master_config_layout.yaml` - Master configuration template (VERSION 2.0)
- `schemas/organisational_graph.yaml` - Graph schema for World Model
- `docs/Configuration Architecture.md` - Documentation
- `development/project/dsi_restructure_plan.md` - Comprehensive restructure plan

### Implementation Roadmap (Phases 21-23)

```
Phase 20 (Config) ──► Phase 21 (Loss Runtime) ──► Phase 23 (Graph Runtime)
        │                                                    ▲
        └──────────► Phase 22 (Exposure Runtime) ────────────┘
```

| Phase | Objective | Prerequisites | Key Components |
|-|-|-|-|
| 21 | Loss Correlation Runtime | Phase 20 config | LossCorrelationScorer, LossMonitoringEngine, pricing integration |
| 22 | Exposure Shadow Runtime | Phase 20 config | ExposureMagnitudeCalculator, ComplexityCalculator, pricing integration |
| 23 | Organisational Graph Runtime | Phase 20 schema, 21, 22 | NodeFactory, EdgeInferencer, DerivativeCalculator, AuthorityPropagation |

**Phases 21 and 22 are now unblocked** by Phase 20 configuration work.

### Optional Enhancements

| Item | Phase | Description |
|-|-|-|
| ML module | 8 | Gradient boosting, anomaly detection, clustering |
| Performance dashboards | 8 | Visualization of model performance |
| Natural language search | 9 | Query portfolio with natural language |
| Visualization components | 9 | Interactive charts and dashboards |
| SignalLibrary | 13 | Reusable signal component library |
| CodeGenerator | 13 | Automated code generation for new signals |
| LLM prompts | 13 | Prompt templates for coverage building |
| Builder CLI | 13 | Command-line interface for builder |

### Signal Enhancement Recommendations

Based on retrospective analysis of major insurance losses (2019-2024). See `development/` for full analysis.

| Priority | Area | Description | Reference |
|-|-|-|-|
| 1 | Marine | Port state control deficiencies, pre-departure systems status | Baltimore/Dali analysis |
| 2 | Aerospace | Certification transparency, supply chain quality | Boeing 737 MAX analysis |
| 3 | Cross-Coverage | Real-time regulatory monitoring | SVB, BP Deepwater analysis |

### Reference Documents

| Document | Location | Purpose |
|-|-|-|
| Historical Loss Analysis | `development/historical_loss_analysis.md` | Case-by-case DSI signal mapping |
| Signal Mapping | `development/signal_mapping_to_historical_loss.md` | Technical signal path specifications |
| Retrospective Case Studies | `development/retrospective_case_study_detail.md` | Comprehensive loss analysis |
| Client Assessment Samples | `development/client_assessment_samples.md` | Real-world assessment examples |

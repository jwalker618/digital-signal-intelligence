-----

## name: dsi-framework

description: Digital Signal Intelligence (DSI) insurance pricing framework. Use this skill when working on any aspect of DSI project code.

# DSI Framework Development Guide

## Development Workflow

When starting any DSI work:

1. **Read this SKILL.md first**
1. **Follow the link to the Development documentation indicated in Implementation Status. If this cannot be found, it must be  created first**
1. **Review development/project/ for the relevant items**: Contains phase development plans
1. **Reference YAML config** for the coverage you're working on
1. **Follow the standard patterns** - don't invent new structures
1. **Follow the 14-step workflow** - don't skip or reorder steps
1. **Never hardcode** - if it's in YAML, read it from YAML
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

**Current State**: Core framework complete and validated. 50 free production extractors with global coverage. Routing module complete with jurisdiction-aware routing, extractor tiers, and multi-source aggregation. 13 routed inference functions integrated. Routing cache with TTL support. Loss Signal Correlation Layer specification complete (Phase 16). Exposure Shadow Layer specification complete (Phase 17). Comprehensive repository review completed January 2026.

**Validation Status** (January 2026):
- ✅ All core Python imports validated and working
- ✅ Signal analytics module fixed (import order corrected)
- ✅ API schemas complete (country_hint field added)
- ✅ Configuration YAML syntax errors fixed
- ✅ Documentation links validated and corrected
- ✅ 32 API endpoints documented and functional
- ✅ All 7 demo applications validated
- ⚠️ Test coverage at ~12.6% (critical modules need unit tests)
- ⚠️ 23 function name typos in configs (runtime warnings, not failures)

**Next Steps**: See [Outstanding Work](#outstanding-work) section for consolidated pending, planned, and optional items.

---

## What is DSI?

Digital Signal Intelligence (DSI) is insurance underwriting based on **observable digital signals** rather than self-reported documentation. Core insight: who trusts/partners/certifies an entity reveals risk quality more reliably than what they claim about themselves.

All Foundational Principles, which must be adhered to, can be found here:  `docs/overview/Foundational Principles.md`

The detailed whitepaper can be found here: `docs/overview/Whitepaper - Digital Signal Intelligence.docx`

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

The complete model execution follows this extended workflow (Step 0 discovery + Steps 1-13 pricing, with parallel assessment at Steps 5 and 9):

```
Steps 1-4: Setup & Signal Extraction
     │
     ▼
Steps 5a/5b/5c: THREE-LAYER PARALLEL SCORING ←── Same signals, different weights
     │
     ▼
Steps 6-8: Conditions & Overrides
     │
     ▼
Steps 9a/9b/9c: CAPTURE ALL THREE LAYER OUTPUTS
     │
     ▼
Steps 10-13: Pricing & Decision (uses all three layers)
```

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

## File Structure (Current)

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
│   │   ├── Foundational Principles.md    # Core DSI principles
│   │   └── White Paper - Digital Signal Intelligence.docx  # Detailed whitepaper
│   ├── agent_interaction/
│   │   └── dsi_specification.md     # Agent integration spec
│   └── case_studies/                # Loss case studies
│
├── development/                     # Development documentation
│   ├── project/                     # Phase documents
│   │   ├── phase_1.md ... phase_17.md   # Implementation phases
│   │   └── original.md              # Master SKILL document
│   ├── historical_loss_analysis.md  # Loss analysis
│   ├── signal_mapping_to_historical_loss.md
│   ├── retrospective_case_study_detail.md
│   ├── retrospective_case_study_executive_summary.md
│   ├── retrospective_methodology.md
│   ├── client_assessment_samples.md
│   └── extractor_implementation_plan.md
│
├── technical_pricing/               # Core framework
│   ├── __init__.py
│   ├── coverages/                   # Coverage configurations
│   │   ├── aerospace/config.yaml    ✅
│   │   ├── cyber/config.yaml        ✅
│   │   ├── do/config.yaml           ✅
│   │   ├── energy/config.yaml       ✅
│   │   ├── fi/config.yaml           ✅
│   │   ├── marine/config.yaml       ✅
│   │   └── pi/config.yaml           ✅
│   │
│   ├── signals/                     # Signal architecture
│   │   ├── __init__.py
│   │   ├── base.py                  ✅ Base classes
│   │   ├── types.py                 ✅ Data structures
│   │   ├── extractors/
│   │   │   ├── base.py              ✅ StubExtractor + utilities
│   │   │   ├── stubs/               ✅ Coverage-specific stub extractors
│   │   │   │   ├── common.py        ✅ Cross-coverage extractors
│   │   │   │   ├── aerospace/       ✅ cyber/ do/ energy/ fi/ marine/ pi/
│   │   │   └── production/          ✅ PHASE 15 - 50 free extractors
│   │   │       ├── base.py          ✅ ProductionExtractor base
│   │   │       ├── factory.py       ✅ Stub/production switching
│   │   │       ├── config.py        ✅ API key configuration
│   │   │       ├── dns/             ✅ http/ network/ sec/ regulatory/
│   │   │       ├── sanctions/       ✅ security/ industry/ corporate/
│   │   │       ├── environment/     ✅ maritime/
│   │   ├── aggregators/
│   │   │   ├── base.py              ✅ ProductionAggregator
│   │   │   ├── routing_bridges.py   ✅ PHASE 15.7 (6 bridge classes)
│   │   │   └── implementations/     ✅ Coverage-specific aggregators
│   │   ├── categorisers/            # Note: British spelling
│   │   │   ├── base.py              ✅ ProductionCategorizer
│   │   │   └── types/               ✅ threshold_bucket, boolean_score, etc.
│   │   ├── inference/
│   │   │   ├── registry.py          ✅ Function registration
│   │   │   └── functions/           ✅ Coverage-specific + routed/
│   │   ├── routing/                 ✅ PHASE 15
│   │   │   ├── router.py            ✅ JurisdictionRouter
│   │   │   ├── schemas.py           ✅ Unified output schemas
│   │   │   ├── multi_source.py      ✅ MultiSourceAggregator + RoutingCache
│   │   │   ├── sanctions_aggregator.py  ✅
│   │   │   └── corporate_aggregator.py  ✅
│   │   └── cross_walk/
│   │       └── by_coverage.json     ✅ Coverage crosswalk mappings
│   │
│   ├── discovery/                   ✅ PHASE 6
│   │   └── website_discovery.py     ✅ Discovery engine
│   │
│   ├── model/                       ✅ PHASE 4
│   │   ├── types.py                 ✅ All dataclasses
│   │   ├── config_manager.py        ✅ Config hashing/storage
│   │   ├── model_data.py            ✅ Model data file management
│   │   ├── scorer.py                ✅ Steps 4-6
│   │   ├── query_evaluator.py       ✅ Step 7
│   │   ├── pricer.py                ✅ Steps 8-12
│   │   ├── workflow.py              ✅ Full orchestration + Step 0
│   │   └── modifiers/               ✅ PHASE 7
│   │       ├── base.py              ✅ loss_history.py exposure.py external_rating.py
│   │
│   ├── analytics/                   ✅ PHASE 8-9
│   │   ├── types.py                 ✅ portfolio_types.py
│   │   ├── performance.py           ✅ cohorts.py tuning.py
│   │   ├── portfolio.py             ✅ workflow_analytics.py signal_analytics.py
│   │
│   ├── orchestration/               ✅ PHASE 10
│   │   ├── types.py                 ✅ multi_coverage.py
│   │   ├── locale_detection.py      ✅ aggregator.py
│   │
│   ├── api/                         ✅ PHASE 11
│   │   ├── main.py                  ✅ FastAPI application
│   │   ├── types.py                 ✅ API types
│   │   ├── routes/                  ✅ analytics.py submissions.py referrals.py quotes.py
│   │   ├── auth/                    ✅ jwt_auth.py api_key.py
│   │   └── middleware/              ✅ Rate limiting, logging
│   │
│   ├── integrations/                ✅ PHASE 12
│   │   ├── types.py                 ✅ email/ documents/ webhooks/
│   │
│   ├── builder/                     ✅ PHASE 13
│   │   ├── coverage_builder.py      ✅ validator.py
│   │   ├── signal_library.py        ✅ types.py
│   │
│   ├── db/                          ✅ Database layer
│   │   ├── models.py                ✅ repositories.py config.py
│   │
│   └── tests/                       ✅ Unit and integration tests
│       ├── conftest.py              ✅ unit/ integration/
│
├── exposure/                        # Exposure Shadow Layer (PHASE 17)
│   └── shadow_layer/
│       └── development/             ✅ Specification documents
│           ├── README.md
│           ├── plan.md              ✅ Full implementation plan
│           ├── executive_briefing.md ✅ Executive summary
│           └── actuarial_validation.md ✅ Validation requirements
│
├── loss/                            # Loss Correlation Layer (PHASE 16)
│   └── correlation_layer/
│       └── development/             ✅ Specification documents
│           ├── README.md
│           ├── plan.md              ✅ Full implementation plan
│           └── specification.txt    ✅ Technical specification
│
├── demo/                            ✅ Live demos
│   ├── server.py                    ✅ FastAPI demo server
│   ├── examples/                    ✅ PHASE 14 + 15
│   │   ├── run_aerospace.py ... run_pi.py  ✅ Coverage examples
│   │   ├── run_multi.py             ✅ Multi-coverage example
│   │   └── run_hybrid.py            ✅ PHASE 15.7 - Routing demo
│   └── html_dashboards/             ✅ Interactive HTML demos
│
├── deploy/                          ✅ Deployment configs
│   └── kubernetes/                  ✅ K8s manifests
│
└── tests/                           ✅ Top-level test suite
    ├── unit/                        ✅ test_traditional_modifiers.py etc.
    ├── integration/                 ✅ test_integrations.py
    └── api/                         ✅ test_api.py
```

Legend: ✅ Complete | 🔲 Not Started

-----

## Planned Architecture Evolution

**STATUS: CRITICAL PRIORITY** - This restructuring is the highest priority item. See [Outstanding Work](#outstanding-work).

As signals are now used across all three assessment layers (Risk, Exposure, Loss), the architecture must be restructured to extract signals to the root level:

```
# Target State (Phase 18)
digital-signal-intelligence/
├── signals/                         # Shared signal infrastructure (extracted from technical_pricing/)
│   ├── __init__.py
│   ├── base.py
│   ├── types.py
│   ├── extractors/
│   │   ├── base.py
│   │   ├── stubs/
│   │   └── production/
│   ├── aggregators/
│   ├── categorisers/
│   ├── inference/
│   ├── routing/
│   └── cross_walk/
│
├── layers/                          # Assessment layer implementations
│   ├── risk/                        # Current technical_pricing/model (renamed)
│   │   ├── scorer.py
│   │   ├── pricer.py
│   │   ├── workflow.py
│   │   └── modifiers/
│   ├── exposure/                    # Phase 17 implementation
│   │   ├── scorer.py
│   │   ├── complexity.py
│   │   └── band_mapper.py
│   └── loss/                        # Phase 16 implementation
│       ├── scorer.py
│       ├── matrix.py
│       └── monitoring.py
│
├── coverages/                       # Coverage configurations (extracted from technical_pricing/)
│   ├── aerospace/config.yaml
│   ├── cyber/config.yaml
│   └── ...
│
├── api/                             # API layer (from technical_pricing/api/)
├── analytics/                       # Analytics (from technical_pricing/analytics/)
├── orchestration/                   # Orchestration (from technical_pricing/orchestration/)
├── discovery/                       # Discovery (from technical_pricing/discovery/)
├── integrations/                    # Integrations (from technical_pricing/integrations/)
├── builder/                         # Builder (from technical_pricing/builder/)
├── db/                              # Database (from technical_pricing/db/)
│
├── development/                     # Development documentation (unchanged)
├── demo/                            # Demos (unchanged)
├── deploy/                          # Deployment (unchanged)
├── docs/                            # Documentation (unchanged)
└── tests/                           # Tests (merged from technical_pricing/tests/ and root tests/)
```

**Restructuring must be completed before implementing Phases 16 and 17** to avoid technical debt from building new layers in the wrong location.

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

```yaml
coverage:                          # Domain (e.g., aerospace, cyber, marine)
  configuration:                   # Instantiable model (e.g., aerospace_general)
    metadata:                      # Name, version, min premium, markets
      name: str
      version: str
      min_premium: float
      markets: list[str]
      
    required_inputs:               # Minimum viable inputs (Step 3)
      - entity_id
      - tiv                        # Or revenue, payroll, etc.
      
    direct_queries:                # Boolean questions (Step 7)
      - id: str
        question: str
        impacts:
          - type: tier_override | referral | note | modifier
            value: int | str | float
            
    categorical_groups:            # Groups that impact pricing
      - group_name
      
    categorical_features:          # Categories within groups + modifiers
      group_name:
        category_a: 1.0            # Base
        category_b: 1.15           # 15% loading
        
    signal_groups:                 # Groups with weights (sum to 1.0)
      - name: str
        weight: float
        conditions:                # Group-level conditions (Step 6)
          - condition_type: str
            condition_value: any
            action: tier_override | referral | note
            action_value: any
            
    signal_features:               # Signals within groups (sum to 1.0 per group)
      group_name:
        - name: str
          weight: float
          inference_function: str
          categorizer_type: str
          categorizer_params: dict
          conditions:              # Signal-level conditions (Step 6)
            - condition_type: str
              condition_value: any
              action: tier_override | referral | note
              action_value: any
              
    tier_thresholds:               # Score → tier → premium basis
      - tier: 1
        min_score: 800
        max_score: 1000
        base_premium: 10000        # Option A: pure
        # OR
        rate: 0.005                # Option B: metric-based
        rate_basis: tiv
        decision: approve          # approve | refer | decline
        
    limit_bands:                   # ILF table (Step 12)
      - limit: 1000000
        ilf: 1.0
      - limit: 2000000
        ilf: 1.5
        
    deductible_credits:            # Deductible → credit factor
      10000: 1.0
      25000: 0.95
      50000: 0.90
      
    test_profiles:                 # Validation scenarios
      - name: str
        inputs: dict
        expected: dict
```

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

1. **Conditions cannot modify premium**: Only tier override, referral, or note (Step 6)
1. **Direct queries can modify premium**: Via modifiers applied after base premium (Step 7)
1. **Maximum tier override wins**: When multiple overrides, apply worst tier (Step 8)
1. **Every interaction is versioned**: Full audit trail via model versions (Step 2)

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
|------|-------|----------|-------|
| **Restructure: Extract signals to root level** | 18 | **Critical** | Signals now feed all three layers. See [Planned Architecture Evolution](#planned-architecture-evolution) |
| Implement Phase 16 (Loss Correlation Layer) | 16 | High | Specification complete. See `loss/correlation_layer/development/` |
| Implement Phase 17 (Exposure Shadow Layer) | 17 | High | Specification complete. See `exposure/shadow_layer/development/` |
| Tag v1.0.0 release | 14 | High | Awaiting final validation |
| Add unit tests for critical modules | - | High | Test coverage at ~12.6% |
| Implement paid extractors (Shodan, VirusTotal, D&B) | 15 | Medium | See `development/extractor_implementation_plan.md` |
| Fix remaining config typos (inference_utility_function) | - | Medium | 23 function name typos |

### Restructuring Rationale

The current architecture has signals nested within `technical_pricing/signals/`. However, the three-layer assessment model means signals are now a **shared infrastructure** feeding:

1. **Risk Layer** - existing risk scoring (Steps 5a, 9a)
2. **Exposure Shadow Layer** - Phase 17 (Steps 5b, 9b)
3. **Loss Correlation Layer** - Phase 16 (Steps 5c, 9c)

Implementing Phases 16 and 17 before restructuring will create technical debt. The restructuring should:
- Extract `signals/` to repository root
- Create `layers/` directory for assessment layer implementations
- Update all imports and references
- Ensure all tests pass after migration

### Optional Enhancements

| Item | Phase | Description |
|------|-------|-------------|
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
|----------|------|-------------|-----------|
| 1 | Marine | Port state control deficiencies, pre-departure systems status | Baltimore/Dali analysis |
| 2 | Aerospace | Certification transparency, supply chain quality | Boeing 737 MAX analysis |
| 3 | Cross-Coverage | Real-time regulatory monitoring | SVB, BP Deepwater analysis |

### Reference Documents

| Document | Location | Purpose |
|----------|----------|---------|
| Historical Loss Analysis | `development/historical_loss_analysis.md` | Case-by-case DSI signal mapping |
| Signal Mapping | `development/signal_mapping_to_historical_loss.md` | Technical signal path specifications |
| Retrospective Case Studies | `development/retrospective_case_study_detail.md` | Comprehensive loss analysis |
| Client Assessment Samples | `development/client_assessment_samples.md` | Real-world assessment examples |

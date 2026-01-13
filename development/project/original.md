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

**Current State**: Core framework complete and validated. 50 free production extractors with global coverage. Routing module complete with jurisdiction-aware routing, extractor tiers, and multi-source aggregation. 13 routed inference functions integrated. Routing cache with TTL support. Loss Signal Correlation Layer specification complete (Phase 16). Comprehensive repository review completed January 2026.

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

**Next Steps for Production**:
1. **HIGH PRIORITY**: Add unit tests for extractors, aggregators, and inference functions
2. Implement paid extractors (Shodan, VirusTotal, D&B) - see Phase 15.6
3. Fix remaining config typos (inference_utility_function spelling errors)
4. Deploy production monitoring and alerting
5. **Phase 16**: Implement Loss Signal Correlation Layer for loss propensity scoring
6. Tag v1.0.0 release

---

## What is DSI?

Digital Signal Intelligence (DSI) is insurance underwriting based on **observable digital signals** rather than self-reported documentation. Core insight: who trusts/partners/certifies an entity reveals risk quality more reliably than what they claim about themselves.

All Foundational Principles, which must be adhered to, can be found here:  `docs/overview/Foundational Principles.md`

The detailed whitepaper can be found here: `docs/overview/Whitepaper - Digital Signal Intelligence.docx`

-----

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     SUBMISSION INPUT                            │
│     Company name, domain hint, coverage, TIV, limits            │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                   DISCOVERY MODULE (Step 0)                     │
│                                                                 │
│  ┌──────────┐    ┌──────────┐    ┌───────────┐                  │
│  │SEARCH    │ →  │VALIDATE  │ →  │IDENTIFY   │                  │
│  │          │    │          │    │           │                  │
│  │Find      │    │Corporate │    │Primary    │                  │
│  │candidates│    │website   │    │website    │                  │
│  └──────────┘    └──────────┘    └───────────┘                  │
│                                                                 │
│  Output: Discovered website URL + confidence + identity         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                        YAML CONFIG                              │
│     Single source of truth for coverage model definition        │
│   (weights, modifiers, tiers, direct queries, conditions)       │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    SIGNAL ARCHITECTURE                          │
│                                                                 │
│  ┌──────────┐    ┌──────────┐    ┌───────────┐    ┌──────────┐  │
│  │EXTRACTOR │ →  │AGGREGATOR│ →  │CATEGORIZER│ →  │INFERENCE │  │
│  │          │    │          │    │           │    │          │  │
│  │Raw data  │    │Structure/│    │Score or   │    │Orchestrat│  │
│  │from APIs │    │normalize │    │category   │    │pipeline  │  │
│  └──────────┘    └──────────┘    └───────────┘    └──────────┘  │
│                                                                 │
│  Uses discovered website for data extraction                    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      MODEL LAYER                                │
│                                                                 │
│  ┌──────────┐    ┌──────────────────────────────────────────┐   │
│  │CONFIG    │    │         PARALLEL SCORING                 │   │
│  │MANAGER   │    │  ┌────────────┐    ┌─────────────────┐   │   │
│  │Hash/store│ →  │  │RISK SCORER │    │LOSS CORRELATION │   │   │
│  │validate  │    │  │            │    │SCORER (Phase 16)│   │   │
│  └──────────┘    │  │Composite   │    │Propensity +     │   │   │
│                  │  │+ conditions│    │Cohort + Monitor │   │   │
│                  │  └────────────┘    └─────────────────┘   │   │
│                  └──────────────────────────────────────────┘   │
│                              │                                  │
│                              ▼                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  PRICER → WORKFLOW ENGINE → Decision (Approve/Refer/Decl)│   │
│  │  Risk Tier × Loss Propensity × Exposure → Final Premium  │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      MODEL OUTPUT                               │
│  Score → Conditions → Tier → Base Premium → Loss Modifier       │
│                    → Limits → Decision (Approve/Refer/Decline)  │
│  + Loss Propensity Score + Cohort Assignment + Monitoring       │
└─────────────────────────────────────────────────────────────────┘
```

-----

## Model Process Workflow

The complete model execution follows this 14-step workflow (Step 0 discovery + Steps 1-13 pricing):

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

### Step 5: Pure Composite Score Calculation

- Calculate weighted composite score (0-1000)
- No conditions applied yet - pure signal-based score

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

### Step 9: Final Tier Capture

- Final tier (after all overrides) captured in model data file
- This is the tier used for premium calculation

### Step 10: Base Premium Generation

As defined in YAML `tier_thresholds`:

**Option A - Pure Premium:**

```yaml
tier_thresholds:
  - tier: 1
    base_premium: 10000
```

**Option B - Metric-Based:**

```yaml
tier_thresholds:
  - tier: 1
    rate: 0.005  # TIV * 0.5%
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

-----

## File Structure (Complete)

```
technical_pricing/
├── __init__.py
├── coverages/
│   ├── aerospace/config.yaml        ✅
│   ├── cyber/config.yaml            ✅
│   ├── do/config.yaml               ✅
│   ├── energy/config.yaml           ✅
│   ├── fi/config.yaml               ✅
│   ├── marine/config.yaml           ✅
│   └── pi/config.yaml               ✅
├── signals/
│   ├── __init__.py
│   ├── base.py                      ✅ Base classes
│   ├── types.py                     ✅ Data structures
│   ├── extractors/
│   │   ├── __init__.py
│   │   ├── base.py                  ✅ StubExtractor + utilities
│   │   ├── stubs/
│   │   │   ├── __init__.py
│   │   │   ├── common.py            ✅ Cross-coverage extractors
│   │   │   ├── aerospace/           ✅ 21 extractors
│   │   │   ├── cyber/               ✅ 35 extractors
│   │   │   ├── do/                  ✅ 46 extractors
│   │   │   ├── energy/              ✅ 44 extractors
│   │   │   ├── fi/                  ✅ ~40 extractors
│   │   │   ├── marine/              ✅ ~38 extractors
│   │   │   └── pi/                  ✅ ~35 extractors
│   │   └── production/              ✅ PHASE 15
│   │       ├── __init__.py          ✅ Factory + registration
│   │       ├── base.py              ✅ ProductionExtractor base
│   │       ├── factory.py           ✅ Stub/production switching
│   │       ├── config.py            ✅ API key configuration
│   │       ├── dns/                 ✅ 4 extractors (SPF, DKIM, DNSSEC, WHOIS)
│   │       ├── http/                ✅ 2 extractors (headers, security.txt)
│   │       ├── network/             ✅ 4 extractors (cloud, CDN, WAF, TLS)
│   │       ├── sec/                 ✅ 5 extractors (EDGAR, SEDAR+)
│   │       ├── regulatory/          ✅ 9 extractors (OFAC, EPA, FCA, etc.)
│   │       ├── sanctions/           ✅ 10 extractors (OpenSanctions, MDBs)
│   │       ├── security/            ✅ 2 extractors (NVD, HHS)
│   │       ├── industry/            ✅ 2 extractors (PCAOB, aviation)
│   │       ├── corporate/           ✅ 5 extractors (CH, OpenCorp, GLEIF)
│   │       ├── environment/         ✅ 2 extractors (EEA, NPRI)
│   │       └── maritime/            ✅ 2 extractors (IMO, IOSA)
│   ├── aggregators/
│   │   ├── __init__.py
│   │   ├── base.py                  ✅ ProductionAggregator
│   │   ├── routing_bridges.py       ✅ PHASE 15.7 (6 bridge classes)
│   │   └── implementations/
│   │       ├── __init__.py
│   │       ├── common.py            ✅ Cross-coverage
│   │       ├── aerospace/           ✅ 26 aggregators
│   │       ├── cyber/               ✅ 35 aggregators
│   │       ├── do/                  ✅ 46 aggregators
│   │       ├── energy/              ✅ 44 aggregators
│   │       ├── fi/                  ✅ ~40 aggregators
│   │       ├── marine/              ✅ ~38 aggregators
│   │       └── pi/                  ✅ ~35 aggregators
│   ├── categorizers/
│   │   ├── __init__.py
│   │   ├── base.py                  ✅ ProductionCategorizer
│   │   └── types/
│   │       ├── __init__.py
│   │       ├── threshold_bucket.py  ✅
│   │       ├── boolean_score.py     ✅
│   │       ├── weighted_composite.py ✅
│   │       └── category_mapper.py   ✅
│   ├── inference/
│   │   ├── __init__.py
│   │   ├── registry.py              ✅
│   │   └── functions/
│   │       ├── __init__.py
│   │       ├── registry.py          ✅ Function registration
│   │       ├── aerospace/           ✅ 41 functions
│   │       ├── cyber/               ✅ 38 functions
│   │       ├── do/                  ✅ 47 functions
│   │       ├── energy/              ✅ 46 functions
│   │       ├── fi/                  ✅ ~42 functions
│   │       ├── marine/              ✅ ~40 functions
│   │       ├── pi/                  ✅ ~38 functions
│   │       └── routed/              ✅ PHASE 15.7 (13 functions)
│   │           ├── __init__.py      ✅ register_all()
│   │           └── signals.py       ✅ Multi-source inference functions
│   └── routing/                     ✅ PHASE 15
│       ├── __init__.py              ✅ Package exports
│       ├── router.py                ✅ JurisdictionRouter + tier system
│       ├── schemas.py               ✅ Unified output schemas
│       ├── multi_source.py          ✅ MultiSourceAggregator + RoutingCache
│       ├── sanctions_aggregator.py  ✅ Sanctions multi-source
│       └── corporate_aggregator.py  ✅ Corporate multi-source
├── discovery/                       ✅ PHASE 6
│   ├── __init__.py                  ✅ Package exports
│   └── website_discovery.py         ✅ Discovery engine
├── model/                           ✅ PHASE 4
│   ├── __init__.py
│   ├── types.py                     ✅ All dataclasses
│   ├── config_manager.py            ✅ Config hashing/storage
│   ├── model_data.py                ✅ Model data file management
│   ├── scorer.py                    ✅ Steps 4-6
│   ├── query_evaluator.py           ✅ Step 7
│   ├── pricer.py                    ✅ Steps 8-12
│   ├── workflow.py                  ✅ Full orchestration + Step 0
│   ├── modifiers/                   ✅ PHASE 7
│   │   ├── base.py                  ✅ TraditionalModifier base
│   │   ├── loss_history.py          ✅ Experience rating
│   │   ├── exposure.py              ✅ Exposure adjustments
│   │   └── external_rating.py       ✅ Credit/financial ratings
│   └── loss_correlation/            🔲 PHASE 16 (Specification Complete)
│       ├── __init__.py              🔲 Package exports
│       ├── types.py                 🔲 LossPropensityResult, enums
│       ├── scorer.py                🔲 LossCorrelationScorer
│       ├── matrix.py                🔲 CorrelationMatrixManager
│       ├── monitoring.py            🔲 LossMonitoringEngine
│       └── integration.py           🔲 Pricing integration patterns
├── analytics/                       ✅ PHASE 8-9
│   ├── types.py                     ✅ Metrics types
│   ├── performance.py               ✅ Performance tracking
│   ├── cohorts.py                   ✅ Cohort analysis
│   ├── tuning.py                    ✅ Model tuning
│   ├── portfolio.py                 ✅ Portfolio management
│   ├── workflow_analytics.py        ✅ Workflow metrics
│   └── signal_analytics.py          ✅ Signal analysis
├── orchestration/                   ✅ PHASE 10
│   ├── types.py                     ✅ Orchestration types
│   ├── multi_coverage.py            ✅ Multi-coverage orchestrator
│   ├── locale_detection.py          ✅ Locale detection
│   └── aggregator.py                ✅ Result aggregation
├── api/                             ✅ PHASE 11
│   ├── main.py                      ✅ FastAPI application
│   ├── types.py                     ✅ API types
│   ├── routes/                      ✅ Endpoint modules
│   ├── auth/                        ✅ JWT + API key auth
│   └── middleware/                  ✅ Rate limiting, logging
├── integrations/                    ✅ PHASE 12
│   ├── types.py                     ✅ Integration types
│   ├── email/                       ✅ Email parsing
│   ├── documents/                   ✅ Document processing
│   └── webhooks/                    ✅ Webhook manager
├── builder/                         ✅ PHASE 13
│   ├── coverage_builder.py          ✅ Coverage builder
│   └── validator.py                 ✅ Config validation
├── db/                              ✅ Database layer
│   ├── models.py                    ✅ SQLAlchemy models
│   ├── repositories.py              ✅ Data access layer
│   └── session.py                   ✅ Session management
└── tests/                           ✅ PHASE 5
    ├── conftest.py                  ✅ Test configuration
    ├── unit/                        ✅ Unit tests
    ├── integration/                 ✅ Integration tests
    └── api/                         ✅ API tests

# Additional directories (at repo root):
examples/                            ✅ PHASE 14 + 15
├── run_aerospace.py                 ✅ Aerospace example
├── run_cyber.py                     ✅ Cyber example
├── run_do.py                        ✅ D&O example
├── run_energy.py                    ✅ Energy example
├── run_fi.py                        ✅ Financial Institutions example
├── run_marine.py                    ✅ Marine example
├── run_pi.py                        ✅ Professional Indemnity example
├── run_multi.py                     ✅ Multi-coverage example
└── run_hybrid.py                    ✅ PHASE 15.7 - Routing/hybrid demo

demo/                                ✅ Live demos
├── server.py                        ✅ FastAPI demo server
├── index.html                       ✅ Interactive dashboard
└── standalone/                      ✅ No-install HTML demos
    ├── index.html                   ✅ Demo gallery
    ├── signal-scoring.html          ✅ Signal weight explorer
    ├── tier-visualization.html      ✅ Score-to-tier mapping
    ├── pricing-calculator.html      ✅ Premium calculation
    ├── workflow-animation.html      ✅ 14-step workflow animation
    └── coverage-comparison.html     ✅ Coverage comparison

deploy/                              ✅ Deployment configs
├── docker-compose.yml               ✅ Docker Compose
├── kubernetes/                      ✅ K8s manifests
└── DEPLOYMENT.md                    ✅ Deployment guide

loss/                                ✅ Loss analysis specifications
└── correlation_layer/               ✅ PHASE 16 specifications
    ├── development_plan.md          ✅ Implementation plan
    └── loss_signal_correlation_layer_specification.txt  ✅ Full specification
```

Legend: ✅ Complete | 🔲 Not Started (Specification Complete)

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
1. **Conditions cannot modify premium**: Only tier override, referral, or note (Step 6)
1. **Direct queries can modify premium**: Via modifiers applied after base premium (Step 7)
1. **Maximum tier override wins**: When multiple overrides, apply worst tier (Step 8)
1. **Every interaction is versioned**: Full audit trail via model versions (Step 2)
1. **Loss correlation runs in parallel**: Same signals, different weights - runs alongside risk scoring (Phase 16)
1. **Loss propensity has caps/floors**: Pricing impact bounded to prevent extreme adjustments
1. **Cohorts are signal-derived**: Not industry codes - behavioral patterns define peer groups

-----

## Recommended Signal Enhancements

Based on retrospective analysis of major insurance losses (2019-2024), the following signal enhancements are recommended as part of Phase 16 implementation. See `/development_docs/` for full analysis.

### Priority 1: Marine Operational Readiness Signals

From Baltimore/Dali analysis - traditional DSI signals scored the vessel as standard risk, but operational issues were observable:

```yaml
# Proposed addition to marine/config.yaml
signal_features:
  operational_readiness:
    - name: port_state_control_deficiencies
      weight: 0.10
      data_source: equasis_api
      refresh_frequency: voyage
    - name: pre_departure_systems_status
      weight: 0.08
      data_source: port_authority_integration
      conditions:
        - condition_type: equals
          condition_value: false
          action: referral
          reason: "Pre-voyage systems check failed or incomplete"
```

### Priority 2: Aerospace Supply Chain Quality Signals

From Boeing 737 MAX analysis - supply chain and certification disclosure gaps:

```yaml
# Proposed addition to aerospace/config.yaml
signal_features:
  certification_quality:
    - name: certification_transparency
      weight: 0.10
      components:
        - pilot_training_changes_disclosed: 0.3
        - system_failure_modes_documented: 0.4
        - operational_limitations_published: 0.3
  supply_chain_quality:
    - name: component_supplier_audit_status
      data_source: oem_supplier_database
    - name: parts_provenance_verification
      data_source: blockchain_registry
```

### Priority 3: Cross-Coverage Real-Time Regulatory Monitoring

From SVB, BP Deepwater analysis - regulatory actions were observable signals:

```yaml
# Proposed cross-coverage enhancement
cross_coverage:
  regulatory_monitoring:
    - name: enforcement_action_feed
      data_source: regulatory_api_aggregator
      refresh_frequency: daily
      alert_threshold: any_new_action
```

### Signal Effectiveness Summary

From historical loss analysis across 11 major cases:

| Signal Type | Effectiveness | Cases Caught |
|-------------|---------------|--------------|
| Absence Signals | 95% | FTX, Shadow Fleet, SVB (CRO) |
| Regulatory Actions | 90% | SVB, BP Deepwater |
| Safety History | 85% | BP Deepwater, Costa Concordia |
| Governance Signals | 80% | FTX, SVB |
| Network Authority | 75% | FTX, Signature, Shadow Fleet |

### Reference Documents

| Document | Location | Purpose |
|----------|----------|---------|
| Historical Loss Analysis | `development/historical_loss_analysis.md` | Case-by-case DSI signal mapping |
| Signal Mapping | `development/signal_mapping_to_historical_loss.md` | Technical signal path specifications |
| Retrospective Case Studies | `docs/case_studies/retrospective_loss_case_studies.pdf` | Comprehensive loss analysis report |

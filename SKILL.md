-----

## name: dsi-framework

description: Digital Signal Intelligence (DSI) insurance pricing framework. Use this skill when working on DSI project code including extractors, aggregators, categorizers, inference functions, signal processing, YAML config interpretation, or any technical model development. Triggers on mentions of DSI, signal architecture, coverage configs, technical pricing, or insurance underwriting automation.

# DSI Framework Development Guide

## Implementation Status

| Phase | Name | Status | Key Deliverables |
|-------|------|--------|------------------|
| 1-3 | Foundation | ✅ Complete | Types, base classes, signal architecture |
| 4 | Config-Driven Model | ✅ Complete | YAML configs, ConfigManager, 7 coverages |
| 5 | Scoring Engine | ✅ Complete | Scorer, composite scoring, confidence |
| 6 | Discovery Integration | ✅ Complete | Website discovery, Step 0 integration |
| 7 | Traditional Modifiers | ✅ Complete | Loss history, exposure, external ratings |
| 8 | Analytics Engine | ✅ Complete | Performance, signal, portfolio analytics |
| 9 | Test Profiles | ✅ Complete | Validation scenarios, edge cases |
| 10 | Multi-Coverage | ✅ Complete | Orchestration, locale detection, aggregation |
| 11 | Production API | ✅ Complete | FastAPI, routes, auth modules |
| 12 | Integration Layer | ✅ Complete | Email, documents, webhooks |
| 13 | LLM Builder | ✅ Complete | Coverage builder, signal library |
| 14 | Examples | ✅ Complete | Working examples for all 7 coverages |
| 15 | Production Extractors | ✅ Complete | 50 free extractors, routing module, routed inference |

**Current State**: Core framework complete and validated. 50 free production extractors with global coverage. Routing module complete with jurisdiction-aware routing, extractor tiers, and multi-source aggregation. 13 routed inference functions integrated. Routing cache with TTL support. Comprehensive repository review completed January 2026.

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
5. Tag v1.0.0 release

---

## What is DSI?

Digital Signal Intelligence (DSI) is insurance underwriting based on **observable digital signals** rather than self-reported documentation. Core insight: who trusts/partners/certifies an entity reveals risk quality more reliably than what they claim about themselves.

Key principles:

- All primary signals externally observable (no cooperation required)
- Machine-readable, no subjective judgment
- Network authority (PageRank-style) over self-reporting
- Absence is signal (missing expected presence)
- Signal → Score → Tier → Price (auditable flow)

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
│  ┌──────────┐    ┌──────────┐    ┌───────────┐                 │
│  │SEARCH    │ →  │VALIDATE  │ →  │IDENTIFY   │                 │
│  │          │    │          │    │           │                 │
│  │Find      │    │Corporate │    │Primary    │                 │
│  │candidates│    │website   │    │website    │                 │
│  └──────────┘    └──────────┘    └───────────┘                 │
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
│  ┌──────────┐    ┌──────────┐    ┌───────────┐    ┌──────────┐ │
│  │EXTRACTOR │ →  │AGGREGATOR│ →  │CATEGORIZER│ →  │INFERENCE │ │
│  │          │    │          │    │           │    │          │ │
│  │Raw data  │    │Structure/│    │Score or   │    │Orchestrat│ │
│  │from APIs │    │normalize │    │category   │    │pipeline  │ │
│  └──────────┘    └──────────┘    └───────────┘    └──────────┘ │
│                                                                 │
│  Uses discovered website for data extraction                    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      MODEL LAYER                                │
│                                                                 │
│  ┌──────────┐    ┌──────────┐    ┌───────────┐    ┌──────────┐ │
│  │CONFIG    │ →  │SCORER    │ →  │PRICER     │ →  │WORKFLOW  │ │
│  │MANAGER   │    │          │    │           │    │ENGINE    │ │
│  │Hash/store│    │Composite │    │Premium    │    │Approve/  │ │
│  │validate  │    │+ conditions   │calc       │    │Refer/Decl│ │
│  └──────────┘    └──────────┘    └───────────┘    └──────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      MODEL OUTPUT                               │
│  Score → Conditions → Tier → Base Premium → Modifiers → Limits  │
│                    → Decision (Approve/Refer/Decline)           │
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

## Implementation Status

### ✅ Phase 1: Foundation (COMPLETE)

All base infrastructure is built and tested:

|Component                       |File                           |Status    |
|--------------------------------|-------------------------------|----------|
|Core Data Types                 |`signals/types.py`             |✅ Complete|
|Abstract Base Classes           |`signals/base.py`              |✅ Complete|
|StubExtractor (with TTL caching)|`signals/extractors/base.py`   |✅ Complete|
|ProductionAggregator            |`signals/aggregators/base.py`  |✅ Complete|
|ProductionCategorizer           |`signals/categorizers/base.py` |✅ Complete|
|Inference Registry              |`signals/inference/registry.py`|✅ Complete|

### ✅ Phase 2: Reusable Categorizer Types (COMPLETE)

12 parameterized categorizer types ready for use in `signals/categorizers/types/`.

### ✅ Phase 3: Coverage Implementation (COMPLETE - ALL 7 COVERAGES)

|Coverage               |Extractors|Aggregators|Inference|Status    |
|-----------------------|----------|-----------|---------|----------|
|Aerospace              |21        |26         |41       |✅ Complete|
|Cyber                  |35        |35         |38       |✅ Complete|
|D&O                    |46        |46         |47       |✅ Complete|
|Energy                 |44        |44         |46       |✅ Complete|
|Financial Institutions |~40       |~40        |~42      |✅ Complete|
|Marine                 |~38       |~38        |~40      |✅ Complete|
|Professional Indemnity |~35       |~35        |~38      |✅ Complete|
|Common (cross-coverage)|7         |7          |-        |✅ Complete|
|**Total**              |**~266**  |**~271**   |**~292** |          |

### ✅ Phase 4: Model Integration (COMPLETE)

Complete model layer implementing the 14-step workflow:

|Component              |File                      |Status    |
|-----------------------|--------------------------|----------|
|Core Data Types        |`model/types.py`          |✅ Complete|
|Config Manager         |`model/config_manager.py` |✅ Complete|
|Model Data Manager     |`model/model_data.py`     |✅ Complete|
|Model Scorer (4-6)     |`model/scorer.py`         |✅ Complete|
|Query Evaluator (7)    |`model/query_evaluator.py`|✅ Complete|
|Model Pricer (8-12)    |`model/pricer.py`         |✅ Complete|
|Workflow Engine (1-13) |`model/workflow.py`       |✅ Complete|

### ✅ Phase 5: Testing & Validation (COMPLETE)

Comprehensive test suite:

|Test Type              |Location                           |Status    |
|-----------------------|-----------------------------------|----------|
|Config Manager Tests   |`tests/unit/test_config_manager.py`|✅ Complete|
|Model Data Tests       |`tests/unit/test_model_data.py`    |✅ Complete|
|Scorer Tests           |`tests/unit/test_scorer.py`        |✅ Complete|
|Query Evaluator Tests  |`tests/unit/test_query_evaluator.py`|✅ Complete|
|Pricer Tests           |`tests/unit/test_pricer.py`        |✅ Complete|
|Workflow Tests         |`tests/unit/test_workflow.py`      |✅ Complete|
|Integration Tests      |`tests/integration/`               |✅ Complete|

### ✅ Phase 6: Discovery Integration (COMPLETE)

Website discovery integrated into workflow as Step 0:

|Component                       |File                           |Status    |
|--------------------------------|-------------------------------|----------|
|Discovery Types                 |`model/types.py`               |✅ Complete|
|Enhanced InferenceContext       |`signals/types.py`             |✅ Complete|
|Workflow Discovery Integration  |`model/workflow.py`            |✅ Complete|
|Discovery Engine                |`discovery/website_discovery.py`|✅ Complete|

-----

## Production Roadmap

All phases are complete. The framework is ready for production deployment.

### ✅ Phase 7: Traditional Pricing Integration (COMPLETE)

Traditional actuarial modifiers in `model/modifiers/`: loss_history.py, exposure.py, external_rating.py.

### ✅ Phase 8: Performance Monitoring & Analytics (COMPLETE)

Full analytics suite in `analytics/`: performance.py, tuning.py, cohorts.py.

### ✅ Phase 9: Portfolio Analytics (COMPLETE)

Portfolio analytics in `analytics/`: portfolio.py, workflow_analytics.py, signal_analytics.py.

### ✅ Phase 10: Multi-Coverage Orchestration (COMPLETE)

Multi-coverage support with locale detection and configuration-based orchestration.

### ✅ Phase 11: Production API (COMPLETE)

FastAPI implementation in `api/`: routes, auth (JWT + API key), middleware.

### ✅ Phase 12: Integration Layer (COMPLETE)

Integrations in `integrations/`: email parsing, document processing, webhooks.

### ✅ Phase 13: LLM Coverage Builder (COMPLETE)

Coverage builder in `builder/`: coverage_builder.py, validator.py.

### ✅ Phase 14: Complete Examples & Final Validation (COMPLETE)

Working examples for all 7 coverages in `examples/`. Live demo in `demo/`. Deployment configs in `deploy/`.

-----

## Phase 4: Model Integration (Detailed Plan)

This phase builds the runtime engine that executes the 14-step workflow above.

### 4.1 Config Manager (`model/config_manager.py`)

**Purpose**: Handle configuration storage, hashing, and retrieval.

**Content-Addressable Storage Implementation:**

```python
@dataclass
class ConfigVersion:
    """Metadata for a configuration version"""
    version_id: str           # UUID
    config_hash: str          # SHA-256 of YAML payload
    coverage: str
    configuration: str
    created_by: str
    created_at: datetime
    is_active: bool

class ConfigManager:
    """Manages configuration versioning and storage"""
    
    def hash_config(self, yaml_content: str) -> str:
        """Generate SHA-256 hash of YAML payload"""
    
    def store_config(
        self,
        yaml_content: str,
        coverage: str,
        configuration: str,
        user: str
    ) -> ConfigVersion:
        """
        Stage 1: Check hash, store payload if new
        Stage 2: Create metadata record
        Returns: ConfigVersion with version_id
        """
    
    def load_config(self, config_hash: str) -> CoverageConfig:
        """Load and parse config by hash"""
    
    def load_config_by_version(self, version_id: str) -> CoverageConfig:
        """Load config by version ID (looks up hash first)"""
    
    def get_active_config(self, coverage: str) -> CoverageConfig:
        """Get currently active config for a coverage"""
```

**Typed Configuration Structures:**

```python
@dataclass
class SignalCondition:
    """Condition that can trigger tier override, referral, or note"""
    condition_type: str       # 'threshold', 'equals', 'contains', etc.
    condition_value: Any
    action: str               # 'tier_override', 'referral', 'note'
    action_value: Any         # tier number, referral reason, note text

@dataclass
class SignalConfig:
    """Single signal definition from YAML"""
    name: str
    weight: float
    inference_function: str
    categorizer_type: str
    categorizer_params: dict
    conditions: list[SignalCondition]  # Optional conditions

@dataclass
class SignalGroupConfig:
    """Group of signals with collective weight"""
    name: str
    weight: float
    signals: list[SignalConfig]
    conditions: list[SignalCondition]  # Group-level conditions

@dataclass
class DirectQueryConfig:
    """Direct query (boolean question) definition"""
    id: str
    question: str
    impacts: list[dict]       # tier_override, referral, note, modifier

@dataclass
class TierConfig:
    """Score threshold to tier mapping"""
    tier: int
    min_score: int
    max_score: int
    base_premium: float | None        # Option A: pure premium
    rate: float | None                # Option B: metric-based
    rate_basis: str | None            # e.g., 'tiv', 'revenue', 'payroll'
    decision: str                     # 'approve', 'refer', 'decline'

@dataclass
class CoverageConfig:
    """Complete coverage model configuration"""
    coverage: str
    configuration: str
    version: str
    config_hash: str
    
    # Signal architecture
    signal_groups: list[SignalGroupConfig]
    
    # Direct queries
    direct_queries: list[DirectQueryConfig]
    
    # Categorical features
    categorical_groups: list[str]
    categorical_features: dict[str, dict[str, float]]  # group -> category -> modifier
    
    # Tier and pricing
    tier_thresholds: list[TierConfig]
    limit_bands: list[dict]           # ILF table
    deductible_credits: dict          # Deductible -> credit factor
    
    # Required inputs
    required_inputs: list[str]
    
    # Metadata
    metadata: dict
```

### 4.2 Model Data File (`model/model_data.py`)

**Purpose**: Track all signal outputs, versions, and interactions.

```python
@dataclass
class SignalOutput:
    """Output from a single signal"""
    signal_id: str
    signal_name: str
    raw_score: float
    confidence: float
    weighted_score: float
    data_sources: list[str]
    extracted_at: datetime
    conditions_triggered: list[str]

@dataclass
class ModelVersion:
    """A complete model execution snapshot"""
    version_id: str
    model_id: str
    version_number: int
    version_type: str         # 'initial', 'referral_review', 'amendment'
    
    # Inputs
    entity_id: str
    submission_data: dict
    direct_query_responses: dict[str, bool]
    categorical_selections: dict[str, str]
    
    # Signal outputs
    signal_outputs: list[SignalOutput]
    group_scores: dict[str, float]
    
    # Scoring
    pure_composite_score: float
    signal_conditions: list[dict]     # Triggered conditions from Step 6
    query_conditions: list[dict]      # Triggered conditions from Step 7
    tier_overrides: list[int]
    final_tier: int
    
    # Pricing
    base_premium: float
    modifiers_applied: list[dict]     # {name, factor, premium_after}
    limit_premiums: dict[float, float]  # limit -> premium
    final_premium: float
    
    # Decision
    decision: str             # 'approve', 'refer', 'decline'
    auto_approve: bool
    referral_reasons: list[str]
    notes: list[str]
    
    # Metadata
    config_hash: str
    created_at: datetime
    created_by: str

class ModelDataManager:
    """Manages model data file operations"""
    
    def create_model(self, entity_id: str, config: CoverageConfig) -> str:
        """Create new model, return model_id"""
    
    def create_version(
        self,
        model_id: str,
        version_type: str,
        **data
    ) -> ModelVersion:
        """Create new version of existing model"""
    
    def get_latest_version(self, model_id: str) -> ModelVersion:
        """Get most recent version"""
    
    def get_version_history(self, model_id: str) -> list[ModelVersion]:
        """Get all versions for audit trail"""
```

### 4.3 Model Scorer (`model/scorer.py`)

**Purpose**: Execute Steps 4-6 of the workflow.

```python
@dataclass
class ScoringResult:
    """Output from scoring (Steps 4-6)"""
    # Step 4: Signal extraction
    signal_outputs: list[SignalOutput]
    group_scores: dict[str, float]
    
    # Step 5: Pure composite
    pure_composite_score: float
    
    # Step 6: Signal conditions
    signal_conditions_triggered: list[dict]
    tier_overrides_from_signals: list[int]
    referrals_from_signals: list[str]
    notes_from_signals: list[str]

class ModelScorer:
    """Executes signal scoring pipeline"""
    
    def score_entity(
        self,
        entity_id: str,
        config: CoverageConfig,
        parallel: bool = True
    ) -> ScoringResult:
        """
        Execute Steps 4-6:
        - Step 4: Extract all signals
        - Step 5: Calculate pure composite
        - Step 6: Evaluate signal conditions
        """
    
    def extract_signals(
        self,
        entity_id: str,
        config: CoverageConfig
    ) -> list[SignalOutput]:
        """Step 4: Run all inference functions"""
    
    def calculate_composite(
        self,
        signal_outputs: list[SignalOutput],
        config: CoverageConfig
    ) -> tuple[float, dict[str, float]]:
        """Step 5: Weighted composite, returns (score, group_scores)"""
    
    def evaluate_signal_conditions(
        self,
        signal_outputs: list[SignalOutput],
        group_scores: dict[str, float],
        config: CoverageConfig
    ) -> tuple[list[int], list[str], list[str]]:
        """Step 6: Returns (tier_overrides, referrals, notes)"""
```

### 4.4 Query Evaluator (`model/query_evaluator.py`)

**Purpose**: Execute Step 7 of the workflow.

```python
@dataclass
class QueryEvaluationResult:
    """Output from query evaluation (Step 7)"""
    tier_overrides: list[int]
    referrals: list[str]
    notes: list[str]
    modifiers: list[dict]     # {name, factor} - applied after base premium

class QueryEvaluator:
    """Evaluates direct query responses"""
    
    def evaluate_queries(
        self,
        responses: dict[str, bool],
        config: CoverageConfig
    ) -> QueryEvaluationResult:
        """
        Step 7: Evaluate all direct query responses
        Returns impacts: tier overrides, referrals, notes, modifiers
        """
```

### 4.5 Model Pricer (`model/pricer.py`)

**Purpose**: Execute Steps 8-12 of the workflow.

```python
@dataclass
class PricingResult:
    """Output from pricing (Steps 8-12)"""
    # Step 8: Tier override resolution
    tier_overrides_considered: list[int]
    max_tier_override: int | None
    
    # Step 9: Final tier
    score_based_tier: int
    final_tier: int
    
    # Step 10: Base premium
    base_premium: float
    base_premium_method: str  # 'pure' or 'rate_based'
    
    # Step 11: Modifiers
    modifiers_applied: list[dict]  # {name, factor, premium_before, premium_after}
    premium_after_modifiers: float
    
    # Step 12: Limit bands
    limit_premiums: dict[float, float]  # limit -> final premium

class ModelPricer:
    """Calculates premium from score and conditions"""
    
    def price_submission(
        self,
        pure_composite_score: float,
        signal_tier_overrides: list[int],
        query_tier_overrides: list[int],
        query_modifiers: list[dict],
        categorical_selections: dict[str, str],
        submission_data: dict,  # For rate basis (TIV, revenue, etc.)
        config: CoverageConfig
    ) -> PricingResult:
        """Execute Steps 8-12"""
    
    def resolve_tier_overrides(
        self,
        score_tier: int,
        overrides: list[int]
    ) -> int:
        """Step 8: Apply maximum tier override"""
    
    def calculate_base_premium(
        self,
        tier: int,
        submission_data: dict,
        config: CoverageConfig
    ) -> tuple[float, str]:
        """Step 10: Returns (premium, method)"""
    
    def apply_modifiers(
        self,
        base_premium: float,
        categorical_selections: dict[str, str],
        query_modifiers: list[dict],
        config: CoverageConfig
    ) -> tuple[float, list[dict]]:
        """Step 11: Returns (premium, breakdown)"""
    
    def scale_to_limits(
        self,
        premium: float,
        config: CoverageConfig
    ) -> dict[float, float]:
        """Step 12: Returns {limit: premium}"""
```

### 4.6 Workflow Engine (`model/workflow.py`)

**Purpose**: Orchestrate complete 14-step workflow and determine decision.

```python
@dataclass
class WorkflowResult:
    """Complete workflow output (Step 13)"""
    model_version: ModelVersion
    decision: str             # 'approve', 'refer', 'decline'
    auto_approve: bool
    referral_reasons: list[str]
    notes: list[str]
    
    # For API response
    premium_options: dict[float, float]  # limit -> premium
    recommended_limit: float
    recommended_premium: float

class WorkflowEngine:
    """Orchestrates complete model workflow"""
    
    def __init__(
        self,
        config_manager: ConfigManager,
        data_manager: ModelDataManager,
        scorer: ModelScorer,
        query_evaluator: QueryEvaluator,
        pricer: ModelPricer
    ):
        """Inject dependencies"""
    
    def run_workflow(
        self,
        entity_id: str,
        coverage: str,
        submission_data: dict,
        direct_query_responses: dict[str, bool],
        categorical_selections: dict[str, str],
        user: str
    ) -> WorkflowResult:
        """
        Execute complete 14-step workflow:
        1. Load config (from active version)
        2. Create model data file
        3. Verify minimum viable inputs
        4-6. Score entity (signals + conditions)
        7. Evaluate direct queries
        8-9. Resolve tier
        10-12. Calculate premium
        13. Determine decision
        """
    
    def verify_inputs(
        self,
        submission_data: dict,
        config: CoverageConfig
    ) -> tuple[bool, list[str]]:
        """Step 3: Returns (valid, missing_fields)"""
    
    def determine_decision(
        self,
        final_tier: int,
        referral_reasons: list[str],
        config: CoverageConfig
    ) -> tuple[str, bool]:
        """Step 13: Returns (decision, auto_approve)"""
    
    def process_referral(
        self,
        model_id: str,
        reviewer: str,
        decision: str,
        adjustments: dict
    ) -> WorkflowResult:
        """Handle referral review (creates new model version)"""
```

### 4.7 File Structure for Phase 4

```
technical_pricing/
├── model/
│   ├── __init__.py
│   ├── types.py              # All dataclasses
│   ├── config_manager.py     # Config hashing, storage, loading
│   ├── model_data.py         # Model data file management
│   ├── scorer.py             # Steps 4-6
│   ├── query_evaluator.py    # Step 7
│   ├── pricer.py             # Steps 8-12
│   └── workflow.py           # Full orchestration + Step 13
```

-----

## Phase 5: Testing & Validation (Detailed Plan)

### 5.1 Unit Tests

```
tests/
├── unit/
│   ├── test_config_manager.py    # Hash generation, storage, loading
│   ├── test_model_data.py        # Version creation, retrieval
│   ├── test_scorer.py            # Composite calculation, conditions
│   ├── test_query_evaluator.py   # Query impact evaluation
│   ├── test_pricer.py            # Premium calculation, modifiers
│   └── test_workflow.py          # End-to-end orchestration
```

### 5.2 Integration Tests

Using YAML `test_profiles`:

```yaml
test_profiles:
  - name: "excellent_risk_auto_approve"
    inputs:
      entity_type: "major_carrier"
      direct_queries:
        bankruptcy_filed: false
        sanctions_exposure: false
    expected:
      tier: 1
      decision: "approve"
      auto_approve: true
      
  - name: "referral_trigger"
    inputs:
      entity_type: "startup"
      direct_queries:
        bankruptcy_filed: true
    expected:
      decision: "refer"
      auto_approve: false
      referral_reasons: ["bankruptcy_filed"]
```

### 5.3 Workflow Tests

- **Happy path**: Full approve flow
- **Referral flow**: Trigger → review → approve/decline
- **Tier override**: Multiple conditions, max applied
- **Missing inputs**: Proper rejection with field list
- **Version tracking**: Multiple versions for same model

-----

## Phase 6: Discovery Integration (Detailed Plan)

This phase integrates website discovery as a pre-processing step before signal extraction.

### 6.1 The Discovery Problem

When a submission arrives, it typically contains:
- Company name (e.g., "MS Amlin", "Petrobras", "Lufthansa")
- Optional domain hint (e.g., "msamlin.com")
- Optional country/region hint

**Challenge**: The same company name can have multiple web presences:
- Corporate parent vs subsidiary
- Regional variations (petrobras.com vs petrobras.com.br)
- Marketing sites vs investor relations

**Solution**: Discovery module identifies the correct corporate website before signal extraction begins.

### 6.2 Discovery Module (`discovery/`)

Located in `technical_pricing/discovery/`:

```python
from technical_pricing.discovery import (
    WebsiteDiscoveryEngine,
    discover_website,
    DiscoveryResult,
    WebsiteCandidate,
)

# Simple discovery
result = discover_website("MS Amlin")
print(result.primary_website.domain)  # "msamlin.com"
print(result.confidence)              # 0.95

# Discovery with hints
result = discover_website(
    "Petrobras",
    domain_hint="petrobras.com.br",
    country_hint="Brazil"
)
```

**Key Classes:**

```python
@dataclass
class WebsiteCandidate:
    """A potential website match"""
    domain: str
    url: str
    confidence: float
    discovery_method: DiscoveryMethod
    website_type: WebsiteType
    evidence: List[str]

@dataclass
class DiscoveryResult:
    """Complete discovery output"""
    query: str
    primary_website: WebsiteCandidate
    alternate_websites: List[WebsiteCandidate]
    corporate_identity: CompanyIdentity
    relationships: List[CorporateRelationship]
    confidence: float
    discovery_time_ms: float
```

### 6.3 Extended Workflow (Step 0)

The complete workflow is 14 steps (Step 0 discovery + Steps 1-13 pricing):

```
┌─────────────────────────────────────────────────────────────────┐
│                    EXTENDED WORKFLOW                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  STEP 0: DISCOVERY (NEW)                                         │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ Company Name + Hints → Website Discovery → Domain        │   │
│  │                                                           │   │
│  │ Outputs:                                                  │   │
│  │ - Primary website URL/domain                              │   │
│  │ - Corporate identity (parent, subsidiaries)               │   │
│  │ - Confidence score                                        │   │
│  │ - Alternate websites for manual review                    │   │
│  └──────────────────────────────────────────────────────────┘   │
│                              │                                   │
│                              ▼                                   │
│  STEPS 1-13: EXISTING WORKFLOW                                   │
│  (Now with discovered website context for extractors)            │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 6.4 Integration Points

**WorkflowEngine Changes:**

```python
class WorkflowEngine:
    def __init__(
        self,
        config_manager: ConfigManager,
        data_manager: ModelDataManager,
        scorer: ModelScorer,
        query_evaluator: QueryEvaluator,
        pricer: ModelPricer,
        discovery_engine: WebsiteDiscoveryEngine = None  # NEW
    ):
        self.discovery_engine = discovery_engine or WebsiteDiscoveryEngine()

    def run_workflow(
        self,
        entity_name: str,              # Company name for discovery
        coverage: str,
        submission_data: dict,
        domain_hint: str = None,       # Optional domain hint
        country_hint: str = None,      # Optional country hint
        skip_discovery: bool = False,  # Skip if domain already known
        **kwargs
    ) -> WorkflowResult:
        # Step 0: Discovery
        if not skip_discovery:
            discovery = self.discovery_engine.discover(
                entity_name,
                domain_hint=domain_hint,
                country_hint=country_hint
            )
            entity_id = discovery.primary_website.domain
            submission_data["discovered_website"] = discovery.primary_website.url
            submission_data["discovery_confidence"] = discovery.confidence
        else:
            entity_id = domain_hint or entity_name

        # Steps 1-13: Existing workflow
        # ...
```

**InferenceContext Enhancement:**

```python
@dataclass
class InferenceContext:
    # Existing fields
    configuration: dict
    coverage: str
    config_name: str

    # NEW: Discovery context for extractors
    discovered_website: str = None
    discovered_domain: str = None
    corporate_identity: dict = None
    discovery_confidence: float = 1.0
```

### 6.5 Extractor Usage of Discovery

Extractors can use the discovered website to fetch data:

```python
class SecurityHeadersExtractor(StubExtractor):
    def extract(self, entity_id: str, context: InferenceContext) -> ExtractorResult:
        # Use discovered website if available
        url = context.discovered_website or f"https://{entity_id}"

        # In production: fetch and analyze headers
        # In stub mode: return realistic mock data
        return self._generate_stub_data(entity_id, url)
```

### 6.6 File Structure for Phase 6

```
technical_pricing/
├── discovery/
│   ├── __init__.py              ✅ Package exports
│   └── website_discovery.py     ✅ Core discovery engine
├── model/
│   ├── types.py                 ✅ DiscoveryResult integrated
│   └── workflow.py              ✅ Step 0 discovery integrated
└── signals/
    └── types.py                 ✅ InferenceContext enhanced
```

### 6.7 Implementation Tasks

| Task | File | Status |
|------|------|--------|
| Add discovery types to model | `model/types.py` | ✅ Complete |
| Enhance InferenceContext | `signals/types.py` | ✅ Complete |
| Integrate discovery into workflow | `model/workflow.py` | ✅ Complete |
| Add discovery tests | `tests/unit/test_discovery.py` | ✅ Complete |
| Update integration tests | `tests/integration/` | ✅ Complete |

-----

## Phase 7: Traditional Pricing Integration (Detailed Plan)

This phase integrates traditional actuarial data sources as **OPTIONAL** modifiers applied after base premium generation. These complement DSI signals with historical and exposure-based factors when data is available.

### 7.1 The Integration Problem

DSI provides forward-looking risk assessment through digital signals, but traditional pricing can optionally include:
- **Loss History**: Past claims experience (when available)
- **Exposure Data**: Revenue, payroll, TIV, fleet size, etc. (when available)
- **Actuarial Models**: Experience rating, credibility weighting
- **External Ratings**: Credit scores, financial strength (when integrated)

**Key Design Principles**:
1. **All inputs are OPTIONAL** - DSI works without traditional data
2. **Graceful degradation** - Skip modifiers when data unavailable
3. **Streamlined mode** - Quick exposure scoring for STP (Straight-Through Processing)
4. **Full mode** - Detailed analysis when data is rich

**Solution**: Create optional modifier interfaces that can be plugged in after Step 10 (Base Premium) and before Step 11 (Modifier Application). Modifiers that lack data simply return factor=1.0 (no impact).

### 7.2 Traditional Modifier Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                 TRADITIONAL PRICING MODIFIERS                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Applied after base premium (Step 10), before modifiers (Step 11)│
│                                                                  │
│  ┌──────────────────┐   ┌──────────────────┐   ┌──────────────┐ │
│  │LOSS HISTORY      │   │EXPOSURE          │   │EXTERNAL      │ │
│  │MODIFIER          │   │MODIFIER          │   │RATING        │ │
│  │                  │   │                  │   │MODIFIER      │ │
│  │• Claims count    │   │• TIV ratio       │   │• Credit score│ │
│  │• Loss ratio      │   │• Revenue growth  │   │• AM Best     │ │
│  │• Large losses    │   │• Employee count  │   │• S&P rating  │ │
│  │• Trend analysis  │   │• Fleet age       │   │              │ │
│  └──────────────────┘   └──────────────────┘   └──────────────┘ │
│           │                     │                     │          │
│           └─────────────────────┼─────────────────────┘          │
│                                 ▼                                │
│                    COMBINED TRADITIONAL MODIFIER                 │
│                                 │                                │
│                                 ▼                                │
│              Step 11: Apply with DSI modifiers                   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 7.3 Data Structures

```python
@dataclass
class LossHistoryInput:
    """Loss history data for experience rating"""
    policy_years: List[PolicyYear]  # 3-5 years of history
    claims: List[Claim]
    large_loss_threshold: float
    credibility_factor: float  # 0-1 based on exposure volume

@dataclass
class PolicyYear:
    year: int
    premium: float
    incurred_losses: float
    paid_losses: float
    outstanding_reserves: float
    claim_count: int

@dataclass
class Claim:
    claim_id: str
    occurrence_date: date
    incurred_amount: float
    paid_amount: float
    status: str  # open, closed, reopened
    cause_code: str
    is_large_loss: bool

@dataclass
class ExposureInput:
    """
    Exposure metrics for rating - ALL FIELDS OPTIONAL

    Two modes:
    - Streamlined (STP): Only needs revenue OR tiv for quick factor
    - Full: Uses all available data for detailed analysis
    """
    # Core exposure (any ONE enables streamlined mode)
    tiv: Optional[float] = None
    revenue: Optional[float] = None

    # Additional metrics (for full mode)
    employee_count: Optional[int] = None
    payroll: Optional[float] = None
    fleet_size: Optional[int] = None
    fleet_average_age: Optional[float] = None
    locations_count: Optional[int] = None

    # Coverage-specific (optional)
    cyber_endpoints: Optional[int] = None
    vessels_count: Optional[int] = None
    aircraft_count: Optional[int] = None

    @property
    def has_minimal_data(self) -> bool:
        """Check if enough data for streamlined exposure factor"""
        return self.tiv is not None or self.revenue is not None

    @property
    def mode(self) -> str:
        """Determine analysis mode based on available data"""
        if not self.has_minimal_data:
            return "none"  # Skip exposure modifier
        full_fields = [self.employee_count, self.payroll, self.fleet_size]
        if sum(1 for f in full_fields if f is not None) >= 2:
            return "full"
        return "streamlined"  # STP mode

@dataclass
class TraditionalModifierResult:
    """Output from traditional modifier calculation"""
    modifier_type: str  # 'loss_history', 'exposure', 'external_rating'
    factor: float  # Multiplicative factor (1.0 = no change)
    confidence: float  # Data quality/credibility
    components: Dict[str, float]  # Breakdown
    notes: List[str]
    data_sources: List[str]
```

### 7.4 Modifier Interfaces

```python
class TraditionalModifier(ABC):
    """Base class for traditional pricing modifiers"""

    @abstractmethod
    def calculate(
        self,
        entity_id: str,
        coverage: str,
        submission_data: Dict[str, Any],
        context: InferenceContext
    ) -> TraditionalModifierResult:
        """Calculate the modifier factor"""
        pass

    @property
    @abstractmethod
    def modifier_type(self) -> str:
        """Type identifier for this modifier"""
        pass

class LossHistoryModifier(TraditionalModifier):
    """
    Experience rating based on loss history - OPTIONAL input.

    Methods:
    - Pure loss ratio method
    - Frequency/severity method
    - Credibility-weighted method

    When no loss history is provided, returns factor=1.0 (no impact).
    """

    def calculate(self, entity_id: str, ...) -> TraditionalModifierResult:
        # Check if loss data is available
        loss_data = self._get_loss_data(entity_id, submission_data)
        if not loss_data:
            # No loss history - return neutral (no impact)
            return TraditionalModifierResult(
                modifier_type="loss_history",
                factor=1.0,
                confidence=0.0,
                components={},
                notes=["No loss history available - modifier skipped"],
                data_sources=[]
            )

        # Process available loss data
        loss_ratio = self._calculate_loss_ratio(loss_data)
        expected_loss_ratio = self._get_expected_loss_ratio(coverage)
        premium_volume = loss_data.total_premium

        # Experience modification factor with credibility weighting
        credibility = min(1.0, premium_volume / self.full_credibility_premium)
        emf = (credibility * loss_ratio + (1 - credibility) * expected_loss_ratio) / expected_loss_ratio

        # Apply cap and floor
        emf = max(self.floor_factor, min(self.cap_factor, emf))

        return TraditionalModifierResult(
            modifier_type="loss_history",
            factor=emf,
            confidence=credibility,
            components={
                "loss_ratio": loss_ratio,
                "expected_loss_ratio": expected_loss_ratio,
                "credibility": credibility,
                "raw_emf": emf,
            },
            notes=[f"Experience mod based on {len(loss_data.policy_years)} years of history"],
            data_sources=["claims_system", "submission"]
        )

class ExposureModifier(TraditionalModifier):
    """
    Exposure-based adjustments with streamlined STP mode.

    Two modes:
    1. STREAMLINED (STP - Straight-Through Processing):
       - Only needs revenue OR tiv
       - Uses simplified size curve lookup
       - Returns quick factor for automatic processing

    2. FULL (when rich data available):
       - Analyzes multiple exposure metrics
       - Considers growth trends
       - Evaluates concentration factors
    """

    def calculate(self, entity_id: str, ...) -> TraditionalModifierResult:
        exposure = ExposureInput.from_submission(submission_data)

        if not exposure.has_minimal_data:
            # No exposure data - return neutral (no impact)
            return TraditionalModifierResult(
                modifier_type="exposure",
                factor=1.0,
                confidence=0.0,
                components={},
                notes=["No exposure data available - modifier skipped"],
                data_sources=[]
            )

        if exposure.mode == "streamlined":
            # STP mode: Quick factor from size curve
            factor = self._streamlined_factor(exposure)
            return TraditionalModifierResult(
                modifier_type="exposure",
                factor=factor,
                confidence=0.7,  # Lower confidence for simplified analysis
                components={"size_factor": factor},
                notes=["Streamlined exposure analysis (STP mode)"],
                data_sources=["submission"]
            )
        else:
            # Full mode: Detailed analysis
            return self._full_analysis(exposure)

class ExternalRatingModifier(TraditionalModifier):
    """
    External rating adjustments.

    Sources:
    - Credit ratings (D&B, Experian)
    - Financial strength (AM Best, S&P)
    - ESG scores
    """
    pass
```

### 7.5 Integration with Workflow

```python
class WorkflowEngine:
    def __init__(
        self,
        # ... existing
        traditional_modifiers: List[TraditionalModifier] = None
    ):
        self.traditional_modifiers = traditional_modifiers or []

    def run_workflow(self, ...):
        # Steps 1-10: Existing workflow

        # NEW: Step 10.5 - Traditional Modifiers
        traditional_results = []
        for modifier in self.traditional_modifiers:
            result = modifier.calculate(
                entity_id=entity_id,
                coverage=coverage,
                submission_data=submission_data,
                context=context
            )
            traditional_results.append(result)

        # Step 11: Apply all modifiers (DSI + Traditional)
        all_modifiers = query_modifiers + [
            {"name": r.modifier_type, "factor": r.factor}
            for r in traditional_results
        ]
```

### 7.6 Configuration

```yaml
traditional_modifiers:
  loss_history:
    enabled: true
    full_credibility_premium: 500000
    years_required: 3
    large_loss_threshold: 100000
    cap_factor: 1.50  # Max loading
    floor_factor: 0.75  # Max credit

  exposure:
    enabled: true
    size_curve: "iso_curve_2"
    growth_threshold: 0.20  # >20% growth triggers review

  external_rating:
    enabled: false  # Enable when integration ready
    sources:
      - type: credit_rating
        provider: dun_bradstreet
      - type: financial_strength
        provider: am_best
```

### 7.7 Implementation Tasks

| Task | File | Status |
|------|------|--------|
| Create TraditionalModifier base class | `model/modifiers/base.py` | ✅ Complete |
| Implement LossHistoryModifier | `model/modifiers/loss_history.py` | ✅ Complete |
| Implement ExposureModifier | `model/modifiers/exposure.py` | ✅ Complete |
| Implement ExternalRatingModifier | `model/modifiers/external_rating.py` | ✅ Complete |
| Add modifier types | `model/types.py` | ✅ Complete |
| Integrate into workflow | `model/workflow.py` | ✅ Complete |
| Add YAML configuration schema | `coverages/*/config.yaml` | ✅ Complete |
| Create unit tests | `tests/unit/test_traditional_modifiers.py` | ✅ Complete |

-----

## Phase 8: Performance Monitoring & Analytics (Detailed Plan)

This phase implements performance tracking against actual losses, pattern identification, and model tuning capabilities.

### 8.1 The Monitoring Problem

DSI produces risk assessments, but we need to:
- **Track Accuracy**: Compare predictions to actual outcomes
- **Identify Patterns**: Find systematic over/under-pricing
- **Tune Models**: Adjust weights and thresholds based on evidence
- **Cohort Analysis**: Compare similar risks to identify discrepancies

### 8.2 Performance Tracking Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                 PERFORMANCE MONITORING SYSTEM                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐       │
│  │ DSI OUTPUT   │    │ ACTUAL       │    │ COMPARISON   │       │
│  │              │    │ OUTCOMES     │    │ ENGINE       │       │
│  │ • Score      │ +  │ • Claims     │ →  │ • Accuracy   │       │
│  │ • Tier       │    │ • Losses     │    │ • Bias       │       │
│  │ • Premium    │    │ • Events     │    │ • Patterns   │       │
│  └──────────────┘    └──────────────┘    └──────────────┘       │
│                                                                  │
│                              │                                   │
│                              ▼                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    ANALYTICS OUTPUTS                       │   │
│  │                                                            │   │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐          │   │
│  │  │ REPORTS    │  │ ALERTS     │  │ TUNING     │          │   │
│  │  │            │  │            │  │ RECS       │          │   │
│  │  │ • By tier  │  │ • Drift    │  │ • Weights  │          │   │
│  │  │ • By signal│  │ • Anomaly  │  │ • Thresholds│         │   │
│  │  │ • By cohort│  │ • Trend    │  │ • Signals  │          │   │
│  │  └────────────┘  └────────────┘  └────────────┘          │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│                              │                                   │
│                              ▼                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    ML ENHANCEMENT (Optional)              │   │
│  │                                                            │   │
│  │  • Gradient boosting for weight optimization              │   │
│  │  • Anomaly detection for outlier identification           │   │
│  │  • Time series for trend prediction                       │   │
│  │  • Clustering for cohort discovery                        │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 8.3 Data Structures

```python
@dataclass
class OutcomeRecord:
    """Actual outcome for a priced risk"""
    entity_id: str
    model_id: str
    policy_inception: date
    policy_expiry: date

    # What we predicted
    dsi_score: float
    dsi_tier: int
    quoted_premium: float
    bound_premium: float  # May differ from quote

    # What actually happened
    claim_count: int
    incurred_losses: float
    large_losses: List[float]
    loss_ratio: float

    # Metadata
    coverage: str
    configuration: str
    recorded_at: datetime

@dataclass
class PerformanceMetrics:
    """Aggregated performance metrics"""
    period: str  # 'monthly', 'quarterly', 'annual'
    start_date: date
    end_date: date

    # Accuracy metrics
    tier_accuracy: float  # % where tier matched outcome
    score_correlation: float  # Correlation with loss ratio
    lift_curve_auc: float  # Area under lift curve

    # Bias metrics
    average_prediction_error: float
    systematic_bias: float  # Over/under-pricing trend

    # By tier breakdown
    tier_metrics: Dict[int, TierPerformance]

    # By signal breakdown
    signal_contribution: Dict[str, SignalPerformance]

@dataclass
class TierPerformance:
    tier: int
    count: int
    average_score: float
    average_loss_ratio: float
    expected_loss_ratio: float
    actual_vs_expected: float

@dataclass
class CohortDefinition:
    """Definition of a comparison cohort"""
    cohort_id: str
    name: str
    criteria: Dict[str, Any]  # Filters
    # e.g., {"coverage": "fi", "tier": [1,2], "size": "large"}
```

### 8.4 Cohort Analysis

```python
class CohortAnalyzer:
    """
    Compare performance of similar risks.

    Use cases:
    - Large banks vs other large banks
    - Tech companies by tier
    - Geographic performance differences
    """

    def define_cohort(
        self,
        name: str,
        coverage: str,
        filters: Dict[str, Any]
    ) -> CohortDefinition:
        """Create a cohort for comparison"""
        pass

    def compare_cohorts(
        self,
        cohort_a: str,
        cohort_b: str,
        metrics: List[str]
    ) -> CohortComparison:
        """Compare two cohorts on specified metrics"""
        pass

    def identify_outliers(
        self,
        cohort: str,
        threshold: float = 2.0  # Standard deviations
    ) -> List[OutlierRisk]:
        """Find risks that deviate from cohort norm"""
        pass

    def suggest_cohort_adjustments(
        self,
        cohort: str
    ) -> List[TuningRecommendation]:
        """Suggest signal weight adjustments for cohort"""
        pass
```

### 8.5 Auto-Tuning System

```python
class ModelTuner:
    """
    Automated model tuning based on performance data.

    Modes:
    - Manual: Generate recommendations for human review
    - Semi-auto: Apply recommendations with approval
    - Auto: Automatically adjust within bounds
    """

    def analyze_performance(
        self,
        coverage: str,
        period: str = "12_months"
    ) -> PerformanceAnalysis:
        """Analyze model performance over period"""
        pass

    def generate_recommendations(
        self,
        analysis: PerformanceAnalysis
    ) -> List[TuningRecommendation]:
        """
        Generate tuning recommendations:
        - Weight adjustments
        - Threshold changes
        - Signal additions/deprecations
        """
        pass

    def apply_tuning(
        self,
        recommendations: List[TuningRecommendation],
        mode: str = "manual"  # manual, semi_auto, auto
    ) -> TuningResult:
        """Apply recommendations based on mode"""
        pass

    def backtest_tuning(
        self,
        recommendations: List[TuningRecommendation],
        historical_data: List[OutcomeRecord]
    ) -> BacktestResult:
        """Test recommendations against historical data"""
        pass

@dataclass
class TuningRecommendation:
    """A specific tuning recommendation"""
    recommendation_id: str
    type: str  # 'weight_adjust', 'threshold_adjust', 'signal_add', 'signal_deprecate'
    target: str  # Signal or group ID
    current_value: Any
    recommended_value: Any
    expected_impact: float  # Estimated improvement
    confidence: float
    rationale: str
    evidence: Dict[str, Any]
```

### 8.6 ML Integration (Optional)

```python
class MLEnhancedTuner:
    """
    ML-powered tuning and prediction.

    Models:
    - XGBoost/LightGBM for weight optimization
    - Isolation Forest for anomaly detection
    - K-Means for cohort discovery
    - ARIMA for trend prediction
    """

    def optimize_weights(
        self,
        historical_data: pd.DataFrame,
        target: str = "loss_ratio"
    ) -> Dict[str, float]:
        """Use gradient boosting to find optimal weights"""
        pass

    def detect_anomalies(
        self,
        recent_submissions: List[ModelVersion]
    ) -> List[AnomalyAlert]:
        """Identify unusual patterns in recent submissions"""
        pass

    def discover_cohorts(
        self,
        portfolio_data: pd.DataFrame,
        n_clusters: int = 5
    ) -> List[DiscoveredCohort]:
        """Automatically discover natural cohorts"""
        pass

    def predict_trend(
        self,
        metric: str,
        horizon: int = 12  # months
    ) -> TrendPrediction:
        """Predict future performance trend"""
        pass
```

### 8.7 Implementation Tasks

| Task | File | Status |
|------|------|--------|
| Create OutcomeRecord and metrics types | `analytics/types.py` | ✅ Complete |
| Implement PerformanceTracker | `analytics/performance.py` | ✅ Complete |
| Implement CohortAnalyzer | `analytics/cohorts.py` | ✅ Complete |
| Implement ModelTuner | `analytics/tuning.py` | ✅ Complete |
| Create ML module (optional) | `analytics/ml/` | 🔲 Optional |
| Add outcome ingestion API | `api/outcomes.py` | ✅ Complete |
| Create performance dashboards | `analytics/dashboards.py` | 🔲 Optional |
| Add unit tests | `tests/unit/test_analytics.py` | ✅ Complete |

-----

## Phase 9: Portfolio Analytics (Detailed Plan)

Rebuilt portfolio analytics allowing review of all risks, submissions, and workflow across the book.

### 9.1 Portfolio Analytics Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                   PORTFOLIO ANALYTICS SYSTEM                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                     DATA LAYER                            │   │
│  │                                                           │   │
│  │  Submissions  │  Quotes  │  Binds  │  Claims  │  Signals │   │
│  └──────────────────────────────────────────────────────────┘   │
│                              │                                   │
│                              ▼                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                   ANALYTICS ENGINE                        │   │
│  │                                                           │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐       │   │
│  │  │ PORTFOLIO   │  │ WORKFLOW    │  │ SIGNAL      │       │   │
│  │  │ METRICS     │  │ ANALYTICS   │  │ ANALYTICS   │       │   │
│  │  │             │  │             │  │             │       │   │
│  │  │ • Tier dist │  │ • Turnaround│  │ • Coverage  │       │   │
│  │  │ • Premium   │  │ • Referrals │  │ • Quality   │       │   │
│  │  │ • Growth    │  │ • Decline % │  │ • Trends    │       │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘       │   │
│  └──────────────────────────────────────────────────────────┘   │
│                              │                                   │
│                              ▼                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                   VISUALIZATION LAYER                     │   │
│  │                                                           │   │
│  │  • Interactive dashboards                                 │   │
│  │  • Drill-down capability                                  │   │
│  │  • Export to PDF/Excel                                    │   │
│  │  • Scheduled reports                                      │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 9.2 Core Analytics Classes

```python
class PortfolioManager:
    """
    Central portfolio analytics and management.
    """

    def get_portfolio_summary(
        self,
        coverage: str = None,
        date_range: Tuple[date, date] = None
    ) -> PortfolioSummary:
        """High-level portfolio metrics"""
        pass

    def get_tier_distribution(
        self,
        coverage: str = None,
        compare_to: str = "prior_year"
    ) -> TierDistribution:
        """Distribution of risks by tier"""
        pass

    def get_submission_funnel(
        self,
        period: str = "mtd"
    ) -> SubmissionFunnel:
        """Submission → Quote → Bind conversion"""
        pass

    def search_risks(
        self,
        query: str,  # Natural language query
        filters: Dict[str, Any] = None
    ) -> List[RiskSummary]:
        """Search portfolio with natural language"""
        pass

class WorkflowAnalytics:
    """
    Workflow efficiency and quality metrics.
    """

    def get_turnaround_times(
        self,
        period: str = "30_days"
    ) -> TurnaroundMetrics:
        """Submission to decision timing"""
        pass

    def get_referral_analysis(
        self,
        period: str = "30_days"
    ) -> ReferralAnalysis:
        """Referral reasons and outcomes"""
        pass

    def get_underwriter_metrics(
        self,
        underwriter: str = None
    ) -> UnderwriterMetrics:
        """Per-underwriter activity and performance"""
        pass

class SignalAnalytics:
    """
    Signal quality and coverage analysis.
    """

    def get_signal_coverage(
        self,
        coverage: str
    ) -> SignalCoverageReport:
        """% of signals successfully extracted"""
        pass

    def get_signal_distributions(
        self,
        coverage: str,
        signal_group: str = None
    ) -> SignalDistributions:
        """Score distributions by signal"""
        pass

    def identify_signal_issues(
        self,
        threshold: float = 0.7
    ) -> List[SignalIssue]:
        """Find signals with low coverage or quality"""
        pass
```

### 9.3 Dashboard Components

```python
@dataclass
class PortfolioDashboard:
    """Interactive portfolio dashboard"""

    # Summary cards
    total_gwp: float
    risk_count: int
    average_score: float
    tier_distribution: Dict[int, int]

    # Charts
    premium_trend: TimeSeriesChart
    tier_migration: SankeyChart
    geographic_heat_map: MapChart
    signal_quality_radar: RadarChart

    # Tables
    recent_submissions: List[SubmissionRow]
    pending_referrals: List[ReferralRow]
    alerts: List[AlertRow]

    # Filters
    coverage_filter: List[str]
    date_range: Tuple[date, date]
    tier_filter: List[int]
```

### 9.4 Implementation Tasks

| Task | File | Status |
|------|------|--------|
| Create PortfolioManager | `analytics/portfolio.py` | ✅ Complete |
| Create WorkflowAnalytics | `analytics/workflow_analytics.py` | ✅ Complete |
| Create SignalAnalytics | `analytics/signal_analytics.py` | ✅ Complete |
| Implement natural language search | `analytics/search.py` | 🔲 Optional |
| Create dashboard data models | `analytics/portfolio_types.py` | ✅ Complete |
| Build dashboard API endpoints | `api/routes/analytics.py` | ✅ Complete |
| Create visualization components | `analytics/visualizations.py` | 🔲 Optional |
| Add unit tests | `tests/unit/test_portfolio_analytics.py` | ✅ Complete |

-----

## Phase 10: Multi-Coverage Orchestration (Detailed Plan)

This phase enables automatic pricing across multiple coverages and locales from a single submission.

### 10.1 The Multi-Coverage Problem

When a submission arrives, we may want to:
- **Price Multiple Lines**: FI, PI, D&O, Cyber for the same client
- **Test Multiple Locales**: FI in US, UK, Europe to find the best fit
- **Unknown Locale Resolution**: Client name only, no country hint
- **Cost Optimization**: Only run expensive signals when needed

### 10.2 Multi-Coverage Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                  MULTI-COVERAGE ORCHESTRATOR                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    SUBMISSION INPUT                       │   │
│  │                                                           │   │
│  │  Entity: "Global Bank Ltd"                                │   │
│  │  Mode: "multi_coverage" | "multi_locale" | "auto_detect"  │   │
│  │  Coverages: ["fi", "do", "cyber"] (or auto)               │   │
│  │  Locales: ["US", "UK", "EU"] (or auto-detect)             │   │
│  └──────────────────────────────────────────────────────────┘   │
│                              │                                   │
│                              ▼                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                   ROUTING ENGINE                          │   │
│  │                                                           │   │
│  │  1. Determine applicable coverages (from hints or rules)  │   │
│  │  2. Determine applicable locales (from discovery)         │   │
│  │  3. Generate execution plan                               │   │
│  │  4. Estimate cost (signal calls)                          │   │
│  │  5. Get approval if cost exceeds threshold                │   │
│  └──────────────────────────────────────────────────────────┘   │
│                              │                                   │
│                              ▼                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                   PARALLEL EXECUTOR                        │   │
│  │                                                           │   │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐      │   │
│  │  │FI - US  │  │FI - UK  │  │D&O - US │  │Cyber    │      │   │
│  │  │Workflow │  │Workflow │  │Workflow │  │Workflow │      │   │
│  │  └─────────┘  └─────────┘  └─────────┘  └─────────┘      │   │
│  │                                                           │   │
│  │  Shared signal cache across parallel runs                 │   │
│  └──────────────────────────────────────────────────────────┘   │
│                              │                                   │
│                              ▼                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                   RESULTS AGGREGATOR                      │   │
│  │                                                           │   │
│  │  • Best locale match per coverage                         │   │
│  │  • Consolidated quote package                             │   │
│  │  • Cross-coverage discounts                               │   │
│  │  • Package recommendations                                │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 10.3 Data Structures

```python
@dataclass
class MultiCoverageRequest:
    """Request for multi-coverage pricing"""
    entity_name: str
    domain_hint: Optional[str] = None

    # Coverage selection
    coverages: List[str] = None  # None = auto-detect
    coverage_rules: Dict[str, Any] = None  # Rules for auto-selection

    # Locale selection
    locales: List[str] = None  # None = auto-detect from discovery
    locale_detection_mode: str = "discovery"  # discovery, all, explicit

    # Cost control
    max_cost_units: int = None  # Max signal calls
    require_approval_above: int = 50  # Prompt if exceeds

    # Execution options
    parallel: bool = True
    share_cache: bool = True  # Share signal cache across runs
    fail_fast: bool = False  # Stop on first failure

@dataclass
class ExecutionPlan:
    """Plan for multi-coverage execution"""
    runs: List[PlannedRun]
    estimated_cost_units: int
    estimated_duration_seconds: float
    shared_signals: List[str]  # Signals that can be shared
    requires_approval: bool

@dataclass
class PlannedRun:
    coverage: str
    locale: str
    configuration: str
    estimated_signals: int
    estimated_cost: float

@dataclass
class MultiCoverageResult:
    """Combined results from multi-coverage pricing"""
    entity_name: str
    discovered_domain: str
    detected_locale: str

    # Per-coverage results
    coverage_results: Dict[str, WorkflowResult]

    # Best matches
    best_locale_per_coverage: Dict[str, str]
    recommended_package: List[str]

    # Aggregate metrics
    total_cost_units: int
    total_duration_seconds: float
    cache_hit_rate: float

    # Package discount (if applicable)
    package_discount: float
    combined_premium: float
```

### 10.4 Configuration

```yaml
multi_coverage:
  # Auto-detection rules
  coverage_detection:
    default_coverages: ["cyber"]  # Always include
    conditional_coverages:
      - coverage: "fi"
        condition: "sic_code in ['6021', '6022', '6029']"
      - coverage: "do"
        condition: "is_public_company"
      - coverage: "marine"
        condition: "has_vessels"

  # Locale detection
  locale_detection:
    use_discovery: true  # Use website discovery TLD
    fallback_locales: ["US", "UK"]  # Try if no hint

  # Cost control
  cost_limits:
    approval_threshold: 50  # Cost units
    max_parallel_runs: 10
    signal_cache_ttl: 3600  # Share within session

  # Package discounts
  package_discounts:
    - coverages: ["fi", "do"]
      discount: 0.05  # 5% for FI + D&O
    - coverages: ["fi", "do", "cyber"]
      discount: 0.10  # 10% for full package
```

### 10.5 Implementation Tasks

| Task | File | Status |
|------|------|--------|
| Create MultiCoverageOrchestrator | `orchestration/multi_coverage.py` | ✅ Complete |
| Create LocaleDetector | `orchestration/locale_detection.py` | ✅ Complete |
| Create ResultAggregator | `orchestration/aggregator.py` | ✅ Complete |
| Implement shared signal cache | `orchestration/multi_coverage.py` | ✅ Complete |
| Add package discount logic | `orchestration/multi_coverage.py` | ✅ Complete |
| Create orchestration types | `orchestration/types.py` | ✅ Complete |
| Add configuration schema | `coverages/*/config.yaml` | ✅ Complete |
| Add unit tests | `tests/unit/test_multi_coverage.py` | ✅ Complete |

-----

## Phase 11: Production API (Detailed Plan)

Complete production-grade API for full model interaction.

### 11.1 API Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      DSI API GATEWAY                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Authentication │ Rate Limiting │ Logging │ Monitoring          │
│                                                                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    REST ENDPOINTS                         │   │
│  │                                                           │   │
│  │  /api/v1/submissions     POST, GET                        │   │
│  │  /api/v1/quotes          POST, GET, PATCH                 │   │
│  │  /api/v1/referrals       GET, PATCH                       │   │
│  │  /api/v1/discovery       POST                             │   │
│  │  /api/v1/portfolio       GET                              │   │
│  │  /api/v1/analytics       GET                              │   │
│  │  /api/v1/config          GET, POST (admin)                │   │
│  │  /api/v1/health          GET                              │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    ASYNC JOBS                             │   │
│  │                                                           │   │
│  │  /api/v1/jobs            POST (long-running)              │   │
│  │  /api/v1/jobs/{id}       GET (status)                     │   │
│  │  /api/v1/webhooks        POST (callbacks)                 │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    WEBSOCKET                              │   │
│  │                                                           │   │
│  │  /ws/submissions/{id}    Real-time status updates         │   │
│  │  /ws/portfolio           Live portfolio feed              │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 11.2 Core Endpoints

```python
# Submission endpoints
@router.post("/api/v1/submissions")
async def create_submission(
    request: SubmissionRequest,
    background_tasks: BackgroundTasks
) -> SubmissionResponse:
    """
    Create new submission and trigger pricing.

    Request:
    {
        "entity_name": "Acme Corp",
        "domain_hint": "acme.com",
        "coverage": "cyber",
        "submission_data": {
            "tiv": 10000000,
            "revenue": 50000000
        },
        "direct_query_responses": {
            "bankruptcy_filed": false
        }
    }

    Response:
    {
        "submission_id": "sub_abc123",
        "status": "processing",
        "estimated_completion": "2024-01-15T10:30:00Z"
    }
    """
    pass

@router.get("/api/v1/quotes/{quote_id}")
async def get_quote(quote_id: str) -> QuoteResponse:
    """
    Retrieve quote details.

    Response:
    {
        "quote_id": "quo_xyz789",
        "submission_id": "sub_abc123",
        "status": "ready",
        "composite_score": 742,
        "tier": 2,
        "tier_label": "STANDARD",
        "decision": "approve",
        "premium_options": {
            "1000000": 12500,
            "2000000": 18750,
            "5000000": 31250
        },
        "recommended_premium": 18750,
        "discovery": {
            "domain": "acme.com",
            "confidence": "high"
        },
        "signal_summary": {...},
        "valid_until": "2024-02-15T00:00:00Z"
    }
    """
    pass

@router.patch("/api/v1/referrals/{referral_id}")
async def process_referral(
    referral_id: str,
    decision: ReferralDecision
) -> QuoteResponse:
    """
    Process a referral decision.

    Request:
    {
        "decision": "approve",  # approve, decline, modify
        "adjustments": {
            "tier_override": 3,
            "premium_adjustment": 1.15
        },
        "notes": ["Manual review completed"]
    }
    """
    pass

# Multi-coverage endpoint
@router.post("/api/v1/submissions/multi")
async def create_multi_coverage_submission(
    request: MultiCoverageRequest
) -> MultiSubmissionResponse:
    """Create submission across multiple coverages/locales"""
    pass

# Analytics endpoints
@router.get("/api/v1/analytics/portfolio")
async def get_portfolio_analytics(
    coverage: str = None,
    period: str = "mtd"
) -> PortfolioAnalytics:
    """Get portfolio-level analytics"""
    pass
```

### 11.3 Authentication & Security

```python
# JWT-based authentication
@router.post("/api/v1/auth/token")
async def create_token(credentials: Credentials) -> TokenResponse:
    """Issue JWT token"""
    pass

# API key authentication for system integrations
@router.post("/api/v1/auth/api-key")
async def validate_api_key(api_key: str) -> ValidationResponse:
    """Validate API key"""
    pass

# Role-based access control
class Permission(Enum):
    SUBMIT = "submit"           # Create submissions
    QUOTE = "quote"             # View quotes
    REFERRAL = "referral"       # Process referrals
    ANALYTICS = "analytics"     # View analytics
    ADMIN = "admin"             # Admin operations

@requires_permission(Permission.REFERRAL)
async def process_referral(...):
    pass
```

### 11.4 Rate Limiting & Quotas

```yaml
rate_limits:
  default:
    requests_per_minute: 60
    requests_per_day: 10000

  by_endpoint:
    /api/v1/submissions:
      requests_per_minute: 30
    /api/v1/discovery:
      requests_per_minute: 20

  by_tier:
    standard:
      requests_per_minute: 60
    premium:
      requests_per_minute: 300
    enterprise:
      requests_per_minute: 1000

quotas:
  submissions_per_month: 1000
  api_calls_per_month: 100000
```

### 11.5 Implementation Tasks

| Task | File | Status |
|------|------|--------|
| Set up FastAPI application | `api/main.py` | ✅ Complete |
| Create submission endpoints | `api/routes/submissions.py` | ✅ Complete |
| Create quote endpoints | `api/routes/quotes.py` | ✅ Complete |
| Create referral endpoints | `api/routes/referrals.py` | ✅ Complete |
| Create analytics endpoints | `api/routes/analytics.py` | ✅ Complete |
| Implement authentication | `api/auth/` | ✅ Complete |
| Add rate limiting | `api/middleware/` | ✅ Complete |
| Add request logging | `api/middleware/` | ✅ Complete |
| Create OpenAPI documentation | FastAPI auto-generated | ✅ Complete |
| Add API tests | `tests/api/` | ✅ Complete |
| Create Docker configuration | `deploy/docker-compose.yml` | ✅ Complete |

-----

## Phase 12: Integration Layer (Detailed Plan)

Email/inbox integration and external system connectivity.

### 12.1 Integration Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     INTEGRATION LAYER                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    EMAIL/INBOX                            │   │
│  │                                                           │   │
│  │  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐   │   │
│  │  │ EMAIL       │    │ PARSER      │    │ SUBMISSION  │   │   │
│  │  │ MONITOR     │ →  │             │ →  │ CREATOR     │   │   │
│  │  │             │    │ Extract:    │    │             │   │   │
│  │  │ • IMAP      │    │ • Entity    │    │ Auto-create │   │   │
│  │  │ • Graph API │    │ • Coverage  │    │ submission  │   │   │
│  │  │ • Webhook   │    │ • Data      │    │             │   │   │
│  │  └─────────────┘    └─────────────┘    └─────────────┘   │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    DOCUMENT PROCESSING                    │   │
│  │                                                           │   │
│  │  • PDF extraction (submissions, SOVs)                     │   │
│  │  • Excel parsing (exposure data)                          │   │
│  │  • OCR for scanned documents                              │   │
│  │  • AI-powered data extraction                             │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    EXTERNAL SYSTEMS                       │   │
│  │                                                           │   │
│  │  • Policy admin systems                                   │   │
│  │  • Claims systems                                         │   │
│  │  • Broker portals                                         │   │
│  │  • Accounting systems                                     │   │
│  │  • Reinsurance platforms                                  │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    WEBHOOKS                               │   │
│  │                                                           │   │
│  │  • Quote ready notifications                              │   │
│  │  • Referral notifications                                 │   │
│  │  • Bind confirmations                                     │   │
│  │  • Alert notifications                                    │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 12.2 Email Integration

```python
class EmailIntegration:
    """
    Monitor inbox for submissions and create automatically.
    """

    def __init__(
        self,
        provider: str,  # 'imap', 'graph', 'gmail'
        config: EmailConfig
    ):
        pass

    async def monitor_inbox(
        self,
        folder: str = "INBOX",
        filter_rules: List[FilterRule] = None
    ):
        """
        Continuously monitor inbox for new submissions.

        Filter rules:
        - From domain (e.g., broker.com)
        - Subject patterns
        - Attachment types
        """
        pass

    async def parse_submission_email(
        self,
        email: EmailMessage
    ) -> ParsedSubmission:
        """
        Extract submission data from email.

        Uses:
        - NLP for entity extraction
        - Attachment parsing
        - Previous correspondence context
        """
        pass

    async def create_submission_from_email(
        self,
        parsed: ParsedSubmission,
        auto_approve: bool = False
    ) -> SubmissionResponse:
        """Create DSI submission from parsed email"""
        pass

    async def send_quote_response(
        self,
        quote: QuoteResponse,
        recipient: str,
        template: str = "standard"
    ):
        """Send quote as email response"""
        pass

@dataclass
class FilterRule:
    field: str  # 'from', 'subject', 'body', 'attachment'
    operator: str  # 'contains', 'matches', 'equals'
    value: str
    action: str  # 'process', 'ignore', 'flag'

@dataclass
class ParsedSubmission:
    entity_name: str
    suggested_coverage: str
    confidence: float
    extracted_data: Dict[str, Any]
    attachments: List[Attachment]
    original_email_id: str
    requires_review: bool
    review_reasons: List[str]
```

### 12.3 Document Processing

```python
class DocumentProcessor:
    """
    Extract structured data from documents.
    """

    async def process_pdf(
        self,
        file: bytes,
        document_type: str = "auto"
    ) -> ExtractedData:
        """
        Extract data from PDF.

        Document types:
        - submission: Broker submission form
        - sov: Statement of values
        - financial: Financial statements
        - application: Application form
        """
        pass

    async def process_excel(
        self,
        file: bytes,
        sheet_hints: Dict[str, str] = None
    ) -> ExtractedData:
        """Extract data from Excel (exposure, SOV)"""
        pass

    async def extract_with_ai(
        self,
        document: bytes,
        extraction_schema: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Use LLM to extract specific fields.

        Schema example:
        {
            "entity_name": {"type": "string", "required": True},
            "tiv": {"type": "number", "format": "currency"},
            "locations": {"type": "array", "items": {...}}
        }
        """
        pass
```

### 12.4 Implementation Tasks

| Task | File | Status |
|------|------|--------|
| Create EmailIntegration base | `integrations/email/base.py` | ✅ Complete |
| Implement email providers | `integrations/email/` | ✅ Complete |
| Create email parser | `integrations/email/parser.py` | ✅ Complete |
| Create DocumentProcessor | `integrations/documents/processor.py` | ✅ Complete |
| Add document extraction | `integrations/documents/` | ✅ Complete |
| Create webhook manager | `integrations/webhooks/manager.py` | ✅ Complete |
| Add integration types | `integrations/types.py` | ✅ Complete |
| Add integration tests | `tests/integration/test_integrations.py` | ✅ Complete |

-----

## Phase 13: LLM Coverage Builder (Detailed Plan)

Automated coverage creation via LLM with validation and integration.

### 13.1 The Coverage Building Problem

Creating a new coverage requires:
- Industry domain expertise
- Understanding of signal types
- Configuration of 40+ signals
- Proper weighting
- Tier threshold calibration
- Test profile creation

**Solution**: LLM-assisted workflow that guides coverage creation with validation.

### 13.2 LLM Builder Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    LLM COVERAGE BUILDER                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                      INPUTS                               │   │
│  │                                                           │   │
│  │  Required:                                                │   │
│  │  • Coverage name (e.g., "Renewable Energy")               │   │
│  │  • Industry description                                   │   │
│  │  • Target market (region, company size)                   │   │
│  │  • Risk characteristics                                   │   │
│  │                                                           │   │
│  │  Optional:                                                │   │
│  │  • Example companies                                      │   │
│  │  • Known risk factors                                     │   │
│  │  • Existing similar coverage to extend                    │   │
│  │  • Historical loss data                                   │   │
│  └──────────────────────────────────────────────────────────┘   │
│                              │                                   │
│                              ▼                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                   GENERATION STEPS                        │   │
│  │                                                           │   │
│  │  1. Analyze industry and identify signal categories       │   │
│  │  2. Select appropriate signal groups from library         │   │
│  │  3. Configure signal weights based on industry            │   │
│  │  4. Define tier thresholds                                │   │
│  │  5. Create direct queries                                 │   │
│  │  6. Generate test profiles                                │   │
│  │  7. Validate configuration                                │   │
│  │  8. Generate documentation                                │   │
│  └──────────────────────────────────────────────────────────┘   │
│                              │                                   │
│                              ▼                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                   VALIDATION                              │   │
│  │                                                           │   │
│  │  • Schema validation                                      │   │
│  │  • Weight sum verification (= 1.0)                        │   │
│  │  • Tier coverage verification                             │   │
│  │  • Test profile execution                                 │   │
│  │  • Signal availability check                              │   │
│  │  • Human review prompts                                   │   │
│  └──────────────────────────────────────────────────────────┘   │
│                              │                                   │
│                              ▼                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                   OUTPUTS                                 │   │
│  │                                                           │   │
│  │  • config.yaml (complete coverage configuration)          │   │
│  │  • Extractors stubs (for new signals)                     │   │
│  │  • Aggregators (for new signals)                          │   │
│  │  • Inference functions (for new signals)                  │   │
│  │  • Test cases                                             │   │
│  │  • Documentation                                          │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 13.3 Builder Workflow

```python
class CoverageBuilder:
    """
    LLM-assisted coverage building.
    """

    def __init__(
        self,
        llm_client: LLMClient,
        signal_library: SignalLibrary,
        validator: ConfigValidator
    ):
        pass

    async def create_coverage(
        self,
        spec: CoverageSpec
    ) -> CoverageBuildResult:
        """
        Main entry point for coverage creation.

        Steps:
        1. Analyze industry requirements
        2. Select and configure signals
        3. Generate configuration
        4. Validate and test
        5. Generate code stubs
        """
        pass

    async def analyze_industry(
        self,
        description: str,
        examples: List[str] = None
    ) -> IndustryAnalysis:
        """
        LLM analyzes industry to identify:
        - Key risk factors
        - Relevant signal categories
        - Industry-specific considerations
        """
        pass

    async def select_signals(
        self,
        analysis: IndustryAnalysis
    ) -> List[SignalSelection]:
        """
        Select signals from library based on analysis.

        Returns ranked list of signals with:
        - Relevance score
        - Suggested weight
        - Customization notes
        """
        pass

    async def generate_config(
        self,
        selections: List[SignalSelection],
        tier_strategy: str = "standard"
    ) -> CoverageConfig:
        """Generate complete YAML configuration"""
        pass

    async def validate_config(
        self,
        config: CoverageConfig
    ) -> ValidationResult:
        """
        Validate configuration:
        - Schema compliance
        - Weight verification
        - Signal availability
        - Test execution
        """
        pass

    async def generate_stubs(
        self,
        config: CoverageConfig,
        new_signals: List[str]
    ) -> GeneratedCode:
        """
        Generate code stubs for new signals:
        - Extractors
        - Aggregators
        - Inference functions
        """
        pass

@dataclass
class CoverageSpec:
    """Input specification for new coverage"""
    name: str
    description: str
    industry: str
    target_market: str  # "US mid-market", "Global enterprise", etc.
    risk_factors: List[str]
    example_companies: List[str] = None
    base_coverage: str = None  # Extend from existing
    notes: str = None

@dataclass
class CoverageBuildResult:
    """Output from coverage building"""
    success: bool
    config_yaml: str
    generated_files: Dict[str, str]  # path -> content
    validation_results: ValidationResult
    warnings: List[str]
    human_review_required: List[str]
```

### 13.4 Signal Library

```python
class SignalLibrary:
    """
    Reusable signal components for coverage building.
    """

    # Standard signal groups available
    SIGNAL_GROUPS = {
        "technical_infrastructure": [
            "security_headers",
            "tls_configuration",
            "email_authentication",
            "dns_security",
            # ...
        ],
        "corporate_footprint": [
            "website_quality",
            "security_disclosure",
            "leadership_visibility",
            # ...
        ],
        "network_authority": [
            "customer_quality",
            "partner_ecosystem",
            "certification_status",
            # ...
        ],
        # ... more groups
    }

    def get_signals_for_industry(
        self,
        industry: str
    ) -> List[SignalRecommendation]:
        """Get recommended signals for industry"""
        pass

    def get_signal_template(
        self,
        signal_id: str
    ) -> SignalTemplate:
        """Get template for signal implementation"""
        pass
```

### 13.5 Implementation Tasks

| Task | File | Status |
|------|------|--------|
| Create CoverageBuilder | `builder/coverage_builder.py` | ✅ Complete |
| Create ConfigValidator | `builder/validator.py` | ✅ Complete |
| Add builder tests | `tests/unit/test_builder.py` | ✅ Complete |
| Create SignalLibrary | `builder/signal_library.py` | 🔲 Optional |
| Create CodeGenerator | `builder/code_generator.py` | 🔲 Optional |
| Implement LLM prompts | `builder/prompts/` | 🔲 Optional |
| Create builder CLI | `builder/cli.py` | 🔲 Optional |
| Create documentation | `docs/coverage_building.md` | 🔲 Optional |

-----

## Phase 14: Complete Examples & Final Validation (Detailed Plan)

Working examples for all coverages and complete repository validation.

### 14.1 Coverage Example Scripts

Create runnable examples for each coverage that:
- Demonstrate complete workflow
- Use stub extractors with realistic data
- Output full model execution details
- Serve as integration tests

```python
# examples/run_aerospace_example.py

"""
Complete Aerospace Coverage Example

Demonstrates:
- Discovery workflow
- Signal extraction (stub mode)
- Composite scoring
- Tier assignment
- Premium calculation
- Full audit trail
"""

from technical_pricing.model.workflow import run_assessment
from technical_pricing.model.types import WorkflowResult

def run_example():
    # Example aerospace entity
    result = run_assessment(
        entity_id="boeing-example",
        coverage="aerospace",
        entity_name="Boeing Company",
        domain_hint="boeing.com",
        country_hint="US",
        submission_data={
            "tiv": 500_000_000,
            "fleet_size": 450,
            "annual_departures": 125000,
            "limit_requested": 100_000_000,
        },
        direct_query_responses={
            "grounding_events": False,
            "regulatory_actions": False,
            "accident_history_3yr": False,
        }
    )

    # Output full details
    print_result_summary(result)
    print_signal_breakdown(result)
    print_pricing_breakdown(result)
    print_audit_trail(result)

    return result

def print_result_summary(result: WorkflowResult):
    print("=" * 60)
    print("DSI ASSESSMENT SUMMARY")
    print("=" * 60)
    print(f"Entity: {result.model_version.entity_id}")
    print(f"Coverage: {result.model_version.coverage}")
    print(f"")
    print(f"Discovery:")
    print(f"  Domain: {result.discovered_domain}")
    print(f"  Confidence: {result.discovery_confidence}")
    print(f"")
    print(f"Scoring:")
    print(f"  Composite Score: {result.composite_score}/1000")
    print(f"  Tier: {result.tier} ({result.tier_label})")
    print(f"  Confidence: {result.confidence:.1%}")
    print(f"")
    print(f"Decision:")
    print(f"  Decision: {result.decision.value.upper()}")
    print(f"  Auto-Approve: {result.auto_approve}")
    if result.referral_reasons:
        print(f"  Referral Reasons: {result.referral_reasons}")
    print(f"")
    print(f"Premium:")
    print(f"  Recommended: ${result.recommended_premium:,.0f}")
    print(f"  Options: {result.premium_options}")

def print_signal_breakdown(result: WorkflowResult):
    print("=" * 60)
    print("SIGNAL BREAKDOWN")
    print("=" * 60)
    for output in result.model_version.signal_outputs:
        print(f"{output.signal_name}:")
        print(f"  Raw Score: {output.raw_score:.1f}")
        print(f"  Weight: {output.weight:.2f}")
        print(f"  Weighted: {output.weighted_score:.1f}")
        print(f"  Confidence: {output.confidence:.1%}")
        if output.conditions_triggered:
            print(f"  Conditions: {output.conditions_triggered}")

if __name__ == "__main__":
    run_example()
```

### 14.2 Repository Validation Checklist

```markdown
## Pre-Production Validation Checklist

### Code Quality
- [ ] All tests passing (pytest)
- [ ] Test coverage > 80%
- [ ] No linting errors (flake8, mypy)
- [ ] Documentation complete
- [ ] No TODO/FIXME in production code

### Configuration
- [ ] All 7 coverages have valid YAML configs
- [ ] Weight sums verified (= 1.0)
- [ ] Tier thresholds complete (0-1000 coverage)
- [ ] Test profiles defined for each coverage

### Architecture
- [ ] No circular dependencies
- [ ] Clean module boundaries
- [ ] Consistent error handling
- [ ] Logging throughout

### Security
- [ ] No hardcoded credentials
- [ ] Input validation on all endpoints
- [ ] Rate limiting configured
- [ ] Authentication implemented

### Performance
- [ ] Benchmark tests passing
- [ ] Response time < 5s for single quote
- [ ] Memory usage acceptable
- [ ] Database queries optimized

### Documentation
- [ ] README.md complete
- [ ] SKILL.md up to date
- [ ] API documentation (OpenAPI)
- [ ] Deployment guide
- [ ] Troubleshooting guide
```

### 14.3 Implementation Tasks

| Task | File | Status |
|------|------|--------|
| Create aerospace example | `examples/run_aerospace.py` | ✅ Complete |
| Create cyber example | `examples/run_cyber.py` | ✅ Complete |
| Create do example | `examples/run_do.py` | ✅ Complete |
| Create energy example | `examples/run_energy.py` | ✅ Complete |
| Create fi example | `examples/run_fi.py` | ✅ Complete |
| Create marine example | `examples/run_marine.py` | ✅ Complete |
| Create pi example | `examples/run_pi.py` | ✅ Complete |
| Create multi-coverage example | `examples/run_multi.py` | ✅ Complete |
| Run validation checklist | - | ✅ Complete |
| Fix any identified issues | - | ✅ Complete |
| Final documentation review | `*.md` | ✅ Complete |
| Tag release | - | 🔲 Pending |

-----

## Phase 15: Production Extractors & Signal Routing (Detailed Plan)

Implement production extractors that connect to real data sources with jurisdiction-aware routing for global coverage.

### 15.1 Production Extractor Architecture

Production extractors replace stub extractors with real API connections:

```
┌─────────────────────────────────────────────────────────────────┐
│                    SIGNAL ROUTING MODULE                        │
│                                                                 │
│  ┌────────────────┐    ┌────────────────┐    ┌───────────────┐ │
│  │JURISDICTION    │ →  │MULTI-SOURCE    │ →  │UNIFIED        │ │
│  │ROUTER          │    │AGGREGATOR      │    │SCHEMA         │ │
│  │                │    │                │    │               │ │
│  │Maps locale →   │    │Parallel calls  │    │Normalized     │ │
│  │extractors      │    │consolidate     │    │output format  │ │
│  └────────────────┘    └────────────────┘    └───────────────┘ │
│                                                                 │
│  Routing Strategies:                                            │
│  - LOCALE_PLUS_GLOBAL: Region-specific + global (recommended) │
│  - LOCALE_ONLY: Only regional sources                          │
│  - GLOBAL_ONLY: Only global sources                            │
│  - PRIMARY_ONLY: Single best source (fastest)                  │
│  - ALL: All available sources                                   │
│                                                                 │
│  Extractor Tiers:                                               │
│  - FREE: No API keys required (50 extractors implemented)      │
│  - PAID_BASIC: Low-cost APIs (Shodan, VirusTotal)              │
│  - PAID_PREMIUM: Commercial APIs (D&B, Experian, Refinitiv)    │
│  - ENTERPRISE: Premium sources (Bloomberg, FactSet)            │
└─────────────────────────────────────────────────────────────────┘
```

### 15.2 Free Production Extractors (50 Total)

| Category | Count | Extractors | Coverage |
|----------|-------|------------|----------|
| DNS | 4 | email_auth, dnssec, dns_records, whois_rdap | Global |
| HTTP | 2 | security_headers, security_txt | Global |
| Network | 4 | cloud_infra, cdn_usage, waf_presence, tls_config | Global |
| Securities | 5 | sec_filings, sec_financials, sec_litigation, sec_governance, sedar_canada | US, Canada |
| Regulatory | 9 | ofac_sanctions, epa_echo, cfpb_complaints, osha_violations, faa_certificate, eu_safety_list, fdic_enforcement, bsee_incidents, uk_fca_register | US, UK, EU |
| Sanctions | 10 | opensanctions, uk_ofsi, eu_sanctions, worldbank_debarred, interpol_red_notices, fbi_most_wanted, adb_sanctions, idb_sanctions, ebrd_ineligible, afdb_sanctions | Global |
| Security | 2 | nvd_cve, hhs_breach | Global, US |
| Industry | 2 | pcaob, aviation_safety | Global |
| Corporate | 5 | companies_house, opencorporates, australia_abn, india_mca, gleif_lei | UK, AU, IN, Global |
| Environment | 2 | eea_environment, canada_npri | EU, Canada |
| Maritime | 2 | imo_gisis, iosa_registry | Global |

### 15.3 Routing Module Components

```python
# Usage example
from technical_pricing.signals.routing import (
    JurisdictionRouter,
    RoutingStrategy,
    ExtractorTier,
    SanctionsAggregator,
)

# Get extractors for UK sanctions check
router = JurisdictionRouter()
extractors = router.get_extractors(
    signal_type='sanctions',
    locale='UK',
    strategy=RoutingStrategy.LOCALE_PLUS_GLOBAL,
    max_tier=ExtractorTier.FREE,
)
# Returns: ['uk_ofsi', 'opensanctions', 'interpol_red_notices', ...]

# Full multi-source aggregation
aggregator = SanctionsAggregator()
result = aggregator.aggregate(
    entity_id='Acme Corporation',
    signal_type='sanctions',
    locale='UK'
)
print(f"Risk: {result.result.risk_level}")  # CLEAR/LOW/MEDIUM/HIGH/CRITICAL
print(f"Matches: {result.result.total_matches}")
print(f"Sources: {result.result.sources_checked}")
```

### 15.4 Unified Output Schemas

Each signal type has a standardized output schema regardless of data source:

- **SanctionsResult**: risk_level, total_matches, matches[], confirmed_sanctioned
- **CorporateResult**: records_found, primary_record, lei, any_active
- **RegulatoryResult**: total_violations, open_violations, risk_level
- **DomainResult**: domain_age_days, expires_soon, privacy_protected

### 15.5 Signal Framework Integration (Pending)

Integration points to connect routing to existing inference layer:

1. **InferenceContext.entity_locale** - Populate from discovery/submission
2. **Bridge Aggregators** - Convert unified schemas → signal scores
3. **Routed Inference Functions** - Use router instead of hardcoded extractors

```python
# Pending: Bridge aggregator example
class SanctionsSignalAggregator(ProductionAggregator):
    """Converts SanctionsResult → signal score 0-100"""

    RISK_TO_SCORE = {
        RiskLevel.CLEAR: 95,
        RiskLevel.LOW: 75,
        RiskLevel.MEDIUM: 50,
        RiskLevel.HIGH: 25,
        RiskLevel.CRITICAL: 5,
    }

    def aggregate(self, results, locale, entity_id):
        agg = SanctionsAggregator()
        multi_result = agg.aggregate(entity_id, 'sanctions', locale)
        score = self.RISK_TO_SCORE[multi_result.result.risk_level]
        return AggregatorResult(success=True, data={'score': score})
```

### 15.6 Implementation Tasks

| Task | File | Status |
|------|------|--------|
| DNS extractors (4) | `production/dns/` | ✅ Complete |
| HTTP extractors (2) | `production/http/` | ✅ Complete |
| Network extractors (4) | `production/network/` | ✅ Complete |
| SEC extractors (5) | `production/sec/` | ✅ Complete |
| Regulatory extractors (9) | `production/regulatory/` | ✅ Complete |
| Sanctions extractors (10) | `production/sanctions/` | ✅ Complete |
| Security extractors (2) | `production/security/` | ✅ Complete |
| Industry extractors (2) | `production/industry/` | ✅ Complete |
| Corporate extractors (5) | `production/corporate/` | ✅ Complete |
| Environment extractors (2) | `production/environment/` | ✅ Complete |
| Maritime extractors (2) | `production/maritime/` | ✅ Complete |
| JurisdictionRouter | `routing/router.py` | ✅ Complete |
| Unified schemas | `routing/schemas.py` | ✅ Complete |
| MultiSourceAggregator | `routing/multi_source.py` | ✅ Complete |
| SanctionsAggregator | `routing/sanctions_aggregator.py` | ✅ Complete |
| CorporateAggregator | `routing/corporate_aggregator.py` | ✅ Complete |
| ExtractorTier system | `routing/router.py` | ✅ Complete |
| Paid extractor mappings | `routing/router.py` | ✅ Complete |
| InferenceContext.locale | `signals/types.py` | ✅ Complete |
| Bridge aggregators | `aggregators/routing_bridges.py` | ✅ Complete |
| Routed inference functions | `inference/functions/routed/` | ✅ Complete |
| Routing-level caching | `routing/multi_source.py` | ✅ Complete |
| Unit tests for routing | `tests/unit/test_routing.py` | ✅ Complete |
| Hybrid mode demo | `examples/run_hybrid.py` | ✅ Complete |
| Paid extractors (Shodan, etc.) | `production/paid/` | 🔲 Pending |

### 15.7 Phase 15 Integration Layer (Complete)

The routing module is now fully integrated with the signal framework:

#### 15.7.1 InferenceContext Locale Fields
```python
# technical_pricing/signals/types.py
@dataclass
class InferenceContext:
    # ... existing fields ...
    entity_locale: Optional[str] = None      # ISO country code (UK, US, DE)
    entity_country: Optional[str] = None     # Full country name
    locale_source: Optional[str] = None      # 'submission', 'discovery', 'domain_tld'
```

#### 15.7.2 Bridge Aggregators
```python
# technical_pricing/signals/aggregators/routing_bridges.py
class SanctionsSignalBridge(RoutingBridge):
    """Converts SanctionsResult → signal score (0-100)"""
    RISK_TO_SCORE = {CLEAR: 95, LOW: 75, MEDIUM: 50, HIGH: 25, CRITICAL: 5}

class CorporateSignalBridge(RoutingBridge):
    """Multi-score output: registration_score, status_score, age_score, lei_score"""

class DNSSignalBridge(RoutingBridge):
    """Methods: get_email_auth_score, get_dnssec_score, get_domain_age_score"""

class NetworkSignalBridge(RoutingBridge):
    """Methods: get_security_headers_score, get_tls_config_score, get_infrastructure_score"""

class SecuritySignalBridge(RoutingBridge):
    """Method: get_vulnerability_score"""
```

#### 15.7.3 Routed Inference Functions (13 Total)
```python
# technical_pricing/signals/inference/functions/routed/signals.py

# Sanctions & Corporate (5)
sanctions_check_routed         # Multi-source sanctions screening
corporate_registry_routed      # Multi-registry company lookup
corporate_status_routed        # Company active/dissolved status
corporate_age_routed           # Company establishment age
lei_verification_routed        # Legal Entity Identifier check

# DNS (3)
email_auth_routed              # SPF/DKIM/DMARC configuration
dnssec_routed                  # DNSSEC validation status
domain_age_routed              # Domain registration age

# Network (3)
security_headers_routed        # HTTP security headers
tls_config_routed              # TLS/SSL configuration
infrastructure_routed          # Cloud/CDN/WAF detection

# Security (2)
vulnerability_routed           # CVE exposure check
breach_history_routed          # Data breach history
```

#### 15.7.4 Routing-Level Cache
```python
# technical_pricing/signals/routing/multi_source.py
class RoutingCache:
    """Thread-safe TTL cache for extraction results"""
    def get(extractor_name, entity_id) -> Optional[CachedResult]
    def set(extractor_name, entity_id, data, ttl_seconds=300)
    def invalidate(extractor_name=None, entity_id=None) -> int
    def get_stats() -> Dict[str, Any]  # hits, misses, hit_rate

# Global cache singleton
get_routing_cache() -> RoutingCache
set_routing_cache(cache)  # For testing
```

#### 15.7.5 Usage Example
```python
from technical_pricing.signals.inference.functions.routed import (
    sanctions_check_routed,
    corporate_registry_routed,
    register_all,
)
from technical_pricing.signals.types import InferenceContext

# Register all routed functions
register_all()

# Create context with locale
context = InferenceContext(
    configuration={},
    coverage='general',
    config_name='test',
    entity_locale='UK',
    entity_country='United Kingdom',
    locale_source='submission',
)

# Run multi-source sanctions check
result = sanctions_check_routed('Test Company Ltd', context)
print(f"Score: {result.score}")           # 95 = clear, 5 = sanctioned
print(f"Risk: {result.raw_data.get('risk_level')}")
print(f"Sources: {result.metadata.get('sources_checked')}")
```

#### 15.7.6 Hybrid Mode Demo
```bash
# Run the Phase 15 demo
python examples/run_hybrid.py
```

Demonstrates:
- Jurisdiction-aware routing (UK, US, AU, etc.)
- Locale detection from domain TLD
- Routing strategies (LOCALE_ONLY, GLOBAL_ONLY, LOCALE_PLUS_GLOBAL)
- Extractor tier filtering (FREE, PAID_BASIC, PAID_PREMIUM)
- Routing cache with TTL expiration
- Bridge aggregators for all signal types

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
│   └── modifiers/                   ✅ PHASE 7
│       ├── base.py                  ✅ TraditionalModifier base
│       ├── loss_history.py          ✅ Experience rating
│       ├── exposure.py              ✅ Exposure adjustments
│       └── external_rating.py       ✅ Credit/financial ratings
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
```

Legend: ✅ Complete | 🔲 Optional

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

-----

## Development Workflow

When starting any DSI work:

1. **Read this SKILL.md first**
1. **Check coverage_crosswalk.json** for common concepts
1. **Reference YAML config** for the coverage you’re working on
1. **Follow the standard patterns** - don’t invent new structures
1. **Never hardcode** - if it’s in YAML, read it from YAML
1. **Follow the 14-step workflow** - don't skip or reorder steps
-----

## name: dsi-framework

description: Digital Signal Intelligence (DSI) insurance pricing framework. Use this skill when working on DSI project code including extractors, aggregators, categorizers, inference functions, signal processing, YAML config interpretation, or any technical model development. Triggers on mentions of DSI, signal architecture, coverage configs, technical pricing, or insurance underwriting automation.

# DSI Framework Development Guide

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

The complete model execution follows this 13-step workflow:

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

|Component          |File                      |Status    |
|-------------------|--------------------------|----------|
|Type Definitions   |`model/types.py`          |✅ Complete|
|Config Manager     |`model/config_manager.py` |✅ Complete|
|Model Data Manager |`model/model_data.py`     |✅ Complete|
|Scorer (Steps 4-6) |`model/scorer.py`         |✅ Complete|
|Query Evaluator    |`model/query_evaluator.py`|✅ Complete|
|Pricer (Steps 8-12)|`model/pricer.py`         |✅ Complete|
|Workflow Engine    |`model/workflow.py`       |✅ Complete|

### 🔲 Phase 5: Testing & Validation (CURRENT PHASE)

See detailed breakdown below.

-----

## Phase 4: Model Integration (Detailed Plan)

This phase builds the runtime engine that executes the 13-step workflow above.

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

**Purpose**: Orchestrate complete 13-step workflow and determine decision.

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
        Execute complete 13-step workflow:
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
│   │   └── stubs/
│   │       ├── __init__.py
│   │       ├── common.py            ✅ Cross-coverage extractors
│   │       ├── aerospace/           ✅ 21 extractors
│   │       ├── cyber/               ✅ 35 extractors
│   │       ├── do/                  ✅ 46 extractors
│   │       ├── energy/              ✅ 44 extractors
│   │       ├── fi/                  ✅ ~40 extractors
│   │       ├── marine/              ✅ ~38 extractors
│   │       └── pi/                  ✅ ~35 extractors
│   ├── aggregators/
│   │   ├── __init__.py
│   │   ├── base.py                  ✅ ProductionAggregator
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
│   └── inference/
│       ├── __init__.py
│       ├── registry.py              ✅
│       └── functions/
│           ├── __init__.py
│           ├── aerospace/           ✅ 41 functions
│           ├── cyber/               ✅ 38 functions
│           ├── do/                  ✅ 47 functions
│           ├── energy/              ✅ 46 functions
│           ├── fi/                  ✅ ~42 functions
│           ├── marine/              ✅ ~40 functions
│           └── pi/                  ✅ ~38 functions
├── model/                           ✅ PHASE 4 COMPLETE
│   ├── __init__.py                  ✅
│   ├── types.py                     ✅ All dataclasses
│   ├── config_manager.py            ✅ Config hashing/storage
│   ├── model_data.py                ✅ Model data file management
│   ├── scorer.py                    ✅ Steps 4-6
│   ├── query_evaluator.py           ✅ Step 7
│   ├── pricer.py                    ✅ Steps 8-12
│   └── workflow.py                  ✅ Full orchestration
└── tests/                           🔲 PHASE 5
    ├── unit/
    └── integration/
```

Legend: ✅ Complete | 🔲 Not Started

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
1. **Follow the 13-step workflow** - don’t skip or reorder steps
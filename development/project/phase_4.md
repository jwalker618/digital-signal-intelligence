# Phase 4: Model Integration

## Purpose
Implement the full 14-step model workflow, including configuration management, scoring, pricing, and workflow orchestration.

## Key Deliverables
- Config Manager
- Model Data Manager
- Scorer (Steps 4–6)
- Query Evaluator (Step 7)
- Pricer (Steps 8–12)
- Workflow Engine (Steps 1–13)

## Implementation Summary
This phase builds the runtime engine that executes the full DSI pricing workflow. It includes content-addressable configuration storage, versioning, scoring, condition evaluation, pricing, and decision logic.

## Detailed Plan

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

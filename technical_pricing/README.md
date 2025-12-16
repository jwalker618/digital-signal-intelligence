# DSI Technical Pricing Architecture v2.0

## Overview

This document defines the clean separation of concerns between:
1. **Extractors** - Fetch raw data from external sources
2. **Aggregators** - Combine multiple extractor outputs into signal scores
3. **Categorizers** - Map signal scores/values to categories
4. **Utility Functions** - Model-level operations (composite scoring, tier assignment)
5. **Inference Functions** - Orchestrate extractor→aggregator→categorizer chains

## Core Design Principles

### 1. Configuration-Driven Architecture
```
coverage:           aerospace           # Top-level coverage cohort
  configuration:    aerospace_general   # Specific model configuration
```

All modifiers, weights, tier definitions, and bands are defined in the config YAML.
Code never hardcodes these values - it reads them from configuration.

### 2. Instantiation by Configuration (Not Coverage)
```python
# CORRECT - instantiate by configuration
model = DSIModel.from_config("aerospace", "aerospace_general")

# WRONG - never instantiate by coverage alone
model = DSIModel("aerospace")  # Ambiguous - which configuration?
```

### 3. Clean Separation of Concerns

```
┌─────────────────────────────────────────────────────────────────────┐
│                        CONFIG.YAML                                   │
│  (aerospace_general)                                                 │
│                                                                      │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────┐  ┌───────────┐ │
│  │ signal_     │  │ categorical_ │  │ tier_       │  │ direct_   │ │
│  │ groups      │  │ features     │  │ thresholds  │  │ queries   │ │
│  └─────────────┘  └──────────────┘  └─────────────┘  └───────────┘ │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     INFERENCE FUNCTIONS                              │
│  (orchestrate data flow for each signal feature)                    │
│                                                                      │
│  alliance_membership_inference:                                      │
│    extractor: IATARegistryExtractor                                  │
│    aggregator: AllianceMembershipAggregator                         │
│    categorizer: scoring_logic                                        │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    EXTRACTORS / AGGREGATORS / CATEGORIZERS          │
│  (stateless functions that process data → return scores/categories) │
│                                                                      │
│  Input: raw data / extractor outputs                                │
│  Output: score (0-100) + metadata                                   │
│  NO ACCESS TO: modifiers, weights, tier definitions                 │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      UTILITY FUNCTIONS                               │
│  (model-level operations that apply config values)                  │
│                                                                      │
│  ┌──────────────────┐  ┌───────────────┐  ┌────────────────────┐   │
│  │ CompositeScorer  │  │ TierAssigner  │  │ ConditionEvaluator │   │
│  │ (applies weights │  │ (maps score   │  │ (evaluates bands   │   │
│  │  from config)    │  │  to tier)     │  │  from config)      │   │
│  └──────────────────┘  └───────────────┘  └────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

## Component Specifications

### Extractors
**Purpose**: Fetch raw data from external sources
**Scope**: One data source per extractor
**Output**: Raw API response or normalized data structure
**Config Access**: NONE - extractors are source-specific, not config-specific

```python
class DataExtractor(ABC):
    @abstractmethod
    def extract(self, entity_id: str, **params) -> ExtractorResult:
        """Fetch data from external source."""
        pass

@dataclass
class ExtractorResult:
    data: Dict[str, Any]      # Raw or normalized data
    source: str               # e.g., "iata_registry"
    timestamp: datetime
    confidence: float
    metadata: Dict[str, Any]
```

### Aggregators
**Purpose**: Combine multiple extractor outputs into a signal score
**Scope**: One signal per aggregator
**Output**: Score (0-100) with supporting evidence
**Config Access**: NONE - scoring logic is internal to aggregator

```python
class SignalAggregator(ABC):
    @abstractmethod
    def aggregate(self, extractor_results: Dict[str, ExtractorResult]) -> AggregatorResult:
        """Combine extractor outputs into signal score."""
        pass

@dataclass
class AggregatorResult:
    signal_id: str            # e.g., "alliance_membership"
    score: float              # 0-100
    category: Optional[str]   # e.g., "STAR_ALLIANCE"
    evidence: List[str]       # Supporting data points
    confidence: float
    metadata: Dict[str, Any]
```

### Categorizers
**Purpose**: Map values to categories (for categorical feature inference)
**Scope**: Stateless mapping functions
**Output**: Category with confidence
**Config Access**: NONE - mapping logic is internal

```python
class DataCategorizer(ABC):
    @abstractmethod
    def categorize(self, value: Any) -> CategorizationResult:
        """Map value to category."""
        pass

@dataclass
class CategorizationResult:
    category: str
    score: Optional[float]
    confidence: float
    metadata: Dict[str, Any]
```

### Inference Functions
**Purpose**: Orchestrate extractor→aggregator→categorizer chains
**Scope**: One signal feature per inference function
**Output**: Signal score ready for utility functions
**Config Access**: Referenced by name in config, receives config context

```python
# In config.yaml
signal_features:
  network_authority:
    - id: "alliance_membership"
      inference_function: "alliance_membership_inference"
      weight: 0.25  # Weight lives in config, not in inference function

# In inference_functions.py
def alliance_membership_inference(entity_id: str, config: Dict) -> InferenceResult:
    """
    Orchestrates:
    1. IATARegistryExtractor → raw IATA data
    2. AllianceMembershipAggregator → alliance score
    3. Returns score for utility functions to apply weights
    """
    # Extract
    iata_result = IATARegistryExtractor().extract(entity_id)
    
    # Aggregate
    aggregator_result = AllianceMembershipAggregator().aggregate({
        "iata": iata_result
    })
    
    return InferenceResult(
        signal_id="alliance_membership",
        score=aggregator_result.score,
        category=aggregator_result.category,
        evidence=aggregator_result.evidence,
        confidence=aggregator_result.confidence
    )
```

### Utility Functions
**Purpose**: Model-level operations that apply config values
**Scope**: Operate on signal scores using config-defined parameters
**Output**: Final model decisions (tier, composite score, actions)
**Config Access**: FULL - utilities apply weights, bands, tier definitions

```python
class CompositeScorer(UtilityFunction):
    """Applies config-defined weights to signal scores."""
    
    def calculate(self, signal_scores: Dict[str, float]) -> UtilityResult:
        # Weights come from self.configuration, not hardcoded
        weights = self.configuration.get("signal_groups", [])
        # ... apply weights from config

class TierAssigner(UtilityFunction):
    """Maps composite score to tier using config-defined thresholds."""
    
    def assign(self, composite_score: float) -> UtilityResult:
        # Tier definitions come from self.configuration
        tiers = self.configuration.get("tier_thresholds", {}).get("tiers", [])
        # ... find matching tier

class ConditionEvaluator(UtilityFunction):
    """Evaluates signal scores against config-defined bands."""
    
    def evaluate(self, signal_scores: Dict[str, float]) -> List[UtilityResult]:
        # Bands come from self.configuration
        groups = self.configuration.get("signal_groups", [])
        # ... evaluate against bands
```

## Data Flow Example

```
Entity: "Delta Air Lines"
Configuration: aerospace_general

1. INFERENCE PHASE (per signal feature)
   ┌─────────────────────────────────────────────────────────────┐
   │ alliance_membership_inference("Delta")                       │
   │   └─ IATARegistryExtractor.extract("Delta")                 │
   │        └─ returns: {alliance: "SkyTeam", status: "active"}  │
   │   └─ AllianceMembershipAggregator.aggregate(iata_result)    │
   │        └─ returns: score=88, category="SKYTEAM"             │
   └─────────────────────────────────────────────────────────────┘
   
   Repeat for all 41 signal features...
   
   Result: Dict[signal_id, score]
   {
     "alliance_membership": 88,
     "codeshare_quality": 85,
     "accident_history": 100,
     ...
   }

2. UTILITY PHASE (applies config values)
   ┌─────────────────────────────────────────────────────────────┐
   │ ConditionEvaluator.evaluate(signal_scores)                  │
   │   └─ Checks bands from config for score_condition=true      │
   │   └─ returns: [actions, overrides]                          │
   │                                                              │
   │ CompositeScorer.calculate(signal_scores)                    │
   │   └─ Applies weights from config                            │
   │   └─ returns: composite_score=847                           │
   │                                                              │
   │ TierAssigner.assign(847)                                    │
   │   └─ Uses tier_thresholds from config                       │
   │   └─ returns: tier=1, label="PREFERRED"                     │
   └─────────────────────────────────────────────────────────────┘

3. OUTPUT
   {
     "tier": 1,
     "tier_label": "PREFERRED",
     "composite_score": 847,
     "auto_approve": true,
     "actions": [],
     "signal_breakdown": {...}
   }
```

## Registry Design

### Inference Function Registry
```python
INFERENCE_REGISTRY: Dict[str, Callable] = {}

def register_inference(name: str):
    def decorator(func):
        INFERENCE_REGISTRY[name] = func
        return func
    return decorator

@register_inference("alliance_membership_inference")
def alliance_membership_inference(entity_id: str, config: Dict) -> InferenceResult:
    ...
```

### Config Reference
```yaml
# In aerospace_general config
signal_features:
  network_authority:
    - id: "alliance_membership"
      name: "Airline Alliance Membership"
      weight: 0.25
      inference_function: "alliance_membership_inference"  # Registry lookup
      score_condition: false
```

## Migration Path

### Current categorizers_v2.py Issues
1. ❌ Hardcodes threshold profiles, scoring logic, weights
2. ❌ Mixes signal processing with model-level operations
3. ❌ No distinction between configuration and coverage

### Required Changes
1. ✅ Move all profiles/weights/thresholds to config YAML
2. ✅ Extract utility functions to separate module
3. ✅ Create inference function registry
4. ✅ Refactor categorizers to be stateless mappers
5. ✅ All instantiation by configuration name

## File Structure

```
technical_pricing/
├── coverages/
│   ├── aerospace/
│   │   └── config.yaml          # aerospace_general config
│   ├── marine/
│   │   └── config.yaml          # marine_general, marine_hull configs
│   └── cyber/
│       └── config.yaml
├── signals/
│   ├── extractors.py            # Data source extractors
│   ├── aggregators.py           # Signal score aggregators
│   ├── categorizers.py          # Stateless value→category mappers
│   ├── inference_functions.py   # Orchestration layer
│   └── utility.py               # Model-level operations
└── models/
    └── dsi_model.py             # Main model class
```

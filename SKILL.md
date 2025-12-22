---
name: dsi-framework
description: Digital Signal Intelligence (DSI) insurance pricing framework. Use this skill when working on DSI project code including extractors, aggregators, categorizers, inference functions, signal processing, YAML config interpretation, or any technical model development. Triggers on mentions of DSI, signal architecture, coverage configs, technical pricing, or insurance underwriting automation.
---

# DSI Framework Development Guide

## What is DSI?

Digital Signal Intelligence (DSI) is insurance underwriting based on **observable digital signals** rather than self-reported documentation. Core insight: who trusts/partners/certifies an entity reveals risk quality more reliably than what they claim about themselves.

Key principles:
- All primary signals externally observable (no cooperation required)
- Machine-readable, no subjective judgment
- Network authority (PageRank-style) over self-reporting
- Absence is signal (missing expected presence)
- Signal → Score → Tier → Price (auditable flow)

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        YAML CONFIG                              │
│     Single source of truth for coverage model definition        │
│     (weights, modifiers, tiers, direct queries, features)       │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    SIGNAL ARCHITECTURE                          │
│                                                                 │
│  ┌──────────┐    ┌──────────┐    ┌───────────┐    ┌────────── ┐ │
│  │EXTRACTOR │ →  │AGGREGATOR│ →  │CATEGORIZER│ →  │INFERENCE  │ │
│  │          │    │          │    │           │    │           │ │
│  │Raw data  │    │Structure/│    │Score or   │    │Orchestrate│
│  │from APIs │    │normalize │    │category   │    │pipeline   │
│  └──────────┘    └──────────┘    └───────────┘    └───────── ─┘ │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      MODEL OUTPUT                               │
│  Composite score (0-1000) → Tier (1-5) → Premium + Modifiers    │
└─────────────────────────────────────────────────────────────────┘
```

## YAML Config Structure

**CRITICAL: The YAML config is the single source of truth. Never hardcode values that exist in config.**

```
coverage:                          # Domain (e.g., aerospace, cyber, marine)
  configuration:                   # Instantiable model (e.g., aerospace_general)
    metadata:                      # Name, version, min premium, markets
    direct_queries:                # Optional boolean questions (max 5-10)
    categorical_groups:            # Groups that impact pricing (modifier or premium basis)
    categorical_features:          # Categories within each group + their modifiers
    signal_groups:                 # Groups of signals with weights (must sum to 1.0)
    signal_features:               # Individual signals within groups (weights sum to 1.0 per group)
    tier_thresholds:               # Score ranges → tiers → premiums
    pricing:                       # ILF tables, deductible credits, experience mods
    test_profiles:                 # Validation scenarios
```

### Key Config Elements

**Signal Features** (within signal_groups):
```yaml
- id: "alliance_membership"
  name: "Airline Alliance Membership"
  weight: 0.25
  inference_utility_function: alliance_membership_basefunction  # Links to code
  score_condition: false  # If true, check bands for overrides
  bands:                  # Optional - score thresholds that trigger actions
    - max: 30
      override: 5         # Force to tier 5
      action: "DECLINE"
```

**Categorical Features**:
```yaml
operator_type:
  - cat: "MAJOR_AIRLINE"
    label: "Major Airline"
    modifier: 0.85        # Applied to base premium
```

## Signal Architecture Components

### 1. Extractors (STUB - Simulate Real Data)

**Purpose**: Fetch raw data from external sources (APIs, databases, FTP).

**Implementation Status**: STUB only. Return randomized but structurally realistic data.

**Design Rules**:
- One extractor CAN serve multiple signals/categorical features
- Return raw data structure that mimics real API responses
- Include realistic field names, data types, nested structures
- Randomize values within realistic bounds
- Include metadata (timestamp, source, request_id)

**Template**:
```python
class AllianceMembershipExtractor(BaseExtractor):
    """
    STUB: Simulates airline alliance membership API.
    Real implementation would query IATA/alliance databases.
    """
    
    def extract(self, entity_id: str) -> ExtractorResult:
        # Simulate API response structure
        raw_data = {
            "query_timestamp": datetime.utcnow().isoformat(),
            "entity_id": entity_id,
            "source": "iata_alliance_registry",
            "data": {
                "alliance_code": random.choice([None, "STAR", "OW", "ST"]),
                "membership_status": random.choice(["ACTIVE", "PENDING", "NONE"]),
                "join_date": self._random_date_or_none(),
                "tier_level": random.choice(["FOUNDING", "FULL", "ASSOCIATE", None]),
            },
            "metadata": {
                "api_version": "2.1",
                "response_time_ms": random.randint(50, 500),
            }
        }
        return ExtractorResult(
            success=True,
            data=raw_data,
            source="iata_alliance_registry",
            extracted_at=datetime.utcnow()
        )
```

### 2. Aggregators (PRODUCTION READY)

**Purpose**: Transform raw extractor data into normalized structure ready for scoring.

**Implementation Status**: Production ready. No changes needed when extractors become real.

**Design Rules**:
- One aggregator CAN serve multiple signals/categorical features
- Input: Raw extractor output (potentially from multiple extractors)
- Output: Normalized, structured data optimized for categorizer
- Handle missing/malformed data gracefully
- Include validation and error states
- Document expected input structure

**Template**:
```python
class AllianceMembershipAggregator(BaseAggregator):
    """
    Transforms raw alliance data into normalized scoring structure.
    
    Expected input (from AllianceMembershipExtractor):
        {
            "data": {
                "alliance_code": str | None,
                "membership_status": str,
                "join_date": str | None,
                "tier_level": str | None
            }
        }
    
    Output:
        {
            "has_alliance": bool,
            "alliance_tier": int (0-3),
            "membership_years": int,
            "is_founding_member": bool
        }
    """
    
    ALLIANCE_TIERS = {
        "STAR": 3, "OW": 3, "ST": 3,  # Major alliances
        None: 0
    }
    
    def aggregate(self, extractor_results: List[ExtractorResult]) -> AggregatorResult:
        raw = extractor_results[0].data.get("data", {})
        
        alliance_code = raw.get("alliance_code")
        membership_status = raw.get("membership_status", "NONE")
        join_date = raw.get("join_date")
        tier_level = raw.get("tier_level")
        
        # Normalize
        has_alliance = alliance_code is not None and membership_status == "ACTIVE"
        alliance_tier = self.ALLIANCE_TIERS.get(alliance_code, 0) if has_alliance else 0
        membership_years = self._calculate_years(join_date) if join_date else 0
        is_founding = tier_level == "FOUNDING"
        
        return AggregatorResult(
            success=True,
            data={
                "has_alliance": has_alliance,
                "alliance_tier": alliance_tier,
                "membership_years": membership_years,
                "is_founding_member": is_founding,
            },
            aggregated_at=datetime.utcnow()
        )
```

### 3. Categorizers (PRODUCTION READY)

**Purpose**: Apply scoring/categorization logic to produce final values.

**Implementation Status**: Production ready. Reusable patterns across signals.

**Design Rules**:
- Categorizer TYPES are reusable (threshold_bucket, range_mapper, boolean_score, etc.)
- Input: Aggregated data + scoring parameters
- Output: Score (0-100) OR category string
- Scoring logic is parameterized, not hardcoded
- Must be deterministic given same inputs

**Common Categorizer Types**:

```python
class ThresholdBucketCategorizer(BaseCategorizer):
    """
    Maps a numeric value to a score based on threshold buckets.
    Reusable for any signal that scores based on ranges.
    """
    
    def categorize(self, aggregated_data: dict, params: dict) -> CategorizerResult:
        value = aggregated_data.get(params["value_field"])
        buckets = params["buckets"]  # List of {max: x, score: y}
        
        if value is None:
            return CategorizerResult(score=params.get("null_score", 50))
        
        for bucket in sorted(buckets, key=lambda x: x["max"]):
            if value <= bucket["max"]:
                return CategorizerResult(score=bucket["score"])
        
        return CategorizerResult(score=buckets[-1].get("overflow_score", 100))


class BooleanScoreCategorizer(BaseCategorizer):
    """
    Maps boolean presence to score.
    """
    
    def categorize(self, aggregated_data: dict, params: dict) -> CategorizerResult:
        value = aggregated_data.get(params["value_field"], False)
        true_score = params.get("true_score", 100)
        false_score = params.get("false_score", 0)
        
        return CategorizerResult(score=true_score if value else false_score)


class WeightedCompositeCategorizer(BaseCategorizer):
    """
    Combines multiple sub-scores with weights.
    """
    
    def categorize(self, aggregated_data: dict, params: dict) -> CategorizerResult:
        components = params["components"]  # List of {field: x, weight: y}
        
        total_score = 0
        total_weight = 0
        
        for comp in components:
            value = aggregated_data.get(comp["field"])
            if value is not None:
                total_score += value * comp["weight"]
                total_weight += comp["weight"]
        
        if total_weight == 0:
            return CategorizerResult(score=50, confidence=0.0)
        
        return CategorizerResult(
            score=total_score / total_weight,
            confidence=total_weight / sum(c["weight"] for c in components)
        )


class CategoryMapperCategorizer(BaseCategorizer):
    """
    Maps aggregated data to a categorical feature value.
    Used for categorical_groups like operator_type, fleet_size.
    """
    
    def categorize(self, aggregated_data: dict, params: dict) -> CategorizerResult:
        # params contains mapping rules
        rules = params["rules"]  # List of {conditions: {...}, category: "X"}
        default = params.get("default_category", "UNKNOWN")
        
        for rule in rules:
            if self._matches_conditions(aggregated_data, rule["conditions"]):
                return CategorizerResult(category=rule["category"])
        
        return CategorizerResult(category=default)
```

### 4. Inference Functions (PRODUCTION READY)

**Purpose**: Orchestrate the full pipeline for ONE specific signal or categorical feature.

**Implementation Status**: Production ready. Each inference function is the bridge between config and code.

**Design Rules**:
- One inference function per `inference_utility_function` in YAML
- Knows which extractor(s), aggregator(s), categorizer(s) to use
- Returns standardized result with score/category + metadata
- Handles errors gracefully with fallback scores
- Name matches YAML reference (e.g., `alliance_membership_basefunction`)

**Template**:
```python
def alliance_membership_basefunction(entity_id: str, context: InferenceContext) -> SignalResult:
    """
    Inference function for alliance_membership signal.
    
    Maps to: signal_features.network_authority.alliance_membership
    YAML ref: inference_utility_function: alliance_membership_basefunction
    
    Pipeline:
        AllianceMembershipExtractor → AllianceMembershipAggregator → WeightedCompositeCategorizer
    """
    try:
        # 1. Extract
        extractor = AllianceMembershipExtractor()
        extract_result = extractor.extract(entity_id)
        
        if not extract_result.success:
            return SignalResult(
                signal_id="alliance_membership",
                score=50,  # Neutral score on extraction failure
                confidence=0.0,
                error="Extraction failed"
            )
        
        # 2. Aggregate
        aggregator = AllianceMembershipAggregator()
        agg_result = aggregator.aggregate([extract_result])
        
        if not agg_result.success:
            return SignalResult(
                signal_id="alliance_membership",
                score=50,
                confidence=0.3,
                error="Aggregation failed"
            )
        
        # 3. Categorize
        categorizer = WeightedCompositeCategorizer()
        cat_result = categorizer.categorize(
            agg_result.data,
            params={
                "components": [
                    {"field": "alliance_tier", "weight": 0.5, "scale": 33.33},
                    {"field": "membership_years", "weight": 0.3, "scale": 5},
                    {"field": "is_founding_member", "weight": 0.2, "true_score": 100, "false_score": 50},
                ]
            }
        )
        
        return SignalResult(
            signal_id="alliance_membership",
            score=cat_result.score,
            confidence=cat_result.confidence or 1.0,
            raw_data=extract_result.data,
            aggregated_data=agg_result.data,
            metadata={
                "extractor": "AllianceMembershipExtractor",
                "aggregator": "AllianceMembershipAggregator",
                "categorizer": "WeightedCompositeCategorizer",
            }
        )
        
    except Exception as e:
        return SignalResult(
            signal_id="alliance_membership",
            score=50,
            confidence=0.0,
            error=str(e)
        )
```

## Coverages

Seven coverage domains, each with YAML config:

| Coverage | Config File | Key Signal Focus |
|----------|-------------|------------------|
| Aerospace | `aerospace/config.yaml` | Safety record, regulatory compliance, fleet quality |
| Cyber | `cyber/config.yaml` | Technical infrastructure, security posture |
| D&O | `do/config.yaml` | Corporate governance, regulatory filings |
| Energy | `energy/config.yaml` | Operational safety, environmental compliance |
| Financial Institutions | `fi/config.yaml` | Regulatory standing, financial stability |
| Marine | `marine/config.yaml` | Vessel tracking, classification society, port state control |
| Professional Indemnity | `pi/config.yaml` | Professional certifications, claims history |

## Scoring Flow

```
1. Load config for coverage/configuration (e.g., aerospace_general)

2. For each signal_feature in config:
   - Call inference_utility_function(entity_id)
   - Get score (0-100)
   - Apply weight within signal_group
   - Check score_condition bands for overrides

3. For each signal_group:
   - Weighted sum of feature scores → group score
   - Apply group weight to composite
   - Check group score_condition bands for overrides

4. Calculate composite score (0-1000):
   composite = sum(group_score * group_weight) * 10

5. Determine tier from tier_thresholds

6. For each categorical_group:
   - Call inference_utility_function(entity_id)
   - Get category (e.g., "MAJOR_AIRLINE")
   - Look up modifier from categorical_features

7. Calculate premium:
   base_premium = tier.premium
   final_premium = base_premium * product(all_modifiers)
```

## Data Structures

```python
@dataclass
class ExtractorResult:
    success: bool
    data: Dict[str, Any]
    source: str
    extracted_at: datetime
    error: Optional[str] = None

@dataclass
class AggregatorResult:
    success: bool
    data: Dict[str, Any]
    aggregated_at: datetime
    error: Optional[str] = None

@dataclass
class CategorizerResult:
    score: Optional[float] = None      # 0-100 for signals
    category: Optional[str] = None     # For categorical features
    confidence: Optional[float] = None # 0-1
    error: Optional[str] = None

@dataclass
class SignalResult:
    signal_id: str
    score: float
    confidence: float
    raw_data: Optional[Dict] = None
    aggregated_data: Optional[Dict] = None
    metadata: Optional[Dict] = None
    error: Optional[str] = None

@dataclass
class ModelResult:
    entity_id: str
    configuration: str
    composite_score: float
    tier: int
    tier_label: str
    signal_results: Dict[str, SignalResult]
    categorical_results: Dict[str, str]
    modifiers: Dict[str, float]
    base_premium: float
    final_premium: float
    confidence: float
    overrides: List[Dict]  # Any triggered score_condition bands
    timestamp: datetime
```

## File Structure

```
technical_pricing/
├── coverages/
│   ├── aerospace/
│   │   └── config.yaml
│   ├── cyber/
│   │   └── config.yaml
│   ├── do/
│   │   └── config.yaml
│   ├── energy/
│   │   └── config.yaml
│   ├── fi/
│   │   └── config.yaml
│   ├── marine/
│   │   └── config.yaml
│   └── pi/
│       └── config.yaml
├── signals/
│   ├── __init__.py
│   ├── base.py              # Base classes: BaseExtractor, BaseAggregator, etc.
│   ├── types.py             # Data structures: ExtractorResult, SignalResult, etc.
│   ├── extractors/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   └── stubs/           # STUB implementations by domain
│   │       ├── aerospace.py
│   │       ├── cyber.py
│   │       └── ...
│   ├── aggregators/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   └── implementations/ # Production aggregators
│   │       ├── aerospace.py
│   │       └── ...
│   ├── categorizers/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   └── types/           # Reusable categorizer types
│   │       ├── threshold_bucket.py
│   │       ├── boolean_score.py
│   │       ├── weighted_composite.py
│   │       └── category_mapper.py
│   └── inference/
│       ├── __init__.py
│       ├── registry.py      # Maps function names to implementations
│       └── functions/       # Inference functions by domain
│           ├── aerospace.py
│           └── ...
├── model/
│   ├── __init__.py
│   ├── config_loader.py     # Load and parse YAML configs
│   ├── scorer.py            # Composite scoring logic
│   └── pricer.py            # Premium calculation
└── tests/
    ├── test_extractors.py
    ├── test_aggregators.py
    ├── test_categorizers.py
    ├── test_inference.py
    └── test_model.py        # End-to-end with test_profiles from config
```

## Implementation Checklist

### Phase 1: Foundation
- [ ] Base classes (BaseExtractor, BaseAggregator, BaseCategorizer)
- [ ] Data structures (ExtractorResult, AggregatorResult, CategorizerResult, SignalResult)
- [ ] Config loader (parse YAML, validate structure)
- [ ] Inference registry (map function names to implementations)

### Phase 2: Categorizers (Reusable)
- [ ] ThresholdBucketCategorizer
- [ ] BooleanScoreCategorizer
- [ ] WeightedCompositeCategorizer
- [ ] CategoryMapperCategorizer
- [ ] RangeMapperCategorizer

### Phase 3: One Coverage End-to-End (e.g., Aerospace)
- [ ] All stub extractors for aerospace signals
- [ ] All aggregators for aerospace signals
- [ ] All inference functions for aerospace signals
- [ ] Categorical inference functions
- [ ] Model scorer integration
- [ ] Test with aerospace test_profiles

### Phase 4: Remaining Coverages
- [ ] Cyber
- [ ] D&O
- [ ] Energy
- [ ] Financial Institutions
- [ ] Marine
- [ ] Professional Indemnity

### Phase 5: Integration
- [ ] End-to-end pipeline testing
- [ ] Confidence scoring
- [ ] Override/referral handling
- [ ] Premium calculation with modifiers

## Critical Rules

1. **YAML is truth**: Never hardcode weights, thresholds, modifiers, or tier definitions
2. **Extractors are stubs**: Randomized but structurally realistic
3. **Aggregators are production**: Must handle real data when extractors upgraded
4. **Categorizers are reusable**: Parameterized, not signal-specific logic
5. **Inference functions are glue**: One per YAML `inference_utility_function`
6. **Test profiles validate**: Every config has test scenarios - use them
7. **Scores are 0-100**: Individual signals
8. **Composite is 0-1000**: Weighted sum * 10
9. **Confidence matters**: Track data availability throughout pipeline

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
│  │Raw data  │    │Structure/│    │Score or   │    │Orchestrate│ │
│  │from APIs │    │normalize │    │category   │    │pipeline   │ │
│  └──────────┘    └──────────┘    └───────────┘    └───────── ─┘ │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      MODEL OUTPUT                               │
│  Composite score (0-1000) → Tier (1-5) → Premium + Modifiers    │
└─────────────────────────────────────────────────────────────────┘
```

## Implementation Status

### ✅ Phase 1: Foundation (COMPLETE)

All base infrastructure is built and tested:

| Component | File | Status |
|-----------|------|--------|
| Core Data Types | `signals/types.py` | ✅ Complete |
| Abstract Base Classes | `signals/base.py` | ✅ Complete |
| StubExtractor (with TTL caching) | `signals/extractors/base.py` | ✅ Complete |
| ProductionAggregator | `signals/aggregators/base.py` | ✅ Complete |
| ProductionCategorizer | `signals/categorizers/base.py` | ✅ Complete |
| Inference Registry | `signals/inference/registry.py` | ✅ Complete |

**Key Features Implemented:**
- TTL-aware caching at extractor level (configurable per data source)
- Source tracking in AggregatorResult
- Execution time tracking in SignalResult
- Skipped/not-applicable states for categorizers
- Comprehensive helper utilities for all base classes

### ✅ Phase 2: Reusable Categorizer Types (COMPLETE)

12 parameterized categorizer types ready for use:

**Score Categorizers (return 0-100):**
| Categorizer | Purpose | File |
|-------------|---------|------|
| `ThresholdBucketCategorizer` | Map numeric values to scores via thresholds | `threshold_bucket.py` |
| `InverseThresholdBucketCategorizer` | Higher input = lower score | `threshold_bucket.py` |
| `BooleanScoreCategorizer` | Map boolean to score | `boolean_score.py` |
| `PresenceScoreCategorizer` | Score based on value presence/absence | `boolean_score.py` |
| `MultiBooleanScoreCategorizer` | Weighted scoring of multiple booleans | `boolean_score.py` |
| `WeightedCompositeCategorizer` | Combine multiple fields with weights | `weighted_composite.py` |
| `LinearScaleCategorizer` | Scale numeric value to score range | `weighted_composite.py` |
| `AverageScoreCategorizer` | Average multiple score fields | `weighted_composite.py` |

**Category Categorizers (return string):**
| Categorizer | Purpose | File |
|-------------|---------|------|
| `CategoryMapperCategorizer` | Rule-based category assignment | `category_mapper.py` |
| `DirectMappingCategorizer` | Simple value-to-category mapping | `category_mapper.py` |
| `RangeCategorizer` | Map numeric ranges to categories | `category_mapper.py` |
| `MultiFieldCategorizer` | Category from multiple fields with priority | `category_mapper.py` |

### 🔲 Phase 3: Coverage Implementation (NOT STARTED)

One end-to-end coverage (e.g., Aerospace) needs:
- [ ] Stub extractors for all signals
- [ ] Aggregators for all signals
- [ ] Inference functions for all signals
- [ ] Categorical inference functions
- [ ] Integration testing with test_profiles

### 🔲 Phase 4: Remaining Coverages (NOT STARTED)

- [ ] Cyber
- [ ] D&O
- [ ] Energy
- [ ] Financial Institutions
- [ ] Marine
- [ ] Professional Indemnity

### 🔲 Phase 5: Model Integration (NOT STARTED)

- [ ] Config loader (parse YAML, validate structure)
- [ ] Model scorer (composite scoring logic)
- [ ] Model pricer (premium calculation with modifiers)
- [ ] End-to-end pipeline testing

---

## YAML Config Structure

**CRITICAL: The YAML config is the single source of truth. Never hardcode values that exist in config.**

```yaml
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

### 1. Extractors (STUB - TTL-Aware Caching)

**Purpose**: Fetch raw data from external sources (APIs, databases, FTP).

**Implementation Status**: STUB only. Return randomized but structurally realistic data.

**TTL Configuration**: Each extractor defines `DEFAULT_TTL_SECONDS` based on data freshness needs:
- `TTL_REALTIME` (60s): Live prices, vessel positions
- `TTL_FREQUENT` (300s): Frequently updated feeds
- `TTL_HOURLY` (3600s): General API data
- `TTL_DAILY` (86400s): Regulatory status, certifications
- `TTL_WEEKLY` (604800s): Corporate structure
- `TTL_MONTHLY` (2592000s): Historical records

**Template**:
```python
class AllianceMembershipExtractor(StubExtractor):
    """
    STUB: Simulates airline alliance membership API.
    Real implementation would query IATA/alliance databases.
    """
    SOURCE_NAME = "iata_alliance_registry"
    DEFAULT_TTL_SECONDS = StubExtractor.TTL_DAILY  # Alliance data rarely changes
    
    def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
        # Simulate API response structure
        data = {
            "query_timestamp": utcnow().isoformat(),
            "entity_id": entity_id,
            "data": {
                "alliance_code": self._random_choice([None, "STAR", "OW", "ST"]),
                "membership_status": self._random_choice(["ACTIVE", "PENDING", "NONE"]),
                "join_date": self._random_date_or_none(years_back=10),
                "tier_level": self._random_choice(["FOUNDING", "FULL", "ASSOCIATE", None]),
            }
        }
        return self._create_success_result(data)
```

### 2. Aggregators (PRODUCTION READY)

**Purpose**: Transform raw extractor data into normalized structure ready for scoring.

**Implementation Status**: Production ready. No changes needed when extractors become real.

**Template**:
```python
class AllianceMembershipAggregator(ProductionAggregator):
    """
    Transforms raw alliance data into normalized scoring structure.
    
    Expected input (from AllianceMembershipExtractor):
        {"data": {"alliance_code": str | None, "membership_status": str, ...}}
    
    Output:
        {"has_alliance": bool, "alliance_tier": int, "membership_years": int, ...}
    """
    
    ALLIANCE_TIERS = {"STAR": 3, "OW": 3, "ST": 3, None: 0}
    
    def aggregate(self, extractor_results: List[ExtractorResult]) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        
        alliance_code = raw.get("alliance_code")
        membership_status = raw.get("membership_status", "NONE")
        
        has_alliance = alliance_code is not None and membership_status == "ACTIVE"
        alliance_tier = self.ALLIANCE_TIERS.get(alliance_code, 0) if has_alliance else 0
        membership_years = self._calculate_years_since(raw.get("join_date"))
        is_founding = raw.get("tier_level") == "FOUNDING"
        
        return self._create_success_result({
            "has_alliance": has_alliance,
            "alliance_tier": alliance_tier,
            "membership_years": membership_years,
            "is_founding_member": is_founding,
        }, extractor_results)
```

### 3. Categorizers (PRODUCTION READY - 12 Types Available)

**Purpose**: Apply scoring/categorization logic to produce final values.

**Implementation Status**: Production ready. Use the 12 reusable types with params.

**Usage Pattern**:
```python
# For scoring signals - use appropriate categorizer type with params
categorizer = WeightedCompositeCategorizer()
result = categorizer.categorize(
    aggregated_data,
    params={
        "components": [
            {"field": "alliance_tier", "weight": 0.5, "scale": 33.33},
            {"field": "membership_years", "weight": 0.3, "scale": 5, "max": 100},
            {"field": "is_founding_member", "weight": 0.2, "scale": 100},
        ]
    }
)

# For categorical features - use category mapper
categorizer = RangeCategorizer()
result = categorizer.categorize(
    aggregated_data,
    params={
        "value_field": "fleet_count",
        "ranges": [
            {"min": 150, "category": "MAJOR"},
            {"min": 51, "max": 150, "category": "LARGE"},
            {"min": 21, "max": 51, "category": "MEDIUM"},
        ],
        "default_category": "SMALL"
    }
)
```

### 4. Inference Functions (PRODUCTION READY)

**Purpose**: Orchestrate the full pipeline for ONE specific signal or categorical feature.

**Implementation Status**: Registry is ready. Functions registered per coverage.

**Template**:
```python
@register_inference_function("alliance_membership_basefunction")
def alliance_membership_basefunction(entity_id: str, context: InferenceContext) -> SignalResult:
    """
    Inference function for alliance_membership signal.
    
    Maps to: signal_features.network_authority.alliance_membership
    YAML ref: inference_utility_function: alliance_membership_basefunction
    
    Pipeline:
        AllianceMembershipExtractor → AllianceMembershipAggregator → WeightedCompositeCategorizer
    """
    import time
    start_time = time.time()
    
    try:
        # 1. Extract (with TTL caching via context)
        extractor = AllianceMembershipExtractor()
        extract_result = extractor.extract(entity_id, context)
        
        if not extract_result.success:
            return SignalResult(
                signal_id="alliance_membership",
                score=50,
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
                    {"field": "membership_years", "weight": 0.3, "scale": 5, "max": 100},
                    {"field": "is_founding_member", "weight": 0.2, "scale": 100},
                ]
            }
        )
        
        execution_time = (time.time() - start_time) * 1000
        
        return SignalResult(
            signal_id="alliance_membership",
            score=cat_result.score,
            confidence=cat_result.confidence or 1.0,
            raw_data=extract_result.data,
            aggregated_data=agg_result.data,
            execution_time_ms=execution_time,
            metadata={
                "extractor": "AllianceMembershipExtractor",
                "aggregator": "AllianceMembershipAggregator",
                "categorizer": "WeightedCompositeCategorizer",
                "from_cache": extract_result.from_cache,
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
   - Call inference_utility_function(entity_id, context)
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
   - Call inference_utility_function(entity_id, context)
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
    ttl_seconds: int = 3600           # NEW: TTL for caching
    expires_at: Optional[datetime]     # NEW: Computed expiration
    from_cache: bool = False           # NEW: Cache hit indicator
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class AggregatorResult:
    success: bool
    data: Dict[str, Any]
    aggregated_at: datetime
    sources: Optional[List[str]]       # NEW: Contributing sources
    error: Optional[str] = None
    source_extractions: int = 1
    warnings: Optional[List[str]] = None

@dataclass
class CategorizerResult:
    score: Optional[float] = None      # 0-100 for signals
    category: Optional[str] = None     # For categorical features
    confidence: Optional[float] = None # 0-1
    skipped: bool = False              # NEW: Not applicable state
    error: Optional[str] = None
    reasoning: Optional[str] = None

@dataclass
class SignalResult:
    signal_id: str
    score: Optional[float] = None
    category: Optional[str] = None
    confidence: float = 1.0
    execution_time_ms: Optional[float] # NEW: Performance tracking
    skipped: bool = False              # NEW: Not applicable state
    raw_data: Optional[Dict] = None
    aggregated_data: Optional[Dict] = None
    metadata: Optional[Dict] = None
    error: Optional[str] = None

@dataclass
class InferenceContext:
    configuration: Dict[str, Any]
    coverage: str
    config_name: str
    cache: Optional[Dict[str, ExtractorResult]]  # TTL-aware cache
    cache_stats: Optional[Dict[str, int]]        # hits, misses, expired, stores
```

## File Structure

```
technical_pricing/
├── __init__.py                          ✅
├── coverages/
│   ├── aerospace/
│   │   └── config.yaml                  🔲
│   ├── cyber/
│   │   └── config.yaml                  🔲
│   └── ... (other coverages)
├── signals/
│   ├── __init__.py                      ✅
│   ├── base.py                          ✅ Base classes
│   ├── types.py                         ✅ Data structures
│   ├── extractors/
│   │   ├── __init__.py                  ✅
│   │   ├── base.py                      ✅ StubExtractor + utilities
│   │   └── stubs/
│   │       ├── __init__.py              ✅
│   │       ├── aerospace.py             🔲
│   │       └── ...
│   ├── aggregators/
│   │   ├── __init__.py                  ✅
│   │   ├── base.py                      ✅ ProductionAggregator + utilities
│   │   └── implementations/
│   │       ├── __init__.py              ✅
│   │       ├── aerospace.py             🔲
│   │       └── ...
│   ├── categorizers/
│   │   ├── __init__.py                  ✅
│   │   ├── base.py                      ✅ ProductionCategorizer + utilities
│   │   └── types/
│   │       ├── __init__.py              ✅
│   │       ├── threshold_bucket.py      ✅
│   │       ├── boolean_score.py         ✅
│   │       ├── weighted_composite.py    ✅
│   │       └── category_mapper.py       ✅
│   └── inference/
│       ├── __init__.py                  ✅
│       ├── registry.py                  ✅
│       └── functions/
│           ├── __init__.py              ✅
│           ├── aerospace.py             🔲
│           └── ...
├── model/
│   ├── __init__.py                      🔲
│   ├── config_loader.py                 🔲
│   ├── scorer.py                        🔲
│   └── pricer.py                        🔲
└── tests/
    ├── test_extractors.py               🔲
    ├── test_aggregators.py              🔲
    ├── test_categorizers.py             🔲
    ├── test_inference.py                🔲
    └── test_model.py                    🔲
```

Legend: ✅ Complete | 🔲 Not Started

## Critical Rules

1. **YAML is truth**: Never hardcode weights, thresholds, modifiers, or tier definitions
2. **Extractors are stubs**: Randomized but structurally realistic, with TTL caching
3. **Aggregators are production**: Must handle real data when extractors upgraded
4. **Categorizers are reusable**: Use the 12 parameterized types, don't create signal-specific logic
5. **Inference functions are glue**: One per YAML `inference_utility_function`
6. **Test profiles validate**: Every config has test scenarios - use them
7. **Scores are 0-100**: Individual signals
8. **Composite is 0-1000**: Weighted sum * 10
9. **Confidence matters**: Track data availability throughout pipeline
10. **TTL varies by source**: Set appropriate `DEFAULT_TTL_SECONDS` per extractor

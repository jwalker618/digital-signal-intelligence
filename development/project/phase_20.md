# Phase 20: Configuration Architecture & Organisational Graph

## Purpose

Restructure the DSI configuration architecture to:
1. **Unify signal collection** - signals defined once, interpreted for risk, loss, and exposure
2. **Establish the Organisational Graph schema** - the encoder for the World Model
3. **Standardise pricing integration** - consistent banding approach for loss and exposure
4. **Separate configuration from analysis** - empirical parameters derived externally

This phase establishes the configuration foundation required for implementing Phases 16 (Loss Correlation) and 17 (Exposure Shadow), and introduces the Organisational Graph from the Vision Paper.

## Status

✅ **Structure Agreed** - Master config layout finalised with all structural decisions

## Relationship to Other Phases

```
Phase 18 (Architecture)     Phase 19 (Demo)
        │                        │
        │                        │ (parallel)
        ▼                        ▼
┌───────────────────────────────────────────────────────────────┐
│                      PHASE 20                                  │
│         Configuration Architecture & Org Graph                 │
│                                                                │
│  - Unified signal architecture (risk/loss/exposure)            │
│  - source: score vs source: metadata.field pattern             │
│  - Organisational Graph schema                                 │
│  - Pricing integration standardisation                         │
└───────────────────────────────────────────────────────────────┘
        │
        │ enables
        ▼
┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│   Phase 21    │    │   Phase 22    │    │   Phase 23    │
│ Loss Layer    │    │ Exposure Layer│    │  Org Graph    │
│Implementation │    │Implementation │    │   Runtime     │
└───────────────┘    └───────────────┘    └───────────────┘
```

## Key Deliverables

### 1. Master Config Layout

**File**: `coverages/cyber/master_config_layout.yaml`

Defines the complete structure for coverage configurations with all structural decisions:

| Structural Principle | Description |
|---------------------|-------------|
| Unified signal registry | Signals defined once with `group_id` reference |
| `source: score` (default) | Uses 0-100 inference return |
| `source: metadata.field` | Uses inference metadata with bands/categories mapping |
| Categorical groups | Apply modifiers (`applied:`), not scores |
| `score_condition` | Applies actions/overrides at signal or group level |
| `proxy_tier` | At signal level (DIRECT_OBSERVABLE, INFERRED_PROXY, COHORT_INFERENCE) |
| `group_id` | snake_case naming consistently |

### 2. Unified Signal Architecture

Signals are defined once with dimension-specific subsections:

```yaml
signal_registry:
  - id: "{signal_id}"
    inference_utility_function: "{function_name}"
    proxy_tier: INFERRED_PROXY
    three_layer_assessment:
      group_id: technical_infrastructure    # Same group for all dimensions

      risk:
        # source: score                     # DEFAULT - omit if using score
        correlation_direction: positive
        weight: 0.10

      loss:
        severity:
          correlation_direction: negative
          weight: 0.35
        frequency:
          source: metadata.incident_count   # Can use metadata
          bands:
            - {min: 0, max: 0, score: 95}
            - {min: 1, max: 2, score: 60}
            - {min: 3, max: null, score: 25}
          weight: 0.35

      exposure:
        size:
          source: metadata.resource_count
          bands:
            - {min: 0, max: 100, score: 20}
            - {min: 101, max: 500, score: 40}
            - {min: 501, max: null, score: 80}
          weight: 0.08
        complexity:
          source: metadata.provider_type
          categories:
            - {match: "SINGLE", score: 30}
            - {match: "MULTI", score: 70}
            - {match: null, score: 50}      # default/catch-all
          weight: 0.06
```

**Key Decisions**:
- `source: score` is the default; only specify when using metadata
- `source: metadata.*` requires `bands:` (numeric) or `categories:` (text)
- Bands/categories return `score` values (0-100), not modifiers
- Exposure uses the SAME groups as risk/loss (not separate exposure groups)
- Modifiers come from `score_condition`, not from bands

### 3. Metadata Source Patterns

When using inference metadata instead of score:

**Numeric Metadata with Bands**:
```yaml
source: metadata.resource_count
bands:
  - min: 0
    max: 100
    score: 20                 # Score contribution (0-100)
  - min: 101
    max: 500
    score: 40
  - min: 501
    max: null                 # null = no upper limit
    score: 80
```

**Text Metadata with Categories**:
```yaml
source: metadata.dominant_region
categories:
  - match: "US"
    score: 50
  - match: "EU"
    score: 70                 # GDPR complexity
  - match: null               # null = default/catch-all
    score: 60
```

### 4. Organisational Graph Schema

**File**: `schemas/organisational_graph.yaml`

Organisation-wide schema defining the encoder for the World Model:

| Component | Contents |
|-----------|----------|
| **Node Types** | organisation, asset, partner, person, process, jurisdiction |
| **Edge Types** | dependency, trust, data_flow, ownership, operates_in, employment |
| **Derivatives** | entropy, velocity, drift, concentration, fragility |
| **Proxy Tiers** | DIRECT_OBSERVABLE, INFERRED_PROXY, COHORT_INFERENCE |
| **Graph Operations** | authority_propagation, risk_propagation, exposure_aggregation |

**Ownership**: Data Architecture / Ontology Team (coverage-agnostic)

### 5. Groups Structure

**Categorical Groups** - Apply pricing modifiers (not scores):
```yaml
groups:
  categories:
    - id: "industry_classification"
      label: "Industry Classification"
      impact: "MODIFIER"              # Underlying signals have applied: values
      default_cat: "OTHER"
```

**Three-Layer Assessment Groups** - Aggregate signal scores:
```yaml
groups:
  three_layer_assessment:
    - id: "technical_infrastructure"
      label: "Technical Infrastructure"
      risk:
        weight: 0.35                  # Group weights sum to 1.0
        score_condition:
          - {max: 30, action: "DECLINE", note: "..."}
      loss:
        weight: 0.35
      exposure:
        weight: 0.35                  # Same groups for all dimensions
```

### 6. Pricing Integration

**Loss Tier Bands**:
```yaml
loss_tier_bands:
  bands:
    - id: 1
      label: "VERY_LOW"
      interpretation:
        bands: {min: 0, max: 20}
        application:
          frequency_weight: 0.6
          severity_weight: 0.4
          floor: 0.55
          cap: 0.75
```

**Exposure Tier Bands**:
```yaml
exposure:
  size:
    weight: 0.60
    bands:
      - id: 1
        label: "MICRO"
        interpretation:
          bands: {min: 0, max: 20}
          application:
            applied: 0.50
            implied_thresholds: [0, 1000000]
  complexity:
    weight: 0.40
    bands:
      - ...
```

## Architectural Decisions

### Decision 1: Unified vs Separate Signal Definitions

**Decision**: Unified - signals defined once in `signal_registry`

**Rationale**:
- Prevents signal definition drift between layers
- Single inference function per signal
- Clear visibility into which signals contribute to which dimensions
- Enables "collect once, analyse many ways" pattern

### Decision 2: source: score vs source: metadata.field

**Decision**: Explicit source binding with default to score

**Rationale**:
- Makes clear when score vs metadata is used
- Prevents need for separate inference functions for exposure/loss
- Metadata sources require explicit band/category mapping
- Keeps normalization logic in inference functions (not config)

### Decision 3: Bands/Categories Return Scores, Not Modifiers

**Decision**: Bands/categories return `score:` (0-100), not `applied:`

**Rationale**:
- Scores aggregate within groups before tier banding
- Tier bands then apply modifiers based on combined group score
- `score_condition` handles action/modifier application
- Clean separation: signals contribute scores, tiers apply modifiers

### Decision 4: Exposure Uses Same Groups as Risk/Loss

**Decision**: No separate exposure_magnitude/exposure_complexity groups

**Rationale**:
- Maintains consistency across all three dimensions
- Signals contribute to network_authority, technical_infrastructure, etc. for all dimensions
- Exposure size/complexity are sub-dimensions within signals, not separate group hierarchies
- Reduces configuration complexity

### Decision 5: Normaliser at Inference Function Level

**Decision**: Remove `normaliser` from YAML; handled by inference functions

**Rationale**:
- Inference functions return normalized 0-100 scores
- Analysis parameters (log scale, percentile bins) are empirically derived
- Config defines WHAT to use; inference defines HOW to normalize
- Exception: categorical_map patterns captured as bands/categories in metadata sources

### Decision 6: Organisational Graph in Separate Schema

**Decision**: Separate schema file with coverage config bindings

**Rationale**:
- Graph schema is coverage-agnostic (same nodes/edges for cyber, D&O, marine)
- Different specialists own schema vs config (data architects vs actuaries)
- Different change cadences (schema rarely, config frequently)
- Enables cross-coverage consistency

## Files Changed

| File | Change |
|------|--------|
| `coverages/cyber/master_config_layout.yaml` | **UPDATED** - Complete annotated structure |
| `coverages/cyber/config_rework_v2.yaml` | Working implementation (to be updated) |
| `schemas/organisational_graph.yaml` | Graph schema |
| `docs/Configuration Architecture.md` | Documentation |

## Implementation Tasks

| Task | Status |
|------|--------|
| Agree unified signal registry structure | ✅ Complete |
| Agree source: score vs source: metadata pattern | ✅ Complete |
| Agree bands/categories return scores not modifiers | ✅ Complete |
| Agree exposure uses same groups as risk/loss | ✅ Complete |
| Agree normaliser at inference function level | ✅ Complete |
| Agree proxy_tier at signal level | ✅ Complete |
| Agree group_id snake_case naming | ✅ Complete |
| Agree loss supports metadata sources | ✅ Complete |
| Create complete master_config_layout.yaml | ✅ Complete |
| Create organisational_graph.yaml schema | ✅ Complete |
| Create Configuration Architecture documentation | ✅ Complete |
| Apply structure to config_rework_v2.yaml | ⏳ Pending |
| Apply structure to all coverage YAMLs | ⏳ Pending |

## Outstanding Items (Next Steps)

| Item | Target | Notes |
|------|--------|-------|
| Apply agreed structure to config_rework_v2.yaml | Phase 20b | Implement all signals with new pattern |
| Validate weights sum to 1.0 within groups | Phase 20b | Automated validation |
| Apply structure to all coverage YAMLs | Phase 20b | Systematic application |
| Implement loss correlation runtime | Phase 21 | Uses config structure from this phase |
| Implement exposure scoring runtime | Phase 22 | Uses config structure from this phase |
| Implement graph bindings | Phase 23 | Reference schema from coverage |

## Verification

After implementation:

1. **Config Structure**: Verify `config_rework_v2.yaml` follows master layout
2. **Source Binding**: Verify all metadata sources have bands or categories
3. **Weight Validation**: Verify weights sum to 1.0 within groups per dimension
4. **Score Returns**: Verify bands/categories use `score:` not `applied:`
5. **Group Consistency**: Verify exposure uses same groups as risk/loss
6. **Schema Validation**: Verify all YAML files are valid

## Summary of Agreed Structure

```
signal_registry:
  - id: signal_id
    inference_utility_function: function_name
    proxy_tier: DIRECT_OBSERVABLE | INFERRED_PROXY | COHORT_INFERENCE

    # For categorical signals (modifiers)
    categories:
      group_id: category_group
      features:
        - {cat: "CODE", label: "Label", applied: 1.15}

    # For scored signals (scores)
    three_layer_assessment:
      group_id: assessment_group

      risk:
        source: score | metadata.field     # default: score
        bands: [...] | categories: [...]   # if metadata source
        correlation_direction: positive | negative
        weight: float
        score_condition: [...]             # optional actions

      loss:
        severity: {source, bands/categories, correlation_direction, weight}
        frequency: {source, bands/categories, correlation_direction, weight}

      exposure:
        size: {source, bands/categories, correlation_direction, weight}
        complexity: {source, bands/categories, correlation_direction, weight}
```

---

**This phase establishes the configuration foundation for the World Model architecture described in the Vision Paper.**

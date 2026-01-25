# Phase 20: Configuration Architecture & Organisational Graph

## Purpose

Restructure the DSI configuration architecture to:
1. **Unify signal collection** - signals defined once, interpreted for risk, loss, and exposure
2. **Establish the Organisational Graph schema** - the encoder for the World Model
3. **Standardise pricing integration** - consistent banding approach for loss and exposure
4. **Separate configuration from analysis** - empirical parameters derived externally

This phase establishes the configuration foundation required for implementing Phases 16 (Loss Correlation) and 17 (Exposure Shadow), and introduces the Organisational Graph from the Vision Paper.

## Status

✅ **Complete** - Configuration restructuring and schema creation done

## Relationship to Other Phases

```
Phase 18 (Architecture)     Phase 19 (Demo)
        │                        │
        │                        │ (parallel)
        ▼                        ▼
┌───────────────────────────────────────────────────────────┐
│                      PHASE 20                              │
│         Configuration Architecture & Org Graph             │
│                                                            │
│  - Unified signal architecture (risk/loss/exposure)        │
│  - Organisational Graph schema                             │
│  - Pricing integration standardisation                     │
│  - Analysis layer separation                               │
└───────────────────────────────────────────────────────────┘
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

### 1. Unified Signal Architecture

**File**: `coverages/cyber/config_rework.yaml`

Signals are now defined once with dimension-specific subsections:

```yaml
signal_features:
  technical_infrastructure:
    - id: "tls_score"
      inference_utility_function: tls_configuration_basefunction
      risk:
        weight: 0.12
      loss:
        weight: 0.25
        correlation_type: frequency
        correlation_direction: negative
      exposure:  # Optional - only if signal contributes to exposure
        weight: 0.04
        proxy_tier: INFERRED_PROXY
        group: digital_footprint
```

**Benefits**:
- Single source of truth for signal definitions
- One inference function call serves all dimensions
- Consistent monitoring across risk, loss, and exposure
- Clear which signals contribute to which dimensions

### 2. Organisational Graph Schema

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

### 3. Pricing Integration Standardisation

Both loss and exposure now use consistent banding approach:

```yaml
loss_integration:
  method: multiplicative
  frequency_weight: 0.6
  severity_weight: 0.4
  band_constraints:
    elevated:
      floor: 1.10
      cap: 1.30

exposure_integration:
  method: multiplicative
  exposure_weight: 0.60
  complexity_weight: 0.40
  band_constraints:
    large:
      floor: 1.30
      cap: 1.70
```

**Calculation**: `(component_1 × weight_1) + (component_2 × weight_2)`, constrained by band floor/cap

### 4. Exposure Scoring Restructure

Replaced `exposure_shadow` (inline signal definitions) with `exposure_scoring` (grouping references):

**Before**:
```yaml
exposure_shadow:
  exposure_groups:
    - name: digital_footprint
      features:
        - id: dns_complexity      # Defined inline - duplicates signal_features
          weight: 0.25
```

**After**:
```yaml
signal_features:
  exposure_magnitude:
    - id: "dns_complexity"        # Defined once with inference function
      inference_utility_function: dns_complexity_basefunction
      exposure:
        weight: 0.08
        group: digital_footprint

exposure_scoring:
  magnitude_groups:
    - name: digital_footprint
      signals: [dns_complexity, subdomain_count, ...]  # References to signals
```

### 5. Documentation

**File**: `docs/Configuration Architecture.md`

Comprehensive documentation covering:
- Layered architecture (schema → config → analysis → model)
- Three dimensions (risk, loss, exposure)
- Pricing integration patterns
- Organisational graph integration
- Analysis layer separation

## Architectural Decisions

### Decision 1: Unified vs Separate Signal Definitions

**Decision**: Unified - signals defined once in `signal_features`

**Rationale**:
- Prevents signal definition drift between layers
- Single inference function per signal
- Clear visibility into which signals contribute to which dimensions
- Enables "collect once, analyse many ways" pattern

### Decision 2: Organisational Graph in Coverage Config vs Separate

**Decision**: Separate schema file with coverage config bindings

**Rationale**:
- Graph schema is coverage-agnostic (same nodes/edges for cyber, D&O, marine)
- Different specialists own schema vs config (data architects vs actuaries)
- Different change cadences (schema rarely, config frequently)
- Enables cross-coverage consistency

### Decision 3: Analysis Parameters in Config vs External

**Decision**: External - analysis outputs stored separately

**Rationale**:
- `lag_months`, normalizer coefficients are empirically derived
- Separation enables actuarial ownership of analysis layer
- Config defines WHAT to correlate; analysis determines HOW
- Versioned analysis outputs enable model reproducibility

### Decision 4: Exposure Shadow as Separate Section vs Integrated

**Decision**: Integrated - exposure signals in `signal_features`

**Rationale**:
- Consistent with risk and loss pattern
- Enables signal reuse (e.g., `cloud_infrastructure` for both risk and exposure)
- Single source of truth for inference functions
- Grouping done via references, not inline definitions

## Files Changed

| File | Change |
|------|--------|
| `coverages/cyber/config_rework.yaml` | Unified signal architecture, exposure restructure |
| `schemas/organisational_graph.yaml` | **NEW** - Graph schema |
| `docs/Configuration Architecture.md` | **NEW** - Documentation |

## New Signal Groups Added

| Group | Purpose | Signal Count |
|-------|---------|--------------|
| `exposure_magnitude` | TIV proxy signals | 15 signals |
| `exposure_complexity` | Complexity proxy signals | 12 signals |

## Implementation Tasks

| Task | Status |
|------|--------|
| Add `exposure:` subsection support to signal_features | ✅ Complete |
| Create exposure_magnitude signal group | ✅ Complete |
| Create exposure_complexity signal group | ✅ Complete |
| Add 27 new exposure signals with inference functions | ✅ Complete |
| Update cloud_infrastructure with exposure subsection | ✅ Complete |
| Replace exposure_shadow with exposure_scoring | ✅ Complete |
| Implement banding-based pricing integration | ✅ Complete |
| Create organisational_graph.yaml schema | ✅ Complete |
| Create Configuration Architecture documentation | ✅ Complete |
| Add loss section to network_authority signals | ✅ Complete |
| Fix YAML syntax errors in propensity_band | ✅ Complete |

## Outstanding Items (Deferred to Future Phases)

| Item | Target Phase | Notes |
|------|--------------|-------|
| Implement loss correlation runtime | Phase 21 | Uses config structure from this phase |
| Implement exposure scoring runtime | Phase 22 | Uses config structure from this phase |
| Implement graph bindings in coverage config | Phase 23 | Reference schema from coverage |
| Create analysis output template | Phase 21 | Structure for empirical parameters |
| Update test_profiles with exposure signals | TBD | Test values for new signals |
| Validate YAML with linter | TBD | Syntax validation |

## Verification

After implementation:

1. **Config Structure**: Verify `config_rework.yaml` passes YAML linting
2. **Signal Completeness**: Verify all exposure signals have inference functions
3. **Weight Validation**: Verify weights sum to 1.0 within groups
4. **Schema Validation**: Verify `organisational_graph.yaml` is valid YAML
5. **Documentation**: Verify all sections of Configuration Architecture.md are accurate

## Next Steps

### Phase 21: Loss Correlation Layer Implementation

Implement the runtime components for loss correlation using the unified signal architecture:
- Loss propensity scorer using `loss:` subsections from signals
- Pricing integration using `loss_integration` config
- Referral rules from `propensity_band` auto-apply conditions

### Phase 22: Exposure Shadow Layer Implementation

Implement the runtime components for exposure estimation using the unified signal architecture:
- Exposure magnitude calculator using `exposure_magnitude` signals
- Complexity calculator using `exposure_complexity` signals
- Pricing integration using `exposure_integration` config

### Phase 23: Organisational Graph Runtime

Implement graph instantiation and operations:
- Node creation from signal data
- Edge inference from relationships
- Derivative calculation (entropy, velocity, drift)
- Authority propagation (PageRank-style)

---

**This phase establishes the configuration foundation for the World Model architecture described in the Vision Paper.**

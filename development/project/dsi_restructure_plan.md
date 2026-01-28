# DSI Comprehensive Restructure Plan

**Version:** 1.0
**Date:** 2026-01-28
**Status:** DRAFT - Awaiting Approval

---

## Executive Summary

This plan consolidates all outstanding work into an optimised execution sequence. It encompasses:

1. **Configuration Architecture** - Master config layout enhancements
2. **Coverage Rebuilds** - All 7 coverages rebuilt to new structure
3. **Signal Architecture** - Inference functions, metadata, normalisers alignment
4. **Infrastructure** - Builder, API, DB, Analytics, Integrations verification
5. **Layer Implementations** - Risk updates, Loss layer, Exposure layer
6. **Validation Framework** - Comprehensive model configuration validation
7. **Organisational Graph** - Runtime implementation (Phase 23)
8. **Performance Enhancement** - Rust evaluation for critical components
9. **Documentation** - README.md, SKILL.md updates
10. **Cleanup** - Removal of redundant items
11. **Testing** - Complete production test coverage (final phase)

**Estimated Phases:** 11 major phases with sub-tasks
**Dependencies:** Clearly mapped to ensure optimal execution order

---

## Table of Contents

1. [Phase 1: Master Configuration Layout](#phase-1-master-configuration-layout)
2. [Phase 2: Signal Architecture Alignment](#phase-2-signal-architecture-alignment)
3. [Phase 3: Coverage Configuration Rebuilds](#phase-3-coverage-configuration-rebuilds)
4. [Phase 4: Infrastructure Builder Revision](#phase-4-infrastructure-builder-revision)
5. [Phase 5: Infrastructure Verification](#phase-5-infrastructure-verification)
6. [Phase 6: Layer Implementations](#phase-6-layer-implementations)
7. [Phase 7: Model Configuration Validation](#phase-7-model-configuration-validation)
8. [Phase 8: Organisational Graph Runtime](#phase-8-organisational-graph-runtime)
9. [Phase 9: Performance Enhancement (Rust Evaluation)](#phase-9-performance-enhancement)
10. [Phase 10: Documentation & Cleanup](#phase-10-documentation-and-cleanup)
11. [Phase 11: Testing](#phase-11-testing)

---

## Dependency Graph

```
Phase 1 (Master Config)
    │
    ├──► Phase 2 (Signal Architecture)
    │        │
    │        └──► Phase 3 (Coverage Rebuilds)
    │                 │
    │                 ├──► Phase 4 (Builder Revision)
    │                 │
    │                 └──► Phase 6 (Layer Implementations)
    │                          │
    │                          └──► Phase 7 (Validation Framework)
    │                                   │
    │                                   └──► Phase 8 (Org Graph Runtime)
    │
    └──► Phase 5 (Infrastructure Verification) [Parallel with 2-4]

Phase 9 (Rust Evaluation) [Can run parallel after Phase 6]

Phase 10 (Documentation & Cleanup) [After Phases 7-8]
    │
    └──► Phase 11 (Testing) [Final - requires stable implementation]
```

---

## Phase 1: Master Configuration Layout

**Objective:** Enhance `coverages/master_config_layout.yaml` with MODIFIER actions, MULTIPLIER pricing method, and three-layer score_condition support.

**Prerequisites:** None (starting point)

### 1.1 Score Condition Enhancement

**Current Structure:**
```yaml
score_condition:
  threshold: <value>
  comparison: ">=" | "<=" | "==" | ">" | "<"
  action: "FLAG" | "REFER"
  override: <tier>  # For tier override
  note: <string>    # For flagging
```

**New Structure:**
```yaml
score_condition:
  threshold: <value>
  comparison: ">=" | "<=" | "==" | ">" | "<"
  action: "FLAG" | "MODIFIER" | "REFER"
  # Action-specific fields:
  override: <tier>      # For REFER with tier override
  applied: <float>      # For MODIFIER - multiplicative to final premium
  note: <string>        # For FLAG and general documentation
```

**Tasks:**
| ID | Task | Details |
|----|------|---------|
| 1.1.1 | Define MODIFIER action schema | `applied` field as float, multiplicative to final premium |
| 1.1.2 | Update score_condition in signal_registry | Support FLAG \| MODIFIER \| REFER for risk, loss, exposure |
| 1.1.3 | Update score_condition in groups | Same actions available at group level |
| 1.1.4 | Document action precedence | How multiple modifiers combine (multiplicative chain) |

### 1.2 Risk Tier Bands - MULTIPLIER Method

**Current Structure:**
```yaml
risk_tier_bands:
  - tier: 1
    min_score: 800
    max_score: 1000
    label: "PREFERRED"
    decision: "APPROVE"
    application:
      method: "PREMIUM_BASE"
      value: 15000
```

**New Structure:**
```yaml
risk_tier_bands:
  - tier: 1
    min_score: 800
    max_score: 1000
    label: "PREFERRED"
    decision: "APPROVE"
    application:
      method: "PREMIUM_BASE" | "MULTIPLIER"
      # For PREMIUM_BASE:
      value: 15000
      # For MULTIPLIER:
      applied: 0.0035        # Rate multiplier
      basis: "tiv" | "limit" | "revenue" | "payroll" | <custom>
```

**Tasks:**
| ID | Task | Details |
|----|------|---------|
| 1.2.1 | Define MULTIPLIER method schema | `applied` (rate) and `basis` (what to multiply) |
| 1.2.2 | Update minimum_viable_input | Basis field must be in minimum_viable_input when MULTIPLIER used |
| 1.2.3 | Add validation rule | If method=MULTIPLIER, basis must exist in minimum_viable_input |
| 1.2.4 | Document both methods | Clear guidance on when to use each |

### 1.3 Loss Tier Bands Enhancement

**Current Structure:**
```yaml
loss_tier_bands:
  - tier: 1
    min_score: 0
    max_score: 200
    label: "VERY_LOW"
    frequency_modifier: 0.85
    severity_modifier: 0.90
```

**New Structure (adding score_condition):**
```yaml
loss_tier_bands:
  - tier: 1
    min_score: 0
    max_score: 200
    label: "VERY_LOW"
    frequency_modifier: 0.85
    severity_modifier: 0.90
    score_condition:              # NEW: Optional tier-level condition
      threshold: 150              # Within-tier threshold
      comparison: ">="
      action: "MODIFIER"
      applied: 0.95               # Additional 5% credit for very low loss
      note: "Exceptional loss profile"
```

**Tasks:**
| ID | Task | Details |
|----|------|---------|
| 1.3.1 | Add score_condition to loss_tier_bands | Optional, same schema as risk |
| 1.3.2 | Define modifier interaction | How loss modifiers combine with tier modifiers |
| 1.3.3 | Add to loss signal_registry | score_condition per signal for loss dimension |
| 1.3.4 | Add to loss groups | score_condition per group for loss dimension |

### 1.4 Exposure Tier Bands Enhancement

**Current Structure:**
```yaml
exposure:
  size_tier_bands:
    - tier: 1
      label: "MICRO"
      min_tiv: 0
      max_tiv: 1000000
      base_modifier: 0.90
```

**New Structure (adding score_condition and MULTIPLIER):**
```yaml
exposure:
  size_tier_bands:
    - tier: 1
      label: "MICRO"
      min_tiv: 0
      max_tiv: 1000000
      application:
        method: "MODIFIER"        # or "MULTIPLIER"
        applied: 0.90             # For MODIFIER: multiplicative factor
        # For MULTIPLIER:
        # applied: 0.002
        # basis: "tiv"
      score_condition:            # NEW: Optional
        threshold: 25
        comparison: "<="
        action: "MODIFIER"
        applied: 0.95
        note: "Very small exposure - additional credit"
```

**Tasks:**
| ID | Task | Details |
|----|------|---------|
| 1.4.1 | Add score_condition to exposure size_tier_bands | Optional, same schema |
| 1.4.2 | Add score_condition to complexity_tier_bands | Optional, same schema |
| 1.4.3 | Add MULTIPLIER option to exposure bands | Alternative to flat modifier |
| 1.4.4 | Add to exposure signal_registry | score_condition per signal for exposure dimension |
| 1.4.5 | Add to exposure groups | score_condition per group for exposure dimension |

### 1.5 Master Config Layout Document

**Tasks:**
| ID | Task | Details |
|----|------|---------|
| 1.5.1 | Update master_config_layout.yaml | Incorporate all above changes |
| 1.5.2 | Add comprehensive comments | Document every section and field |
| 1.5.3 | Add validation rules section | Document all validation requirements |
| 1.5.4 | Create schema reference | JSON Schema or equivalent for validation |

### Phase 1 Deliverables

- [ ] Updated `coverages/master_config_layout.yaml`
- [ ] JSON Schema for config validation
- [ ] Validation rules documentation

---

## Phase 2: Signal Architecture Alignment

**Objective:** Ensure all inference functions, metadata, and normalisers are correct and provide necessary items for configuration files.

**Prerequisites:** Phase 1 complete

### 2.1 Inference Function Audit

**Location:** `signal_architecture/signals/inference/`

**Tasks:**
| ID | Task | Details |
|----|------|---------|
| 2.1.1 | Inventory all inference functions | List every function referenced in configs |
| 2.1.2 | Map functions to config references | Cross-reference with all 7 coverage configs |
| 2.1.3 | Identify missing functions | Functions referenced but not implemented |
| 2.1.4 | Identify orphaned functions | Functions implemented but not referenced |
| 2.1.5 | Fix 23 function name typos | Known typos in configs (from SKILL.md) |
| 2.1.6 | Create stub implementations | For any missing functions |
| 2.1.7 | Standardise function signatures | Consistent input/output contracts |

**Standard Inference Function Signature:**
```python
def infer_{signal_name}(
    context: InferenceContext,
    extracted_data: Dict[str, Any],
    metadata: SignalMetadata
) -> InferenceResult:
    """
    Returns:
        InferenceResult with:
        - score: float (0-100)
        - confidence: float (0-1)
        - source_tier: ProxyTier
        - metadata: Dict[str, Any]
    """
```

### 2.2 Metadata Registry

**Location:** `signal_architecture/signals/inference/metadata/`

**Tasks:**
| ID | Task | Details |
|----|------|---------|
| 2.2.1 | Define metadata schema | Standard structure for all signal metadata |
| 2.2.2 | Create metadata registry | Central registry of all available metadata |
| 2.2.3 | Map metadata to signals | Which metadata each signal requires/produces |
| 2.2.4 | Validate config metadata references | All referenced metadata must exist |
| 2.2.5 | Create metadata stubs | For any missing metadata items |

**Metadata Schema:**
```python
@dataclass
class SignalMetadata:
    signal_id: str
    signal_name: str
    category: str
    proxy_tier: ProxyTier
    ttl_seconds: int
    required_extractors: List[str]
    output_type: Literal["score", "category", "boolean", "numeric"]
    value_range: Optional[Tuple[float, float]]
    # Three-layer weights (from config)
    risk_weight: Optional[float]
    loss_weight: Optional[float]
    exposure_weight: Optional[float]
```

### 2.3 Normaliser Alignment

**Location:** `signal_architecture/signals/categorisers/`

**Tasks:**
| ID | Task | Details |
|----|------|---------|
| 2.3.1 | Audit categoriser types | List all 12+ parameterised types |
| 2.3.2 | Map to config usage | Which categorisers used where |
| 2.3.3 | Validate parameter consistency | Params in config match categoriser expectations |
| 2.3.4 | Add missing categorisers | If configs reference types not implemented |
| 2.3.5 | Standardise output format | Consistent normalised output structure |

**Categoriser Types Required:**
1. `threshold_bucket` - Score into bands
2. `category_mapper` - Text to category
3. `boolean_score` - True/false to score
4. `weighted_composite` - Multi-input aggregation
5. `percentile_rank` - Rank within cohort
6. `z_score` - Standard deviation from mean
7. `min_max_scale` - Scale to 0-100
8. `logarithmic_scale` - Log transformation
9. `exponential_decay` - Time-weighted decay
10. `binary_threshold` - Above/below threshold
11. `multi_class` - Multiple discrete categories
12. `continuous_interpolation` - Linear interpolation between points

### 2.4 Extractor-to-Inference Pipeline

**Tasks:**
| ID | Task | Details |
|----|------|---------|
| 2.4.1 | Document pipeline flow | Extractor → Aggregator → Categoriser → Inference |
| 2.4.2 | Validate all pipelines | Every config signal has complete pipeline |
| 2.4.3 | Create pipeline registry | Central mapping of signal → pipeline components |
| 2.4.4 | Add pipeline validation | Runtime check that all components exist |

### Phase 2 Deliverables

- [ ] Inference function inventory with implementation status
- [ ] Metadata registry with all signals mapped
- [ ] Categoriser audit report
- [ ] Pipeline validation framework
- [ ] All stubs created for missing components

---

## Phase 3: Coverage Configuration Rebuilds

**Objective:** Rebuild all 7 coverage configs to the new master structure.

**Prerequisites:** Phase 1 and Phase 2 complete

### 3.1 Coverage Rebuild Process

For each coverage, the rebuild follows this process:

```
1. Export current config values (preserve business logic)
2. Apply new master_config_layout.yaml structure
3. Add score_condition to signals (risk, loss, exposure)
4. Add score_condition to groups (risk, loss, exposure)
5. Update tier bands with new structure
6. Add MODIFIER actions where appropriate
7. Configure MULTIPLIER method where applicable
8. Validate weights sum to 1.0 (per group, per layer)
9. Validate all metadata references
10. Validate all inference function references
11. Run config validation
12. Generate test profiles
```

### 3.2 Coverage-Specific Tasks

#### 3.2.1 Cyber (`coverages/cyber/config.yaml`)

| ID | Task | Details |
|----|------|---------|
| 3.2.1.1 | Restructure to master layout | Apply Phase 1 structure |
| 3.2.1.2 | Add loss score_conditions | Security posture → loss propensity |
| 3.2.1.3 | Add exposure score_conditions | Digital footprint → exposure magnitude |
| 3.2.1.4 | Configure MULTIPLIER tiers | TIV-based pricing option |
| 3.2.1.5 | Validate all weights | Sum to 1.0 per group per layer |
| 3.2.1.6 | Validate inference functions | All 25+ signals have valid functions |
| 3.2.1.7 | Update test profiles | Reflect new structure |

#### 3.2.2 Financial Institutions (`coverages/fi/config.yaml`)

| ID | Task | Details |
|----|------|---------|
| 3.2.2.1 | Restructure to master layout | Apply Phase 1 structure |
| 3.2.2.2 | Add loss score_conditions | Regulatory standing → loss propensity |
| 3.2.2.3 | Add exposure score_conditions | AUM/transaction volume → exposure |
| 3.2.2.4 | Configure MULTIPLIER tiers | Revenue-based pricing option |
| 3.2.2.5 | Validate all weights | Sum to 1.0 per group per layer |
| 3.2.2.6 | Validate inference functions | All signals have valid functions |
| 3.2.2.7 | Update test profiles | Reflect new structure |

#### 3.2.3 Energy (`coverages/energy/config.yaml`)

| ID | Task | Details |
|----|------|---------|
| 3.2.3.1 | Restructure to master layout | Apply Phase 1 structure |
| 3.2.3.2 | Add loss score_conditions | Safety culture → loss propensity |
| 3.2.3.3 | Add exposure score_conditions | Operational scale → exposure |
| 3.2.3.4 | Configure MULTIPLIER tiers | TIV-based pricing |
| 3.2.3.5 | Validate all weights | Sum to 1.0 per group per layer |
| 3.2.3.6 | Validate inference functions | All signals have valid functions |
| 3.2.3.7 | Update test profiles | Reflect new structure |

#### 3.2.4 Marine (`coverages/marine/config.yaml`)

| ID | Task | Details |
|----|------|---------|
| 3.2.4.1 | Restructure to master layout | Apply Phase 1 structure |
| 3.2.4.2 | Add loss score_conditions | Classification/flag → loss propensity |
| 3.2.4.3 | Add exposure score_conditions | Vessel value/routes → exposure |
| 3.2.4.4 | Configure MULTIPLIER tiers | Hull value-based pricing |
| 3.2.4.5 | Validate all weights | Sum to 1.0 per group per layer |
| 3.2.4.6 | Validate inference functions | All signals have valid functions |
| 3.2.4.7 | Update test profiles | Reflect new structure |

#### 3.2.5 Directors & Officers (`coverages/do/config.yaml`)

| ID | Task | Details |
|----|------|---------|
| 3.2.5.1 | Restructure to master layout | Apply Phase 1 structure |
| 3.2.5.2 | Add loss score_conditions | Governance → loss propensity |
| 3.2.5.3 | Add exposure score_conditions | Market cap/litigation → exposure |
| 3.2.5.4 | Configure MULTIPLIER tiers | Revenue-based pricing |
| 3.2.5.5 | Validate all weights | Sum to 1.0 per group per layer |
| 3.2.5.6 | Validate inference functions | All signals have valid functions |
| 3.2.5.7 | Update test profiles | Reflect new structure |

#### 3.2.6 Professional Indemnity (`coverages/pi/config.yaml`)

| ID | Task | Details |
|----|------|---------|
| 3.2.6.1 | Restructure to master layout | Apply Phase 1 structure |
| 3.2.6.2 | Add loss score_conditions | Professional standards → loss propensity |
| 3.2.6.3 | Add exposure score_conditions | Revenue/client base → exposure |
| 3.2.6.4 | Configure MULTIPLIER tiers | Revenue-based pricing |
| 3.2.6.5 | Validate all weights | Sum to 1.0 per group per layer |
| 3.2.6.6 | Validate inference functions | All signals have valid functions |
| 3.2.6.7 | Update test profiles | Reflect new structure |

#### 3.2.7 Aerospace (`coverages/aerospace/config.yaml`)

| ID | Task | Details |
|----|------|---------|
| 3.2.7.1 | Restructure to master layout | Apply Phase 1 structure |
| 3.2.7.2 | Add loss score_conditions | Certification/safety → loss propensity |
| 3.2.7.3 | Add exposure score_conditions | Fleet value/operations → exposure |
| 3.2.7.4 | Configure MULTIPLIER tiers | Hull value-based pricing |
| 3.2.7.5 | Validate all weights | Sum to 1.0 per group per layer |
| 3.2.7.6 | Validate inference functions | All signals have valid functions |
| 3.2.7.7 | Update test profiles | Reflect new structure |

### 3.3 Cross-Coverage Validation

| ID | Task | Details |
|----|------|---------|
| 3.3.1 | Validate structural consistency | All 7 configs follow same structure |
| 3.3.2 | Validate crosswalk alignment | Common concepts consistent across coverages |
| 3.3.3 | Update coverage_crosswalk.json | Reflect any structural changes |
| 3.3.4 | Generate coverage comparison report | Side-by-side structure validation |

### Phase 3 Deliverables

- [ ] 7 rebuilt coverage configuration files
- [ ] Validation report for each coverage
- [ ] Updated coverage_crosswalk.json
- [ ] Coverage comparison report

---

## Phase 4: Infrastructure Builder Revision

**Objective:** Update the AI builder to generate configs matching the new master structure.

**Prerequisites:** Phase 1 and Phase 3 complete

### 4.1 Builder Core Updates

**Location:** `infrastructure/builder/`

| ID | Task | Details |
|----|------|---------|
| 4.1.1 | Update CoverageBuilder.generate_config() | Output new master structure |
| 4.1.2 | Add score_condition generation | Generate appropriate score_conditions |
| 4.1.3 | Add MULTIPLIER support | Generate MULTIPLIER tier bands when appropriate |
| 4.1.4 | Update _build_signal_groups() | Include three-layer weights |
| 4.1.5 | Update _build_tier_config() | Support both PREMIUM_BASE and MULTIPLIER |
| 4.1.6 | Add _build_loss_tier_bands() | Generate loss tier configuration |
| 4.1.7 | Add _build_exposure_config() | Generate exposure tier configuration |

### 4.2 Validator Updates

**Location:** `infrastructure/builder/validator.py`

| ID | Task | Details |
|----|------|---------|
| 4.2.1 | Update schema validation | Match new master_config_layout |
| 4.2.2 | Add weight sum validation | Verify weights sum to 1.0 |
| 4.2.3 | Add score_condition validation | Verify action/applied/override combinations |
| 4.2.4 | Add MULTIPLIER basis validation | Verify basis in minimum_viable_input |
| 4.2.5 | Add inference function validation | Verify all referenced functions exist |
| 4.2.6 | Add metadata validation | Verify all referenced metadata exists |
| 4.2.7 | Create validation report format | Structured output for validation results |

### 4.3 Signal Library Updates

**Location:** `infrastructure/builder/signal_library.py`

| ID | Task | Details |
|----|------|---------|
| 4.3.1 | Update signal templates | Include three-layer weights |
| 4.3.2 | Add score_condition templates | Default score_conditions per signal type |
| 4.3.3 | Update industry profiles | Reflect new structure |
| 4.3.4 | Add loss/exposure weight suggestions | Industry-specific weight recommendations |

### 4.4 Builder Types Updates

**Location:** `infrastructure/builder/types.py`

| ID | Task | Details |
|----|------|---------|
| 4.4.1 | Update CoverageSpec | Add loss/exposure configuration options |
| 4.4.2 | Update SignalSelection | Include three-layer weights |
| 4.4.3 | Add ScoreConditionSpec | Type for score_condition configuration |
| 4.4.4 | Add TierBandSpec | Type for tier band configuration |
| 4.4.5 | Update ValidationResult | Include new validation categories |

### Phase 4 Deliverables

- [ ] Updated coverage_builder.py
- [ ] Updated validator.py with comprehensive validation
- [ ] Updated signal_library.py
- [ ] Updated types.py
- [ ] Builder integration tests

---

## Phase 5: Infrastructure Verification

**Objective:** Verify and update API, DB, Analytics, and Integrations for new structure.

**Prerequisites:** Phase 1 complete (can run parallel with Phases 2-4)

### 5.1 API Layer Verification

**Location:** `infrastructure/api/`

| ID | Task | Details |
|----|------|---------|
| 5.1.1 | Audit API schemas | Verify request/response schemas match new config |
| 5.1.2 | Update submission endpoints | Handle new config structure |
| 5.1.3 | Update analytics endpoints | Return three-layer results |
| 5.1.4 | Add MODIFIER tracking | Track applied modifiers in responses |
| 5.1.5 | Update documentation | OpenAPI spec reflects changes |
| 5.1.6 | Verify authentication | No changes needed (confirm) |
| 5.1.7 | Verify rate limiting | No changes needed (confirm) |

### 5.2 Database Layer Verification

**Location:** `infrastructure/db/`

| ID | Task | Details |
|----|------|---------|
| 5.2.1 | Audit data models | Verify models support new structure |
| 5.2.2 | Add modifier tracking fields | Store applied modifiers |
| 5.2.3 | Add three-layer result fields | Store loss/exposure results |
| 5.2.4 | Update repositories | Handle new data structures |
| 5.2.5 | Create migration scripts | If schema changes required |
| 5.2.6 | Verify indexing | Performance for new queries |

### 5.3 Analytics Engine Verification

**Location:** `infrastructure/analytics/`

| ID | Task | Details |
|----|------|---------|
| 5.3.1 | Update signal_analytics.py | Handle three-layer signals |
| 5.3.2 | Update portfolio_analytics.py | Include loss/exposure metrics |
| 5.3.3 | Add modifier analytics | Track modifier application patterns |
| 5.3.4 | Update performance.py | Track three-layer performance |
| 5.3.5 | Add loss correlation analytics | Specific loss layer analytics |
| 5.3.6 | Add exposure analytics | Specific exposure layer analytics |

### 5.4 Integrations Verification

**Location:** `infrastructure/integrations/`

| ID | Task | Details |
|----|------|---------|
| 5.4.1 | Verify email integration | Can send three-layer results |
| 5.4.2 | Verify document generation | Can generate three-layer reports |
| 5.4.3 | Verify webhooks | Payload includes new structure |
| 5.4.4 | Update notification templates | Include modifier information |

### Phase 5 Deliverables

- [ ] API verification report
- [ ] Database migration scripts (if needed)
- [ ] Updated analytics modules
- [ ] Integration verification report

---

## Phase 6: Layer Implementations

**Objective:** Implement/update Risk, Loss, and Exposure layer engines.

**Prerequisites:** Phase 3 complete

### 6.1 Risk Layer Updates

**Location:** `layers/risk/`

| ID | Task | Details |
|----|------|---------|
| 6.1.1 | Update scorer.py | Handle MODIFIER score_conditions |
| 6.1.2 | Update pricer.py | Handle MULTIPLIER tier bands |
| 6.1.3 | Update pricer.py | Apply modifiers multiplicatively |
| 6.1.4 | Update config_manager.py | Load new config structure |
| 6.1.5 | Update workflow.py | Integrate modifier tracking |
| 6.1.6 | Update query_evaluator.py | Handle MODIFIER actions |
| 6.1.7 | Add modifier accumulator | Track and apply all modifiers |
| 6.1.8 | Update types.py | New types for modifiers |

**Modifier Application Logic:**
```python
def apply_modifiers(base_premium: float, modifiers: List[Modifier]) -> float:
    """Apply all modifiers multiplicatively to final premium."""
    final_premium = base_premium
    for modifier in modifiers:
        final_premium *= modifier.applied
    return final_premium
```

### 6.2 Loss Layer Implementation

**Location:** `layers/loss/`

| ID | Task | Details |
|----|------|---------|
| 6.2.1 | Create loss_scorer.py | Score signals for loss propensity |
| 6.2.2 | Create loss_config.py | Load loss-specific config sections |
| 6.2.3 | Implement score_condition handling | FLAG \| MODIFIER \| REFER for loss |
| 6.2.4 | Implement tier band assignment | Map loss score to frequency/severity modifiers |
| 6.2.5 | Implement cohort assignment | Assign to behavioral cohort |
| 6.2.6 | Implement trend detection | Calculate loss trend direction |
| 6.2.7 | Create loss_types.py | Loss-specific data types |
| 6.2.8 | Integrate with pricing engine | Apply loss modifiers to premium |
| 6.2.9 | Add monitoring hooks | For continuous deterioration monitoring |

**Loss Scorer Interface:**
```python
@dataclass
class LossAssessmentResult:
    loss_score: float                    # 0-1000 composite
    frequency_propensity: float          # 0-100
    severity_propensity: float           # 0-100
    frequency_modifier: float            # Multiplicative modifier
    severity_modifier: float             # Multiplicative modifier
    combined_modifier: float             # frequency × severity
    cohort_id: str                       # Behavioral cohort assignment
    cohort_percentile: float             # Position within cohort
    trend_direction: Literal["improving", "stable", "deteriorating"]
    confidence: float                    # 0-1
    triggered_conditions: List[TriggeredCondition]
    applied_modifiers: List[Modifier]
```

### 6.3 Exposure Layer Implementation

**Location:** `layers/exposure/`

| ID | Task | Details |
|----|------|---------|
| 6.3.1 | Create exposure_scorer.py | Score signals for exposure magnitude |
| 6.3.2 | Create exposure_config.py | Load exposure-specific config sections |
| 6.3.3 | Implement score_condition handling | FLAG \| MODIFIER \| REFER for exposure |
| 6.3.4 | Implement size tier assignment | Map to MICRO/SMALL/MEDIUM/LARGE/VERY_LARGE |
| 6.3.5 | Implement complexity scoring | Calculate complexity category |
| 6.3.6 | Implement confidence gating | High exposure + low confidence = REFER |
| 6.3.7 | Create exposure_types.py | Exposure-specific data types |
| 6.3.8 | Integrate with pricing engine | Apply exposure modifiers |
| 6.3.9 | Implement TIV/limit inference | When not directly provided |

**Exposure Scorer Interface:**
```python
@dataclass
class ExposureAssessmentResult:
    exposure_score: float                # 0-1000 composite
    size_tier: int                       # 1-5
    size_label: str                      # MICRO, SMALL, etc.
    complexity_tier: int                 # 1-5
    complexity_label: str                # SIMPLE, MODERATE, etc.
    size_modifier: float                 # Multiplicative modifier
    complexity_modifier: float           # Multiplicative modifier
    combined_modifier: float             # size × complexity
    implied_tiv_range: Tuple[float, float]  # Estimated TIV range
    confidence: float                    # 0-1
    proxy_tier: ProxyTier                # DIRECT/INFERRED/COHORT
    triggered_conditions: List[TriggeredCondition]
    applied_modifiers: List[Modifier]
```

### 6.4 Pricing Engine Integration

**Location:** `layers/risk/pricer.py` (updated)

| ID | Task | Details |
|----|------|---------|
| 6.4.1 | Update premium calculation | Integrate all three layer outputs |
| 6.4.2 | Implement modifier chain | Risk → Loss → Exposure → Final |
| 6.4.3 | Add MULTIPLIER calculation | basis × applied rate |
| 6.4.4 | Track modifier sources | Audit trail for each modifier |
| 6.4.5 | Implement caps/floors | Prevent extreme premium adjustments |

**Integrated Pricing Formula:**
```python
def calculate_premium(
    risk_result: RiskAssessmentResult,
    loss_result: LossAssessmentResult,
    exposure_result: ExposureAssessmentResult,
    tier_config: TierConfig,
    submission: Submission
) -> PremiumResult:

    # Base premium from risk tier
    if tier_config.method == "PREMIUM_BASE":
        base = tier_config.value
    else:  # MULTIPLIER
        basis_value = getattr(submission, tier_config.basis)
        base = basis_value * tier_config.applied

    # Apply all modifiers multiplicatively
    all_modifiers = (
        risk_result.applied_modifiers +
        loss_result.applied_modifiers +
        exposure_result.applied_modifiers
    )

    final_premium = base
    for modifier in all_modifiers:
        final_premium *= modifier.applied

    # Apply loss layer modifiers
    final_premium *= loss_result.combined_modifier

    # Apply exposure layer modifiers
    final_premium *= exposure_result.combined_modifier

    return PremiumResult(
        base_premium=base,
        final_premium=final_premium,
        modifiers_applied=all_modifiers,
        audit_trail=build_audit_trail(...)
    )
```

### 6.5 Workflow Integration

**Location:** `layers/risk/workflow.py`

| ID | Task | Details |
|----|------|---------|
| 6.5.1 | Update to run three layers in parallel | asyncio.gather for all three |
| 6.5.2 | Combine layer results | Unified assessment result |
| 6.5.3 | Aggregate referrals | From all three layers |
| 6.5.4 | Aggregate flags | From all three layers |
| 6.5.5 | Update decision logic | Consider all layer outputs |
| 6.5.6 | Update audit trail | Include all three layer traces |

### Phase 6 Deliverables

- [ ] Updated risk layer with MODIFIER and MULTIPLIER support
- [ ] Complete loss layer implementation
- [ ] Complete exposure layer implementation
- [ ] Integrated pricing engine
- [ ] Updated workflow orchestration
- [ ] Layer-specific unit tests

---

## Phase 7: Model Configuration Validation

**Objective:** Build comprehensive validation framework ensuring config correctness.

**Prerequisites:** Phase 6 complete

### 7.1 Validation Rules

| ID | Rule | Implementation |
|----|------|----------------|
| 7.1.1 | Weights sum to 1.0 | Per group, per layer (risk/loss/exposure) |
| 7.1.2 | MODIFIER has applied field | action=MODIFIER requires applied: float |
| 7.1.3 | REFER has optional override | action=REFER may have override: int |
| 7.1.4 | FLAG has note field | action=FLAG requires note: string |
| 7.1.5 | MULTIPLIER has basis | method=MULTIPLIER requires basis field |
| 7.1.6 | Basis in minimum_viable_input | MULTIPLIER basis must be required input |
| 7.1.7 | Inference functions exist | All referenced functions implemented |
| 7.1.8 | Metadata items exist | All referenced metadata available |
| 7.1.9 | Tier bands are contiguous | No gaps in score ranges |
| 7.1.10 | Tier bands don't overlap | No overlapping score ranges |
| 7.1.11 | Signal IDs unique | No duplicate signal IDs within coverage |
| 7.1.12 | Group IDs unique | No duplicate group IDs within coverage |
| 7.1.13 | Threshold values valid | Within expected ranges (0-100 for signals) |
| 7.1.14 | Comparison operators valid | One of: >=, <=, ==, >, < |
| 7.1.15 | Applied values reasonable | Modifiers within bounds (e.g., 0.5-2.0) |

### 7.2 Validation Framework

**Location:** `infrastructure/builder/validator.py` (expanded)

| ID | Task | Details |
|----|------|---------|
| 7.2.1 | Create ValidationRule base class | Standard interface for all rules |
| 7.2.2 | Implement WeightSumRule | Validate weight sums |
| 7.2.3 | Implement ScoreConditionRule | Validate score_condition structure |
| 7.2.4 | Implement TierBandRule | Validate tier band configuration |
| 7.2.5 | Implement ReferenceRule | Validate all references resolve |
| 7.2.6 | Implement BoundsRule | Validate values within bounds |
| 7.2.7 | Create ValidationEngine | Run all rules, aggregate results |
| 7.2.8 | Create ValidationReport | Structured output format |

**Validation Engine Interface:**
```python
class ConfigValidator:
    def validate(self, config: Dict[str, Any]) -> ValidationReport:
        """
        Run all validation rules against configuration.

        Returns:
            ValidationReport with:
            - valid: bool
            - errors: List[ValidationError]  # Must fix
            - warnings: List[ValidationWarning]  # Should fix
            - info: List[ValidationInfo]  # FYI
        """
```

### 7.3 Runtime Validation

| ID | Task | Details |
|----|------|---------|
| 7.3.1 | Add config load validation | Validate on every config load |
| 7.3.2 | Add startup validation | Validate all configs on API startup |
| 7.3.3 | Add CI validation | Validate configs in CI pipeline |
| 7.3.4 | Create validation CLI | Command-line config validation |

### 7.4 Validation Reporting

| ID | Task | Details |
|----|------|---------|
| 7.4.1 | Create JSON report format | Machine-readable validation results |
| 7.4.2 | Create human-readable format | CLI-friendly output |
| 7.4.3 | Create fix suggestions | Actionable guidance for errors |
| 7.4.4 | Add validation metrics | Track validation pass/fail rates |

### Phase 7 Deliverables

- [ ] Comprehensive validation rule set
- [ ] ValidationEngine implementation
- [ ] Validation CLI tool
- [ ] CI integration
- [ ] Validation report formats

---

## Phase 8: Organisational Graph Runtime

**Objective:** Implement runtime for the Organisational Graph (Phase 23 from roadmap).

**Prerequisites:** Phases 6 and 7 complete

### 8.1 Core Graph Infrastructure

**Location:** `signal_architecture/graph/` (new directory)

| ID | Task | Details |
|----|------|---------|
| 8.1.1 | Create graph/types.py | Node, Edge, Graph types |
| 8.1.2 | Create graph/node_factory.py | Create nodes from signal data |
| 8.1.3 | Create graph/edge_inferencer.py | Infer edges from relationships |
| 8.1.4 | Create graph/graph_builder.py | Build complete graph from signals |
| 8.1.5 | Create graph/storage.py | Persist and retrieve graphs |

### 8.2 Node Implementation

| ID | Task | Details |
|----|------|---------|
| 8.2.1 | Implement OrganisationNode | Root entity node |
| 8.2.2 | Implement AssetNode | Digital/physical assets |
| 8.2.3 | Implement PartnerNode | External relationships |
| 8.2.4 | Implement PersonNode | Key individuals |
| 8.2.5 | Implement ProcessNode | Business processes |
| 8.2.6 | Implement JurisdictionNode | Geographic/regulatory |
| 8.2.7 | Add signal attachment | Connect signals to nodes |

### 8.3 Edge Implementation

| ID | Task | Details |
|----|------|---------|
| 8.3.1 | Implement DependencyEdge | Operational dependencies |
| 8.3.2 | Implement TrustEdge | Authority relationships |
| 8.3.3 | Implement DataFlowEdge | Data movement |
| 8.3.4 | Implement OwnershipEdge | Control relationships |
| 8.3.5 | Implement OperatesInEdge | Jurisdiction presence |
| 8.3.6 | Implement EmploymentEdge | Personnel relationships |
| 8.3.7 | Add propagation rules | Per edge type |

### 8.4 Derivative Calculations

**Location:** `signal_architecture/graph/derivatives/`

| ID | Task | Details |
|----|------|---------|
| 8.4.1 | Implement entropy calculation | Control decay indicator |
| 8.4.2 | Implement velocity calculation | Operational overload indicator |
| 8.4.3 | Implement drift calculation | Peer divergence indicator |
| 8.4.4 | Implement concentration calculation | Single-point-of-failure indicator |
| 8.4.5 | Implement fragility calculation | Composite resilience indicator |
| 8.4.6 | Add threshold monitoring | Warning/critical thresholds |

### 8.5 Authority Propagation

**Location:** `signal_architecture/graph/propagation/`

| ID | Task | Details |
|----|------|---------|
| 8.5.1 | Implement PageRank algorithm | Authority flow through trust edges |
| 8.5.2 | Implement risk propagation | Risk flow through dependencies |
| 8.5.3 | Implement exposure aggregation | Aggregate across jurisdictions |
| 8.5.4 | Add convergence monitoring | Track algorithm convergence |

### 8.6 Graph Integration

| ID | Task | Details |
|----|------|---------|
| 8.6.1 | Integrate with workflow | Build graph during assessment |
| 8.6.2 | Add graph-based scoring | Use graph metrics in scoring |
| 8.6.3 | Add graph visualization data | Export for visualization |
| 8.6.4 | Add graph persistence | Store for trend analysis |

### Phase 8 Deliverables

- [ ] Complete graph infrastructure
- [ ] All node types implemented
- [ ] All edge types implemented
- [ ] Derivative calculations working
- [ ] Authority propagation working
- [ ] Workflow integration complete

---

## Phase 9: Performance Enhancement

**Objective:** Evaluate and implement Rust for performance-critical components.

**Prerequisites:** Phase 6 complete (can run parallel with 7-8)

### 9.1 Performance Baseline

| ID | Task | Details |
|----|------|---------|
| 9.1.1 | Establish performance benchmarks | Current Python performance |
| 9.1.2 | Identify bottlenecks | Profile signal extraction, graph computation |
| 9.1.3 | Define performance targets | Target improvements per component |
| 9.1.4 | Create benchmark suite | Reproducible performance tests |

### 9.2 Rust Evaluation

| ID | Task | Details |
|----|------|---------|
| 9.2.1 | Create dsi-core Rust crate | Basic project structure |
| 9.2.2 | Implement proof-of-concept | One component in Rust |
| 9.2.3 | Create PyO3 bindings | Python integration |
| 9.2.4 | Benchmark comparison | Rust vs Python performance |
| 9.2.5 | Evaluate development impact | Build complexity, maintainability |
| 9.2.6 | Make go/no-go decision | Based on benchmarks and complexity |

### 9.3 Rust Implementation (if approved)

| ID | Task | Details |
|----|------|---------|
| 9.3.1 | Implement graph computations | PageRank, propagation in Rust |
| 9.3.2 | Implement derivative calculations | Entropy, velocity, drift in Rust |
| 9.3.3 | Implement signal extraction core | Network I/O, parsing in Rust |
| 9.3.4 | Create Python package | dsi_core with seamless integration |
| 9.3.5 | Update CI/CD | Rust build integration |
| 9.3.6 | Document Rust components | Developer guide |

### Phase 9 Deliverables

- [ ] Performance baseline report
- [ ] Rust evaluation report with recommendation
- [ ] (If approved) dsi-core Rust crate
- [ ] (If approved) Python bindings
- [ ] Performance comparison report

---

## Phase 10: Documentation and Cleanup

**Objective:** Update all documentation and remove redundant items.

**Prerequisites:** Phases 7-8 complete

### 10.1 README.md Update

| ID | Task | Details |
|----|------|---------|
| 10.1.1 | Update project status | Reflect completed phases |
| 10.1.2 | Update architecture diagram | Three-layer parallel assessment |
| 10.1.3 | Update configuration section | New config structure |
| 10.1.4 | Update getting started | Any new setup requirements |
| 10.1.5 | Update API documentation | New endpoints/responses |
| 10.1.6 | Update validation section | New validation framework |

### 10.2 SKILL.md Update

| ID | Task | Details |
|----|------|---------|
| 10.2.1 | Update implementation status | All phases current |
| 10.2.2 | Update architecture overview | Reflect changes |
| 10.2.3 | Update YAML config structure | New master structure |
| 10.2.4 | Update critical rules | New rules for modifiers |
| 10.2.5 | Update outstanding work | Remove completed, add new |
| 10.2.6 | Update file structure | Any new directories/files |

### 10.3 Configuration Architecture Documentation

| ID | Task | Details |
|----|------|---------|
| 10.3.1 | Update Configuration Architecture.md | Reflect all changes |
| 10.3.2 | Add MODIFIER documentation | Usage and examples |
| 10.3.3 | Add MULTIPLIER documentation | Usage and examples |
| 10.3.4 | Add validation documentation | All validation rules |

### 10.4 Phase Document Updates

| ID | Task | Details |
|----|------|---------|
| 10.4.1 | Archive outdated phase docs | Move to archive/ |
| 10.4.2 | Create consolidated phase doc | Single reference for completed work |
| 10.4.3 | Update phase roadmap | Reflect new phase numbers |

### 10.5 Cleanup - Redundant Items

| ID | Task | Details |
|----|------|---------|
| 10.5.1 | Remove deleted config files | config.yaml, config_rework.yaml already deleted |
| 10.5.2 | Remove orphaned code | Code not referenced by new structure |
| 10.5.3 | Remove outdated tests | Tests for removed functionality |
| 10.5.4 | Remove duplicate utilities | Consolidated into single location |
| 10.5.5 | Clean up imports | Remove unused imports |
| 10.5.6 | Archive old demos | Replace with production demo |

### 10.6 Cleanup - Branch Management

| ID | Task | Details |
|----|------|---------|
| 10.6.1 | Verify all branches deleted | Per user comment - branches deleted |
| 10.6.2 | Tag release version | v1.0.0 or appropriate version |
| 10.6.3 | Update CHANGELOG.md | Document all changes |

### Phase 10 Deliverables

- [ ] Updated README.md
- [ ] Updated SKILL.md
- [ ] Updated Configuration Architecture.md
- [ ] Archived outdated documents
- [ ] Cleaned codebase (no redundant items)
- [ ] Release tag

---

## Phase 11: Testing

**Objective:** Complete production test coverage.

**Prerequisites:** All previous phases complete (stable implementation)

### 11.1 Test Strategy

```
Unit Tests (70%)
├── Signal Architecture
│   ├── Inference functions
│   ├── Categorisers
│   ├── Aggregators
│   └── Extractors
├── Layers
│   ├── Risk scorer
│   ├── Loss scorer
│   ├── Exposure scorer
│   └── Pricer
├── Infrastructure
│   ├── Builder
│   ├── Validator
│   └── Analytics
└── Graph
    ├── Node factory
    ├── Edge inferencer
    └── Derivatives

Integration Tests (20%)
├── End-to-end workflow
├── Three-layer assessment
├── API endpoints
└── Database operations

Performance Tests (10%)
├── Throughput benchmarks
├── Latency benchmarks
└── Stress tests
```

### 11.2 Unit Test Implementation

| ID | Task | Details | Target Coverage |
|----|------|---------|-----------------|
| 11.2.1 | Signal architecture tests | All inference, categorisers, aggregators | 90% |
| 11.2.2 | Risk layer tests | Scorer, pricer, workflow | 90% |
| 11.2.3 | Loss layer tests | Scorer, tier assignment, cohort | 90% |
| 11.2.4 | Exposure layer tests | Scorer, tier assignment, complexity | 90% |
| 11.2.5 | Builder tests | Config generation, validation | 85% |
| 11.2.6 | Validator tests | All validation rules | 95% |
| 11.2.7 | Graph tests | Nodes, edges, derivatives, propagation | 85% |
| 11.2.8 | Analytics tests | Signal, portfolio, performance | 80% |

### 11.3 Integration Test Implementation

| ID | Task | Details |
|----|------|---------|
| 11.3.1 | End-to-end workflow tests | Complete 14-step workflow |
| 11.3.2 | Three-layer integration tests | All layers working together |
| 11.3.3 | Config loading tests | All 7 coverages load correctly |
| 11.3.4 | API integration tests | All 32+ endpoints |
| 11.3.5 | Database integration tests | CRUD operations, migrations |
| 11.3.6 | Graph integration tests | Build and query graphs |

### 11.4 Performance Test Implementation

| ID | Task | Details |
|----|------|---------|
| 11.4.1 | Single assessment benchmark | Target: <500ms |
| 11.4.2 | Batch assessment benchmark | Target: 100 assessments/minute |
| 11.4.3 | Graph computation benchmark | Target: <100ms for 1000 nodes |
| 11.4.4 | API throughput benchmark | Target: 50 requests/second |
| 11.4.5 | Stress test | Sustained load for 1 hour |

### 11.5 Test Coverage Targets

| Component | Current | Target |
|-----------|---------|--------|
| Overall | 12.6% | 80% |
| Signal Architecture | ~15% | 90% |
| Risk Layer | ~40% | 90% |
| Loss Layer | 0% | 90% |
| Exposure Layer | 0% | 90% |
| Infrastructure | ~20% | 85% |
| Graph | 0% | 85% |

### 11.6 Test Infrastructure

| ID | Task | Details |
|----|------|---------|
| 11.6.1 | Set up test fixtures | Reusable test data |
| 11.6.2 | Create test config generator | Generate valid test configs |
| 11.6.3 | Set up CI coverage reporting | Automated coverage tracking |
| 11.6.4 | Create test documentation | Testing guide for developers |
| 11.6.5 | Set up performance CI | Automated performance regression |

### Phase 11 Deliverables

- [ ] Unit test suite (target: 80% coverage)
- [ ] Integration test suite
- [ ] Performance test suite
- [ ] CI/CD integration
- [ ] Test documentation
- [ ] Coverage report

---

## Execution Summary

### Phase Order (Optimised)

| Phase | Name | Dependencies | Estimated Effort |
|-------|------|--------------|------------------|
| 1 | Master Configuration Layout | None | Medium |
| 2 | Signal Architecture Alignment | Phase 1 | Medium |
| 3 | Coverage Configuration Rebuilds | Phases 1, 2 | High |
| 4 | Infrastructure Builder Revision | Phases 1, 3 | Medium |
| 5 | Infrastructure Verification | Phase 1 (parallel with 2-4) | Medium |
| 6 | Layer Implementations | Phase 3 | High |
| 7 | Model Configuration Validation | Phase 6 | Medium |
| 8 | Organisational Graph Runtime | Phases 6, 7 | High |
| 9 | Performance Enhancement (Rust) | Phase 6 (parallel with 7-8) | Medium |
| 10 | Documentation & Cleanup | Phases 7, 8 | Medium |
| 11 | Testing | All previous phases | High |

### Parallelisation Opportunities

```
Timeline:
─────────────────────────────────────────────────────────────────►

Phase 1 ──► Phase 2 ──► Phase 3 ──► Phase 6 ──► Phase 7 ──► Phase 8 ──► Phase 10 ──► Phase 11
                │           │           │           │
                │           │           └── Phase 9 ┘ (parallel)
                │           │
                │           └────────── Phase 4
                │
                └──────────────────────── Phase 5 (parallel with 2-4)
```

### Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Scope creep | Strict adherence to defined tasks |
| Config breaking changes | Comprehensive validation before deploy |
| Performance regression | Baseline benchmarks, continuous monitoring |
| Integration failures | Incremental integration, feature flags |
| Testing bottleneck | Parallel test development with implementation |

### Success Criteria

- [ ] All 7 coverages rebuilt and validated
- [ ] Three-layer assessment fully operational
- [ ] MODIFIER and MULTIPLIER working in production
- [ ] Organisational Graph runtime complete
- [ ] Validation framework catching all config errors
- [ ] Test coverage >= 80%
- [ ] Documentation current and complete
- [ ] No redundant files in repository
- [ ] Performance targets met

---

## Appendices

### Appendix A: Master Config Layout Reference

See `coverages/master_config_layout.yaml` (to be updated in Phase 1)

### Appendix B: Validation Rules Reference

See Phase 7 detailed rules

### Appendix C: Test Coverage Matrix

See Phase 11 coverage targets

### Appendix D: Rust Component Candidates

- Graph computations (PageRank, propagation)
- Derivative calculations (entropy, velocity, drift)
- Signal extraction core (network I/O, parsing)
- Config validation (WASM for browser)

---

**Document Status:** DRAFT
**Awaiting:** User approval before execution
**Next Action:** Review and confirm plan, then begin Phase 1

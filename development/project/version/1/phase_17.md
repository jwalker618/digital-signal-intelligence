# Phase 17: Exposure Shadow Layer

## Purpose

Extend DSI to estimate **exposure magnitude** and **exposure complexity** using observable digital signals, enabling:
- TIV estimation without client-provided data
- Exposure band classification (micro → very_large)
- Complexity assessment (simple → extremely_complex)
- Two-dimensional pricing (tier × exposure band)

This is the third intelligence layer of the DSI framework.

## Key Deliverables

- Exposure magnitude scorer
- Complexity scorer
- Band mapping and cohort priors
- Pricing integration (parallel, embedded, grid patterns)
- Auto-apply rules engine

## Status

🔲 **Not Started** - Specification Complete

## Detailed Specification

**Full specification documents are located in**: `exposure/shadow_layer/development/`

| Document | Purpose |
|----------|---------|
| `plan.md` | Complete implementation plan with code examples |
| `executive_briefing.md` | Executive summary and business case |
| `actuarial_validation.md` | Validation requirements and methodology |
| `README.md` | Overview and quick start |

**Do not duplicate specification content here.** Refer to the detailed documents for:
- Core types and dataclasses
- ExposureScorer implementation
- ComplexityScorer implementation
- BandMapper and CohortManager
- YAML configuration schema
- Pricing integration patterns
- Workflow integration details

## Architecture Integration

The Exposure Shadow Layer runs in parallel with risk scoring and loss correlation:

```
Signal Extraction (Steps 0-4)
           │
           ├──────────────┬──────────────┐
           │              │              │
           ▼              ▼              ▼
    ┌──────────┐   ┌──────────┐   ┌──────────┐
    │   RISK   │   │ EXPOSURE │   │   LOSS   │
    │ SCORING  │   │  SHADOW  │   │CORRELATION│
    │          │   │  LAYER   │   │  LAYER   │
    │ Steps 5-6│   │ Phase 17 │   │ Phase 16 │
    └──────────┘   └──────────┘   └──────────┘
           │              │              │
           └──────────────┴──────────────┘
                          │
                          ▼
                   Pricing Engine
    Risk Tier × Exposure Band × Loss Propensity → Premium
```

## Key Concepts

### Exposure Assessment Output

```python
@dataclass
class ExposureResult:
    score: float                      # 0-100
    band: ExposureBand               # micro/small/medium/large/very_large
    confidence: float                # 0-1
    proxy_tier: ProxyTier            # direct_observable/inferred/cohort/unknown
    range_low: float                 # Score range (lower bound)
    range_high: float                # Score range (upper bound)
    implied_tiv_range: Tuple[float, float]  # Estimated TIV range
    group_scores: Dict[str, float]   # Per-group scores

@dataclass
class ComplexityResult:
    score: float                      # 0-100
    category: ComplexityCategory     # simple → extremely_complex
    confidence: float
    geographic_score: float          # Geographic dispersion
    structural_score: float          # Organizational complexity
    technical_score: float           # Technology heterogeneity
    regulatory_score: float          # Regulatory jurisdiction count
```

### Proxy Tier Hierarchy

| Tier | Description | Confidence |
|------|-------------|------------|
| 1 - Direct Observable | Market cap, regulated asset disclosures | High |
| 2 - Inferred Proxy | Employee count, tech stack, partner network | Medium |
| 3 - Cohort Inference | Similar entity comparisons | Low |
| 4 - Unknown | Insufficient data | Very Low |

### Exposure Bands

| Band | Score Range | Implied TIV |
|------|-------------|-------------|
| Micro | 0-15 | $0 - $1M |
| Small | 15-35 | $1M - $10M |
| Medium | 35-60 | $10M - $50M |
| Large | 60-85 | $50M - $250M |
| Very Large | 85-100 | $250M+ |

### Pricing Integration Patterns

**Pattern A - Parallel (Recommended)**
```python
base_premium = tier_based_premium(risk_tier)
exposure_modifier = get_exposure_modifier(exposure_band)
complexity_modifier = get_complexity_modifier(complexity_category)
adjusted_premium = base_premium * exposure_modifier * complexity_modifier
```

**Pattern B - Grid-Based**
```python
rate = pricing_grid[tier][exposure_band][complexity_category]
premium = rate * exposure_basis
```

## Critical Rules

1. **Parallel processing**: Exposure scoring runs alongside risk scoring, not in sequence
2. **Same signals, different weights**: Uses same extracted signals with exposure-specific weighting
3. **Proxy tier determines confidence**: Higher tier = higher confidence in estimate
4. **Bounded ranges acknowledge uncertainty**: Output ranges, not point estimates
5. **Cohort calibration improves over time**: Learn from actual TIV data when available
6. **High exposure + low confidence = referral**: Prevent auto-pricing uncertain large risks
7. **Complexity multiplies exposure**: More complex = higher pricing adjustment
8. **Full auditability**: Every pricing adjustment traces to signal patterns

## Workflow Integration

Extended 14-step workflow:

| Step | Description | Phase 17 Addition |
|------|-------------|-------------------|
| 4 | Signal extraction | + Exposure and complexity signals |
| 5a | Risk composite score | (unchanged) |
| **5b** | **Exposure magnitude score** | **NEW** |
| **5c** | **Complexity score** | **NEW** |
| 9 | Final tier capture | (unchanged) |
| **9b** | **Final exposure band capture** | **NEW** |
| **9c** | **Final complexity category capture** | **NEW** |
| 10 | Base premium generation | Uses tier + band + complexity |

## Implementation Tasks

| Task | File | Status |
|------|------|--------|
| Create exposure types | `exposure/types.py` | 🔲 Not Started |
| Implement ExposureScorer | `exposure/scorer.py` | 🔲 Not Started |
| Implement ComplexityScorer | `exposure/complexity.py` | 🔲 Not Started |
| Implement BandMapper | `exposure/band_mapper.py` | 🔲 Not Started |
| Implement CohortManager | `exposure/cohort_manager.py` | 🔲 Not Started |
| Implement ExposureRulesEngine | `exposure/rules_engine.py` | 🔲 Not Started |
| Extend YAML config schema | `coverages/*/config.yaml` | 🔲 Not Started |
| Extend ModelVersion | `model/types.py` | 🔲 Not Started |
| Integrate into workflow | `model/workflow.py` | 🔲 Not Started |
| Extend Pricer | `model/pricer.py` | 🔲 Not Started |
| Add unit tests | `tests/unit/test_exposure.py` | 🔲 Not Started |
| Add integration tests | `tests/integration/test_exposure_workflow.py` | 🔲 Not Started |

## File Structure

```
exposure/
├── __init__.py
├── types.py                  # All dataclasses and enums
├── scorer.py                 # Exposure magnitude calculation
├── complexity.py             # Complexity scoring
├── band_mapper.py            # Score-to-band mapping
├── cohort_manager.py         # Cohort prior management
├── rules_engine.py           # Auto-apply rules evaluation
└── shadow_layer/
    └── development/          # Specification documents (existing)
```

## Validation Requirements

Before deployment, the Exposure Shadow Layer must pass actuarial validation:

| Test | Threshold | Purpose |
|------|-----------|---------|
| Correlation | r ≥ 0.50 | Exposure score correlates with actual TIV |
| Discrimination | KS ≥ 0.30 | Bands represent meaningfully different exposures |
| Calibration | 75-85% coverage | Predicted ranges contain actual TIVs |
| Stability | r ≥ 0.40 all segments | Consistent across sectors and regions |
| Lift | ΔR² ≥ 0.10 | Adds value beyond simple proxies |

## Implementation Roadmap

| Phase | Objectives |
|-------|------------|
| 1. Validation Dataset | Collect historical submissions with verified TIVs |
| 2. Calibration | Extract exposure signals, tune weights, validate bands |
| 3. Integration | Workflow integration, pricing patterns, UI components |
| 4. Continuous Calibration | Cohort-based calibration, drift monitoring |

-----

**For complete implementation details, see**: `exposure/shadow_layer/development/plan.md`

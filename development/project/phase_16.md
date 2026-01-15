# Phase 16: Loss Signal Correlation Layer

## Purpose

Extend DSI from risk-quality scoring to **loss propensity prediction**, enabling:
- Loss likelihood scoring
- Cohort-based benchmarking
- Continuous monitoring
- Portfolio-level loss forecasting

This is the second intelligence layer of the DSI framework.

## Key Deliverables

- Loss propensity scorer
- Cohort analysis engine
- Continuous monitoring module
- Loss-signal correlation models
- Integration with pricing engine

## Status

✅ **COMPLETE** - Implemented 2026-01-15

## Detailed Specification

**Full specification documents are located in**: `layers/loss/development/`

| Document | Purpose |
|----------|---------|
| `plan.md` | Complete implementation plan with code examples |
| `specification.txt` | Technical specification and API details |
| `README.md` | Overview and quick start |

## Architecture Integration

The Loss Signal Correlation Layer runs in parallel with risk scoring:

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

### Loss Propensity Output

```python
@dataclass
class LossPropensityResult:
    loss_propensity_score: float      # 0-100
    severity_propensity_score: float  # 0-100
    loss_propensity_band: LossPropensityBand  # very_low → high
    loss_confidence: float            # 0-1
    cohort_id: str
    frequency_multiplier: float
    severity_multiplier: float
    combined_loss_modifier: float
    trend_direction: TrendDirection   # improving/stable/deteriorating
    referral_triggered: bool
```

### Pricing Impact

```python
# Pattern A - Multiplicative (recommended)
base_premium = tier_based_premium(risk_tier, exposure_band)
loss_adjusted_premium = base_premium * combined_loss_modifier
# combined_loss_modifier bounded by caps (1.50) and floors (0.70)
```

## Critical Rules

1. **Parallel processing**: Loss correlation runs alongside risk scoring, not in sequence
2. **Same signals, different weights**: Uses same extracted signals with loss-specific weighting
3. **Direction matters**: Negative correlation signals are inverted before scoring
4. **Confidence gates decisions**: Low confidence prevents automatic pricing adjustments
5. **Caps and floors apply**: Pricing impact bounded to prevent extreme adjustments
6. **Cohorts are signal-derived**: Not based on industry code or traditional segmentation
7. **Trend monitoring is continuous**: Not just at bind and renewal
8. **Correlation matrix requires calibration**: Initial weights are hypotheses, validated against loss data
9. **Deterioration triggers action**: Not just observation
10. **Full auditability**: Every pricing adjustment traces to signal patterns

## Implementation Tasks

| Task | File | Status |
|------|------|--------|
| Create loss correlation types | `layers/loss/types.py` | ✅ Complete |
| Implement LossCorrelationScorer | `layers/loss/scorer.py` | ✅ Complete |
| Implement CorrelationMatrixManager | `layers/loss/matrix.py` | ✅ Complete |
| Implement LossMonitoringEngine | `layers/loss/monitoring.py` | ✅ Complete |
| Add pricing integration | `layers/loss/integration.py` | ✅ Complete |
| Extend YAML config schema | `coverages/cyber/config.yaml` | ✅ Complete |
| Extend ModelVersion for loss data | `layers/risk/types.py` | ✅ Complete |
| Integrate into workflow | `layers/risk/workflow.py` | ✅ Complete |
| Add unit tests | `tests/unit/test_loss_correlation.py` | ✅ Complete |
| Add integration tests | `tests/integration/test_loss_workflow.py` | ✅ Complete |

## File Structure (Post-Phase 18 Restructuring)

```
layers/
├── loss/                            # Loss Correlation Layer (Phase 16)
│   ├── __init__.py                  ✅ Module exports
│   ├── types.py                     ✅ All dataclasses and enums
│   ├── scorer.py                    ✅ LossCorrelationScorer
│   ├── matrix.py                    ✅ CorrelationMatrixManager
│   ├── monitoring.py                ✅ LossMonitoringEngine
│   ├── integration.py               ✅ LossPricingIntegration
│   └── development/                 # Specification documents
│       ├── README.md
│       ├── plan.md
│       └── specification.txt
├── risk/                            # Risk Layer (extended)
│   ├── types.py                     ✅ ModelVersion with loss fields
│   └── workflow.py                  ✅ Loss propensity integration

coverages/
├── cyber/config.yaml                ✅ loss_correlation schema added
```

## Components Implemented

### 1. LossCorrelationScorer (`layers/loss/scorer.py`)
- Calculates loss propensity from signal outputs
- Separate frequency and severity scoring
- Cohort assignment based on signal patterns
- Trend analysis with velocity tracking
- Auto-apply rules for referrals/flags

### 2. CorrelationMatrixManager (`layers/loss/matrix.py`)
- Calibrates signal-loss correlations from historical data
- Pearson correlation coefficient calculation
- Information value scoring for predictive power
- Stability scoring across time periods
- JSON persistence for correlation matrices

### 3. LossMonitoringEngine (`layers/loss/monitoring.py`)
- Continuous portfolio monitoring
- Deterioration alerts (warning/critical)
- Band migration detection
- Velocity spike detection
- Portfolio-wide statistics

### 4. LossPricingIntegration (`layers/loss/integration.py`)
- Three pricing patterns: multiplicative, additive, grid
- Configurable caps and floors
- Confidence threshold gating
- Default pricing grid generation

### 5. ModelVersion Extensions (`layers/risk/types.py`)
17 new fields added:
- `loss_propensity_score`, `severity_propensity_score`
- `loss_propensity_band`, `severity_propensity_band`
- `loss_confidence`
- `loss_cohort_id`, `loss_cohort_name`, `loss_cohort_confidence`
- `loss_frequency_multiplier`, `loss_severity_multiplier`, `loss_combined_modifier`
- `loss_trend_direction`, `loss_previous_score`, `loss_score_velocity`
- `loss_last_refresh`
- `correlation_matrix_version`, `correlation_matrix_hash`

### 6. Workflow Integration (`layers/risk/workflow.py`)
- `_calculate_loss_propensity()` method added
- Called after Step 4-6 (parallel to risk scoring)
- Loss modifier added to pricing modifiers
- Loss referrals integrated into decision
- Model version populated with loss fields

## Implementation Roadmap

| Phase | Objectives | Status |
|-------|------------|--------|
| 1. Retrospective Analysis | Partner with carrier for historical data, build initial correlation matrix | 🔲 Requires Data Partner |
| 2. Prospective Tagging | Tag new submissions with signal snapshots, track loss emergence | 🔲 Requires Production Use |
| 3. Pricing Integration | Production scoring, pricing adjustments, continuous monitoring | ✅ Code Complete |
| 4. Continuous Calibration | Automated recalibration, dynamic cohorts, ML enhancement | 🔲 Future Enhancement |

-----

**Implementation complete. Ready for carrier data integration and production validation.**

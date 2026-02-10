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

🔲 **Not Started** - Specification Complete

## Detailed Specification

**Full specification documents are located in**: `loss/correlation_layer/development/`

| Document | Purpose |
|----------|---------|
| `plan.md` | Complete implementation plan with code examples |
| `specification.txt` | Technical specification and API details |
| `README.md` | Overview and quick start |

**Do not duplicate specification content here.** Refer to the detailed documents for:
- Core types and dataclasses
- LossCorrelationScorer implementation
- CorrelationMatrixManager implementation
- LossMonitoringEngine implementation
- YAML configuration schema
- Pricing integration patterns

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
| Create loss correlation types | `model/loss_correlation/types.py` | 🔲 Not Started |
| Implement LossCorrelationScorer | `model/loss_correlation/scorer.py` | 🔲 Not Started |
| Implement CorrelationMatrixManager | `model/loss_correlation/matrix.py` | 🔲 Not Started |
| Implement LossMonitoringEngine | `model/loss_correlation/monitoring.py` | 🔲 Not Started |
| Add pricing integration | `model/loss_correlation/integration.py` | 🔲 Not Started |
| Extend YAML config schema | `coverages/*/config.yaml` | 🔲 Not Started |
| Extend ModelVersion for loss data | `model/types.py` | 🔲 Not Started |
| Integrate into workflow | `model/workflow.py` | 🔲 Not Started |
| Add unit tests | `tests/unit/test_loss_correlation.py` | 🔲 Not Started |
| Add integration tests | `tests/integration/test_loss_workflow.py` | 🔲 Not Started |

## File Structure

```
technical_pricing/
├── model/
│   ├── loss_correlation/
│   │   ├── __init__.py
│   │   ├── types.py              # All dataclasses and enums
│   │   ├── scorer.py             # Loss propensity calculation
│   │   ├── matrix.py             # Correlation matrix management
│   │   ├── monitoring.py         # Continuous monitoring engine
│   │   └── integration.py        # Pricing integration patterns
│   └── ...
```

## Implementation Roadmap

| Phase | Objectives |
|-------|------------|
| 1. Retrospective Analysis | Partner with carrier for historical data, build initial correlation matrix |
| 2. Prospective Tagging | Tag new submissions with signal snapshots, track loss emergence |
| 3. Pricing Integration | Production scoring, pricing adjustments, continuous monitoring |
| 4. Continuous Calibration | Automated recalibration, dynamic cohorts, ML enhancement |

-----

**For complete implementation details, see**: `loss/correlation_layer/development/plan.md`

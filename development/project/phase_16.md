# Phase 16: Loss Signal Correlation Layer

## Purpose
Extend DSI from risk‑quality scoring to **loss propensity prediction**, enabling:
- Loss likelihood scoring
- Cohort‑based benchmarking
- Continuous monitoring
- Portfolio‑level loss forecasting

This is the second intelligence layer of the DSI framework.

## Key Deliverables
- Loss propensity scorer
- Cohort analysis engine
- Continuous monitoring module
- Loss‑signal correlation models
- Integration with pricing engine

## Implementation Summary
This phase introduces a new scoring dimension: **loss correlation**.  
Where the existing DSI engine measures *risk quality*, this layer measures *expected loss behaviour* by correlating signals with historical loss outcomes.

## Detailed Plan

**Full specification documents**: `loss/correlation_layer/development/`

### 16.1 The Loss Analysis Problem

Traditional loss analysis suffers from:
- **Data Sparsity**: 80-90% of policies have zero claims in any given year
- **Feature Poverty**: Only 5-10 features available vs 200-400 DSI signals
- **Attribution Impossibility**: Weak correlations at portfolio level only
- **Emergence Lag**: 6-48 months for loss patterns to become visible
- **Aggregation Masking**: Profitable business subsidizes unprofitable business

**DSI Solution**: Use 200-400 observable signals to identify patterns that precede and predict loss events.

### 16.2 Architecture Integration

The Loss Signal Correlation Layer runs in parallel with risk scoring:

```
┌─────────────────────────────────────────────────────────────────┐
│                    ENHANCED DSI ARCHITECTURE                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                     SIGNAL EXTRACTION                    │   │
│  │                    (Steps 0-4 unchanged)                 │   │
│  └──────────────────────────────────────────────────────────┘   │
│                              │                                  │
│              ┌───────────────┼───────────────┐                  │
│              │               │               │                  │
│              ▼               ▼               ▼                  │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐             │
│  │ RISK SCORING │ │  EXPOSURE    │ │    LOSS      │             │
│  │              │ │  SHADOW      │ │ CORRELATION  │             │
│  │ Steps 5-6    │ │  LAYER       │ │    LAYER     │             │
│  │ Composite    │ │              │ │              │             │
│  │ + Conditions │ │ Exposure Band│ │ Propensity   │             │
│  │              │ │ + Complexity │ │ + Cohort     │             │
│  └──────────────┘ └──────────────┘ └──────────────┘             │
│              │               │               │                  │
│              └───────────────┼───────────────┘                  │
│                              │                                  │
│                              ▼                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    PRICING ENGINE                        │   │
│  │                                                          │   │
│  │  Risk Tier × Exposure Band × Loss Propensity → Premium   │   │
│  │                                                          │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 16.3 Core Components

#### 16.3.1 Loss Propensity Output

```python
@dataclass
class LossPropensityResult:
    """Complete output from loss propensity calculation"""
    # Primary scores
    loss_propensity_score: float  # 0-100
    severity_propensity_score: float  # 0-100
    loss_propensity_band: LossPropensityBand  # very_low, low, moderate, elevated, high
    severity_propensity_band: SeverityPropensityBand  # minimal, moderate, significant, severe, catastrophic
    loss_confidence: float  # 0-1

    # Cohort assignment
    cohort_id: str
    cohort_name: str
    cohort_confidence: float

    # Pricing impact
    frequency_multiplier: float
    severity_multiplier: float
    combined_loss_modifier: float

    # Monitoring
    trend_direction: TrendDirection  # improving, stable, deteriorating
    score_velocity: float  # points per month

    # Referral triggers
    referral_triggered: bool
    referral_reasons: List[str]
    flags: List[str]
```

#### 16.3.2 Loss Correlation Scorer (`model/loss_correlation/scorer.py`)

Calculates loss propensity from signal outputs using loss-specific weighting:

```python
class LossCorrelationScorer:
    """
    Calculates loss propensity scores from signal outputs.
    Uses same signals as risk scoring but with loss-specific weights.
    """

    def calculate_propensity(
        self,
        signal_outputs: List[SignalOutput],
        previous_result: Optional[LossPropensityResult] = None
    ) -> LossPropensityResult:
        """
        Calculate loss propensity from signal outputs.
        Runs in parallel with risk scoring (Steps 5-6).
        """
```

#### 16.3.3 Correlation Matrix Manager (`model/loss_correlation/matrix.py`)

Manages empirically-derived signal-loss correlations:

```python
class CorrelationMatrixManager:
    """
    Manages the loss correlation matrix - relationships between
    signals and loss outcomes validated against historical data.
    """

    def calibrate(
        self,
        policies: List[Dict],  # Policy data with signal snapshots
        losses: List[Dict],    # Loss data linked to policies
    ) -> CorrelationMatrix:
        """Calibrate correlation matrix from historical data."""
```

#### 16.3.4 Monitoring Engine (`model/loss_correlation/monitoring.py`)

Continuous monitoring for in-force policies:

```python
class LossMonitoringEngine:
    """
    Continuous monitoring of loss propensity for in-force policies.
    Detects deterioration, triggers alerts, and recommends actions.
    """

    def check_entity(
        self,
        entity_id: str,
        signal_outputs: List,
        force_refresh: bool = False
    ) -> MonitoringResult:
        """Check an entity's loss propensity and generate alerts."""
```

### 16.4 Canonical Loss-Predictive Signals

28 signals with hypothesized loss correlation:

| Category | Signals | Correlation Type |
|-|-|-|
| Network Authority | certification_authority_score, partner_quality_index, customer_concentration, regulatory_standing_score | Both |
| Technical Infrastructure | security_header_completeness, tls_configuration_score, software_currency_index, exposed_service_count, dns_security_score | Frequency |
| Corporate Footprint | content_recency_score, leadership_visibility_index, hiring_activity_trend, policy_documentation_score, crisis_communication_presence | Both |
| Behavioural | management_stability_index, regulatory_engagement_pattern, incident_response_history, change_velocity_score, disclosure_consistency | Severity |
| Public Record | litigation_frequency, regulatory_action_history, bankruptcy_proximity_signals, ownership_change_frequency, ip_filing_trend | Frequency |
| Structured Data | credit_rating_trajectory, esg_score_trend, financial_ratio_anomalies, peer_comparison_rank | Both |

### 16.5 YAML Configuration Extension

```yaml
loss_correlation:
  enabled: true
  version: "2026-01-08"

  correlation_groups:
    - name: loss_technical_infrastructure
      weight: 0.35
      confidence_threshold: 0.7
      features:
        - id: security_header_completeness
          weight: 0.30
          correlation_type: both      # frequency, severity, or both
          correlation_direction: negative  # higher signal = lower loss
          normalizer: linear
          lag_months: 6

  propensity_band_mapping:
    method: fixed_threshold
    bands:
      - name: very_low
        min_score: 0
        max_score: 20
        expected_frequency_multiplier: 0.60
        expected_severity_multiplier: 0.70
      - name: elevated
        min_score: 60
        max_score: 80
        expected_frequency_multiplier: 1.25
        expected_severity_multiplier: 1.15

  pricing_integration:
    method: multiplicative
    frequency_impact_cap: 1.50
    frequency_impact_floor: 0.70
    frequency_weight: 0.60
    severity_weight: 0.40

  auto_apply_rules:
    - condition: "loss_propensity_band == 'high' AND loss_confidence >= 0.8"
      action: refer
      reason: "High loss propensity with high confidence"

  monitoring:
    refresh_frequency: monthly
    deterioration_threshold: 15
```

### 16.6 Pricing Integration Patterns

**Pattern A — Multiplicative Adjustment (Recommended)**

```python
base_premium = tier_based_premium(risk_tier, exposure_band)
loss_adjusted_premium = base_premium * combined_loss_modifier

# Where:
combined_loss_modifier = (
    (frequency_multiplier * frequency_weight) +
    (severity_multiplier * severity_weight)
)
# Bounded by caps and floors
```

**Pattern B — Grid-Based Pricing**

```yaml
pricing_grid:
  tier_1:
    very_low: 0.0035
    low: 0.0040
    moderate: 0.0045
    elevated: 0.0055
    high: 0.0070
```

### 16.7 Model Version Extensions

```python
# Add to ModelVersion dataclass:

# Loss Propensity Outputs
loss_propensity_score: Optional[float] = None
severity_propensity_score: Optional[float] = None
loss_propensity_band: Optional[str] = None
loss_confidence: Optional[float] = None

# Cohort Assignment
loss_cohort_id: Optional[str] = None
loss_cohort_name: Optional[str] = None

# Pricing Impact
loss_frequency_multiplier: Optional[float] = None
loss_severity_multiplier: Optional[float] = None
loss_combined_modifier: Optional[float] = None

# Monitoring State
loss_trend_direction: Optional[str] = None
loss_previous_score: Optional[float] = None
loss_score_velocity: Optional[float] = None
```

### 16.8 Implementation Roadmap

| Phase | Timeline | Objectives |
|-|-|-|
| 1. Retrospective Analysis | Months 1-6 | Partner with carrier for historical data, build initial correlation matrix |
| 2. Prospective Tagging | Months 6-18 | Tag new submissions with signal snapshots, track loss emergence |
| 3. Pricing Integration | Months 12-24 | Production scoring, pricing adjustments, continuous monitoring |
| 4. Continuous Calibration | Months 18+ | Automated recalibration, dynamic cohorts, ML enhancement |

### 16.9 Critical Rules

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

### 16.10 Implementation Tasks

| Task | File | Status |
|-|-|-|
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

### 16.11 File Structure for Phase 16

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

-----

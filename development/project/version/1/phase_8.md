# Phase 8: Analytics Engine

## Purpose
Provide analytics capabilities for performance tuning, signal analysis, and cohort evaluation.

## Key Deliverables
- Performance analytics
- Signal analytics
- Tuning utilities
- Cohort analysis

## Implementation Summary
This phase introduces a full analytics suite enabling model introspection, performance evaluation, and signal‑level diagnostics. It supports both single‑entity and portfolio‑level analysis.

## Detailed Plan

This phase implements performance tracking against actual losses, pattern identification, and model tuning capabilities.

### 8.1 The Monitoring Problem

DSI produces risk assessments, but we need to:
- **Track Accuracy**: Compare predictions to actual outcomes
- **Identify Patterns**: Find systematic over/under-pricing
- **Tune Models**: Adjust weights and thresholds based on evidence
- **Cohort Analysis**: Compare similar risks to identify discrepancies

### 8.2 Performance Tracking Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                 PERFORMANCE MONITORING SYSTEM                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐       │
│  │ DSI OUTPUT   │    │ ACTUAL       │    │ COMPARISON   │       │
│  │              │    │ OUTCOMES     │    │ ENGINE       │       │
│  │ • Score      │ +  │ • Claims     │ →  │ • Accuracy   │       │
│  │ • Tier       │    │ • Losses     │    │ • Bias       │       │
│  │ • Premium    │    │ • Events     │    │ • Patterns   │       │
│  └──────────────┘    └──────────────┘    └──────────────┘       │
│                                                                 │
│                              │                                  │
│                              ▼                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    ANALYTICS OUTPUTS                     │   │
│  │                                                          │   │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐          │   │
│  │  │ REPORTS    │  │ ALERTS     │  │ TUNING     │          │   │
│  │  │            │  │            │  │ RECS       │          │   │
│  │  │ • By tier  │  │ • Drift    │  │ • Weights  │          │   │
│  │  │ • By signal│  │ • Anomaly  │  │ • Thresholds│         │   │
│  │  │ • By cohort│  │ • Trend    │  │ • Signals  │          │   │
│  │  └────────────┘  └────────────┘  └────────────┘          │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                 │
│                              │                                  │
│                              ▼                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    ML ENHANCEMENT (Optional)             │   │
│  │                                                          │   │
│  │  • Gradient boosting for weight optimization             │   │
│  │  • Anomaly detection for outlier identification          │   │
│  │  • Time series for trend prediction                      │   │
│  │  • Clustering for cohort discovery                       │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 8.3 Data Structures

```python
@dataclass
class OutcomeRecord:
    """Actual outcome for a priced risk"""
    entity_id: str
    model_id: str
    policy_inception: date
    policy_expiry: date

    # What we predicted
    dsi_score: float
    dsi_tier: int
    quoted_premium: float
    bound_premium: float  # May differ from quote

    # What actually happened
    claim_count: int
    incurred_losses: float
    large_losses: List[float]
    loss_ratio: float

    # Metadata
    coverage: str
    configuration: str
    recorded_at: datetime

@dataclass
class PerformanceMetrics:
    """Aggregated performance metrics"""
    period: str  # 'monthly', 'quarterly', 'annual'
    start_date: date
    end_date: date

    # Accuracy metrics
    tier_accuracy: float  # % where tier matched outcome
    score_correlation: float  # Correlation with loss ratio
    lift_curve_auc: float  # Area under lift curve

    # Bias metrics
    average_prediction_error: float
    systematic_bias: float  # Over/under-pricing trend

    # By tier breakdown
    tier_metrics: Dict[int, TierPerformance]

    # By signal breakdown
    signal_contribution: Dict[str, SignalPerformance]

@dataclass
class TierPerformance:
    tier: int
    count: int
    average_score: float
    average_loss_ratio: float
    expected_loss_ratio: float
    actual_vs_expected: float

@dataclass
class CohortDefinition:
    """Definition of a comparison cohort"""
    cohort_id: str
    name: str
    criteria: Dict[str, Any]  # Filters
    # e.g., {"coverage": "fi", "tier": [1,2], "size": "large"}
```

### 8.4 Cohort Analysis

```python
class CohortAnalyzer:
    """
    Compare performance of similar risks.

    Use cases:
    - Large banks vs other large banks
    - Tech companies by tier
    - Geographic performance differences
    """

    def define_cohort(
        self,
        name: str,
        coverage: str,
        filters: Dict[str, Any]
    ) -> CohortDefinition:
        """Create a cohort for comparison"""
        pass

    def compare_cohorts(
        self,
        cohort_a: str,
        cohort_b: str,
        metrics: List[str]
    ) -> CohortComparison:
        """Compare two cohorts on specified metrics"""
        pass

    def identify_outliers(
        self,
        cohort: str,
        threshold: float = 2.0  # Standard deviations
    ) -> List[OutlierRisk]:
        """Find risks that deviate from cohort norm"""
        pass

    def suggest_cohort_adjustments(
        self,
        cohort: str
    ) -> List[TuningRecommendation]:
        """Suggest signal weight adjustments for cohort"""
        pass
```

### 8.5 Auto-Tuning System

```python
class ModelTuner:
    """
    Automated model tuning based on performance data.

    Modes:
    - Manual: Generate recommendations for human review
    - Semi-auto: Apply recommendations with approval
    - Auto: Automatically adjust within bounds
    """

    def analyze_performance(
        self,
        coverage: str,
        period: str = "12_months"
    ) -> PerformanceAnalysis:
        """Analyze model performance over period"""
        pass

    def generate_recommendations(
        self,
        analysis: PerformanceAnalysis
    ) -> List[TuningRecommendation]:
        """
        Generate tuning recommendations:
        - Weight adjustments
        - Threshold changes
        - Signal additions/deprecations
        """
        pass

    def apply_tuning(
        self,
        recommendations: List[TuningRecommendation],
        mode: str = "manual"  # manual, semi_auto, auto
    ) -> TuningResult:
        """Apply recommendations based on mode"""
        pass

    def backtest_tuning(
        self,
        recommendations: List[TuningRecommendation],
        historical_data: List[OutcomeRecord]
    ) -> BacktestResult:
        """Test recommendations against historical data"""
        pass

@dataclass
class TuningRecommendation:
    """A specific tuning recommendation"""
    recommendation_id: str
    type: str  # 'weight_adjust', 'threshold_adjust', 'signal_add', 'signal_deprecate'
    target: str  # Signal or group ID
    current_value: Any
    recommended_value: Any
    expected_impact: float  # Estimated improvement
    confidence: float
    rationale: str
    evidence: Dict[str, Any]
```

### 8.6 ML Integration (Optional)

```python
class MLEnhancedTuner:
    """
    ML-powered tuning and prediction.

    Models:
    - XGBoost/LightGBM for weight optimization
    - Isolation Forest for anomaly detection
    - K-Means for cohort discovery
    - ARIMA for trend prediction
    """

    def optimize_weights(
        self,
        historical_data: pd.DataFrame,
        target: str = "loss_ratio"
    ) -> Dict[str, float]:
        """Use gradient boosting to find optimal weights"""
        pass

    def detect_anomalies(
        self,
        recent_submissions: List[ModelVersion]
    ) -> List[AnomalyAlert]:
        """Identify unusual patterns in recent submissions"""
        pass

    def discover_cohorts(
        self,
        portfolio_data: pd.DataFrame,
        n_clusters: int = 5
    ) -> List[DiscoveredCohort]:
        """Automatically discover natural cohorts"""
        pass

    def predict_trend(
        self,
        metric: str,
        horizon: int = 12  # months
    ) -> TrendPrediction:
        """Predict future performance trend"""
        pass
```

### 8.7 Implementation Tasks

| Task | File | Status |
|-|-|-|
| Create OutcomeRecord and metrics types | `analytics/types.py` | ✅ Complete |
| Implement PerformanceTracker | `analytics/performance.py` | ✅ Complete |
| Implement CohortAnalyzer | `analytics/cohorts.py` | ✅ Complete |
| Implement ModelTuner | `analytics/tuning.py` | ✅ Complete |
| Create ML module (optional) | `analytics/ml/` | 🔲 Optional |
| Add outcome ingestion API | `api/outcomes.py` | ✅ Complete |
| Create performance dashboards | `analytics/dashboards.py` | 🔲 Optional |
| Add unit tests | `tests/unit/test_analytics.py` | ✅ Complete |


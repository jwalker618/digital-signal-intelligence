# ${\color{blue}Digital\space Signal\space Intelligence\space (DSI)}$

## A New Information Substrate for Insurance

| Item | Value |
|-|-|
|Version|0.1.0|
|Date|January 2025|
|Classification|exposure|

---

# DSI Exposure Shadow Layer — Technical Specification v2.0

## Document Control

|Version|Date      |Author|Changes                                                                                                 |
|-------|----------|------|--------------------------------------------------------------------------------------------------------|
|1.0    |2025-12-28|-     |Initial specification                                                                                   |
|2.0    |2025-12-29|-     |Revised with coverage-specific weights, tiered proxy hierarchy, complexity scoring, unified architecture|

-----

## 1. Executive Summary

The Exposure Shadow Layer extends DSI’s observable-signal methodology to estimate **exposure magnitude** and **exposure complexity** without requiring client-provided schedules, bordereaux, or asset declarations. It runs as a parallel scoring system alongside risk quality assessment, enabling two-dimensional pricing (risk tier × exposure band) while maintaining full auditability.

### Key Enhancements in v2.0

1. **Tiered Proxy Hierarchy** — Direct observables prioritized over inferred signals
1. **Complexity Scoring** — Separate magnitude and complexity dimensions
1. **Coverage-Specific Weights** — Signal relevance varies by coverage type
1. **Bounded Range Outputs** — Ranges rather than point estimates
1. **Unified Signal Architecture** — Reuses existing Extractor → Aggregator → Categorizer → Inference pipeline
1. **Incremental Calibration Strategy** — Bootstrap path from fixed thresholds to cohort quantiles

-----

## 2. Conceptual Foundation

### 2.1 The Separation Principle

DSI distinguishes between two orthogonal dimensions:

|Dimension              |Question                                       |Output                                                     |
|-----------------------|-----------------------------------------------|-----------------------------------------------------------|
|**Risk Quality**       |How well-managed is this risk?                 |Risk Score (0-1000) → Tier (1-5)                           |
|**Exposure Magnitude** |How large is the insurable exposure?           |Exposure Score (0-100) → Band (micro-very_large)           |
|**Exposure Complexity**|How distributed/interconnected is the exposure?|Complexity Score (0-100) → Category (simple-highly_complex)|

A large, well-managed bank (high exposure, good risk) prices differently than a small, poorly-managed startup (low exposure, poor risk). Conflating size and quality produces actuarially unsound results.

### 2.2 The Observable Exposure Thesis

Traditional exposure estimation requires:

- Statements of Value (SOVs)
- Asset schedules
- Revenue/payroll declarations
- Bordereaux

DSI’s thesis: **Observable digital signals correlate with exposure magnitude**. An entity’s digital footprint, network position, regulatory presence, and partner ecosystem reveal scale without self-reporting.

### 2.3 Confidence and Uncertainty

Unlike risk signals (where absence often indicates poor practice), exposure signal absence may indicate:

- Very small entity (true low exposure)
- Detection failure (unknown exposure)
- Atypical digital presence (unreliable inference)

The system explicitly tracks uncertainty and outputs bounded ranges rather than false-precision point estimates.

-----

## 3. Architecture Overview

### 3.1 Unified Signal Architecture

Exposure scoring reuses the existing DSI signal pipeline with a type distinction:

```
┌─────────────────────────────────────────────────────────────────┐
│                    UNIFIED SIGNAL ARCHITECTURE                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    YAML CONFIG                            │   │
│  │                                                           │   │
│  │  signal_groups:                                           │   │
│  │    - name: financial_stability                            │   │
│  │      signal_type: risk          ← contributes to risk     │   │
│  │      weight: 0.20                                         │   │
│  │                                                           │   │
│  │    - name: exposure_digital_footprint                     │   │
│  │      signal_type: exposure      ← contributes to exposure │   │
│  │      weight: 0.30                                         │   │
│  │                                                           │   │
│  │    - name: exposure_complexity                            │   │
│  │      signal_type: complexity    ← contributes to complexity│  │
│  │      weight: 0.25                                         │   │
│  └──────────────────────────────────────────────────────────┘   │
│                              │                                   │
│                              ▼                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              SHARED SIGNAL PIPELINE                       │   │
│  │                                                           │   │
│  │  EXTRACTOR → AGGREGATOR → CATEGORIZER → INFERENCE         │   │
│  │                                                           │   │
│  │  Same infrastructure, different output targets            │   │
│  └──────────────────────────────────────────────────────────┘   │
│                              │                                   │
│              ┌───────────────┼───────────────┐                  │
│              ▼               ▼               ▼                  │
│  ┌────────────────┐ ┌────────────────┐ ┌────────────────┐       │
│  │  RISK SCORER   │ │EXPOSURE SCORER │ │COMPLEXITY SCORER│      │
│  │                │ │                │ │                │       │
│  │  Composite:    │ │  Magnitude:    │ │  Distribution: │       │
│  │  0-1000        │ │  0-100         │ │  0-100         │       │
│  │  → Tier 1-5    │ │  → Band        │ │  → Category    │       │
│  └────────────────┘ └────────────────┘ └────────────────┘       │
│              │               │               │                  │
│              └───────────────┼───────────────┘                  │
│                              ▼                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    PRICER                                 │   │
│  │                                                           │   │
│  │  Pricing Method:                                          │   │
│  │  - Pattern A: Parallel (exposure as modifier)             │   │
│  │  - Pattern B: Embedded (exposure in composite)            │   │
│  │  - Pattern C: Grid (tier × band × complexity matrix)      │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 Workflow Integration

The 14-step DSI workflow extends to accommodate exposure:

```
Step 0:   Discovery (website identification)
Step 1:   Configuration instantiation
Step 2:   Model data file creation
Step 3:   Minimum viable input verification
Step 4:   Signal extraction (risk + exposure + complexity)
Step 5a:  Risk composite score calculation
Step 5b:  Exposure magnitude score calculation      ← NEW
Step 5c:  Exposure complexity score calculation     ← NEW
Step 6:   Signal conditions evaluation (all types)
Step 7:   Direct query response evaluation
Step 8:   Maximum tier override application
Step 9:   Final tier capture
Step 9b:  Final exposure band capture               ← NEW
Step 9c:  Final complexity category capture         ← NEW
Step 10:  Base premium generation (using tier + band + complexity)
Step 11:  Modifier application
Step 12:  Limit band scaling
Step 13:  Output decision
```

-----

## 4. Tiered Proxy Hierarchy

### 4.1 Reliability Tiers

Not all exposure signals have equal reliability. The system uses a hierarchy:

```
┌─────────────────────────────────────────────────────────────────┐
│                    PROXY RELIABILITY HIERARCHY                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  TIER 1: DIRECT OBSERVABLES (Confidence: 0.85-1.0)              │
│  ────────────────────────────────────────────────                │
│  • Public company financials (market cap, revenue, assets)       │
│  • Regulatory filings (banks, insurers, utilities)               │
│  • Government registrations (employee count bands)               │
│  • Listed fleet/asset registrations (marine, aviation)           │
│                                                                  │
│  When available, these override lower tiers.                     │
│                                                                  │
│  TIER 2: INFERRED PROXIES (Confidence: 0.60-0.85)               │
│  ────────────────────────────────────────────────                │
│  • Digital footprint signals (domains, tech stack, web reach)    │
│  • Network authority signals (partners, certifications)          │
│  • Geographic presence signals (locations, regulatory citations) │
│  • Distribution proxy signals (broker tier, programme flag)      │
│                                                                  │
│  Used when Tier 1 unavailable. Multiple signals aggregated.      │
│                                                                  │
│  TIER 3: COHORT INFERENCE (Confidence: 0.40-0.60)               │
│  ────────────────────────────────────────────────                │
│  • Sector + digital footprint band → implied TIV range           │
│  • Region + network authority band → implied scale               │
│  • Historical portfolio cohort matching                          │
│                                                                  │
│  Fallback when Tier 1-2 insufficient. Wide confidence bands.     │
│                                                                  │
│  TIER 4: UNKNOWN (Confidence: 0.0-0.40)                         │
│  ────────────────────────────────────────────────                │
│  • Insufficient signal availability                              │
│  • Detection failure suspected                                   │
│  • Mandatory referral triggered                                  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 4.2 Tier Selection Logic

```python
def select_exposure_tier(signals: ExposureSignals) -> ProxyTier:
    """
    Select highest-reliability tier with sufficient data.
    """
    # Tier 1: Check for direct observables
    if signals.has_public_financials():
        return ProxyTier.DIRECT_OBSERVABLE
    if signals.has_regulatory_filings():
        return ProxyTier.DIRECT_OBSERVABLE
    if signals.has_registered_assets():
        return ProxyTier.DIRECT_OBSERVABLE
    
    # Tier 2: Check inferred proxy availability
    available_signals = signals.count_available_inferred()
    if available_signals >= 4 and signals.average_confidence() >= 0.6:
        return ProxyTier.INFERRED_PROXY
    
    # Tier 3: Check cohort matching feasibility
    if signals.can_match_cohort():
        return ProxyTier.COHORT_INFERENCE
    
    # Tier 4: Insufficient data
    return ProxyTier.UNKNOWN
```

-----

## 5. Signal Definitions

### 5.1 Canonical Exposure Signals

#### 5.1.1 Magnitude Signals

|Signal ID                  |Description                  |Data Source            |Reliability|
|---------------------------|-----------------------------|-----------------------|-----------|
|`public_market_cap`        |Market capitalization        |Stock exchanges        |Tier 1     |
|`public_revenue`           |Reported annual revenue      |SEC/Companies House    |Tier 1     |
|`public_assets`            |Total assets on balance sheet|Regulatory filings     |Tier 1     |
|`registered_employee_count`|Official employee band       |Government registries  |Tier 1     |
|`domain_count`             |Number of owned domains      |DNS/WHOIS              |Tier 2     |
|`subdomain_complexity`     |Subdomain tree depth/breadth |DNS enumeration        |Tier 2     |
|`tech_stack_count`         |Detected technologies        |Wappalyzer/BuiltWith   |Tier 2     |
|`web_reach_proxy`          |Traffic/engagement estimates |SimilarWeb/Alexa       |Tier 2     |
|`marquee_partner_count`    |Major client/partner mentions|Web scraping           |Tier 2     |
|`location_count`           |Physical locations detected  |Google Places/Maps     |Tier 2     |
|`regulatory_citation_count`|Regulatory body mentions     |Regulatory databases   |Tier 2     |
|`systemic_link_score`      |Network centrality measure   |Link analysis          |Tier 2     |
|`broker_tier`              |Submitting broker size tier  |Internal classification|Tier 2     |
|`programme_complexity_flag`|Multi-layer/multi-territory  |Submission metadata    |Tier 2     |

#### 5.1.2 Complexity Signals

|Signal ID                      |Description                   |Indicator            |
|-------------------------------|------------------------------|---------------------|
|`geographic_dispersion`        |Countries/regions of operation|Higher = more complex|
|`subsidiary_count`             |Number of legal entities      |Higher = more complex|
|`technology_heterogeneity`     |Diversity of tech stacks      |Higher = more complex|
|`regulatory_jurisdiction_count`|Number of regulatory regimes  |Higher = more complex|
|`supply_chain_depth`           |Tier depth in supply networks |Higher = more complex|
|`customer_concentration`       |Revenue concentration index   |Lower = more complex |
|`product_line_count`           |Distinct product/service lines|Higher = more complex|
|`acquisition_frequency`        |M&A activity rate             |Higher = more complex|

### 5.2 Coverage-Specific Signal Weights

Signal relevance varies significantly by coverage. Weights are configured per coverage in YAML:

#### Cyber Coverage

```yaml
exposure:
  signal_groups:
    - name: exposure_digital_footprint
      signal_type: exposure
      weight: 0.40  # High weight - digital footprint directly correlates
      features:
        - id: domain_count
          weight: 0.20
        - id: subdomain_complexity
          weight: 0.25
        - id: tech_stack_count
          weight: 0.35
        - id: web_reach_proxy
          weight: 0.20
    
    - name: exposure_network_authority
      signal_type: exposure
      weight: 0.25
      features:
        - id: marquee_partner_count
          weight: 0.50
        - id: systemic_link_score
          weight: 0.50
    
    - name: exposure_scale_proxy
      signal_type: exposure
      weight: 0.35
      features:
        - id: public_revenue
          weight: 0.40
          tier: 1
        - id: registered_employee_count
          weight: 0.30
          tier: 1
        - id: location_count
          weight: 0.30
          tier: 2
```

#### Marine Coverage

```yaml
exposure:
  signal_groups:
    - name: exposure_fleet_scale
      signal_type: exposure
      weight: 0.50  # Fleet size is primary driver
      features:
        - id: registered_vessel_count
          weight: 0.50
          tier: 1
        - id: aggregate_dwt
          weight: 0.30
          tier: 1
        - id: port_call_frequency
          weight: 0.20
          tier: 2
    
    - name: exposure_geographic
      signal_type: exposure
      weight: 0.30
      features:
        - id: trading_region_count
          weight: 0.40
        - id: high_risk_region_pct
          weight: 0.60
    
    - name: exposure_network
      signal_type: exposure
      weight: 0.20
      features:
        - id: charterer_quality_score
          weight: 0.50
        - id: p_and_i_club_tier
          weight: 0.50
```

#### Financial Institutions Coverage

```yaml
exposure:
  signal_groups:
    - name: exposure_balance_sheet
      signal_type: exposure
      weight: 0.45
      features:
        - id: public_assets
          weight: 0.50
          tier: 1
        - id: regulatory_capital_tier
          weight: 0.30
          tier: 1
        - id: deposit_base_estimate
          weight: 0.20
          tier: 2
    
    - name: exposure_systemic
      signal_type: exposure
      weight: 0.35
      features:
        - id: systemic_link_score
          weight: 0.40
        - id: correspondent_network_size
          weight: 0.30
        - id: interbank_exposure_proxy
          weight: 0.30
    
    - name: exposure_operational
      signal_type: exposure
      weight: 0.20
      features:
        - id: branch_count
          weight: 0.40
        - id: atm_network_size
          weight: 0.30
        - id: digital_channel_complexity
          weight: 0.30
```

*(Additional coverage-specific configurations for Aerospace, Energy, D&O, PI follow same pattern)*

-----

## 6. Scoring Methodology

### 6.1 Normalization Functions

Each signal value is normalized to 0-100 scale:

```python
class Normalizer:
    """Signal value normalizers."""
    
    @staticmethod
    def log_scale(value: float, base: float = 10, scale: float = 25) -> float:
        """
        Logarithmic scaling for signals with exponential distributions.
        
        Example: domain_count
        - 1 domain → 0
        - 10 domains → 25
        - 100 domains → 50
        - 1000 domains → 75
        """
        if value <= 0:
            return 0.0
        return min(100.0, math.log(value, base) * scale)
    
    @staticmethod
    def linear(value: float, min_val: float, max_val: float) -> float:
        """
        Linear scaling between min and max.
        
        Example: employee_count with min=10, max=100000
        """
        if value <= min_val:
            return 0.0
        if value >= max_val:
            return 100.0
        return ((value - min_val) / (max_val - min_val)) * 100
    
    @staticmethod
    def capped(value: float, cap: float) -> float:
        """
        Linear up to cap, then flat.
        
        Example: tech_stack_count capped at 50
        """
        return min(value, cap) / cap * 100
    
    @staticmethod
    def percentile(value: float, distribution: List[float]) -> float:
        """
        Percentile rank within reference distribution.
        
        Example: web_reach vs cohort distribution
        """
        rank = sum(1 for v in distribution if v <= value)
        return (rank / len(distribution)) * 100
    
    @staticmethod
    def categorical(value: str, mapping: Dict[str, float]) -> float:
        """
        Categorical value to score mapping.
        
        Example: broker_tier → {'tier1': 90, 'tier2': 70, 'tier3': 50, 'tier4': 30}
        """
        return mapping.get(value, 0.0)
```

### 6.2 Group Scoring

```python
def calculate_group_score(
    group: ExposureSignalGroup,
    signals: Dict[str, SignalOutput]
) -> Tuple[float, float]:
    """
    Calculate weighted group score and confidence.
    
    Returns: (group_score, group_confidence)
    """
    weighted_sum = 0.0
    weight_sum = 0.0
    confidence_sum = 0.0
    
    for feature in group.features:
        if feature.id in signals:
            signal = signals[feature.id]
            normalized = normalize(signal.value, feature.normalizer, feature.params)
            weighted_sum += normalized * feature.weight * signal.confidence
            weight_sum += feature.weight * signal.confidence
            confidence_sum += signal.confidence * feature.weight
    
    if weight_sum == 0:
        return (0.0, 0.0)
    
    group_score = weighted_sum / weight_sum
    group_confidence = confidence_sum / sum(f.weight for f in group.features)
    
    return (group_score, group_confidence)
```

### 6.3 Composite Exposure Score

```python
def calculate_exposure_composite(
    groups: List[ExposureSignalGroup],
    group_scores: Dict[str, Tuple[float, float]]
) -> ExposureResult:
    """
    Calculate composite exposure score with bounded range.
    """
    weighted_sum = 0.0
    weight_sum = 0.0
    confidence_sum = 0.0
    
    for group in groups:
        score, confidence = group_scores[group.name]
        weighted_sum += score * group.weight * confidence
        weight_sum += group.weight * confidence
        confidence_sum += confidence * group.weight
    
    if weight_sum == 0:
        return ExposureResult(
            score=0.0,
            confidence=0.0,
            tier=ProxyTier.UNKNOWN,
            range_low=0.0,
            range_high=100.0
        )
    
    point_estimate = weighted_sum / weight_sum
    overall_confidence = confidence_sum / sum(g.weight for g in groups)
    
    # Calculate bounded range based on confidence
    uncertainty = (1 - overall_confidence) * 30  # Max ±30 points at 0 confidence
    range_low = max(0, point_estimate - uncertainty)
    range_high = min(100, point_estimate + uncertainty)
    
    return ExposureResult(
        score=point_estimate,
        confidence=overall_confidence,
        tier=determine_proxy_tier(group_scores),
        range_low=range_low,
        range_high=range_high
    )
```

### 6.4 Complexity Scoring

Complexity is scored separately from magnitude:

```python
def calculate_complexity_score(
    complexity_signals: Dict[str, SignalOutput]
) -> ComplexityResult:
    """
    Calculate exposure complexity score.
    
    High complexity = geographically dispersed, many entities,
    heterogeneous systems, multiple regulatory regimes.
    """
    components = {
        'geographic': calculate_geographic_dispersion(complexity_signals),
        'structural': calculate_structural_complexity(complexity_signals),
        'technical': calculate_technical_heterogeneity(complexity_signals),
        'regulatory': calculate_regulatory_complexity(complexity_signals)
    }
    
    # Weighted composite
    weights = {
        'geographic': 0.30,
        'structural': 0.25,
        'technical': 0.25,
        'regulatory': 0.20
    }
    
    score = sum(components[k] * weights[k] for k in components)
    
    return ComplexityResult(
        score=score,
        category=map_to_complexity_category(score),
        components=components
    )

def map_to_complexity_category(score: float) -> str:
    """Map complexity score to category."""
    if score < 20:
        return 'simple'
    elif score < 40:
        return 'moderate'
    elif score < 60:
        return 'complex'
    elif score < 80:
        return 'highly_complex'
    else:
        return 'extremely_complex'
```

-----

## 7. Exposure Band Mapping

### 7.1 Mapping Methods

Two methods are supported, selected per coverage:

#### Method A: Fixed Thresholds

```yaml
exposure_band_mapping:
  method: fixed_threshold
  bands:
    - name: micro
      min_score: 0
      max_score: 15
      implied_tiv_range: "$0 - $1M"
    - name: small
      min_score: 15
      max_score: 35
      implied_tiv_range: "$1M - $10M"
    - name: medium
      min_score: 35
      max_score: 60
      implied_tiv_range: "$10M - $50M"
    - name: large
      min_score: 60
      max_score: 85
      implied_tiv_range: "$50M - $250M"
    - name: very_large
      min_score: 85
      max_score: 100
      implied_tiv_range: "$250M+"
```

#### Method B: Cohort Quantile

```yaml
exposure_band_mapping:
  method: cohort_quantile
  cohort_definition:
    dimensions:
      - sector
      - region
      - digital_footprint_band
  quantile_thresholds:
    micro: 0.10        # Bottom 10%
    small: 0.35        # 10-35%
    medium: 0.65       # 35-65%
    large: 0.90        # 65-90%
    very_large: 1.00   # Top 10%
```

### 7.2 Cohort Prior Management

```python
@dataclass
class CohortPrior:
    """Historical cohort data for calibration."""
    
    cohort_id: str
    sector: str
    region: str
    digital_footprint_band: str
    
    # Empirical distributions
    tiv_distribution: List[float]  # Observed TIVs in cohort
    exposure_score_distribution: List[float]  # Historical scores
    loss_severity_distribution: List[float]  # For validation
    
    # Calibration metadata
    sample_size: int
    last_updated: datetime
    confidence: float  # Based on sample size and recency

class CohortPriorManager:
    """Manages cohort priors for exposure calibration."""
    
    def get_prior(
        self,
        sector: str,
        region: str,
        digital_footprint_band: str
    ) -> Optional[CohortPrior]:
        """Retrieve matching cohort prior."""
        pass
    
    def update_prior(
        self,
        cohort_id: str,
        new_observation: ExposureObservation
    ) -> None:
        """Update prior with new observation."""
        pass
    
    def calculate_implied_tiv_range(
        self,
        exposure_score: float,
        cohort: CohortPrior
    ) -> Tuple[float, float]:
        """
        Map exposure score to implied TIV range using cohort.
        
        Returns: (low_estimate, high_estimate)
        """
        percentile = self._score_to_percentile(exposure_score, cohort)
        
        low_idx = int(percentile * 0.8 * len(cohort.tiv_distribution))
        high_idx = int(min(1.0, percentile * 1.2) * len(cohort.tiv_distribution))
        
        sorted_tivs = sorted(cohort.tiv_distribution)
        return (sorted_tivs[low_idx], sorted_tivs[high_idx])
```

### 7.3 Calibration Bootstrap Strategy

For new deployments without historical cohort data:

```
Phase 1: Fixed Thresholds (Months 0-6)
├── Use actuarially-derived fixed thresholds
├── Collect observations where actual TIV is known
├── Build cohort prior foundations
└── Monitor signal-TIV correlations

Phase 2: Hybrid (Months 6-12)
├── Fixed thresholds as fallback
├── Cohort quantile where sufficient data exists
├── A/B testing of methods
└── Continuous calibration

Phase 3: Full Cohort (Month 12+)
├── Cohort quantile as primary method
├── Fixed thresholds only for novel cohorts
├── Automated recalibration
└── Drift monitoring and alerts
```

-----

## 8. Pricing Integration Patterns

### 8.1 Pattern A: Parallel View (Recommended Default)

Exposure band applies a multiplicative modifier after base premium:

```yaml
pricing:
  exposure_integration: parallel
  exposure_modifiers:
    micro: 0.80       # 20% credit
    small: 0.90       # 10% credit
    medium: 1.00      # Base
    large: 1.15       # 15% loading
    very_large: 1.35  # 35% loading
```

```python
def apply_exposure_modifier(
    base_premium: float,
    exposure_band: str,
    config: CoverageConfig
) -> float:
    """Apply exposure-based premium modifier."""
    modifier = config.exposure_modifiers.get(exposure_band, 1.0)
    return base_premium * modifier
```

### 8.2 Pattern B: Embedded Weight

Exposure signals contribute directly to composite risk score:

```yaml
signal_groups:
  # Risk signals
  - name: financial_stability
    signal_type: risk
    weight: 0.20
  
  # Exposure as risk factor (use cautiously)
  - name: exposure_scale
    signal_type: risk  # Contributes to risk composite
    weight: 0.10       # Low weight - size alone isn't risk
```

**Warning:** Only use Pattern B when actuarial analysis confirms exposure magnitude correlates with loss frequency/severity for the specific coverage.

### 8.3 Pattern C: Two-Dimensional Grid (Most Granular)

Pricing determined by (risk tier × exposure band × complexity category) matrix:

```yaml
pricing:
  method: grid_3d
  pricing_grid:
    # Format: tier.band.complexity → rate
    tier1:
      micro:
        simple: 0.0035
        moderate: 0.0038
        complex: 0.0042
      small:
        simple: 0.0040
        moderate: 0.0044
        complex: 0.0050
      medium:
        simple: 0.0045
        moderate: 0.0052
        complex: 0.0060
      large:
        simple: 0.0055
        moderate: 0.0065
        complex: 0.0080
      very_large:
        simple: 0.0070
        moderate: 0.0085
        complex: 0.0110
    
    tier2:
      # ... similar structure
    
    # ... tiers 3-5
```

```python
def get_grid_rate(
    tier: int,
    exposure_band: str,
    complexity_category: str,
    config: CoverageConfig
) -> float:
    """Look up rate from 3D pricing grid."""
    tier_key = f"tier{tier}"
    grid = config.pricing_grid
    
    return grid[tier_key][exposure_band][complexity_category]
```

-----

## 9. Auto-Apply Rules

### 9.1 Rule Definition

```yaml
exposure:
  auto_apply_rules:
    # Referral rules
    - id: high_exposure_low_confidence
      condition: "exposure_band in ['large', 'very_large'] and exposure_confidence < 0.6"
      action: refer
      reason: "High inferred exposure with low confidence requires manual verification"
    
    - id: unknown_exposure
      condition: "proxy_tier == 'unknown'"
      action: refer
      reason: "Insufficient data to estimate exposure"
    
    - id: extreme_complexity
      condition: "complexity_category == 'extremely_complex'"
      action: refer
      reason: "Extremely complex exposure structure requires specialist review"
    
    # Modifier rules
    - id: very_large_minimum_tier
      condition: "exposure_band == 'very_large' and tier < 3"
      action: tier_floor
      value: 3
      reason: "Very large exposures require minimum Tier 3 pricing"
    
    # Note rules
    - id: cohort_outlier
      condition: "cohort_percentile > 95 or cohort_percentile < 5"
      action: note
      value: "Exposure score is a significant outlier vs cohort - review signal inputs"
```

### 9.2 Rule Evaluation

```python
def evaluate_exposure_rules(
    exposure_result: ExposureResult,
    complexity_result: ComplexityResult,
    tier: int,
    config: CoverageConfig
) -> List[RuleOutcome]:
    """
    Evaluate all auto-apply rules.
    
    Returns list of triggered rule outcomes.
    """
    outcomes = []
    context = {
        'exposure_band': exposure_result.band,
        'exposure_score': exposure_result.score,
        'exposure_confidence': exposure_result.confidence,
        'proxy_tier': exposure_result.tier.value,
        'complexity_category': complexity_result.category,
        'complexity_score': complexity_result.score,
        'tier': tier,
        'cohort_percentile': exposure_result.cohort_percentile
    }
    
    for rule in config.exposure.auto_apply_rules:
        if evaluate_condition(rule.condition, context):
            outcomes.append(RuleOutcome(
                rule_id=rule.id,
                action=rule.action,
                value=rule.value,
                reason=rule.reason
            ))
    
    return outcomes
```

-----

## 10. Data Structures

### 10.1 Core Types

```python
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Tuple

class ProxyTier(Enum):
    """Exposure estimation reliability tier."""
    DIRECT_OBSERVABLE = "direct_observable"
    INFERRED_PROXY = "inferred_proxy"
    COHORT_INFERENCE = "cohort_inference"
    UNKNOWN = "unknown"

class ExposureBand(Enum):
    """Exposure magnitude band."""
    MICRO = "micro"
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"
    VERY_LARGE = "very_large"

class ComplexityCategory(Enum):
    """Exposure complexity category."""
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
    HIGHLY_COMPLEX = "highly_complex"
    EXTREMELY_COMPLEX = "extremely_complex"

@dataclass
class ExposureSignalOutput:
    """Output from a single exposure signal."""
    signal_id: str
    value: any
    normalized_value: float  # 0-100
    confidence: float  # 0-1
    source_urls: List[str]
    extracted_at: datetime
    tier: ProxyTier
    notes: Optional[str] = None

@dataclass
class ExposureGroupScore:
    """Score for an exposure signal group."""
    group_name: str
    score: float  # 0-100
    confidence: float  # 0-1
    signals_available: int
    signals_total: int
    contributing_signals: List[str]

@dataclass
class ExposureResult:
    """Complete exposure assessment result."""
    # Magnitude
    score: float  # 0-100 point estimate
    range_low: float  # Lower bound
    range_high: float  # Upper bound
    band: ExposureBand
    
    # Metadata
    confidence: float  # 0-1
    proxy_tier: ProxyTier
    method_used: str  # 'fixed_threshold' or 'cohort_quantile'
    
    # Cohort context
    cohort_id: Optional[str]
    cohort_percentile: Optional[float]
    implied_tiv_range: Optional[Tuple[float, float]]
    
    # Group breakdown
    group_scores: Dict[str, ExposureGroupScore]
    
    # Audit
    signals_used: List[ExposureSignalOutput]
    rules_triggered: List[str]

@dataclass
class ComplexityResult:
    """Complete complexity assessment result."""
    score: float  # 0-100
    category: ComplexityCategory
    confidence: float
    
    # Component breakdown
    geographic_score: float
    structural_score: float
    technical_score: float
    regulatory_score: float
    
    # Contributing factors
    factors: List[str]  # Human-readable complexity drivers

@dataclass
class CombinedExposureAssessment:
    """Combined magnitude and complexity assessment."""
    magnitude: ExposureResult
    complexity: ComplexityResult
    
    # Combined outputs
    pricing_band: str  # e.g., "large_complex"
    premium_modifier: float
    referral_required: bool
    referral_reasons: List[str]
    notes: List[str]
```

### 10.2 Model Version Extensions

```python
@dataclass
class ModelVersionExposureExtension:
    """Exposure data stored in ModelVersion."""
    
    # Magnitude
    exposure_score: float
    exposure_score_range: Tuple[float, float]
    exposure_band: str
    exposure_confidence: float
    exposure_proxy_tier: str
    
    # Complexity
    complexity_score: float
    complexity_category: str
    complexity_confidence: float
    
    # Breakdown
    exposure_group_scores: Dict[str, float]
    exposure_group_confidences: Dict[str, float]
    complexity_components: Dict[str, float]
    
    # Cohort
    exposure_cohort_id: Optional[str]
    exposure_cohort_percentile: Optional[float]
    exposure_implied_tiv_range: Optional[Tuple[float, float]]
    
    # Calibration snapshot (for audit)
    cohort_prior_version: Optional[str]
    calibration_date: Optional[datetime]
    
    # Pricing impact
    exposure_modifiers_applied: List[Dict[str, any]]
    pricing_method: str  # 'parallel', 'embedded', 'grid'
```

-----

## 11. YAML Configuration Schema

### 11.1 Complete Exposure Configuration

```yaml
# Coverage-level exposure configuration
exposure:
  enabled: true
  version: "2025-12-29"
  
  # Signal groups with coverage-specific weights
  signal_groups:
    - name: exposure_digital_footprint
      signal_type: exposure
      weight: 0.30
      confidence_threshold: 0.5
      features:
        - id: domain_count
          weight: 0.25
          normalizer: log_scale
          normalizer_params:
            base: 10
            scale: 25
          tier: 2
        - id: subdomain_complexity
          weight: 0.25
          normalizer: capped
          normalizer_params:
            cap: 100
          tier: 2
        - id: tech_stack_count
          weight: 0.30
          normalizer: capped
          normalizer_params:
            cap: 50
          tier: 2
        - id: web_reach_proxy
          weight: 0.20
          normalizer: percentile
          tier: 2
    
    - name: exposure_network_authority
      signal_type: exposure
      weight: 0.25
      confidence_threshold: 0.5
      features:
        - id: marquee_partner_count
          weight: 0.40
          normalizer: log_scale
          normalizer_params:
            base: 10
            scale: 30
          tier: 2
        - id: systemic_link_score
          weight: 0.35
          normalizer: linear
          normalizer_params:
            min: 0
            max: 100
          tier: 2
        - id: regulatory_citation_count
          weight: 0.25
          normalizer: log_scale
          normalizer_params:
            base: 10
            scale: 25
          tier: 2
    
    - name: exposure_scale_direct
      signal_type: exposure
      weight: 0.30
      confidence_threshold: 0.7
      priority: 1  # Tier 1 signals - use if available
      features:
        - id: public_revenue
          weight: 0.40
          normalizer: log_scale
          normalizer_params:
            base: 10
            scale: 12.5  # $10B = score 100
          tier: 1
        - id: public_assets
          weight: 0.35
          normalizer: log_scale
          normalizer_params:
            base: 10
            scale: 10
          tier: 1
        - id: registered_employee_count
          weight: 0.25
          normalizer: log_scale
          normalizer_params:
            base: 10
            scale: 20
          tier: 1
    
    - name: exposure_geographic
      signal_type: exposure
      weight: 0.15
      confidence_threshold: 0.5
      features:
        - id: location_count
          weight: 0.50
          normalizer: log_scale
          normalizer_params:
            base: 10
            scale: 30
          tier: 2
        - id: high_intensity_location_pct
          weight: 0.50
          normalizer: linear
          normalizer_params:
            min: 0
            max: 100
          tier: 2
  
  # Complexity signal groups
  complexity_groups:
    - name: geographic_complexity
      weight: 0.30
      features:
        - id: geographic_dispersion
          weight: 0.60
        - id: regulatory_jurisdiction_count
          weight: 0.40
    
    - name: structural_complexity
      weight: 0.25
      features:
        - id: subsidiary_count
          weight: 0.50
        - id: acquisition_frequency
          weight: 0.50
    
    - name: technical_complexity
      weight: 0.25
      features:
        - id: technology_heterogeneity
          weight: 0.60
        - id: product_line_count
          weight: 0.40
    
    - name: operational_complexity
      weight: 0.20
      features:
        - id: supply_chain_depth
          weight: 0.50
        - id: customer_concentration
          weight: 0.50
          invert: true  # Lower concentration = higher complexity
  
  # Band mapping configuration
  exposure_band_mapping:
    method: fixed_threshold  # or 'cohort_quantile'
    bands:
      - name: micro
        min_score: 0
        max_score: 15
        implied_tiv_range: "$0 - $1M"
      - name: small
        min_score: 15
        max_score: 35
        implied_tiv_range: "$1M - $10M"
      - name: medium
        min_score: 35
        max_score: 60
        implied_tiv_range: "$10M - $50M"
      - name: large
        min_score: 60
        max_score: 85
        implied_tiv_range: "$50M - $250M"
      - name: very_large
        min_score: 85
        max_score: 100
        implied_tiv_range: "$250M+"
  
  # Complexity category mapping
  complexity_mapping:
    simple:
      max_score: 20
    moderate:
      max_score: 40
    complex:
      max_score: 60
    highly_complex:
      max_score: 80
    extremely_complex:
      max_score: 100
  
  # Auto-apply rules
  auto_apply_rules:
    - id: high_exposure_low_confidence
      condition: "exposure_band in ['large', 'very_large'] and exposure_confidence < 0.6"
      action: refer
      reason: "High inferred exposure with low confidence"
    
    - id: unknown_proxy_tier
      condition: "proxy_tier == 'unknown'"
      action: refer
      reason: "Insufficient data for exposure estimation"
    
    - id: extreme_complexity_referral
      condition: "complexity_category == 'extremely_complex'"
      action: refer
      reason: "Extremely complex exposure structure"
    
    - id: very_large_tier_floor
      condition: "exposure_band == 'very_large' and tier < 3"
      action: tier_floor
      value: 3
      reason: "Minimum tier for very large exposures"

# Pricing integration
pricing:
  exposure_integration: parallel  # 'parallel', 'embedded', or 'grid'
  
  # For parallel integration
  exposure_modifiers:
    micro: 0.80
    small: 0.90
    medium: 1.00
    large: 1.15
    very_large: 1.35
  
  complexity_modifiers:
    simple: 0.95
    moderate: 1.00
    complex: 1.10
    highly_complex: 1.25
    extremely_complex: 1.50
  
  # For grid integration (alternative)
  # pricing_grid:
  #   tier1:
  #     micro:
  #       simple: 0.0035
  #       ...
```

-----

## 12. Testing and Validation

### 12.1 Unit Tests

```python
# tests/unit/test_exposure_scoring.py

class TestExposureNormalization:
    """Test normalization functions."""
    
    def test_log_scale_normalization(self):
        assert Normalizer.log_scale(1, base=10, scale=25) == 0.0
        assert Normalizer.log_scale(10, base=10, scale=25) == 25.0
        assert Normalizer.log_scale(100, base=10, scale=25) == 50.0
        assert Normalizer.log_scale(10000, base=10, scale=25) == 100.0
    
    def test_capped_normalization(self):
        assert Normalizer.capped(25, cap=50) == 50.0
        assert Normalizer.capped(50, cap=50) == 100.0
        assert Normalizer.capped(100, cap=50) == 100.0
    
    def test_linear_normalization(self):
        assert Normalizer.linear(0, min_val=0, max_val=100) == 0.0
        assert Normalizer.linear(50, min_val=0, max_val=100) == 50.0
        assert Normalizer.linear(100, min_val=0, max_val=100) == 100.0

class TestExposureBandMapping:
    """Test exposure score to band mapping."""
    
    def test_fixed_threshold_mapping(self):
        mapper = FixedThresholdMapper(bands=[
            Band('micro', 0, 15),
            Band('small', 15, 35),
            Band('medium', 35, 60),
            Band('large', 60, 85),
            Band('very_large', 85, 100)
        ])
        
        assert mapper.map(10) == 'micro'
        assert mapper.map(25) == 'small'
        assert mapper.map(50) == 'medium'
        assert mapper.map(75) == 'large'
        assert mapper.map(95) == 'very_large'
    
    def test_boundary_conditions(self):
        mapper = FixedThresholdMapper(bands=[...])
        
        assert mapper.map(15) == 'small'  # At boundary
        assert mapper.map(14.99) == 'micro'
        assert mapper.map(0) == 'micro'
        assert mapper.map(100) == 'very_large'

class TestComplexityScoring:
    """Test complexity score calculation."""
    
    def test_complexity_components(self):
        signals = {
            'geographic_dispersion': SignalOutput(value=45, confidence=0.8),
            'subsidiary_count': SignalOutput(value=12, confidence=0.9),
            'technology_heterogeneity': SignalOutput(value=30, confidence=0.7)
        }
        
        result = calculate_complexity_score(signals)
        
        assert 0 <= result.score <= 100
        assert result.category in ComplexityCategory
        assert result.geographic_score >= 0
```

### 12.2 Integration Tests

```python
# tests/integration/test_exposure_workflow.py

class TestExposureWorkflowIntegration:
    """Test exposure integration with full workflow."""
    
    def test_parallel_integration(self):
        """Test exposure as parallel modifier."""
        result = run_workflow(
            entity_id="test-large-corp",
            coverage="cyber",
            submission_data={"limit_requested": 10_000_000},
            direct_query_responses={}
        )
        
        # Verify exposure was calculated
        assert result.exposure_assessment is not None
        assert result.exposure_assessment.magnitude.band in ExposureBand
        
        # Verify modifier was applied
        assert 'exposure_modifier' in [m['name'] for m in result.modifiers_applied]
    
    def test_grid_integration(self):
        """Test three-dimensional pricing grid."""
        result = run_workflow(
            entity_id="test-complex-corp",
            coverage="fi",
            submission_data={"limit_requested": 50_000_000},
            config_override={'pricing.exposure_integration': 'grid'}
        )
        
        # Verify grid pricing was used
        assert result.pricing_method == 'grid'
        assert result.grid_coordinates == {
            'tier': result.tier,
            'band': result.exposure_assessment.magnitude.band,
            'complexity': result.exposure_assessment.complexity.category
        }
    
    def test_referral_on_low_confidence(self):
        """Test referral triggered by low exposure confidence."""
        result = run_workflow(
            entity_id="test-unknown-corp",
            coverage="cyber",
            mock_signals={'exposure_confidence': 0.3}
        )
        
        assert result.referral_required == True
        assert 'low confidence' in str(result.referral_reasons).lower()
```

### 12.3 Calibration Validation

```python
# tests/calibration/test_exposure_calibration.py

class TestExposureCalibration:
    """Validate exposure scoring against known TIVs."""
    
    @pytest.fixture
    def historical_data(self):
        """Load historical submissions with known TIVs."""
        return load_calibration_dataset('exposure_calibration_v1.csv')
    
    def test_score_tiv_correlation(self, historical_data):
        """Exposure score should correlate with actual TIV."""
        scores = []
        tivs = []
        
        for record in historical_data:
            result = calculate_exposure_score(record.signals)
            scores.append(result.score)
            tivs.append(math.log10(record.actual_tiv))  # Log TIV
        
        correlation = pearsonr(scores, tivs)
        
        # Expect moderate to strong correlation
        assert correlation.statistic >= 0.5, f"Weak correlation: {correlation}"
    
    def test_band_accuracy(self, historical_data):
        """Band assignments should match TIV ranges."""
        correct = 0
        total = 0
        
        for record in historical_data:
            result = calculate_exposure_score(record.signals)
            predicted_band = result.band
            actual_band = tiv_to_band(record.actual_tiv)
            
            # Allow one-band tolerance
            if abs(band_to_ordinal(predicted_band) - band_to_ordinal(actual_band)) <= 1:
                correct += 1
            total += 1
        
        accuracy = correct / total
        assert accuracy >= 0.70, f"Band accuracy too low: {accuracy:.1%}"
    
    def test_cohort_calibration(self, historical_data):
        """Cohort priors should produce calibrated ranges."""
        for cohort_id in get_unique_cohorts(historical_data):
            cohort_records = filter_by_cohort(historical_data, cohort_id)
            
            in_range = 0
            for record in cohort_records:
                result = calculate_exposure_score(record.signals)
                low, high = result.implied_tiv_range
                
                if low <= record.actual_tiv <= high:
                    in_range += 1
            
            coverage = in_range / len(cohort_records)
            
            # 80% of actual TIVs should fall within implied ranges
            assert coverage >= 0.80, f"Cohort {cohort_id} coverage: {coverage:.1%}"
```

-----

## 13. Monitoring and Governance

### 13.1 Operational Metrics

```yaml
monitoring:
  exposure_metrics:
    # Signal availability
    - name: exposure_signal_availability
      description: "% of exposure signals successfully extracted"
      threshold_warning: 0.85
      threshold_critical: 0.70
    
    # Confidence distribution
    - name: exposure_confidence_mean
      description: "Mean confidence across assessments"
      threshold_warning: 0.65
      threshold_critical: 0.50
    
    - name: exposure_proxy_tier_distribution
      description: "Distribution of proxy tiers used"
      alert_if: "tier_4_unknown_pct > 0.20"
    
    # Band distribution
    - name: exposure_band_distribution
      description: "Distribution of exposure bands"
      baseline_check: true
      drift_threshold: 0.15
    
    # Referral rates
    - name: exposure_referral_rate
      description: "% of submissions referred due to exposure"
      threshold_warning: 0.25
      threshold_critical: 0.40

  calibration_metrics:
    # Accuracy (when actual TIV known)
    - name: band_accuracy_within_one
      description: "% of predictions within one band of actual"
      threshold_warning: 0.75
      threshold_critical: 0.60
    
    # Calibration (predicted ranges contain actual)
    - name: tiv_range_coverage
      description: "% of actual TIVs within predicted ranges"
      threshold_warning: 0.75
      threshold_critical: 0.65
    
    # Discrimination (Kolmogorov-Smirnov)
    - name: exposure_ks_statistic
      description: "KS stat for exposure vs loss severity"
      threshold_warning: 0.30
      threshold_critical: 0.20
```

### 13.2 Alerting Rules

```python
class ExposureMonitor:
    """Monitor exposure scoring health."""
    
    def check_signal_availability(self) -> Alert | None:
        """Alert if signal availability drops."""
        availability = self.calculate_signal_availability(period='24h')
        
        if availability < 0.70:
            return Alert(
                severity='critical',
                message=f"Exposure signal availability critical: {availability:.1%}",
                action="Check extractor health and data source availability"
            )
        elif availability < 0.85:
            return Alert(
                severity='warning',
                message=f"Exposure signal availability degraded: {availability:.1%}"
            )
        return None
    
    def check_calibration_drift(self) -> Alert | None:
        """Alert if calibration drifts from baseline."""
        current_dist = self.get_band_distribution(period='7d')
        baseline_dist = self.get_baseline_distribution()
        
        drift = self.calculate_distribution_drift(current_dist, baseline_dist)
        
        if drift > 0.20:
            return Alert(
                severity='warning',
                message=f"Exposure band distribution drift detected: {drift:.1%}",
                action="Review recent submissions and recalibrate if needed"
            )
        return None
    
    def check_cohort_stability(self) -> Alert | None:
        """Alert if cohort priors become stale."""
        for cohort in self.get_active_cohorts():
            age_days = (datetime.now() - cohort.last_updated).days
            
            if age_days > 90 and cohort.sample_size < 100:
                return Alert(
                    severity='warning',
                    message=f"Cohort {cohort.id} has stale priors ({age_days} days, n={cohort.sample_size})",
                    action="Review cohort and consider merging or refreshing"
                )
        return None
```

-----

## 14. Underwriter Interface

### 14.1 Exposure Summary Card

```
┌─────────────────────────────────────────────────────────────────┐
│                    EXPOSURE ASSESSMENT                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  MAGNITUDE                          COMPLEXITY                   │
│  ───────────────────                ───────────────────          │
│  Band:      LARGE                   Category: COMPLEX            │
│  Score:     72 (range: 65-79)       Score:    58                 │
│  Confidence: 0.78                   Confidence: 0.82             │
│                                                                  │
│  Method: Inferred Proxy (Tier 2)                                 │
│  Implied TIV: $75M - $180M                                       │
│                                                                  │
├─────────────────────────────────────────────────────────────────┤
│  TOP MAGNITUDE DRIVERS              TOP COMPLEXITY DRIVERS       │
│  ────────────────────               ──────────────────           │
│  1. Tech stack: 42 technologies     1. 12 countries of operation │
│  2. 8 marquee partners detected     2. 7 regulatory jurisdictions│
│  3. 156 subdomains                  3. 4 recent acquisitions     │
│                                                                  │
├─────────────────────────────────────────────────────────────────┤
│  COHORT COMPARISON                                               │
│  ────────────────                                                │
│  Sector: Technology | Region: North America                      │
│  Cohort Size: 847 | Your Percentile: 78th                        │
│                                                                  │
│  Digital Footprint:  ████████░░  80th percentile                 │
│  Network Authority:  ██████░░░░  62nd percentile                 │
│  Geographic Spread:  █████████░  91st percentile                 │
│                                                                  │
├─────────────────────────────────────────────────────────────────┤
│  PRICING IMPACT                                                  │
│  ──────────────                                                  │
│  Exposure Modifier: 1.15 (+15%)                                  │
│  Complexity Modifier: 1.10 (+10%)                                │
│  Combined Impact: 1.265 (+26.5%)                                 │
│                                                                  │
│  ⚠ REFERRAL TRIGGER: High exposure with moderate confidence      │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 14.2 Audit Trail

```json
{
  "exposure_assessment": {
    "assessment_id": "exp_abc123",
    "timestamp": "2025-12-29T14:30:00Z",
    "config_version": "2025-12-29",
    
    "magnitude": {
      "score": 72.3,
      "range": [65.1, 79.5],
      "band": "large",
      "confidence": 0.78,
      "proxy_tier": "inferred_proxy",
      
      "group_scores": {
        "exposure_digital_footprint": {"score": 68.5, "confidence": 0.82},
        "exposure_network_authority": {"score": 71.2, "confidence": 0.75},
        "exposure_scale_direct": {"score": null, "confidence": 0.0},
        "exposure_geographic": {"score": 78.9, "confidence": 0.80}
      },
      
      "signals_used": [
        {"id": "domain_count", "value": 23, "normalized": 34.1, "confidence": 0.95},
        {"id": "subdomain_complexity", "value": 156, "normalized": 100.0, "confidence": 0.90},
        {"id": "tech_stack_count", "value": 42, "normalized": 84.0, "confidence": 0.85},
        {"id": "marquee_partner_count", "value": 8, "normalized": 67.8, "confidence": 0.70}
      ]
    },
    
    "complexity": {
      "score": 58.2,
      "category": "complex",
      "confidence": 0.82,
      
      "components": {
        "geographic": 72.5,
        "structural": 45.0,
        "technical": 55.3,
        "regulatory": 61.8
      }
    },
    
    "cohort": {
      "cohort_id": "tech_na_moderate",
      "sample_size": 847,
      "percentile": 78,
      "implied_tiv_range": [75000000, 180000000],
      "prior_version": "2025-12-15"
    },
    
    "pricing_impact": {
      "exposure_modifier": 1.15,
      "complexity_modifier": 1.10,
      "combined_modifier": 1.265
    },
    
    "rules_triggered": [
      {
        "rule_id": "high_exposure_moderate_confidence",
        "action": "refer",
        "reason": "High inferred exposure with confidence below 0.80"
      }
    ]
  }
}
```

-----

## 15. Implementation Roadmap

### Phase 15: Exposure Shadow Layer

|Task                             |Priority|Effort |Dependencies                |
|---------------------------------|--------|-------|----------------------------|
|Define exposure signal extractors|High    |2 weeks|Existing extractor framework|
|Implement normalization functions|High    |1 week |None                        |
|Implement exposure scorer        |High    |2 weeks|Normalization               |
|Implement complexity scorer      |High    |1 week |Normalization               |
|Extend YAML schema               |High    |1 week |Scorer implementation       |
|Implement band mapping           |Medium  |1 week |Scorer                      |
|Implement cohort prior manager   |Medium  |2 weeks|Band mapping                |
|Integrate with workflow engine   |High    |2 weeks|All scorers                 |
|Implement pricing patterns A/B/C |High    |2 weeks|Workflow integration        |
|Build underwriter UI components  |Medium  |2 weeks|Workflow integration        |
|Implement monitoring/alerting    |Medium  |1 week |All above                   |
|Calibration validation framework |High    |2 weeks|Historical data             |
|Documentation and training       |Medium  |1 week |All above                   |

**Total Estimated Effort: 16-18 weeks**

### Success Criteria

1. **Signal Availability**: ≥85% of exposure signals extractable
1. **Confidence Distribution**: Mean confidence ≥0.65
1. **Band Accuracy**: ≥70% within one band of actual (where known)
1. **Range Coverage**: ≥75% of actual TIVs within predicted ranges
1. **Processing Time**: <500ms added latency to workflow
1. **Referral Rate**: ≤25% referred due to exposure uncertainty

-----

## 16. Appendix: Coverage-Specific Configurations

*(Full YAML configurations for each of the 7 coverages would be included here, following the pattern established in Section 11)*

-----

## Document End

**Version**: 2.0  
**Status**: Draft for Review  
**Next Review**: Upon actuarial validation completion

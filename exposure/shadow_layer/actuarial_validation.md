# DSI Exposure Shadow Layer — Actuarial Validation Framework

## Document Purpose

This document provides the technical framework for actuaries to validate whether observable digital signals correlate meaningfully with exposure magnitude. It defines the validation methodology, data requirements, statistical tests, and acceptance criteria necessary to determine if the Exposure Shadow Layer can be deployed for production pricing.

-----

## 1. Validation Objectives

### 1.1 Primary Questions

The actuarial validation must answer:

1. **Correlation**: Do proposed digital signals correlate with actual Total Insured Value (TIV)?
1. **Discrimination**: Can the signals distinguish between exposure bands (micro/small/medium/large/very_large)?
1. **Calibration**: Do predicted TIV ranges contain actual TIVs at the expected frequency?
1. **Stability**: Are correlations stable across time, sectors, and regions?
1. **Lift**: Does the exposure score add predictive value beyond simple proxies (e.g., employee count alone)?

### 1.2 Hypothesis Framework

|Hypothesis                                 |Test                         |Acceptance Threshold            |
|-------------------------------------------|-----------------------------|--------------------------------|
|H1: Exposure score correlates with log(TIV)|Pearson correlation          |r ≥ 0.50                        |
|H2: Bands discriminate TIV distributions   |Kolmogorov-Smirnov           |KS ≥ 0.30 between adjacent bands|
|H3: Predicted ranges are calibrated        |Coverage probability         |75-85% of actuals in range      |
|H4: Correlations stable across sectors     |Sector-stratified correlation|r ≥ 0.40 in each major sector   |
|H5: Composite outperforms single proxies   |Incremental R²               |ΔR² ≥ 0.10 vs best single signal|

-----

## 2. Data Requirements

### 2.1 Calibration Dataset Specification

To validate the exposure signals, construct a calibration dataset with the following structure:

#### Required Fields

|Field             |Type  |Description                |Source               |
|------------------|------|---------------------------|---------------------|
|`entity_id`       |string|Unique identifier          |Policy system        |
|`entity_name`     |string|Company name               |Policy system        |
|`domain`          |string|Primary website domain     |Discovery            |
|`sector`          |string|Industry sector (NAICS/SIC)|Submission           |
|`region`          |string|Primary operating region   |Submission           |
|`actual_tiv`      |float |Actual Total Insured Value |Submission (verified)|
|`actual_revenue`  |float |Actual annual revenue      |Submission (verified)|
|`actual_employees`|int   |Actual employee count      |Submission (verified)|
|`policy_inception`|date  |Policy start date          |Policy system        |
|`coverage`        |string|Coverage type              |Policy system        |

#### Signal Fields (Extracted)

For each entity, extract and record:

|Signal ID                    |Description                   |Extraction Method     |
|-----------------------------|------------------------------|----------------------|
|`domain_count`               |Number of owned domains       |WHOIS/DNS lookup      |
|`subdomain_complexity`       |Count of unique subdomains    |DNS enumeration       |
|`tech_stack_count`           |Detected technologies         |Wappalyzer/BuiltWith  |
|`web_reach_proxy`            |Traffic rank or estimate      |SimilarWeb/Alexa      |
|`marquee_partner_count`      |Named major partners          |Web scraping          |
|`regulatory_citation_count`  |Regulatory body mentions      |Regulatory DB search  |
|`systemic_link_score`        |Inbound link authority        |Backlink analysis     |
|`location_count`             |Physical locations            |Google Places API     |
|`high_intensity_location_pct`|% locations in high-risk zones|Geocoding + cat models|
|`public_market_cap`          |Market cap (if public)        |Stock exchange        |
|`public_assets`              |Total assets (if public)      |SEC/filings           |

#### Derived Fields

|Field                    |Calculation                                                                                        |
|-------------------------|---------------------------------------------------------------------------------------------------|
|`log_tiv`                |log₁₀(actual_tiv)                                                                                  |
|`tiv_band_actual`        |Bucketed TIV: micro (<$1M), small ($1-10M), medium ($10-50M), large ($50-250M), very_large (>$250M)|
|`exposure_score`         |Calculated per specification (0-100)                                                               |
|`exposure_band_predicted`|Mapped from exposure_score                                                                         |
|`complexity_score`       |Calculated per specification (0-100)                                                               |

### 2.2 Minimum Sample Requirements

|Segment     |Minimum N|Rationale                        |
|------------|---------|---------------------------------|
|Overall     |1,000    |Statistical power for correlation|
|Per coverage|150      |Coverage-specific validation     |
|Per sector  |100      |Sector stability testing         |
|Per TIV band|100      |Band discrimination testing      |

### 2.3 Data Quality Requirements

- **TIV Verification**: Only include records where TIV was verified (not self-reported without validation)
- **Signal Completeness**: Minimum 8/12 signals must be extractable per entity
- **Recency**: Submissions within last 3 years preferred
- **Outlier Handling**: Document approach (winsorize at 1st/99th percentile vs. exclude)

-----

## 3. Validation Methodology

### 3.1 Test 1: Signal-TIV Correlation Analysis

#### Objective

Determine if individual signals and composite exposure score correlate with actual TIV.

#### Method

```
For each signal S and the composite exposure score:
1. Extract signal values for all entities in calibration set
2. Calculate Pearson correlation: r = corr(S, log₁₀(TIV))
3. Calculate Spearman correlation: ρ = spearman(S, TIV)
4. Calculate p-value and 95% confidence interval
5. Visualize with scatter plot and regression line
```

#### Expected Output

|Signal              |Pearson r|Spearman ρ|p-value   |95% CI          |
|--------------------|---------|----------|----------|----------------|
|domain_count        |0.52     |0.48      |<0.001    |[0.47, 0.57]    |
|subdomain_complexity|0.61     |0.55      |<0.001    |[0.56, 0.66]    |
|tech_stack_count    |0.44     |0.41      |<0.001    |[0.38, 0.50]    |
|…                   |…        |…         |…         |…               |
|**exposure_score**  |**0.68** |**0.64**  |**<0.001**|**[0.64, 0.72]**|

#### Acceptance Criteria

- Composite exposure_score: r ≥ 0.50
- At least 6/12 individual signals: r ≥ 0.30
- All correlations statistically significant (p < 0.01)

#### Visualization Requirements

- Scatter plots: exposure_score vs log(TIV) with regression line
- Correlation matrix heatmap for all signals
- Residual plots to check linearity assumption

-----

### 3.2 Test 2: Band Discrimination Analysis

#### Objective

Verify that exposure bands correspond to meaningfully different TIV distributions.

#### Method

```
For each pair of adjacent bands (micro↔small, small↔medium, etc.):
1. Extract actual TIVs for entities in each band
2. Perform Kolmogorov-Smirnov test
3. Calculate effect size (Cohen's d)
4. Visualize with overlapping density plots
```

#### Expected Output

|Band Pair         |KS Statistic|KS p-value|Cohen’s d|Median TIV Ratio|
|------------------|------------|----------|---------|----------------|
|micro ↔ small     |0.45        |<0.001    |1.2      |5.8x            |
|small ↔ medium    |0.52        |<0.001    |1.4      |6.2x            |
|medium ↔ large    |0.48        |<0.001    |1.3      |5.5x            |
|large ↔ very_large|0.41        |<0.001    |1.1      |4.8x            |

#### Acceptance Criteria

- KS statistic ≥ 0.30 for all adjacent band pairs
- Cohen’s d ≥ 0.8 (large effect size) for all pairs
- Median TIV ratio ≥ 3x between adjacent bands

#### Visualization Requirements

- Density plots of log(TIV) by predicted band
- Box plots of actual TIV by predicted band
- Confusion matrix: predicted band vs actual band

-----

### 3.3 Test 3: Calibration Analysis

#### Objective

Assess whether predicted TIV ranges contain actual TIVs at appropriate frequency.

#### Method

```
For each entity:
1. Calculate exposure_score and implied TIV range [low, high]
2. Determine if actual_tiv ∈ [low, high]
3. Calculate coverage probability = count(in_range) / total

For calibration curve:
1. Bin entities by exposure_score decile
2. Calculate mean predicted TIV vs mean actual TIV per bin
3. Plot calibration curve
```

#### Expected Output

|Metric                       |Value|Target|
|-----------------------------|-----|------|
|Overall coverage probability |78%  |75-85%|
|Coverage by confidence tier  |     |      |
|- High confidence (>0.8)     |85%  |≥80%  |
|- Medium confidence (0.6-0.8)|76%  |≥70%  |
|- Low confidence (<0.6)      |65%  |≥55%  |

Calibration curve slope should be close to 1.0 (no systematic bias).

#### Acceptance Criteria

- Overall coverage: 75-85%
- Calibration slope: 0.9-1.1
- No systematic over/under-prediction by sector or region

#### Visualization Requirements

- Calibration curve (predicted vs actual mean TIV by decile)
- Coverage probability by confidence level
- Residual analysis by sector and region

-----

### 3.4 Test 4: Stability Analysis

#### Objective

Confirm correlations are stable across different segments.

#### Method

```
Stratified correlation analysis:
1. Segment data by: sector, region, coverage, time period
2. Calculate exposure_score ↔ TIV correlation within each segment
3. Test for significant differences between segments
```

#### Expected Output

**By Sector:**

|Sector            |N  |Correlation|95% CI      |
|------------------|---|-----------|------------|
|Technology        |180|0.65       |[0.55, 0.75]|
|Financial Services|220|0.71       |[0.63, 0.79]|
|Manufacturing     |150|0.58       |[0.45, 0.71]|
|Healthcare        |130|0.62       |[0.50, 0.74]|
|…                 |…  |…          |…           |

**By Region:**

|Region       |N  |Correlation|95% CI      |
|-------------|---|-----------|------------|
|North America|450|0.68       |[0.62, 0.74]|
|Europe       |320|0.66       |[0.58, 0.74]|
|Asia Pacific |180|0.61       |[0.50, 0.72]|

**By Time Period:**

|Period|N  |Correlation|95% CI      |
|------|---|-----------|------------|
|2022  |300|0.67       |[0.59, 0.75]|
|2023  |380|0.69       |[0.62, 0.76]|
|2024  |320|0.68       |[0.60, 0.76]|

#### Acceptance Criteria

- Correlation ≥ 0.40 in all major segments (N ≥ 100)
- No statistically significant difference between segment correlations (overlapping CIs)
- Temporal stability (no declining trend)

-----

### 3.5 Test 5: Incremental Value Analysis

#### Objective

Demonstrate that composite exposure score adds value beyond simple proxies.

#### Method

```
Regression comparison:
1. Model A (baseline): log(TIV) ~ employee_count
2. Model B (single best): log(TIV) ~ best_single_signal
3. Model C (composite): log(TIV) ~ exposure_score
4. Model D (full): log(TIV) ~ all_individual_signals

Compare R² values and perform likelihood ratio tests.
```

#### Expected Output

|Model                 |R²  |Adjusted R²|AIC |BIC |
|----------------------|----|-----------|----|----|
|A: Employee count only|0.35|0.35       |2450|2460|
|B: Best single signal |0.42|0.42       |2380|2390|
|C: Exposure composite |0.52|0.52       |2280|2290|
|D: All signals        |0.58|0.56       |2220|2280|

Incremental R² from composite vs baseline: **+0.17**

#### Acceptance Criteria

- Model C (composite) R² ≥ Model B (best single) R² + 0.05
- Model C (composite) R² ≥ Model A (baseline) R² + 0.10
- Information criteria (AIC/BIC) prefer composite model

-----

### 3.6 Test 6: Complexity Correlation Analysis

#### Objective

Validate that complexity score correlates with actual operational complexity indicators.

#### Method

```
Where complexity ground truth is available:
1. Correlate complexity_score with:
   - Actual subsidiary count
   - Actual country count of operations
   - Known regulatory jurisdiction count
2. Test discrimination of complexity categories
```

#### Expected Output

|Complexity Indicator    |Correlation with complexity_score|
|------------------------|---------------------------------|
|Subsidiary count        |0.58                             |
|Countries of operation  |0.65                             |
|Regulatory jurisdictions|0.52                             |

#### Acceptance Criteria

- Correlation ≥ 0.40 with at least 2/3 complexity indicators
- Complexity categories show ordered relationship with indicators

-----

## 4. Statistical Methods Reference

### 4.1 Pearson Correlation

```python
from scipy.stats import pearsonr
import numpy as np

def calculate_correlation_with_ci(x, y, confidence=0.95):
    """
    Calculate Pearson correlation with confidence interval.
    
    Returns: (r, p_value, ci_low, ci_high)
    """
    r, p = pearsonr(x, y)
    n = len(x)
    
    # Fisher z-transformation for CI
    z = np.arctanh(r)
    se = 1 / np.sqrt(n - 3)
    z_crit = stats.norm.ppf((1 + confidence) / 2)
    
    ci_low = np.tanh(z - z_crit * se)
    ci_high = np.tanh(z + z_crit * se)
    
    return r, p, ci_low, ci_high
```

### 4.2 Kolmogorov-Smirnov Test

```python
from scipy.stats import ks_2samp

def test_band_discrimination(tiv_band_a, tiv_band_b):
    """
    Test if two bands have significantly different TIV distributions.
    
    Returns: (ks_statistic, p_value)
    """
    statistic, p_value = ks_2samp(tiv_band_a, tiv_band_b)
    return statistic, p_value
```

### 4.3 Calibration Metrics

```python
def calculate_calibration_metrics(predicted_ranges, actual_values):
    """
    Calculate calibration coverage and curve.
    
    predicted_ranges: List of (low, high) tuples
    actual_values: List of actual TIV values
    
    Returns: coverage_probability, calibration_curve_data
    """
    in_range = sum(
        1 for (low, high), actual in zip(predicted_ranges, actual_values)
        if low <= actual <= high
    )
    coverage = in_range / len(actual_values)
    
    # Calibration curve: bin by predicted midpoint
    midpoints = [(low + high) / 2 for low, high in predicted_ranges]
    bins = np.percentile(midpoints, np.arange(0, 101, 10))
    
    calibration_data = []
    for i in range(len(bins) - 1):
        mask = (midpoints >= bins[i]) & (midpoints < bins[i+1])
        if sum(mask) > 0:
            mean_predicted = np.mean([m for m, b in zip(midpoints, mask) if b])
            mean_actual = np.mean([a for a, b in zip(actual_values, mask) if b])
            calibration_data.append((mean_predicted, mean_actual))
    
    return coverage, calibration_data
```

### 4.4 Cohen’s d Effect Size

```python
def cohens_d(group1, group2):
    """
    Calculate Cohen's d effect size between two groups.
    
    Interpretation:
    - Small: d = 0.2
    - Medium: d = 0.5
    - Large: d = 0.8
    """
    n1, n2 = len(group1), len(group2)
    var1, var2 = np.var(group1, ddof=1), np.var(group2, ddof=1)
    
    pooled_std = np.sqrt(((n1-1)*var1 + (n2-1)*var2) / (n1+n2-2))
    
    return (np.mean(group1) - np.mean(group2)) / pooled_std
```

-----

## 5. Validation Report Template

### 5.1 Executive Summary

```
EXPOSURE SHADOW LAYER VALIDATION REPORT
=======================================

Dataset: [Description, N=X, Date Range]
Validation Date: [Date]
Analyst: [Name]

OVERALL ASSESSMENT: [PASS / CONDITIONAL PASS / FAIL]

Key Findings:
1. Composite exposure score achieves r=[X] correlation with log(TIV)
   [PASS/FAIL vs threshold r≥0.50]

2. Band discrimination KS statistic ranges from [X] to [Y]
   [PASS/FAIL vs threshold KS≥0.30]

3. Calibration coverage is [X]%
   [PASS/FAIL vs threshold 75-85%]

4. Stability across sectors: minimum correlation r=[X]
   [PASS/FAIL vs threshold r≥0.40]

5. Incremental R² vs baseline: +[X]
   [PASS/FAIL vs threshold ΔR²≥0.10]

Recommendation: [Deploy / Deploy with conditions / Do not deploy]
```

### 5.2 Detailed Findings

*(Structure for each of the 6 tests with tables, charts, and interpretation)*

### 5.3 Appendices

- A: Full correlation matrix
- B: Signal extraction methodology
- C: Outlier analysis
- D: Sensitivity analysis results
- E: Raw data summary statistics

-----

## 6. Sensitivity Analysis

### 6.1 Signal Weight Sensitivity

Test how results change with different signal weight configurations:

```python
def sensitivity_analysis_weights(data, weight_scenarios):
    """
    Test exposure score performance under different weighting schemes.
    """
    results = []
    for scenario_name, weights in weight_scenarios.items():
        scores = calculate_exposure_scores(data, weights)
        correlation = pearsonr(scores, data['log_tiv'])[0]
        results.append({
            'scenario': scenario_name,
            'correlation': correlation,
            'weights': weights
        })
    return pd.DataFrame(results)

# Example scenarios
weight_scenarios = {
    'baseline': {'digital_footprint': 0.30, 'network_authority': 0.25, ...},
    'digital_heavy': {'digital_footprint': 0.50, 'network_authority': 0.20, ...},
    'network_heavy': {'digital_footprint': 0.20, 'network_authority': 0.40, ...},
    'equal_weights': {'digital_footprint': 0.25, 'network_authority': 0.25, ...}
}
```

### 6.2 Threshold Sensitivity

Test how band mapping thresholds affect accuracy:

```python
def sensitivity_analysis_thresholds(data, threshold_scenarios):
    """
    Test band accuracy under different threshold configurations.
    """
    results = []
    for scenario_name, thresholds in threshold_scenarios.items():
        predicted_bands = map_to_bands(data['exposure_score'], thresholds)
        accuracy = calculate_band_accuracy(predicted_bands, data['actual_band'])
        results.append({
            'scenario': scenario_name,
            'accuracy': accuracy,
            'thresholds': thresholds
        })
    return pd.DataFrame(results)
```

### 6.3 Outlier Sensitivity

Test impact of outlier handling:

```python
def sensitivity_analysis_outliers(data, outlier_methods):
    """
    Test correlation robustness to outlier treatment.
    """
    results = []
    for method_name, method_func in outlier_methods.items():
        clean_data = method_func(data)
        correlation = pearsonr(clean_data['exposure_score'], clean_data['log_tiv'])[0]
        results.append({
            'method': method_name,
            'correlation': correlation,
            'n_removed': len(data) - len(clean_data)
        })
    return pd.DataFrame(results)

outlier_methods = {
    'none': lambda d: d,
    'winsorize_1_99': lambda d: winsorize(d, limits=[0.01, 0.01]),
    'exclude_3sd': lambda d: d[np.abs(zscore(d['log_tiv'])) < 3],
    'exclude_iqr': lambda d: d[~is_outlier_iqr(d['log_tiv'])]
}
```

-----

## 7. Known Limitations

### 7.1 Signal Availability Bias

Entities with poor digital presence may have:

- Fewer extractable signals
- Lower confidence scores
- Potentially systematically different actual TIVs

**Mitigation**: Report validation results separately for high vs. low signal availability groups.

### 7.2 Selection Bias

The calibration dataset contains entities that:

- Applied for insurance (not the full population)
- Provided verifiable TIV information

**Mitigation**: Compare calibration set demographics to target population; document differences.

### 7.3 Temporal Lag

Digital signals are extracted at submission time, but TIV may change:

- Acquisitions/divestitures
- Growth/contraction
- Asset value fluctuations

**Mitigation**: Use TIV at policy inception for validation; note policy term.

### 7.4 Sector-Specific Dynamics

Signal-TIV relationships may differ fundamentally by sector:

- Tech companies: high digital footprint, moderate TIV
- Industrial: low digital footprint, high TIV
- Financial: high regulatory presence, variable TIV

**Mitigation**: Develop sector-specific weight configurations if baseline validation shows significant sector variation.

-----

## 8. Validation Timeline

|Phase                 |Duration|Activities                              |
|----------------------|--------|----------------------------------------|
|1. Data Collection    |2 weeks |Extract calibration dataset, verify TIVs|
|2. Signal Extraction  |2 weeks |Run extractors on calibration entities  |
|3. Analysis           |3 weeks |Execute all validation tests            |
|4. Sensitivity Testing|1 week  |Weight/threshold/outlier sensitivity    |
|5. Report Preparation |1 week  |Document findings, visualizations       |
|6. Review & Iteration |2 weeks |Stakeholder review, address feedback    |

**Total: 11 weeks**

-----

## 9. Deliverables Checklist

|Deliverable               |Description                       |Status|
|--------------------------|----------------------------------|------|
|Calibration dataset       |CSV with all required fields      |☐     |
|Correlation analysis      |Test 1 results and visualizations |☐     |
|Discrimination analysis   |Test 2 results and visualizations |☐     |
|Calibration analysis      |Test 3 results and visualizations |☐     |
|Stability analysis        |Test 4 results by segment         |☐     |
|Incremental value analysis|Test 5 regression comparison      |☐     |
|Complexity validation     |Test 6 results (if data available)|☐     |
|Sensitivity analysis      |Weight/threshold/outlier results  |☐     |
|Validation report         |Complete report per template      |☐     |
|Recommendation memo       |Deployment recommendation         |☐     |

-----

## 10. Contacts and Escalation

|Role             |Responsibility                           |
|-----------------|-----------------------------------------|
|Lead Actuary     |Final validation sign-off                |
|Data Science Lead|Signal extraction and scoring methodology|
|Pricing Actuary  |Calibration dataset preparation          |
|Underwriting Lead|Ground truth verification                |
|Project Manager  |Timeline and deliverable tracking        |

-----

## Document End

**Version**: 1.0  
**Status**: For Actuarial Team Use  
**Classification**: Internal Technical Document
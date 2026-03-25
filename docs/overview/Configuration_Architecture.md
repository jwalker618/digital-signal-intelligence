# ${\color{blue}Digital\space Signal\space Intelligence\space (DSI)}$

## A New Information Substrate for Insurance

| Item | Value |
|-|-|
|Version|0.1.0|
|Date|January 2025|
|Classification|Configuration Architecture|

---

# Configuration Architecture

## Overview

This document describes the DSI configuration architecture, explaining how the different layers work together to enable signal-based pricing, loss correlation, exposure estimation, and the Organisational Graph.

---

## Architectural Layers

DSI uses a layered architecture that separates concerns and enables different specialists to own different components:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    ORGANISATION-WIDE SCHEMA                             │
│                  (schemas/organisational_graph.yaml)                    │
│                                                                         │
│  Owned by: Data Architecture / Ontology Team                            │
│  Defines: Node types, edge types, derivatives, graph operations         │
│  Changes: Rarely (major architectural decisions)                        │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ references
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                     COVERAGE CONFIGURATION                              │
│                 (coverages/{coverage}/config.yaml)                      │
│                                                                         │
│  Owned by: Product / Actuarial Team                                     │
│  Defines: Signals, weights, bands, pricing parameters                   │
│  Changes: Regularly (tuning, new signals)                               │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ informed by
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        ANALYSIS OUTPUTS                                 │
│              (analysis_outputs/{coverage}_v{date}.yaml)                 │
│                                                                         │
│  Owned by: Actuarial / Data Science Team                                │
│  Defines: Empirically-derived parameters (lag, normalizer coefficients) │
│  Changes: Periodically (model recalibration)                            │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ combined into
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         MODEL VERSION                                   │
│                 (models/{coverage}_v{version}.yaml)                     │
│                                                                         │
│  Owned by: Model Governance                                             │
│  Contains: Locked snapshot of config + analysis at deployment           │
│  Changes: Never (immutable once deployed)                               │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ priced through
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                     COMMERCIAL ENTITY                                   │
│                (commercial/entities/{entity}.yaml)                      │
│                                                                         │
│  Owned by: Distribution / Underwriting Management                       │
│  Defines: Appetite, distribution, commission, taxes, FX, discretion     │
│  Changes: Occasionally (new entities, authority changes)                │
│  See: docs/overview/Commercial_Entity_Schema.md                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Coverage Configuration Structure

Each coverage has a configuration file that defines:

### 1. Metadata

Basic information about the model:

```yaml
metadata:
  name: "DSI Cyber Technical Pricing Model"
  version: "2.0.0"
  loss_correlation_layer:
    enabled: true
    monitoring: {...}
  exposure_shadow_layer:
    enabled: true
    monitoring: {...}
```

### 2. Direct Queries (Optional)

Yes/No questions for factors that cannot be externally observed:

```yaml
direct_queries:
  - id: "mfa_enabled"
    question: "Is multi-factor authentication enabled?"
    bands:
      - return: false
        action: "FLAG"
        note: "MFA not enabled - increased ransomware risk"
```

### 3. Categorical Groups and Features

Classifications derived from signals that impact pricing:

```yaml
categorical_groups:
  - id: "industry_classification"
    impact: "modifier"
    inference_utility_function: industry_classification_basefunction

categorical_features:
  industry_classification:
    - cat: "HEALTHCARE"
      modifier: 1.50
```

### 4. Signal Groups

High-level groupings of signals. Each group can contribute to risk, loss, and/or exposure:

```yaml
signal_groups:
  - id: "technical_infrastructure"
    name: "Technical Infrastructure"
    risk:
      weight: 0.35
      score_condition: true
      bands: [...]
    loss:
      weight: 0.35
      confidence_threshold: 0.7
```

### 5. Signal Features

Individual signals with their inference functions and dimension-specific configurations:

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
      exposure:  # Optional - if signal contributes to exposure
        weight: 0.04
        proxy_tier: INFERRED_PROXY
        group: digital_footprint
```

---

## The Three Dimensions

Every signal can contribute to one or more of three dimensions:

### Risk (Tier Scoring)

- **Purpose**: Determine pricing tier and underwriting action
- **Output**: Score 0-1000, mapped to Tier 1-5
- **Configuration**:
  - `weight`: Contribution to group score
  - `score_condition`: Whether to apply conditional bands
  - `bands`: Thresholds for DECLINE/REFER/FLAG actions

### Loss (Propensity Scoring)

- **Purpose**: Predict claim frequency and severity
- **Output**: Loss propensity band (very_low to high)
- **Configuration**:
  - `weight`: Contribution to loss propensity score
  - `correlation_type`: frequency, severity, or both
  - `correlation_direction`: positive or negative correlation
  - `normalizer`: How to transform raw score (moved to analysis layer)

### Exposure (TIV Proxy)

- **Purpose**: Estimate Total Insurable Value without client-provided data
- **Output**: Exposure band (micro to very_large) and complexity category
- **Configuration**:
  - `weight`: Contribution to magnitude or complexity score
  - `proxy_tier`: Data quality indicator (DIRECT_OBSERVABLE, INFERRED_PROXY, COHORT_INFERENCE)
  - `group`: Which exposure group this signal belongs to

---

## Unified Signal Collection

A fundamental principle: **signals are collected once and interpreted multiple ways**.

```
                    ┌─────────────────────────┐
                    │   Signal Collection     │
                    │   (inference function)  │
                    └───────────┬─────────────┘
                                │
                                │ raw score (0-100)
                                │
            ┌───────────────────┼───────────────────┐
            ▼                   ▼                   ▼
    ┌───────────────┐   ┌───────────────┐   ┌───────────────┐
    │ Risk Layer    │   │ Loss Layer    │   │Exposure Layer │
    │               │   │               │   │               │
    │ weight: 0.12  │   │ weight: 0.25  │   │ weight: 0.04  │
    │ → tier score  │   │ correlation:- │   │ proxy: INFER  │
    │               │   │ → propensity  │   │ → TIV proxy   │
    └───────────────┘   └───────────────┘   └───────────────┘
```

Benefits:
- Single source of truth for signal definitions
- One inference function call serves all dimensions
- Consistent monitoring across risk, loss, and exposure
- Reduced complexity and maintenance burden

---

## Pricing Integration

Both loss and exposure integrate with pricing using a consistent pattern:

### Calculation Formula

```
dimension_modifier = (component_1 × weight_1) + (component_2 × weight_2)
final_modifier = constrain(dimension_modifier, band_floor, band_cap)
```

### Loss Integration

```yaml
loss_integration:
  method: multiplicative
  frequency_weight: 0.6
  severity_weight: 0.4
  band_constraints:
    elevated:
      floor: 1.10
      cap: 1.30
```

Calculation: `(freq_mult × 0.6) + (sev_mult × 0.4)`, constrained by band.

### Exposure Integration

```yaml
exposure_integration:
  method: multiplicative
  exposure_weight: 0.60
  complexity_weight: 0.40
  band_constraints:
    large:
      floor: 1.30
      cap: 1.70
```

Calculation: `(exposure_mod × 0.6) + (complexity_mod × 0.4)`, constrained by band.

### Auditability

All components are stored at the atomic level:
- Individual signal scores
- Group aggregations
- Dimension calculations
- Final modifiers

This ensures full transparency and enables model governance review.

---

## Exposure Scoring

Exposure signals are grouped into two categories:

### Magnitude Groups (TIV Proxy)

| Group | Purpose | Example Signals |
|-|-|-|
| digital_footprint | Digital scale | subdomain_count, ssl_certificate_count |
| corporate_indicators | Business scale | employee_estimate, location_count |
| public_financials | Direct financials | market_cap, revenue_estimate |
| industry_context | Cohort benchmarks | industry_tiv_benchmark |

### Complexity Groups

| Group | Purpose | Example Signals |
|-|-|-|
| geographic_dispersion | Where they operate | country_count, timezone_spread |
| structural_complexity | Corporate structure | subsidiary_count, brand_count |
| technical_heterogeneity | Tech stack variety | tech_stack_diversity, multi_cloud_indicator |
| regulatory_jurisdictions | Compliance burden | regulatory_jurisdiction_count |

---

## Organisational Graph Integration

The Organisational Graph schema (`schemas/organisational_graph.yaml`) defines:

### Node Types

- **organisation**: The insured entity
- **asset**: Domains, IPs, certificates, cloud resources
- **partner**: Vendors, customers, certification bodies
- **person**: Leadership, security team
- **process**: Hiring, security operations, compliance
- **jurisdiction**: Geographic and regulatory

### Edge Types

- **dependency**: Operational dependencies
- **trust**: Authority relationships (PageRank-style)
- **data_flow**: Data movement paths
- **ownership**: Parent-subsidiary relationships
- **operates_in**: Jurisdictional presence
- **employment**: Personnel relationships

### Behavioural Derivatives

Computed from signal time-series:

| Derivative | Indicates | Early Warning Of |
|-|-|-|
| Entropy | Control decay | Security degradation |
| Velocity | Change rate vs governance | Operational overload |
| Drift | Deviation from peers | Emerging fragility |
| Concentration | Single points of failure | Resilience gaps |
| Fragility | Composite resilience | Inability to absorb shocks |

### Coverage Binding

Each coverage config references the schema and defines how its signals attach:

```yaml
graph_bindings:
  schema_ref: "schemas/organisational_graph.yaml"
  node_bindings:
    asset:
      signals: [tls_score, security_headers, cve_exposure]
    partner:
      signals: [customer_quality, partner_quality, security_vendor]
```

---

## Analysis Layer

Empirically-derived parameters are separated from configuration:

### What Goes in Config (design decisions)

- Signal definitions and inference functions
- Weights (how much each signal matters)
- Correlation type and direction
- Band thresholds

### What Goes in Analysis (empirical findings)

- `lag_months`: Time delay between signal and claim
- Normalizer coefficients: Shape of score-to-outcome relationship
- Confidence intervals
- Sample sizes

### Analysis Output Example

```yaml
# analysis_outputs/cyber_loss_correlation_v2026-01.yaml
signal_correlations:
  security_headers:
    lag_months: 6
    lag_confidence: 0.82
    normalizer_coefficients:
      type: piecewise_linear
      breakpoints: [20, 50, 80]
      slopes: [0.8, 1.0, 1.2]
```

---

## Monitoring

With unified signal collection, monitoring becomes standardised:

```yaml
monitoring:
  refresh_frequency: monthly
  deterioration_threshold: 15   # Alert if score drops by 15+
  improvement_threshold: 15     # Alert if score improves by 15+
  alert_on_band_change: true
  alert_on_velocity_spike: true
  velocity_spike_threshold: 10.0
```

The same signals serve:
- Risk tier monitoring (premium adequacy)
- Loss propensity monitoring (claims prediction)
- Exposure monitoring (TIV drift)
- Derivative calculation (entropy, velocity, drift)

---

## Summary

| Layer | Owner | Contents | Changes |
|-|-|-|-|
| Org Graph Schema | Data Architecture | Node/edge types, derivatives | Rarely |
| Coverage Config | Product/Actuarial | Signals, weights, bands | Regularly |
| Analysis Output | Data Science | Empirical parameters | Periodically |
| Model Version | Governance | Locked snapshot | Never |
| Commercial Entity | Distribution/UW Mgmt | Appetite, commission, taxes, distribution | Occasionally |

This architecture enables:
- **Separation of concerns**: Different specialists own different layers
- **Unified signals**: Collect once, interpret for risk/loss/exposure
- **Technical/commercial separation**: Pricing engine produces a USD technical premium; commercial entities handle distribution economics, FX, and offered premium independently
- **Full auditability**: Every component recorded at atomic level
- **World Model readiness**: Graph schema enables causal simulation

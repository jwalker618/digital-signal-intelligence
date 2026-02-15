# Aerospace Coverage Configuration

**Coverage ID:** `aerospace`
**Generated:** 2026-02-13 13:34
**Schema Version:** v2.2

This document describes the configuration, decision logic, and pricing structure
for the Aerospace coverage vertical in the DSI platform.

## Table of Contents

1. [Configuration Overview](#configuration-overview)
2. [Signal Groups](#signal-groups)
3. [Scoring Logic](#scoring-logic)
4. [Pricing Structure](#pricing-structure)
5. [Direct Queries](#direct-queries)
6. [Decision Flow](#decision-flow)


---


## Configuration: Aerospace General

### Metadata

- **Name:** DSI Aerospace Insurance Model
- **Version:** 2.2.0
- **Description:** Aviation hull and liability coverage based on observable safety and operational signals
- **Product Types:** `aviation_hull`, `aviation_liability`, `aviation_hull_liability_combined`
- **Markets:** US, UK, EU, APAC, LATAM, MEA
- **Minimum Premium:** $25,000
- **Currency:** USD

#### Multiplexer Configuration (V4)

- **Model Specificity:** 1 (General)
- **Routing Constraints:** None (accepts all)

### Signal Registry

**Total Signals:** 48


#### Group: `corporate_governance`

| Signal ID | Type | Weight | Direction | Proxy Tier |
|-----------|------|--------|-----------|------------|
| `management_stability` | Scoring | 25.00% | positive | INFERRED_PROXY |
| `safety_leadership` | Scoring | 25.00% | positive | INFERRED_PROXY |
| `safety_reporting` | Scoring | 20.00% | positive | DIRECT_OBSERVABLE |
| `corporate_structure` | Scoring | 15.00% | positive | INFERRED_PROXY |
| `industry_engagement` | Scoring | 15.00% | positive | DIRECT_OBSERVABLE |

#### Group: `financial_stability`

| Signal ID | Type | Weight | Direction | Proxy Tier |
|-----------|------|--------|-----------|------------|
| `credit_rating` | Scoring | 35.00% | positive | DIRECT_OBSERVABLE |
| `public_financials` | Scoring | 30.00% | positive | DIRECT_OBSERVABLE |
| `market_position` | Scoring | 20.00% | positive | INFERRED_PROXY |
| `government_support` | Scoring | 15.00% | positive | DIRECT_OBSERVABLE |

#### Group: `fleet_category`

| Signal ID | Type | Weight | Direction | Proxy Tier |
|-----------|------|--------|-----------|------------|
| `fleet_category` | Categorical | N/A | modifier | INFERRED_PROXY |

#### Group: `fleet_quality`

| Signal ID | Type | Weight | Direction | Proxy Tier |
|-----------|------|--------|-----------|------------|
| `fleet_age` | Scoring | 30.00% | negative | INFERRED_PROXY |
| `fleet_homogeneity` | Scoring | 20.00% | positive | INFERRED_PROXY |
| `aircraft_generation` | Scoring | 25.00% | positive | INFERRED_PROXY |
| `order_backlog` | Scoring | 15.00% | positive | DIRECT_OBSERVABLE |
| `maintenance_indicators` | Scoring | 5.00% | positive | INFERRED_PROXY |
| `supply_chain_quality` | Scoring | 5.00% | positive | INFERRED_PROXY |

#### Group: `fleet_size`

| Signal ID | Type | Weight | Direction | Proxy Tier |
|-----------|------|--------|-----------|------------|
| `fleet_size` | Categorical | N/A | modifier | INFERRED_PROXY |

#### Group: `iosa_status`

| Signal ID | Type | Weight | Direction | Proxy Tier |
|-----------|------|--------|-----------|------------|
| `iosa_status` | Categorical | N/A | modifier | INFERRED_PROXY |

#### Group: `network_authority`

| Signal ID | Type | Weight | Direction | Proxy Tier |
|-----------|------|--------|-----------|------------|
| `alliance_membership` | Scoring | 25.00% | positive | DIRECT_OBSERVABLE |
| `codeshare_quality` | Scoring | 20.00% | positive | INFERRED_PROXY |
| `lessor_quality` | Scoring | 20.00% | positive | INFERRED_PROXY |
| `oem_relationship` | Scoring | 15.00% | positive | INFERRED_PROXY |
| `mro_quality` | Scoring | 20.00% | positive | INFERRED_PROXY |

#### Group: `operational_quality`

| Signal ID | Type | Weight | Direction | Proxy Tier |
|-----------|------|--------|-----------|------------|
| `otp_score` | Scoring | 20.00% | positive | DIRECT_OBSERVABLE |
| `dispatch_reliability` | Scoring | 20.00% | positive | DIRECT_OBSERVABLE |
| `crew_experience` | Scoring | 15.00% | positive | INFERRED_PROXY |
| `training_indicators` | Scoring | 15.00% | positive | INFERRED_PROXY |
| `operational_complexity` | Scoring | 15.00% | negative | INFERRED_PROXY |
| `growth_rate` | Scoring | 15.00% | negative | DIRECT_OBSERVABLE |

#### Group: `operator_type`

| Signal ID | Type | Weight | Direction | Proxy Tier |
|-----------|------|--------|-----------|------------|
| `operator_type` | Categorical | N/A | modifier | INFERRED_PROXY |

#### Group: `regulatory_compliance`

| Signal ID | Type | Weight | Direction | Proxy Tier |
|-----------|------|--------|-----------|------------|
| `certificate_status` | Scoring | 25.00% | positive | DIRECT_OBSERVABLE |
| `enforcement_actions` | Scoring | 20.00% | positive | DIRECT_OBSERVABLE |
| `iosa_audit_status` | Scoring | 15.00% | positive | DIRECT_OBSERVABLE |
| `ramp_inspection` | Scoring | 15.00% | positive | DIRECT_OBSERVABLE |
| `eu_safety_list` | Scoring | 15.00% | positive | DIRECT_OBSERVABLE |
| `state_safety_rating` | Scoring | 5.00% | positive | DIRECT_OBSERVABLE |
| `certification_transparency` | Scoring | 5.00% | positive | INFERRED_PROXY |

#### Group: `regulatory_framework`

| Signal ID | Type | Weight | Direction | Proxy Tier |
|-----------|------|--------|-----------|------------|
| `regulatory_framework` | Categorical | N/A | modifier | INFERRED_PROXY |

#### Group: `route_risk`

| Signal ID | Type | Weight | Direction | Proxy Tier |
|-----------|------|--------|-----------|------------|
| `conflict_zone_exposure` | Scoring | 30.00% | negative | DIRECT_OBSERVABLE |
| `challenging_airports` | Scoring | 20.00% | negative | DIRECT_OBSERVABLE |
| `high_risk_destinations` | Scoring | 25.00% | negative | DIRECT_OBSERVABLE |
| `weather_exposure` | Scoring | 15.00% | negative | INFERRED_PROXY |
| `terrain_exposure` | Scoring | 10.00% | negative | INFERRED_PROXY |

#### Group: `safety_record`

| Signal ID | Type | Weight | Direction | Proxy Tier |
|-----------|------|--------|-----------|------------|
| `accident_history` | Scoring | 30.00% | positive | DIRECT_OBSERVABLE |
| `incident_history` | Scoring | 20.00% | positive | DIRECT_OBSERVABLE |
| `accident_rate` | Scoring | 20.00% | positive | COHORT_INFERENCE |
| `fatality_history` | Scoring | 20.00% | positive | DIRECT_OBSERVABLE |
| `investigation_findings` | Scoring | 10.00% | positive | DIRECT_OBSERVABLE |

### Signal Groups

#### Categorical Groups

These groups apply modifiers based on classification:

| Group ID | Label | Impact | Default |
|----------|-------|--------|---------|
| `operator_type` | Operator Type | MODIFIER | OTHER |
| `fleet_category` | Fleet category | MODIFIER | OTHER |
| `fleet_size` | Fleet Size | MODIFIER | OTHER |
| `regulatory_framework` | Regulatory Framework | MODIFIER | OTHER |
| `iosa_status` | IOSA Status | MODIFIER | NOT_APPLICABLE |

#### Three-Layer Assessment Groups

These groups contribute to Risk, Loss, and Exposure scoring:

| Group ID | Risk Weight | Loss Weight | Exposure Weight |
|----------|-------------|-------------|-----------------|
| `network_authority` | 10% | 0% | 0% |
| `safety_record` | 30% | 0% | 0% |
| `regulatory_compliance` | 20% | 0% | 0% |
| `operational_quality` | 15% | 0% | 0% |
| `fleet_quality` | 10% | 0% | 0% |
| `financial_stability` | 5% | 0% | 0% |
| `route_risk` | 5% | 0% | 0% |
| `corporate_governance` | 5% | 0% | 0% |

### Risk Tier Bands

Risk tiers determine the base pricing and underwriting action:

| Tier | Label | Score Range | Action | Base Premium |
|------|-------|-------------|--------|--------------|
| 1 | PREFERRED | 800-1000 | APPROVE | $0 |
| 2 | STANDARD_PLUS | 650-799 | APPROVE | $0 |
| 3 | STANDARD | 500-649 | REFER | $0 |
| 4 | SUBSTANDARD | 350-499 | REFER | $0 |
| 5 | DECLINE | 0-349 | DECLINE | $0 |

**Decision Logic:**
- Scores 0-1000 (composite from weighted signals)
- Higher scores = better risk = lower tier number
- APPROVE: Automatic binding eligible
- REFER: Requires underwriter review
- DECLINE: Outside risk appetite

### Loss Tier Bands

Loss tiers adjust premium based on expected loss frequency and severity:

| Tier | Label | Score Range | Freq Modifier | Sev Modifier |
|------|-------|-------------|---------------|--------------|
| 1 | VERY_LOW | 80-100 | 0.70x | 0.80x |
| 2 | LOW | 60-79 | 0.85x | 0.90x |
| 3 | MODERATE | 40-59 | 1.00x | 1.00x |
| 4 | ELEVATED | 20-39 | 1.15x | 1.15x |
| 5 | HIGH | 0-19 | 1.35x | 1.40x |

**Constraints:** Floor = 0.55, Cap = 1.60

### Direct Queries

Binary questions that cannot be inferred from external signals:

| Query ID | Question | Trigger | Action | Impact |
|----------|----------|---------|--------|--------|
| `pending_claims` | Are there any pending aviation liability claims ex... | Answer = True | REFER | Override to Tier 3 |
| `regulatory_action` | Is there any pending regulatory enforcement action... | Answer = True | REFER | Override to Tier 5 |
| `coverage_declined` | Has aviation coverage been declined or non-renewed... | Answer = True | REFER | Override to Tier 5 |
| `fleet_change` | Are there planned fleet changes exceeding 20% in t... | Answer = True | REFER | Override to Tier 3 |
| `route_expansion` | Is there planned expansion into conflict zones or ... | Answer = True | REFER | Override to Tier 4 |
| `ownership_change` | Has there been a change in majority ownership in t... | Answer = True | REFER | Override to Tier 3 |
| `wet_lease_operations` | Do you operate aircraft under wet lease arrangemen... | Answer = True | MODIFIER | Modifier: 1.15x |

**Action Types:**
- **FLAG:** Adds note to underwriter; no pricing impact
- **MODIFIER:** Applies premium multiplier
- **REFER:** Forces underwriter review regardless of score

### Pricing Structure

Pricing varies by product type:


#### Aviation Hull

**Pricing Anchors (V5):**
- Base Limit Reference: $10,000,000
- Base Deductible Reference: $50,000

**Increased Limit Factors (ILF):**

| Limit | Factor | Premium Multiplier |
|-------|--------|-------------------|
| $10,000,000 (base) | 1.00 | 1.00x base |
| $25,000,000 | 2.00 | 2.00x base |
| $50,000,000 | 3.50 | 3.50x base |
| $100,000,000 | 6.00 | 6.00x base |
| $250,000,000 | 12.00 | 12.00x base |
| $500,000,000 | 20.00 | 20.00x base |
| $1,000,000,000 | 35.00 | 35.00x base |

**Deductible Factors (V5):**

| Deductible | Factor | Effect |
|------------|--------|--------|
| $10,000 | 1.50 | +50% loading |
| $25,000 | 1.15 | +15% loading |
| $50,000 (anchor) | 1.00 | Base price |
| $100,000 | 0.95 | -5% credit |
| $250,000 | 0.90 | -10% credit |
| $500,000 | 0.70 | -30% credit |
| $1,000,000 | 0.70 | -30% credit |


#### Aviation Liability

**Pricing Anchors (V5):**
- Base Limit Reference: $10,000,000
- Base Deductible Reference: $50,000

**Increased Limit Factors (ILF):**

| Limit | Factor | Premium Multiplier |
|-------|--------|-------------------|
| $10,000,000 (base) | 1.00 | 1.00x base |
| $25,000,000 | 2.30 | 2.30x base |
| $50,000,000 | 4.20 | 4.20x base |
| $100,000,000 | 7.50 | 7.50x base |
| $250,000,000 | 15.50 | 15.50x base |
| $500,000,000 | 27.00 | 27.00x base |
| $1,000,000,000 | 48.00 | 48.00x base |

**Deductible Factors (V5):**

| Deductible | Factor | Effect |
|------------|--------|--------|
| $10,000 | 1.50 | +50% loading |
| $25,000 | 1.15 | +15% loading |
| $50,000 (anchor) | 1.00 | Base price |
| $100,000 | 0.96 | -4% credit |
| $250,000 | 0.92 | -8% credit |
| $500,000 | 0.70 | -30% credit |
| $1,000,000 | 0.70 | -30% credit |


#### Aviation Hull Liability Combined

**Pricing Anchors (V5):**
- Base Limit Reference: $10,000,000
- Base Deductible Reference: $50,000

**Increased Limit Factors (ILF):**

| Limit | Factor | Premium Multiplier |
|-------|--------|-------------------|
| $10,000,000 (base) | 1.00 | 1.00x base |
| $25,000,000 | 2.15 | 2.15x base |
| $50,000,000 | 3.85 | 3.85x base |
| $100,000,000 | 6.75 | 6.75x base |
| $250,000,000 | 13.75 | 13.75x base |
| $500,000,000 | 23.50 | 23.50x base |
| $1,000,000,000 | 41.50 | 41.50x base |

**Deductible Factors (V5):**

| Deductible | Factor | Effect |
|------------|--------|--------|
| $10,000 | 1.50 | +50% loading |
| $25,000 | 1.15 | +15% loading |
| $50,000 (anchor) | 1.00 | Base price |
| $100,000 | 0.95 | -5% credit |
| $250,000 | 0.91 | -9% credit |
| $500,000 | 0.70 | -30% credit |
| $1,000,000 | 0.70 | -30% credit |


### Limit Bandings

Pre-configured limit/deductible packages:

| Package | Limit | Deductible |
|---------|-------|------------|
| 1 | $10,000,000 | $500,000 |
| 2 | $25,000,000 | $1,000,000 |
| 3 | $50,000,000 | $2,000,000 |
| 4 | $100,000,000 | $5,000,000 |
| 5 | $250,000,000 | $10,000,000 |


---


## Configuration: Aerospace Sme

### Metadata

- **Name:** DSI Aerospace SME Model
- **Version:** 2.2.0
- **Description:** Aviation coverage for small/medium operators with hull value under $50M
- **Product Types:** `aviation_hull`, `aviation_liability`, `aviation_hull_liability_combined`
- **Markets:** US, UK, EU, APAC, LATAM, MEA
- **Minimum Premium:** $15,000
- **Currency:** USD

#### Multiplexer Configuration (V4)

- **Model Specificity:** 2 (Segment)
- **Routing Constraints:**
  - `hull_value <= 50000000` (required)
  - `limit <= 10000000` (required)

### Signal Registry

**Total Signals:** 22


#### Group: `corporate_governance`

| Signal ID | Type | Weight | Direction | Proxy Tier |
|-----------|------|--------|-----------|------------|
| `management_stability` | Scoring | 40.00% | positive | INFERRED_PROXY |
| `safety_leadership` | Scoring | 35.00% | positive | INFERRED_PROXY |
| `corporate_structure` | Scoring | 25.00% | positive | INFERRED_PROXY |

#### Group: `fleet_category`

| Signal ID | Type | Weight | Direction | Proxy Tier |
|-----------|------|--------|-----------|------------|
| `fleet_category` | Categorical | N/A | modifier | INFERRED_PROXY |

#### Group: `fleet_quality`

| Signal ID | Type | Weight | Direction | Proxy Tier |
|-----------|------|--------|-----------|------------|
| `fleet_age` | Scoring | 40.00% | negative | INFERRED_PROXY |
| `fleet_homogeneity` | Scoring | 25.00% | positive | INFERRED_PROXY |
| `maintenance_indicators` | Scoring | 35.00% | positive | INFERRED_PROXY |

#### Group: `fleet_size`

| Signal ID | Type | Weight | Direction | Proxy Tier |
|-----------|------|--------|-----------|------------|
| `fleet_size` | Categorical | N/A | modifier | INFERRED_PROXY |

#### Group: `operational_quality`

| Signal ID | Type | Weight | Direction | Proxy Tier |
|-----------|------|--------|-----------|------------|
| `crew_experience` | Scoring | 35.00% | positive | INFERRED_PROXY |
| `training_indicators` | Scoring | 30.00% | positive | INFERRED_PROXY |
| `operational_complexity` | Scoring | 20.00% | negative | INFERRED_PROXY |
| `growth_rate` | Scoring | 15.00% | negative | DIRECT_OBSERVABLE |

#### Group: `operator_type`

| Signal ID | Type | Weight | Direction | Proxy Tier |
|-----------|------|--------|-----------|------------|
| `operator_type` | Categorical | N/A | modifier | INFERRED_PROXY |

#### Group: `regulatory_compliance`

| Signal ID | Type | Weight | Direction | Proxy Tier |
|-----------|------|--------|-----------|------------|
| `certificate_status` | Scoring | 35.00% | positive | DIRECT_OBSERVABLE |
| `enforcement_actions` | Scoring | 30.00% | positive | DIRECT_OBSERVABLE |
| `ramp_inspection` | Scoring | 20.00% | positive | DIRECT_OBSERVABLE |
| `state_safety_rating` | Scoring | 15.00% | positive | DIRECT_OBSERVABLE |

#### Group: `regulatory_framework`

| Signal ID | Type | Weight | Direction | Proxy Tier |
|-----------|------|--------|-----------|------------|
| `regulatory_framework` | Categorical | N/A | modifier | INFERRED_PROXY |

#### Group: `safety_record`

| Signal ID | Type | Weight | Direction | Proxy Tier |
|-----------|------|--------|-----------|------------|
| `accident_history` | Scoring | 35.00% | positive | DIRECT_OBSERVABLE |
| `incident_history` | Scoring | 25.00% | positive | DIRECT_OBSERVABLE |
| `fatality_history` | Scoring | 25.00% | positive | DIRECT_OBSERVABLE |
| `investigation_findings` | Scoring | 15.00% | positive | DIRECT_OBSERVABLE |

### Signal Groups

#### Categorical Groups

These groups apply modifiers based on classification:

| Group ID | Label | Impact | Default |
|----------|-------|--------|---------|
| `operator_type` | Operator Type | MODIFIER | OTHER |
| `fleet_category` | Fleet Category | MODIFIER | OTHER |
| `fleet_size` | Fleet Size | MODIFIER | OTHER |
| `regulatory_framework` | Regulatory Framework | MODIFIER | OTHER |

#### Three-Layer Assessment Groups

These groups contribute to Risk, Loss, and Exposure scoring:

| Group ID | Risk Weight | Loss Weight | Exposure Weight |
|----------|-------------|-------------|-----------------|
| `safety_record` | 35% | 0% | 0% |
| `regulatory_compliance` | 25% | 0% | 0% |
| `operational_quality` | 20% | 0% | 0% |
| `fleet_quality` | 15% | 0% | 0% |
| `corporate_governance` | 5% | 0% | 0% |

### Risk Tier Bands

Risk tiers determine the base pricing and underwriting action:

| Tier | Label | Score Range | Action | Base Premium |
|------|-------|-------------|--------|--------------|
| 1 | PREFERRED | 800-1000 | APPROVE | $0 |
| 2 | STANDARD_PLUS | 650-799 | APPROVE | $0 |
| 3 | STANDARD | 500-649 | REFER | $0 |
| 4 | SUBSTANDARD | 350-499 | REFER | $0 |
| 5 | DECLINE | 0-349 | DECLINE | $0 |

**Decision Logic:**
- Scores 0-1000 (composite from weighted signals)
- Higher scores = better risk = lower tier number
- APPROVE: Automatic binding eligible
- REFER: Requires underwriter review
- DECLINE: Outside risk appetite

### Loss Tier Bands

Loss tiers adjust premium based on expected loss frequency and severity:

| Tier | Label | Score Range | Freq Modifier | Sev Modifier |
|------|-------|-------------|---------------|--------------|
| 1 | VERY_LOW | 80-100 | 0.70x | 0.80x |
| 2 | LOW | 60-79 | 0.85x | 0.90x |
| 3 | MODERATE | 40-59 | 1.00x | 1.00x |
| 4 | ELEVATED | 20-39 | 1.15x | 1.15x |
| 5 | HIGH | 0-19 | 1.30x | 1.35x |

**Constraints:** Floor = 0.60, Cap = 1.50

### Direct Queries

Binary questions that cannot be inferred from external signals:

| Query ID | Question | Trigger | Action | Impact |
|----------|----------|---------|--------|--------|
| `pending_claims` | Are there any pending aviation liability claims ex... | Answer = True | REFER | Override to Tier 3 |
| `regulatory_action` | Is there any pending regulatory enforcement action... | Answer = True | REFER | Override to Tier 5 |
| `coverage_declined` | Has aviation coverage been declined or non-renewed... | Answer = True | REFER | Override to Tier 5 |
| `fleet_change` | Are there planned fleet changes exceeding 30% in t... | Answer = True | REFER | Override to Tier 3 |
| `route_expansion` | Is there planned expansion into conflict zones or ... | Answer = True | REFER | Override to Tier 4 |
| `ownership_change` | Has there been a change in majority ownership in t... | Answer = True | REFER | Override to Tier 3 |

**Action Types:**
- **FLAG:** Adds note to underwriter; no pricing impact
- **MODIFIER:** Applies premium multiplier
- **REFER:** Forces underwriter review regardless of score

### Pricing Structure

Pricing varies by product type:


#### Aviation Hull

**Pricing Anchors (V5):**
- Base Limit Reference: $1,000,000
- Base Deductible Reference: $50,000

**Increased Limit Factors (ILF):**

| Limit | Factor | Premium Multiplier |
|-------|--------|-------------------|
| $1,000,000 (base) | 1.00 | 1.00x base |
| $2,500,000 | 2.00 | 2.00x base |
| $5,000,000 | 3.50 | 3.50x base |
| $10,000,000 | 6.00 | 6.00x base |

**Deductible Factors (V5):**

| Deductible | Factor | Effect |
|------------|--------|--------|
| $10,000 | 1.50 | +50% loading |
| $25,000 | 1.15 | +15% loading |
| $50,000 (anchor) | 1.00 | Base price |
| $100,000 | 0.95 | -5% credit |
| $250,000 | 0.90 | -10% credit |
| $500,000 | 0.70 | -30% credit |
| $1,000,000 | 0.70 | -30% credit |


#### Aviation Liability

**Pricing Anchors (V5):**
- Base Limit Reference: $1,000,000
- Base Deductible Reference: $50,000

**Increased Limit Factors (ILF):**

| Limit | Factor | Premium Multiplier |
|-------|--------|-------------------|
| $1,000,000 (base) | 1.00 | 1.00x base |
| $2,500,000 | 2.20 | 2.20x base |
| $5,000,000 | 4.00 | 4.00x base |
| $10,000,000 | 7.00 | 7.00x base |

**Deductible Factors (V5):**

| Deductible | Factor | Effect |
|------------|--------|--------|
| $10,000 | 1.50 | +50% loading |
| $25,000 | 1.15 | +15% loading |
| $50,000 (anchor) | 1.00 | Base price |
| $100,000 | 0.96 | -4% credit |
| $250,000 | 0.92 | -8% credit |
| $500,000 | 0.70 | -30% credit |
| $1,000,000 | 0.70 | -30% credit |


#### Aviation Hull Liability Combined

**Pricing Anchors (V5):**
- Base Limit Reference: $1,000,000
- Base Deductible Reference: $50,000

**Increased Limit Factors (ILF):**

| Limit | Factor | Premium Multiplier |
|-------|--------|-------------------|
| $1,000,000 (base) | 1.00 | 1.00x base |
| $2,500,000 | 2.10 | 2.10x base |
| $5,000,000 | 3.75 | 3.75x base |
| $10,000,000 | 6.50 | 6.50x base |

**Deductible Factors (V5):**

| Deductible | Factor | Effect |
|------------|--------|--------|
| $10,000 | 1.50 | +50% loading |
| $25,000 | 1.15 | +15% loading |
| $50,000 (anchor) | 1.00 | Base price |
| $100,000 | 0.95 | -5% credit |
| $250,000 | 0.91 | -9% credit |
| $500,000 | 0.70 | -30% credit |
| $1,000,000 | 0.70 | -30% credit |


### Limit Bandings

Pre-configured limit/deductible packages:

| Package | Limit | Deductible |
|---------|-------|------------|
| 1 | $1,000,000 | $25,000 |
| 2 | $2,500,000 | $50,000 |
| 3 | $5,000,000 | $100,000 |
| 4 | $10,000,000 | $250,000 |


---

## Decision Flow Summary

```
┌─────────────────────────────────────────────────────────────┐
│                    DSI Decision Flow                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. SIGNAL EXTRACTION                                       │
│     └─► External APIs → Normalized Scores (0-100)          │
│                                                             │
│  2. GROUP AGGREGATION                                       │
│     └─► Weighted combination within groups                  │
│                                                             │
│  3. THREE-LAYER ASSESSMENT                                  │
│     ├─► Risk Score (0-1000)                                │
│     ├─► Loss Score (frequency × severity)                  │
│     └─► Exposure Score (size × complexity)                 │
│                                                             │
│  4. TIER ASSIGNMENT                                         │
│     └─► Risk Score → Tier Band → Base Premium              │
│                                                             │
│  5. DIRECT QUERIES                                          │
│     └─► Binary answers → FLAGS / MODIFIERS / REFERS        │
│                                                             │
│  6. PRICING CALCULATION                                     │
│     └─► Base × ILF × Ded Factor × Modifiers × Tax          │
│                                                             │
│  7. DECISION OUTPUT                                         │
│     └─► APPROVE / REFER / DECLINE + Audit Trail            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

*Generated by DSI Coverage Documentation Generator*

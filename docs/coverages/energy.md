# Energy Coverage Configuration

**Coverage ID:** `energy`
**Generated:** 2026-02-13 13:34
**Schema Version:** v2.2

This document describes the configuration, decision logic, and pricing structure
for the Energy coverage vertical in the DSI platform.

## Table of Contents

1. [Configuration Overview](#configuration-overview)
2. [Signal Groups](#signal-groups)
3. [Scoring Logic](#scoring-logic)
4. [Pricing Structure](#pricing-structure)
5. [Direct Queries](#direct-queries)
6. [Decision Flow](#decision-flow)


---


## Configuration: Energy General

### Metadata

- **Name:** DSI Energy Technical Pricing Model
- **Version:** 2.2.0
- **Description:** Energy property and liability coverage based on observable safety, environmental, and operational signals
- **Product Types:** `property_damage`, `business_interruption`, `control_of_well`, `operators_extra_expense`, `third_party_liability`, `pollution_liability`, `removal_of_wreck`
- **Markets:** US, UK, EU, APAC, LATAM, MENA
- **Minimum Premium:** $100,000
- **Currency:** USD

#### Multiplexer Configuration (V4)

- **Model Specificity:** 1 (General)
- **Routing Constraints:** None (accepts all)

### Signal Registry

**Total Signals:** 47


#### Group: `asset_portfolio`

| Signal ID | Type | Weight | Direction | Proxy Tier |
|-----------|------|--------|-----------|------------|
| `asset_age` | Scoring | 25.00% | negative | INFERRED_PROXY |
| `concentration` | Scoring | 20.00% | negative | INFERRED_PROXY |
| `complexity` | Scoring | 20.00% | negative | INFERRED_PROXY |
| `decommissioning` | Scoring | 20.00% | positive | INFERRED_PROXY |
| `permit_status` | Scoring | 15.00% | positive | DIRECT_OBSERVABLE |

#### Group: `corporate_footprint`

| Signal ID | Type | Weight | Direction | Proxy Tier |
|-----------|------|--------|-----------|------------|
| `safety_communication` | Scoring | 20.00% | positive | DIRECT_OBSERVABLE |
| `esg_reporting` | Scoring | 20.00% | positive | DIRECT_OBSERVABLE |
| `technical_hiring` | Scoring | 15.00% | positive | INFERRED_PROXY |
| `industry_presence` | Scoring | 15.00% | positive | DIRECT_OBSERVABLE |
| `disclosure_quality` | Scoring | 15.00% | positive | INFERRED_PROXY |
| `hse_leadership` | Scoring | 15.00% | positive | INFERRED_PROXY |

#### Group: `environmental_compliance`

| Signal ID | Type | Weight | Direction | Proxy Tier |
|-----------|------|--------|-----------|------------|
| `epa_violation` | Scoring | 20.00% | positive | DIRECT_OBSERVABLE |
| `spill_history` | Scoring | 25.00% | positive | DIRECT_OBSERVABLE |
| `emissions_compliance` | Scoring | 15.00% | positive | DIRECT_OBSERVABLE |
| `flaring` | Scoring | 15.00% | negative | DIRECT_OBSERVABLE |
| `methane` | Scoring | 15.00% | negative | DIRECT_OBSERVABLE |
| `remediation` | Scoring | 10.00% | positive | INFERRED_PROXY |

#### Group: `financial_stability`

| Signal ID | Type | Weight | Direction | Proxy Tier |
|-----------|------|--------|-----------|------------|
| `credit_rating` | Scoring | 25.00% | positive | DIRECT_OBSERVABLE |
| `leverage` | Scoring | 20.00% | negative | DIRECT_OBSERVABLE |
| `aro_coverage` | Scoring | 20.00% | positive | INFERRED_PROXY |
| `capex_trend` | Scoring | 20.00% | positive | DIRECT_OBSERVABLE |
| `restructuring` | Scoring | 15.00% | positive | DIRECT_OBSERVABLE |

#### Group: `geographic_focus`

| Signal ID | Type | Weight | Direction | Proxy Tier |
|-----------|------|--------|-----------|------------|
| `geographic_focus` | Categorical | N/A | modifier | INFERRED_PROXY |

#### Group: `network_authority`

| Signal ID | Type | Weight | Direction | Proxy Tier |
|-----------|------|--------|-----------|------------|
| `partner_quality` | Scoring | 20.00% | positive | INFERRED_PROXY |
| `contractor_quality` | Scoring | 15.00% | positive | INFERRED_PROXY |
| `banking_relationship` | Scoring | 15.00% | positive | INFERRED_PROXY |
| `insurance_history` | Scoring | 15.00% | positive | INFERRED_PROXY |
| `industry_association` | Scoring | 10.00% | positive | DIRECT_OBSERVABLE |
| `regulator_relationship` | Scoring | 15.00% | positive | INFERRED_PROXY |
| `customer_quality` | Scoring | 10.00% | positive | INFERRED_PROXY |

#### Group: `operation_segment`

| Signal ID | Type | Weight | Direction | Proxy Tier |
|-----------|------|--------|-----------|------------|
| `operation_segment` | Categorical | N/A | modifier | INFERRED_PROXY |

#### Group: `operational_telemetry`

| Signal ID | Type | Weight | Direction | Proxy Tier |
|-----------|------|--------|-----------|------------|
| `production_consistency` | Scoring | 20.00% | positive | INFERRED_PROXY |
| `facility_activity` | Scoring | 20.00% | positive | INFERRED_PROXY |
| `well_integrity` | Scoring | 20.00% | positive | INFERRED_PROXY |
| `maintenance_pattern` | Scoring | 20.00% | positive | INFERRED_PROXY |
| `operational_efficiency` | Scoring | 20.00% | positive | INFERRED_PROXY |

#### Group: `operator_type`

| Signal ID | Type | Weight | Direction | Proxy Tier |
|-----------|------|--------|-----------|------------|
| `operator_type` | Categorical | N/A | modifier | INFERRED_PROXY |

#### Group: `safety_performance`

| Signal ID | Type | Weight | Direction | Proxy Tier |
|-----------|------|--------|-----------|------------|
| `osha_trir` | Scoring | 20.00% | positive | DIRECT_OBSERVABLE |
| `osha_violations` | Scoring | 15.00% | positive | DIRECT_OBSERVABLE |
| `bsee_incident` | Scoring | 10.00% | positive | DIRECT_OBSERVABLE |
| `process_safety` | Scoring | 20.00% | positive | INFERRED_PROXY |
| `fatality` | Scoring | 15.00% | positive | DIRECT_OBSERVABLE |
| `major_incident` | Scoring | 15.00% | positive | DIRECT_OBSERVABLE |
| `near_miss` | Scoring | 5.00% | positive | INFERRED_PROXY |

#### Group: `structured_data`

| Signal ID | Type | Weight | Direction | Proxy Tier |
|-----------|------|--------|-----------|------------|
| `esg_rating` | Scoring | 40.00% | positive | DIRECT_OBSERVABLE |
| `benchmark` | Scoring | 35.00% | positive | COHORT_INFERENCE |
| `credit` | Scoring | 25.00% | positive | DIRECT_OBSERVABLE |

### Signal Groups

#### Categorical Groups

These groups apply modifiers based on classification:

| Group ID | Label | Impact | Default |
|----------|-------|--------|---------|
| `operator_type` | Operator Type | MODIFIER | OTHER |
| `operation_segment` | Operation Segment | MODIFIER | OTHER |
| `geographic_focus` | Geographic Focus | MODIFIER | OTHER |

#### Three-Layer Assessment Groups

These groups contribute to Risk, Loss, and Exposure scoring:

| Group ID | Risk Weight | Loss Weight | Exposure Weight |
|----------|-------------|-------------|-----------------|
| `network_authority` | 10% | 0% | 0% |
| `safety_performance` | 30% | 0% | 0% |
| `environmental_compliance` | 20% | 0% | 0% |
| `operational_telemetry` | 10% | 0% | 0% |
| `financial_stability` | 10% | 0% | 0% |
| `asset_portfolio` | 10% | 0% | 0% |
| `corporate_footprint` | 5% | 0% | 0% |
| `structured_data` | 5% | 0% | 0% |

### Risk Tier Bands

Risk tiers determine the base pricing and underwriting action:

| Tier | Label | Score Range | Action | Base Premium |
|------|-------|-------------|--------|--------------|
| 1 | PREFERRED | 800-1000 | APPROVE | 0.0008x |
| 2 | STANDARD_PLUS | 650-799 | APPROVE | 0.0012x |
| 3 | STANDARD | 500-649 | REFER | 0.0018x |
| 4 | SUBSTANDARD | 350-499 | REFER | 0.0028x |
| 5 | DECLINE | 0-349 | DECLINE | 0.0045x |

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
| `major_incidents` | Any major incidents (explosion, blowout, major spi... | Answer = True | REFER | Override to Tier 4 |
| `fatalities` | Any work-related fatalities in past 3 years? | Answer = True | REFER | Override to Tier 3 |
| `regulatory_enforcement` | Any significant regulatory enforcement actions pen... | Answer = True | REFER | Override to Tier 4 |
| `decommissioning_obligations` | Any significant unfunded decommissioning obligatio... | Answer = True | FLAG | Unfunded decommissioning obligations |
| `joint_venture_operator` | Are you the designated operator for JV assets? | Answer = True | FLAG | JV operator status |
| `third_party_contractor` | Do you use third-party contractors for drilling/co... | Answer = True | FLAG | Third-party contractor usage |

**Action Types:**
- **FLAG:** Adds note to underwriter; no pricing impact
- **MODIFIER:** Applies premium multiplier
- **REFER:** Forces underwriter review regardless of score

### Pricing Structure

Pricing varies by product type:


#### Property Damage

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


#### Business Interruption

**Pricing Anchors (V5):**
- Base Limit Reference: $10,000,000
- Base Deductible Reference: $50,000

**Increased Limit Factors (ILF):**

| Limit | Factor | Premium Multiplier |
|-------|--------|-------------------|
| $10,000,000 (base) | 1.00 | 1.00x base |
| $25,000,000 | 2.20 | 2.20x base |
| $50,000,000 | 4.00 | 4.00x base |
| $100,000,000 | 7.00 | 7.00x base |
| $250,000,000 | 14.50 | 14.50x base |
| $500,000,000 | 25.00 | 25.00x base |
| $1,000,000,000 | 45.00 | 45.00x base |

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


#### Control Of Well

**Pricing Anchors (V5):**
- Base Limit Reference: $10,000,000
- Base Deductible Reference: $50,000

**Increased Limit Factors (ILF):**

| Limit | Factor | Premium Multiplier |
|-------|--------|-------------------|
| $10,000,000 (base) | 1.00 | 1.00x base |
| $25,000,000 | 2.50 | 2.50x base |
| $50,000,000 | 4.80 | 4.80x base |
| $100,000,000 | 8.50 | 8.50x base |
| $250,000,000 | 18.00 | 18.00x base |
| $500,000,000 | 32.00 | 32.00x base |
| $1,000,000,000 | 58.00 | 58.00x base |

**Deductible Factors (V5):**

| Deductible | Factor | Effect |
|------------|--------|--------|
| $10,000 | 1.50 | +50% loading |
| $25,000 | 1.15 | +15% loading |
| $50,000 (anchor) | 1.00 | Base price |
| $100,000 | 0.97 | -3% credit |
| $250,000 | 0.94 | -6% credit |
| $500,000 | 0.70 | -30% credit |
| $1,000,000 | 0.70 | -30% credit |


#### Operators Extra Expense

**Pricing Anchors (V5):**
- Base Limit Reference: $5,000,000
- Base Deductible Reference: $50,000

**Increased Limit Factors (ILF):**

| Limit | Factor | Premium Multiplier |
|-------|--------|-------------------|
| $5,000,000 (base) | 1.00 | 1.00x base |
| $10,000,000 | 1.80 | 1.80x base |
| $25,000,000 | 3.80 | 3.80x base |
| $50,000,000 | 6.50 | 6.50x base |
| $100,000,000 | 11.50 | 11.50x base |
| $250,000,000 | 24.00 | 24.00x base |
| $500,000,000 | 42.00 | 42.00x base |

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


#### Third Party Liability

**Pricing Anchors (V5):**
- Base Limit Reference: $10,000,000
- Base Deductible Reference: $50,000

**Increased Limit Factors (ILF):**

| Limit | Factor | Premium Multiplier |
|-------|--------|-------------------|
| $10,000,000 (base) | 1.00 | 1.00x base |
| $25,000,000 | 2.00 | 2.00x base |
| $50,000,000 | 3.60 | 3.60x base |
| $100,000,000 | 6.20 | 6.20x base |
| $250,000,000 | 13.00 | 13.00x base |
| $500,000,000 | 22.00 | 22.00x base |
| $1,000,000,000 | 38.00 | 38.00x base |

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


#### Pollution Liability

**Pricing Anchors (V5):**
- Base Limit Reference: $10,000,000
- Base Deductible Reference: $50,000

**Increased Limit Factors (ILF):**

| Limit | Factor | Premium Multiplier |
|-------|--------|-------------------|
| $10,000,000 (base) | 1.00 | 1.00x base |
| $25,000,000 | 2.60 | 2.60x base |
| $50,000,000 | 5.00 | 5.00x base |
| $100,000,000 | 9.00 | 9.00x base |
| $250,000,000 | 19.00 | 19.00x base |
| $500,000,000 | 34.00 | 34.00x base |
| $1,000,000,000 | 62.00 | 62.00x base |

**Deductible Factors (V5):**

| Deductible | Factor | Effect |
|------------|--------|--------|
| $10,000 | 1.50 | +50% loading |
| $25,000 | 1.15 | +15% loading |
| $50,000 (anchor) | 1.00 | Base price |
| $100,000 | 0.97 | -3% credit |
| $250,000 | 0.94 | -6% credit |
| $500,000 | 0.70 | -30% credit |
| $1,000,000 | 0.70 | -30% credit |


#### Removal Of Wreck

**Pricing Anchors (V5):**
- Base Limit Reference: $5,000,000
- Base Deductible Reference: $50,000

**Increased Limit Factors (ILF):**

| Limit | Factor | Premium Multiplier |
|-------|--------|-------------------|
| $5,000,000 (base) | 1.00 | 1.00x base |
| $10,000,000 | 1.70 | 1.70x base |
| $25,000,000 | 3.40 | 3.40x base |
| $50,000,000 | 5.80 | 5.80x base |
| $100,000,000 | 10.00 | 10.00x base |
| $250,000,000 | 20.00 | 20.00x base |
| $500,000,000 | 35.00 | 35.00x base |

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

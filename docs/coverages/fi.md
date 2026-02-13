# Fi Coverage Configuration

**Coverage ID:** `financial_institutions`
**Generated:** 2026-02-13 13:34
**Schema Version:** v2.2

This document describes the configuration, decision logic, and pricing structure
for the Fi coverage vertical in the DSI platform.

## Table of Contents

1. [Configuration Overview](#configuration-overview)
2. [Signal Groups](#signal-groups)
3. [Scoring Logic](#scoring-logic)
4. [Pricing Structure](#pricing-structure)
5. [Direct Queries](#direct-queries)
6. [Decision Flow](#decision-flow)


---


## Configuration: Fi General

### Metadata

- **Name:** DSI Financial Institutions Technical Pricing Model
- **Version:** 2.2.0
- **Description:** FI bond, professional liability, D&O, cyber coverage based on observable regulatory and financial signals
- **Product Types:** `financial_institution_bond`, `professional_liability`, `directors_officers`, `cyber_liability`, `employment_practices`, `fiduciary_liability`
- **Markets:** US
- **Minimum Premium:** $25,000
- **Currency:** USD

#### Multiplexer Configuration (V4)

- **Model Specificity:** 1 (General)
- **Routing Constraints:** None (accepts all)

### Signal Registry

**Total Signals:** 51


#### Group: `asset_size_band`

| Signal ID | Type | Weight | Direction | Proxy Tier |
|-----------|------|--------|-----------|------------|
| `asset_size_band` | Categorical | N/A | modifier | INFERRED_PROXY |

#### Group: `corporate_footprint`

| Signal ID | Type | Weight | Direction | Proxy Tier |
|-----------|------|--------|-----------|------------|
| `investor_relations` | Scoring | 20.00% | positive | INFERRED_PROXY |
| `disclosure_quality` | Scoring | 20.00% | positive | INFERRED_PROXY |
| `security_page` | Scoring | 15.00% | positive | DIRECT_OBSERVABLE |
| `hiring_signals` | Scoring | 15.00% | positive | INFERRED_PROXY |
| `esg_reporting` | Scoring | 15.00% | positive | INFERRED_PROXY |
| `community_presence` | Scoring | 15.00% | positive | INFERRED_PROXY |

#### Group: `cyber_security`

| Signal ID | Type | Weight | Direction | Proxy Tier |
|-----------|------|--------|-----------|------------|
| `tls_score` | Scoring | 20.00% | positive | DIRECT_OBSERVABLE |
| `email_auth` | Scoring | 20.00% | positive | DIRECT_OBSERVABLE |
| `security_headers` | Scoring | 15.00% | positive | DIRECT_OBSERVABLE |
| `network_exposure` | Scoring | 20.00% | positive | DIRECT_OBSERVABLE |
| `vulnerability` | Scoring | 15.00% | positive | DIRECT_OBSERVABLE |
| `security_rating` | Scoring | 10.00% | positive | DIRECT_OBSERVABLE |

#### Group: `financial_condition`

| Signal ID | Type | Weight | Direction | Proxy Tier |
|-----------|------|--------|-----------|------------|
| `capital_ratio` | Scoring | 20.00% | positive | DIRECT_OBSERVABLE |
| `asset_quality` | Scoring | 20.00% | positive | DIRECT_OBSERVABLE |
| `liquidity` | Scoring | 15.00% | positive | DIRECT_OBSERVABLE |
| `earnings` | Scoring | 15.00% | positive | DIRECT_OBSERVABLE |
| `concentration` | Scoring | 10.00% | negative | DIRECT_OBSERVABLE |
| `interest_rate_risk` | Scoring | 10.00% | negative | DIRECT_OBSERVABLE |
| `growth_rate` | Scoring | 10.00% | positive | DIRECT_OBSERVABLE |

#### Group: `governance`

| Signal ID | Type | Weight | Direction | Proxy Tier |
|-----------|------|--------|-----------|------------|
| `board_independence` | Scoring | 20.00% | positive | DIRECT_OBSERVABLE |
| `board_expertise` | Scoring | 20.00% | positive | INFERRED_PROXY |
| `executive_stability` | Scoring | 15.00% | positive | INFERRED_PROXY |
| `risk_committee` | Scoring | 20.00% | positive | DIRECT_OBSERVABLE |
| `audit_committee` | Scoring | 15.00% | positive | DIRECT_OBSERVABLE |
| `related_party` | Scoring | 10.00% | negative | DIRECT_OBSERVABLE |

#### Group: `institution_type`

| Signal ID | Type | Weight | Direction | Proxy Tier |
|-----------|------|--------|-----------|------------|
| `institution_type` | Categorical | N/A | modifier | INFERRED_PROXY |

#### Group: `network_authority`

| Signal ID | Type | Weight | Direction | Proxy Tier |
|-----------|------|--------|-----------|------------|
| `correspondent_quality` | Scoring | 20.00% | positive | INFERRED_PROXY |
| `fhlb_membership` | Scoring | 10.00% | positive | DIRECT_OBSERVABLE |
| `clearing_relationship` | Scoring | 15.00% | positive | INFERRED_PROXY |
| `auditor_quality` | Scoring | 20.00% | positive | DIRECT_OBSERVABLE |
| `legal_counsel` | Scoring | 10.00% | positive | INFERRED_PROXY |
| `industry_association` | Scoring | 10.00% | positive | DIRECT_OBSERVABLE |
| `credit_rating` | Scoring | 15.00% | positive | DIRECT_OBSERVABLE |

#### Group: `operational_risk`

| Signal ID | Type | Weight | Direction | Proxy Tier |
|-----------|------|--------|-----------|------------|
| `cfpb_complaint` | Scoring | 25.00% | positive | DIRECT_OBSERVABLE |
| `bbb_complaint` | Scoring | 10.00% | positive | DIRECT_OBSERVABLE |
| `litigation` | Scoring | 25.00% | positive | DIRECT_OBSERVABLE |
| `breach_history` | Scoring | 25.00% | positive | DIRECT_OBSERVABLE |
| `operational_incident` | Scoring | 15.00% | positive | INFERRED_PROXY |

#### Group: `publicly_traded`

| Signal ID | Type | Weight | Direction | Proxy Tier |
|-----------|------|--------|-----------|------------|
| `publicly_traded` | Categorical | N/A | modifier | INFERRED_PROXY |

#### Group: `regulatory_compliance`

| Signal ID | Type | Weight | Direction | Proxy Tier |
|-----------|------|--------|-----------|------------|
| `examination_rating` | Scoring | 20.00% | positive | DIRECT_OBSERVABLE |
| `enforcement_action` | Scoring | 25.00% | positive | DIRECT_OBSERVABLE |
| `informal_action` | Scoring | 10.00% | positive | DIRECT_OBSERVABLE |
| `cra_rating` | Scoring | 10.00% | positive | DIRECT_OBSERVABLE |
| `bsa_aml` | Scoring | 15.00% | positive | DIRECT_OBSERVABLE |
| `fair_lending` | Scoring | 10.00% | positive | DIRECT_OBSERVABLE |
| `consumer_compliance` | Scoring | 10.00% | positive | DIRECT_OBSERVABLE |

#### Group: `regulatory_framework`

| Signal ID | Type | Weight | Direction | Proxy Tier |
|-----------|------|--------|-----------|------------|
| `regulatory_framework` | Categorical | N/A | modifier | INFERRED_PROXY |

#### Group: `structured_data`

| Signal ID | Type | Weight | Direction | Proxy Tier |
|-----------|------|--------|-----------|------------|
| `credit_rating_structured` | Scoring | 40.00% | positive | DIRECT_OBSERVABLE |
| `esg_rating` | Scoring | 30.00% | positive | DIRECT_OBSERVABLE |
| `peer_benchmark` | Scoring | 30.00% | positive | COHORT_INFERENCE |

### Signal Groups

#### Categorical Groups

These groups apply modifiers based on classification:

| Group ID | Label | Impact | Default |
|----------|-------|--------|---------|
| `institution_type` | Institution Type | MODIFIER | OTHER |
| `regulatory_framework` | Regulatory Framework | MODIFIER | OTHER |
| `asset_size_band` | Asset Size Band | MODIFIER | OTHER |
| `publicly_traded` | Publically Traded | MODIFIER | OTHER |

#### Three-Layer Assessment Groups

These groups contribute to Risk, Loss, and Exposure scoring:

| Group ID | Risk Weight | Loss Weight | Exposure Weight |
|----------|-------------|-------------|-----------------|
| `network_authority` | 10% | 0% | 0% |
| `regulatory_compliance` | 25% | 0% | 0% |
| `financial_condition` | 20% | 0% | 0% |
| `governance` | 15% | 0% | 0% |
| `operational_risk` | 10% | 0% | 0% |
| `cyber_security` | 10% | 0% | 0% |
| `corporate_footprint` | 5% | 0% | 0% |
| `structured_data` | 5% | 0% | 0% |

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
| `regulatory_action` | Any pending or recent (3 years) regulatory enforce... | Answer = True | REFER | Override to Tier 4 |
| `examination_issues` | Any MRAs/MRIAs outstanding from most recent examin... | Answer = True | REFER | Override to Tier 3 |
| `litigation_pending` | Any material litigation pending (class action, reg... | Answer = True | REFER | Override to Tier 3 |
| `cyber_incident` | Any reportable cyber incidents in past 24 months? | Answer = True | REFER | Override to Tier 3 |
| `significant_growth` | Asset growth >20% in past 12 months? | Answer = True | FLAG | Rapid growth >20% |
| `new_product_line` | Any significant new product lines launched in past... | Answer = True | FLAG | New product line risk |

**Action Types:**
- **FLAG:** Adds note to underwriter; no pricing impact
- **MODIFIER:** Applies premium multiplier
- **REFER:** Forces underwriter review regardless of score

### Pricing Structure

Pricing varies by product type:


#### Financial Institution Bond

**Pricing Anchors (V5):**
- Base Limit Reference: $1,000,000
- Base Deductible Reference: $50,000

**Increased Limit Factors (ILF):**

| Limit | Factor | Premium Multiplier |
|-------|--------|-------------------|
| $1,000,000 (base) | 1.00 | 1.00x base |
| $2,000,000 | 1.65 | 1.65x base |
| $5,000,000 | 2.90 | 2.90x base |
| $10,000,000 | 4.30 | 4.30x base |
| $25,000,000 | 7.50 | 7.50x base |
| $50,000,000 | 11.50 | 11.50x base |
| $100,000,000 | 17.00 | 17.00x base |

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


#### Professional Liability

**Pricing Anchors (V5):**
- Base Limit Reference: $1,000,000
- Base Deductible Reference: $50,000

**Increased Limit Factors (ILF):**

| Limit | Factor | Premium Multiplier |
|-------|--------|-------------------|
| $1,000,000 (base) | 1.00 | 1.00x base |
| $2,000,000 | 1.75 | 1.75x base |
| $5,000,000 | 3.30 | 3.30x base |
| $10,000,000 | 5.20 | 5.20x base |
| $25,000,000 | 9.50 | 9.50x base |
| $50,000,000 | 15.00 | 15.00x base |
| $100,000,000 | 23.00 | 23.00x base |

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


#### Directors Officers

**Pricing Anchors (V5):**
- Base Limit Reference: $1,000,000
- Base Deductible Reference: $50,000

**Increased Limit Factors (ILF):**

| Limit | Factor | Premium Multiplier |
|-------|--------|-------------------|
| $1,000,000 (base) | 1.00 | 1.00x base |
| $2,000,000 | 1.85 | 1.85x base |
| $5,000,000 | 3.60 | 3.60x base |
| $10,000,000 | 5.80 | 5.80x base |
| $25,000,000 | 11.00 | 11.00x base |
| $50,000,000 | 18.00 | 18.00x base |
| $100,000,000 | 28.00 | 28.00x base |

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


#### Cyber Liability

**Pricing Anchors (V5):**
- Base Limit Reference: $1,000,000
- Base Deductible Reference: $50,000

**Increased Limit Factors (ILF):**

| Limit | Factor | Premium Multiplier |
|-------|--------|-------------------|
| $1,000,000 (base) | 1.00 | 1.00x base |
| $2,000,000 | 1.75 | 1.75x base |
| $5,000,000 | 3.40 | 3.40x base |
| $10,000,000 | 5.50 | 5.50x base |
| $25,000,000 | 10.00 | 10.00x base |
| $50,000,000 | 16.00 | 16.00x base |
| $100,000,000 | 25.00 | 25.00x base |

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


#### Employment Practices

**Pricing Anchors (V5):**
- Base Limit Reference: $1,000,000
- Base Deductible Reference: $50,000

**Increased Limit Factors (ILF):**

| Limit | Factor | Premium Multiplier |
|-------|--------|-------------------|
| $1,000,000 (base) | 1.00 | 1.00x base |
| $2,000,000 | 1.60 | 1.60x base |
| $5,000,000 | 2.80 | 2.80x base |
| $10,000,000 | 4.20 | 4.20x base |
| $25,000,000 | 7.00 | 7.00x base |
| $50,000,000 | 10.50 | 10.50x base |
| $100,000,000 | 15.50 | 15.50x base |

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


#### Fiduciary Liability

**Pricing Anchors (V5):**
- Base Limit Reference: $1,000,000
- Base Deductible Reference: $50,000

**Increased Limit Factors (ILF):**

| Limit | Factor | Premium Multiplier |
|-------|--------|-------------------|
| $1,000,000 (base) | 1.00 | 1.00x base |
| $2,000,000 | 1.70 | 1.70x base |
| $5,000,000 | 3.10 | 3.10x base |
| $10,000,000 | 4.80 | 4.80x base |
| $25,000,000 | 8.50 | 8.50x base |
| $50,000,000 | 13.00 | 13.00x base |
| $100,000,000 | 20.00 | 20.00x base |

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
| 1 | $5,000,000 | $100,000 |
| 2 | $10,000,000 | $250,000 |
| 3 | $25,000,000 | $500,000 |
| 4 | $50,000,000 | $1,000,000 |
| 5 | $100,000,000 | $2,000,000 |


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

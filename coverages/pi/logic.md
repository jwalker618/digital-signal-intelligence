# Pi Coverage Configuration

**Coverage ID:** `professional_indemnity`
**Generated:** 2026-02-15 09:41
**Schema Version:** v2.2

This document describes the configuration, decision logic, and pricing structure
for the Pi coverage vertical in the DSI platform.

## Table of Contents

1. [Configuration Overview](#configuration-overview)
2. [Signal Groups](#signal-groups)
3. [Scoring Logic](#scoring-logic)
4. [Pricing Structure](#pricing-structure)
5. [Direct Queries](#direct-queries)
6. [Decision Flow](#decision-flow)


---


## Configuration: Pi General

### Metadata

- **Name:** DSI Professional Indemnity Technical Pricing Model
- **Version:** 2.2.0
- **Description:** PI/E&O coverage based on observable regulatory, practice quality, and stability signals
- **Product Types:** `professional_liability`, `errors_omissions`, `malpractice`
- **Markets:** US, UK, EU, APAC
- **Minimum Premium:** $2,500
- **Currency:** USD

#### Multiplexer Configuration (V4)

- **Model Specificity:** 1 (General)
- **Routing Constraints:** None (accepts all)

### Signal Registry

**Total Signals:** 44


#### Group: `corporate_footprint`

| Signal ID | Type | Weight | Direction | Proxy Tier |
|-----------|------|--------|-----------|------------|
| `website_quality` | Scoring | 25.00% | positive | DIRECT_OBSERVABLE |
| `bio_completeness` | Scoring | 20.00% | positive | DIRECT_OBSERVABLE |
| `practice_clarity` | Scoring | 15.00% | positive | INFERRED_PROXY |
| `publications` | Scoring | 15.00% | positive | DIRECT_OBSERVABLE |
| `community_involvement` | Scoring | 15.00% | positive | INFERRED_PROXY |
| `diversity` | Scoring | 10.00% | positive | INFERRED_PROXY |

#### Group: `firm_size`

| Signal ID | Type | Weight | Direction | Proxy Tier |
|-----------|------|--------|-----------|------------|
| `firm_size` | Categorical | N/A | modifier | INFERRED_PROXY |

#### Group: `firm_stability`

| Signal ID | Type | Weight | Direction | Proxy Tier |
|-----------|------|--------|-----------|------------|
| `tenure` | Scoring | 20.00% | positive | INFERRED_PROXY |
| `partner_stability` | Scoring | 25.00% | positive | INFERRED_PROXY |
| `staff_retention` | Scoring | 15.00% | positive | INFERRED_PROXY |
| `office_stability` | Scoring | 10.00% | positive | INFERRED_PROXY |
| `financial_stability` | Scoring | 20.00% | positive | INFERRED_PROXY |
| `succession_planning` | Scoring | 10.00% | positive | INFERRED_PROXY |

#### Group: `litigation_history`

| Signal ID | Type | Weight | Direction | Proxy Tier |
|-----------|------|--------|-----------|------------|
| `malpractice_suits` | Scoring | 35.00% | positive | DIRECT_OBSERVABLE |
| `fee_disputes_litigation` | Scoring | 15.00% | positive | DIRECT_OBSERVABLE |
| `regulatory_enforcement` | Scoring | 25.00% | positive | DIRECT_OBSERVABLE |
| `civil_litigation` | Scoring | 15.00% | positive | DIRECT_OBSERVABLE |
| `bankruptcy` | Scoring | 10.00% | positive | DIRECT_OBSERVABLE |

#### Group: `network_authority`

| Signal ID | Type | Weight | Direction | Proxy Tier |
|-----------|------|--------|-----------|------------|
| `peer_ranking` | Scoring | 25.00% | positive | COHORT_INFERENCE |
| `client_quality` | Scoring | 20.00% | positive | INFERRED_PROXY |
| `referral_network` | Scoring | 15.00% | positive | INFERRED_PROXY |
| `association_leadership` | Scoring | 15.00% | positive | DIRECT_OBSERVABLE |
| `thought_leadership` | Scoring | 15.00% | positive | INFERRED_PROXY |
| `panel_membership` | Scoring | 10.00% | positive | DIRECT_OBSERVABLE |

#### Group: `practice_quality`

| Signal ID | Type | Weight | Direction | Proxy Tier |
|-----------|------|--------|-----------|------------|
| `outcome_patterns` | Scoring | 20.00% | positive | INFERRED_PROXY |
| `client_reviews` | Scoring | 25.00% | positive | DIRECT_OBSERVABLE |
| `work_quality` | Scoring | 15.00% | positive | INFERRED_PROXY |
| `fee_dispute` | Scoring | 15.00% | positive | DIRECT_OBSERVABLE |
| `complaint_history` | Scoring | 25.00% | positive | DIRECT_OBSERVABLE |

#### Group: `profession_type`

| Signal ID | Type | Weight | Direction | Proxy Tier |
|-----------|------|--------|-----------|------------|
| `profession_type` | Categorical | N/A | modifier | INFERRED_PROXY |

#### Group: `regulatory_standing`

| Signal ID | Type | Weight | Direction | Proxy Tier |
|-----------|------|--------|-----------|------------|
| `license_status` | Scoring | 25.00% | positive | DIRECT_OBSERVABLE |
| `disciplinary_history` | Scoring | 30.00% | positive | DIRECT_OBSERVABLE |
| `malpractice_record` | Scoring | 15.00% | positive | DIRECT_OBSERVABLE |
| `ce_compliance` | Scoring | 5.00% | positive | DIRECT_OBSERVABLE |
| `specialty_certification` | Scoring | 10.00% | positive | DIRECT_OBSERVABLE |
| `peer_review` | Scoring | 10.00% | positive | DIRECT_OBSERVABLE |
| `pcaob_standing` | Scoring | 5.00% | positive | DIRECT_OBSERVABLE |

#### Group: `revenue_size`

| Signal ID | Type | Weight | Direction | Proxy Tier |
|-----------|------|--------|-----------|------------|
| `revenue_size` | Categorical | N/A | modifier | INFERRED_PROXY |

#### Group: `sub_profession_type`

| Signal ID | Type | Weight | Direction | Proxy Tier |
|-----------|------|--------|-----------|------------|
| `sub_profession_type` | Categorical | N/A | modifier | INFERRED_PROXY |

#### Group: `technical_infrastructure`

| Signal ID | Type | Weight | Direction | Proxy Tier |
|-----------|------|--------|-----------|------------|
| `tls_score` | Scoring | 25.00% | positive | DIRECT_OBSERVABLE |
| `email_auth` | Scoring | 25.00% | positive | DIRECT_OBSERVABLE |
| `security_headers` | Scoring | 15.00% | positive | DIRECT_OBSERVABLE |
| `portal_security` | Scoring | 15.00% | positive | DIRECT_OBSERVABLE |
| `breach_history` | Scoring | 20.00% | positive | DIRECT_OBSERVABLE |

### Signal Groups

#### Categorical Groups

These groups apply modifiers based on classification:

| Group ID | Label | Impact | Default |
|----------|-------|--------|---------|
| `profession_type` | Profession Type | PREMIUM_BASE | OTHER |
| `sub_profession_type` | Sub Profession Type | MODIFIER | OTHER |
| `firm_size` | Firm Size | MODIFIER | OTHER |
| `revenue_size` | Revenue Size | MODIFIER | OTHER |

#### Three-Layer Assessment Groups

These groups contribute to Risk, Loss, and Exposure scoring:

| Group ID | Risk Weight | Loss Weight | Exposure Weight |
|----------|-------------|-------------|-----------------|
| `network_authority` | 15% | 10% | 5% |
| `regulatory_standing` | 25% | 25% | 10% |
| `firm_stability` | 15% | 15% | 20% |
| `practice_quality` | 15% | 20% | 15% |
| `technical_infrastructure` | 10% | 10% | 10% |
| `corporate_footprint` | 10% | 5% | 25% |
| `litigation_history` | 10% | 15% | 15% |

### Risk Tier Bands

Risk tiers determine the base pricing and underwriting action:

| Tier | Label | Score Range | Action | Base Premium |
|------|-------|-------------|--------|--------------|
| 1 | PREFERRED | 800-1000 | APPROVE | 0.75x |
| 2 | STANDARD_PLUS | 650-799 | APPROVE | 1.0x |
| 3 | STANDARD | 500-649 | REFER | 1.3x |
| 4 | SUBSTANDARD | 350-499 | REFER | 1.75x |
| 5 | DECLINE | 0-349 | DECLINE | 2.5x |

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
| `pending_claims` | Any pending or threatened malpractice claims? | Answer = True | REFER | Override to Tier 4 |
| `disciplinary_pending` | Any pending disciplinary proceedings against any p... | Answer = True | REFER | Override to Tier 4 |
| `coverage_declined` | Has any PI coverage been declined or non-renewed i... | Answer = True | REFER | Override to Tier 5 |
| `practice_area_change` | Any significant change in practice areas in past 2... | Answer = True | FLAG | Significant practice area change |
| `merger_activity` | Any merger, acquisition, or spin-off in past 2 yea... | Answer = True | FLAG | Recent merger/acquisition activity |
| `major_client_loss` | Loss of client representing >25% of revenue in pas... | Answer = True | FLAG | Major client loss (>25% revenue) |

**Action Types:**
- **FLAG:** Adds note to underwriter; no pricing impact
- **MODIFIER:** Applies premium multiplier
- **REFER:** Forces underwriter review regardless of score

### Limit & Deductible Configuration

**Type:** `DECOUPLED`

**Mode:** Tower Pricing (Independent Selection)

Clients independently select from valid limits and deductibles. 
Pricing scales via ILF curves and deductible factors.

**Available Limits:**

- $250,000
- $500,000
- $1,000,000
- $2,000,000
- $3,000,000
- $5,000,000
- $10,000,000

**Available Deductibles:**

- $10,000
- $25,000
- $50,000
- $100,000
- $250,000
- $500,000
- $1,000,000

### Pricing Structure

Pricing varies by product type:


#### Professional Liability

**Pricing Anchors (V5):**
- Base Limit Reference: $1,000,000
- Base Deductible Reference: $50,000

**Increased Limit Factors (ILF):**

| Limit | Factor | Premium Multiplier |
|-------|--------|-------------------|
| $250,000 | 0.50 | 0.50x base |
| $500,000 | 0.75 | 0.75x base |
| $1,000,000 (base) | 1.00 | 1.00x base |
| $2,000,000 | 1.65 | 1.65x base |
| $3,000,000 | 2.20 | 2.20x base |
| $5,000,000 | 3.00 | 3.00x base |
| $10,000,000 | 4.50 | 4.50x base |

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


#### Errors Omissions

**Pricing Anchors (V5):**
- Base Limit Reference: $1,000,000
- Base Deductible Reference: $50,000

**Increased Limit Factors (ILF):**

| Limit | Factor | Premium Multiplier |
|-------|--------|-------------------|
| $250,000 | 0.48 | 0.48x base |
| $500,000 | 0.72 | 0.72x base |
| $1,000,000 (base) | 1.00 | 1.00x base |
| $2,000,000 | 1.55 | 1.55x base |
| $3,000,000 | 2.00 | 2.00x base |
| $5,000,000 | 2.70 | 2.70x base |
| $10,000,000 | 4.00 | 4.00x base |

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


#### Malpractice

**Pricing Anchors (V5):**
- Base Limit Reference: $1,000,000
- Base Deductible Reference: $50,000

**Increased Limit Factors (ILF):**

| Limit | Factor | Premium Multiplier |
|-------|--------|-------------------|
| $250,000 | 0.55 | 0.55x base |
| $500,000 | 0.80 | 0.80x base |
| $1,000,000 (base) | 1.00 | 1.00x base |
| $2,000,000 | 1.75 | 1.75x base |
| $3,000,000 | 2.40 | 2.40x base |
| $5,000,000 | 3.30 | 3.30x base |
| $10,000,000 | 5.20 | 5.20x base |

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

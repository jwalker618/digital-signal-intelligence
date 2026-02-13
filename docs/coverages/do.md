# Do Coverage Configuration

**Coverage ID:** `directors_officers`
**Generated:** 2026-02-13 13:34
**Schema Version:** v2.2

This document describes the configuration, decision logic, and pricing structure
for the Do coverage vertical in the DSI platform.

## Table of Contents

1. [Configuration Overview](#configuration-overview)
2. [Signal Groups](#signal-groups)
3. [Scoring Logic](#scoring-logic)
4. [Pricing Structure](#pricing-structure)
5. [Direct Queries](#direct-queries)
6. [Decision Flow](#decision-flow)


---


## Configuration: Do General

### Metadata

- **Name:** DSI Directors & Officers Technical Pricing Model
- **Version:** 2.2.0
- **Description:** D&O liability coverage based on observable governance, financial, and litigation signals
- **Product Types:** `side_a`, `side_b`, `side_c`, `side_a_dic`, `employment_practices`, `fiduciary`
- **Markets:** US, UK, EU, APAC
- **Minimum Premium:** $10,000
- **Currency:** USD

#### Multiplexer Configuration (V4)

- **Model Specificity:** 1 (General)
- **Routing Constraints:** None (accepts all)

### Signal Registry

**Total Signals:** 48


#### Group: `company_type`

| Signal ID | Type | Weight | Direction | Proxy Tier |
|-----------|------|--------|-----------|------------|
| `company_type` | Categorical | N/A | modifier | INFERRED_PROXY |

#### Group: `corporate_footprint`

| Signal ID | Type | Weight | Direction | Proxy Tier |
|-----------|------|--------|-----------|------------|
| `investor_relations` | Scoring | 25.00% | positive | INFERRED_PROXY |
| `governance_page` | Scoring | 20.00% | positive | DIRECT_OBSERVABLE |
| `esg_reporting` | Scoring | 15.00% | positive | DIRECT_OBSERVABLE |
| `press_release` | Scoring | 15.00% | positive | INFERRED_PROXY |
| `leadership_visibility` | Scoring | 15.00% | positive | INFERRED_PROXY |
| `hiring_signals` | Scoring | 10.00% | positive | INFERRED_PROXY |

#### Group: `executive`

| Signal ID | Type | Weight | Direction | Proxy Tier |
|-----------|------|--------|-----------|------------|
| `executive_stability` | Scoring | 25.00% | positive | INFERRED_PROXY |
| `cfo_quality` | Scoring | 20.00% | positive | INFERRED_PROXY |
| `insider_trading` | Scoring | 25.00% | negative | DIRECT_OBSERVABLE |
| `executive_background` | Scoring | 15.00% | positive | INFERRED_PROXY |
| `trading_plan` | Scoring | 15.00% | positive | DIRECT_OBSERVABLE |

#### Group: `financial`

| Signal ID | Type | Weight | Direction | Proxy Tier |
|-----------|------|--------|-----------|------------|
| `audit_opinion` | Scoring | 20.00% | positive | DIRECT_OBSERVABLE |
| `internal_controls` | Scoring | 20.00% | positive | DIRECT_OBSERVABLE |
| `restatement` | Scoring | 20.00% | positive | DIRECT_OBSERVABLE |
| `filing_timeliness` | Scoring | 10.00% | positive | DIRECT_OBSERVABLE |
| `revenue_recognition` | Scoring | 10.00% | positive | INFERRED_PROXY |
| `debt_covenant` | Scoring | 5.00% | positive | INFERRED_PROXY |
| `stock_volatility` | Scoring | 10.00% | negative | DIRECT_OBSERVABLE |
| `short_interest` | Scoring | 5.00% | negative | DIRECT_OBSERVABLE |

#### Group: `governance`

| Signal ID | Type | Weight | Direction | Proxy Tier |
|-----------|------|--------|-----------|------------|
| `board_independence` | Scoring | 20.00% | positive | DIRECT_OBSERVABLE |
| `board_diversity` | Scoring | 10.00% | positive | DIRECT_OBSERVABLE |
| `ceo_chair_separation` | Scoring | 15.00% | positive | DIRECT_OBSERVABLE |
| `committee_structure` | Scoring | 15.00% | positive | DIRECT_OBSERVABLE |
| `board_refreshment` | Scoring | 10.00% | positive | DIRECT_OBSERVABLE |
| `related_party` | Scoring | 10.00% | negative | DIRECT_OBSERVABLE |
| `compensation_structure` | Scoring | 10.00% | positive | DIRECT_OBSERVABLE |
| `shareholder_rights` | Scoring | 10.00% | positive | DIRECT_OBSERVABLE |

#### Group: `industry`

| Signal ID | Type | Weight | Direction | Proxy Tier |
|-----------|------|--------|-----------|------------|
| `industry` | Categorical | N/A | modifier | INFERRED_PROXY |

#### Group: `litigation`

| Signal ID | Type | Weight | Direction | Proxy Tier |
|-----------|------|--------|-----------|------------|
| `securities_litigation` | Scoring | 35.00% | positive | DIRECT_OBSERVABLE |
| `derivative_litigation` | Scoring | 15.00% | positive | DIRECT_OBSERVABLE |
| `sec_enforcement` | Scoring | 20.00% | positive | DIRECT_OBSERVABLE |
| `regulatory_action` | Scoring | 15.00% | positive | DIRECT_OBSERVABLE |
| `pending_litigation` | Scoring | 10.00% | positive | INFERRED_PROXY |
| `whistleblower` | Scoring | 5.00% | positive | INFERRED_PROXY |

#### Group: `network_authority`

| Signal ID | Type | Weight | Direction | Proxy Tier |
|-----------|------|--------|-----------|------------|
| `auditor_quality` | Scoring | 20.00% | positive | DIRECT_OBSERVABLE |
| `legal_counsel` | Scoring | 15.00% | positive | INFERRED_PROXY |
| `banking_relationship` | Scoring | 15.00% | positive | INFERRED_PROXY |
| `investor_quality` | Scoring | 15.00% | positive | DIRECT_OBSERVABLE |
| `board_network` | Scoring | 15.00% | positive | INFERRED_PROXY |
| `index_inclusion` | Scoring | 5.00% | positive | DIRECT_OBSERVABLE |
| `analyst_coverage` | Scoring | 10.00% | positive | DIRECT_OBSERVABLE |
| `industry_association` | Scoring | 5.00% | positive | DIRECT_OBSERVABLE |

#### Group: `stock_exchange`

| Signal ID | Type | Weight | Direction | Proxy Tier |
|-----------|------|--------|-----------|------------|
| `stock_exchange` | Categorical | N/A | modifier | INFERRED_PROXY |

#### Group: `structured_data`

| Signal ID | Type | Weight | Direction | Proxy Tier |
|-----------|------|--------|-----------|------------|
| `credit_rating` | Scoring | 30.00% | positive | DIRECT_OBSERVABLE |
| `esg_rating` | Scoring | 20.00% | positive | DIRECT_OBSERVABLE |
| `governance_rating` | Scoring | 30.00% | positive | DIRECT_OBSERVABLE |
| `iss_governance` | Scoring | 20.00% | positive | DIRECT_OBSERVABLE |

### Signal Groups

#### Categorical Groups

These groups apply modifiers based on classification:

| Group ID | Label | Impact | Default |
|----------|-------|--------|---------|
| `company_type` | Company Type | MODIFIER | OTHER |
| `industry` | Industry | MODIFIER | OTHER |
| `stock_exchange` | Stock Exchange | MODIFIER | OTHER |

#### Three-Layer Assessment Groups

These groups contribute to Risk, Loss, and Exposure scoring:

| Group ID | Risk Weight | Loss Weight | Exposure Weight |
|----------|-------------|-------------|-----------------|
| `network_authority` | 10% | 0% | 0% |
| `governance` | 25% | 0% | 0% |
| `financial` | 20% | 0% | 0% |
| `litigation` | 25% | 0% | 0% |
| `executive` | 10% | 0% | 0% |
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
| `pending_claims` | Are there any pending securities class actions or ... | Answer = True | REFER | Override to Tier 4 |
| `regulatory_investigation` | Is the company or any director/officer under regul... | Answer = True | REFER | Override to Tier 3 |
| `planned_transaction` | Is there a planned M&A, IPO, SPAC merger, or mater... | Answer = True | FLAG | Planned transaction - tail coverage needed |
| `covenant_compliance` | Is the company in compliance with all debt covenan... | Answer = False | FLAG | Covenant non-compliance disclosed |
| `executive_dispute` | Are there any disputes with current or former exec... | Answer = True | REFER | Override to Tier 3 |

**Action Types:**
- **FLAG:** Adds note to underwriter; no pricing impact
- **MODIFIER:** Applies premium multiplier
- **REFER:** Forces underwriter review regardless of score

### Pricing Structure

Pricing varies by product type:


#### Side A

**Pricing Anchors (V5):**
- Base Limit Reference: $1,000,000
- Base Deductible Reference: $50,000

**Increased Limit Factors (ILF):**

| Limit | Factor | Premium Multiplier |
|-------|--------|-------------------|
| $1,000,000 (base) | 1.00 | 1.00x base |
| $2,000,000 | 1.90 | 1.90x base |
| $5,000,000 | 3.80 | 3.80x base |
| $10,000,000 | 6.20 | 6.20x base |
| $25,000,000 | 12.00 | 12.00x base |
| $50,000,000 | 19.00 | 19.00x base |
| $100,000,000 | 30.00 | 30.00x base |

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


#### Side B

**Pricing Anchors (V5):**
- Base Limit Reference: $1,000,000
- Base Deductible Reference: $50,000

**Increased Limit Factors (ILF):**

| Limit | Factor | Premium Multiplier |
|-------|--------|-------------------|
| $1,000,000 (base) | 1.00 | 1.00x base |
| $2,000,000 | 1.80 | 1.80x base |
| $5,000,000 | 3.50 | 3.50x base |
| $10,000,000 | 5.60 | 5.60x base |
| $25,000,000 | 10.50 | 10.50x base |
| $50,000,000 | 16.50 | 16.50x base |
| $100,000,000 | 26.00 | 26.00x base |

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


#### Side C

**Pricing Anchors (V5):**
- Base Limit Reference: $1,000,000
- Base Deductible Reference: $50,000

**Increased Limit Factors (ILF):**

| Limit | Factor | Premium Multiplier |
|-------|--------|-------------------|
| $1,000,000 (base) | 1.00 | 1.00x base |
| $2,000,000 | 1.95 | 1.95x base |
| $5,000,000 | 4.00 | 4.00x base |
| $10,000,000 | 6.80 | 6.80x base |
| $25,000,000 | 13.50 | 13.50x base |
| $50,000,000 | 22.00 | 22.00x base |
| $100,000,000 | 35.00 | 35.00x base |

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


#### Side A Dic

**Pricing Anchors (V5):**
- Base Limit Reference: $1,000,000
- Base Deductible Reference: $50,000

**Increased Limit Factors (ILF):**

| Limit | Factor | Premium Multiplier |
|-------|--------|-------------------|
| $1,000,000 (base) | 1.00 | 1.00x base |
| $2,000,000 | 2.00 | 2.00x base |
| $5,000,000 | 4.20 | 4.20x base |
| $10,000,000 | 7.20 | 7.20x base |
| $25,000,000 | 14.50 | 14.50x base |
| $50,000,000 | 24.00 | 24.00x base |
| $100,000,000 | 38.00 | 38.00x base |

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


#### Fiduciary

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


## Configuration: Do Sme

### Metadata

- **Name:** DSI D&O SME Model
- **Version:** 2.2.0
- **Description:** D&O coverage for private companies with revenue under $100M
- **Product Types:** `side_a`, `side_b`, `employment_practices`, `fiduciary`
- **Markets:** US, UK, EU, APAC
- **Minimum Premium:** $5,000
- **Currency:** USD

#### Multiplexer Configuration (V4)

- **Model Specificity:** 2 (Segment)
- **Routing Constraints:**
  - `revenue <= 100000000` (required)
  - `limit <= 5000000` (required)

### Signal Registry

**Total Signals:** 15


#### Group: `company_type`

| Signal ID | Type | Weight | Direction | Proxy Tier |
|-----------|------|--------|-----------|------------|
| `company_type` | Categorical | N/A | modifier | INFERRED_PROXY |

#### Group: `financial`

| Signal ID | Type | Weight | Direction | Proxy Tier |
|-----------|------|--------|-----------|------------|
| `financial_health` | Scoring | 35.00% | positive | INFERRED_PROXY |
| `growth_trajectory` | Scoring | 25.00% | negative | INFERRED_PROXY |
| `debt_position` | Scoring | 20.00% | positive | INFERRED_PROXY |
| `auditor_quality` | Scoring | 20.00% | positive | INFERRED_PROXY |

#### Group: `footprint`

| Signal ID | Type | Weight | Direction | Proxy Tier |
|-----------|------|--------|-----------|------------|
| `corporate_footprint` | Scoring | 50.00% | positive | INFERRED_PROXY |
| `employee_count` | Scoring | 50.00% | positive | INFERRED_PROXY |

#### Group: `governance`

| Signal ID | Type | Weight | Direction | Proxy Tier |
|-----------|------|--------|-----------|------------|
| `board_composition` | Scoring | 30.00% | positive | INFERRED_PROXY |
| `investor_quality` | Scoring | 25.00% | positive | INFERRED_PROXY |
| `management_stability` | Scoring | 25.00% | positive | INFERRED_PROXY |
| `related_party` | Scoring | 20.00% | negative | INFERRED_PROXY |

#### Group: `industry`

| Signal ID | Type | Weight | Direction | Proxy Tier |
|-----------|------|--------|-----------|------------|
| `industry` | Categorical | N/A | modifier | INFERRED_PROXY |

#### Group: `litigation`

| Signal ID | Type | Weight | Direction | Proxy Tier |
|-----------|------|--------|-----------|------------|
| `litigation_history` | Scoring | 40.00% | positive | INFERRED_PROXY |
| `employment_claims` | Scoring | 30.00% | positive | INFERRED_PROXY |
| `regulatory_history` | Scoring | 30.00% | positive | INFERRED_PROXY |

### Signal Groups

#### Categorical Groups

These groups apply modifiers based on classification:

| Group ID | Label | Impact | Default |
|----------|-------|--------|---------|
| `company_type` | Company Type | MODIFIER | OTHER |
| `industry` | Industry | MODIFIER | OTHER |

#### Three-Layer Assessment Groups

These groups contribute to Risk, Loss, and Exposure scoring:

| Group ID | Risk Weight | Loss Weight | Exposure Weight |
|----------|-------------|-------------|-----------------|
| `governance` | 30% | 0% | 0% |
| `financial` | 25% | 0% | 0% |
| `litigation` | 30% | 0% | 0% |
| `footprint` | 15% | 0% | 0% |

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
| `pending_claims` | Are there any pending claims against directors or ... | Answer = True | REFER | Override to Tier 4 |
| `regulatory_investigation` | Is the company or any director/officer under regul... | Answer = True | REFER | Override to Tier 3 |
| `planned_transaction` | Is there a planned M&A, sale, or material transact... | Answer = True | FLAG | Planned transaction - tail coverage needed |
| `executive_dispute` | Are there any disputes with current or former exec... | Answer = True | REFER | Override to Tier 3 |

**Action Types:**
- **FLAG:** Adds note to underwriter; no pricing impact
- **MODIFIER:** Applies premium multiplier
- **REFER:** Forces underwriter review regardless of score

### Pricing Structure

Pricing varies by product type:


#### Side A

**Pricing Anchors (V5):**
- Base Limit Reference: $1,000,000
- Base Deductible Reference: $50,000

**Increased Limit Factors (ILF):**

| Limit | Factor | Premium Multiplier |
|-------|--------|-------------------|
| $1,000,000 (base) | 1.00 | 1.00x base |
| $2,000,000 | 1.80 | 1.80x base |
| $5,000,000 | 3.50 | 3.50x base |

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


#### Side B

**Pricing Anchors (V5):**
- Base Limit Reference: $1,000,000
- Base Deductible Reference: $50,000

**Increased Limit Factors (ILF):**

| Limit | Factor | Premium Multiplier |
|-------|--------|-------------------|
| $1,000,000 (base) | 1.00 | 1.00x base |
| $2,000,000 | 1.70 | 1.70x base |
| $5,000,000 | 3.20 | 3.20x base |

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
| $2,000,000 | 1.55 | 1.55x base |
| $5,000,000 | 2.60 | 2.60x base |

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


#### Fiduciary

**Pricing Anchors (V5):**
- Base Limit Reference: $1,000,000
- Base Deductible Reference: $50,000

**Increased Limit Factors (ILF):**

| Limit | Factor | Premium Multiplier |
|-------|--------|-------------------|
| $1,000,000 (base) | 1.00 | 1.00x base |
| $2,000,000 | 1.60 | 1.60x base |
| $5,000,000 | 2.80 | 2.80x base |

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
| 1 | $1,000,000 | $10,000 |
| 2 | $2,000,000 | $25,000 |
| 3 | $5,000,000 | $50,000 |


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

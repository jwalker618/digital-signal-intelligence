# DSI Logic Document: `DO`
*Generated: 2026-05-14*

## DSI Foundational Principles Adherence
This configuration is validated against the DSI Whitepaper & Vision Paper:
- **Objective Observation:** Signals derived from verifiable digital footprints, avoiding subjective interpretation.
- **Three-Layer Engine:** Modifiers explicitly target Risk, Loss, and Exposure dimensions.
- **Phase 5 Anchoring:** Polymorphic pricing limits scale from mathematically absolute anchor points.

## The Three-Layer Assessment Engine
Every DSI model scores a risk across three independent pillars before any premium is calculated. Each pillar answers a distinct underwriting question and enters the pricing formula at a different point:

- **Risk** — *How likely is this account to behave badly?* Signal evidence is aggregated into a quality score that maps to an underwriting action (approve / refer / decline) and selects the base rate applied to the exposure basis.
- **Loss** — *If a loss occurs, how often and how severe?* Scored separately into frequency and severity modifiers, letting the model distinguish attritional-loss accounts from low-frequency / high-severity ones.
- **Exposure** — *How much value is at stake?* Scales premium to the size of the insured object, independent of risk quality.

Within each pillar, signals are organised into groups (e.g. Construction Quality, Occupancy Risk). The weight tables show how much each group contributes to each pillar; the signal detail tables show how each individual signal informs them. Critically, a single signal can carry very different weight across the three pillars — highly predictive of loss severity, say, yet barely moving the exposure score.

---

## Model: `do_general`
*D&O liability coverage based on observable governance, financial, and litigation signals*

### Routing Protocol (Multiplexer)
- `revenue > 50000000`

### Three-Layer Weight Distribution
> *DSI requires that weights for Risk, Loss, and Exposure each sum to 1.0 across all signal groups.*

**Validation:** PASS

| Group | Risk | Loss | Exposure |
|-------|------|------|----------|
| Network Authority | 0.10 | 0.05 | 0.05 |
| Corporate Governance | 0.40 | 0.38 | 0.45 |
| Financial Integrity | 0.25 | 0.32 | 0.45 |
| Litigation Profile | 0.25 | 0.25 | 0.05 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

**Group Definitions:**
- **Network Authority:** Quality of professional relationships and institutional credibility
- **Corporate Governance:** Board composition, structure, and shareholder rights
- **Financial Integrity:** Audit quality, internal controls, financial reporting
- **Litigation Profile:** Securities litigation, regulatory actions, enforcement history

*Reading the table: a group's three weights are independent. The same group can be a dominant driver of one pillar and a minor input to another — e.g. a group may carry most of the Exposure weight while contributing little to Risk.*

### Signal Architecture Rationale
This configuration contains **48 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `DIRECT_OBSERVABLE` (31 signals): Highest confidence
- `INFERRED_PROXY` (17 signals): Medium confidence

**Signal Count by Group:**
- `corporate_footprint`: 19 signals
- `structured_data`: 12 signals
- `network_authority`: 8 signals
- `public_record`: 6 signals
- `company_type`: 1 signals
- `industry`: 1 signals
- `stock_exchange`: 1 signals

**Selection Rationale:**
- 65% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Detail by Group
> *Each signal is an objectively observable data point. The weights show how strongly that signal informs each assessment pillar; correlation direction indicates whether a higher observed value increases (+) or decreases (-) the assessed exposure.*

#### Network Authority
*Quality of professional relationships and institutional credibility*

| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `auditor_quality` | DIRECT_OBSERVABLE | 0.20 | 0.15 / 0.15 | 0.00 | + |
| `legal_counsel` | INFERRED_PROXY | 0.15 | 0.00 / 0.10 | 0.00 | + |
| `banking_relationship` | INFERRED_PROXY | 0.15 | 0.00 / 0.10 | 0.00 | + |
| `investor_quality` | DIRECT_OBSERVABLE | 0.15 | 0.10 / 0.00 | 0.10 | + |
| `board_network` | INFERRED_PROXY | 0.15 | 0.10 / 0.00 | 0.00 | + |
| `index_inclusion` | DIRECT_OBSERVABLE | 0.05 | 0.00 / 0.00 | 0.15 | + |
| `analyst_coverage` | DIRECT_OBSERVABLE | 0.10 | 0.00 / 0.00 | 0.10 | + |
| `industry_association` | DIRECT_OBSERVABLE | 0.05 | 0.00 / 0.00 | 0.00 | + |

#### Corporate Governance
*Board composition, structure, and shareholder rights*

| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `board_independence` | DIRECT_OBSERVABLE | 0.20 | 0.15 / 0.10 | 0.00 | + |
| `board_diversity` | DIRECT_OBSERVABLE | 0.10 | 0.10 / 0.00 | 0.00 | + |
| `ceo_chair_separation` | DIRECT_OBSERVABLE | 0.15 | 0.00 / 0.00 | 0.00 | + |
| `committee_structure` | DIRECT_OBSERVABLE | 0.15 | 0.10 / 0.00 | 0.00 | + |
| `board_refreshment` | DIRECT_OBSERVABLE | 0.10 | 0.00 / 0.00 | 0.00 | + |
| `related_party` | DIRECT_OBSERVABLE | 0.10 | 0.15 / 0.10 | 0.00 | - |
| `compensation_structure` | DIRECT_OBSERVABLE | 0.10 | 0.00 / 0.00 | 0.00 | + |
| `shareholder_rights` | DIRECT_OBSERVABLE | 0.10 | 0.10 / 0.00 | 0.00 | + |
| `executive_stability` | INFERRED_PROXY | 0.25 | 0.15 / 0.00 | 0.00 | + |
| `cfo_quality` | INFERRED_PROXY | 0.20 | 0.15 / 0.10 | 0.00 | + |
| `insider_trading` | DIRECT_OBSERVABLE | 0.25 | 0.20 / 0.15 | 0.00 | - |
| `executive_background` | INFERRED_PROXY | 0.15 | 0.15 / 0.10 | 0.00 | + |
| `trading_plan` | DIRECT_OBSERVABLE | 0.15 | 0.00 / 0.00 | 0.00 | + |
| `investor_relations` | INFERRED_PROXY | 0.25 | 0.00 / 0.00 | 0.15 | + |
| `governance_page` | DIRECT_OBSERVABLE | 0.20 | 0.00 / 0.00 | 0.00 | + |
| `esg_reporting` | DIRECT_OBSERVABLE | 0.15 | 0.00 / 0.00 | 0.00 | + |
| `press_release` | INFERRED_PROXY | 0.15 | 0.00 / 0.00 | 0.10 | + |
| `leadership_visibility` | INFERRED_PROXY | 0.15 | 0.00 / 0.00 | 0.00 | + |
| `hiring_signals` | INFERRED_PROXY | 0.10 | 0.00 / 0.00 | 0.25 | + |

#### Financial Integrity
*Audit quality, internal controls, financial reporting*

| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `audit_opinion` | DIRECT_OBSERVABLE | 0.20 | 0.20 / 0.25 | 0.00 | + |
| `internal_controls` | DIRECT_OBSERVABLE | 0.20 | 0.20 / 0.15 | 0.00 | + |
| `restatement` | DIRECT_OBSERVABLE | 0.20 | 0.25 / 0.30 | 0.00 | + |
| `filing_timeliness` | DIRECT_OBSERVABLE | 0.10 | 0.10 / 0.00 | 0.00 | + |
| `revenue_recognition` | INFERRED_PROXY | 0.10 | 0.15 / 0.10 | 0.00 | + |
| `debt_covenant` | INFERRED_PROXY | 0.05 | 0.00 / 0.00 | 0.00 | + |
| `stock_volatility` | DIRECT_OBSERVABLE | 0.10 | 0.15 / 0.10 | 0.00 | - |
| `short_interest` | DIRECT_OBSERVABLE | 0.05 | 0.10 / 0.00 | 0.10 | - |
| `credit_rating` | DIRECT_OBSERVABLE | 0.30 | 0.00 / 0.25 | 0.00 | + |
| `esg_rating` | DIRECT_OBSERVABLE | 0.20 | 0.00 / 0.00 | 0.00 | + |
| `governance_rating` | DIRECT_OBSERVABLE | 0.30 | 0.00 / 0.00 | 0.00 | + |
| `iss_governance` | DIRECT_OBSERVABLE | 0.20 | 0.00 / 0.00 | 0.00 | + |

#### Litigation Profile
*Securities litigation, regulatory actions, enforcement history*

| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `securities_litigation` | DIRECT_OBSERVABLE | 0.35 | 0.35 / 0.40 | 0.35 | + |
| `derivative_litigation` | DIRECT_OBSERVABLE | 0.15 | 0.15 / 0.15 | 0.00 | + |
| `sec_enforcement` | DIRECT_OBSERVABLE | 0.20 | 0.25 / 0.30 | 0.00 | + |
| `regulatory_action` | DIRECT_OBSERVABLE | 0.15 | 0.15 / 0.10 | 0.00 | + |
| `pending_litigation` | INFERRED_PROXY | 0.10 | 0.20 / 0.15 | 0.00 | + |
| `whistleblower` | INFERRED_PROXY | 0.05 | 0.10 / 0.00 | 0.00 | + |

#### company_type
**Categorical signal `company_type`** — proxy tier: `INFERRED_PROXY`, source: `metadata.company_type`

| Category | Label | Applied Factor |
|----------|-------|----------------|
| `PUBLIC_LARGE_CAP` | Public Large Cap | 0.12 |
| `PUBLIC_MID_CAP` | Public Mid Cap | 0.4 |
| `PUBLIC_SMALL_CAP` | Public Small Cap | 1.0 |
| `PUBLIC_MICRO_CAP` | Public Micro Cap | 1.5 |
| `PRE_IPO` | Pre-IPO | 1.8 |
| `SPAC` | SPAC | 2.5 |
| `PRIVATE_BACKED` | Private VC/PE Backed | 0.6 |
| `PRIVATE_OTHER` | Private Other | 0.5 |
| `NONPROFIT` | Nonprofit | 0.4 |
| `OTHER` | UNKNOWN | 1.0 |

#### industry
**Categorical signal `industry`** — proxy tier: `INFERRED_PROXY`, source: `metadata.industry`

| Category | Label | Applied Factor |
|----------|-------|----------------|
| `CRYPTO_DIGITAL` | Crypto/Digital Assets | 2.5 |
| `CANNABIS` | Cannabis | 2.0 |
| `HEALTHCARE_PHARMA` | Healthcare/Pharma | 1.6 |
| `FINANCIAL_SERVICES` | Financial Services | 1.4 |
| `TECHNOLOGY` | Technology | 1.25 |
| `ENERGY` | Energy | 1.15 |
| `REAL_ESTATE` | Real Estate | 1.1 |
| `RETAIL_CONSUMER` | Retail/Consumer | 1.0 |
| `MANUFACTURING` | Manufacturing | 0.9 |
| `OTHER` | Other | 1.0 |

#### stock_exchange
**Categorical signal `stock_exchange`** — proxy tier: `INFERRED_PROXY`, source: `metadata.stock_exchange`

| Category | Label | Applied Factor |
|----------|-------|----------------|
| `NYSE` | NYSE | 1.0 |
| `NASDAQ` | NASDAQ | 1.0 |
| `NYSE_AMERICAN` | NYSE American | 1.1 |
| `OTC` | OTC Markets | 1.3 |
| `FOREIGN` | Foreign Exchange | 1.15 |
| `NONE` | Not Listed | 0.8 |
| `OTHER` | UNKNOWN | 1.0 |

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 | Corporate Governance | 1.23 | 0.40 | 0.38 | 0.45 |
| 2 | Financial Integrity | 1.02 | 0.25 | 0.32 | 0.45 |
| 3 | Litigation Profile | 0.55 | 0.25 | 0.25 | 0.05 |
| 4 | Network Authority | 0.20 | 0.10 | 0.05 | 0.05 |

**Primary Assessment Driver:** `Corporate Governance` with combined weight of 1.23
**Secondary Driver:** `Financial Integrity` with combined weight of 1.02

### Three-Layer Pricing Translation
> *How each pillar's tier score becomes a concrete underwriting action or pricing modifier. This is the bridge between signal observation and premium.*

**Risk -> Underwriting Action & Base Rate**

| Tier | Score Band | Action | Rate / Method |
|------|-----------|--------|---------------|
| PREFERRED | 800-1000 | APPROVE | 0.004% (MULTIPLIER) |
| STANDARD_PLUS | 650-799 | APPROVE | 0.006% (MULTIPLIER) |
| STANDARD | 500-649 | REFER | 0.008% (MULTIPLIER) |
| SUBSTANDARD | 350-499 | REFER | 0.015% (MULTIPLIER) |
| DECLINE | 0-349 | DECLINE | 0.03% (MULTIPLIER) |

**Loss -> Frequency & Severity Modifiers**

| Tier | Score Band | Frequency Modifier | Severity Modifier |
|------|-----------|--------------------|-------------------|
| VERY_LOW | 80-100 | 0.7 | 0.8 |
| LOW | 60-79 | 0.85 | 0.9 |
| MODERATE | 40-59 | 1.0 | 1.0 |
| ELEVATED | 20-39 | 1.15 | 1.15 |
| HIGH | 0-19 | 1.35 | 1.4 |

*Loss modifier is bounded: floor 0.55, cap 1.6.*

**Exposure (size) -> Scale Modifier**

| Band | Score Band | Modifier | Implied Value Range |
|------|-----------|----------|---------------------|
| MICRO | 0-20 | 0.5 | $0 - $1,000,000 |
| SMALL | 21-40 | 0.75 | $1,000,000 - $10,000,000 |
| MEDIUM | 41-60 | 1.0 | $10,000,000 - $50,000,000 |
| LARGE | 61-80 | 1.5 | $50,000,000 - $250,000,000 |
| VERY_LARGE | 81-100 | 1.3 | $250,000,000 - $1,000,000,000 |

**Exposure (complexity) -> Scale Modifier**

| Band | Score Band | Modifier | Implied Value Range |
|------|-----------|----------|---------------------|
| SIMPLE | 0-20 | 0.85 | n/a |
| MODERATE | 21-40 | 0.95 | n/a |
| COMPLEX | 41-60 | 1.1 | n/a |
| HIGHLY_COMPLEX | 61-80 | 1.3 | n/a |
| EXTREMELY_COMPLEX | 81-100 | 1.6 | n/a |

### Theoretical Premium Calculation (Tier 3 Standard)
> *Per the DSI Premium Calculation Methodology v2.0, the core formula is:*
> *P_final = (Base × Rate) × ILF_relativity × Deductible_Factor × Modifiers*

**1. The Pricing Anchor:** The Base Rate of `0.008%` on `revenue` purchases exactly a `$1,000,000` Limit with a `$50,000` Deductible.
**2. Theoretical Execution:**
  - Assume `revenue` = $10,000,000
  - Base Premium = $10,000,000 × 8e-05 = **$800**
  - If the client requests the Anchor Limit/Deductible, the factors are 1.00, resulting in a technical premium of **$800**.

---

## Model: `do_sme`
*D&O coverage for private companies with revenue under $100M*

### Routing Protocol (Multiplexer)
- `revenue <= 50000000`

### Three-Layer Weight Distribution
> *DSI requires that weights for Risk, Loss, and Exposure each sum to 1.0 across all signal groups.*

**Validation:** PASS

| Group | Risk | Loss | Exposure |
|-------|------|------|----------|
| Governance | 0.45 | 0.40 | 0.55 |
| Financial Health | 0.25 | 0.35 | 0.25 |
| Litigation Profile | 0.30 | 0.25 | 0.20 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

**Group Definitions:**
- **Governance:** Board composition and management quality
- **Financial Health:** Financial stability and audit quality
- **Litigation Profile:** Claims and regulatory history

*Reading the table: a group's three weights are independent. The same group can be a dominant driver of one pillar and a minor input to another — e.g. a group may carry most of the Exposure weight while contributing little to Risk.*

### Signal Architecture Rationale
This configuration contains **15 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `INFERRED_PROXY` (15 signals): Medium confidence

**Signal Count by Group:**
- `corporate_footprint`: 6 signals
- `structured_data`: 4 signals
- `public_record`: 3 signals
- `company_type`: 1 signals
- `industry`: 1 signals

**Selection Rationale:**
- 0% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Detail by Group
> *Each signal is an objectively observable data point. The weights show how strongly that signal informs each assessment pillar; correlation direction indicates whether a higher observed value increases (+) or decreases (-) the assessed exposure.*

#### Governance
*Board composition and management quality*

| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `board_composition` | INFERRED_PROXY | 0.30 | 0.20 / 0.00 | 0.00 | + |
| `investor_quality` | INFERRED_PROXY | 0.25 | 0.15 / 0.00 | 0.00 | + |
| `management_stability` | INFERRED_PROXY | 0.25 | 0.20 / 0.00 | 0.00 | + |
| `related_party` | INFERRED_PROXY | 0.20 | 0.15 / 0.00 | 0.00 | - |
| `corporate_footprint` | INFERRED_PROXY | 0.50 | 0.00 / 0.00 | 0.25 | + |
| `employee_count` | INFERRED_PROXY | 0.50 | 0.00 / 0.00 | 0.50 | + |

#### Financial Health
*Financial stability and audit quality*

| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `financial_health` | INFERRED_PROXY | 0.35 | 0.00 / 0.30 | 0.00 | + |
| `growth_trajectory` | INFERRED_PROXY | 0.25 | 0.00 / 0.00 | 0.20 | - |
| `debt_position` | INFERRED_PROXY | 0.20 | 0.00 / 0.15 | 0.00 | + |
| `auditor_quality` | INFERRED_PROXY | 0.20 | 0.15 / 0.00 | 0.00 | + |

#### Litigation Profile
*Claims and regulatory history*

| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `litigation_history` | INFERRED_PROXY | 0.40 | 0.35 / 0.30 | 0.00 | + |
| `employment_claims` | INFERRED_PROXY | 0.30 | 0.30 / 0.00 | 0.00 | + |
| `regulatory_history` | INFERRED_PROXY | 0.30 | 0.20 / 0.00 | 0.00 | + |

#### company_type
**Categorical signal `company_type`** — proxy tier: `INFERRED_PROXY`, source: `metadata.company_type`

| Category | Label | Applied Factor |
|----------|-------|----------------|
| `PRIVATE_BACKED` | Private VC/PE Backed | 0.7 |
| `PRIVATE_OTHER` | Private Other | 0.55 |
| `NONPROFIT` | Nonprofit | 0.45 |
| `OTHER` | UNKNOWN | 1.0 |

#### industry
**Categorical signal `industry`** — proxy tier: `INFERRED_PROXY`, source: `metadata.industry`

| Category | Label | Applied Factor |
|----------|-------|----------------|
| `HEALTHCARE_PHARMA` | Healthcare/Pharma | 1.4 |
| `FINANCIAL_SERVICES` | Financial Services | 1.25 |
| `TECHNOLOGY` | Technology | 1.15 |
| `RETAIL_CONSUMER` | Retail/Consumer | 1.0 |
| `MANUFACTURING` | Manufacturing | 0.9 |
| `OTHER` | Other | 1.0 |

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 | Governance | 1.40 | 0.45 | 0.40 | 0.55 |
| 2 | Financial Health | 0.85 | 0.25 | 0.35 | 0.25 |
| 3 | Litigation Profile | 0.75 | 0.30 | 0.25 | 0.20 |

**Primary Assessment Driver:** `Governance` with combined weight of 1.40
**Secondary Driver:** `Financial Health` with combined weight of 0.85

### Three-Layer Pricing Translation
> *How each pillar's tier score becomes a concrete underwriting action or pricing modifier. This is the bridge between signal observation and premium.*

**Risk -> Underwriting Action & Base Rate**

| Tier | Score Band | Action | Rate / Method |
|------|-----------|--------|---------------|
| PREFERRED | 800-1000 | APPROVE | PREMIUM_BASE |
| STANDARD_PLUS | 650-799 | APPROVE | PREMIUM_BASE |
| STANDARD | 500-649 | REFER | PREMIUM_BASE |
| SUBSTANDARD | 350-499 | REFER | PREMIUM_BASE |
| DECLINE | 0-349 | DECLINE | PREMIUM_BASE |

**Loss -> Frequency & Severity Modifiers**

| Tier | Score Band | Frequency Modifier | Severity Modifier |
|------|-----------|--------------------|-------------------|
| VERY_LOW | 80-100 | 0.7 | 0.8 |
| LOW | 60-79 | 0.85 | 0.9 |
| MODERATE | 40-59 | 1.0 | 1.0 |
| ELEVATED | 20-39 | 1.15 | 1.15 |
| HIGH | 0-19 | 1.3 | 1.35 |

*Loss modifier is bounded: floor 0.6, cap 1.5.*

**Exposure (size) -> Scale Modifier**

| Band | Score Band | Modifier | Implied Value Range |
|------|-----------|----------|---------------------|
| MICRO | 0-25 | 0.6 | $0 - $5,000,000 |
| SMALL | 26-50 | 0.8 | $5,000,000 - $25,000,000 |
| MEDIUM | 51-75 | 1.0 | $25,000,000 - $50,000,000 |
| MEDIUM_LARGE | 76-100 | 1.2 | $50,000,000 - $100,000,000 |

**Exposure (complexity) -> Scale Modifier**

| Band | Score Band | Modifier | Implied Value Range |
|------|-----------|----------|---------------------|
| SIMPLE | 0-33 | 0.9 | n/a |
| MODERATE | 34-66 | 1.0 | n/a |
| COMPLEX | 67-100 | 1.15 | n/a |

### Theoretical Premium Calculation (Tier 3 Standard)
> *Per the DSI Premium Calculation Methodology v2.0, the core formula is:*
> *P_final = (Base × Rate) × ILF_relativity × Deductible_Factor × Modifiers*

**1. The Pricing Anchor:** The Flat Premium of `$5,000` purchases exactly the `$1,000,000` Limit / `$10,000` Deductible Base Package.
**2. Theoretical Execution:**
  - Technical Premium = **$5,000**
  - *Scaling relies entirely on selecting a different Limit ID from the Bundled limit_configuration packages.*

---

## Model: `do_public`
*Publicly listed companies — SEC reporting, securities litigation, shareholder activism*

### Routing Protocol (Multiplexer)
- `company_segment == PUBLIC`
- `revenue >= 100000000`

### Three-Layer Weight Distribution
> *DSI requires that weights for Risk, Loss, and Exposure each sum to 1.0 across all signal groups.*

**Validation:** PASS

| Group | Risk | Loss | Exposure |
|-------|------|------|----------|
| Public Company Governance | 0.50 | 0.55 | 0.45 |
| Transaction & Event Risk | 0.20 | 0.20 | 0.20 |
| Corporate Footprint | 0.15 | 0.10 | 0.20 |
| Firm Stability | 0.15 | 0.15 | 0.15 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

**Group Definitions:**
- **Public Company Governance:** SEC filing quality, board independence, shareholder activism, restatement risk
- **Transaction & Event Risk:** M&A activity, IPO/SPAC risk, delisting exposure, PE sponsor dynamics

*Reading the table: a group's three weights are independent. The same group can be a dominant driver of one pillar and a minor input to another — e.g. a group may carry most of the Exposure weight while contributing little to Risk.*

### Signal Architecture Rationale
This configuration contains **24 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `DIRECT_OBSERVABLE` (16 signals): Highest confidence
- `INFERRED_PROXY` (7 signals): Medium confidence
- `COHORT_INFERENCE` (1 signals): Lowest confidence

**Signal Count by Group:**
- `public_record`: 19 signals
- `structured_data`: 5 signals

**Selection Rationale:**
- 67% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Detail by Group
> *Each signal is an objectively observable data point. The weights show how strongly that signal informs each assessment pillar; correlation direction indicates whether a higher observed value increases (+) or decreases (-) the assessed exposure.*

#### Public Company Governance
*SEC filing quality, board independence, shareholder activism, restatement risk*

| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `sec_filing_quality` | DIRECT_OBSERVABLE | 0.25 | 0.20 / 0.15 | 0.00 | + |
| `board_independence` | DIRECT_OBSERVABLE | 0.20 | 0.10 / 0.00 | 0.00 | + |
| `shareholder_activism` | INFERRED_PROXY | 0.15 | 0.15 / 0.15 | 0.00 | + |
| `securities_litigation_exposure` | COHORT_INFERENCE | 0.20 | 0.20 / 0.25 | 0.00 | + |
| `executive_compensation_structure` | DIRECT_OBSERVABLE | 0.10 | 0.10 / 0.00 | 0.10 | + |
| `shareholder_suit_history` | DIRECT_OBSERVABLE | 0.05 | 0.04 / 0.04 | 0.00 | + |
| `dodd_frank_whistleblower_telemetry` | INFERRED_PROXY | 0.03 | 0.03 / 0.00 | 0.00 | + |
| `iss_proxy_recommendation` | DIRECT_OBSERVABLE | 0.04 | 0.00 / 0.03 | 0.00 | - |
| `glass_lewis_recommendation` | DIRECT_OBSERVABLE | 0.03 | 0.00 / 0.03 | 0.00 | - |
| `proxy_dissent_rate` | DIRECT_OBSERVABLE | 0.04 | 0.03 / 0.00 | 0.00 | + |
| `board_refreshment_velocity` | INFERRED_PROXY | 0.03 | 0.00 / 0.03 | 0.00 | + |
| `ceo_tenure_band` | DIRECT_OBSERVABLE | 0.03 | 0.03 / 0.00 | 0.00 | + |
| `audit_qualification_history` | DIRECT_OBSERVABLE | 0.05 | 0.04 / 0.04 | 0.00 | + |
| `restatement_record` | DIRECT_OBSERVABLE | 0.05 | 0.00 / 0.05 | 0.00 | + |
| `cfo_turnover_velocity` | INFERRED_PROXY | 0.03 | 0.03 / 0.00 | 0.00 | + |
| `director_interlock_density` | INFERRED_PROXY | 0.02 | 0.00 / 0.02 | 0.00 | + |
| `related_party_transaction_volume` | DIRECT_OBSERVABLE | 0.03 | 0.00 / 0.03 | 0.00 | + |
| `clawback_policy_presence` | DIRECT_OBSERVABLE | 0.02 | 0.02 / 0.00 | 0.00 | - |
| `equity_grant_dilution_trend` | DIRECT_OBSERVABLE | 0.02 | 0.00 / 0.02 | 0.00 | + |

#### Transaction & Event Risk
*M&A activity, IPO/SPAC risk, delisting exposure, PE sponsor dynamics*

| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `ma_activity` | DIRECT_OBSERVABLE | 0.25 | 0.20 / 0.20 | 0.00 | + |
| `ipo_spac_exposure` | DIRECT_OBSERVABLE | 0.25 | 0.25 / 0.25 | 0.00 | + |
| `pe_sponsor_dynamics` | INFERRED_PROXY | 0.20 | 0.15 / 0.15 | 0.15 | + |
| `bankruptcy_distress_risk` | INFERRED_PROXY | 0.20 | 0.20 / 0.25 | 0.00 | + |
| `regulatory_investigation_exposure` | DIRECT_OBSERVABLE | 0.10 | 0.15 / 0.15 | 0.00 | + |

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 | Public Company Governance | 1.50 | 0.50 | 0.55 | 0.45 |
| 2 | Transaction & Event Risk | 0.60 | 0.20 | 0.20 | 0.20 |
| 3 | Corporate Footprint | 0.45 | 0.15 | 0.10 | 0.20 |
| 4 | Firm Stability | 0.45 | 0.15 | 0.15 | 0.15 |

**Primary Assessment Driver:** `Public Company Governance` with combined weight of 1.50
**Secondary Driver:** `Transaction & Event Risk` with combined weight of 0.60

### Three-Layer Pricing Translation
> *How each pillar's tier score becomes a concrete underwriting action or pricing modifier. This is the bridge between signal observation and premium.*

**Risk -> Underwriting Action & Base Rate**

| Tier | Score Band | Action | Rate / Method |
|------|-----------|--------|---------------|
| PREFERRED | 800-1000 | APPROVE | 0.005% (MULTIPLIER) |
| STANDARD_PLUS | 650-799 | APPROVE | 0.008% (MULTIPLIER) |
| STANDARD | 500-649 | REFER | 0.014% (MULTIPLIER) |
| SUBSTANDARD | 350-499 | REFER | 0.025% (MULTIPLIER) |
| DECLINE | 0-349 | DECLINE | 0.04% (MULTIPLIER) |

**Loss -> Frequency & Severity Modifiers**

| Tier | Score Band | Frequency Modifier | Severity Modifier |
|------|-----------|--------------------|-------------------|
| VERY_LOW | 80-100 | 0.7 | 0.8 |
| LOW | 60-79 | 0.85 | 0.9 |
| MODERATE | 40-59 | 1.0 | 1.0 |
| ELEVATED | 20-39 | 1.15 | 1.15 |
| HIGH | 0-19 | 1.35 | 1.4 |

*Loss modifier is bounded: floor 0.5, cap 1.8.*

**Exposure (size) -> Scale Modifier**

| Band | Score Band | Modifier | Implied Value Range |
|------|-----------|----------|---------------------|
| MICRO | 0-20 | 0.5 | $0 - $10,000,000 |
| SMALL | 21-40 | 0.75 | $10,000,000 - $100,000,000 |
| MEDIUM | 41-60 | 1.0 | $100,000,000 - $1,000,000,000 |
| LARGE | 61-80 | 1.5 | $1,000,000,000 - $10,000,000,000 |
| VERY_LARGE | 81-100 | 2.5 | $10,000,000,000 - $100,000,000,000 |

**Exposure (complexity) -> Scale Modifier**

| Band | Score Band | Modifier | Implied Value Range |
|------|-----------|----------|---------------------|
| SIMPLE | 0-20 | 0.85 | n/a |
| MODERATE | 21-40 | 0.95 | n/a |
| COMPLEX | 41-60 | 1.1 | n/a |
| HIGHLY_COMPLEX | 61-80 | 1.3 | n/a |
| EXTREMELY_COMPLEX | 81-100 | 1.6 | n/a |

### Theoretical Premium Calculation (Tier 3 Standard)
> *Per the DSI Premium Calculation Methodology v2.0, the core formula is:*
> *P_final = (Base × Rate) × ILF_relativity × Deductible_Factor × Modifiers*

**1. The Pricing Anchor:** The Base Rate of `0.013999999999999999%` on `revenue` purchases exactly a `$10,000,000` Limit with a `$500,000` Deductible.
**2. Theoretical Execution:**
  - Assume `revenue` = $10,000,000
  - Base Premium = $10,000,000 × 0.00014 = **$1,400**
  - If the client requests the Anchor Limit/Deductible, the factors are 1.00, resulting in a technical premium of **$1,400**.

---

## Model: `do_pe_backed`
*PE/VC portfolio companies — sponsor dynamics, exit pressure, board composition*

### Routing Protocol (Multiplexer)
- `company_segment == PE_BACKED`

### Three-Layer Weight Distribution
> *DSI requires that weights for Risk, Loss, and Exposure each sum to 1.0 across all signal groups.*

**Validation:** PASS

| Group | Risk | Loss | Exposure |
|-------|------|------|----------|
| Transaction & Event Risk | 0.35 | 0.30 | 0.25 |
| Corporate Footprint | 0.20 | 0.20 | 0.25 |
| Firm Stability | 0.20 | 0.20 | 0.20 |
| Regulatory Standing | 0.25 | 0.30 | 0.30 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

**Group Definitions:**
- **Transaction & Event Risk:** M&A activity, IPO/SPAC risk, delisting exposure, PE sponsor dynamics

*Reading the table: a group's three weights are independent. The same group can be a dominant driver of one pillar and a minor input to another — e.g. a group may carry most of the Exposure weight while contributing little to Risk.*

### Signal Architecture Rationale
This configuration contains **5 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `DIRECT_OBSERVABLE` (3 signals): Highest confidence
- `INFERRED_PROXY` (2 signals): Medium confidence

**Signal Count by Group:**
- `structured_data`: 5 signals

**Selection Rationale:**
- 60% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Detail by Group
> *Each signal is an objectively observable data point. The weights show how strongly that signal informs each assessment pillar; correlation direction indicates whether a higher observed value increases (+) or decreases (-) the assessed exposure.*

#### Transaction & Event Risk
*M&A activity, IPO/SPAC risk, delisting exposure, PE sponsor dynamics*

| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `ma_activity` | DIRECT_OBSERVABLE | 0.25 | 0.20 / 0.20 | 0.00 | + |
| `ipo_spac_exposure` | DIRECT_OBSERVABLE | 0.25 | 0.25 / 0.25 | 0.00 | + |
| `pe_sponsor_dynamics` | INFERRED_PROXY | 0.20 | 0.15 / 0.15 | 0.15 | + |
| `bankruptcy_distress_risk` | INFERRED_PROXY | 0.20 | 0.20 / 0.25 | 0.00 | + |
| `regulatory_investigation_exposure` | DIRECT_OBSERVABLE | 0.10 | 0.15 / 0.15 | 0.00 | + |

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 | Transaction & Event Risk | 0.90 | 0.35 | 0.30 | 0.25 |
| 2 | Regulatory Standing | 0.85 | 0.25 | 0.30 | 0.30 |
| 3 | Corporate Footprint | 0.65 | 0.20 | 0.20 | 0.25 |
| 4 | Firm Stability | 0.60 | 0.20 | 0.20 | 0.20 |

**Primary Assessment Driver:** `Transaction & Event Risk` with combined weight of 0.90
**Secondary Driver:** `Regulatory Standing` with combined weight of 0.85

### Three-Layer Pricing Translation
> *How each pillar's tier score becomes a concrete underwriting action or pricing modifier. This is the bridge between signal observation and premium.*

**Risk -> Underwriting Action & Base Rate**

| Tier | Score Band | Action | Rate / Method |
|------|-----------|--------|---------------|
| PREFERRED | 800-1000 | APPROVE | 0.005% (MULTIPLIER) |
| STANDARD_PLUS | 650-799 | APPROVE | 0.008% (MULTIPLIER) |
| STANDARD | 500-649 | REFER | 0.013% (MULTIPLIER) |
| SUBSTANDARD | 350-499 | REFER | 0.022% (MULTIPLIER) |
| DECLINE | 0-349 | DECLINE | 0.035% (MULTIPLIER) |

**Loss -> Frequency & Severity Modifiers**

| Tier | Score Band | Frequency Modifier | Severity Modifier |
|------|-----------|--------------------|-------------------|
| VERY_LOW | 80-100 | 0.7 | 0.8 |
| LOW | 60-79 | 0.85 | 0.9 |
| MODERATE | 40-59 | 1.0 | 1.0 |
| ELEVATED | 20-39 | 1.15 | 1.15 |
| HIGH | 0-19 | 1.35 | 1.4 |

*Loss modifier is bounded: floor 0.5, cap 1.8.*

**Exposure (size) -> Scale Modifier**

| Band | Score Band | Modifier | Implied Value Range |
|------|-----------|----------|---------------------|
| MICRO | 0-20 | 0.5 | $0 - $10,000,000 |
| SMALL | 21-40 | 0.75 | $10,000,000 - $100,000,000 |
| MEDIUM | 41-60 | 1.0 | $100,000,000 - $1,000,000,000 |
| LARGE | 61-80 | 1.5 | $1,000,000,000 - $10,000,000,000 |
| VERY_LARGE | 81-100 | 2.5 | $10,000,000,000 - $100,000,000,000 |

**Exposure (complexity) -> Scale Modifier**

| Band | Score Band | Modifier | Implied Value Range |
|------|-----------|----------|---------------------|
| SIMPLE | 0-20 | 0.85 | n/a |
| MODERATE | 21-40 | 0.95 | n/a |
| COMPLEX | 41-60 | 1.1 | n/a |
| HIGHLY_COMPLEX | 61-80 | 1.3 | n/a |
| EXTREMELY_COMPLEX | 81-100 | 1.6 | n/a |

### Theoretical Premium Calculation (Tier 3 Standard)
> *Per the DSI Premium Calculation Methodology v2.0, the core formula is:*
> *P_final = (Base × Rate) × ILF_relativity × Deductible_Factor × Modifiers*

**1. The Pricing Anchor:** The Base Rate of `0.013%` on `revenue` purchases exactly a `$5,000,000` Limit with a `$250,000` Deductible.
**2. Theoretical Execution:**
  - Assume `revenue` = $10,000,000
  - Base Premium = $10,000,000 × 0.00013 = **$1,300**
  - If the client requests the Anchor Limit/Deductible, the factors are 1.00, resulting in a technical premium of **$1,300**.

---

## Model: `do_nonprofit`
*Non-profit and charitable organisations — donor restrictions, fiduciary duties, regulatory compliance*

### Routing Protocol (Multiplexer)
- `company_segment == NONPROFIT`

### Three-Layer Weight Distribution
> *DSI requires that weights for Risk, Loss, and Exposure each sum to 1.0 across all signal groups.*

**Validation:** PASS

| Group | Risk | Loss | Exposure |
|-------|------|------|----------|
| Corporate Footprint | 0.25 | 0.20 | 0.25 |
| Firm Stability | 0.25 | 0.25 | 0.20 |
| Regulatory Standing | 0.40 | 0.45 | 0.40 |
| Transaction & Event Risk | 0.10 | 0.10 | 0.15 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

**Group Definitions:**
- **Transaction & Event Risk:** M&A activity, IPO/SPAC risk, delisting exposure, PE sponsor dynamics

*Reading the table: a group's three weights are independent. The same group can be a dominant driver of one pillar and a minor input to another — e.g. a group may carry most of the Exposure weight while contributing little to Risk.*

### Signal Architecture Rationale
This configuration contains **5 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `DIRECT_OBSERVABLE` (3 signals): Highest confidence
- `INFERRED_PROXY` (2 signals): Medium confidence

**Signal Count by Group:**
- `structured_data`: 5 signals

**Selection Rationale:**
- 60% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Detail by Group
> *Each signal is an objectively observable data point. The weights show how strongly that signal informs each assessment pillar; correlation direction indicates whether a higher observed value increases (+) or decreases (-) the assessed exposure.*

#### Transaction & Event Risk
*M&A activity, IPO/SPAC risk, delisting exposure, PE sponsor dynamics*

| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `ma_activity` | DIRECT_OBSERVABLE | 0.25 | 0.20 / 0.20 | 0.00 | + |
| `ipo_spac_exposure` | DIRECT_OBSERVABLE | 0.25 | 0.25 / 0.25 | 0.00 | + |
| `pe_sponsor_dynamics` | INFERRED_PROXY | 0.20 | 0.15 / 0.15 | 0.15 | + |
| `bankruptcy_distress_risk` | INFERRED_PROXY | 0.20 | 0.20 / 0.25 | 0.00 | + |
| `regulatory_investigation_exposure` | DIRECT_OBSERVABLE | 0.10 | 0.15 / 0.15 | 0.00 | + |

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 | Regulatory Standing | 1.25 | 0.40 | 0.45 | 0.40 |
| 2 | Corporate Footprint | 0.70 | 0.25 | 0.20 | 0.25 |
| 3 | Firm Stability | 0.70 | 0.25 | 0.25 | 0.20 |
| 4 | Transaction & Event Risk | 0.35 | 0.10 | 0.10 | 0.15 |

**Primary Assessment Driver:** `Regulatory Standing` with combined weight of 1.25
**Secondary Driver:** `Corporate Footprint` with combined weight of 0.70

### Three-Layer Pricing Translation
> *How each pillar's tier score becomes a concrete underwriting action or pricing modifier. This is the bridge between signal observation and premium.*

**Risk -> Underwriting Action & Base Rate**

| Tier | Score Band | Action | Rate / Method |
|------|-----------|--------|---------------|
| PREFERRED | 800-1000 | APPROVE | 0.002% (MULTIPLIER) |
| STANDARD_PLUS | 650-799 | APPROVE | 0.0035% (MULTIPLIER) |
| STANDARD | 500-649 | REFER | 0.006% (MULTIPLIER) |
| SUBSTANDARD | 350-499 | REFER | 0.01% (MULTIPLIER) |
| DECLINE | 0-349 | DECLINE | 0.018% (MULTIPLIER) |

**Loss -> Frequency & Severity Modifiers**

| Tier | Score Band | Frequency Modifier | Severity Modifier |
|------|-----------|--------------------|-------------------|
| VERY_LOW | 80-100 | 0.7 | 0.8 |
| LOW | 60-79 | 0.85 | 0.9 |
| MODERATE | 40-59 | 1.0 | 1.0 |
| ELEVATED | 20-39 | 1.15 | 1.15 |
| HIGH | 0-19 | 1.35 | 1.4 |

*Loss modifier is bounded: floor 0.5, cap 1.8.*

**Exposure (size) -> Scale Modifier**

| Band | Score Band | Modifier | Implied Value Range |
|------|-----------|----------|---------------------|
| MICRO | 0-20 | 0.5 | $0 - $10,000,000 |
| SMALL | 21-40 | 0.75 | $10,000,000 - $100,000,000 |
| MEDIUM | 41-60 | 1.0 | $100,000,000 - $1,000,000,000 |
| LARGE | 61-80 | 1.5 | $1,000,000,000 - $10,000,000,000 |
| VERY_LARGE | 81-100 | 2.5 | $10,000,000,000 - $100,000,000,000 |

**Exposure (complexity) -> Scale Modifier**

| Band | Score Band | Modifier | Implied Value Range |
|------|-----------|----------|---------------------|
| SIMPLE | 0-20 | 0.85 | n/a |
| MODERATE | 21-40 | 0.95 | n/a |
| COMPLEX | 41-60 | 1.1 | n/a |
| HIGHLY_COMPLEX | 61-80 | 1.3 | n/a |
| EXTREMELY_COMPLEX | 81-100 | 1.6 | n/a |

### Theoretical Premium Calculation (Tier 3 Standard)
> *Per the DSI Premium Calculation Methodology v2.0, the core formula is:*
> *P_final = (Base × Rate) × ILF_relativity × Deductible_Factor × Modifiers*

**1. The Pricing Anchor:** The Base Rate of `0.006%` on `revenue` purchases exactly a `$2,000,000` Limit with a `$25,000` Deductible.
**2. Theoretical Execution:**
  - Assume `revenue` = $10,000,000
  - Base Premium = $10,000,000 × 6e-05 = **$600**
  - If the client requests the Anchor Limit/Deductible, the factors are 1.00, resulting in a technical premium of **$600**.

---

## Model: `do_ipo_spac`
*IPO and SPAC de-SPAC transactions — elevated SCA risk, prospectus liability, short selling*

### Routing Protocol (Multiplexer)
- `company_segment in ['IPO', 'SPAC']`
- `revenue >= 10000000`

### Three-Layer Weight Distribution
> *DSI requires that weights for Risk, Loss, and Exposure each sum to 1.0 across all signal groups.*

**Validation:** PASS

| Group | Risk | Loss | Exposure |
|-------|------|------|----------|
| Transaction & Event Risk | 0.40 | 0.40 | 0.30 |
| Public Company Governance | 0.30 | 0.35 | 0.35 |
| Corporate Footprint | 0.15 | 0.10 | 0.20 |
| Firm Stability | 0.15 | 0.15 | 0.15 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

**Group Definitions:**
- **Transaction & Event Risk:** M&A activity, IPO/SPAC risk, delisting exposure, PE sponsor dynamics
- **Public Company Governance:** SEC filing quality, board independence, shareholder activism, restatement risk

*Reading the table: a group's three weights are independent. The same group can be a dominant driver of one pillar and a minor input to another — e.g. a group may carry most of the Exposure weight while contributing little to Risk.*

### Signal Architecture Rationale
This configuration contains **10 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `DIRECT_OBSERVABLE` (6 signals): Highest confidence
- `INFERRED_PROXY` (3 signals): Medium confidence
- `COHORT_INFERENCE` (1 signals): Lowest confidence

**Signal Count by Group:**
- `public_record`: 5 signals
- `structured_data`: 5 signals

**Selection Rationale:**
- 60% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Detail by Group
> *Each signal is an objectively observable data point. The weights show how strongly that signal informs each assessment pillar; correlation direction indicates whether a higher observed value increases (+) or decreases (-) the assessed exposure.*

#### Transaction & Event Risk
*M&A activity, IPO/SPAC risk, delisting exposure, PE sponsor dynamics*

| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `ma_activity` | DIRECT_OBSERVABLE | 0.25 | 0.20 / 0.20 | 0.00 | + |
| `ipo_spac_exposure` | DIRECT_OBSERVABLE | 0.25 | 0.25 / 0.25 | 0.00 | + |
| `pe_sponsor_dynamics` | INFERRED_PROXY | 0.20 | 0.15 / 0.15 | 0.15 | + |
| `bankruptcy_distress_risk` | INFERRED_PROXY | 0.20 | 0.20 / 0.25 | 0.00 | + |
| `regulatory_investigation_exposure` | DIRECT_OBSERVABLE | 0.10 | 0.15 / 0.15 | 0.00 | + |

#### Public Company Governance
*SEC filing quality, board independence, shareholder activism, restatement risk*

| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `sec_filing_quality` | DIRECT_OBSERVABLE | 0.25 | 0.20 / 0.15 | 0.00 | + |
| `board_independence` | DIRECT_OBSERVABLE | 0.20 | 0.10 / 0.00 | 0.00 | + |
| `shareholder_activism` | INFERRED_PROXY | 0.15 | 0.15 / 0.15 | 0.00 | + |
| `securities_litigation_exposure` | COHORT_INFERENCE | 0.20 | 0.20 / 0.25 | 0.00 | + |
| `executive_compensation_structure` | DIRECT_OBSERVABLE | 0.10 | 0.10 / 0.00 | 0.10 | + |

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 | Transaction & Event Risk | 1.10 | 0.40 | 0.40 | 0.30 |
| 2 | Public Company Governance | 1.00 | 0.30 | 0.35 | 0.35 |
| 3 | Corporate Footprint | 0.45 | 0.15 | 0.10 | 0.20 |
| 4 | Firm Stability | 0.45 | 0.15 | 0.15 | 0.15 |

**Primary Assessment Driver:** `Transaction & Event Risk` with combined weight of 1.10
**Secondary Driver:** `Public Company Governance` with combined weight of 1.00

### Three-Layer Pricing Translation
> *How each pillar's tier score becomes a concrete underwriting action or pricing modifier. This is the bridge between signal observation and premium.*

**Risk -> Underwriting Action & Base Rate**

| Tier | Score Band | Action | Rate / Method |
|------|-----------|--------|---------------|
| PREFERRED | 800-1000 | APPROVE | 0.01% (MULTIPLIER) |
| STANDARD_PLUS | 650-799 | APPROVE | 0.018% (MULTIPLIER) |
| STANDARD | 500-649 | REFER | 0.03% (MULTIPLIER) |
| SUBSTANDARD | 350-499 | REFER | 0.05% (MULTIPLIER) |
| DECLINE | 0-349 | DECLINE | 0.08% (MULTIPLIER) |

**Loss -> Frequency & Severity Modifiers**

| Tier | Score Band | Frequency Modifier | Severity Modifier |
|------|-----------|--------------------|-------------------|
| VERY_LOW | 80-100 | 0.7 | 0.8 |
| LOW | 60-79 | 0.85 | 0.9 |
| MODERATE | 40-59 | 1.0 | 1.0 |
| ELEVATED | 20-39 | 1.15 | 1.15 |
| HIGH | 0-19 | 1.35 | 1.4 |

*Loss modifier is bounded: floor 0.5, cap 1.8.*

**Exposure (size) -> Scale Modifier**

| Band | Score Band | Modifier | Implied Value Range |
|------|-----------|----------|---------------------|
| MICRO | 0-20 | 0.5 | $0 - $10,000,000 |
| SMALL | 21-40 | 0.75 | $10,000,000 - $100,000,000 |
| MEDIUM | 41-60 | 1.0 | $100,000,000 - $1,000,000,000 |
| LARGE | 61-80 | 1.5 | $1,000,000,000 - $10,000,000,000 |
| VERY_LARGE | 81-100 | 2.5 | $10,000,000,000 - $100,000,000,000 |

**Exposure (complexity) -> Scale Modifier**

| Band | Score Band | Modifier | Implied Value Range |
|------|-----------|----------|---------------------|
| SIMPLE | 0-20 | 0.85 | n/a |
| MODERATE | 21-40 | 0.95 | n/a |
| COMPLEX | 41-60 | 1.1 | n/a |
| HIGHLY_COMPLEX | 61-80 | 1.3 | n/a |
| EXTREMELY_COMPLEX | 81-100 | 1.6 | n/a |

### Theoretical Premium Calculation (Tier 3 Standard)
> *Per the DSI Premium Calculation Methodology v2.0, the core formula is:*
> *P_final = (Base × Rate) × ILF_relativity × Deductible_Factor × Modifiers*

**1. The Pricing Anchor:** The Base Rate of `0.03%` on `revenue` purchases exactly a `$10,000,000` Limit with a `$1,000,000` Deductible.
**2. Theoretical Execution:**
  - Assume `revenue` = $10,000,000
  - Base Premium = $10,000,000 × 0.0003 = **$3,000**
  - If the client requests the Anchor Limit/Deductible, the factors are 1.00, resulting in a technical premium of **$3,000**.


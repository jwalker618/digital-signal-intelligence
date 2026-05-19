# DSI Logic Document: `FI`
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

## Model: `fi_general`
*FI bond, professional liability, D&O, cyber coverage based on observable regulatory and financial signals*

### Routing Protocol (Multiplexer)
- `aum > 500000000`

### Three-Layer Weight Distribution
> *DSI requires that weights for Risk, Loss, and Exposure each sum to 1.0 across all signal groups.*

**Validation:** PASS

| Group | Risk | Loss | Exposure |
|-------|------|------|----------|
| Network Authority | 0.10 | 0.05 | 0.05 |
| Regulatory Compliance | 0.25 | 0.25 | 0.10 |
| Financial Condition | 0.20 | 0.30 | 0.25 |
| Corporate Governance | 0.20 | 0.18 | 0.25 |
| Operational Risk | 0.20 | 0.20 | 0.20 |
| Structured Data | 0.05 | 0.02 | 0.15 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

**Group Definitions:**
- **Network Authority:** Quality of institutional relationships and counterparties
- **Regulatory Compliance:** Examination results, enforcement actions, compliance ratings
- **Financial Condition:** Capital, asset quality, liquidity, earnings (CAMELS proxies)
- **Corporate Governance:** Board composition, executive stability, committee quality
- **Operational Risk:** Complaints, litigation, breach history, incidents
- **Structured Data:** Third-party ratings and benchmarks

*Reading the table: a group's three weights are independent. The same group can be a dominant driver of one pillar and a minor input to another — e.g. a group may carry most of the Exposure weight while contributing little to Risk.*

### Signal Architecture Rationale
This configuration contains **51 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `DIRECT_OBSERVABLE` (35 signals): Highest confidence
- `INFERRED_PROXY` (15 signals): Medium confidence
- `COHORT_INFERENCE` (1 signals): Lowest confidence

**Signal Count by Group:**
- `corporate_footprint`: 12 signals
- `technical_infrastructure`: 11 signals
- `network_authority`: 7 signals
- `public_record`: 7 signals
- `behavioural`: 7 signals
- `structured_data`: 3 signals
- `institution_type`: 1 signals
- `regulatory_framework`: 1 signals
- `asset_size_band`: 1 signals
- `publicly_traded`: 1 signals

**Selection Rationale:**
- 69% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Detail by Group
> *Each signal is an objectively observable data point. The weights show how strongly that signal informs each assessment pillar; correlation direction indicates whether a higher observed value increases (+) or decreases (-) the assessed exposure.*

#### Network Authority
*Quality of institutional relationships and counterparties*

| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `correspondent_quality` | INFERRED_PROXY | 0.20 | 0.15 / 0.10 | 0.00 | + |
| `fhlb_membership` | DIRECT_OBSERVABLE | 0.10 | 0.00 / 0.05 | 0.00 | + |
| `clearing_relationship` | INFERRED_PROXY | 0.15 | 0.10 / 0.00 | 0.00 | + |
| `auditor_quality` | DIRECT_OBSERVABLE | 0.20 | 0.15 / 0.15 | 0.00 | + |
| `legal_counsel` | INFERRED_PROXY | 0.10 | 0.00 / 0.10 | 0.00 | + |
| `industry_association` | DIRECT_OBSERVABLE | 0.10 | 0.00 / 0.00 | 0.00 | + |
| `credit_rating` | DIRECT_OBSERVABLE | 0.15 | 0.00 / 0.20 | 0.00 | + |

#### Regulatory Compliance
*Examination results, enforcement actions, compliance ratings*

| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `examination_rating` | DIRECT_OBSERVABLE | 0.20 | 0.20 / 0.15 | 0.00 | + |
| `enforcement_action` | DIRECT_OBSERVABLE | 0.25 | 0.25 / 0.25 | 0.15 | + |
| `informal_action` | DIRECT_OBSERVABLE | 0.10 | 0.10 / 0.00 | 0.00 | + |
| `cra_rating` | DIRECT_OBSERVABLE | 0.10 | 0.10 / 0.00 | 0.00 | + |
| `bsa_aml` | DIRECT_OBSERVABLE | 0.15 | 0.20 / 0.20 | 0.00 | + |
| `fair_lending` | DIRECT_OBSERVABLE | 0.10 | 0.15 / 0.10 | 0.00 | + |
| `consumer_compliance` | DIRECT_OBSERVABLE | 0.10 | 0.10 / 0.00 | 0.00 | + |

#### Financial Condition
*Capital, asset quality, liquidity, earnings (CAMELS proxies)*

| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `capital_ratio` | DIRECT_OBSERVABLE | 0.20 | 0.00 / 0.25 | 0.20 | + |
| `asset_quality` | DIRECT_OBSERVABLE | 0.20 | 0.15 / 0.20 | 0.00 | + |
| `liquidity` | DIRECT_OBSERVABLE | 0.15 | 0.00 / 0.15 | 0.00 | + |
| `earnings` | DIRECT_OBSERVABLE | 0.15 | 0.00 / 0.10 | 0.00 | + |
| `concentration` | DIRECT_OBSERVABLE | 0.10 | 0.00 / 0.15 | 0.10 | - |
| `interest_rate_risk` | DIRECT_OBSERVABLE | 0.10 | 0.00 / 0.10 | 0.00 | - |
| `growth_rate` | DIRECT_OBSERVABLE | 0.10 | 0.00 / 0.00 | 0.10 | + |

#### Corporate Governance
*Board composition, executive stability, committee quality*

| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `board_independence` | DIRECT_OBSERVABLE | 0.20 | 0.15 / 0.10 | 0.00 | + |
| `board_expertise` | INFERRED_PROXY | 0.20 | 0.10 / 0.00 | 0.00 | + |
| `executive_stability` | INFERRED_PROXY | 0.15 | 0.15 / 0.00 | 0.00 | + |
| `risk_committee` | DIRECT_OBSERVABLE | 0.20 | 0.15 / 0.10 | 0.00 | + |
| `audit_committee` | DIRECT_OBSERVABLE | 0.15 | 0.15 / 0.00 | 0.00 | + |
| `related_party` | DIRECT_OBSERVABLE | 0.10 | 0.15 / 0.10 | 0.00 | - |
| `investor_relations` | INFERRED_PROXY | 0.20 | 0.00 / 0.00 | 0.10 | + |
| `disclosure_quality` | INFERRED_PROXY | 0.20 | 0.10 / 0.00 | 0.00 | + |
| `security_page` | DIRECT_OBSERVABLE | 0.15 | 0.00 / 0.00 | 0.00 | + |
| `hiring_signals` | INFERRED_PROXY | 0.15 | 0.00 / 0.00 | 0.25 | + |
| `esg_reporting` | INFERRED_PROXY | 0.15 | 0.00 / 0.00 | 0.00 | + |
| `community_presence` | INFERRED_PROXY | 0.15 | 0.00 / 0.00 | 0.10 | + |

#### Operational Risk
*Complaints, litigation, breach history, incidents*

| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `cfpb_complaint` | DIRECT_OBSERVABLE | 0.25 | 0.30 / 0.15 | 0.10 | + |
| `bbb_complaint` | DIRECT_OBSERVABLE | 0.10 | 0.10 / 0.00 | 0.00 | + |
| `litigation` | DIRECT_OBSERVABLE | 0.25 | 0.35 / 0.30 | 0.00 | + |
| `breach_history` | DIRECT_OBSERVABLE | 0.25 | 0.30 / 0.25 | 0.00 | + |
| `operational_incident` | INFERRED_PROXY | 0.15 | 0.20 / 0.15 | 0.00 | + |
| `tls_score` | DIRECT_OBSERVABLE | 0.20 | 0.15 / 0.10 | 0.00 | + |
| `email_auth` | DIRECT_OBSERVABLE | 0.20 | 0.20 / 0.00 | 0.00 | + |
| `security_headers` | DIRECT_OBSERVABLE | 0.15 | 0.10 / 0.00 | 0.00 | + |
| `network_exposure` | DIRECT_OBSERVABLE | 0.20 | 0.15 / 0.15 | 0.15 | + |
| `vulnerability` | DIRECT_OBSERVABLE | 0.15 | 0.25 / 0.20 | 0.00 | + |
| `security_rating` | DIRECT_OBSERVABLE | 0.10 | 0.10 / 0.10 | 0.00 | + |

#### Structured Data
*Third-party ratings and benchmarks*

| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `credit_rating_structured` | DIRECT_OBSERVABLE | 0.40 | 0.00 / 0.30 | 0.00 | + |
| `esg_rating` | DIRECT_OBSERVABLE | 0.30 | 0.10 / 0.00 | 0.00 | + |
| `peer_benchmark` | COHORT_INFERENCE | 0.30 | 0.15 / 0.15 | 0.00 | + |

#### institution_type
**Categorical signal `institution_type`** — proxy tier: `INFERRED_PROXY`, source: `metadata.institution_type`

| Category | Label | Applied Factor |
|----------|-------|----------------|
| `MONEY_CENTER_BANK` | Money Center Bank | 1.5 |
| `REGIONAL_BANK` | Regional Bank | 1.2 |
| `COMMUNITY_BANK` | Community Bank | 1.0 |
| `CREDIT_UNION` | Credit Union | 0.85 |
| `SAVINGS_INSTITUTION` | Savings Institution | 0.9 |
| `BROKER_DEALER` | Broker-Dealer | 1.4 |
| `INVESTMENT_ADVISER` | Investment Adviser | 1.25 |
| `INSURANCE_COMPANY` | Insurance Company | 1.1 |
| `ASSET_MANAGER` | Asset Manager | 1.3 |
| `FINTECH` | Fintech | 1.5 |
| `MORTGAGE_COMPANY` | Mortgage Company | 1.35 |
| `PAYMENT_PROCESSOR` | Payment Processor | 1.4 |
| `OTHER` | Other Financial Institution | 1.2 |

#### regulatory_framework
**Categorical signal `regulatory_framework`** — proxy tier: `INFERRED_PROXY`, source: `metadata.regulatory_framework`

| Category | Label | Applied Factor |
|----------|-------|----------------|
| `OCC` | OCC (National Banks) | 1.0 |
| `FDIC` | FDIC (State Non-Member) | 1.0 |
| `FED` | Federal Reserve | 1.0 |
| `NCUA` | NCUA (Credit Unions) | 0.95 |
| `SEC` | SEC | 1.1 |
| `FINRA` | FINRA | 1.1 |
| `STATE` | State Regulated | 1.15 |
| `MULTI` | Multiple Regulators | 1.05 |
| `OTHER` | UNKNOWN | 1.0 |

#### asset_size_band
**Categorical signal `asset_size_band`** — proxy tier: `INFERRED_PROXY`, source: `metadata.asset_size_band`

| Category | Label | Applied Factor |
|----------|-------|----------------|
| `MEGA` | Mega (>$250B) | 0.15 |
| `LARGE` | Large ($50B-$250B) | 0.35 |
| `MID` | Mid-Size ($10B-$50B) | 1.0 |
| `SMALL` | Small ($1B-$10B) | 1.5 |
| `COMMUNITY` | Community (<$1B) | 2.0 |
| `OTHER` | UNKNOWN | 1.0 |

#### publicly_traded
**Categorical signal `publicly_traded`** — proxy tier: `INFERRED_PROXY`, source: `metadata.publicly_traded`

| Category | Label | Applied Factor |
|----------|-------|----------------|
| `PUBLIC` | Publicly Traded | 1.1 |
| `PRIVATE` | Private | 1.0 |
| `OTHER` | UNKNOWN | 1.0 |

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 | Financial Condition | 0.75 | 0.20 | 0.30 | 0.25 |
| 2 | Corporate Governance | 0.63 | 0.20 | 0.18 | 0.25 |
| 3 | Regulatory Compliance | 0.60 | 0.25 | 0.25 | 0.10 |
| 4 | Operational Risk | 0.60 | 0.20 | 0.20 | 0.20 |
| 5 | Structured Data | 0.22 | 0.05 | 0.02 | 0.15 |
| 6 | Network Authority | 0.20 | 0.10 | 0.05 | 0.05 |

**Primary Assessment Driver:** `Financial Condition` with combined weight of 0.75
**Secondary Driver:** `Corporate Governance` with combined weight of 0.63

### Three-Layer Pricing Translation
> *How each pillar's tier score becomes a concrete underwriting action or pricing modifier. This is the bridge between signal observation and premium.*

**Risk -> Underwriting Action & Base Rate**

| Tier | Score Band | Action | Rate / Method |
|------|-----------|--------|---------------|
| PREFERRED | 800-1000 | APPROVE | 0.0008% (MULTIPLIER) |
| STANDARD_PLUS | 650-799 | APPROVE | 0.0012% (MULTIPLIER) |
| STANDARD | 500-649 | REFER | 0.0015% (MULTIPLIER) |
| SUBSTANDARD | 350-499 | REFER | 0.0025% (MULTIPLIER) |
| DECLINE | 0-349 | DECLINE | 0.005% (MULTIPLIER) |

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

### Theoretical Premium Calculation (Worked Example)
> *Per the DSI Premium Calculation Methodology v2.0, the full factor chain is:*
> *P_final = (Basis × Base Rate) × ILF_relativity × Deductible_Factor × Loss_Modifier × Exposure_Modifier*

**Worked example — Risk Tier 3 (STANDARD), Loss Tier 4 (ELEVATED), requesting the anchor limit/deductible:**

| Factor | Source | Value |
|--------|--------|-------|
| `total_assets` (rating basis) | Routing-valid assumption | $10,000,000 |
| Base Rate | Risk Tier 3 (STANDARD) | 0.0015% |
| **Base Premium** | `total_assets` × Base Rate | **$150** |
| ILF relativity | Limit = anchor ($1,000,000) | 1.00 |
| Deductible factor | Deductible = anchor ($50,000) | 1.00 |
| Loss frequency modifier | Loss Tier 4 (ELEVATED) | 1.15 |
| Loss severity modifier | Loss Tier 4 (ELEVATED) | 1.15 |
| **Loss modifier** | Frequency × Severity, bounded [0.55, 1.6] | **1.32** |
| Exposure modifier | Size band MEDIUM | 1.00 |
| **Technical Premium** | Product of all factors | **$198** |

*Basis vs. limit: `total_assets` is the total insured value the rate is applied to — a Base Rate of 0.0015% on `total_assets` is the rated cost of risk, not the policy limit. The policy Limit (anchored at $1,000,000) is the maximum payout and scales premium independently via the ILF curve; requesting a limit above the anchor lifts the ILF relativity above 1.00.*

**Loss Tier Sensitivity** — holding Risk Tier 3 and the Exposure modifier constant, the technical premium moves with the Loss tier:

| Loss Tier | Freq Mod | Sev Mod | Loss Modifier | Technical Premium |
|-----------|----------|---------|---------------|-------------------|
| 1 VERY_LOW | 0.70 | 0.80 | 0.56 | $84 |
| 2 LOW | 0.85 | 0.90 | 0.77 | $115 |
| 3 MODERATE | 1.00 | 1.00 | 1.00 | $150 |
| 4 ELEVATED  *(example)* | 1.15 | 1.15 | 1.32 | $198 |
| 5 HIGH | 1.35 | 1.40 | 1.60 | $240 |


---

## Model: `fi_sme`
*Streamlined FI coverage for community banks, small advisers, and funds*

### Routing Protocol (Multiplexer)
- `total_assets <= 500000000`

### Three-Layer Weight Distribution
> *DSI requires that weights for Risk, Loss, and Exposure each sum to 1.0 across all signal groups.*

**Validation:** PASS

| Group | Risk | Loss | Exposure |
|-------|------|------|----------|
| Regulatory Compliance | 0.35 | 0.30 | 0.10 |
| Financial Condition | 0.35 | 0.30 | 0.40 |
| Cyber Security | 0.30 | 0.40 | 0.50 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

*Reading the table: a group's three weights are independent. The same group can be a dominant driver of one pillar and a minor input to another — e.g. a group may carry most of the Exposure weight while contributing little to Risk.*

### Signal Architecture Rationale
This configuration contains **8 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `DIRECT_OBSERVABLE` (7 signals): Highest confidence
- `INFERRED_PROXY` (1 signals): Medium confidence

**Signal Count by Group:**
- `technical_infrastructure`: 3 signals
- `public_record`: 2 signals
- `behavioural`: 2 signals
- `institution_type`: 1 signals

**Selection Rationale:**
- 88% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Detail by Group
> *Each signal is an objectively observable data point. The weights show how strongly that signal informs each assessment pillar; correlation direction indicates whether a higher observed value increases (+) or decreases (-) the assessed exposure.*

#### Regulatory Compliance
| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `examination_rating` | DIRECT_OBSERVABLE | 0.60 | 0.50 / 0.00 | 0.00 | + |
| `enforcement_action` | DIRECT_OBSERVABLE | 0.40 | 0.50 / 0.00 | 0.00 | + |

#### Financial Condition
| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `capital_ratio` | DIRECT_OBSERVABLE | 0.50 | 0.00 / 0.50 | 0.50 | + |
| `asset_quality` | DIRECT_OBSERVABLE | 0.50 | 0.50 / 0.00 | 0.50 | + |

#### Cyber Security
| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `tls_score` | DIRECT_OBSERVABLE | 0.50 | 0.50 / 0.00 | 0.00 | + |
| `breach_history` | DIRECT_OBSERVABLE | 0.50 | 0.00 / 0.50 | 0.00 | + |
| `litigation` | DIRECT_OBSERVABLE | 1.00 | 1.00 / 0.00 | 0.00 | + |

#### institution_type
**Categorical signal `institution_type`** — proxy tier: `INFERRED_PROXY`, source: `metadata.institution_type`

| Category | Label | Applied Factor |
|----------|-------|----------------|
| `COMMUNITY_BANK` | Community Bank | 0.85 |
| `CREDIT_UNION` | Credit Union | 0.8 |
| `INVESTMENT_ADVISER` | Investment Adviser | 1.1 |
| `FINTECH` | Fintech Startup | 1.5 |
| `OTHER` | Other | 1.0 |

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 | Cyber Security | 1.20 | 0.30 | 0.40 | 0.50 |
| 2 | Financial Condition | 1.05 | 0.35 | 0.30 | 0.40 |
| 3 | Regulatory Compliance | 0.75 | 0.35 | 0.30 | 0.10 |

**Primary Assessment Driver:** `Cyber Security` with combined weight of 1.20
**Secondary Driver:** `Financial Condition` with combined weight of 1.05

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
| HIGH | 0-19 | 1.35 | 1.4 |

*Loss modifier is bounded: floor 0.6, cap 1.5.*

**Exposure (size) -> Scale Modifier**

| Band | Score Band | Modifier | Implied Value Range |
|------|-----------|----------|---------------------|
| MICRO | 0-33 | 0.8 | n/a |
| SMALL | 34-66 | 1.0 | n/a |
| MEDIUM | 67-100 | 1.25 | n/a |

**Exposure (complexity) -> Scale Modifier**

| Band | Score Band | Modifier | Implied Value Range |
|------|-----------|----------|---------------------|
| SIMPLE | 0-50 | 0.9 | n/a |
| COMPLEX | 51-100 | 1.15 | n/a |

### Theoretical Premium Calculation (Worked Example)
> *Per the DSI Premium Calculation Methodology v2.0, the core formula is:*
> *P_final = Base Package Premium × Modifiers*

**1. The Pricing Anchor:** The Flat Premium of `$12,000` purchases exactly the `$1,000,000` Limit / `$10,000` Deductible Base Package.
**2. Theoretical Execution:**
  - Technical Premium = **$12,000**
  - *Scaling relies entirely on selecting a different Limit ID from the Bundled limit_configuration packages.*

---

## Model: `fi_bank`
*Regulated banks — commercial, community, savings; capital adequacy and loan quality focus*

### Routing Protocol (Multiplexer)
- `fi_segment == BANK`
- `total_assets >= 1000000000`

### Three-Layer Weight Distribution
> *DSI requires that weights for Risk, Loss, and Exposure each sum to 1.0 across all signal groups.*

**Validation:** PASS

| Group | Risk | Loss | Exposure |
|-------|------|------|----------|
| Banking Risk | 0.40 | 0.40 | 0.30 |
| Regulatory Framework | 0.30 | 0.30 | 0.30 |
| Corporate Footprint | 0.15 | 0.15 | 0.25 |
| Firm Stability | 0.15 | 0.15 | 0.15 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

**Group Definitions:**
- **Banking Risk:** Bank-specific risk — capital adequacy, loan quality, regulatory exam results, BSA/AML compliance

*Reading the table: a group's three weights are independent. The same group can be a dominant driver of one pillar and a minor input to another — e.g. a group may carry most of the Exposure weight while contributing little to Risk.*

### Signal Architecture Rationale
This configuration contains **11 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `DIRECT_OBSERVABLE` (8 signals): Highest confidence
- `INFERRED_PROXY` (3 signals): Medium confidence

**Signal Count by Group:**
- `structured_data`: 9 signals
- `public_record`: 2 signals

**Selection Rationale:**
- 73% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Detail by Group
> *Each signal is an objectively observable data point. The weights show how strongly that signal informs each assessment pillar; correlation direction indicates whether a higher observed value increases (+) or decreases (-) the assessed exposure.*

#### Banking Risk
*Bank-specific risk — capital adequacy, loan quality, regulatory exam results, BSA/AML compliance*

| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `capital_adequacy` | DIRECT_OBSERVABLE | 0.25 | 0.10 / 0.00 | 0.20 | + |
| `loan_portfolio_quality` | DIRECT_OBSERVABLE | 0.25 | 0.25 / 0.20 | 0.00 | + |
| `regulatory_exam_results` | DIRECT_OBSERVABLE | 0.20 | 0.15 / 0.15 | 0.00 | + |
| `bsa_aml_compliance` | INFERRED_PROXY | 0.20 | 0.15 / 0.15 | 0.00 | + |
| `interest_rate_sensitivity` | INFERRED_PROXY | 0.10 | 0.00 / 0.15 | 0.15 | + |
| `ffiec_call_report_ratios` | DIRECT_OBSERVABLE | 0.05 | 0.04 / 0.04 | 0.00 | + |
| `ubpr_roe_volatility` | DIRECT_OBSERVABLE | 0.04 | 0.00 / 0.04 | 0.00 | + |
| `camels_proxy_composite` | INFERRED_PROXY | 0.04 | 0.03 / 0.04 | 0.00 | + |
| `dfast_ccar_outcome` | DIRECT_OBSERVABLE | 0.03 | 0.00 / 0.03 | 0.00 | - |

#### Regulatory Framework
| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `bsa_aml_enforcement` | DIRECT_OBSERVABLE | 0.05 | 0.04 / 0.05 | 0.00 | + |
| `cra_rating` | DIRECT_OBSERVABLE | 0.03 | 0.00 / 0.03 | 0.00 | - |

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 | Banking Risk | 1.10 | 0.40 | 0.40 | 0.30 |
| 2 | Regulatory Framework | 0.90 | 0.30 | 0.30 | 0.30 |
| 3 | Corporate Footprint | 0.55 | 0.15 | 0.15 | 0.25 |
| 4 | Firm Stability | 0.45 | 0.15 | 0.15 | 0.15 |

**Primary Assessment Driver:** `Banking Risk` with combined weight of 1.10
**Secondary Driver:** `Regulatory Framework` with combined weight of 0.90

### Three-Layer Pricing Translation
> *How each pillar's tier score becomes a concrete underwriting action or pricing modifier. This is the bridge between signal observation and premium.*

**Risk -> Underwriting Action & Base Rate**

| Tier | Score Band | Action | Rate / Method |
|------|-----------|--------|---------------|
| PREFERRED | 800-1000 | APPROVE | 0.0006% (MULTIPLIER) |
| STANDARD_PLUS | 650-799 | APPROVE | 0.001% (MULTIPLIER) |
| STANDARD | 500-649 | REFER | 0.0018% (MULTIPLIER) |
| SUBSTANDARD | 350-499 | REFER | 0.003% (MULTIPLIER) |
| DECLINE | 0-349 | DECLINE | 0.005% (MULTIPLIER) |

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
| MICRO | 0-20 | 0.5 | $0 - $500,000,000 |
| SMALL | 21-40 | 0.75 | $500,000,000 - $5,000,000,000 |
| MEDIUM | 41-60 | 1.0 | $5,000,000,000 - $50,000,000,000 |
| LARGE | 61-80 | 1.5 | $50,000,000,000 - $500,000,000,000 |
| VERY_LARGE | 81-100 | 2.5 | $500,000,000,000 - $5,000,000,000,000 |

**Exposure (complexity) -> Scale Modifier**

| Band | Score Band | Modifier | Implied Value Range |
|------|-----------|----------|---------------------|
| SIMPLE | 0-20 | 0.85 | n/a |
| MODERATE | 21-40 | 0.95 | n/a |
| COMPLEX | 41-60 | 1.1 | n/a |
| HIGHLY_COMPLEX | 61-80 | 1.3 | n/a |
| EXTREMELY_COMPLEX | 81-100 | 1.6 | n/a |

### Theoretical Premium Calculation (Worked Example)
> *Per the DSI Premium Calculation Methodology v2.0, the full factor chain is:*
> *P_final = (Basis × Base Rate) × ILF_relativity × Deductible_Factor × Loss_Modifier × Exposure_Modifier*

**Worked example — Risk Tier 3 (STANDARD), Loss Tier 4 (ELEVATED), requesting the anchor limit/deductible:**

| Factor | Source | Value |
|--------|--------|-------|
| `total_assets` (rating basis) | Routing-valid assumption | $3,000,000,000 |
| Base Rate | Risk Tier 3 (STANDARD) | 0.0018% |
| **Base Premium** | `total_assets` × Base Rate | **$54,000** |
| ILF relativity | Limit = anchor ($10,000,000) | 1.00 |
| Deductible factor | Deductible = anchor ($500,000) | 1.00 |
| Loss frequency modifier | Loss Tier 4 (ELEVATED) | 1.15 |
| Loss severity modifier | Loss Tier 4 (ELEVATED) | 1.15 |
| **Loss modifier** | Frequency × Severity, bounded [0.5, 1.8] | **1.32** |
| Exposure modifier | Size band SMALL | 0.75 |
| **Technical Premium** | Product of all factors | **$53,561** |

*Basis vs. limit: `total_assets` is the total insured value the rate is applied to — a Base Rate of 0.0018% on `total_assets` is the rated cost of risk, not the policy limit. The policy Limit (anchored at $10,000,000) is the maximum payout and scales premium independently via the ILF curve; requesting a limit above the anchor lifts the ILF relativity above 1.00.*

**Loss Tier Sensitivity** — holding Risk Tier 3 and the Exposure modifier constant, the technical premium moves with the Loss tier:

| Loss Tier | Freq Mod | Sev Mod | Loss Modifier | Technical Premium |
|-----------|----------|---------|---------------|-------------------|
| 1 VERY_LOW | 0.70 | 0.80 | 0.56 | $22,680 |
| 2 LOW | 0.85 | 0.90 | 0.77 | $30,982 |
| 3 MODERATE | 1.00 | 1.00 | 1.00 | $40,500 |
| 4 ELEVATED  *(example)* | 1.15 | 1.15 | 1.32 | $53,561 |
| 5 HIGH | 1.35 | 1.40 | 1.80 | $72,900 |


---

## Model: `fi_insurer`
*Insurance companies — solvency, reserve adequacy, reinsurance quality, regulatory compliance*

### Routing Protocol (Multiplexer)
- `fi_segment == INSURER`

### Three-Layer Weight Distribution
> *DSI requires that weights for Risk, Loss, and Exposure each sum to 1.0 across all signal groups.*

**Validation:** PASS

| Group | Risk | Loss | Exposure |
|-------|------|------|----------|
| Regulatory Framework | 0.50 | 0.50 | 0.45 |
| Corporate Footprint | 0.25 | 0.25 | 0.30 |
| Firm Stability | 0.25 | 0.25 | 0.25 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

*Reading the table: a group's three weights are independent. The same group can be a dominant driver of one pillar and a minor input to another — e.g. a group may carry most of the Exposure weight while contributing little to Risk.*

### Signal Architecture Rationale
This configuration contains **4 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `DIRECT_OBSERVABLE` (4 signals): Highest confidence

**Signal Count by Group:**
- `public_record`: 4 signals

**Selection Rationale:**
- 100% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Detail by Group
> *Each signal is an objectively observable data point. The weights show how strongly that signal informs each assessment pillar; correlation direction indicates whether a higher observed value increases (+) or decreases (-) the assessed exposure.*

#### Regulatory Framework
| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `naic_rbc_band` | DIRECT_OBSERVABLE | 0.05 | 0.04 / 0.05 | 0.00 | - |
| `iris_ratio_band` | DIRECT_OBSERVABLE | 0.04 | 0.04 / 0.04 | 0.00 | + |
| `complaint_index` | DIRECT_OBSERVABLE | 0.04 | 0.04 / 0.00 | 0.00 | + |
| `jiri_index` | DIRECT_OBSERVABLE | 0.03 | 0.00 / 0.03 | 0.00 | + |

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 | Regulatory Framework | 1.45 | 0.50 | 0.50 | 0.45 |
| 2 | Corporate Footprint | 0.80 | 0.25 | 0.25 | 0.30 |
| 3 | Firm Stability | 0.75 | 0.25 | 0.25 | 0.25 |

**Primary Assessment Driver:** `Regulatory Framework` with combined weight of 1.45
**Secondary Driver:** `Corporate Footprint` with combined weight of 0.80

### Three-Layer Pricing Translation
> *How each pillar's tier score becomes a concrete underwriting action or pricing modifier. This is the bridge between signal observation and premium.*

**Risk -> Underwriting Action & Base Rate**

| Tier | Score Band | Action | Rate / Method |
|------|-----------|--------|---------------|
| PREFERRED | 800-1000 | APPROVE | 0.0007% (MULTIPLIER) |
| STANDARD_PLUS | 650-799 | APPROVE | 0.001% (MULTIPLIER) |
| STANDARD | 500-649 | REFER | 0.0015% (MULTIPLIER) |
| SUBSTANDARD | 350-499 | REFER | 0.0025% (MULTIPLIER) |
| DECLINE | 0-349 | DECLINE | 0.004% (MULTIPLIER) |

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
| MICRO | 0-20 | 0.5 | $0 - $500,000,000 |
| SMALL | 21-40 | 0.75 | $500,000,000 - $5,000,000,000 |
| MEDIUM | 41-60 | 1.0 | $5,000,000,000 - $50,000,000,000 |
| LARGE | 61-80 | 1.5 | $50,000,000,000 - $500,000,000,000 |
| VERY_LARGE | 81-100 | 2.5 | $500,000,000,000 - $5,000,000,000,000 |

**Exposure (complexity) -> Scale Modifier**

| Band | Score Band | Modifier | Implied Value Range |
|------|-----------|----------|---------------------|
| SIMPLE | 0-20 | 0.85 | n/a |
| MODERATE | 21-40 | 0.95 | n/a |
| COMPLEX | 41-60 | 1.1 | n/a |
| HIGHLY_COMPLEX | 61-80 | 1.3 | n/a |
| EXTREMELY_COMPLEX | 81-100 | 1.6 | n/a |

### Theoretical Premium Calculation (Worked Example)
> *Per the DSI Premium Calculation Methodology v2.0, the full factor chain is:*
> *P_final = (Basis × Base Rate) × ILF_relativity × Deductible_Factor × Loss_Modifier × Exposure_Modifier*

**Worked example — Risk Tier 3 (STANDARD), Loss Tier 4 (ELEVATED), requesting the anchor limit/deductible:**

| Factor | Source | Value |
|--------|--------|-------|
| `total_assets` (rating basis) | Routing-valid assumption | $10,000,000 |
| Base Rate | Risk Tier 3 (STANDARD) | 0.0015% |
| **Base Premium** | `total_assets` × Base Rate | **$150** |
| ILF relativity | Limit = anchor ($10,000,000) | 1.00 |
| Deductible factor | Deductible = anchor ($250,000) | 1.00 |
| Loss frequency modifier | Loss Tier 4 (ELEVATED) | 1.15 |
| Loss severity modifier | Loss Tier 4 (ELEVATED) | 1.15 |
| **Loss modifier** | Frequency × Severity, bounded [0.5, 1.8] | **1.32** |
| Exposure modifier | Size band MICRO | 0.50 |
| **Technical Premium** | Product of all factors | **$99** |

*Basis vs. limit: `total_assets` is the total insured value the rate is applied to — a Base Rate of 0.0015% on `total_assets` is the rated cost of risk, not the policy limit. The policy Limit (anchored at $10,000,000) is the maximum payout and scales premium independently via the ILF curve; requesting a limit above the anchor lifts the ILF relativity above 1.00.*

**Loss Tier Sensitivity** — holding Risk Tier 3 and the Exposure modifier constant, the technical premium moves with the Loss tier:

| Loss Tier | Freq Mod | Sev Mod | Loss Modifier | Technical Premium |
|-----------|----------|---------|---------------|-------------------|
| 1 VERY_LOW | 0.70 | 0.80 | 0.56 | $42 |
| 2 LOW | 0.85 | 0.90 | 0.77 | $57 |
| 3 MODERATE | 1.00 | 1.00 | 1.00 | $75 |
| 4 ELEVATED  *(example)* | 1.15 | 1.15 | 1.32 | $99 |
| 5 HIGH | 1.35 | 1.40 | 1.80 | $135 |


---

## Model: `fi_fintech`
*Fintech companies — digital banking, payments, lending platforms, neobanks*

### Routing Protocol (Multiplexer)
- `fi_segment == FINTECH`

### Three-Layer Weight Distribution
> *DSI requires that weights for Risk, Loss, and Exposure each sum to 1.0 across all signal groups.*

**Validation:** PASS

| Group | Risk | Loss | Exposure |
|-------|------|------|----------|
| Fintech & Digital Risk | 0.40 | 0.35 | 0.30 |
| Regulatory Framework | 0.25 | 0.30 | 0.30 |
| Corporate Footprint | 0.15 | 0.15 | 0.20 |
| Firm Stability | 0.20 | 0.20 | 0.20 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

**Group Definitions:**
- **Fintech & Digital Risk:** Fintech-specific risk — regulatory uncertainty, crypto exposure, platform risk, licensing

*Reading the table: a group's three weights are independent. The same group can be a dominant driver of one pillar and a minor input to another — e.g. a group may carry most of the Exposure weight while contributing little to Risk.*

### Signal Architecture Rationale
This configuration contains **8 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `DIRECT_OBSERVABLE` (3 signals): Highest confidence
- `INFERRED_PROXY` (5 signals): Medium confidence

**Signal Count by Group:**
- `structured_data`: 5 signals
- `public_record`: 2 signals
- `corporate_footprint`: 1 signals

**Selection Rationale:**
- 38% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Detail by Group
> *Each signal is an objectively observable data point. The weights show how strongly that signal informs each assessment pillar; correlation direction indicates whether a higher observed value increases (+) or decreases (-) the assessed exposure.*

#### Fintech & Digital Risk
*Fintech-specific risk — regulatory uncertainty, crypto exposure, platform risk, licensing*

| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `regulatory_licensing_status` | DIRECT_OBSERVABLE | 0.25 | 0.15 / 0.00 | 0.00 | + |
| `crypto_asset_exposure` | INFERRED_PROXY | 0.25 | 0.20 / 0.25 | 0.20 | + |
| `platform_technology_risk` | INFERRED_PROXY | 0.20 | 0.20 / 0.15 | 0.00 | + |
| `consumer_protection_compliance` | DIRECT_OBSERVABLE | 0.20 | 0.20 / 0.15 | 0.00 | + |
| `partner_bank_dependency` | INFERRED_PROXY | 0.10 | 0.00 / 0.10 | 0.15 | + |

#### Regulatory Framework
| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `bsa_findings_velocity` | INFERRED_PROXY | 0.03 | 0.03 / 0.00 | 0.00 | + |
| `complaint_velocity` | DIRECT_OBSERVABLE | 0.03 | 0.03 / 0.00 | 0.00 | + |

#### Corporate Footprint
| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `sponsor_bank_dependency` | INFERRED_PROXY | 0.04 | 0.00 / 0.04 | 0.00 | + |

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 | Fintech & Digital Risk | 1.05 | 0.40 | 0.35 | 0.30 |
| 2 | Regulatory Framework | 0.85 | 0.25 | 0.30 | 0.30 |
| 3 | Firm Stability | 0.60 | 0.20 | 0.20 | 0.20 |
| 4 | Corporate Footprint | 0.50 | 0.15 | 0.15 | 0.20 |

**Primary Assessment Driver:** `Fintech & Digital Risk` with combined weight of 1.05
**Secondary Driver:** `Regulatory Framework` with combined weight of 0.85

### Three-Layer Pricing Translation
> *How each pillar's tier score becomes a concrete underwriting action or pricing modifier. This is the bridge between signal observation and premium.*

**Risk -> Underwriting Action & Base Rate**

| Tier | Score Band | Action | Rate / Method |
|------|-----------|--------|---------------|
| PREFERRED | 800-1000 | APPROVE | 0.08% (MULTIPLIER) |
| STANDARD_PLUS | 650-799 | APPROVE | 0.15% (MULTIPLIER) |
| STANDARD | 500-649 | REFER | 0.25% (MULTIPLIER) |
| SUBSTANDARD | 350-499 | REFER | 0.42% (MULTIPLIER) |
| DECLINE | 0-349 | DECLINE | 0.7% (MULTIPLIER) |

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
| MICRO | 0-20 | 0.5 | $0 - $500,000,000 |
| SMALL | 21-40 | 0.75 | $500,000,000 - $5,000,000,000 |
| MEDIUM | 41-60 | 1.0 | $5,000,000,000 - $50,000,000,000 |
| LARGE | 61-80 | 1.5 | $50,000,000,000 - $500,000,000,000 |
| VERY_LARGE | 81-100 | 2.5 | $500,000,000,000 - $5,000,000,000,000 |

**Exposure (complexity) -> Scale Modifier**

| Band | Score Band | Modifier | Implied Value Range |
|------|-----------|----------|---------------------|
| SIMPLE | 0-20 | 0.85 | n/a |
| MODERATE | 21-40 | 0.95 | n/a |
| COMPLEX | 41-60 | 1.1 | n/a |
| HIGHLY_COMPLEX | 61-80 | 1.3 | n/a |
| EXTREMELY_COMPLEX | 81-100 | 1.6 | n/a |

### Theoretical Premium Calculation (Worked Example)
> *Per the DSI Premium Calculation Methodology v2.0, the full factor chain is:*
> *P_final = (Basis × Base Rate) × ILF_relativity × Deductible_Factor × Loss_Modifier × Exposure_Modifier*

**Worked example — Risk Tier 3 (STANDARD), Loss Tier 4 (ELEVATED), requesting the anchor limit/deductible:**

| Factor | Source | Value |
|--------|--------|-------|
| `revenue` (rating basis) | Routing-valid assumption | $10,000,000 |
| Base Rate | Risk Tier 3 (STANDARD) | 0.25% |
| **Base Premium** | `revenue` × Base Rate | **$25,000** |
| ILF relativity | Limit = anchor ($5,000,000) | 1.00 |
| Deductible factor | Deductible = anchor ($100,000) | 1.00 |
| Loss frequency modifier | Loss Tier 4 (ELEVATED) | 1.15 |
| Loss severity modifier | Loss Tier 4 (ELEVATED) | 1.15 |
| **Loss modifier** | Frequency × Severity, bounded [0.5, 1.8] | **1.32** |
| Exposure modifier | Size band MICRO | 0.50 |
| **Technical Premium** | Product of all factors | **$16,531** |

*Basis vs. limit: `revenue` is the total insured value the rate is applied to — a Base Rate of 0.25% on `revenue` is the rated cost of risk, not the policy limit. The policy Limit (anchored at $5,000,000) is the maximum payout and scales premium independently via the ILF curve; requesting a limit above the anchor lifts the ILF relativity above 1.00.*

**Loss Tier Sensitivity** — holding Risk Tier 3 and the Exposure modifier constant, the technical premium moves with the Loss tier:

| Loss Tier | Freq Mod | Sev Mod | Loss Modifier | Technical Premium |
|-----------|----------|---------|---------------|-------------------|
| 1 VERY_LOW | 0.70 | 0.80 | 0.56 | $7,000 |
| 2 LOW | 0.85 | 0.90 | 0.77 | $9,562 |
| 3 MODERATE | 1.00 | 1.00 | 1.00 | $12,500 |
| 4 ELEVATED  *(example)* | 1.15 | 1.15 | 1.32 | $16,531 |
| 5 HIGH | 1.35 | 1.40 | 1.80 | $22,500 |


---

## Model: `fi_crypto`
*Crypto exchanges, custodians, DeFi protocols, stablecoin issuers*

### Routing Protocol (Multiplexer)
- `fi_segment == CRYPTO`
- `aum >= 100000000`

### Three-Layer Weight Distribution
> *DSI requires that weights for Risk, Loss, and Exposure each sum to 1.0 across all signal groups.*

**Validation:** PASS

| Group | Risk | Loss | Exposure |
|-------|------|------|----------|
| Fintech & Digital Risk | 0.45 | 0.40 | 0.35 |
| Regulatory Framework | 0.25 | 0.30 | 0.30 |
| Corporate Footprint | 0.15 | 0.15 | 0.20 |
| Firm Stability | 0.15 | 0.15 | 0.15 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

**Group Definitions:**
- **Fintech & Digital Risk:** Fintech-specific risk — regulatory uncertainty, crypto exposure, platform risk, licensing

*Reading the table: a group's three weights are independent. The same group can be a dominant driver of one pillar and a minor input to another — e.g. a group may carry most of the Exposure weight while contributing little to Risk.*

### Signal Architecture Rationale
This configuration contains **10 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `DIRECT_OBSERVABLE` (2 signals): Highest confidence
- `INFERRED_PROXY` (8 signals): Medium confidence

**Signal Count by Group:**
- `structured_data`: 7 signals
- `public_record`: 2 signals
- `corporate_footprint`: 1 signals

**Selection Rationale:**
- 20% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Detail by Group
> *Each signal is an objectively observable data point. The weights show how strongly that signal informs each assessment pillar; correlation direction indicates whether a higher observed value increases (+) or decreases (-) the assessed exposure.*

#### Fintech & Digital Risk
*Fintech-specific risk — regulatory uncertainty, crypto exposure, platform risk, licensing*

| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `regulatory_licensing_status` | DIRECT_OBSERVABLE | 0.25 | 0.15 / 0.00 | 0.00 | + |
| `crypto_asset_exposure` | INFERRED_PROXY | 0.25 | 0.20 / 0.25 | 0.20 | + |
| `platform_technology_risk` | INFERRED_PROXY | 0.20 | 0.20 / 0.15 | 0.00 | + |
| `consumer_protection_compliance` | DIRECT_OBSERVABLE | 0.20 | 0.20 / 0.15 | 0.00 | + |
| `partner_bank_dependency` | INFERRED_PROXY | 0.10 | 0.00 / 0.10 | 0.15 | + |
| `travel_rule_compliance` | INFERRED_PROXY | 0.03 | 0.03 / 0.00 | 0.00 | - |
| `reserve_attestation_cadence` | INFERRED_PROXY | 0.03 | 0.00 / 0.03 | 0.00 | - |

#### Regulatory Framework
| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `ofac_exposure_proxy` | INFERRED_PROXY | 0.05 | 0.00 / 0.05 | 0.00 | + |
| `mixer_tumbler_interaction` | INFERRED_PROXY | 0.04 | 0.04 / 0.00 | 0.00 | + |

#### Corporate Footprint
| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `cex_dex_exposure_mix` | INFERRED_PROXY | 0.03 | 0.03 / 0.00 | 0.00 | + |

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 | Fintech & Digital Risk | 1.20 | 0.45 | 0.40 | 0.35 |
| 2 | Regulatory Framework | 0.85 | 0.25 | 0.30 | 0.30 |
| 3 | Corporate Footprint | 0.50 | 0.15 | 0.15 | 0.20 |
| 4 | Firm Stability | 0.45 | 0.15 | 0.15 | 0.15 |

**Primary Assessment Driver:** `Fintech & Digital Risk` with combined weight of 1.20
**Secondary Driver:** `Regulatory Framework` with combined weight of 0.85

### Three-Layer Pricing Translation
> *How each pillar's tier score becomes a concrete underwriting action or pricing modifier. This is the bridge between signal observation and premium.*

**Risk -> Underwriting Action & Base Rate**

| Tier | Score Band | Action | Rate / Method |
|------|-----------|--------|---------------|
| PREFERRED | 800-1000 | APPROVE | 0.08% (MULTIPLIER) |
| STANDARD_PLUS | 650-799 | APPROVE | 0.15% (MULTIPLIER) |
| STANDARD | 500-649 | REFER | 0.28% (MULTIPLIER) |
| SUBSTANDARD | 350-499 | REFER | 0.5% (MULTIPLIER) |
| DECLINE | 0-349 | DECLINE | 0.85% (MULTIPLIER) |

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
| MICRO | 0-20 | 0.5 | $0 - $500,000,000 |
| SMALL | 21-40 | 0.75 | $500,000,000 - $5,000,000,000 |
| MEDIUM | 41-60 | 1.0 | $5,000,000,000 - $50,000,000,000 |
| LARGE | 61-80 | 1.5 | $50,000,000,000 - $500,000,000,000 |
| VERY_LARGE | 81-100 | 2.5 | $500,000,000,000 - $5,000,000,000,000 |

**Exposure (complexity) -> Scale Modifier**

| Band | Score Band | Modifier | Implied Value Range |
|------|-----------|----------|---------------------|
| SIMPLE | 0-20 | 0.85 | n/a |
| MODERATE | 21-40 | 0.95 | n/a |
| COMPLEX | 41-60 | 1.1 | n/a |
| HIGHLY_COMPLEX | 61-80 | 1.3 | n/a |
| EXTREMELY_COMPLEX | 81-100 | 1.6 | n/a |

### Theoretical Premium Calculation (Worked Example)
> *Per the DSI Premium Calculation Methodology v2.0, the full factor chain is:*
> *P_final = (Basis × Base Rate) × ILF_relativity × Deductible_Factor × Loss_Modifier × Exposure_Modifier*

**Worked example — Risk Tier 3 (STANDARD), Loss Tier 4 (ELEVATED), requesting the anchor limit/deductible:**

| Factor | Source | Value |
|--------|--------|-------|
| `aum` (rating basis) | Routing-valid assumption | $300,000,000 |
| Base Rate | Risk Tier 3 (STANDARD) | 0.28% |
| **Base Premium** | `aum` × Base Rate | **$840,000** |
| ILF relativity | Limit = anchor ($10,000,000) | 1.00 |
| Deductible factor | Deductible = anchor ($1,000,000) | 1.00 |
| Loss frequency modifier | Loss Tier 4 (ELEVATED) | 1.15 |
| Loss severity modifier | Loss Tier 4 (ELEVATED) | 1.15 |
| **Loss modifier** | Frequency × Severity, bounded [0.5, 1.8] | **1.32** |
| Exposure modifier | Size band MICRO | 0.50 |
| **Technical Premium** | Product of all factors | **$555,450** |

*Basis vs. limit: `aum` is the total insured value the rate is applied to — a Base Rate of 0.28% on `aum` is the rated cost of risk, not the policy limit. The policy Limit (anchored at $10,000,000) is the maximum payout and scales premium independently via the ILF curve; requesting a limit above the anchor lifts the ILF relativity above 1.00.*

**Loss Tier Sensitivity** — holding Risk Tier 3 and the Exposure modifier constant, the technical premium moves with the Loss tier:

| Loss Tier | Freq Mod | Sev Mod | Loss Modifier | Technical Premium |
|-----------|----------|---------|---------------|-------------------|
| 1 VERY_LOW | 0.70 | 0.80 | 0.56 | $235,200 |
| 2 LOW | 0.85 | 0.90 | 0.77 | $321,300 |
| 3 MODERATE | 1.00 | 1.00 | 1.00 | $420,000 |
| 4 ELEVATED  *(example)* | 1.15 | 1.15 | 1.32 | $555,450 |
| 5 HIGH | 1.35 | 1.40 | 1.80 | $756,000 |



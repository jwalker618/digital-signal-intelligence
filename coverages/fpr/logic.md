# DSI Logic Document: `FPR`
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

## Model: `fpr_trade_credit`
*Trade credit — buyer default, insolvency, protracted default, political risk on receivables*

### Routing Protocol (Multiplexer)
- `product_type == trade_credit`
- `turnover >= 5000000`

### Three-Layer Weight Distribution
> *DSI requires that weights for Risk, Loss, and Exposure each sum to 1.0 across all signal groups.*

**Validation:** PASS

| Group | Risk | Loss | Exposure |
|-------|------|------|----------|
| Trade Credit Risk | 0.40 | 0.40 | 0.35 |
| Political Risk | 0.25 | 0.25 | 0.30 |
| Corporate Footprint | 0.20 | 0.15 | 0.20 |
| Firm Stability | 0.15 | 0.20 | 0.15 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

**Group Definitions:**
- **Trade Credit Risk:** Buyer creditworthiness, payment behaviour, country risk, concentration, trade terms
- **Political Risk:** Sovereign risk, expropriation, currency inconvertibility, contract frustration, political violence

*Reading the table: a group's three weights are independent. The same group can be a dominant driver of one pillar and a minor input to another — e.g. a group may carry most of the Exposure weight while contributing little to Risk.*

### Signal Architecture Rationale
This configuration contains **40 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `DIRECT_OBSERVABLE` (6 signals): Highest confidence
- `INFERRED_PROXY` (33 signals): Medium confidence
- `COHORT_INFERENCE` (1 signals): Lowest confidence

**Signal Count by Group:**
- `structured_data`: 35 signals
- `public_record`: 5 signals

**Selection Rationale:**
- 15% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Detail by Group
> *Each signal is an objectively observable data point. The weights show how strongly that signal informs each assessment pillar; correlation direction indicates whether a higher observed value increases (+) or decreases (-) the assessed exposure.*

#### Trade Credit Risk
*Buyer creditworthiness, payment behaviour, country risk, concentration, trade terms*

| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `buyer_creditworthiness` | DIRECT_OBSERVABLE | 0.30 | 0.25 / 0.20 | 0.00 | + |
| `payment_terms_exposure` | DIRECT_OBSERVABLE | 0.15 | 0.15 / 0.15 | 0.15 | + |
| `buyer_concentration` | DIRECT_OBSERVABLE | 0.15 | 0.00 / 0.20 | 0.20 | + |
| `country_risk_exposure` | INFERRED_PROXY | 0.20 | 0.15 / 0.20 | 0.15 | + |
| `trade_dispute_frequency` | DIRECT_OBSERVABLE | 0.10 | 0.20 / 0.10 | 0.00 | + |
| `sector_cyclicality` | COHORT_INFERENCE | 0.10 | 0.10 / 0.00 | 0.10 | + |
| `sector_credit_spread` | DIRECT_OBSERVABLE | 0.05 | 0.04 / 0.04 | 0.00 | + |
| `fpr_primary_derived_01` | INFERRED_PROXY | 0.01 | 0.01 / 0.00 | 0.00 | + |
| `fpr_primary_derived_02` | INFERRED_PROXY | 0.01 | 0.00 / 0.00 | 0.00 | + |
| `fpr_primary_derived_03` | INFERRED_PROXY | 0.01 | 0.00 / 0.01 | 0.00 | + |
| `fpr_primary_derived_04` | INFERRED_PROXY | 0.01 | 0.01 / 0.00 | 0.00 | + |
| `fpr_primary_derived_05` | INFERRED_PROXY | 0.01 | 0.00 / 0.00 | 0.00 | + |
| `fpr_primary_derived_06` | INFERRED_PROXY | 0.01 | 0.00 / 0.01 | 0.00 | + |
| `fpr_primary_derived_07` | INFERRED_PROXY | 0.01 | 0.01 / 0.00 | 0.00 | + |
| `fpr_primary_derived_08` | INFERRED_PROXY | 0.01 | 0.00 / 0.00 | 0.00 | + |
| `fpr_primary_derived_09` | INFERRED_PROXY | 0.01 | 0.00 / 0.01 | 0.00 | + |
| `fpr_primary_derived_10` | INFERRED_PROXY | 0.01 | 0.01 / 0.00 | 0.00 | + |
| `fpr_primary_derived_11` | INFERRED_PROXY | 0.01 | 0.00 / 0.00 | 0.00 | + |
| `fpr_primary_derived_12` | INFERRED_PROXY | 0.01 | 0.00 / 0.01 | 0.00 | + |
| `fpr_primary_derived_13` | INFERRED_PROXY | 0.01 | 0.01 / 0.00 | 0.00 | + |
| `fpr_primary_derived_14` | INFERRED_PROXY | 0.01 | 0.00 / 0.00 | 0.00 | + |
| `fpr_primary_derived_15` | INFERRED_PROXY | 0.01 | 0.00 / 0.01 | 0.00 | + |
| `fpr_primary_derived_16` | INFERRED_PROXY | 0.01 | 0.01 / 0.00 | 0.00 | + |
| `fpr_primary_derived_17` | INFERRED_PROXY | 0.01 | 0.00 / 0.00 | 0.00 | + |
| `fpr_primary_derived_18` | INFERRED_PROXY | 0.01 | 0.00 / 0.01 | 0.00 | + |
| `fpr_primary_derived_19` | INFERRED_PROXY | 0.01 | 0.01 / 0.00 | 0.00 | + |
| `fpr_primary_derived_20` | INFERRED_PROXY | 0.01 | 0.00 / 0.00 | 0.00 | + |
| `fpr_primary_derived_21` | INFERRED_PROXY | 0.01 | 0.00 / 0.01 | 0.00 | + |
| `fpr_primary_derived_22` | INFERRED_PROXY | 0.01 | 0.01 / 0.00 | 0.00 | + |
| `fpr_primary_derived_23` | INFERRED_PROXY | 0.01 | 0.00 / 0.00 | 0.00 | + |
| `fpr_primary_derived_24` | INFERRED_PROXY | 0.01 | 0.00 / 0.01 | 0.00 | + |
| `fpr_primary_derived_25` | INFERRED_PROXY | 0.01 | 0.01 / 0.00 | 0.00 | + |
| `fpr_primary_derived_26` | INFERRED_PROXY | 0.01 | 0.00 / 0.00 | 0.00 | + |
| `fpr_primary_derived_27` | INFERRED_PROXY | 0.01 | 0.00 / 0.01 | 0.00 | + |
| `fpr_primary_derived_28` | INFERRED_PROXY | 0.01 | 0.01 / 0.00 | 0.00 | + |

#### Political Risk
*Sovereign risk, expropriation, currency inconvertibility, contract frustration, political violence*

| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `expropriation_risk` | INFERRED_PROXY | 0.25 | 0.15 / 0.30 | 0.00 | + |
| `currency_inconvertibility` | INFERRED_PROXY | 0.20 | 0.20 / 0.15 | 0.00 | + |
| `contract_frustration` | INFERRED_PROXY | 0.15 | 0.15 / 0.15 | 0.10 | + |
| `political_violence_exposure` | INFERRED_PROXY | 0.15 | 0.15 / 0.20 | 0.00 | + |

**Categorical signal `sovereign_risk_rating`** — proxy tier: `DIRECT_OBSERVABLE`, source: `metadata.sovereign_risk_rating`

| Category | Label | Applied Factor |
|----------|-------|----------------|
| `LOW` | Low Risk (OECD Core) | 0.6 |
| `MODERATE` | Moderate (Emerging Market Stable) | 1.0 |
| `HIGH` | High (Frontier/Volatile) | 1.5 |
| `SEVERE` | Severe (Conflict/Failed State) | 2.2 |

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 | Trade Credit Risk | 1.15 | 0.40 | 0.40 | 0.35 |
| 2 | Political Risk | 0.80 | 0.25 | 0.25 | 0.30 |
| 3 | Corporate Footprint | 0.55 | 0.20 | 0.15 | 0.20 |
| 4 | Firm Stability | 0.50 | 0.15 | 0.20 | 0.15 |

**Primary Assessment Driver:** `Trade Credit Risk` with combined weight of 1.15
**Secondary Driver:** `Political Risk` with combined weight of 0.80

### Three-Layer Pricing Translation
> *How each pillar's tier score becomes a concrete underwriting action or pricing modifier. This is the bridge between signal observation and premium.*

**Risk -> Underwriting Action & Base Rate**

| Tier | Score Band | Action | Rate / Method |
|------|-----------|--------|---------------|
| PREFERRED | 800-1000 | APPROVE | 0.2% (MULTIPLIER) |
| STANDARD_PLUS | 650-799 | APPROVE | 0.4% (MULTIPLIER) |
| STANDARD | 500-649 | REFER | 0.7% (MULTIPLIER) |
| SUBSTANDARD | 350-499 | REFER | 1.2% (MULTIPLIER) |
| DECLINE | 0-349 | DECLINE | 2% (MULTIPLIER) |

**Loss -> Frequency & Severity Modifiers**

| Tier | Score Band | Frequency Modifier | Severity Modifier |
|------|-----------|--------------------|-------------------|
| VERY_LOW | 80-100 | 0.7 | 0.8 |
| LOW | 60-79 | 0.85 | 0.9 |
| MODERATE | 40-59 | 1.0 | 1.0 |
| ELEVATED | 20-39 | 1.15 | 1.15 |
| HIGH | 0-19 | 1.35 | 1.4 |

*Loss modifier is bounded: floor 0.45, cap 2.0.*

**Exposure (size) -> Scale Modifier**

| Band | Score Band | Modifier | Implied Value Range |
|------|-----------|----------|---------------------|
| MICRO | 0-20 | 0.5 | $0 - $5,000,000 |
| SMALL | 21-40 | 0.75 | $5,000,000 - $25,000,000 |
| MEDIUM | 41-60 | 1.0 | $25,000,000 - $100,000,000 |
| LARGE | 61-80 | 1.5 | $100,000,000 - $500,000,000 |
| VERY_LARGE | 81-100 | 2.5 | $500,000,000 - $5,000,000,000 |

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

**1. The Pricing Anchor:** The Base Rate of `0.7000000000000001%` on `turnover` purchases exactly a `$5,000,000` Limit with a `$100,000` Deductible.
**2. Theoretical Execution:**
  - Assume `turnover` = $10,000,000
  - Base Premium = $10,000,000 × 0.007 = **$70,000**
  - If the client requests the Anchor Limit/Deductible, the factors are 1.00, resulting in a technical premium of **$70,000**.

---

## Model: `fpr_political_risk`
*Political risk — expropriation, currency inconvertibility, political violence, contract frustration*

### Routing Protocol (Multiplexer)
- `product_type in ['political_risk', 'political_violence']`

### Three-Layer Weight Distribution
> *DSI requires that weights for Risk, Loss, and Exposure each sum to 1.0 across all signal groups.*

**Validation:** PASS

| Group | Risk | Loss | Exposure |
|-------|------|------|----------|
| Political Risk | 0.65 | 0.70 | 0.60 |
| Corporate Footprint | 0.20 | 0.15 | 0.25 |
| Firm Stability | 0.15 | 0.15 | 0.15 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

**Group Definitions:**
- **Political Risk:** Sovereign risk, expropriation, currency inconvertibility, contract frustration, political violence

*Reading the table: a group's three weights are independent. The same group can be a dominant driver of one pillar and a minor input to another — e.g. a group may carry most of the Exposure weight while contributing little to Risk.*

### Signal Architecture Rationale
This configuration contains **10 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `DIRECT_OBSERVABLE` (5 signals): Highest confidence
- `INFERRED_PROXY` (5 signals): Medium confidence

**Signal Count by Group:**
- `public_record`: 10 signals

**Selection Rationale:**
- 50% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Detail by Group
> *Each signal is an objectively observable data point. The weights show how strongly that signal informs each assessment pillar; correlation direction indicates whether a higher observed value increases (+) or decreases (-) the assessed exposure.*

#### Political Risk
*Sovereign risk, expropriation, currency inconvertibility, contract frustration, political violence*

| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `expropriation_risk` | INFERRED_PROXY | 0.25 | 0.15 / 0.30 | 0.00 | + |
| `currency_inconvertibility` | INFERRED_PROXY | 0.20 | 0.20 / 0.15 | 0.00 | + |
| `contract_frustration` | INFERRED_PROXY | 0.15 | 0.15 / 0.15 | 0.10 | + |
| `political_violence_exposure` | INFERRED_PROXY | 0.15 | 0.15 / 0.20 | 0.00 | + |
| `acled_incident_density` | INFERRED_PROXY | 0.05 | 0.04 / 0.05 | 0.00 | + |
| `wb_wgi_score` | DIRECT_OBSERVABLE | 0.05 | 0.04 / 0.04 | 0.00 | - |
| `ofac_country_tier` | DIRECT_OBSERVABLE | 0.05 | 0.04 / 0.04 | 0.00 | + |
| `capital_controls_watchlist` | DIRECT_OBSERVABLE | 0.04 | 0.03 / 0.03 | 0.00 | + |
| `bit_treaty_coverage` | DIRECT_OBSERVABLE | 0.04 | 0.03 / 0.03 | 0.00 | - |

**Categorical signal `sovereign_risk_rating`** — proxy tier: `DIRECT_OBSERVABLE`, source: `metadata.sovereign_risk_rating`

| Category | Label | Applied Factor |
|----------|-------|----------------|
| `LOW` | Low Risk (OECD Core) | 0.6 |
| `MODERATE` | Moderate (Emerging Market Stable) | 1.0 |
| `HIGH` | High (Frontier/Volatile) | 1.5 |
| `SEVERE` | Severe (Conflict/Failed State) | 2.2 |

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 | Political Risk | 1.95 | 0.65 | 0.70 | 0.60 |
| 2 | Corporate Footprint | 0.60 | 0.20 | 0.15 | 0.25 |
| 3 | Firm Stability | 0.45 | 0.15 | 0.15 | 0.15 |

**Primary Assessment Driver:** `Political Risk` with combined weight of 1.95
**Secondary Driver:** `Corporate Footprint` with combined weight of 0.60

### Three-Layer Pricing Translation
> *How each pillar's tier score becomes a concrete underwriting action or pricing modifier. This is the bridge between signal observation and premium.*

**Risk -> Underwriting Action & Base Rate**

| Tier | Score Band | Action | Rate / Method |
|------|-----------|--------|---------------|
| PREFERRED | 800-1000 | APPROVE | 0.5% (MULTIPLIER) |
| STANDARD_PLUS | 650-799 | APPROVE | 1.2% (MULTIPLIER) |
| STANDARD | 500-649 | REFER | 2.2% (MULTIPLIER) |
| SUBSTANDARD | 350-499 | REFER | 3.8% (MULTIPLIER) |
| DECLINE | 0-349 | DECLINE | 6% (MULTIPLIER) |

**Loss -> Frequency & Severity Modifiers**

| Tier | Score Band | Frequency Modifier | Severity Modifier |
|------|-----------|--------------------|-------------------|
| VERY_LOW | 80-100 | 0.7 | 0.8 |
| LOW | 60-79 | 0.85 | 0.9 |
| MODERATE | 40-59 | 1.0 | 1.0 |
| ELEVATED | 20-39 | 1.15 | 1.15 |
| HIGH | 0-19 | 1.35 | 1.4 |

*Loss modifier is bounded: floor 0.45, cap 2.0.*

**Exposure (size) -> Scale Modifier**

| Band | Score Band | Modifier | Implied Value Range |
|------|-----------|----------|---------------------|
| MICRO | 0-20 | 0.5 | $0 - $5,000,000 |
| SMALL | 21-40 | 0.75 | $5,000,000 - $25,000,000 |
| MEDIUM | 41-60 | 1.0 | $25,000,000 - $100,000,000 |
| LARGE | 61-80 | 1.5 | $100,000,000 - $500,000,000 |
| VERY_LARGE | 81-100 | 2.5 | $500,000,000 - $5,000,000,000 |

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

**1. The Pricing Anchor:** The Base Rate of `2.1999999999999997%` on `limit` purchases exactly a `$5,000,000` Limit with a `$100,000` Deductible.
**2. Theoretical Execution:**
  - Assume `limit` = $10,000,000
  - Base Premium = $10,000,000 × 0.022 = **$220,000**
  - If the client requests the Anchor Limit/Deductible, the factors are 1.00, resulting in a technical premium of **$220,000**.

---

## Model: `fpr_surety`
*Surety bonds — performance, payment, bid, maintenance; contractor financial strength focus*

### Routing Protocol (Multiplexer)
- `product_type in ['surety_bond', 'contract_bond']`

### Three-Layer Weight Distribution
> *DSI requires that weights for Risk, Loss, and Exposure each sum to 1.0 across all signal groups.*

**Validation:** PASS

| Group | Risk | Loss | Exposure |
|-------|------|------|----------|
| Surety & Bond Risk | 0.45 | 0.45 | 0.35 |
| Corporate Footprint | 0.25 | 0.20 | 0.30 |
| Firm Stability | 0.20 | 0.20 | 0.20 |
| Regulatory Standing | 0.10 | 0.15 | 0.15 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

**Group Definitions:**
- **Surety & Bond Risk:** Principal financial strength, project execution capability, bonding capacity, default history

*Reading the table: a group's three weights are independent. The same group can be a dominant driver of one pillar and a minor input to another — e.g. a group may carry most of the Exposure weight while contributing little to Risk.*

### Signal Architecture Rationale
This configuration contains **5 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `DIRECT_OBSERVABLE` (4 signals): Highest confidence
- `INFERRED_PROXY` (1 signals): Medium confidence

**Signal Count by Group:**
- `structured_data`: 5 signals

**Selection Rationale:**
- 80% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Detail by Group
> *Each signal is an objectively observable data point. The weights show how strongly that signal informs each assessment pillar; correlation direction indicates whether a higher observed value increases (+) or decreases (-) the assessed exposure.*

#### Surety & Bond Risk
*Principal financial strength, project execution capability, bonding capacity, default history*

| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `principal_financial_strength` | DIRECT_OBSERVABLE | 0.30 | 0.25 / 0.15 | 0.00 | + |
| `project_execution_track_record` | DIRECT_OBSERVABLE | 0.25 | 0.20 / 0.10 | 0.00 | + |
| `backlog_to_capacity` | DIRECT_OBSERVABLE | 0.20 | 0.15 / 0.15 | 0.15 | + |
| `bond_default_history` | DIRECT_OBSERVABLE | 0.15 | 0.25 / 0.20 | 0.00 | + |
| `obligee_complexity` | INFERRED_PROXY | 0.10 | 0.00 / 0.10 | 0.20 | + |

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 | Surety & Bond Risk | 1.25 | 0.45 | 0.45 | 0.35 |
| 2 | Corporate Footprint | 0.75 | 0.25 | 0.20 | 0.30 |
| 3 | Firm Stability | 0.60 | 0.20 | 0.20 | 0.20 |
| 4 | Regulatory Standing | 0.40 | 0.10 | 0.15 | 0.15 |

**Primary Assessment Driver:** `Surety & Bond Risk` with combined weight of 1.25
**Secondary Driver:** `Corporate Footprint` with combined weight of 0.75

### Three-Layer Pricing Translation
> *How each pillar's tier score becomes a concrete underwriting action or pricing modifier. This is the bridge between signal observation and premium.*

**Risk -> Underwriting Action & Base Rate**

| Tier | Score Band | Action | Rate / Method |
|------|-----------|--------|---------------|
| PREFERRED | 800-1000 | APPROVE | 0.8% (MULTIPLIER) |
| STANDARD_PLUS | 650-799 | APPROVE | 1.5% (MULTIPLIER) |
| STANDARD | 500-649 | REFER | 2.5% (MULTIPLIER) |
| SUBSTANDARD | 350-499 | REFER | 4% (MULTIPLIER) |
| DECLINE | 0-349 | DECLINE | 6.5% (MULTIPLIER) |

**Loss -> Frequency & Severity Modifiers**

| Tier | Score Band | Frequency Modifier | Severity Modifier |
|------|-----------|--------------------|-------------------|
| VERY_LOW | 80-100 | 0.7 | 0.8 |
| LOW | 60-79 | 0.85 | 0.9 |
| MODERATE | 40-59 | 1.0 | 1.0 |
| ELEVATED | 20-39 | 1.15 | 1.15 |
| HIGH | 0-19 | 1.35 | 1.4 |

*Loss modifier is bounded: floor 0.45, cap 2.0.*

**Exposure (size) -> Scale Modifier**

| Band | Score Band | Modifier | Implied Value Range |
|------|-----------|----------|---------------------|
| MICRO | 0-20 | 0.5 | $0 - $5,000,000 |
| SMALL | 21-40 | 0.75 | $5,000,000 - $25,000,000 |
| MEDIUM | 41-60 | 1.0 | $25,000,000 - $100,000,000 |
| LARGE | 61-80 | 1.5 | $100,000,000 - $500,000,000 |
| VERY_LARGE | 81-100 | 2.5 | $500,000,000 - $5,000,000,000 |

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

**1. The Pricing Anchor:** The Base Rate of `2.5%` on `bond_amount` purchases exactly a `$5,000,000` Limit with a `$50,000` Deductible.
**2. Theoretical Execution:**
  - Assume `bond_amount` = $10,000,000
  - Base Premium = $10,000,000 × 0.025 = **$250,000**
  - If the client requests the Anchor Limit/Deductible, the factors are 1.00, resulting in a technical premium of **$250,000**.

---

## Model: `fpr_kidnap_ransom`
*K&R — kidnap, ransom, extortion, detention, hijack; crisis response included*

### Routing Protocol (Multiplexer)
- `product_type == kidnap_ransom`

### Three-Layer Weight Distribution
> *DSI requires that weights for Risk, Loss, and Exposure each sum to 1.0 across all signal groups.*

**Validation:** PASS

| Group | Risk | Loss | Exposure |
|-------|------|------|----------|
| Kidnap & Ransom Risk | 0.70 | 0.65 | 0.60 |
| Corporate Footprint | 0.20 | 0.20 | 0.25 |
| Firm Stability | 0.10 | 0.15 | 0.15 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

**Group Definitions:**
- **Kidnap & Ransom Risk:** Travel exposure, country threat, executive protection, crisis response capability

*Reading the table: a group's three weights are independent. The same group can be a dominant driver of one pillar and a minor input to another — e.g. a group may carry most of the Exposure weight while contributing little to Risk.*

### Signal Architecture Rationale
This configuration contains **13 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `DIRECT_OBSERVABLE` (4 signals): Highest confidence
- `INFERRED_PROXY` (9 signals): Medium confidence

**Signal Count by Group:**
- `public_record`: 11 signals
- `behavioural`: 1 signals
- `corporate_footprint`: 1 signals

**Selection Rationale:**
- 31% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Detail by Group
> *Each signal is an objectively observable data point. The weights show how strongly that signal informs each assessment pillar; correlation direction indicates whether a higher observed value increases (+) or decreases (-) the assessed exposure.*

#### Kidnap & Ransom Risk
*Travel exposure, country threat, executive protection, crisis response capability*

| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `expropriation_risk` | INFERRED_PROXY | 0.25 | 0.15 / 0.30 | 0.00 | + |
| `currency_inconvertibility` | INFERRED_PROXY | 0.20 | 0.20 / 0.15 | 0.00 | + |
| `contract_frustration` | INFERRED_PROXY | 0.15 | 0.15 / 0.15 | 0.10 | + |
| `political_violence_exposure` | INFERRED_PROXY | 0.15 | 0.15 / 0.20 | 0.00 | + |
| `travel_exposure_profile` | DIRECT_OBSERVABLE | 0.25 | 0.25 / 0.00 | 0.20 | + |
| `executive_protection` | DIRECT_OBSERVABLE | 0.25 | 0.15 / 0.15 | 0.00 | + |
| `crisis_response_capability` | INFERRED_PROXY | 0.20 | 0.00 / 0.25 | 0.00 | + |
| `expatriate_population` | DIRECT_OBSERVABLE | 0.10 | 0.15 / 0.00 | 0.15 | + |
| `acled_kfr_rate_country` | INFERRED_PROXY | 0.06 | 0.05 / 0.05 | 0.00 | + |

**Categorical signal `sovereign_risk_rating`** — proxy tier: `DIRECT_OBSERVABLE`, source: `metadata.sovereign_risk_rating`

| Category | Label | Applied Factor |
|----------|-------|----------------|
| `LOW` | Low Risk (OECD Core) | 0.6 |
| `MODERATE` | Moderate (Emerging Market Stable) | 1.0 |
| `HIGH` | High (Frontier/Volatile) | 1.5 |
| `SEVERE` | Severe (Conflict/Failed State) | 2.2 |

**Categorical signal `country_threat_level`** — proxy tier: `INFERRED_PROXY`, source: `metadata.kr_threat_level`

| Category | Label | Applied Factor |
|----------|-------|----------------|
| `LOW` | Low Threat | 0.6 |
| `MODERATE` | Moderate Threat | 1.0 |
| `HIGH` | High Threat | 1.5 |
| `EXTREME` | Extreme Threat | 2.2 |

#### Corporate Footprint
| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `executive_exposure_footprint` | INFERRED_PROXY | 0.04 | 0.03 / 0.03 | 0.00 | + |

#### Firm Stability
| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `travel_pattern_density` | INFERRED_PROXY | 0.05 | 0.04 / 0.04 | 0.00 | + |

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 | Kidnap & Ransom Risk | 1.95 | 0.70 | 0.65 | 0.60 |
| 2 | Corporate Footprint | 0.65 | 0.20 | 0.20 | 0.25 |
| 3 | Firm Stability | 0.40 | 0.10 | 0.15 | 0.15 |

**Primary Assessment Driver:** `Kidnap & Ransom Risk` with combined weight of 1.95
**Secondary Driver:** `Corporate Footprint` with combined weight of 0.65

### Three-Layer Pricing Translation
> *How each pillar's tier score becomes a concrete underwriting action or pricing modifier. This is the bridge between signal observation and premium.*

**Risk -> Underwriting Action & Base Rate**

| Tier | Score Band | Action | Rate / Method |
|------|-----------|--------|---------------|
| PREFERRED | 800-1000 | APPROVE | 0.5% (MULTIPLIER) |
| STANDARD_PLUS | 650-799 | APPROVE | 1% (MULTIPLIER) |
| STANDARD | 500-649 | REFER | 1.8% (MULTIPLIER) |
| SUBSTANDARD | 350-499 | REFER | 3% (MULTIPLIER) |
| DECLINE | 0-349 | DECLINE | 5% (MULTIPLIER) |

**Loss -> Frequency & Severity Modifiers**

| Tier | Score Band | Frequency Modifier | Severity Modifier |
|------|-----------|--------------------|-------------------|
| VERY_LOW | 80-100 | 0.7 | 0.8 |
| LOW | 60-79 | 0.85 | 0.9 |
| MODERATE | 40-59 | 1.0 | 1.0 |
| ELEVATED | 20-39 | 1.15 | 1.15 |
| HIGH | 0-19 | 1.35 | 1.4 |

*Loss modifier is bounded: floor 0.45, cap 2.0.*

**Exposure (size) -> Scale Modifier**

| Band | Score Band | Modifier | Implied Value Range |
|------|-----------|----------|---------------------|
| MICRO | 0-20 | 0.5 | $0 - $5,000,000 |
| SMALL | 21-40 | 0.75 | $5,000,000 - $25,000,000 |
| MEDIUM | 41-60 | 1.0 | $25,000,000 - $100,000,000 |
| LARGE | 61-80 | 1.5 | $100,000,000 - $500,000,000 |
| VERY_LARGE | 81-100 | 2.5 | $500,000,000 - $5,000,000,000 |

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

**1. The Pricing Anchor:** The Base Rate of `1.7999999999999998%` on `limit` purchases exactly a `$5,000,000` Limit with a `$50,000` Deductible.
**2. Theoretical Execution:**
  - Assume `limit` = $10,000,000
  - Base Premium = $10,000,000 × 0.018 = **$180,000**
  - If the client requests the Anchor Limit/Deductible, the factors are 1.00, resulting in a technical premium of **$180,000**.

---

## Model: `fpr_sme`
*Simplified FPR for smaller exposures — trade credit + political risk combined*

### Routing Protocol (Multiplexer)
- `product_type in ['trade_credit', 'political_risk']`
- `limit < 5000000`

### Three-Layer Weight Distribution
> *DSI requires that weights for Risk, Loss, and Exposure each sum to 1.0 across all signal groups.*

**Validation:** PASS

| Group | Risk | Loss | Exposure |
|-------|------|------|----------|
| Trade Credit Risk | 0.30 | 0.30 | 0.25 |
| Political Risk | 0.35 | 0.35 | 0.35 |
| Corporate Footprint | 0.20 | 0.15 | 0.25 |
| Firm Stability | 0.15 | 0.20 | 0.15 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

**Group Definitions:**
- **Trade Credit Risk:** Buyer creditworthiness, payment behaviour, country risk, concentration, trade terms
- **Political Risk:** Sovereign risk, expropriation, currency inconvertibility, contract frustration, political violence

*Reading the table: a group's three weights are independent. The same group can be a dominant driver of one pillar and a minor input to another — e.g. a group may carry most of the Exposure weight while contributing little to Risk.*

### Signal Architecture Rationale
This configuration contains **11 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `DIRECT_OBSERVABLE` (5 signals): Highest confidence
- `INFERRED_PROXY` (5 signals): Medium confidence
- `COHORT_INFERENCE` (1 signals): Lowest confidence

**Signal Count by Group:**
- `structured_data`: 6 signals
- `public_record`: 5 signals

**Selection Rationale:**
- 45% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Detail by Group
> *Each signal is an objectively observable data point. The weights show how strongly that signal informs each assessment pillar; correlation direction indicates whether a higher observed value increases (+) or decreases (-) the assessed exposure.*

#### Trade Credit Risk
*Buyer creditworthiness, payment behaviour, country risk, concentration, trade terms*

| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `buyer_creditworthiness` | DIRECT_OBSERVABLE | 0.30 | 0.25 / 0.20 | 0.00 | + |
| `payment_terms_exposure` | DIRECT_OBSERVABLE | 0.15 | 0.15 / 0.15 | 0.15 | + |
| `buyer_concentration` | DIRECT_OBSERVABLE | 0.15 | 0.00 / 0.20 | 0.20 | + |
| `country_risk_exposure` | INFERRED_PROXY | 0.20 | 0.15 / 0.20 | 0.15 | + |
| `trade_dispute_frequency` | DIRECT_OBSERVABLE | 0.10 | 0.20 / 0.10 | 0.00 | + |
| `sector_cyclicality` | COHORT_INFERENCE | 0.10 | 0.10 / 0.00 | 0.10 | + |

#### Political Risk
*Sovereign risk, expropriation, currency inconvertibility, contract frustration, political violence*

| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `expropriation_risk` | INFERRED_PROXY | 0.25 | 0.15 / 0.30 | 0.00 | + |
| `currency_inconvertibility` | INFERRED_PROXY | 0.20 | 0.20 / 0.15 | 0.00 | + |
| `contract_frustration` | INFERRED_PROXY | 0.15 | 0.15 / 0.15 | 0.10 | + |
| `political_violence_exposure` | INFERRED_PROXY | 0.15 | 0.15 / 0.20 | 0.00 | + |

**Categorical signal `sovereign_risk_rating`** — proxy tier: `DIRECT_OBSERVABLE`, source: `metadata.sovereign_risk_rating`

| Category | Label | Applied Factor |
|----------|-------|----------------|
| `LOW` | Low Risk (OECD Core) | 0.6 |
| `MODERATE` | Moderate (Emerging Market Stable) | 1.0 |
| `HIGH` | High (Frontier/Volatile) | 1.5 |
| `SEVERE` | Severe (Conflict/Failed State) | 2.2 |

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 | Political Risk | 1.05 | 0.35 | 0.35 | 0.35 |
| 2 | Trade Credit Risk | 0.85 | 0.30 | 0.30 | 0.25 |
| 3 | Corporate Footprint | 0.60 | 0.20 | 0.15 | 0.25 |
| 4 | Firm Stability | 0.50 | 0.15 | 0.20 | 0.15 |

**Primary Assessment Driver:** `Political Risk` with combined weight of 1.05
**Secondary Driver:** `Trade Credit Risk` with combined weight of 0.85

### Three-Layer Pricing Translation
> *How each pillar's tier score becomes a concrete underwriting action or pricing modifier. This is the bridge between signal observation and premium.*

**Risk -> Underwriting Action & Base Rate**

| Tier | Score Band | Action | Rate / Method |
|------|-----------|--------|---------------|
| PREFERRED | 800-1000 | APPROVE | 0.8% (MULTIPLIER) |
| STANDARD_PLUS | 650-799 | APPROVE | 1.5% (MULTIPLIER) |
| STANDARD | 500-649 | REFER | 2.5% (MULTIPLIER) |
| SUBSTANDARD | 350-499 | REFER | 4.2% (MULTIPLIER) |
| DECLINE | 0-349 | DECLINE | 6.5% (MULTIPLIER) |

**Loss -> Frequency & Severity Modifiers**

| Tier | Score Band | Frequency Modifier | Severity Modifier |
|------|-----------|--------------------|-------------------|
| VERY_LOW | 80-100 | 0.7 | 0.8 |
| LOW | 60-79 | 0.85 | 0.9 |
| MODERATE | 40-59 | 1.0 | 1.0 |
| ELEVATED | 20-39 | 1.15 | 1.15 |
| HIGH | 0-19 | 1.35 | 1.4 |

*Loss modifier is bounded: floor 0.45, cap 2.0.*

**Exposure (size) -> Scale Modifier**

| Band | Score Band | Modifier | Implied Value Range |
|------|-----------|----------|---------------------|
| MICRO | 0-20 | 0.5 | $0 - $5,000,000 |
| SMALL | 21-40 | 0.75 | $5,000,000 - $25,000,000 |
| MEDIUM | 41-60 | 1.0 | $25,000,000 - $100,000,000 |
| LARGE | 61-80 | 1.5 | $100,000,000 - $500,000,000 |
| VERY_LARGE | 81-100 | 2.5 | $500,000,000 - $5,000,000,000 |

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

**1. The Pricing Anchor:** The Base Rate of `2.5%` on `limit` purchases exactly a `$1,000,000` Limit with a `$25,000` Deductible.
**2. Theoretical Execution:**
  - Assume `limit` = $10,000,000
  - Base Premium = $10,000,000 × 0.025 = **$250,000**
  - If the client requests the Anchor Limit/Deductible, the factors are 1.00, resulting in a technical premium of **$250,000**.


# DSI Logic Document: `PRODLIB`
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

## Model: `prodlib_consumer_goods`
*CPSC-regulated consumer goods*

### Routing Protocol (Multiplexer)
- `product_category == consumer_goods`

### Three-Layer Weight Distribution
> *DSI requires that weights for Risk, Loss, and Exposure each sum to 1.0 across all signal groups.*

**Validation:** PASS

| Group | Risk | Loss | Exposure |
|-------|------|------|----------|
|  | 0.43 | 0.43 | 0.43 |
|  | 0.20 | 0.20 | 0.20 |
|  | 0.18 | 0.18 | 0.18 |
|  | 0.18 | 0.18 | 0.18 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

*Reading the table: a group's three weights are independent. The same group can be a dominant driver of one pillar and a minor input to another — e.g. a group may carry most of the Exposure weight while contributing little to Risk.*

### Signal Architecture Rationale
This configuration contains **40 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `DIRECT_OBSERVABLE` (9 signals): Highest confidence
- `INFERRED_PROXY` (31 signals): Medium confidence

**Signal Count by Group:**
- `structured_data`: 14 signals
- `technical_infrastructure`: 13 signals
- `corporate_footprint`: 7 signals
- `network_authority`: 6 signals

**Selection Rationale:**
- 22% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Detail by Group
> *Each signal is an objectively observable data point. The weights show how strongly that signal informs each assessment pillar; correlation direction indicates whether a higher observed value increases (+) or decreases (-) the assessed exposure.*

#### technical_infrastructure
| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `business_continuity` | INFERRED_PROXY | 0.17 | 0.12 / 0.05 | 0.00 | + |
| `disaster_recovery` | INFERRED_PROXY | 0.17 | 0.12 / 0.05 | 0.00 | + |
| `operational_resilience` | INFERRED_PROXY | 0.17 | 0.12 / 0.05 | 0.00 | + |
| `technology_stack` | INFERRED_PROXY | 0.17 | 0.12 / 0.05 | 0.00 | + |
| `process_maturity` | INFERRED_PROXY | 0.17 | 0.12 / 0.05 | 0.00 | + |
| `quality_management` | INFERRED_PROXY | 0.17 | 0.12 / 0.05 | 0.00 | + |
| `security_headers` | DIRECT_OBSERVABLE | 0.14 | 0.10 / 0.04 | 0.07 | + |
| `tls_configuration` | DIRECT_OBSERVABLE | 0.14 | 0.10 / 0.04 | 0.07 | + |
| `email_authentication` | DIRECT_OBSERVABLE | 0.14 | 0.10 / 0.04 | 0.07 | + |
| `dns_security` | DIRECT_OBSERVABLE | 0.14 | 0.10 / 0.04 | 0.07 | + |
| `web_security` | DIRECT_OBSERVABLE | 0.14 | 0.10 / 0.04 | 0.07 | + |
| `ssl_certificate` | DIRECT_OBSERVABLE | 0.14 | 0.10 / 0.04 | 0.07 | + |
| `content_security_policy` | DIRECT_OBSERVABLE | 0.14 | 0.10 / 0.04 | 0.07 | + |

#### network_authority
| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `customer_quality` | INFERRED_PROXY | 0.17 | 0.12 / 0.05 | 0.08 | + |
| `partner_ecosystem` | INFERRED_PROXY | 0.17 | 0.12 / 0.05 | 0.08 | + |
| `certification_status` | INFERRED_PROXY | 0.17 | 0.12 / 0.05 | 0.08 | + |
| `vendor_relationships` | INFERRED_PROXY | 0.17 | 0.12 / 0.05 | 0.08 | + |
| `industry_associations` | INFERRED_PROXY | 0.17 | 0.12 / 0.05 | 0.08 | + |
| `supply_chain_visibility` | INFERRED_PROXY | 0.17 | 0.12 / 0.05 | 0.08 | + |

#### structured_data
| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `revenue_growth` | INFERRED_PROXY | 0.14 | 0.10 / 0.04 | 0.00 | + |
| `profitability` | INFERRED_PROXY | 0.14 | 0.10 / 0.04 | 0.00 | + |
| `liquidity_ratio` | INFERRED_PROXY | 0.14 | 0.10 / 0.04 | 0.00 | + |
| `debt_ratio` | INFERRED_PROXY | 0.14 | 0.10 / 0.04 | 0.00 | + |
| `credit_rating` | DIRECT_OBSERVABLE | 0.14 | 0.10 / 0.04 | 0.00 | + |
| `stock_performance` | DIRECT_OBSERVABLE | 0.14 | 0.10 / 0.04 | 0.00 | + |
| `funding_status` | INFERRED_PROXY | 0.14 | 0.10 / 0.04 | 0.00 | + |
| `prodlib_primary_derived_01` | INFERRED_PROXY | 0.01 | 0.01 / 0.00 | 0.00 | + |
| `prodlib_primary_derived_02` | INFERRED_PROXY | 0.01 | 0.00 / 0.00 | 0.00 | + |
| `prodlib_primary_derived_03` | INFERRED_PROXY | 0.01 | 0.00 / 0.01 | 0.00 | + |
| `prodlib_primary_derived_04` | INFERRED_PROXY | 0.01 | 0.01 / 0.00 | 0.00 | + |
| `prodlib_primary_derived_05` | INFERRED_PROXY | 0.01 | 0.00 / 0.00 | 0.00 | + |
| `prodlib_primary_derived_06` | INFERRED_PROXY | 0.01 | 0.00 / 0.01 | 0.00 | + |
| `prodlib_primary_derived_07` | INFERRED_PROXY | 0.01 | 0.01 / 0.00 | 0.00 | + |

#### corporate_footprint
| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `website_quality` | INFERRED_PROXY | 0.14 | 0.10 / 0.04 | 0.07 | + |
| `security_disclosure` | INFERRED_PROXY | 0.14 | 0.10 / 0.04 | 0.07 | + |
| `leadership_visibility` | INFERRED_PROXY | 0.14 | 0.10 / 0.04 | 0.07 | + |
| `social_presence` | INFERRED_PROXY | 0.14 | 0.10 / 0.04 | 0.07 | + |
| `brand_reputation` | INFERRED_PROXY | 0.14 | 0.10 / 0.04 | 0.07 | + |
| `media_coverage` | INFERRED_PROXY | 0.14 | 0.10 / 0.04 | 0.07 | + |
| `investor_relations` | INFERRED_PROXY | 0.14 | 0.10 / 0.04 | 0.07 | + |

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 |  | 1.30 | 0.43 | 0.43 | 0.43 |
| 2 |  | 0.60 | 0.20 | 0.20 | 0.20 |
| 3 |  | 0.55 | 0.18 | 0.18 | 0.18 |
| 4 |  | 0.55 | 0.18 | 0.18 | 0.18 |

**Primary Assessment Driver:** `` with combined weight of 1.30
**Secondary Driver:** `` with combined weight of 0.60

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

*Loss modifier is bounded: floor 0.55, cap 1.6.*

**Exposure (size) -> Scale Modifier**

| Band | Score Band | Modifier | Implied Value Range |
|------|-----------|----------|---------------------|
| MICRO | 0-20 | 0.5 | $0 - $1,000,000 |
| SMALL | 21-40 | 0.75 | $1,000,000 - $10,000,000 |
| MEDIUM | 41-60 | 1.0 | $10,000,000 - $50,000,000 |
| LARGE | 61-80 | 1.5 | $50,000,000 - $250,000,000 |
| VERY_LARGE | 81-100 | 2.5 | $250,000,000 - $1,000,000,000 |

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
> *P_final = Base Package Premium × Modifiers*

**1. The Pricing Anchor:** The Flat Premium of `$18,000` purchases exactly the `$1,000,000` Limit / `$50,000` Deductible Base Package.
**2. Theoretical Execution:**
  - Technical Premium = **$18,000**
  - *Scaling relies entirely on selecting a different Limit ID from the Bundled limit_configuration packages.*

---

## Model: `prodlib_medical_device`
*FDA-regulated medical devices*

### Routing Protocol (Multiplexer)
- `product_category == medical_device`

### Three-Layer Weight Distribution
> *DSI requires that weights for Risk, Loss, and Exposure each sum to 1.0 across all signal groups.*

**Validation:** PASS

| Group | Risk | Loss | Exposure |
|-------|------|------|----------|
|  | 0.43 | 0.43 | 0.43 |
|  | 0.20 | 0.20 | 0.20 |
|  | 0.18 | 0.18 | 0.18 |
|  | 0.18 | 0.18 | 0.18 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

*Reading the table: a group's three weights are independent. The same group can be a dominant driver of one pillar and a minor input to another — e.g. a group may carry most of the Exposure weight while contributing little to Risk.*

### Signal Architecture Rationale
This configuration contains **33 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `DIRECT_OBSERVABLE` (9 signals): Highest confidence
- `INFERRED_PROXY` (24 signals): Medium confidence

**Signal Count by Group:**
- `technical_infrastructure`: 13 signals
- `structured_data`: 7 signals
- `corporate_footprint`: 7 signals
- `network_authority`: 6 signals

**Selection Rationale:**
- 27% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Detail by Group
> *Each signal is an objectively observable data point. The weights show how strongly that signal informs each assessment pillar; correlation direction indicates whether a higher observed value increases (+) or decreases (-) the assessed exposure.*

#### technical_infrastructure
| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `business_continuity` | INFERRED_PROXY | 0.17 | 0.12 / 0.05 | 0.00 | + |
| `disaster_recovery` | INFERRED_PROXY | 0.17 | 0.12 / 0.05 | 0.00 | + |
| `operational_resilience` | INFERRED_PROXY | 0.17 | 0.12 / 0.05 | 0.00 | + |
| `technology_stack` | INFERRED_PROXY | 0.17 | 0.12 / 0.05 | 0.00 | + |
| `process_maturity` | INFERRED_PROXY | 0.17 | 0.12 / 0.05 | 0.00 | + |
| `quality_management` | INFERRED_PROXY | 0.17 | 0.12 / 0.05 | 0.00 | + |
| `security_headers` | DIRECT_OBSERVABLE | 0.14 | 0.10 / 0.04 | 0.07 | + |
| `tls_configuration` | DIRECT_OBSERVABLE | 0.14 | 0.10 / 0.04 | 0.07 | + |
| `email_authentication` | DIRECT_OBSERVABLE | 0.14 | 0.10 / 0.04 | 0.07 | + |
| `dns_security` | DIRECT_OBSERVABLE | 0.14 | 0.10 / 0.04 | 0.07 | + |
| `web_security` | DIRECT_OBSERVABLE | 0.14 | 0.10 / 0.04 | 0.07 | + |
| `ssl_certificate` | DIRECT_OBSERVABLE | 0.14 | 0.10 / 0.04 | 0.07 | + |
| `content_security_policy` | DIRECT_OBSERVABLE | 0.14 | 0.10 / 0.04 | 0.07 | + |

#### network_authority
| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `customer_quality` | INFERRED_PROXY | 0.17 | 0.12 / 0.05 | 0.08 | + |
| `partner_ecosystem` | INFERRED_PROXY | 0.17 | 0.12 / 0.05 | 0.08 | + |
| `certification_status` | INFERRED_PROXY | 0.17 | 0.12 / 0.05 | 0.08 | + |
| `vendor_relationships` | INFERRED_PROXY | 0.17 | 0.12 / 0.05 | 0.08 | + |
| `industry_associations` | INFERRED_PROXY | 0.17 | 0.12 / 0.05 | 0.08 | + |
| `supply_chain_visibility` | INFERRED_PROXY | 0.17 | 0.12 / 0.05 | 0.08 | + |

#### structured_data
| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `revenue_growth` | INFERRED_PROXY | 0.14 | 0.10 / 0.04 | 0.00 | + |
| `profitability` | INFERRED_PROXY | 0.14 | 0.10 / 0.04 | 0.00 | + |
| `liquidity_ratio` | INFERRED_PROXY | 0.14 | 0.10 / 0.04 | 0.00 | + |
| `debt_ratio` | INFERRED_PROXY | 0.14 | 0.10 / 0.04 | 0.00 | + |
| `credit_rating` | DIRECT_OBSERVABLE | 0.14 | 0.10 / 0.04 | 0.00 | + |
| `stock_performance` | DIRECT_OBSERVABLE | 0.14 | 0.10 / 0.04 | 0.00 | + |
| `funding_status` | INFERRED_PROXY | 0.14 | 0.10 / 0.04 | 0.00 | + |

#### corporate_footprint
| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `website_quality` | INFERRED_PROXY | 0.14 | 0.10 / 0.04 | 0.07 | + |
| `security_disclosure` | INFERRED_PROXY | 0.14 | 0.10 / 0.04 | 0.07 | + |
| `leadership_visibility` | INFERRED_PROXY | 0.14 | 0.10 / 0.04 | 0.07 | + |
| `social_presence` | INFERRED_PROXY | 0.14 | 0.10 / 0.04 | 0.07 | + |
| `brand_reputation` | INFERRED_PROXY | 0.14 | 0.10 / 0.04 | 0.07 | + |
| `media_coverage` | INFERRED_PROXY | 0.14 | 0.10 / 0.04 | 0.07 | + |
| `investor_relations` | INFERRED_PROXY | 0.14 | 0.10 / 0.04 | 0.07 | + |

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 |  | 1.30 | 0.43 | 0.43 | 0.43 |
| 2 |  | 0.60 | 0.20 | 0.20 | 0.20 |
| 3 |  | 0.55 | 0.18 | 0.18 | 0.18 |
| 4 |  | 0.55 | 0.18 | 0.18 | 0.18 |

**Primary Assessment Driver:** `` with combined weight of 1.30
**Secondary Driver:** `` with combined weight of 0.60

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

*Loss modifier is bounded: floor 0.55, cap 1.6.*

**Exposure (size) -> Scale Modifier**

| Band | Score Band | Modifier | Implied Value Range |
|------|-----------|----------|---------------------|
| MICRO | 0-20 | 0.5 | $0 - $1,000,000 |
| SMALL | 21-40 | 0.75 | $1,000,000 - $10,000,000 |
| MEDIUM | 41-60 | 1.0 | $10,000,000 - $50,000,000 |
| LARGE | 61-80 | 1.5 | $50,000,000 - $250,000,000 |
| VERY_LARGE | 81-100 | 2.5 | $250,000,000 - $1,000,000,000 |

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
> *P_final = Base Package Premium × Modifiers*

**1. The Pricing Anchor:** The Flat Premium of `$18,000` purchases exactly the `$1,000,000` Limit / `$50,000` Deductible Base Package.
**2. Theoretical Execution:**
  - Technical Premium = **$18,000**
  - *Scaling relies entirely on selecting a different Limit ID from the Bundled limit_configuration packages.*

---

## Model: `prodlib_auto_parts`
*NHTSA-regulated auto parts*

### Routing Protocol (Multiplexer)
- `product_category == auto_parts`

### Three-Layer Weight Distribution
> *DSI requires that weights for Risk, Loss, and Exposure each sum to 1.0 across all signal groups.*

**Validation:** PASS

| Group | Risk | Loss | Exposure |
|-------|------|------|----------|
|  | 0.43 | 0.43 | 0.43 |
|  | 0.20 | 0.20 | 0.20 |
|  | 0.18 | 0.18 | 0.18 |
|  | 0.18 | 0.18 | 0.18 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

*Reading the table: a group's three weights are independent. The same group can be a dominant driver of one pillar and a minor input to another — e.g. a group may carry most of the Exposure weight while contributing little to Risk.*

### Signal Architecture Rationale
This configuration contains **33 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `DIRECT_OBSERVABLE` (9 signals): Highest confidence
- `INFERRED_PROXY` (24 signals): Medium confidence

**Signal Count by Group:**
- `technical_infrastructure`: 13 signals
- `structured_data`: 7 signals
- `corporate_footprint`: 7 signals
- `network_authority`: 6 signals

**Selection Rationale:**
- 27% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Detail by Group
> *Each signal is an objectively observable data point. The weights show how strongly that signal informs each assessment pillar; correlation direction indicates whether a higher observed value increases (+) or decreases (-) the assessed exposure.*

#### technical_infrastructure
| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `business_continuity` | INFERRED_PROXY | 0.17 | 0.12 / 0.05 | 0.00 | + |
| `disaster_recovery` | INFERRED_PROXY | 0.17 | 0.12 / 0.05 | 0.00 | + |
| `operational_resilience` | INFERRED_PROXY | 0.17 | 0.12 / 0.05 | 0.00 | + |
| `technology_stack` | INFERRED_PROXY | 0.17 | 0.12 / 0.05 | 0.00 | + |
| `process_maturity` | INFERRED_PROXY | 0.17 | 0.12 / 0.05 | 0.00 | + |
| `quality_management` | INFERRED_PROXY | 0.17 | 0.12 / 0.05 | 0.00 | + |
| `security_headers` | DIRECT_OBSERVABLE | 0.14 | 0.10 / 0.04 | 0.07 | + |
| `tls_configuration` | DIRECT_OBSERVABLE | 0.14 | 0.10 / 0.04 | 0.07 | + |
| `email_authentication` | DIRECT_OBSERVABLE | 0.14 | 0.10 / 0.04 | 0.07 | + |
| `dns_security` | DIRECT_OBSERVABLE | 0.14 | 0.10 / 0.04 | 0.07 | + |
| `web_security` | DIRECT_OBSERVABLE | 0.14 | 0.10 / 0.04 | 0.07 | + |
| `ssl_certificate` | DIRECT_OBSERVABLE | 0.14 | 0.10 / 0.04 | 0.07 | + |
| `content_security_policy` | DIRECT_OBSERVABLE | 0.14 | 0.10 / 0.04 | 0.07 | + |

#### network_authority
| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `customer_quality` | INFERRED_PROXY | 0.17 | 0.12 / 0.05 | 0.08 | + |
| `partner_ecosystem` | INFERRED_PROXY | 0.17 | 0.12 / 0.05 | 0.08 | + |
| `certification_status` | INFERRED_PROXY | 0.17 | 0.12 / 0.05 | 0.08 | + |
| `vendor_relationships` | INFERRED_PROXY | 0.17 | 0.12 / 0.05 | 0.08 | + |
| `industry_associations` | INFERRED_PROXY | 0.17 | 0.12 / 0.05 | 0.08 | + |
| `supply_chain_visibility` | INFERRED_PROXY | 0.17 | 0.12 / 0.05 | 0.08 | + |

#### structured_data
| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `revenue_growth` | INFERRED_PROXY | 0.14 | 0.10 / 0.04 | 0.00 | + |
| `profitability` | INFERRED_PROXY | 0.14 | 0.10 / 0.04 | 0.00 | + |
| `liquidity_ratio` | INFERRED_PROXY | 0.14 | 0.10 / 0.04 | 0.00 | + |
| `debt_ratio` | INFERRED_PROXY | 0.14 | 0.10 / 0.04 | 0.00 | + |
| `credit_rating` | DIRECT_OBSERVABLE | 0.14 | 0.10 / 0.04 | 0.00 | + |
| `stock_performance` | DIRECT_OBSERVABLE | 0.14 | 0.10 / 0.04 | 0.00 | + |
| `funding_status` | INFERRED_PROXY | 0.14 | 0.10 / 0.04 | 0.00 | + |

#### corporate_footprint
| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `website_quality` | INFERRED_PROXY | 0.14 | 0.10 / 0.04 | 0.07 | + |
| `security_disclosure` | INFERRED_PROXY | 0.14 | 0.10 / 0.04 | 0.07 | + |
| `leadership_visibility` | INFERRED_PROXY | 0.14 | 0.10 / 0.04 | 0.07 | + |
| `social_presence` | INFERRED_PROXY | 0.14 | 0.10 / 0.04 | 0.07 | + |
| `brand_reputation` | INFERRED_PROXY | 0.14 | 0.10 / 0.04 | 0.07 | + |
| `media_coverage` | INFERRED_PROXY | 0.14 | 0.10 / 0.04 | 0.07 | + |
| `investor_relations` | INFERRED_PROXY | 0.14 | 0.10 / 0.04 | 0.07 | + |

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 |  | 1.30 | 0.43 | 0.43 | 0.43 |
| 2 |  | 0.60 | 0.20 | 0.20 | 0.20 |
| 3 |  | 0.55 | 0.18 | 0.18 | 0.18 |
| 4 |  | 0.55 | 0.18 | 0.18 | 0.18 |

**Primary Assessment Driver:** `` with combined weight of 1.30
**Secondary Driver:** `` with combined weight of 0.60

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

*Loss modifier is bounded: floor 0.55, cap 1.6.*

**Exposure (size) -> Scale Modifier**

| Band | Score Band | Modifier | Implied Value Range |
|------|-----------|----------|---------------------|
| MICRO | 0-20 | 0.5 | $0 - $1,000,000 |
| SMALL | 21-40 | 0.75 | $1,000,000 - $10,000,000 |
| MEDIUM | 41-60 | 1.0 | $10,000,000 - $50,000,000 |
| LARGE | 61-80 | 1.5 | $50,000,000 - $250,000,000 |
| VERY_LARGE | 81-100 | 2.5 | $250,000,000 - $1,000,000,000 |

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
> *P_final = Base Package Premium × Modifiers*

**1. The Pricing Anchor:** The Flat Premium of `$18,000` purchases exactly the `$1,000,000` Limit / `$50,000` Deductible Base Package.
**2. Theoretical Execution:**
  - Technical Premium = **$18,000**
  - *Scaling relies entirely on selecting a different Limit ID from the Bundled limit_configuration packages.*

---

## Model: `prodlib_food_bev`
*USDA FSIS / FDA-regulated food + beverage*

### Routing Protocol (Multiplexer)
- `product_category == food_bev`

### Three-Layer Weight Distribution
> *DSI requires that weights for Risk, Loss, and Exposure each sum to 1.0 across all signal groups.*

**Validation:** PASS

| Group | Risk | Loss | Exposure |
|-------|------|------|----------|
|  | 0.43 | 0.43 | 0.43 |
|  | 0.20 | 0.20 | 0.20 |
|  | 0.18 | 0.18 | 0.18 |
|  | 0.18 | 0.18 | 0.18 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

*Reading the table: a group's three weights are independent. The same group can be a dominant driver of one pillar and a minor input to another — e.g. a group may carry most of the Exposure weight while contributing little to Risk.*

### Signal Architecture Rationale
This configuration contains **33 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `DIRECT_OBSERVABLE` (9 signals): Highest confidence
- `INFERRED_PROXY` (24 signals): Medium confidence

**Signal Count by Group:**
- `technical_infrastructure`: 13 signals
- `structured_data`: 7 signals
- `corporate_footprint`: 7 signals
- `network_authority`: 6 signals

**Selection Rationale:**
- 27% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Detail by Group
> *Each signal is an objectively observable data point. The weights show how strongly that signal informs each assessment pillar; correlation direction indicates whether a higher observed value increases (+) or decreases (-) the assessed exposure.*

#### technical_infrastructure
| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `business_continuity` | INFERRED_PROXY | 0.17 | 0.12 / 0.05 | 0.00 | + |
| `disaster_recovery` | INFERRED_PROXY | 0.17 | 0.12 / 0.05 | 0.00 | + |
| `operational_resilience` | INFERRED_PROXY | 0.17 | 0.12 / 0.05 | 0.00 | + |
| `technology_stack` | INFERRED_PROXY | 0.17 | 0.12 / 0.05 | 0.00 | + |
| `process_maturity` | INFERRED_PROXY | 0.17 | 0.12 / 0.05 | 0.00 | + |
| `quality_management` | INFERRED_PROXY | 0.17 | 0.12 / 0.05 | 0.00 | + |
| `security_headers` | DIRECT_OBSERVABLE | 0.14 | 0.10 / 0.04 | 0.07 | + |
| `tls_configuration` | DIRECT_OBSERVABLE | 0.14 | 0.10 / 0.04 | 0.07 | + |
| `email_authentication` | DIRECT_OBSERVABLE | 0.14 | 0.10 / 0.04 | 0.07 | + |
| `dns_security` | DIRECT_OBSERVABLE | 0.14 | 0.10 / 0.04 | 0.07 | + |
| `web_security` | DIRECT_OBSERVABLE | 0.14 | 0.10 / 0.04 | 0.07 | + |
| `ssl_certificate` | DIRECT_OBSERVABLE | 0.14 | 0.10 / 0.04 | 0.07 | + |
| `content_security_policy` | DIRECT_OBSERVABLE | 0.14 | 0.10 / 0.04 | 0.07 | + |

#### network_authority
| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `customer_quality` | INFERRED_PROXY | 0.17 | 0.12 / 0.05 | 0.08 | + |
| `partner_ecosystem` | INFERRED_PROXY | 0.17 | 0.12 / 0.05 | 0.08 | + |
| `certification_status` | INFERRED_PROXY | 0.17 | 0.12 / 0.05 | 0.08 | + |
| `vendor_relationships` | INFERRED_PROXY | 0.17 | 0.12 / 0.05 | 0.08 | + |
| `industry_associations` | INFERRED_PROXY | 0.17 | 0.12 / 0.05 | 0.08 | + |
| `supply_chain_visibility` | INFERRED_PROXY | 0.17 | 0.12 / 0.05 | 0.08 | + |

#### structured_data
| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `revenue_growth` | INFERRED_PROXY | 0.14 | 0.10 / 0.04 | 0.00 | + |
| `profitability` | INFERRED_PROXY | 0.14 | 0.10 / 0.04 | 0.00 | + |
| `liquidity_ratio` | INFERRED_PROXY | 0.14 | 0.10 / 0.04 | 0.00 | + |
| `debt_ratio` | INFERRED_PROXY | 0.14 | 0.10 / 0.04 | 0.00 | + |
| `credit_rating` | DIRECT_OBSERVABLE | 0.14 | 0.10 / 0.04 | 0.00 | + |
| `stock_performance` | DIRECT_OBSERVABLE | 0.14 | 0.10 / 0.04 | 0.00 | + |
| `funding_status` | INFERRED_PROXY | 0.14 | 0.10 / 0.04 | 0.00 | + |

#### corporate_footprint
| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `website_quality` | INFERRED_PROXY | 0.14 | 0.10 / 0.04 | 0.07 | + |
| `security_disclosure` | INFERRED_PROXY | 0.14 | 0.10 / 0.04 | 0.07 | + |
| `leadership_visibility` | INFERRED_PROXY | 0.14 | 0.10 / 0.04 | 0.07 | + |
| `social_presence` | INFERRED_PROXY | 0.14 | 0.10 / 0.04 | 0.07 | + |
| `brand_reputation` | INFERRED_PROXY | 0.14 | 0.10 / 0.04 | 0.07 | + |
| `media_coverage` | INFERRED_PROXY | 0.14 | 0.10 / 0.04 | 0.07 | + |
| `investor_relations` | INFERRED_PROXY | 0.14 | 0.10 / 0.04 | 0.07 | + |

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 |  | 1.30 | 0.43 | 0.43 | 0.43 |
| 2 |  | 0.60 | 0.20 | 0.20 | 0.20 |
| 3 |  | 0.55 | 0.18 | 0.18 | 0.18 |
| 4 |  | 0.55 | 0.18 | 0.18 | 0.18 |

**Primary Assessment Driver:** `` with combined weight of 1.30
**Secondary Driver:** `` with combined weight of 0.60

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

*Loss modifier is bounded: floor 0.55, cap 1.6.*

**Exposure (size) -> Scale Modifier**

| Band | Score Band | Modifier | Implied Value Range |
|------|-----------|----------|---------------------|
| MICRO | 0-20 | 0.5 | $0 - $1,000,000 |
| SMALL | 21-40 | 0.75 | $1,000,000 - $10,000,000 |
| MEDIUM | 41-60 | 1.0 | $10,000,000 - $50,000,000 |
| LARGE | 61-80 | 1.5 | $50,000,000 - $250,000,000 |
| VERY_LARGE | 81-100 | 2.5 | $250,000,000 - $1,000,000,000 |

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
> *P_final = Base Package Premium × Modifiers*

**1. The Pricing Anchor:** The Flat Premium of `$18,000` purchases exactly the `$1,000,000` Limit / `$50,000` Deductible Base Package.
**2. Theoretical Execution:**
  - Technical Premium = **$18,000**
  - *Scaling relies entirely on selecting a different Limit ID from the Bundled limit_configuration packages.*

---

## Model: `prodlib_sme`
*Sub-scale distributors (<100k units/yr)*

### Routing Protocol (Multiplexer)
- `annual_units_distributed < 100000`

### Three-Layer Weight Distribution
> *DSI requires that weights for Risk, Loss, and Exposure each sum to 1.0 across all signal groups.*

**Validation:** PASS

| Group | Risk | Loss | Exposure |
|-------|------|------|----------|
|  | 0.43 | 0.43 | 0.43 |
|  | 0.20 | 0.20 | 0.20 |
|  | 0.18 | 0.18 | 0.18 |
|  | 0.18 | 0.18 | 0.18 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

*Reading the table: a group's three weights are independent. The same group can be a dominant driver of one pillar and a minor input to another — e.g. a group may carry most of the Exposure weight while contributing little to Risk.*

### Signal Architecture Rationale
This configuration contains **33 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `DIRECT_OBSERVABLE` (9 signals): Highest confidence
- `INFERRED_PROXY` (24 signals): Medium confidence

**Signal Count by Group:**
- `technical_infrastructure`: 13 signals
- `structured_data`: 7 signals
- `corporate_footprint`: 7 signals
- `network_authority`: 6 signals

**Selection Rationale:**
- 27% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Detail by Group
> *Each signal is an objectively observable data point. The weights show how strongly that signal informs each assessment pillar; correlation direction indicates whether a higher observed value increases (+) or decreases (-) the assessed exposure.*

#### technical_infrastructure
| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `business_continuity` | INFERRED_PROXY | 0.17 | 0.12 / 0.05 | 0.00 | + |
| `disaster_recovery` | INFERRED_PROXY | 0.17 | 0.12 / 0.05 | 0.00 | + |
| `operational_resilience` | INFERRED_PROXY | 0.17 | 0.12 / 0.05 | 0.00 | + |
| `technology_stack` | INFERRED_PROXY | 0.17 | 0.12 / 0.05 | 0.00 | + |
| `process_maturity` | INFERRED_PROXY | 0.17 | 0.12 / 0.05 | 0.00 | + |
| `quality_management` | INFERRED_PROXY | 0.17 | 0.12 / 0.05 | 0.00 | + |
| `security_headers` | DIRECT_OBSERVABLE | 0.14 | 0.10 / 0.04 | 0.07 | + |
| `tls_configuration` | DIRECT_OBSERVABLE | 0.14 | 0.10 / 0.04 | 0.07 | + |
| `email_authentication` | DIRECT_OBSERVABLE | 0.14 | 0.10 / 0.04 | 0.07 | + |
| `dns_security` | DIRECT_OBSERVABLE | 0.14 | 0.10 / 0.04 | 0.07 | + |
| `web_security` | DIRECT_OBSERVABLE | 0.14 | 0.10 / 0.04 | 0.07 | + |
| `ssl_certificate` | DIRECT_OBSERVABLE | 0.14 | 0.10 / 0.04 | 0.07 | + |
| `content_security_policy` | DIRECT_OBSERVABLE | 0.14 | 0.10 / 0.04 | 0.07 | + |

#### network_authority
| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `customer_quality` | INFERRED_PROXY | 0.17 | 0.12 / 0.05 | 0.08 | + |
| `partner_ecosystem` | INFERRED_PROXY | 0.17 | 0.12 / 0.05 | 0.08 | + |
| `certification_status` | INFERRED_PROXY | 0.17 | 0.12 / 0.05 | 0.08 | + |
| `vendor_relationships` | INFERRED_PROXY | 0.17 | 0.12 / 0.05 | 0.08 | + |
| `industry_associations` | INFERRED_PROXY | 0.17 | 0.12 / 0.05 | 0.08 | + |
| `supply_chain_visibility` | INFERRED_PROXY | 0.17 | 0.12 / 0.05 | 0.08 | + |

#### structured_data
| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `revenue_growth` | INFERRED_PROXY | 0.14 | 0.10 / 0.04 | 0.00 | + |
| `profitability` | INFERRED_PROXY | 0.14 | 0.10 / 0.04 | 0.00 | + |
| `liquidity_ratio` | INFERRED_PROXY | 0.14 | 0.10 / 0.04 | 0.00 | + |
| `debt_ratio` | INFERRED_PROXY | 0.14 | 0.10 / 0.04 | 0.00 | + |
| `credit_rating` | DIRECT_OBSERVABLE | 0.14 | 0.10 / 0.04 | 0.00 | + |
| `stock_performance` | DIRECT_OBSERVABLE | 0.14 | 0.10 / 0.04 | 0.00 | + |
| `funding_status` | INFERRED_PROXY | 0.14 | 0.10 / 0.04 | 0.00 | + |

#### corporate_footprint
| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `website_quality` | INFERRED_PROXY | 0.14 | 0.10 / 0.04 | 0.07 | + |
| `security_disclosure` | INFERRED_PROXY | 0.14 | 0.10 / 0.04 | 0.07 | + |
| `leadership_visibility` | INFERRED_PROXY | 0.14 | 0.10 / 0.04 | 0.07 | + |
| `social_presence` | INFERRED_PROXY | 0.14 | 0.10 / 0.04 | 0.07 | + |
| `brand_reputation` | INFERRED_PROXY | 0.14 | 0.10 / 0.04 | 0.07 | + |
| `media_coverage` | INFERRED_PROXY | 0.14 | 0.10 / 0.04 | 0.07 | + |
| `investor_relations` | INFERRED_PROXY | 0.14 | 0.10 / 0.04 | 0.07 | + |

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 |  | 1.30 | 0.43 | 0.43 | 0.43 |
| 2 |  | 0.60 | 0.20 | 0.20 | 0.20 |
| 3 |  | 0.55 | 0.18 | 0.18 | 0.18 |
| 4 |  | 0.55 | 0.18 | 0.18 | 0.18 |

**Primary Assessment Driver:** `` with combined weight of 1.30
**Secondary Driver:** `` with combined weight of 0.60

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

*Loss modifier is bounded: floor 0.55, cap 1.6.*

**Exposure (size) -> Scale Modifier**

| Band | Score Band | Modifier | Implied Value Range |
|------|-----------|----------|---------------------|
| MICRO | 0-20 | 0.5 | $0 - $1,000,000 |
| SMALL | 21-40 | 0.75 | $1,000,000 - $10,000,000 |
| MEDIUM | 41-60 | 1.0 | $10,000,000 - $50,000,000 |
| LARGE | 61-80 | 1.5 | $50,000,000 - $250,000,000 |
| VERY_LARGE | 81-100 | 2.5 | $250,000,000 - $1,000,000,000 |

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
> *P_final = Base Package Premium × Modifiers*

**1. The Pricing Anchor:** The Flat Premium of `$18,000` purchases exactly the `$1,000,000` Limit / `$50,000` Deductible Base Package.
**2. Theoretical Execution:**
  - Technical Premium = **$18,000**
  - *Scaling relies entirely on selecting a different Limit ID from the Bundled limit_configuration packages.*


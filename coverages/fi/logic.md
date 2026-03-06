# DSI Logic Document: `FI`
*Generated: 2026-03-06*

## DSI Foundational Principles Adherence
This configuration is validated against the DSI Whitepaper & Vision Paper:
- **Objective Observation:** Signals derived from verifiable digital footprints, avoiding subjective interpretation.
- **Three-Layer Engine:** Modifiers explicitly target Risk, Loss, and Exposure dimensions.
- **Phase 5 Anchoring:** Polymorphic pricing limits scale from mathematically absolute anchor points.

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
| Corporate Governance | 0.15 | 0.15 | 0.10 |
| Operational Risk | 0.10 | 0.10 | 0.10 |
| Cyber Security | 0.10 | 0.10 | 0.10 |
| Corporate Footprint | 0.05 | 0.03 | 0.15 |
| Structured Data | 0.05 | 0.02 | 0.15 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

### Signal Architecture Rationale
This configuration contains **51 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `DIRECT_OBSERVABLE` (35 signals): Highest confidence
- `INFERRED_PROXY` (15 signals): Medium confidence
- `COHORT_INFERENCE` (1 signals): Lowest confidence

**Signal Count by Group:**
- `network_authority`: 7 signals
- `regulatory_compliance`: 7 signals
- `financial_condition`: 7 signals
- `governance`: 6 signals
- `cyber_security`: 6 signals
- `corporate_footprint`: 6 signals
- `operational_risk`: 5 signals
- `structured_data`: 3 signals
- `institution_type`: 1 signals
- `regulatory_framework`: 1 signals
- `asset_size_band`: 1 signals
- `publicly_traded`: 1 signals

**Selection Rationale:**
- 69% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 | Financial Condition | 0.75 | 0.20 | 0.30 | 0.25 |
| 2 | Regulatory Compliance | 0.60 | 0.25 | 0.25 | 0.10 |
| 3 | Corporate Governance | 0.40 | 0.15 | 0.15 | 0.10 |
| 4 | Operational Risk | 0.30 | 0.10 | 0.10 | 0.10 |
| 5 | Cyber Security | 0.30 | 0.10 | 0.10 | 0.10 |
| 6 | Corporate Footprint | 0.23 | 0.05 | 0.03 | 0.15 |
| 7 | Structured Data | 0.22 | 0.05 | 0.02 | 0.15 |
| 8 | Network Authority | 0.20 | 0.10 | 0.05 | 0.05 |

**Primary Assessment Driver:** `Financial Condition` with combined weight of 0.75
**Secondary Driver:** `Regulatory Compliance` with combined weight of 0.60

### Theoretical Premium Calculation (Tier 3 Standard)
> *Per the DSI Premium Calculation Methodology v2.0, the core formula is:*
> *P_final = (Base × Rate) × ILF_relativity × Deductible_Factor × Modifiers*

**1. The Pricing Anchor:** The Base Rate of `0.002%` on `total_assets` purchases exactly a `$1,000,000` Limit with a `$50,000` Deductible.
**2. Theoretical Execution:**
  - Assume `total_assets` = $10,000,000
  - Base Premium = $10,000,000 × 2e-05 = **$200**
  - If the client requests the Anchor Limit/Deductible, the factors are 1.00, resulting in a technical premium of **$200**.

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
| Cyber Security | 0.15 | 0.20 | 0.20 |
| Operational Risk | 0.15 | 0.20 | 0.30 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

### Signal Architecture Rationale
This configuration contains **8 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `DIRECT_OBSERVABLE` (7 signals): Highest confidence
- `INFERRED_PROXY` (1 signals): Medium confidence

**Signal Count by Group:**
- `regulatory_compliance`: 2 signals
- `financial_condition`: 2 signals
- `cyber_security`: 2 signals
- `institution_type`: 1 signals
- `operational_risk`: 1 signals

**Selection Rationale:**
- 88% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 | Financial Condition | 1.05 | 0.35 | 0.30 | 0.40 |
| 2 | Regulatory Compliance | 0.75 | 0.35 | 0.30 | 0.10 |
| 3 | Operational Risk | 0.65 | 0.15 | 0.20 | 0.30 |
| 4 | Cyber Security | 0.55 | 0.15 | 0.20 | 0.20 |

**Primary Assessment Driver:** `Financial Condition` with combined weight of 1.05
**Secondary Driver:** `Regulatory Compliance` with combined weight of 0.75

### Theoretical Premium Calculation (Tier 3 Standard)
> *Per the DSI Premium Calculation Methodology v2.0, the core formula is:*
> *P_final = (Base × Rate) × ILF_relativity × Deductible_Factor × Modifiers*

**1. The Pricing Anchor:** The Flat Premium of `$12,000` purchases exactly the `$1,000,000` Limit / `$10,000` Deductible Base Package.
**2. Theoretical Execution:**
  - Technical Premium = **$12,000**
  - *Scaling relies entirely on selecting a different Limit ID from the Bundled limit_configuration packages.*


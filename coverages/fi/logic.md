# DSI Logic Document: `FI`
*Generated: 2026-04-17*

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
| Corporate Governance | 0.20 | 0.18 | 0.25 |
| Operational Risk | 0.20 | 0.20 | 0.20 |
| Structured Data | 0.05 | 0.02 | 0.15 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

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

### Theoretical Premium Calculation (Tier 3 Standard)
> *Per the DSI Premium Calculation Methodology v2.0, the core formula is:*
> *P_final = (Base × Rate) × ILF_relativity × Deductible_Factor × Modifiers*

**1. The Pricing Anchor:** The Base Rate of `0.0015%` on `total_assets` purchases exactly a `$1,000,000` Limit with a `$50,000` Deductible.
**2. Theoretical Execution:**
  - Assume `total_assets` = $10,000,000
  - Base Premium = $10,000,000 × 1.5e-05 = **$150**
  - If the client requests the Anchor Limit/Deductible, the factors are 1.00, resulting in a technical premium of **$150**.

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

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 | Cyber Security | 1.20 | 0.30 | 0.40 | 0.50 |
| 2 | Financial Condition | 1.05 | 0.35 | 0.30 | 0.40 |
| 3 | Regulatory Compliance | 0.75 | 0.35 | 0.30 | 0.10 |

**Primary Assessment Driver:** `Cyber Security` with combined weight of 1.20
**Secondary Driver:** `Financial Condition` with combined weight of 1.05

### Theoretical Premium Calculation (Tier 3 Standard)
> *Per the DSI Premium Calculation Methodology v2.0, the core formula is:*
> *P_final = (Base × Rate) × ILF_relativity × Deductible_Factor × Modifiers*

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

### Theoretical Premium Calculation (Tier 3 Standard)
> *Per the DSI Premium Calculation Methodology v2.0, the core formula is:*
> *P_final = (Base × Rate) × ILF_relativity × Deductible_Factor × Modifiers*

**1. The Pricing Anchor:** The Base Rate of `0.0018%` on `total_assets` purchases exactly a `$10,000,000` Limit with a `$500,000` Deductible.
**2. Theoretical Execution:**
  - Assume `total_assets` = $10,000,000
  - Base Premium = $10,000,000 × 1.8e-05 = **$180**
  - If the client requests the Anchor Limit/Deductible, the factors are 1.00, resulting in a technical premium of **$180**.

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

### Signal Architecture Rationale
This configuration contains **4 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `DIRECT_OBSERVABLE` (4 signals): Highest confidence

**Signal Count by Group:**
- `structured_data`: 2 signals
- `public_record`: 2 signals

**Selection Rationale:**
- 100% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 | Regulatory Framework | 1.45 | 0.50 | 0.50 | 0.45 |
| 2 | Corporate Footprint | 0.80 | 0.25 | 0.25 | 0.30 |
| 3 | Firm Stability | 0.75 | 0.25 | 0.25 | 0.25 |

**Primary Assessment Driver:** `Regulatory Framework` with combined weight of 1.45
**Secondary Driver:** `Corporate Footprint` with combined weight of 0.80

### Theoretical Premium Calculation (Tier 3 Standard)
> *Per the DSI Premium Calculation Methodology v2.0, the core formula is:*
> *P_final = (Base × Rate) × ILF_relativity × Deductible_Factor × Modifiers*

**1. The Pricing Anchor:** The Base Rate of `0.0015%` on `total_assets` purchases exactly a `$10,000,000` Limit with a `$250,000` Deductible.
**2. Theoretical Execution:**
  - Assume `total_assets` = $10,000,000
  - Base Premium = $10,000,000 × 1.5e-05 = **$150**
  - If the client requests the Anchor Limit/Deductible, the factors are 1.00, resulting in a technical premium of **$150**.

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

### Theoretical Premium Calculation (Tier 3 Standard)
> *Per the DSI Premium Calculation Methodology v2.0, the core formula is:*
> *P_final = (Base × Rate) × ILF_relativity × Deductible_Factor × Modifiers*

**1. The Pricing Anchor:** The Base Rate of `0.25%` on `revenue` purchases exactly a `$5,000,000` Limit with a `$100,000` Deductible.
**2. Theoretical Execution:**
  - Assume `revenue` = $10,000,000
  - Base Premium = $10,000,000 × 0.0025 = **$25,000**
  - If the client requests the Anchor Limit/Deductible, the factors are 1.00, resulting in a technical premium of **$25,000**.

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

### Theoretical Premium Calculation (Tier 3 Standard)
> *Per the DSI Premium Calculation Methodology v2.0, the core formula is:*
> *P_final = (Base × Rate) × ILF_relativity × Deductible_Factor × Modifiers*

**1. The Pricing Anchor:** The Base Rate of `0.27999999999999997%` on `aum` purchases exactly a `$10,000,000` Limit with a `$1,000,000` Deductible.
**2. Theoretical Execution:**
  - Assume `aum` = $10,000,000
  - Base Premium = $10,000,000 × 0.0028 = **$28,000**
  - If the client requests the Anchor Limit/Deductible, the factors are 1.00, resulting in a technical premium of **$28,000**.


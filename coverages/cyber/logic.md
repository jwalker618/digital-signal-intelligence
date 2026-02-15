# DSI Logic Document: `CYBER`
*Generated: 2026-02-15*

## DSI Foundational Principles Adherence
This configuration is validated against the DSI Whitepaper & Vision Paper:
- **Objective Observation:** Signals derived from verifiable digital footprints, avoiding subjective interpretation.
- **Three-Layer Engine:** Modifiers explicitly target Risk, Loss, and Exposure dimensions.
- **Phase 5 Anchoring:** Polymorphic pricing limits scale from mathematically absolute anchor points.

---

## Model: `cyber_general`
*Cyber liability model based on externally observable technical signals*

### Routing Protocol (Multiplexer)
- `revenue > 50000000`

### Three-Layer Weight Distribution
> *DSI requires that weights for Risk, Loss, and Exposure each sum to 1.0 across all signal groups.*

**Validation:** PASS

| Group | Risk | Loss | Exposure |
|-------|------|------|----------|
| Network Authority | 0.15 | 0.15 | 0.15 |
| Technical Infrastructure | 0.35 | 0.35 | 0.35 |
| Corporate Footprint | 0.15 | 0.25 | 0.25 |
| Public Record | 0.25 | 0.15 | 0.15 |
| Structured Data | 0.10 | 0.10 | 0.10 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

### Signal Architecture Rationale
This configuration contains **44 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `DIRECT_OBSERVABLE` (23 signals): Highest confidence
- `INFERRED_PROXY` (21 signals): Medium confidence

**Signal Count by Group:**
- `corporate_footprint`: 15 signals
- `technical_infrastructure`: 10 signals
- `network_authority`: 8 signals
- `public_record`: 5 signals
- `structured_data`: 3 signals
- `industry_classification`: 1 signals
- `size_band`: 1 signals
- `geography`: 1 signals

**Selection Rationale:**
- 52% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 | Technical Infrastructure | 1.05 | 0.35 | 0.35 | 0.35 |
| 2 | Corporate Footprint | 0.65 | 0.15 | 0.25 | 0.25 |
| 3 | Public Record | 0.55 | 0.25 | 0.15 | 0.15 |
| 4 | Network Authority | 0.45 | 0.15 | 0.15 | 0.15 |
| 5 | Structured Data | 0.30 | 0.10 | 0.10 | 0.10 |

**Primary Assessment Driver:** `Technical Infrastructure` with combined weight of 1.05
**Secondary Driver:** `Corporate Footprint` with combined weight of 0.65

### Theoretical Premium Calculation (Tier 3 Standard)
> *Per the DSI Premium Calculation Methodology v2.0, the core formula is:*
> *P_final = (Base × Rate) × ILF_relativity × Deductible_Factor × Modifiers*

**1. The Pricing Anchor:** The Base Rate of `0.25%` on `revenue` purchases exactly a `$1,000,000` Limit with a `$50,000` Deductible.
**2. Theoretical Execution:**
  - Assume `revenue` = $10,000,000
  - Base Premium = $10,000,000 × 0.0025 = **$25,000**
  - If the client requests the Anchor Limit/Deductible, the factors are 1.00, resulting in a technical premium of **$25,000**.

---

## Model: `cyber_sme`
*Cyber liability model for SME segment - automated underwriting for small businesses*

### Routing Protocol (Multiplexer)
- `revenue <= 50000000`
- `limit <= 5000000`

### Three-Layer Weight Distribution
> *DSI requires that weights for Risk, Loss, and Exposure each sum to 1.0 across all signal groups.*

**Validation:** PASS

| Group | Risk | Loss | Exposure |
|-------|------|------|----------|
| Technical Security | 0.60 | 0.55 | 0.45 |
| Public Record | 0.40 | 0.45 | 0.55 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

### Signal Architecture Rationale
This configuration contains **7 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `DIRECT_OBSERVABLE` (6 signals): Highest confidence
- `INFERRED_PROXY` (1 signals): Medium confidence

**Signal Count by Group:**
- `technical_security`: 3 signals
- `public_record`: 2 signals
- `industry_classification`: 1 signals
- `company_size`: 1 signals

**Selection Rationale:**
- 86% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 | Technical Security | 1.60 | 0.60 | 0.55 | 0.45 |
| 2 | Public Record | 1.40 | 0.40 | 0.45 | 0.55 |

**Primary Assessment Driver:** `Technical Security` with combined weight of 1.60
**Secondary Driver:** `Public Record` with combined weight of 1.40

### Theoretical Premium Calculation (Tier 3 Standard)
> *Per the DSI Premium Calculation Methodology v2.0, the core formula is:*
> *P_final = (Base × Rate) × ILF_relativity × Deductible_Factor × Modifiers*

**1. The Pricing Anchor:** The Flat Premium of `$4,000` purchases exactly the `$1,000,000` Limit / `$5,000` Deductible Base Package.
**2. Theoretical Execution:**
  - Technical Premium = **$4,000**
  - *Scaling relies entirely on selecting a different Limit ID from the Bundled limit_configuration packages.*


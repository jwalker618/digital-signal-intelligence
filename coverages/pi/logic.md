# DSI Logic Document: `PI`
*Generated: 2026-03-06*

## DSI Foundational Principles Adherence
This configuration is validated against the DSI Whitepaper & Vision Paper:
- **Objective Observation:** Signals derived from verifiable digital footprints, avoiding subjective interpretation.
- **Three-Layer Engine:** Modifiers explicitly target Risk, Loss, and Exposure dimensions.
- **Phase 5 Anchoring:** Polymorphic pricing limits scale from mathematically absolute anchor points.

---

## Model: `pi_general`
*PI/E&O coverage for mid-market and enterprise firms*

### Routing Protocol (Multiplexer)
- `revenue > 50000000`

### Three-Layer Weight Distribution
> *DSI requires that weights for Risk, Loss, and Exposure each sum to 1.0 across all signal groups.*

**Validation:** PASS

| Group | Risk | Loss | Exposure |
|-------|------|------|----------|
| Network Authority | 0.15 | 0.10 | 0.05 |
| Regulatory Standing | 0.25 | 0.25 | 0.10 |
| Firm Stability | 0.15 | 0.15 | 0.20 |
| Practice Quality | 0.15 | 0.20 | 0.15 |
| Technical Infrastructure | 0.10 | 0.10 | 0.10 |
| Corporate Footprint | 0.10 | 0.05 | 0.25 |
| Litigation History | 0.10 | 0.15 | 0.15 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

### Signal Architecture Rationale
This configuration contains **44 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `DIRECT_OBSERVABLE` (25 signals): Highest confidence
- `INFERRED_PROXY` (18 signals): Medium confidence
- `COHORT_INFERENCE` (1 signals): Lowest confidence

**Signal Count by Group:**
- `regulatory_standing`: 7 signals
- `network_authority`: 6 signals
- `firm_stability`: 6 signals
- `corporate_footprint`: 6 signals
- `practice_quality`: 5 signals
- `technical_infrastructure`: 5 signals
- `litigation_history`: 5 signals
- `profession_type`: 1 signals
- `sub_profession_type`: 1 signals
- `firm_size`: 1 signals
- `revenue_size`: 1 signals

**Selection Rationale:**
- 57% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 | Regulatory Standing | 0.60 | 0.25 | 0.25 | 0.10 |
| 2 | Firm Stability | 0.50 | 0.15 | 0.15 | 0.20 |
| 3 | Practice Quality | 0.50 | 0.15 | 0.20 | 0.15 |
| 4 | Corporate Footprint | 0.40 | 0.10 | 0.05 | 0.25 |
| 5 | Litigation History | 0.40 | 0.10 | 0.15 | 0.15 |
| 6 | Network Authority | 0.30 | 0.15 | 0.10 | 0.05 |
| 7 | Technical Infrastructure | 0.30 | 0.10 | 0.10 | 0.10 |

**Primary Assessment Driver:** `Regulatory Standing` with combined weight of 0.60
**Secondary Driver:** `Firm Stability` with combined weight of 0.50

### Theoretical Premium Calculation (Tier 3 Standard)
> *Per the DSI Premium Calculation Methodology v2.0, the core formula is:*
> *P_final = (Base × Rate) × ILF_relativity × Deductible_Factor × Modifiers*

**1. The Pricing Anchor:** The Base Rate of `0.18%` on `revenue` purchases exactly a `$1,000,000` Limit with a `$50,000` Deductible.
**2. Theoretical Execution:**
  - Assume `revenue` = $10,000,000
  - Base Premium = $10,000,000 × 0.0018 = **$18,000**
  - If the client requests the Anchor Limit/Deductible, the factors are 1.00, resulting in a technical premium of **$18,000**.

---

## Model: `pi_sme`
*PI/E&O coverage for small practices*

### Routing Protocol (Multiplexer)
- `revenue <= 50000000`

### Three-Layer Weight Distribution
> *DSI requires that weights for Risk, Loss, and Exposure each sum to 1.0 across all signal groups.*

**Validation:** FAIL - Weights do not sum to 1.0

| Group | Risk | Loss | Exposure |
|-------|------|------|----------|
| **TOTAL** | **0.00** | **0.00** | **0.00** |

### Signal Architecture Rationale
This configuration contains **1 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `INFERRED_PROXY` (1 signals): Medium confidence

**Signal Count by Group:**
- `profession_type`: 1 signals

**Selection Rationale:**
- 0% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|


### Theoretical Premium Calculation (Tier 3 Standard)
> *Per the DSI Premium Calculation Methodology v2.0, the core formula is:*
> *P_final = (Base × Rate) × ILF_relativity × Deductible_Factor × Modifiers*

**1. The Pricing Anchor:** The Base Rate of `130.0%` on `categorical` purchases exactly a `$1,000,000` Limit with a `$10,000` Deductible.
**2. Theoretical Execution:**
  - Assume `categorical` = $10,000,000
  - Base Premium = $10,000,000 × 1.3 = **$13,000,000**
  - If the client requests the Anchor Limit/Deductible, the factors are 1.00, resulting in a technical premium of **$13,000,000**.


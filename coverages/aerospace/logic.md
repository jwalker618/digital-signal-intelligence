# DSI Logic Document: `AEROSPACE`
*Generated: 2026-02-15*

## DSI Foundational Principles Adherence
This configuration is validated against the DSI Whitepaper & Vision Paper:
- **Objective Observation:** Signals derived from verifiable digital footprints, avoiding subjective interpretation.
- **Three-Layer Engine:** Modifiers explicitly target Risk, Loss, and Exposure dimensions.
- **Phase 5 Anchoring:** Polymorphic pricing limits scale from mathematically absolute anchor points.

---

## Model: `aerospace_general`
*Aviation hull and liability coverage based on observable safety and operational signals*

### Routing Protocol (Multiplexer)
- `hull_value > 50000000`

### Three-Layer Weight Distribution
> *DSI requires that weights for Risk, Loss, and Exposure each sum to 1.0 across all signal groups.*

**Validation:** PASS

| Group | Risk | Loss | Exposure |
|-------|------|------|----------|
| Network Authority | 0.10 | 0.05 | 0.05 |
| Safety Record | 0.30 | 0.40 | 0.10 |
| Regulatory Compliance | 0.20 | 0.20 | 0.10 |
| Operational Quality | 0.15 | 0.15 | 0.15 |
| Fleet Quality | 0.10 | 0.10 | 0.35 |
| Financial Stability | 0.05 | 0.03 | 0.10 |
| Route Risk | 0.05 | 0.05 | 0.10 |
| Corporate Governance | 0.05 | 0.02 | 0.05 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

### Signal Architecture Rationale
This configuration contains **48 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `DIRECT_OBSERVABLE` (23 signals): Highest confidence
- `INFERRED_PROXY` (24 signals): Medium confidence
- `COHORT_INFERENCE` (1 signals): Lowest confidence

**Signal Count by Group:**
- `regulatory_compliance`: 7 signals
- `operational_quality`: 6 signals
- `fleet_quality`: 6 signals
- `network_authority`: 5 signals
- `safety_record`: 5 signals
- `route_risk`: 5 signals
- `corporate_governance`: 5 signals
- `financial_stability`: 4 signals
- `operator_type`: 1 signals
- `fleet_category`: 1 signals
- `fleet_size`: 1 signals
- `regulatory_framework`: 1 signals
- `iosa_status`: 1 signals

**Selection Rationale:**
- 48% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 | Safety Record | 0.80 | 0.30 | 0.40 | 0.10 |
| 2 | Fleet Quality | 0.55 | 0.10 | 0.10 | 0.35 |
| 3 | Regulatory Compliance | 0.50 | 0.20 | 0.20 | 0.10 |
| 4 | Operational Quality | 0.45 | 0.15 | 0.15 | 0.15 |
| 5 | Network Authority | 0.20 | 0.10 | 0.05 | 0.05 |
| 6 | Route Risk | 0.20 | 0.05 | 0.05 | 0.10 |
| 7 | Financial Stability | 0.18 | 0.05 | 0.03 | 0.10 |
| 8 | Corporate Governance | 0.12 | 0.05 | 0.02 | 0.05 |

**Primary Assessment Driver:** `Safety Record` with combined weight of 0.80
**Secondary Driver:** `Fleet Quality` with combined weight of 0.55

### Theoretical Premium Calculation (Tier 3 Standard)
> *Per the DSI Premium Calculation Methodology v2.0, the core formula is:*
> *P_final = (Base × Rate) × ILF_relativity × Deductible_Factor × Modifiers*

**1. The Pricing Anchor:** The Base Rate of `0.27999999999999997%` on `hull_value` purchases exactly a `$10,000,000` Limit with a `$50,000` Deductible.
**2. Theoretical Execution:**
  - Assume `hull_value` = $10,000,000
  - Base Premium = $10,000,000 × 0.0028 = **$28,000**
  - If the client requests the Anchor Limit/Deductible, the factors are 1.00, resulting in a technical premium of **$28,000**.

---

## Model: `aerospace_sme`
*Aviation coverage for small/medium operators with hull value under $50M*

### Routing Protocol (Multiplexer)
- `hull_value <= 50000000`
- `limit <= 10000000`

### Three-Layer Weight Distribution
> *DSI requires that weights for Risk, Loss, and Exposure each sum to 1.0 across all signal groups.*

**Validation:** PASS

| Group | Risk | Loss | Exposure |
|-------|------|------|----------|
| Safety Record | 0.35 | 0.45 | 0.10 |
| Regulatory Compliance | 0.25 | 0.20 | 0.10 |
| Operational Quality | 0.20 | 0.15 | 0.15 |
| Fleet Quality | 0.15 | 0.15 | 0.55 |
| Corporate Governance | 0.05 | 0.05 | 0.10 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

### Signal Architecture Rationale
This configuration contains **22 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `DIRECT_OBSERVABLE` (9 signals): Highest confidence
- `INFERRED_PROXY` (13 signals): Medium confidence

**Signal Count by Group:**
- `safety_record`: 4 signals
- `regulatory_compliance`: 4 signals
- `operational_quality`: 4 signals
- `fleet_quality`: 3 signals
- `corporate_governance`: 3 signals
- `operator_type`: 1 signals
- `fleet_category`: 1 signals
- `fleet_size`: 1 signals
- `regulatory_framework`: 1 signals

**Selection Rationale:**
- 41% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 | Safety Record | 0.90 | 0.35 | 0.45 | 0.10 |
| 2 | Fleet Quality | 0.85 | 0.15 | 0.15 | 0.55 |
| 3 | Regulatory Compliance | 0.55 | 0.25 | 0.20 | 0.10 |
| 4 | Operational Quality | 0.50 | 0.20 | 0.15 | 0.15 |
| 5 | Corporate Governance | 0.20 | 0.05 | 0.05 | 0.10 |

**Primary Assessment Driver:** `Safety Record` with combined weight of 0.90
**Secondary Driver:** `Fleet Quality` with combined weight of 0.85

### Theoretical Premium Calculation (Tier 3 Standard)
> *Per the DSI Premium Calculation Methodology v2.0, the core formula is:*
> *P_final = (Base × Rate) × ILF_relativity × Deductible_Factor × Modifiers*

**1. The Pricing Anchor:** The Flat Premium of `$7,500` purchases exactly the `$5,000,000` Limit / `$10,000` Deductible Base Package.
**2. Theoretical Execution:**
  - Technical Premium = **$7,500**
  - *Scaling relies entirely on selecting a different Limit ID from the Bundled limit_configuration packages.*


# DSI Logic Document: `PROPERTY`
*Generated: 2026-04-17*

## DSI Foundational Principles Adherence
This configuration is validated against the DSI Whitepaper & Vision Paper:
- **Objective Observation:** Signals derived from verifiable digital footprints, avoiding subjective interpretation.
- **Three-Layer Engine:** Modifiers explicitly target Risk, Loss, and Exposure dimensions.
- **Phase 5 Anchoring:** Polymorphic pricing limits scale from mathematically absolute anchor points.

---

## Model: `property_general`
*General commercial property — offices, retail, light industrial, multi-tenant*

### Routing Protocol (Multiplexer)
- `tiv >= 5000000`
- `tiv < 500000000`

### Three-Layer Weight Distribution
> *DSI requires that weights for Risk, Loss, and Exposure each sum to 1.0 across all signal groups.*

**Validation:** PASS

| Group | Risk | Loss | Exposure |
|-------|------|------|----------|
| Construction Quality | 0.50 | 0.45 | 0.20 |
| Occupancy Risk | 0.40 | 0.45 | 0.65 |
| Corporate Footprint | 0.05 | 0.05 | 0.10 |
| Firm Stability | 0.05 | 0.05 | 0.05 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

### Signal Architecture Rationale
This configuration contains **37 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `DIRECT_OBSERVABLE` (20 signals): Highest confidence
- `INFERRED_PROXY` (16 signals): Medium confidence
- `COHORT_INFERENCE` (1 signals): Lowest confidence

**Signal Count by Group:**
- `technical_infrastructure`: 20 signals
- `structured_data`: 17 signals

**Selection Rationale:**
- 54% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 | Occupancy Risk | 1.50 | 0.40 | 0.45 | 0.65 |
| 2 | Construction Quality | 1.15 | 0.50 | 0.45 | 0.20 |
| 3 | Corporate Footprint | 0.20 | 0.05 | 0.05 | 0.10 |
| 4 | Firm Stability | 0.15 | 0.05 | 0.05 | 0.05 |

**Primary Assessment Driver:** `Occupancy Risk` with combined weight of 1.50
**Secondary Driver:** `Construction Quality` with combined weight of 1.15

### Theoretical Premium Calculation (Tier 3 Standard)
> *Per the DSI Premium Calculation Methodology v2.0, the core formula is:*
> *P_final = (Base × Rate) × ILF_relativity × Deductible_Factor × Modifiers*

**1. The Pricing Anchor:** The Base Rate of `0.25%` on `tiv` purchases exactly a `$1,000,000` Limit with a `$25,000` Deductible.
**2. Theoretical Execution:**
  - Assume `tiv` = $10,000,000
  - Base Premium = $10,000,000 × 0.0025 = **$25,000**
  - If the client requests the Anchor Limit/Deductible, the factors are 1.00, resulting in a technical premium of **$25,000**.

---

## Model: `property_high_value`
*High-value commercial property — TIV >$500M, landmark, data centre, critical infrastructure*

### Routing Protocol (Multiplexer)
- `tiv >= 500000000`

### Three-Layer Weight Distribution
> *DSI requires that weights for Risk, Loss, and Exposure each sum to 1.0 across all signal groups.*

**Validation:** PASS

| Group | Risk | Loss | Exposure |
|-------|------|------|----------|
| Construction Quality | 0.40 | 0.35 | 0.20 |
| Occupancy Risk | 0.45 | 0.50 | 0.70 |
| Corporate Footprint | 0.10 | 0.10 | 0.05 |
| Firm Stability | 0.05 | 0.05 | 0.05 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

### Signal Architecture Rationale
This configuration contains **37 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `DIRECT_OBSERVABLE` (20 signals): Highest confidence
- `INFERRED_PROXY` (16 signals): Medium confidence
- `COHORT_INFERENCE` (1 signals): Lowest confidence

**Signal Count by Group:**
- `technical_infrastructure`: 20 signals
- `structured_data`: 17 signals

**Selection Rationale:**
- 54% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 | Occupancy Risk | 1.65 | 0.45 | 0.50 | 0.70 |
| 2 | Construction Quality | 0.95 | 0.40 | 0.35 | 0.20 |
| 3 | Corporate Footprint | 0.25 | 0.10 | 0.10 | 0.05 |
| 4 | Firm Stability | 0.15 | 0.05 | 0.05 | 0.05 |

**Primary Assessment Driver:** `Occupancy Risk` with combined weight of 1.65
**Secondary Driver:** `Construction Quality` with combined weight of 0.95

### Theoretical Premium Calculation (Tier 3 Standard)
> *Per the DSI Premium Calculation Methodology v2.0, the core formula is:*
> *P_final = (Base × Rate) × ILF_relativity × Deductible_Factor × Modifiers*

**1. The Pricing Anchor:** The Base Rate of `0.18%` on `tiv` purchases exactly a `$25,000,000` Limit with a `$500,000` Deductible.
**2. Theoretical Execution:**
  - Assume `tiv` = $10,000,000
  - Base Premium = $10,000,000 × 0.0018 = **$18,000**
  - If the client requests the Anchor Limit/Deductible, the factors are 1.00, resulting in a technical premium of **$18,000**.

---

## Model: `property_cat_exposed`
*CAT-exposed commercial property — coastal wind, earthquake, wildfire zones*

### Routing Protocol (Multiplexer)
- `tiv >= 5000000`
- `cat_zone in ['HIGH_WIND', 'HIGH_EQ', 'HIGH_WILDFIRE', 'HIGH_FLOOD']`

### Three-Layer Weight Distribution
> *DSI requires that weights for Risk, Loss, and Exposure each sum to 1.0 across all signal groups.*

**Validation:** PASS

| Group | Risk | Loss | Exposure |
|-------|------|------|----------|
| Construction Quality | 0.30 | 0.30 | 0.10 |
| Occupancy Risk | 0.55 | 0.55 | 0.80 |
| Corporate Footprint | 0.10 | 0.10 | 0.05 |
| Firm Stability | 0.05 | 0.05 | 0.05 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

### Signal Architecture Rationale
This configuration contains **37 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `DIRECT_OBSERVABLE` (20 signals): Highest confidence
- `INFERRED_PROXY` (16 signals): Medium confidence
- `COHORT_INFERENCE` (1 signals): Lowest confidence

**Signal Count by Group:**
- `technical_infrastructure`: 20 signals
- `structured_data`: 17 signals

**Selection Rationale:**
- 54% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 | Occupancy Risk | 1.90 | 0.55 | 0.55 | 0.80 |
| 2 | Construction Quality | 0.70 | 0.30 | 0.30 | 0.10 |
| 3 | Corporate Footprint | 0.25 | 0.10 | 0.10 | 0.05 |
| 4 | Firm Stability | 0.15 | 0.05 | 0.05 | 0.05 |

**Primary Assessment Driver:** `Occupancy Risk` with combined weight of 1.90
**Secondary Driver:** `Construction Quality` with combined weight of 0.70

### Theoretical Premium Calculation (Tier 3 Standard)
> *Per the DSI Premium Calculation Methodology v2.0, the core formula is:*
> *P_final = (Base × Rate) × ILF_relativity × Deductible_Factor × Modifiers*

**1. The Pricing Anchor:** The Base Rate of `0.44999999999999996%` on `tiv` purchases exactly a `$1,000,000` Limit with a `$50,000` Deductible.
**2. Theoretical Execution:**
  - Assume `tiv` = $10,000,000
  - Base Premium = $10,000,000 × 0.0045 = **$45,000**
  - If the client requests the Anchor Limit/Deductible, the factors are 1.00, resulting in a technical premium of **$45,000**.

---

## Model: `property_builders_risk`
*Construction-phase property coverage — new build, renovation, fit-out*

### Routing Protocol (Multiplexer)
- `product_type == builders_risk`

### Three-Layer Weight Distribution
> *DSI requires that weights for Risk, Loss, and Exposure each sum to 1.0 across all signal groups.*

**Validation:** PASS

| Group | Risk | Loss | Exposure |
|-------|------|------|----------|
| Construction Quality | 0.55 | 0.50 | 0.30 |
| Occupancy Risk | 0.35 | 0.40 | 0.60 |
| Corporate Footprint | 0.05 | 0.05 | 0.05 |
| Firm Stability | 0.05 | 0.05 | 0.05 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

### Signal Architecture Rationale
This configuration contains **37 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `DIRECT_OBSERVABLE` (20 signals): Highest confidence
- `INFERRED_PROXY` (16 signals): Medium confidence
- `COHORT_INFERENCE` (1 signals): Lowest confidence

**Signal Count by Group:**
- `technical_infrastructure`: 20 signals
- `structured_data`: 17 signals

**Selection Rationale:**
- 54% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 | Construction Quality | 1.35 | 0.55 | 0.50 | 0.30 |
| 2 | Occupancy Risk | 1.35 | 0.35 | 0.40 | 0.60 |
| 3 | Corporate Footprint | 0.15 | 0.05 | 0.05 | 0.05 |
| 4 | Firm Stability | 0.15 | 0.05 | 0.05 | 0.05 |

**Primary Assessment Driver:** `Construction Quality` with combined weight of 1.35
**Secondary Driver:** `Occupancy Risk` with combined weight of 1.35

### Theoretical Premium Calculation (Tier 3 Standard)
> *Per the DSI Premium Calculation Methodology v2.0, the core formula is:*
> *P_final = (Base × Rate) × ILF_relativity × Deductible_Factor × Modifiers*

**1. The Pricing Anchor:** The Base Rate of `0.5499999999999999%` on `tiv` purchases exactly a `$1,000,000` Limit with a `$25,000` Deductible.
**2. Theoretical Execution:**
  - Assume `tiv` = $10,000,000
  - Base Premium = $10,000,000 × 0.0055 = **$55,000**
  - If the client requests the Anchor Limit/Deductible, the factors are 1.00, resulting in a technical premium of **$55,000**.

---

## Model: `property_sme`
*Small-to-medium commercial property — TIV under $5M, simplified assessment*

### Routing Protocol (Multiplexer)
- `tiv < 5000000`

### Three-Layer Weight Distribution
> *DSI requires that weights for Risk, Loss, and Exposure each sum to 1.0 across all signal groups.*

**Validation:** PASS

| Group | Risk | Loss | Exposure |
|-------|------|------|----------|
| Construction Quality | 0.55 | 0.50 | 0.30 |
| Occupancy Risk | 0.45 | 0.50 | 0.70 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

### Signal Architecture Rationale
This configuration contains **37 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `DIRECT_OBSERVABLE` (20 signals): Highest confidence
- `INFERRED_PROXY` (16 signals): Medium confidence
- `COHORT_INFERENCE` (1 signals): Lowest confidence

**Signal Count by Group:**
- `technical_infrastructure`: 20 signals
- `structured_data`: 17 signals

**Selection Rationale:**
- 54% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 | Occupancy Risk | 1.65 | 0.45 | 0.50 | 0.70 |
| 2 | Construction Quality | 1.35 | 0.55 | 0.50 | 0.30 |

**Primary Assessment Driver:** `Occupancy Risk` with combined weight of 1.65
**Secondary Driver:** `Construction Quality` with combined weight of 1.35

### Theoretical Premium Calculation (Tier 3 Standard)
> *Per the DSI Premium Calculation Methodology v2.0, the core formula is:*
> *P_final = (Base × Rate) × ILF_relativity × Deductible_Factor × Modifiers*

**1. The Pricing Anchor:** The Base Rate of `0.32%` on `tiv` purchases exactly a `$500,000` Limit with a `$10,000` Deductible.
**2. Theoretical Execution:**
  - Assume `tiv` = $10,000,000
  - Base Premium = $10,000,000 × 0.0032 = **$32,000**
  - If the client requests the Anchor Limit/Deductible, the factors are 1.00, resulting in a technical premium of **$32,000**.


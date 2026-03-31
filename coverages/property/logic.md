# DSI Logic Document: `PROPERTY`
*Generated: 2026-03-31*

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
| Construction Quality | 0.25 | 0.20 | 0.10 |
| Occupancy Risk | 0.20 | 0.20 | 0.15 |
| Catastrophe Exposure | 0.15 | 0.15 | 0.30 |
| Fire Protection | 0.25 | 0.25 | 0.10 |
| Business Interruption | 0.05 | 0.10 | 0.20 |
| Corporate Footprint | 0.05 | 0.05 | 0.10 |
| Firm Stability | 0.05 | 0.05 | 0.05 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

### Signal Architecture Rationale
This configuration contains **27 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `DIRECT_OBSERVABLE` (14 signals): Highest confidence
- `INFERRED_PROXY` (12 signals): Medium confidence
- `COHORT_INFERENCE` (1 signals): Lowest confidence

**Signal Count by Group:**
- `construction_quality`: 6 signals
- `cat_exposure`: 6 signals
- `occupancy_risk`: 5 signals
- `fire_protection`: 5 signals
- `business_interruption`: 5 signals

**Selection Rationale:**
- 52% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 | Catastrophe Exposure | 0.60 | 0.15 | 0.15 | 0.30 |
| 2 | Fire Protection | 0.60 | 0.25 | 0.25 | 0.10 |
| 3 | Construction Quality | 0.55 | 0.25 | 0.20 | 0.10 |
| 4 | Occupancy Risk | 0.55 | 0.20 | 0.20 | 0.15 |
| 5 | Business Interruption | 0.35 | 0.05 | 0.10 | 0.20 |
| 6 | Corporate Footprint | 0.20 | 0.05 | 0.05 | 0.10 |
| 7 | Firm Stability | 0.15 | 0.05 | 0.05 | 0.05 |

**Primary Assessment Driver:** `Catastrophe Exposure` with combined weight of 0.60
**Secondary Driver:** `Fire Protection` with combined weight of 0.60

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
| Construction Quality | 0.20 | 0.15 | 0.10 |
| Occupancy Risk | 0.15 | 0.15 | 0.10 |
| Catastrophe Exposure | 0.20 | 0.20 | 0.35 |
| Fire Protection | 0.20 | 0.20 | 0.10 |
| Business Interruption | 0.10 | 0.15 | 0.25 |
| Corporate Footprint | 0.10 | 0.10 | 0.05 |
| Firm Stability | 0.05 | 0.05 | 0.05 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

### Signal Architecture Rationale
This configuration contains **27 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `DIRECT_OBSERVABLE` (14 signals): Highest confidence
- `INFERRED_PROXY` (12 signals): Medium confidence
- `COHORT_INFERENCE` (1 signals): Lowest confidence

**Signal Count by Group:**
- `construction_quality`: 6 signals
- `cat_exposure`: 6 signals
- `occupancy_risk`: 5 signals
- `fire_protection`: 5 signals
- `business_interruption`: 5 signals

**Selection Rationale:**
- 52% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 | Catastrophe Exposure | 0.75 | 0.20 | 0.20 | 0.35 |
| 2 | Fire Protection | 0.50 | 0.20 | 0.20 | 0.10 |
| 3 | Business Interruption | 0.50 | 0.10 | 0.15 | 0.25 |
| 4 | Construction Quality | 0.45 | 0.20 | 0.15 | 0.10 |
| 5 | Occupancy Risk | 0.40 | 0.15 | 0.15 | 0.10 |
| 6 | Corporate Footprint | 0.25 | 0.10 | 0.10 | 0.05 |
| 7 | Firm Stability | 0.15 | 0.05 | 0.05 | 0.05 |

**Primary Assessment Driver:** `Catastrophe Exposure` with combined weight of 0.75
**Secondary Driver:** `Fire Protection` with combined weight of 0.50

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
| Construction Quality | 0.15 | 0.15 | 0.05 |
| Occupancy Risk | 0.10 | 0.10 | 0.05 |
| Catastrophe Exposure | 0.35 | 0.35 | 0.50 |
| Fire Protection | 0.15 | 0.15 | 0.05 |
| Business Interruption | 0.10 | 0.10 | 0.25 |
| Corporate Footprint | 0.10 | 0.10 | 0.05 |
| Firm Stability | 0.05 | 0.05 | 0.05 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

### Signal Architecture Rationale
This configuration contains **27 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `DIRECT_OBSERVABLE` (14 signals): Highest confidence
- `INFERRED_PROXY` (12 signals): Medium confidence
- `COHORT_INFERENCE` (1 signals): Lowest confidence

**Signal Count by Group:**
- `construction_quality`: 6 signals
- `cat_exposure`: 6 signals
- `occupancy_risk`: 5 signals
- `fire_protection`: 5 signals
- `business_interruption`: 5 signals

**Selection Rationale:**
- 52% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 | Catastrophe Exposure | 1.20 | 0.35 | 0.35 | 0.50 |
| 2 | Business Interruption | 0.45 | 0.10 | 0.10 | 0.25 |
| 3 | Construction Quality | 0.35 | 0.15 | 0.15 | 0.05 |
| 4 | Fire Protection | 0.35 | 0.15 | 0.15 | 0.05 |
| 5 | Occupancy Risk | 0.25 | 0.10 | 0.10 | 0.05 |
| 6 | Corporate Footprint | 0.25 | 0.10 | 0.10 | 0.05 |
| 7 | Firm Stability | 0.15 | 0.05 | 0.05 | 0.05 |

**Primary Assessment Driver:** `Catastrophe Exposure` with combined weight of 1.20
**Secondary Driver:** `Business Interruption` with combined weight of 0.45

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
| Construction Quality | 0.30 | 0.25 | 0.15 |
| Occupancy Risk | 0.05 | 0.05 | 0.05 |
| Catastrophe Exposure | 0.20 | 0.20 | 0.35 |
| Fire Protection | 0.25 | 0.25 | 0.15 |
| Business Interruption | 0.10 | 0.15 | 0.20 |
| Corporate Footprint | 0.05 | 0.05 | 0.05 |
| Firm Stability | 0.05 | 0.05 | 0.05 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

### Signal Architecture Rationale
This configuration contains **27 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `DIRECT_OBSERVABLE` (14 signals): Highest confidence
- `INFERRED_PROXY` (12 signals): Medium confidence
- `COHORT_INFERENCE` (1 signals): Lowest confidence

**Signal Count by Group:**
- `construction_quality`: 6 signals
- `cat_exposure`: 6 signals
- `occupancy_risk`: 5 signals
- `fire_protection`: 5 signals
- `business_interruption`: 5 signals

**Selection Rationale:**
- 52% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 | Catastrophe Exposure | 0.75 | 0.20 | 0.20 | 0.35 |
| 2 | Construction Quality | 0.70 | 0.30 | 0.25 | 0.15 |
| 3 | Fire Protection | 0.65 | 0.25 | 0.25 | 0.15 |
| 4 | Business Interruption | 0.45 | 0.10 | 0.15 | 0.20 |
| 5 | Occupancy Risk | 0.15 | 0.05 | 0.05 | 0.05 |
| 6 | Corporate Footprint | 0.15 | 0.05 | 0.05 | 0.05 |
| 7 | Firm Stability | 0.15 | 0.05 | 0.05 | 0.05 |

**Primary Assessment Driver:** `Catastrophe Exposure` with combined weight of 0.75
**Secondary Driver:** `Construction Quality` with combined weight of 0.70

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
| Construction Quality | 0.30 | 0.25 | 0.15 |
| Occupancy Risk | 0.20 | 0.20 | 0.15 |
| Catastrophe Exposure | 0.15 | 0.15 | 0.30 |
| Fire Protection | 0.25 | 0.25 | 0.15 |
| Business Interruption | 0.10 | 0.15 | 0.25 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

### Signal Architecture Rationale
This configuration contains **27 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `DIRECT_OBSERVABLE` (14 signals): Highest confidence
- `INFERRED_PROXY` (12 signals): Medium confidence
- `COHORT_INFERENCE` (1 signals): Lowest confidence

**Signal Count by Group:**
- `construction_quality`: 6 signals
- `cat_exposure`: 6 signals
- `occupancy_risk`: 5 signals
- `fire_protection`: 5 signals
- `business_interruption`: 5 signals

**Selection Rationale:**
- 52% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 | Construction Quality | 0.70 | 0.30 | 0.25 | 0.15 |
| 2 | Fire Protection | 0.65 | 0.25 | 0.25 | 0.15 |
| 3 | Catastrophe Exposure | 0.60 | 0.15 | 0.15 | 0.30 |
| 4 | Occupancy Risk | 0.55 | 0.20 | 0.20 | 0.15 |
| 5 | Business Interruption | 0.50 | 0.10 | 0.15 | 0.25 |

**Primary Assessment Driver:** `Construction Quality` with combined weight of 0.70
**Secondary Driver:** `Fire Protection` with combined weight of 0.65

### Theoretical Premium Calculation (Tier 3 Standard)
> *Per the DSI Premium Calculation Methodology v2.0, the core formula is:*
> *P_final = (Base × Rate) × ILF_relativity × Deductible_Factor × Modifiers*

**1. The Pricing Anchor:** The Base Rate of `0.32%` on `tiv` purchases exactly a `$500,000` Limit with a `$10,000` Deductible.
**2. Theoretical Execution:**
  - Assume `tiv` = $10,000,000
  - Base Premium = $10,000,000 × 0.0032 = **$32,000**
  - If the client requests the Anchor Limit/Deductible, the factors are 1.00, resulting in a technical premium of **$32,000**.


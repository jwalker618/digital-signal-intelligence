# DSI Logic Document: `ENERGY`
*Generated: 2026-04-17*

## DSI Foundational Principles Adherence
This configuration is validated against the DSI Whitepaper & Vision Paper:
- **Objective Observation:** Signals derived from verifiable digital footprints, avoiding subjective interpretation.
- **Three-Layer Engine:** Modifiers explicitly target Risk, Loss, and Exposure dimensions.
- **Phase 5 Anchoring:** Polymorphic pricing limits scale from mathematically absolute anchor points.

---

## Model: `energy_general`
*Energy property and liability coverage based on observable safety, environmental, and operational signals*

### Routing Protocol (Multiplexer)
- `tiv > 25000000`

### Three-Layer Weight Distribution
> *DSI requires that weights for Risk, Loss, and Exposure each sum to 1.0 across all signal groups.*

**Validation:** PASS

| Group | Risk | Loss | Exposure |
|-------|------|------|----------|
| Network Authority | 0.10 | 0.05 | 0.05 |
| Safety Performance | 0.50 | 0.60 | 0.20 |
| Operational Telemetry | 0.10 | 0.10 | 0.20 |
| Financial Stability | 0.10 | 0.05 | 0.20 |
| Asset Portfolio | 0.15 | 0.18 | 0.33 |
| Structured Data | 0.05 | 0.02 | 0.02 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

### Signal Architecture Rationale
This configuration contains **47 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `DIRECT_OBSERVABLE` (21 signals): Highest confidence
- `INFERRED_PROXY` (25 signals): Medium confidence
- `COHORT_INFERENCE` (1 signals): Lowest confidence

**Signal Count by Group:**
- `public_record`: 13 signals
- `corporate_footprint`: 11 signals
- `network_authority`: 7 signals
- `technical_infrastructure`: 5 signals
- `behavioural`: 5 signals
- `structured_data`: 3 signals
- `operator_type`: 1 signals
- `operation_segment`: 1 signals
- `geographic_focus`: 1 signals

**Selection Rationale:**
- 45% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 | Safety Performance | 1.30 | 0.50 | 0.60 | 0.20 |
| 2 | Asset Portfolio | 0.66 | 0.15 | 0.18 | 0.33 |
| 3 | Operational Telemetry | 0.40 | 0.10 | 0.10 | 0.20 |
| 4 | Financial Stability | 0.35 | 0.10 | 0.05 | 0.20 |
| 5 | Network Authority | 0.20 | 0.10 | 0.05 | 0.05 |
| 6 | Structured Data | 0.09 | 0.05 | 0.02 | 0.02 |

**Primary Assessment Driver:** `Safety Performance` with combined weight of 1.30
**Secondary Driver:** `Asset Portfolio` with combined weight of 0.66

### Theoretical Premium Calculation (Tier 3 Standard)
> *Per the DSI Premium Calculation Methodology v2.0, the core formula is:*
> *P_final = (Base × Rate) × ILF_relativity × Deductible_Factor × Modifiers*

**1. The Pricing Anchor:** The Base Rate of `0.18%` on `tiv` purchases exactly a `$10,000,000` Limit with a `$50,000` Deductible.
**2. Theoretical Execution:**
  - Assume `tiv` = $10,000,000
  - Base Premium = $10,000,000 × 0.0018 = **$18,000**
  - If the client requests the Anchor Limit/Deductible, the factors are 1.00, resulting in a technical premium of **$18,000**.

---

## Model: `energy_upstream_deepwater`
*Deepwater upstream energy operations — subsea, floating, and fixed platform risks*

### Routing Protocol (Multiplexer)
- `tiv > 100000000`
- `operation_segment == UPSTREAM_DEEPWATER`

### Three-Layer Weight Distribution
> *DSI requires that weights for Risk, Loss, and Exposure each sum to 1.0 across all signal groups.*

**Validation:** PASS

| Group | Risk | Loss | Exposure |
|-------|------|------|----------|
| Network Authority | 0.10 | 0.05 | 0.00 |
| Safety Performance | 0.40 | 0.55 | 0.00 |
| Deepwater Operations | 0.20 | 0.15 | 0.35 |
| Financial Stability | 0.10 | 0.05 | 0.15 |
| Asset Portfolio | 0.20 | 0.20 | 0.50 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

### Signal Architecture Rationale
This configuration contains **35 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `DIRECT_OBSERVABLE` (14 signals): Highest confidence
- `INFERRED_PROXY` (21 signals): Medium confidence

**Signal Count by Group:**
- `public_record`: 11 signals
- `network_authority`: 6 signals
- `technical_infrastructure`: 5 signals
- `behavioural`: 5 signals
- `corporate_footprint`: 5 signals
- `operator_type`: 1 signals
- `water_depth_class`: 1 signals
- `geographic_focus`: 1 signals

**Selection Rationale:**
- 40% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 | Safety Performance | 0.95 | 0.40 | 0.55 | 0.00 |
| 2 | Asset Portfolio | 0.90 | 0.20 | 0.20 | 0.50 |
| 3 | Deepwater Operations | 0.70 | 0.20 | 0.15 | 0.35 |
| 4 | Financial Stability | 0.30 | 0.10 | 0.05 | 0.15 |
| 5 | Network Authority | 0.15 | 0.10 | 0.05 | 0.00 |

**Primary Assessment Driver:** `Safety Performance` with combined weight of 0.95
**Secondary Driver:** `Asset Portfolio` with combined weight of 0.90

### Theoretical Premium Calculation (Tier 3 Standard)
> *Per the DSI Premium Calculation Methodology v2.0, the core formula is:*
> *P_final = (Base × Rate) × ILF_relativity × Deductible_Factor × Modifiers*

**1. The Pricing Anchor:** The Base Rate of `0.16%` on `tiv` purchases exactly a `$10,000,000` Limit with a `$1,000,000` Deductible.
**2. Theoretical Execution:**
  - Assume `tiv` = $10,000,000
  - Base Premium = $10,000,000 × 0.0016 = **$16,000**
  - If the client requests the Anchor Limit/Deductible, the factors are 1.00, resulting in a technical premium of **$16,000**.

---

## Model: `energy_upstream_onshore`
*Conventional onshore E&P — Permian, Oklahoma, Louisiana conventional operations*

### Routing Protocol (Multiplexer)
- `operation_segment == UPSTREAM_CONVENTIONAL`

### Three-Layer Weight Distribution
> *DSI requires that weights for Risk, Loss, and Exposure each sum to 1.0 across all signal groups.*

**Validation:** PASS

| Group | Risk | Loss | Exposure |
|-------|------|------|----------|
| Network Authority | 0.05 | 0.03 | 0.03 |
| Safety Performance | 0.45 | 0.50 | 0.20 |
| Operational Telemetry | 0.15 | 0.15 | 0.25 |
| Financial Stability | 0.10 | 0.07 | 0.17 |
| Asset Portfolio | 0.20 | 0.23 | 0.33 |
| Structured Data | 0.05 | 0.02 | 0.02 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

### Signal Architecture Rationale
This configuration contains **49 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `DIRECT_OBSERVABLE` (19 signals): Highest confidence
- `INFERRED_PROXY` (30 signals): Medium confidence

**Signal Count by Group:**
- `public_record`: 14 signals
- `corporate_footprint`: 12 signals
- `network_authority`: 6 signals
- `technical_infrastructure`: 6 signals
- `behavioural`: 5 signals
- `structured_data`: 3 signals
- `operator_type`: 1 signals
- `operation_segment`: 1 signals
- `geographic_focus`: 1 signals

**Selection Rationale:**
- 39% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 | Safety Performance | 1.15 | 0.45 | 0.50 | 0.20 |
| 2 | Asset Portfolio | 0.76 | 0.20 | 0.23 | 0.33 |
| 3 | Operational Telemetry | 0.55 | 0.15 | 0.15 | 0.25 |
| 4 | Financial Stability | 0.34 | 0.10 | 0.07 | 0.17 |
| 5 | Network Authority | 0.11 | 0.05 | 0.03 | 0.03 |
| 6 | Structured Data | 0.09 | 0.05 | 0.02 | 0.02 |

**Primary Assessment Driver:** `Safety Performance` with combined weight of 1.15
**Secondary Driver:** `Asset Portfolio` with combined weight of 0.76

### Theoretical Premium Calculation (Tier 3 Standard)
> *Per the DSI Premium Calculation Methodology v2.0, the core formula is:*
> *P_final = (Base × Rate) × ILF_relativity × Deductible_Factor × Modifiers*

**1. The Pricing Anchor:** The Base Rate of `0.16%` on `tiv` purchases exactly a `$10,000,000` Limit with a `$50,000` Deductible.
**2. Theoretical Execution:**
  - Assume `tiv` = $10,000,000
  - Base Premium = $10,000,000 × 0.0016 = **$16,000**
  - If the client requests the Anchor Limit/Deductible, the factors are 1.00, resulting in a technical premium of **$16,000**.

---

## Model: `energy_upstream_unconventional`
*Tight oil, shale gas, and hydraulic fracturing operations*

### Routing Protocol (Multiplexer)
- `operation_segment == UPSTREAM_UNCONVENTIONAL`

### Three-Layer Weight Distribution
> *DSI requires that weights for Risk, Loss, and Exposure each sum to 1.0 across all signal groups.*

**Validation:** PASS

| Group | Risk | Loss | Exposure |
|-------|------|------|----------|
| Network Authority | 0.05 | 0.03 | 0.03 |
| Safety Performance | 0.50 | 0.55 | 0.25 |
| Operational Telemetry | 0.15 | 0.15 | 0.20 |
| Financial Stability | 0.10 | 0.07 | 0.15 |
| Asset Portfolio | 0.15 | 0.15 | 0.35 |
| Structured Data | 0.05 | 0.05 | 0.02 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

### Signal Architecture Rationale
This configuration contains **52 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `DIRECT_OBSERVABLE` (20 signals): Highest confidence
- `INFERRED_PROXY` (32 signals): Medium confidence

**Signal Count by Group:**
- `public_record`: 14 signals
- `corporate_footprint`: 13 signals
- `technical_infrastructure`: 8 signals
- `network_authority`: 6 signals
- `behavioural`: 5 signals
- `structured_data`: 3 signals
- `operator_type`: 1 signals
- `operation_segment`: 1 signals
- `geographic_focus`: 1 signals

**Selection Rationale:**
- 38% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 | Safety Performance | 1.30 | 0.50 | 0.55 | 0.25 |
| 2 | Asset Portfolio | 0.65 | 0.15 | 0.15 | 0.35 |
| 3 | Operational Telemetry | 0.50 | 0.15 | 0.15 | 0.20 |
| 4 | Financial Stability | 0.32 | 0.10 | 0.07 | 0.15 |
| 5 | Structured Data | 0.12 | 0.05 | 0.05 | 0.02 |
| 6 | Network Authority | 0.11 | 0.05 | 0.03 | 0.03 |

**Primary Assessment Driver:** `Safety Performance` with combined weight of 1.30
**Secondary Driver:** `Asset Portfolio` with combined weight of 0.65

### Theoretical Premium Calculation (Tier 3 Standard)
> *Per the DSI Premium Calculation Methodology v2.0, the core formula is:*
> *P_final = (Base × Rate) × ILF_relativity × Deductible_Factor × Modifiers*

**1. The Pricing Anchor:** The Base Rate of `0.22%` on `tiv` purchases exactly a `$10,000,000` Limit with a `$100,000` Deductible.
**2. Theoretical Execution:**
  - Assume `tiv` = $10,000,000
  - Base Premium = $10,000,000 × 0.0022 = **$22,000**
  - If the client requests the Anchor Limit/Deductible, the factors are 1.00, resulting in a technical premium of **$22,000**.

---

## Model: `energy_midstream`
*Pipeline, processing, and storage operations*

### Routing Protocol (Multiplexer)
- `operation_segment in ['MIDSTREAM_PIPELINE', 'MIDSTREAM_PROCESSING', 'MIDSTREAM_STORAGE']`

### Three-Layer Weight Distribution
> *DSI requires that weights for Risk, Loss, and Exposure each sum to 1.0 across all signal groups.*

**Validation:** PASS

| Group | Risk | Loss | Exposure |
|-------|------|------|----------|
| Network Authority | 0.05 | 0.03 | 0.03 |
| Safety Performance | 0.35 | 0.35 | 0.17 |
| Operational Telemetry | 0.20 | 0.25 | 0.25 |
| Financial Stability | 0.15 | 0.10 | 0.25 |
| Asset Portfolio | 0.20 | 0.25 | 0.28 |
| Structured Data | 0.05 | 0.02 | 0.02 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

### Signal Architecture Rationale
This configuration contains **48 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `DIRECT_OBSERVABLE` (18 signals): Highest confidence
- `INFERRED_PROXY` (30 signals): Medium confidence

**Signal Count by Group:**
- `corporate_footprint`: 13 signals
- `public_record`: 12 signals
- `network_authority`: 6 signals
- `technical_infrastructure`: 6 signals
- `behavioural`: 5 signals
- `structured_data`: 3 signals
- `operator_type`: 1 signals
- `operation_segment`: 1 signals
- `geographic_focus`: 1 signals

**Selection Rationale:**
- 38% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 | Safety Performance | 0.87 | 0.35 | 0.35 | 0.17 |
| 2 | Asset Portfolio | 0.73 | 0.20 | 0.25 | 0.28 |
| 3 | Operational Telemetry | 0.70 | 0.20 | 0.25 | 0.25 |
| 4 | Financial Stability | 0.50 | 0.15 | 0.10 | 0.25 |
| 5 | Network Authority | 0.11 | 0.05 | 0.03 | 0.03 |
| 6 | Structured Data | 0.09 | 0.05 | 0.02 | 0.02 |

**Primary Assessment Driver:** `Safety Performance` with combined weight of 0.87
**Secondary Driver:** `Asset Portfolio` with combined weight of 0.73

### Theoretical Premium Calculation (Tier 3 Standard)
> *Per the DSI Premium Calculation Methodology v2.0, the core formula is:*
> *P_final = (Base × Rate) × ILF_relativity × Deductible_Factor × Modifiers*

**1. The Pricing Anchor:** The Base Rate of `0.12%` on `tiv` purchases exactly a `$10,000,000` Limit with a `$100,000` Deductible.
**2. Theoretical Execution:**
  - Assume `tiv` = $10,000,000
  - Base Premium = $10,000,000 × 0.0012 = **$12,000**
  - If the client requests the Anchor Limit/Deductible, the factors are 1.00, resulting in a technical premium of **$12,000**.

---

## Model: `energy_downstream`
*Refining and petrochemical operations*

### Routing Protocol (Multiplexer)
- `operation_segment in ['DOWNSTREAM_REFINING', 'DOWNSTREAM_PETROCHEMICAL']`

### Three-Layer Weight Distribution
> *DSI requires that weights for Risk, Loss, and Exposure each sum to 1.0 across all signal groups.*

**Validation:** PASS

| Group | Risk | Loss | Exposure |
|-------|------|------|----------|
| Network Authority | 0.05 | 0.03 | 0.03 |
| Safety Performance | 0.40 | 0.45 | 0.17 |
| Operational Telemetry | 0.15 | 0.15 | 0.20 |
| Financial Stability | 0.10 | 0.07 | 0.15 |
| Asset Portfolio | 0.25 | 0.25 | 0.40 |
| Structured Data | 0.05 | 0.05 | 0.05 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

### Signal Architecture Rationale
This configuration contains **49 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `DIRECT_OBSERVABLE` (18 signals): Highest confidence
- `INFERRED_PROXY` (31 signals): Medium confidence

**Signal Count by Group:**
- `corporate_footprint`: 13 signals
- `public_record`: 12 signals
- `network_authority`: 6 signals
- `technical_infrastructure`: 6 signals
- `behavioural`: 6 signals
- `structured_data`: 3 signals
- `operator_type`: 1 signals
- `operation_segment`: 1 signals
- `geographic_focus`: 1 signals

**Selection Rationale:**
- 37% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 | Safety Performance | 1.02 | 0.40 | 0.45 | 0.17 |
| 2 | Asset Portfolio | 0.90 | 0.25 | 0.25 | 0.40 |
| 3 | Operational Telemetry | 0.50 | 0.15 | 0.15 | 0.20 |
| 4 | Financial Stability | 0.32 | 0.10 | 0.07 | 0.15 |
| 5 | Structured Data | 0.15 | 0.05 | 0.05 | 0.05 |
| 6 | Network Authority | 0.11 | 0.05 | 0.03 | 0.03 |

**Primary Assessment Driver:** `Safety Performance` with combined weight of 1.02
**Secondary Driver:** `Asset Portfolio` with combined weight of 0.90

### Theoretical Premium Calculation (Tier 3 Standard)
> *Per the DSI Premium Calculation Methodology v2.0, the core formula is:*
> *P_final = (Base × Rate) × ILF_relativity × Deductible_Factor × Modifiers*

**1. The Pricing Anchor:** The Base Rate of `0.22%` on `tiv` purchases exactly a `$10,000,000` Limit with a `$100,000` Deductible.
**2. Theoretical Execution:**
  - Assume `tiv` = $10,000,000
  - Base Premium = $10,000,000 × 0.0022 = **$22,000**
  - If the client requests the Anchor Limit/Deductible, the factors are 1.00, resulting in a technical premium of **$22,000**.

---

## Model: `energy_offshore_wind`
*Offshore wind farms — maritime construction + technology risk*

### Routing Protocol (Multiplexer)
- `operation_segment == RENEWABLE`
- `technology_type == OFFSHORE_WIND`

### Three-Layer Weight Distribution
> *DSI requires that weights for Risk, Loss, and Exposure each sum to 1.0 across all signal groups.*

**Validation:** PASS

| Group | Risk | Loss | Exposure |
|-------|------|------|----------|
| Network Authority | 0.05 | 0.03 | 0.02 |
| Safety Performance | 0.15 | 0.15 | 0.10 |
| Construction Quality | 0.35 | 0.40 | 0.33 |
| Financial Stability | 0.10 | 0.10 | 0.15 |
| Asset Portfolio | 0.30 | 0.27 | 0.38 |
| Structured Data | 0.05 | 0.05 | 0.02 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

### Signal Architecture Rationale
This configuration contains **46 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `DIRECT_OBSERVABLE` (20 signals): Highest confidence
- `INFERRED_PROXY` (25 signals): Medium confidence
- `COHORT_INFERENCE` (1 signals): Lowest confidence

**Signal Count by Group:**
- `corporate_footprint`: 12 signals
- `technical_infrastructure`: 8 signals
- `behavioural`: 7 signals
- `network_authority`: 6 signals
- `public_record`: 6 signals
- `structured_data`: 3 signals
- `operator_type`: 1 signals
- `foundation_type`: 1 signals
- `construction_phase`: 1 signals
- `geographic_focus`: 1 signals

**Selection Rationale:**
- 43% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 | Construction Quality | 1.08 | 0.35 | 0.40 | 0.33 |
| 2 | Asset Portfolio | 0.95 | 0.30 | 0.27 | 0.38 |
| 3 | Safety Performance | 0.40 | 0.15 | 0.15 | 0.10 |
| 4 | Financial Stability | 0.35 | 0.10 | 0.10 | 0.15 |
| 5 | Structured Data | 0.12 | 0.05 | 0.05 | 0.02 |
| 6 | Network Authority | 0.10 | 0.05 | 0.03 | 0.02 |

**Primary Assessment Driver:** `Construction Quality` with combined weight of 1.08
**Secondary Driver:** `Asset Portfolio` with combined weight of 0.95

### Theoretical Premium Calculation (Tier 3 Standard)
> *Per the DSI Premium Calculation Methodology v2.0, the core formula is:*
> *P_final = (Base × Rate) × ILF_relativity × Deductible_Factor × Modifiers*

**1. The Pricing Anchor:** The Base Rate of `0.2%` on `tiv` purchases exactly a `$25,000,000` Limit with a `$250,000` Deductible.
**2. Theoretical Execution:**
  - Assume `tiv` = $10,000,000
  - Base Premium = $10,000,000 × 0.002 = **$20,000**
  - If the client requests the Anchor Limit/Deductible, the factors are 1.00, resulting in a technical premium of **$20,000**.

---

## Model: `energy_onshore_renewable`
*Onshore wind and utility-scale solar*

### Routing Protocol (Multiplexer)
- `operation_segment == RENEWABLE`
- `technology_type in ['ONSHORE_WIND', 'UTILITY_SOLAR', 'DISTRIBUTED_SOLAR']`

### Three-Layer Weight Distribution
> *DSI requires that weights for Risk, Loss, and Exposure each sum to 1.0 across all signal groups.*

**Validation:** PASS

| Group | Risk | Loss | Exposure |
|-------|------|------|----------|
| Network Authority | 0.05 | 0.03 | 0.03 |
| Safety Performance | 0.10 | 0.10 | 0.05 |
| Construction Quality | 0.30 | 0.32 | 0.32 |
| Financial Stability | 0.15 | 0.12 | 0.15 |
| Asset Portfolio | 0.35 | 0.36 | 0.43 |
| Structured Data | 0.05 | 0.07 | 0.02 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

### Signal Architecture Rationale
This configuration contains **45 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `DIRECT_OBSERVABLE` (21 signals): Highest confidence
- `INFERRED_PROXY` (23 signals): Medium confidence
- `COHORT_INFERENCE` (1 signals): Lowest confidence

**Signal Count by Group:**
- `corporate_footprint`: 12 signals
- `technical_infrastructure`: 9 signals
- `network_authority`: 6 signals
- `behavioural`: 6 signals
- `public_record`: 5 signals
- `structured_data`: 3 signals
- `operator_type`: 1 signals
- `technology_type`: 1 signals
- `construction_phase`: 1 signals
- `geographic_focus`: 1 signals

**Selection Rationale:**
- 47% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 | Asset Portfolio | 1.14 | 0.35 | 0.36 | 0.43 |
| 2 | Construction Quality | 0.94 | 0.30 | 0.32 | 0.32 |
| 3 | Financial Stability | 0.42 | 0.15 | 0.12 | 0.15 |
| 4 | Safety Performance | 0.25 | 0.10 | 0.10 | 0.05 |
| 5 | Structured Data | 0.14 | 0.05 | 0.07 | 0.02 |
| 6 | Network Authority | 0.11 | 0.05 | 0.03 | 0.03 |

**Primary Assessment Driver:** `Asset Portfolio` with combined weight of 1.14
**Secondary Driver:** `Construction Quality` with combined weight of 0.94

### Theoretical Premium Calculation (Tier 3 Standard)
> *Per the DSI Premium Calculation Methodology v2.0, the core formula is:*
> *P_final = (Base × Rate) × ILF_relativity × Deductible_Factor × Modifiers*

**1. The Pricing Anchor:** The Base Rate of `0.13%` on `tiv` purchases exactly a `$10,000,000` Limit with a `$50,000` Deductible.
**2. Theoretical Execution:**
  - Assume `tiv` = $10,000,000
  - Base Premium = $10,000,000 × 0.0013 = **$13,000**
  - If the client requests the Anchor Limit/Deductible, the factors are 1.00, resulting in a technical premium of **$13,000**.

---

## Model: `energy_storage`
*Battery energy storage systems (BESS) and green hydrogen — emerging technology risk with catastrophic severity potential*

### Routing Protocol (Multiplexer)
- `operation_segment == RENEWABLE`
- `technology_type in ['BATTERY_STORAGE', 'HYDROGEN']`

### Three-Layer Weight Distribution
> *DSI requires that weights for Risk, Loss, and Exposure each sum to 1.0 across all signal groups.*

**Validation:** PASS

| Group | Risk | Loss | Exposure |
|-------|------|------|----------|
| Network Authority | 0.05 | 0.03 | 0.02 |
| Safety Performance | 0.15 | 0.15 | 0.10 |
| Construction Quality | 0.25 | 0.30 | 0.25 |
| Financial Stability | 0.10 | 0.07 | 0.13 |
| Asset Portfolio | 0.40 | 0.38 | 0.45 |
| Structured Data | 0.05 | 0.07 | 0.05 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

### Signal Architecture Rationale
This configuration contains **52 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `DIRECT_OBSERVABLE` (19 signals): Highest confidence
- `INFERRED_PROXY` (32 signals): Medium confidence
- `COHORT_INFERENCE` (1 signals): Lowest confidence

**Signal Count by Group:**
- `corporate_footprint`: 15 signals
- `technical_infrastructure`: 11 signals
- `network_authority`: 7 signals
- `public_record`: 7 signals
- `behavioural`: 5 signals
- `structured_data`: 3 signals
- `operator_type`: 1 signals
- `battery_chemistry`: 1 signals
- `construction_phase`: 1 signals
- `geographic_focus`: 1 signals

**Selection Rationale:**
- 37% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 | Asset Portfolio | 1.23 | 0.40 | 0.38 | 0.45 |
| 2 | Construction Quality | 0.80 | 0.25 | 0.30 | 0.25 |
| 3 | Safety Performance | 0.40 | 0.15 | 0.15 | 0.10 |
| 4 | Financial Stability | 0.30 | 0.10 | 0.07 | 0.13 |
| 5 | Structured Data | 0.17 | 0.05 | 0.07 | 0.05 |
| 6 | Network Authority | 0.10 | 0.05 | 0.03 | 0.02 |

**Primary Assessment Driver:** `Asset Portfolio` with combined weight of 1.23
**Secondary Driver:** `Construction Quality` with combined weight of 0.80

### Theoretical Premium Calculation (Tier 3 Standard)
> *Per the DSI Premium Calculation Methodology v2.0, the core formula is:*
> *P_final = (Base × Rate) × ILF_relativity × Deductible_Factor × Modifiers*

**1. The Pricing Anchor:** The Base Rate of `0.27999999999999997%` on `tiv` purchases exactly a `$10,000,000` Limit with a `$100,000` Deductible.
**2. Theoretical Execution:**
  - Assume `tiv` = $10,000,000
  - Base Premium = $10,000,000 × 0.0028 = **$28,000**
  - If the client requests the Anchor Limit/Deductible, the factors are 1.00, resulting in a technical premium of **$28,000**.

---

## Model: `energy_sme`
*Small energy operators — automated underwriting, BUNDLED pricing*

### Routing Protocol (Multiplexer)
- `tiv <= 100000000`
- `employee_count <= 500`

### Three-Layer Weight Distribution
> *DSI requires that weights for Risk, Loss, and Exposure each sum to 1.0 across all signal groups.*

**Validation:** PASS

| Group | Risk | Loss | Exposure |
|-------|------|------|----------|
| Safety Performance | 0.50 | 0.55 | 0.20 |
| Operational Telemetry | 0.15 | 0.15 | 0.25 |
| Financial Stability | 0.20 | 0.15 | 0.30 |
| Asset Portfolio | 0.15 | 0.15 | 0.25 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

### Signal Architecture Rationale
This configuration contains **25 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `DIRECT_OBSERVABLE` (14 signals): Highest confidence
- `INFERRED_PROXY` (11 signals): Medium confidence

**Signal Count by Group:**
- `public_record`: 8 signals
- `corporate_footprint`: 6 signals
- `behavioural`: 5 signals
- `technical_infrastructure`: 3 signals
- `operator_type`: 1 signals
- `operation_segment`: 1 signals
- `geographic_focus`: 1 signals

**Selection Rationale:**
- 56% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 | Safety Performance | 1.25 | 0.50 | 0.55 | 0.20 |
| 2 | Financial Stability | 0.65 | 0.20 | 0.15 | 0.30 |
| 3 | Operational Telemetry | 0.55 | 0.15 | 0.15 | 0.25 |
| 4 | Asset Portfolio | 0.55 | 0.15 | 0.15 | 0.25 |

**Primary Assessment Driver:** `Safety Performance` with combined weight of 1.25
**Secondary Driver:** `Financial Stability` with combined weight of 0.65

### Theoretical Premium Calculation (Tier 3 Standard)
> *Per the DSI Premium Calculation Methodology v2.0, the core formula is:*
> *P_final = (Base × Rate) × ILF_relativity × Deductible_Factor × Modifiers*

**1. The Pricing Anchor:** The Base Rate of `0.2%` on `tiv` purchases exactly a `$0` Limit with a `$0` Deductible.
**2. Theoretical Execution:**
  - Assume `tiv` = $10,000,000
  - Base Premium = $10,000,000 × 0.002 = **$20,000**
  - If the client requests the Anchor Limit/Deductible, the factors are 1.00, resulting in a technical premium of **$20,000**.


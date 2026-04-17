# DSI Logic Document: `AEROSPACE`
*Generated: 2026-04-17*

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
| Safety Record | 0.50 | 0.60 | 0.20 |
| Operational Quality | 0.30 | 0.30 | 0.60 |
| Financial Stability | 0.05 | 0.03 | 0.10 |
| Corporate Governance | 0.05 | 0.02 | 0.05 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

### Signal Architecture Rationale
This configuration contains **48 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `DIRECT_OBSERVABLE` (23 signals): Highest confidence
- `INFERRED_PROXY` (24 signals): Medium confidence
- `COHORT_INFERENCE` (1 signals): Lowest confidence

**Signal Count by Group:**
- `technical_infrastructure`: 17 signals
- `public_record`: 12 signals
- `network_authority`: 5 signals
- `corporate_footprint`: 5 signals
- `behavioural`: 4 signals
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
| 1 | Safety Record | 1.30 | 0.50 | 0.60 | 0.20 |
| 2 | Operational Quality | 1.20 | 0.30 | 0.30 | 0.60 |
| 3 | Network Authority | 0.20 | 0.10 | 0.05 | 0.05 |
| 4 | Financial Stability | 0.18 | 0.05 | 0.03 | 0.10 |
| 5 | Corporate Governance | 0.12 | 0.05 | 0.02 | 0.05 |

**Primary Assessment Driver:** `Safety Record` with combined weight of 1.30
**Secondary Driver:** `Operational Quality` with combined weight of 1.20

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
| Safety Record | 0.60 | 0.65 | 0.20 |
| Operational Quality | 0.35 | 0.30 | 0.70 |
| Corporate Governance | 0.05 | 0.05 | 0.10 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

### Signal Architecture Rationale
This configuration contains **22 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `DIRECT_OBSERVABLE` (9 signals): Highest confidence
- `INFERRED_PROXY` (13 signals): Medium confidence

**Signal Count by Group:**
- `public_record`: 8 signals
- `technical_infrastructure`: 7 signals
- `corporate_footprint`: 3 signals
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
| 1 | Safety Record | 1.45 | 0.60 | 0.65 | 0.20 |
| 2 | Operational Quality | 1.35 | 0.35 | 0.30 | 0.70 |
| 3 | Corporate Governance | 0.20 | 0.05 | 0.05 | 0.10 |

**Primary Assessment Driver:** `Safety Record` with combined weight of 1.45
**Secondary Driver:** `Operational Quality` with combined weight of 1.35

### Theoretical Premium Calculation (Tier 3 Standard)
> *Per the DSI Premium Calculation Methodology v2.0, the core formula is:*
> *P_final = (Base × Rate) × ILF_relativity × Deductible_Factor × Modifiers*

**1. The Pricing Anchor:** The Flat Premium of `$7,500` purchases exactly the `$5,000,000` Limit / `$10,000` Deductible Base Package.
**2. Theoretical Execution:**
  - Technical Premium = **$7,500**
  - *Scaling relies entirely on selecting a different Limit ID from the Bundled limit_configuration packages.*

---

## Model: `aerospace_space`
*Space risk — launch vehicles, satellites, in-orbit operations*

### Routing Protocol (Multiplexer)
- `aviation_segment == SPACE`
- `hull_value >= 50000000`

### Three-Layer Weight Distribution
> *DSI requires that weights for Risk, Loss, and Exposure each sum to 1.0 across all signal groups.*

**Validation:** PASS

| Group | Risk | Loss | Exposure |
|-------|------|------|----------|
| Space Risk | 0.55 | 0.55 | 0.45 |
| Regulatory Framework | 0.15 | 0.10 | 0.15 |
| Corporate Footprint | 0.20 | 0.20 | 0.25 |
| Firm Stability | 0.10 | 0.15 | 0.15 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

### Signal Architecture Rationale
This configuration contains **5 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `DIRECT_OBSERVABLE` (2 signals): Highest confidence
- `INFERRED_PROXY` (3 signals): Medium confidence

**Signal Count by Group:**
- `technical_infrastructure`: 5 signals

**Selection Rationale:**
- 40% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 | Space Risk | 1.55 | 0.55 | 0.55 | 0.45 |
| 2 | Corporate Footprint | 0.65 | 0.20 | 0.20 | 0.25 |
| 3 | Regulatory Framework | 0.40 | 0.15 | 0.10 | 0.15 |
| 4 | Firm Stability | 0.40 | 0.10 | 0.15 | 0.15 |

**Primary Assessment Driver:** `Space Risk` with combined weight of 1.55
**Secondary Driver:** `Corporate Footprint` with combined weight of 0.65

### Theoretical Premium Calculation (Tier 3 Standard)
> *Per the DSI Premium Calculation Methodology v2.0, the core formula is:*
> *P_final = (Base × Rate) × ILF_relativity × Deductible_Factor × Modifiers*

**1. The Pricing Anchor:** The Base Rate of `8.5%` on `hull_value` purchases exactly a `$50,000,000` Limit with a `$5,000,000` Deductible.
**2. Theoretical Execution:**
  - Assume `hull_value` = $10,000,000
  - Base Premium = $10,000,000 × 0.085 = **$850,000**
  - If the client requests the Anchor Limit/Deductible, the factors are 1.00, resulting in a technical premium of **$850,000**.

---

## Model: `aerospace_rotary`
*Helicopter operations — mission-specific, EMS, offshore, utility, corporate*

### Routing Protocol (Multiplexer)
- `aviation_segment == ROTARY_WING`

### Three-Layer Weight Distribution
> *DSI requires that weights for Risk, Loss, and Exposure each sum to 1.0 across all signal groups.*

**Validation:** PASS

| Group | Risk | Loss | Exposure |
|-------|------|------|----------|
| Rotary Wing Risk | 0.45 | 0.45 | 0.40 |
| Iosa Status | 0.25 | 0.20 | 0.25 |
| Corporate Footprint | 0.15 | 0.20 | 0.20 |
| Firm Stability | 0.15 | 0.15 | 0.15 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

### Signal Architecture Rationale
This configuration contains **5 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `DIRECT_OBSERVABLE` (2 signals): Highest confidence
- `INFERRED_PROXY` (3 signals): Medium confidence

**Signal Count by Group:**
- `technical_infrastructure`: 5 signals

**Selection Rationale:**
- 40% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 | Rotary Wing Risk | 1.30 | 0.45 | 0.45 | 0.40 |
| 2 | Iosa Status | 0.70 | 0.25 | 0.20 | 0.25 |
| 3 | Corporate Footprint | 0.55 | 0.15 | 0.20 | 0.20 |
| 4 | Firm Stability | 0.45 | 0.15 | 0.15 | 0.15 |

**Primary Assessment Driver:** `Rotary Wing Risk` with combined weight of 1.30
**Secondary Driver:** `Iosa Status` with combined weight of 0.70

### Theoretical Premium Calculation (Tier 3 Standard)
> *Per the DSI Premium Calculation Methodology v2.0, the core formula is:*
> *P_final = (Base × Rate) × ILF_relativity × Deductible_Factor × Modifiers*

**1. The Pricing Anchor:** The Base Rate of `0.5499999999999999%` on `hull_value` purchases exactly a `$5,000,000` Limit with a `$100,000` Deductible.
**2. Theoretical Execution:**
  - Assume `hull_value` = $10,000,000
  - Base Premium = $10,000,000 × 0.0055 = **$55,000**
  - If the client requests the Anchor Limit/Deductible, the factors are 1.00, resulting in a technical premium of **$55,000**.

---

## Model: `aerospace_unmanned`
*UAS/drone operations — VLOS, BVLOS, autonomous, commercial drone fleets*

### Routing Protocol (Multiplexer)
- `aviation_segment == UNMANNED`

### Three-Layer Weight Distribution
> *DSI requires that weights for Risk, Loss, and Exposure each sum to 1.0 across all signal groups.*

**Validation:** PASS

| Group | Risk | Loss | Exposure |
|-------|------|------|----------|
| Unmanned Aircraft Systems | 0.50 | 0.55 | 0.50 |
| Regulatory Framework | 0.20 | 0.15 | 0.15 |
| Corporate Footprint | 0.15 | 0.15 | 0.20 |
| Firm Stability | 0.15 | 0.15 | 0.15 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

### Signal Architecture Rationale
This configuration contains **5 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `DIRECT_OBSERVABLE` (3 signals): Highest confidence
- `INFERRED_PROXY` (2 signals): Medium confidence

**Signal Count by Group:**
- `technical_infrastructure`: 5 signals

**Selection Rationale:**
- 60% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 | Unmanned Aircraft Systems | 1.55 | 0.50 | 0.55 | 0.50 |
| 2 | Regulatory Framework | 0.50 | 0.20 | 0.15 | 0.15 |
| 3 | Corporate Footprint | 0.50 | 0.15 | 0.15 | 0.20 |
| 4 | Firm Stability | 0.45 | 0.15 | 0.15 | 0.15 |

**Primary Assessment Driver:** `Unmanned Aircraft Systems` with combined weight of 1.55
**Secondary Driver:** `Regulatory Framework` with combined weight of 0.50

### Theoretical Premium Calculation (Tier 3 Standard)
> *Per the DSI Premium Calculation Methodology v2.0, the core formula is:*
> *P_final = (Base × Rate) × ILF_relativity × Deductible_Factor × Modifiers*

**1. The Pricing Anchor:** The Base Rate of `4.0%` on `hull_value` purchases exactly a `$1,000,000` Limit with a `$10,000` Deductible.
**2. Theoretical Execution:**
  - Assume `hull_value` = $10,000,000
  - Base Premium = $10,000,000 × 0.04 = **$400,000**
  - If the client requests the Anchor Limit/Deductible, the factors are 1.00, resulting in a technical premium of **$400,000**.

---

## Model: `aerospace_mro`
*MRO facility liability — workmanship, hangarkeepers, products/completed operations*

### Routing Protocol (Multiplexer)
- `aviation_segment == MRO`
- `revenue >= 5000000`

### Three-Layer Weight Distribution
> *DSI requires that weights for Risk, Loss, and Exposure each sum to 1.0 across all signal groups.*

**Validation:** PASS

| Group | Risk | Loss | Exposure |
|-------|------|------|----------|
| MRO Facility Risk | 0.50 | 0.55 | 0.45 |
| Regulatory Framework | 0.15 | 0.10 | 0.15 |
| Corporate Footprint | 0.20 | 0.20 | 0.25 |
| Firm Stability | 0.15 | 0.15 | 0.15 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

### Signal Architecture Rationale
This configuration contains **5 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `DIRECT_OBSERVABLE` (3 signals): Highest confidence
- `INFERRED_PROXY` (2 signals): Medium confidence

**Signal Count by Group:**
- `technical_infrastructure`: 5 signals

**Selection Rationale:**
- 60% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 | MRO Facility Risk | 1.50 | 0.50 | 0.55 | 0.45 |
| 2 | Corporate Footprint | 0.65 | 0.20 | 0.20 | 0.25 |
| 3 | Firm Stability | 0.45 | 0.15 | 0.15 | 0.15 |
| 4 | Regulatory Framework | 0.40 | 0.15 | 0.10 | 0.15 |

**Primary Assessment Driver:** `MRO Facility Risk` with combined weight of 1.50
**Secondary Driver:** `Corporate Footprint` with combined weight of 0.65

### Theoretical Premium Calculation (Tier 3 Standard)
> *Per the DSI Premium Calculation Methodology v2.0, the core formula is:*
> *P_final = (Base × Rate) × ILF_relativity × Deductible_Factor × Modifiers*

**1. The Pricing Anchor:** The Base Rate of `0.5499999999999999%` on `revenue` purchases exactly a `$5,000,000` Limit with a `$100,000` Deductible.
**2. Theoretical Execution:**
  - Assume `revenue` = $10,000,000
  - Base Premium = $10,000,000 × 0.0055 = **$55,000**
  - If the client requests the Anchor Limit/Deductible, the factors are 1.00, resulting in a technical premium of **$55,000**.

---

## Model: `aerospace_high_value`
*High-value aviation fleet — airlines, major operators, hull value >$500M*

### Routing Protocol (Multiplexer)
- `hull_value >= 500000000`

### Three-Layer Weight Distribution
> *DSI requires that weights for Risk, Loss, and Exposure each sum to 1.0 across all signal groups.*

**Validation:** PASS

| Group | Risk | Loss | Exposure |
|-------|------|------|----------|
| Iosa Status | 0.40 | 0.30 | 0.25 |
| Fleet Size | 0.25 | 0.30 | 0.35 |
| Corporate Footprint | 0.25 | 0.25 | 0.25 |
| Firm Stability | 0.10 | 0.15 | 0.15 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

### Signal Architecture Rationale
This configuration contains **0 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**

**Signal Count by Group:**

**Selection Rationale:**
- 0% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 | Iosa Status | 0.95 | 0.40 | 0.30 | 0.25 |
| 2 | Fleet Size | 0.90 | 0.25 | 0.30 | 0.35 |
| 3 | Corporate Footprint | 0.75 | 0.25 | 0.25 | 0.25 |
| 4 | Firm Stability | 0.40 | 0.10 | 0.15 | 0.15 |

**Primary Assessment Driver:** `Iosa Status` with combined weight of 0.95
**Secondary Driver:** `Fleet Size` with combined weight of 0.90

### Theoretical Premium Calculation (Tier 3 Standard)
> *Per the DSI Premium Calculation Methodology v2.0, the core formula is:*
> *P_final = (Base × Rate) × ILF_relativity × Deductible_Factor × Modifiers*

**1. The Pricing Anchor:** The Base Rate of `0.16%` on `hull_value` purchases exactly a `$100,000,000` Limit with a `$2,500,000` Deductible.
**2. Theoretical Execution:**
  - Assume `hull_value` = $10,000,000
  - Base Premium = $10,000,000 × 0.0016 = **$16,000**
  - If the client requests the Anchor Limit/Deductible, the factors are 1.00, resulting in a technical premium of **$16,000**.


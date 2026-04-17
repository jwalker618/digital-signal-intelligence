# DSI Logic Document: `MARINE`
*Generated: 2026-04-17*

## DSI Foundational Principles Adherence
This configuration is validated against the DSI Whitepaper & Vision Paper:
- **Objective Observation:** Signals derived from verifiable digital footprints, avoiding subjective interpretation.
- **Three-Layer Engine:** Modifiers explicitly target Risk, Loss, and Exposure dimensions.
- **Phase 5 Anchoring:** Polymorphic pricing limits scale from mathematically absolute anchor points.

---

## Model: `marine_general`
*Marine hull and liability coverage based on observable operator behavior, safety records, and fleet patterns*

### Routing Protocol (Multiplexer)
- `hull_value > 50000000`

### Three-Layer Weight Distribution
> *DSI requires that weights for Risk, Loss, and Exposure each sum to 1.0 across all signal groups.*

**Validation:** PASS

| Group | Risk | Loss | Exposure |
|-------|------|------|----------|
| Network Authority | 0.15 | 0.10 | 0.05 |
| Operational Telemetry | 0.30 | 0.30 | 0.50 |
| Safety Compliance | 0.45 | 0.50 | 0.30 |
| Corporate Footprint | 0.05 | 0.05 | 0.10 |
| Structured Data | 0.05 | 0.05 | 0.05 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

### Signal Architecture Rationale
This configuration contains **50 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `DIRECT_OBSERVABLE` (32 signals): Highest confidence
- `INFERRED_PROXY` (18 signals): Medium confidence

**Signal Count by Group:**
- `public_record`: 15 signals
- `technical_infrastructure`: 11 signals
- `network_authority`: 10 signals
- `corporate_footprint`: 6 signals
- `structured_data`: 3 signals
- `operator_type`: 1 signals
- `vessel_category`: 1 signals
- `trading_pattern`: 1 signals
- `flag_state_quality`: 1 signals
- `fleet_age_band`: 1 signals

**Selection Rationale:**
- 64% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 | Safety Compliance | 1.25 | 0.45 | 0.50 | 0.30 |
| 2 | Operational Telemetry | 1.10 | 0.30 | 0.30 | 0.50 |
| 3 | Network Authority | 0.30 | 0.15 | 0.10 | 0.05 |
| 4 | Corporate Footprint | 0.20 | 0.05 | 0.05 | 0.10 |
| 5 | Structured Data | 0.15 | 0.05 | 0.05 | 0.05 |

**Primary Assessment Driver:** `Safety Compliance` with combined weight of 1.25
**Secondary Driver:** `Operational Telemetry` with combined weight of 1.10

### Theoretical Premium Calculation (Tier 3 Standard)
> *Per the DSI Premium Calculation Methodology v2.0, the core formula is:*
> *P_final = (Base × Rate) × ILF_relativity × Deductible_Factor × Modifiers*

**1. The Pricing Anchor:** The Base Rate of `0.32%` on `tiv` purchases exactly a `$10,000,000` Limit with a `$50,000` Deductible.
**2. Theoretical Execution:**
  - Assume `tiv` = $10,000,000
  - Base Premium = $10,000,000 × 0.0032 = **$32,000**
  - If the client requests the Anchor Limit/Deductible, the factors are 1.00, resulting in a technical premium of **$32,000**.

---

## Model: `marine_sme`
*Marine coverage for regional fleets, brown-water, and light commercial*

### Routing Protocol (Multiplexer)
- `hull_value <= 50000000`

### Three-Layer Weight Distribution
> *DSI requires that weights for Risk, Loss, and Exposure each sum to 1.0 across all signal groups.*

**Validation:** PASS

| Group | Risk | Loss | Exposure |
|-------|------|------|----------|
| Safety Compliance | 0.30 | 0.35 | 0.20 |
| Operational Telemetry | 0.45 | 0.40 | 0.50 |
| Network Authority | 0.25 | 0.25 | 0.30 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

### Signal Architecture Rationale
This configuration contains **15 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `DIRECT_OBSERVABLE` (10 signals): Highest confidence
- `INFERRED_PROXY` (5 signals): Medium confidence

**Signal Count by Group:**
- `technical_infrastructure`: 6 signals
- `public_record`: 4 signals
- `network_authority`: 3 signals
- `vessel_category`: 1 signals
- `fleet_age_band`: 1 signals

**Selection Rationale:**
- 67% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 | Operational Telemetry | 1.35 | 0.45 | 0.40 | 0.50 |
| 2 | Safety Compliance | 0.85 | 0.30 | 0.35 | 0.20 |
| 3 | Network Authority | 0.80 | 0.25 | 0.25 | 0.30 |

**Primary Assessment Driver:** `Operational Telemetry` with combined weight of 1.35
**Secondary Driver:** `Safety Compliance` with combined weight of 0.85

### Theoretical Premium Calculation (Tier 3 Standard)
> *Per the DSI Premium Calculation Methodology v2.0, the core formula is:*
> *P_final = (Base × Rate) × ILF_relativity × Deductible_Factor × Modifiers*

**1. The Pricing Anchor:** The Base Rate of `0.8%` on `hull_value` purchases exactly a `$5,000,000` Limit with a `$10,000` Deductible.
**2. Theoretical Execution:**
  - Assume `hull_value` = $10,000,000
  - Base Premium = $10,000,000 × 0.008 = **$80,000**
  - If the client requests the Anchor Limit/Deductible, the factors are 1.00, resulting in a technical premium of **$80,000**.

---

## Model: `marine_cargo`
*Marine cargo insurance — commodity-specific, transit risk, storage exposure*

### Routing Protocol (Multiplexer)
- `product_type == cargo`
- `tiv >= 5000000`

### Three-Layer Weight Distribution
> *DSI requires that weights for Risk, Loss, and Exposure each sum to 1.0 across all signal groups.*

**Validation:** PASS

| Group | Risk | Loss | Exposure |
|-------|------|------|----------|
| Cargo Quality | 0.45 | 0.45 | 0.40 |
| Port State & Regulatory Compliance | 0.25 | 0.25 | 0.20 |
| Trading Pattern | 0.20 | 0.20 | 0.30 |
| Corporate Footprint | 0.10 | 0.10 | 0.10 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

### Signal Architecture Rationale
This configuration contains **11 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `DIRECT_OBSERVABLE` (6 signals): Highest confidence
- `INFERRED_PROXY` (5 signals): Medium confidence

**Signal Count by Group:**
- `technical_infrastructure`: 6 signals
- `public_record`: 5 signals

**Selection Rationale:**
- 55% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 | Cargo Quality | 1.30 | 0.45 | 0.45 | 0.40 |
| 2 | Port State & Regulatory Compliance | 0.70 | 0.25 | 0.25 | 0.20 |
| 3 | Trading Pattern | 0.70 | 0.20 | 0.20 | 0.30 |
| 4 | Corporate Footprint | 0.30 | 0.10 | 0.10 | 0.10 |

**Primary Assessment Driver:** `Cargo Quality` with combined weight of 1.30
**Secondary Driver:** `Port State & Regulatory Compliance` with combined weight of 0.70

### Theoretical Premium Calculation (Tier 3 Standard)
> *Per the DSI Premium Calculation Methodology v2.0, the core formula is:*
> *P_final = (Base × Rate) × ILF_relativity × Deductible_Factor × Modifiers*

**1. The Pricing Anchor:** The Base Rate of `0.3%` on `tiv` purchases exactly a `$5,000,000` Limit with a `$50,000` Deductible.
**2. Theoretical Execution:**
  - Assume `tiv` = $10,000,000
  - Base Premium = $10,000,000 × 0.003 = **$30,000**
  - If the client requests the Anchor Limit/Deductible, the factors are 1.00, resulting in a technical premium of **$30,000**.

---

## Model: `marine_tanker`
*Tanker fleet hull & liability — crude, product, chemical, gas carriers*

### Routing Protocol (Multiplexer)
- `operation_segment == TANKER`
- `hull_value >= 50000000`

### Three-Layer Weight Distribution
> *DSI requires that weights for Risk, Loss, and Exposure each sum to 1.0 across all signal groups.*

**Validation:** PASS

| Group | Risk | Loss | Exposure |
|-------|------|------|----------|
| Tanker Risk | 0.45 | 0.45 | 0.40 |
| Port State & Regulatory Compliance | 0.30 | 0.25 | 0.25 |
| Trading Pattern | 0.15 | 0.20 | 0.25 |
| Corporate Footprint | 0.10 | 0.10 | 0.10 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

### Signal Architecture Rationale
This configuration contains **10 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `DIRECT_OBSERVABLE` (6 signals): Highest confidence
- `INFERRED_PROXY` (4 signals): Medium confidence

**Signal Count by Group:**
- `technical_infrastructure`: 5 signals
- `public_record`: 5 signals

**Selection Rationale:**
- 60% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 | Tanker Risk | 1.30 | 0.45 | 0.45 | 0.40 |
| 2 | Port State & Regulatory Compliance | 0.80 | 0.30 | 0.25 | 0.25 |
| 3 | Trading Pattern | 0.60 | 0.15 | 0.20 | 0.25 |
| 4 | Corporate Footprint | 0.30 | 0.10 | 0.10 | 0.10 |

**Primary Assessment Driver:** `Tanker Risk` with combined weight of 1.30
**Secondary Driver:** `Port State & Regulatory Compliance` with combined weight of 0.80

### Theoretical Premium Calculation (Tier 3 Standard)
> *Per the DSI Premium Calculation Methodology v2.0, the core formula is:*
> *P_final = (Base × Rate) × ILF_relativity × Deductible_Factor × Modifiers*

**1. The Pricing Anchor:** The Base Rate of `0.42%` on `hull_value` purchases exactly a `$10,000,000` Limit with a `$250,000` Deductible.
**2. Theoretical Execution:**
  - Assume `hull_value` = $10,000,000
  - Base Premium = $10,000,000 × 0.0042 = **$42,000**
  - If the client requests the Anchor Limit/Deductible, the factors are 1.00, resulting in a technical premium of **$42,000**.

---

## Model: `marine_offshore`
*Offshore marine units — FPSOs, rigs, OSVs, construction vessels, wind installation*

### Routing Protocol (Multiplexer)
- `operation_segment == OFFSHORE`
- `hull_value >= 50000000`

### Three-Layer Weight Distribution
> *DSI requires that weights for Risk, Loss, and Exposure each sum to 1.0 across all signal groups.*

**Validation:** PASS

| Group | Risk | Loss | Exposure |
|-------|------|------|----------|
| Offshore Marine | 0.50 | 0.45 | 0.45 |
| Port State & Regulatory Compliance | 0.25 | 0.25 | 0.20 |
| Trading Pattern | 0.10 | 0.15 | 0.20 |
| Corporate Footprint | 0.15 | 0.15 | 0.15 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

### Signal Architecture Rationale
This configuration contains **10 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `DIRECT_OBSERVABLE` (8 signals): Highest confidence
- `INFERRED_PROXY` (2 signals): Medium confidence

**Signal Count by Group:**
- `technical_infrastructure`: 5 signals
- `public_record`: 5 signals

**Selection Rationale:**
- 80% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 | Offshore Marine | 1.40 | 0.50 | 0.45 | 0.45 |
| 2 | Port State & Regulatory Compliance | 0.70 | 0.25 | 0.25 | 0.20 |
| 3 | Trading Pattern | 0.45 | 0.10 | 0.15 | 0.20 |
| 4 | Corporate Footprint | 0.45 | 0.15 | 0.15 | 0.15 |

**Primary Assessment Driver:** `Offshore Marine` with combined weight of 1.40
**Secondary Driver:** `Port State & Regulatory Compliance` with combined weight of 0.70

### Theoretical Premium Calculation (Tier 3 Standard)
> *Per the DSI Premium Calculation Methodology v2.0, the core formula is:*
> *P_final = (Base × Rate) × ILF_relativity × Deductible_Factor × Modifiers*

**1. The Pricing Anchor:** The Base Rate of `0.5499999999999999%` on `hull_value` purchases exactly a `$25,000,000` Limit with a `$500,000` Deductible.
**2. Theoretical Execution:**
  - Assume `hull_value` = $10,000,000
  - Base Premium = $10,000,000 × 0.0055 = **$55,000**
  - If the client requests the Anchor Limit/Deductible, the factors are 1.00, resulting in a technical premium of **$55,000**.

---

## Model: `marine_war_risk`
*Marine war risk — hull war, strikes, piracy, confiscation, terrorism*

### Routing Protocol (Multiplexer)
- `product_type == war_risks`

### Three-Layer Weight Distribution
> *DSI requires that weights for Risk, Loss, and Exposure each sum to 1.0 across all signal groups.*

**Validation:** PASS

| Group | Risk | Loss | Exposure |
|-------|------|------|----------|
| Trading Pattern | 0.45 | 0.45 | 0.45 |
| Port State & Regulatory Compliance | 0.35 | 0.30 | 0.25 |
| Fleet Age Band | 0.10 | 0.10 | 0.15 |
| Corporate Footprint | 0.10 | 0.15 | 0.15 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

### Signal Architecture Rationale
This configuration contains **5 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `DIRECT_OBSERVABLE` (4 signals): Highest confidence
- `INFERRED_PROXY` (1 signals): Medium confidence

**Signal Count by Group:**
- `public_record`: 5 signals

**Selection Rationale:**
- 80% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 | Trading Pattern | 1.35 | 0.45 | 0.45 | 0.45 |
| 2 | Port State & Regulatory Compliance | 0.90 | 0.35 | 0.30 | 0.25 |
| 3 | Corporate Footprint | 0.40 | 0.10 | 0.15 | 0.15 |
| 4 | Fleet Age Band | 0.35 | 0.10 | 0.10 | 0.15 |

**Primary Assessment Driver:** `Trading Pattern` with combined weight of 1.35
**Secondary Driver:** `Port State & Regulatory Compliance` with combined weight of 0.90

### Theoretical Premium Calculation (Tier 3 Standard)
> *Per the DSI Premium Calculation Methodology v2.0, the core formula is:*
> *P_final = (Base × Rate) × ILF_relativity × Deductible_Factor × Modifiers*

**1. The Pricing Anchor:** The Base Rate of `0.25%` on `hull_value` purchases exactly a `$5,000,000` Limit with a `$100,000` Deductible.
**2. Theoretical Execution:**
  - Assume `hull_value` = $10,000,000
  - Base Premium = $10,000,000 × 0.0025 = **$25,000**
  - If the client requests the Anchor Limit/Deductible, the factors are 1.00, resulting in a technical premium of **$25,000**.

---

## Model: `marine_high_value`
*High-value fleet hull & liability — modern tonnage, top-tier operators, fleet value >$1B*

### Routing Protocol (Multiplexer)
- `hull_value >= 250000000`

### Three-Layer Weight Distribution
> *DSI requires that weights for Risk, Loss, and Exposure each sum to 1.0 across all signal groups.*

**Validation:** PASS

| Group | Risk | Loss | Exposure |
|-------|------|------|----------|
| Port State & Regulatory Compliance | 0.40 | 0.35 | 0.25 |
| Fleet Age Band | 0.20 | 0.20 | 0.20 |
| Trading Pattern | 0.20 | 0.25 | 0.30 |
| Corporate Footprint | 0.20 | 0.20 | 0.25 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

### Signal Architecture Rationale
This configuration contains **5 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `DIRECT_OBSERVABLE` (4 signals): Highest confidence
- `INFERRED_PROXY` (1 signals): Medium confidence

**Signal Count by Group:**
- `public_record`: 5 signals

**Selection Rationale:**
- 80% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 | Port State & Regulatory Compliance | 1.00 | 0.40 | 0.35 | 0.25 |
| 2 | Trading Pattern | 0.75 | 0.20 | 0.25 | 0.30 |
| 3 | Corporate Footprint | 0.65 | 0.20 | 0.20 | 0.25 |
| 4 | Fleet Age Band | 0.60 | 0.20 | 0.20 | 0.20 |

**Primary Assessment Driver:** `Port State & Regulatory Compliance` with combined weight of 1.00
**Secondary Driver:** `Trading Pattern` with combined weight of 0.75

### Theoretical Premium Calculation (Tier 3 Standard)
> *Per the DSI Premium Calculation Methodology v2.0, the core formula is:*
> *P_final = (Base × Rate) × ILF_relativity × Deductible_Factor × Modifiers*

**1. The Pricing Anchor:** The Base Rate of `0.27999999999999997%` on `hull_value` purchases exactly a `$50,000,000` Limit with a `$1,000,000` Deductible.
**2. Theoretical Execution:**
  - Assume `hull_value` = $10,000,000
  - Base Premium = $10,000,000 × 0.0028 = **$28,000**
  - If the client requests the Anchor Limit/Deductible, the factors are 1.00, resulting in a technical premium of **$28,000**.


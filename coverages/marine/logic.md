# DSI Logic Document: `MARINE`
*Generated: 2026-03-31*

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
| Operational Telemetry | 0.20 | 0.15 | 0.15 |
| Safety Compliance | 0.25 | 0.35 | 0.10 |
| Fleet Profile | 0.10 | 0.15 | 0.35 |
| Sanctions Compliance | 0.15 | 0.10 | 0.10 |
| Environmental Compliance | 0.05 | 0.05 | 0.10 |
| Corporate Footprint | 0.05 | 0.05 | 0.10 |
| Structured Data | 0.05 | 0.05 | 0.05 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

### Signal Architecture Rationale
This configuration contains **50 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `DIRECT_OBSERVABLE` (32 signals): Highest confidence
- `INFERRED_PROXY` (18 signals): Medium confidence

**Signal Count by Group:**
- `network_authority`: 10 signals
- `operational_telemetry`: 6 signals
- `safety_compliance`: 6 signals
- `corporate_footprint`: 6 signals
- `fleet_profile`: 5 signals
- `sanctions_compliance`: 5 signals
- `environmental`: 4 signals
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
| 1 | Safety Compliance | 0.70 | 0.25 | 0.35 | 0.10 |
| 2 | Fleet Profile | 0.60 | 0.10 | 0.15 | 0.35 |
| 3 | Operational Telemetry | 0.50 | 0.20 | 0.15 | 0.15 |
| 4 | Sanctions Compliance | 0.35 | 0.15 | 0.10 | 0.10 |
| 5 | Network Authority | 0.30 | 0.15 | 0.10 | 0.05 |
| 6 | Environmental Compliance | 0.20 | 0.05 | 0.05 | 0.10 |
| 7 | Corporate Footprint | 0.20 | 0.05 | 0.05 | 0.10 |
| 8 | Structured Data | 0.15 | 0.05 | 0.05 | 0.05 |

**Primary Assessment Driver:** `Safety Compliance` with combined weight of 0.70
**Secondary Driver:** `Fleet Profile` with combined weight of 0.60

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
| Operational Telemetry | 0.25 | 0.25 | 0.25 |
| Network Authority | 0.25 | 0.25 | 0.30 |
| Fleet Profile | 0.20 | 0.15 | 0.25 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

### Signal Architecture Rationale
This configuration contains **15 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `DIRECT_OBSERVABLE` (10 signals): Highest confidence
- `INFERRED_PROXY` (5 signals): Medium confidence

**Signal Count by Group:**
- `safety_compliance`: 4 signals
- `operational_telemetry`: 3 signals
- `network_authority`: 3 signals
- `fleet_profile`: 3 signals
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
| 1 | Safety Compliance | 0.85 | 0.30 | 0.35 | 0.20 |
| 2 | Network Authority | 0.80 | 0.25 | 0.25 | 0.30 |
| 3 | Operational Telemetry | 0.75 | 0.25 | 0.25 | 0.25 |
| 4 | Fleet Profile | 0.60 | 0.20 | 0.15 | 0.25 |

**Primary Assessment Driver:** `Safety Compliance` with combined weight of 0.85
**Secondary Driver:** `Network Authority` with combined weight of 0.80

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
| Cargo Quality | 0.35 | 0.35 | 0.30 |
| Port State & Regulatory Compliance | 0.15 | 0.15 | 0.10 |
| Trading Pattern | 0.15 | 0.15 | 0.20 |
| Fleet Age Band | 0.10 | 0.10 | 0.10 |
| Flag State Quality | 0.10 | 0.10 | 0.10 |
| Corporate Footprint | 0.10 | 0.10 | 0.10 |
| Firm Stability | 0.05 | 0.05 | 0.10 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

### Signal Architecture Rationale
This configuration contains **11 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `DIRECT_OBSERVABLE` (6 signals): Highest confidence
- `INFERRED_PROXY` (5 signals): Medium confidence

**Signal Count by Group:**
- `cargo_quality`: 6 signals
- `port_state_compliance`: 5 signals

**Selection Rationale:**
- 55% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 | Cargo Quality | 1.00 | 0.35 | 0.35 | 0.30 |
| 2 | Trading Pattern | 0.50 | 0.15 | 0.15 | 0.20 |
| 3 | Port State & Regulatory Compliance | 0.40 | 0.15 | 0.15 | 0.10 |
| 4 | Fleet Age Band | 0.30 | 0.10 | 0.10 | 0.10 |
| 5 | Flag State Quality | 0.30 | 0.10 | 0.10 | 0.10 |
| 6 | Corporate Footprint | 0.30 | 0.10 | 0.10 | 0.10 |
| 7 | Firm Stability | 0.20 | 0.05 | 0.05 | 0.10 |

**Primary Assessment Driver:** `Cargo Quality` with combined weight of 1.00
**Secondary Driver:** `Trading Pattern` with combined weight of 0.50

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
| Tanker Risk | 0.30 | 0.30 | 0.25 |
| Port State & Regulatory Compliance | 0.20 | 0.15 | 0.15 |
| Fleet Age Band | 0.15 | 0.15 | 0.15 |
| Flag State Quality | 0.10 | 0.10 | 0.10 |
| Trading Pattern | 0.10 | 0.15 | 0.15 |
| Corporate Footprint | 0.10 | 0.10 | 0.10 |
| Firm Stability | 0.05 | 0.05 | 0.10 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

### Signal Architecture Rationale
This configuration contains **10 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `DIRECT_OBSERVABLE` (6 signals): Highest confidence
- `INFERRED_PROXY` (4 signals): Medium confidence

**Signal Count by Group:**
- `tanker_risk`: 5 signals
- `port_state_compliance`: 5 signals

**Selection Rationale:**
- 60% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 | Tanker Risk | 0.85 | 0.30 | 0.30 | 0.25 |
| 2 | Port State & Regulatory Compliance | 0.50 | 0.20 | 0.15 | 0.15 |
| 3 | Fleet Age Band | 0.45 | 0.15 | 0.15 | 0.15 |
| 4 | Trading Pattern | 0.40 | 0.10 | 0.15 | 0.15 |
| 5 | Flag State Quality | 0.30 | 0.10 | 0.10 | 0.10 |
| 6 | Corporate Footprint | 0.30 | 0.10 | 0.10 | 0.10 |
| 7 | Firm Stability | 0.20 | 0.05 | 0.05 | 0.10 |

**Primary Assessment Driver:** `Tanker Risk` with combined weight of 0.85
**Secondary Driver:** `Port State & Regulatory Compliance` with combined weight of 0.50

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
| Offshore Marine | 0.35 | 0.30 | 0.30 |
| Port State & Regulatory Compliance | 0.15 | 0.15 | 0.10 |
| Fleet Age Band | 0.15 | 0.15 | 0.15 |
| Flag State Quality | 0.10 | 0.10 | 0.10 |
| Trading Pattern | 0.05 | 0.10 | 0.10 |
| Corporate Footprint | 0.15 | 0.15 | 0.15 |
| Firm Stability | 0.05 | 0.05 | 0.10 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

### Signal Architecture Rationale
This configuration contains **10 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `DIRECT_OBSERVABLE` (8 signals): Highest confidence
- `INFERRED_PROXY` (2 signals): Medium confidence

**Signal Count by Group:**
- `offshore_marine`: 5 signals
- `port_state_compliance`: 5 signals

**Selection Rationale:**
- 80% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 | Offshore Marine | 0.95 | 0.35 | 0.30 | 0.30 |
| 2 | Fleet Age Band | 0.45 | 0.15 | 0.15 | 0.15 |
| 3 | Corporate Footprint | 0.45 | 0.15 | 0.15 | 0.15 |
| 4 | Port State & Regulatory Compliance | 0.40 | 0.15 | 0.15 | 0.10 |
| 5 | Flag State Quality | 0.30 | 0.10 | 0.10 | 0.10 |
| 6 | Trading Pattern | 0.25 | 0.05 | 0.10 | 0.10 |
| 7 | Firm Stability | 0.20 | 0.05 | 0.05 | 0.10 |

**Primary Assessment Driver:** `Offshore Marine` with combined weight of 0.95
**Secondary Driver:** `Fleet Age Band` with combined weight of 0.45

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
| Trading Pattern | 0.35 | 0.30 | 0.30 |
| Port State & Regulatory Compliance | 0.15 | 0.15 | 0.10 |
| Flag State Quality | 0.20 | 0.15 | 0.15 |
| Fleet Age Band | 0.10 | 0.10 | 0.15 |
| Corporate Footprint | 0.10 | 0.15 | 0.15 |
| Firm Stability | 0.10 | 0.15 | 0.15 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

### Signal Architecture Rationale
This configuration contains **5 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `DIRECT_OBSERVABLE` (4 signals): Highest confidence
- `INFERRED_PROXY` (1 signals): Medium confidence

**Signal Count by Group:**
- `port_state_compliance`: 5 signals

**Selection Rationale:**
- 80% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 | Trading Pattern | 0.95 | 0.35 | 0.30 | 0.30 |
| 2 | Flag State Quality | 0.50 | 0.20 | 0.15 | 0.15 |
| 3 | Port State & Regulatory Compliance | 0.40 | 0.15 | 0.15 | 0.10 |
| 4 | Corporate Footprint | 0.40 | 0.10 | 0.15 | 0.15 |
| 5 | Firm Stability | 0.40 | 0.10 | 0.15 | 0.15 |
| 6 | Fleet Age Band | 0.35 | 0.10 | 0.10 | 0.15 |

**Primary Assessment Driver:** `Trading Pattern` with combined weight of 0.95
**Secondary Driver:** `Flag State Quality` with combined weight of 0.50

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
| Port State & Regulatory Compliance | 0.25 | 0.20 | 0.15 |
| Fleet Age Band | 0.20 | 0.20 | 0.20 |
| Flag State Quality | 0.15 | 0.15 | 0.10 |
| Trading Pattern | 0.10 | 0.15 | 0.15 |
| Corporate Footprint | 0.20 | 0.20 | 0.25 |
| Firm Stability | 0.10 | 0.10 | 0.15 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

### Signal Architecture Rationale
This configuration contains **5 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `DIRECT_OBSERVABLE` (4 signals): Highest confidence
- `INFERRED_PROXY` (1 signals): Medium confidence

**Signal Count by Group:**
- `port_state_compliance`: 5 signals

**Selection Rationale:**
- 80% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 | Corporate Footprint | 0.65 | 0.20 | 0.20 | 0.25 |
| 2 | Port State & Regulatory Compliance | 0.60 | 0.25 | 0.20 | 0.15 |
| 3 | Fleet Age Band | 0.60 | 0.20 | 0.20 | 0.20 |
| 4 | Flag State Quality | 0.40 | 0.15 | 0.15 | 0.10 |
| 5 | Trading Pattern | 0.40 | 0.10 | 0.15 | 0.15 |
| 6 | Firm Stability | 0.35 | 0.10 | 0.10 | 0.15 |

**Primary Assessment Driver:** `Corporate Footprint` with combined weight of 0.65
**Secondary Driver:** `Port State & Regulatory Compliance` with combined weight of 0.60

### Theoretical Premium Calculation (Tier 3 Standard)
> *Per the DSI Premium Calculation Methodology v2.0, the core formula is:*
> *P_final = (Base × Rate) × ILF_relativity × Deductible_Factor × Modifiers*

**1. The Pricing Anchor:** The Base Rate of `0.27999999999999997%` on `hull_value` purchases exactly a `$50,000,000` Limit with a `$1,000,000` Deductible.
**2. Theoretical Execution:**
  - Assume `hull_value` = $10,000,000
  - Base Premium = $10,000,000 × 0.0028 = **$28,000**
  - If the client requests the Anchor Limit/Deductible, the factors are 1.00, resulting in a technical premium of **$28,000**.


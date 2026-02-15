# DSI Logic Document: `MARINE`
*Generated: 2026-02-15*

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
| Safety Compliance | 0.60 | 0.70 | 0.50 |
| Operational Telemetry | 0.40 | 0.30 | 0.50 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

### Signal Architecture Rationale
This configuration contains **5 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `DIRECT_OBSERVABLE` (3 signals): Highest confidence
- `INFERRED_PROXY` (2 signals): Medium confidence

**Signal Count by Group:**
- `safety_compliance`: 2 signals
- `vessel_category`: 1 signals
- `fleet_age_band`: 1 signals
- `operational_telemetry`: 1 signals

**Selection Rationale:**
- 60% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 | Safety Compliance | 1.80 | 0.60 | 0.70 | 0.50 |
| 2 | Operational Telemetry | 1.20 | 0.40 | 0.30 | 0.50 |

**Primary Assessment Driver:** `Safety Compliance` with combined weight of 1.80
**Secondary Driver:** `Operational Telemetry` with combined weight of 1.20

### Theoretical Premium Calculation (Tier 3 Standard)
> *Per the DSI Premium Calculation Methodology v2.0, the core formula is:*
> *P_final = (Base × Rate) × ILF_relativity × Deductible_Factor × Modifiers*

**1. The Pricing Anchor:** The Base Rate of `0.8%` on `hull_value` purchases exactly a `$5,000,000` Limit with a `$10,000` Deductible.
**2. Theoretical Execution:**
  - Assume `hull_value` = $10,000,000
  - Base Premium = $10,000,000 × 0.008 = **$80,000**
  - If the client requests the Anchor Limit/Deductible, the factors are 1.00, resulting in a technical premium of **$80,000**.


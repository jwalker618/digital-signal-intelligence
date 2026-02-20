# DSI Logic Document: `ENERGY`
*Generated: 2026-02-15*

## DSI Foundational Principles Adherence
This configuration is validated against the DSI Whitepaper & Vision Paper:
- **Objective Observation:** Signals derived from verifiable digital footprints, avoiding subjective interpretation.
- **Three-Layer Engine:** Modifiers explicitly target Risk, Loss, and Exposure dimensions.
- **Phase 5 Anchoring:** Polymorphic pricing limits scale from mathematically absolute anchor points.

---

## Model: `energy_general`
*Energy property and liability coverage based on observable safety, environmental, and operational signals*

### Routing Protocol (Multiplexer)
- `tiv > 50000000`

### Three-Layer Weight Distribution
> *DSI requires that weights for Risk, Loss, and Exposure each sum to 1.0 across all signal groups.*

**Validation:** PASS

| Group | Risk | Loss | Exposure |
|-------|------|------|----------|
| Network Authority | 0.10 | 0.05 | 0.05 |
| Safety Performance | 0.30 | 0.35 | 0.10 |
| Environmental Compliance | 0.20 | 0.25 | 0.10 |
| Operational Telemetry | 0.10 | 0.10 | 0.20 |
| Financial Stability | 0.10 | 0.05 | 0.20 |
| Asset Portfolio | 0.10 | 0.15 | 0.30 |
| Corporate Footprint | 0.05 | 0.03 | 0.03 |
| Structured Data | 0.05 | 0.02 | 0.02 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

### Signal Architecture Rationale
This configuration contains **47 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `DIRECT_OBSERVABLE` (21 signals): Highest confidence
- `INFERRED_PROXY` (25 signals): Medium confidence
- `COHORT_INFERENCE` (1 signals): Lowest confidence

**Signal Count by Group:**
- `network_authority`: 7 signals
- `safety_performance`: 7 signals
- `environmental_compliance`: 6 signals
- `corporate_footprint`: 6 signals
- `operational_telemetry`: 5 signals
- `financial_stability`: 5 signals
- `asset_portfolio`: 5 signals
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
| 1 | Safety Performance | 0.75 | 0.30 | 0.35 | 0.10 |
| 2 | Environmental Compliance | 0.55 | 0.20 | 0.25 | 0.10 |
| 3 | Asset Portfolio | 0.55 | 0.10 | 0.15 | 0.30 |
| 4 | Operational Telemetry | 0.40 | 0.10 | 0.10 | 0.20 |
| 5 | Financial Stability | 0.35 | 0.10 | 0.05 | 0.20 |
| 6 | Network Authority | 0.20 | 0.10 | 0.05 | 0.05 |
| 7 | Corporate Footprint | 0.11 | 0.05 | 0.03 | 0.03 |
| 8 | Structured Data | 0.09 | 0.05 | 0.02 | 0.02 |

**Primary Assessment Driver:** `Safety Performance` with combined weight of 0.75
**Secondary Driver:** `Environmental Compliance` with combined weight of 0.55

### Theoretical Premium Calculation (Tier 3 Standard)
> *Per the DSI Premium Calculation Methodology v2.0, the core formula is:*
> *P_final = (Base × Rate) × ILF_relativity × Deductible_Factor × Modifiers*

**1. The Pricing Anchor:** The Base Rate of `0.18%` on `tiv` purchases exactly a `$10,000,000` Limit with a `$50,000` Deductible.
**2. Theoretical Execution:**
  - Assume `tiv` = $10,000,000
  - Base Premium = $10,000,000 × 0.0018 = **$18,000**
  - If the client requests the Anchor Limit/Deductible, the factors are 1.00, resulting in a technical premium of **$18,000**.


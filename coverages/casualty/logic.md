# DSI Logic Document: `CASUALTY`
*Generated: 2026-03-31*

## DSI Foundational Principles Adherence
This configuration is validated against the DSI Whitepaper & Vision Paper:
- **Objective Observation:** Signals derived from verifiable digital footprints, avoiding subjective interpretation.
- **Three-Layer Engine:** Modifiers explicitly target Risk, Loss, and Exposure dimensions.
- **Phase 5 Anchoring:** Polymorphic pricing limits scale from mathematically absolute anchor points.

---

## Model: `casualty_gl`
*Commercial general liability — premises, operations, products/completed ops*

### Routing Protocol (Multiplexer)
- `product_type in ['general_liability', 'products_liability']`
- `revenue >= 5000000`

### Three-Layer Weight Distribution
> *DSI requires that weights for Risk, Loss, and Exposure each sum to 1.0 across all signal groups.*

**Validation:** PASS

| Group | Risk | Loss | Exposure |
|-------|------|------|----------|
| General Liability Class Risk | 0.30 | 0.30 | 0.20 |
| Premises & Operations | 0.25 | 0.25 | 0.20 |
| Corporate Footprint | 0.15 | 0.10 | 0.20 |
| Firm Stability | 0.10 | 0.10 | 0.15 |
| Regulatory Standing | 0.10 | 0.10 | 0.10 |
| Litigation History | 0.10 | 0.15 | 0.15 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

### Signal Architecture Rationale
This configuration contains **11 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `DIRECT_OBSERVABLE` (4 signals): Highest confidence
- `INFERRED_PROXY` (6 signals): Medium confidence
- `COHORT_INFERENCE` (1 signals): Lowest confidence

**Signal Count by Group:**
- `gl_class_risk`: 6 signals
- `premises_operations`: 5 signals

**Selection Rationale:**
- 36% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 | General Liability Class Risk | 0.80 | 0.30 | 0.30 | 0.20 |
| 2 | Premises & Operations | 0.70 | 0.25 | 0.25 | 0.20 |
| 3 | Corporate Footprint | 0.45 | 0.15 | 0.10 | 0.20 |
| 4 | Litigation History | 0.40 | 0.10 | 0.15 | 0.15 |
| 5 | Firm Stability | 0.35 | 0.10 | 0.10 | 0.15 |
| 6 | Regulatory Standing | 0.30 | 0.10 | 0.10 | 0.10 |

**Primary Assessment Driver:** `General Liability Class Risk` with combined weight of 0.80
**Secondary Driver:** `Premises & Operations` with combined weight of 0.70

### Theoretical Premium Calculation (Tier 3 Standard)
> *Per the DSI Premium Calculation Methodology v2.0, the core formula is:*
> *P_final = (Base × Rate) × ILF_relativity × Deductible_Factor × Modifiers*

**1. The Pricing Anchor:** The Base Rate of `0.4%` on `revenue` purchases exactly a `$1,000,000` Limit with a `$10,000` Deductible.
**2. Theoretical Execution:**
  - Assume `revenue` = $10,000,000
  - Base Premium = $10,000,000 × 0.004 = **$40,000**
  - If the client requests the Anchor Limit/Deductible, the factors are 1.00, resulting in a technical premium of **$40,000**.

---

## Model: `casualty_wc`
*Workers compensation — payroll-based, experience mod driven, state-specific*

### Routing Protocol (Multiplexer)
- `product_type == workers_compensation`
- `payroll >= 1000000`

### Three-Layer Weight Distribution
> *DSI requires that weights for Risk, Loss, and Exposure each sum to 1.0 across all signal groups.*

**Validation:** PASS

| Group | Risk | Loss | Exposure |
|-------|------|------|----------|
| Workplace Safety | 0.40 | 0.40 | 0.20 |
| Premises & Operations | 0.15 | 0.15 | 0.20 |
| Corporate Footprint | 0.15 | 0.10 | 0.25 |
| Firm Stability | 0.15 | 0.15 | 0.15 |
| Regulatory Standing | 0.15 | 0.20 | 0.20 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

### Signal Architecture Rationale
This configuration contains **10 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `DIRECT_OBSERVABLE` (5 signals): Highest confidence
- `INFERRED_PROXY` (5 signals): Medium confidence

**Signal Count by Group:**
- `workplace_safety`: 5 signals
- `premises_operations`: 5 signals

**Selection Rationale:**
- 50% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 | Workplace Safety | 1.00 | 0.40 | 0.40 | 0.20 |
| 2 | Regulatory Standing | 0.55 | 0.15 | 0.20 | 0.20 |
| 3 | Premises & Operations | 0.50 | 0.15 | 0.15 | 0.20 |
| 4 | Corporate Footprint | 0.50 | 0.15 | 0.10 | 0.25 |
| 5 | Firm Stability | 0.45 | 0.15 | 0.15 | 0.15 |

**Primary Assessment Driver:** `Workplace Safety` with combined weight of 1.00
**Secondary Driver:** `Regulatory Standing` with combined weight of 0.55

### Theoretical Premium Calculation (Tier 3 Standard)
> *Per the DSI Premium Calculation Methodology v2.0, the core formula is:*
> *P_final = (Base × Rate) × ILF_relativity × Deductible_Factor × Modifiers*

**1. The Pricing Anchor:** The Base Rate of `2.5%` on `payroll` purchases exactly a `$1,000,000` Limit with a `$10,000` Deductible.
**2. Theoretical Execution:**
  - Assume `payroll` = $10,000,000
  - Base Premium = $10,000,000 × 0.025 = **$250,000**
  - If the client requests the Anchor Limit/Deductible, the factors are 1.00, resulting in a technical premium of **$250,000**.

---

## Model: `casualty_auto`
*Commercial auto fleet liability — fleet-value based, driver quality, telematics*

### Routing Protocol (Multiplexer)
- `product_type == commercial_auto`
- `fleet_value >= 500000`

### Three-Layer Weight Distribution
> *DSI requires that weights for Risk, Loss, and Exposure each sum to 1.0 across all signal groups.*

**Validation:** PASS

| Group | Risk | Loss | Exposure |
|-------|------|------|----------|
| Auto Fleet Risk | 0.40 | 0.40 | 0.30 |
| Premises & Operations | 0.10 | 0.10 | 0.10 |
| Corporate Footprint | 0.15 | 0.10 | 0.20 |
| Firm Stability | 0.15 | 0.15 | 0.15 |
| Regulatory Standing | 0.10 | 0.15 | 0.15 |
| Litigation History | 0.10 | 0.10 | 0.10 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

### Signal Architecture Rationale
This configuration contains **11 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `DIRECT_OBSERVABLE` (7 signals): Highest confidence
- `INFERRED_PROXY` (4 signals): Medium confidence

**Signal Count by Group:**
- `auto_fleet_risk`: 6 signals
- `premises_operations`: 5 signals

**Selection Rationale:**
- 64% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 | Auto Fleet Risk | 1.10 | 0.40 | 0.40 | 0.30 |
| 2 | Corporate Footprint | 0.45 | 0.15 | 0.10 | 0.20 |
| 3 | Firm Stability | 0.45 | 0.15 | 0.15 | 0.15 |
| 4 | Regulatory Standing | 0.40 | 0.10 | 0.15 | 0.15 |
| 5 | Premises & Operations | 0.30 | 0.10 | 0.10 | 0.10 |
| 6 | Litigation History | 0.30 | 0.10 | 0.10 | 0.10 |

**Primary Assessment Driver:** `Auto Fleet Risk` with combined weight of 1.10
**Secondary Driver:** `Corporate Footprint` with combined weight of 0.45

### Theoretical Premium Calculation (Tier 3 Standard)
> *Per the DSI Premium Calculation Methodology v2.0, the core formula is:*
> *P_final = (Base × Rate) × ILF_relativity × Deductible_Factor × Modifiers*

**1. The Pricing Anchor:** The Base Rate of `3.5000000000000004%` on `fleet_value` purchases exactly a `$1,000,000` Limit with a `$10,000` Deductible.
**2. Theoretical Execution:**
  - Assume `fleet_value` = $10,000,000
  - Base Premium = $10,000,000 × 0.035 = **$350,000**
  - If the client requests the Anchor Limit/Deductible, the factors are 1.00, resulting in a technical premium of **$350,000**.

---

## Model: `casualty_umbrella`
*Umbrella/excess liability — underlying-premium based, tower position, nuclear verdict exposure*

### Routing Protocol (Multiplexer)
- `product_type == umbrella_excess`
- `underlying_premium >= 25000`

### Three-Layer Weight Distribution
> *DSI requires that weights for Risk, Loss, and Exposure each sum to 1.0 across all signal groups.*

**Validation:** PASS

| Group | Risk | Loss | Exposure |
|-------|------|------|----------|
| Umbrella & Excess Exposure | 0.35 | 0.35 | 0.30 |
| General Liability Class Risk | 0.15 | 0.15 | 0.15 |
| Premises & Operations | 0.10 | 0.10 | 0.10 |
| Corporate Footprint | 0.15 | 0.10 | 0.20 |
| Firm Stability | 0.10 | 0.10 | 0.10 |
| Litigation History | 0.15 | 0.20 | 0.15 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

### Signal Architecture Rationale
This configuration contains **15 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `DIRECT_OBSERVABLE` (6 signals): Highest confidence
- `INFERRED_PROXY` (7 signals): Medium confidence
- `COHORT_INFERENCE` (2 signals): Lowest confidence

**Signal Count by Group:**
- `gl_class_risk`: 6 signals
- `premises_operations`: 5 signals
- `umbrella_exposure`: 4 signals

**Selection Rationale:**
- 40% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 | Umbrella & Excess Exposure | 1.00 | 0.35 | 0.35 | 0.30 |
| 2 | Litigation History | 0.50 | 0.15 | 0.20 | 0.15 |
| 3 | General Liability Class Risk | 0.45 | 0.15 | 0.15 | 0.15 |
| 4 | Corporate Footprint | 0.45 | 0.15 | 0.10 | 0.20 |
| 5 | Premises & Operations | 0.30 | 0.10 | 0.10 | 0.10 |
| 6 | Firm Stability | 0.30 | 0.10 | 0.10 | 0.10 |

**Primary Assessment Driver:** `Umbrella & Excess Exposure` with combined weight of 1.00
**Secondary Driver:** `Litigation History` with combined weight of 0.50

### Theoretical Premium Calculation (Tier 3 Standard)
> *Per the DSI Premium Calculation Methodology v2.0, the core formula is:*
> *P_final = (Base × Rate) × ILF_relativity × Deductible_Factor × Modifiers*

**1. The Pricing Anchor:** The Base Rate of `85.0%` on `underlying_premium` purchases exactly a `$1,000,000` Limit with a `$10,000` Deductible.
**2. Theoretical Execution:**
  - Assume `underlying_premium` = $10,000,000
  - Base Premium = $10,000,000 × 0.85 = **$8,500,000**
  - If the client requests the Anchor Limit/Deductible, the factors are 1.00, resulting in a technical premium of **$8,500,000**.

---

## Model: `casualty_environmental`
*Environmental liability — pollution, remediation, regulatory defence, third-party claims*

### Routing Protocol (Multiplexer)
- `product_type == environmental_liability`
- `revenue >= 5000000`

### Three-Layer Weight Distribution
> *DSI requires that weights for Risk, Loss, and Exposure each sum to 1.0 across all signal groups.*

**Validation:** PASS

| Group | Risk | Loss | Exposure |
|-------|------|------|----------|
| Environmental Liability | 0.40 | 0.40 | 0.30 |
| General Liability Class Risk | 0.10 | 0.10 | 0.10 |
| Premises & Operations | 0.10 | 0.10 | 0.15 |
| Corporate Footprint | 0.15 | 0.10 | 0.20 |
| Firm Stability | 0.10 | 0.10 | 0.10 |
| Regulatory Standing | 0.15 | 0.20 | 0.15 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

### Signal Architecture Rationale
This configuration contains **16 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `DIRECT_OBSERVABLE` (7 signals): Highest confidence
- `INFERRED_PROXY` (7 signals): Medium confidence
- `COHORT_INFERENCE` (2 signals): Lowest confidence

**Signal Count by Group:**
- `gl_class_risk`: 6 signals
- `environmental_liability`: 5 signals
- `premises_operations`: 5 signals

**Selection Rationale:**
- 44% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 | Environmental Liability | 1.10 | 0.40 | 0.40 | 0.30 |
| 2 | Regulatory Standing | 0.50 | 0.15 | 0.20 | 0.15 |
| 3 | Corporate Footprint | 0.45 | 0.15 | 0.10 | 0.20 |
| 4 | Premises & Operations | 0.35 | 0.10 | 0.10 | 0.15 |
| 5 | General Liability Class Risk | 0.30 | 0.10 | 0.10 | 0.10 |
| 6 | Firm Stability | 0.30 | 0.10 | 0.10 | 0.10 |

**Primary Assessment Driver:** `Environmental Liability` with combined weight of 1.10
**Secondary Driver:** `Regulatory Standing` with combined weight of 0.50

### Theoretical Premium Calculation (Tier 3 Standard)
> *Per the DSI Premium Calculation Methodology v2.0, the core formula is:*
> *P_final = (Base × Rate) × ILF_relativity × Deductible_Factor × Modifiers*

**1. The Pricing Anchor:** The Base Rate of `0.5%` on `revenue` purchases exactly a `$1,000,000` Limit with a `$25,000` Deductible.
**2. Theoretical Execution:**
  - Assume `revenue` = $10,000,000
  - Base Premium = $10,000,000 × 0.005 = **$50,000**
  - If the client requests the Anchor Limit/Deductible, the factors are 1.00, resulting in a technical premium of **$50,000**.

---

## Model: `casualty_sme`
*Small-to-medium casualty — revenue under $5M, simplified GL + products*

### Routing Protocol (Multiplexer)
- `product_type in ['general_liability', 'products_liability']`
- `revenue < 5000000`

### Three-Layer Weight Distribution
> *DSI requires that weights for Risk, Loss, and Exposure each sum to 1.0 across all signal groups.*

**Validation:** PASS

| Group | Risk | Loss | Exposure |
|-------|------|------|----------|
| General Liability Class Risk | 0.35 | 0.35 | 0.25 |
| Premises & Operations | 0.25 | 0.25 | 0.25 |
| Corporate Footprint | 0.15 | 0.15 | 0.20 |
| Firm Stability | 0.15 | 0.15 | 0.15 |
| Regulatory Standing | 0.10 | 0.10 | 0.15 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

### Signal Architecture Rationale
This configuration contains **11 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `DIRECT_OBSERVABLE` (4 signals): Highest confidence
- `INFERRED_PROXY` (6 signals): Medium confidence
- `COHORT_INFERENCE` (1 signals): Lowest confidence

**Signal Count by Group:**
- `gl_class_risk`: 6 signals
- `premises_operations`: 5 signals

**Selection Rationale:**
- 36% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 | General Liability Class Risk | 0.95 | 0.35 | 0.35 | 0.25 |
| 2 | Premises & Operations | 0.75 | 0.25 | 0.25 | 0.25 |
| 3 | Corporate Footprint | 0.50 | 0.15 | 0.15 | 0.20 |
| 4 | Firm Stability | 0.45 | 0.15 | 0.15 | 0.15 |
| 5 | Regulatory Standing | 0.35 | 0.10 | 0.10 | 0.15 |

**Primary Assessment Driver:** `General Liability Class Risk` with combined weight of 0.95
**Secondary Driver:** `Premises & Operations` with combined weight of 0.75

### Theoretical Premium Calculation (Tier 3 Standard)
> *Per the DSI Premium Calculation Methodology v2.0, the core formula is:*
> *P_final = (Base × Rate) × ILF_relativity × Deductible_Factor × Modifiers*

**1. The Pricing Anchor:** The Base Rate of `0.5%` on `revenue` purchases exactly a `$500,000` Limit with a `$5,000` Deductible.
**2. Theoretical Execution:**
  - Assume `revenue` = $10,000,000
  - Base Premium = $10,000,000 × 0.005 = **$50,000**
  - If the client requests the Anchor Limit/Deductible, the factors are 1.00, resulting in a technical premium of **$50,000**.


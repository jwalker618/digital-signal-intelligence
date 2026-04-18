# DSI Logic Document: `MEDPROF`
*Generated: 2026-04-17*

## DSI Foundational Principles Adherence
This configuration is validated against the DSI Whitepaper & Vision Paper:
- **Objective Observation:** Signals derived from verifiable digital footprints, avoiding subjective interpretation.
- **Three-Layer Engine:** Modifiers explicitly target Risk, Loss, and Exposure dimensions.
- **Phase 5 Anchoring:** Polymorphic pricing limits scale from mathematically absolute anchor points.

---

## Model: `medprof_hospital`
*Medical Professional Liability — hospital + physician-group + nursing-home + telehealth + SME*

### Routing Protocol (Multiplexer)
- `employee_count >= 500`

### Three-Layer Weight Distribution
> *DSI requires that weights for Risk, Loss, and Exposure each sum to 1.0 across all signal groups.*

**Validation:** PASS

| Group | Risk | Loss | Exposure |
|-------|------|------|----------|
|  | 0.25 | 0.25 | 0.25 |
|  | 0.38 | 0.38 | 0.38 |
|  | 0.18 | 0.18 | 0.18 |
|  | 0.18 | 0.18 | 0.18 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

### Signal Architecture Rationale
This configuration contains **32 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `DIRECT_OBSERVABLE` (6 signals): Highest confidence
- `INFERRED_PROXY` (26 signals): Medium confidence

**Signal Count by Group:**
- `technical_infrastructure`: 13 signals
- `structured_data`: 7 signals
- `public_record`: 6 signals
- `corporate_footprint`: 6 signals

**Selection Rationale:**
- 19% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 |  | 1.15 | 0.38 | 0.38 | 0.38 |
| 2 |  | 0.75 | 0.25 | 0.25 | 0.25 |
| 3 |  | 0.55 | 0.18 | 0.18 | 0.18 |
| 4 |  | 0.55 | 0.18 | 0.18 | 0.18 |

**Primary Assessment Driver:** `` with combined weight of 1.15
**Secondary Driver:** `` with combined weight of 0.75

### Theoretical Premium Calculation (Tier 3 Standard)
> *Per the DSI Premium Calculation Methodology v2.0, the core formula is:*
> *P_final = (Base × Rate) × ILF_relativity × Deductible_Factor × Modifiers*

**1. The Pricing Anchor:** The Flat Premium of `$0` purchases exactly the `$1,000,000` Limit / `$50,000` Deductible Base Package.
**2. Theoretical Execution:**
  - Technical Premium = **$0**
  - *Scaling relies entirely on selecting a different Limit ID from the Bundled limit_configuration packages.*

---

## Model: `medprof_physician_group`
*Medical Professional Liability — hospital + physician-group + nursing-home + telehealth + SME*

### Routing Protocol (Multiplexer)
- `employee_count < 500`
- `employee_count >= 20`

### Three-Layer Weight Distribution
> *DSI requires that weights for Risk, Loss, and Exposure each sum to 1.0 across all signal groups.*

**Validation:** PASS

| Group | Risk | Loss | Exposure |
|-------|------|------|----------|
|  | 0.25 | 0.25 | 0.25 |
|  | 0.38 | 0.38 | 0.38 |
|  | 0.18 | 0.18 | 0.18 |
|  | 0.18 | 0.18 | 0.18 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

### Signal Architecture Rationale
This configuration contains **32 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `DIRECT_OBSERVABLE` (6 signals): Highest confidence
- `INFERRED_PROXY` (26 signals): Medium confidence

**Signal Count by Group:**
- `technical_infrastructure`: 13 signals
- `structured_data`: 7 signals
- `public_record`: 6 signals
- `corporate_footprint`: 6 signals

**Selection Rationale:**
- 19% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 |  | 1.15 | 0.38 | 0.38 | 0.38 |
| 2 |  | 0.75 | 0.25 | 0.25 | 0.25 |
| 3 |  | 0.55 | 0.18 | 0.18 | 0.18 |
| 4 |  | 0.55 | 0.18 | 0.18 | 0.18 |

**Primary Assessment Driver:** `` with combined weight of 1.15
**Secondary Driver:** `` with combined weight of 0.75

### Theoretical Premium Calculation (Tier 3 Standard)
> *Per the DSI Premium Calculation Methodology v2.0, the core formula is:*
> *P_final = (Base × Rate) × ILF_relativity × Deductible_Factor × Modifiers*

**1. The Pricing Anchor:** The Flat Premium of `$0` purchases exactly the `$1,000,000` Limit / `$50,000` Deductible Base Package.
**2. Theoretical Execution:**
  - Technical Premium = **$0**
  - *Scaling relies entirely on selecting a different Limit ID from the Bundled limit_configuration packages.*

---

## Model: `medprof_nursing_home`
*Medical Professional Liability — hospital + physician-group + nursing-home + telehealth + SME*

### Routing Protocol (Multiplexer)
- `facility_type == ltc`

### Three-Layer Weight Distribution
> *DSI requires that weights for Risk, Loss, and Exposure each sum to 1.0 across all signal groups.*

**Validation:** PASS

| Group | Risk | Loss | Exposure |
|-------|------|------|----------|
|  | 0.25 | 0.25 | 0.25 |
|  | 0.38 | 0.38 | 0.38 |
|  | 0.18 | 0.18 | 0.18 |
|  | 0.18 | 0.18 | 0.18 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

### Signal Architecture Rationale
This configuration contains **32 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `DIRECT_OBSERVABLE` (6 signals): Highest confidence
- `INFERRED_PROXY` (26 signals): Medium confidence

**Signal Count by Group:**
- `technical_infrastructure`: 13 signals
- `structured_data`: 7 signals
- `public_record`: 6 signals
- `corporate_footprint`: 6 signals

**Selection Rationale:**
- 19% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 |  | 1.15 | 0.38 | 0.38 | 0.38 |
| 2 |  | 0.75 | 0.25 | 0.25 | 0.25 |
| 3 |  | 0.55 | 0.18 | 0.18 | 0.18 |
| 4 |  | 0.55 | 0.18 | 0.18 | 0.18 |

**Primary Assessment Driver:** `` with combined weight of 1.15
**Secondary Driver:** `` with combined weight of 0.75

### Theoretical Premium Calculation (Tier 3 Standard)
> *Per the DSI Premium Calculation Methodology v2.0, the core formula is:*
> *P_final = (Base × Rate) × ILF_relativity × Deductible_Factor × Modifiers*

**1. The Pricing Anchor:** The Flat Premium of `$0` purchases exactly the `$1,000,000` Limit / `$50,000` Deductible Base Package.
**2. Theoretical Execution:**
  - Technical Premium = **$0**
  - *Scaling relies entirely on selecting a different Limit ID from the Bundled limit_configuration packages.*

---

## Model: `medprof_telehealth`
*Medical Professional Liability — hospital + physician-group + nursing-home + telehealth + SME*

### Routing Protocol (Multiplexer)
- `product_type == telehealth_mpl`

### Three-Layer Weight Distribution
> *DSI requires that weights for Risk, Loss, and Exposure each sum to 1.0 across all signal groups.*

**Validation:** PASS

| Group | Risk | Loss | Exposure |
|-------|------|------|----------|
|  | 0.25 | 0.25 | 0.25 |
|  | 0.38 | 0.38 | 0.38 |
|  | 0.18 | 0.18 | 0.18 |
|  | 0.18 | 0.18 | 0.18 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

### Signal Architecture Rationale
This configuration contains **32 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `DIRECT_OBSERVABLE` (6 signals): Highest confidence
- `INFERRED_PROXY` (26 signals): Medium confidence

**Signal Count by Group:**
- `technical_infrastructure`: 13 signals
- `structured_data`: 7 signals
- `public_record`: 6 signals
- `corporate_footprint`: 6 signals

**Selection Rationale:**
- 19% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 |  | 1.15 | 0.38 | 0.38 | 0.38 |
| 2 |  | 0.75 | 0.25 | 0.25 | 0.25 |
| 3 |  | 0.55 | 0.18 | 0.18 | 0.18 |
| 4 |  | 0.55 | 0.18 | 0.18 | 0.18 |

**Primary Assessment Driver:** `` with combined weight of 1.15
**Secondary Driver:** `` with combined weight of 0.75

### Theoretical Premium Calculation (Tier 3 Standard)
> *Per the DSI Premium Calculation Methodology v2.0, the core formula is:*
> *P_final = (Base × Rate) × ILF_relativity × Deductible_Factor × Modifiers*

**1. The Pricing Anchor:** The Flat Premium of `$0` purchases exactly the `$1,000,000` Limit / `$50,000` Deductible Base Package.
**2. Theoretical Execution:**
  - Technical Premium = **$0**
  - *Scaling relies entirely on selecting a different Limit ID from the Bundled limit_configuration packages.*

---

## Model: `medprof_sme`
*Medical Professional Liability — hospital + physician-group + nursing-home + telehealth + SME*

### Routing Protocol (Multiplexer)
- `employee_count < 20`

### Three-Layer Weight Distribution
> *DSI requires that weights for Risk, Loss, and Exposure each sum to 1.0 across all signal groups.*

**Validation:** PASS

| Group | Risk | Loss | Exposure |
|-------|------|------|----------|
|  | 0.25 | 0.25 | 0.25 |
|  | 0.38 | 0.38 | 0.38 |
|  | 0.18 | 0.18 | 0.18 |
|  | 0.18 | 0.18 | 0.18 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

### Signal Architecture Rationale
This configuration contains **32 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `DIRECT_OBSERVABLE` (6 signals): Highest confidence
- `INFERRED_PROXY` (26 signals): Medium confidence

**Signal Count by Group:**
- `technical_infrastructure`: 13 signals
- `structured_data`: 7 signals
- `public_record`: 6 signals
- `corporate_footprint`: 6 signals

**Selection Rationale:**
- 19% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 |  | 1.15 | 0.38 | 0.38 | 0.38 |
| 2 |  | 0.75 | 0.25 | 0.25 | 0.25 |
| 3 |  | 0.55 | 0.18 | 0.18 | 0.18 |
| 4 |  | 0.55 | 0.18 | 0.18 | 0.18 |

**Primary Assessment Driver:** `` with combined weight of 1.15
**Secondary Driver:** `` with combined weight of 0.75

### Theoretical Premium Calculation (Tier 3 Standard)
> *Per the DSI Premium Calculation Methodology v2.0, the core formula is:*
> *P_final = (Base × Rate) × ILF_relativity × Deductible_Factor × Modifiers*

**1. The Pricing Anchor:** The Flat Premium of `$0` purchases exactly the `$1,000,000` Limit / `$50,000` Deductible Base Package.
**2. Theoretical Execution:**
  - Technical Premium = **$0**
  - *Scaling relies entirely on selecting a different Limit ID from the Bundled limit_configuration packages.*


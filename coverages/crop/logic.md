# DSI Logic Document: `CROP`
*Generated: 2026-04-17*

## DSI Foundational Principles Adherence
This configuration is validated against the DSI Whitepaper & Vision Paper:
- **Objective Observation:** Signals derived from verifiable digital footprints, avoiding subjective interpretation.
- **Three-Layer Engine:** Modifiers explicitly target Risk, Loss, and Exposure dimensions.
- **Phase 5 Anchoring:** Polymorphic pricing limits scale from mathematically absolute anchor points.

---

## Model: `crop_multi_peril`
*MPCI — multi-peril crop insurance*

### Routing Protocol (Multiplexer)
- *Universal Routing (No constraints)*

### Three-Layer Weight Distribution
> *DSI requires that weights for Risk, Loss, and Exposure each sum to 1.0 across all signal groups.*

**Validation:** PASS

| Group | Risk | Loss | Exposure |
|-------|------|------|----------|
|  | 0.25 | 0.25 | 0.25 |
|  | 0.25 | 0.25 | 0.25 |
|  | 0.25 | 0.25 | 0.25 |
|  | 0.25 | 0.25 | 0.25 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

### Signal Architecture Rationale
This configuration contains **26 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `DIRECT_OBSERVABLE` (2 signals): Highest confidence
- `INFERRED_PROXY` (24 signals): Medium confidence

**Signal Count by Group:**
- `corporate_footprint`: 7 signals
- `structured_data`: 7 signals
- `network_authority`: 6 signals
- `technical_infrastructure`: 6 signals

**Selection Rationale:**
- 8% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 |  | 0.75 | 0.25 | 0.25 | 0.25 |
| 2 |  | 0.75 | 0.25 | 0.25 | 0.25 |
| 3 |  | 0.75 | 0.25 | 0.25 | 0.25 |
| 4 |  | 0.75 | 0.25 | 0.25 | 0.25 |

**Primary Assessment Driver:** `` with combined weight of 0.75
**Secondary Driver:** `` with combined weight of 0.75

### Theoretical Premium Calculation (Tier 3 Standard)
> *Per the DSI Premium Calculation Methodology v2.0, the core formula is:*
> *P_final = (Base × Rate) × ILF_relativity × Deductible_Factor × Modifiers*

**1. The Pricing Anchor:** The Flat Premium of `$0` purchases exactly the `$1,000,000` Limit / `$50,000` Deductible Base Package.
**2. Theoretical Execution:**
  - Technical Premium = **$0**
  - *Scaling relies entirely on selecting a different Limit ID from the Bundled limit_configuration packages.*

---

## Model: `crop_yield_protection`
*Yield protection programs*

### Routing Protocol (Multiplexer)
- `product_type == yield_protection`

### Three-Layer Weight Distribution
> *DSI requires that weights for Risk, Loss, and Exposure each sum to 1.0 across all signal groups.*

**Validation:** PASS

| Group | Risk | Loss | Exposure |
|-------|------|------|----------|
|  | 0.25 | 0.25 | 0.25 |
|  | 0.25 | 0.25 | 0.25 |
|  | 0.25 | 0.25 | 0.25 |
|  | 0.25 | 0.25 | 0.25 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

### Signal Architecture Rationale
This configuration contains **26 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `DIRECT_OBSERVABLE` (2 signals): Highest confidence
- `INFERRED_PROXY` (24 signals): Medium confidence

**Signal Count by Group:**
- `corporate_footprint`: 7 signals
- `structured_data`: 7 signals
- `network_authority`: 6 signals
- `technical_infrastructure`: 6 signals

**Selection Rationale:**
- 8% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 |  | 0.75 | 0.25 | 0.25 | 0.25 |
| 2 |  | 0.75 | 0.25 | 0.25 | 0.25 |
| 3 |  | 0.75 | 0.25 | 0.25 | 0.25 |
| 4 |  | 0.75 | 0.25 | 0.25 | 0.25 |

**Primary Assessment Driver:** `` with combined weight of 0.75
**Secondary Driver:** `` with combined weight of 0.75

### Theoretical Premium Calculation (Tier 3 Standard)
> *Per the DSI Premium Calculation Methodology v2.0, the core formula is:*
> *P_final = (Base × Rate) × ILF_relativity × Deductible_Factor × Modifiers*

**1. The Pricing Anchor:** The Flat Premium of `$0` purchases exactly the `$1,000,000` Limit / `$50,000` Deductible Base Package.
**2. Theoretical Execution:**
  - Technical Premium = **$0**
  - *Scaling relies entirely on selecting a different Limit ID from the Bundled limit_configuration packages.*

---

## Model: `crop_parametric_weather`
*Index-based / parametric weather covers*

### Routing Protocol (Multiplexer)
- `product_type == parametric_weather`

### Three-Layer Weight Distribution
> *DSI requires that weights for Risk, Loss, and Exposure each sum to 1.0 across all signal groups.*

**Validation:** PASS

| Group | Risk | Loss | Exposure |
|-------|------|------|----------|
|  | 0.25 | 0.25 | 0.25 |
|  | 0.25 | 0.25 | 0.25 |
|  | 0.25 | 0.25 | 0.25 |
|  | 0.25 | 0.25 | 0.25 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

### Signal Architecture Rationale
This configuration contains **26 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `DIRECT_OBSERVABLE` (2 signals): Highest confidence
- `INFERRED_PROXY` (24 signals): Medium confidence

**Signal Count by Group:**
- `corporate_footprint`: 7 signals
- `structured_data`: 7 signals
- `network_authority`: 6 signals
- `technical_infrastructure`: 6 signals

**Selection Rationale:**
- 8% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 |  | 0.75 | 0.25 | 0.25 | 0.25 |
| 2 |  | 0.75 | 0.25 | 0.25 | 0.25 |
| 3 |  | 0.75 | 0.25 | 0.25 | 0.25 |
| 4 |  | 0.75 | 0.25 | 0.25 | 0.25 |

**Primary Assessment Driver:** `` with combined weight of 0.75
**Secondary Driver:** `` with combined weight of 0.75

### Theoretical Premium Calculation (Tier 3 Standard)
> *Per the DSI Premium Calculation Methodology v2.0, the core formula is:*
> *P_final = (Base × Rate) × ILF_relativity × Deductible_Factor × Modifiers*

**1. The Pricing Anchor:** The Flat Premium of `$0` purchases exactly the `$1,000,000` Limit / `$50,000` Deductible Base Package.
**2. Theoretical Execution:**
  - Technical Premium = **$0**
  - *Scaling relies entirely on selecting a different Limit ID from the Bundled limit_configuration packages.*

---

## Model: `crop_livestock`
*Livestock mortality / market decline*

### Routing Protocol (Multiplexer)
- `crop_type == livestock`

### Three-Layer Weight Distribution
> *DSI requires that weights for Risk, Loss, and Exposure each sum to 1.0 across all signal groups.*

**Validation:** PASS

| Group | Risk | Loss | Exposure |
|-------|------|------|----------|
|  | 0.25 | 0.25 | 0.25 |
|  | 0.25 | 0.25 | 0.25 |
|  | 0.25 | 0.25 | 0.25 |
|  | 0.25 | 0.25 | 0.25 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

### Signal Architecture Rationale
This configuration contains **26 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `DIRECT_OBSERVABLE` (2 signals): Highest confidence
- `INFERRED_PROXY` (24 signals): Medium confidence

**Signal Count by Group:**
- `corporate_footprint`: 7 signals
- `structured_data`: 7 signals
- `network_authority`: 6 signals
- `technical_infrastructure`: 6 signals

**Selection Rationale:**
- 8% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 |  | 0.75 | 0.25 | 0.25 | 0.25 |
| 2 |  | 0.75 | 0.25 | 0.25 | 0.25 |
| 3 |  | 0.75 | 0.25 | 0.25 | 0.25 |
| 4 |  | 0.75 | 0.25 | 0.25 | 0.25 |

**Primary Assessment Driver:** `` with combined weight of 0.75
**Secondary Driver:** `` with combined weight of 0.75

### Theoretical Premium Calculation (Tier 3 Standard)
> *Per the DSI Premium Calculation Methodology v2.0, the core formula is:*
> *P_final = (Base × Rate) × ILF_relativity × Deductible_Factor × Modifiers*

**1. The Pricing Anchor:** The Flat Premium of `$0` purchases exactly the `$1,000,000` Limit / `$50,000` Deductible Base Package.
**2. Theoretical Execution:**
  - Technical Premium = **$0**
  - *Scaling relies entirely on selecting a different Limit ID from the Bundled limit_configuration packages.*

---

## Model: `crop_sme`
*Acreage < 1000*

### Routing Protocol (Multiplexer)
- `acreage < 1000`

### Three-Layer Weight Distribution
> *DSI requires that weights for Risk, Loss, and Exposure each sum to 1.0 across all signal groups.*

**Validation:** PASS

| Group | Risk | Loss | Exposure |
|-------|------|------|----------|
|  | 0.25 | 0.25 | 0.25 |
|  | 0.25 | 0.25 | 0.25 |
|  | 0.25 | 0.25 | 0.25 |
|  | 0.25 | 0.25 | 0.25 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

### Signal Architecture Rationale
This configuration contains **26 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `DIRECT_OBSERVABLE` (2 signals): Highest confidence
- `INFERRED_PROXY` (24 signals): Medium confidence

**Signal Count by Group:**
- `corporate_footprint`: 7 signals
- `structured_data`: 7 signals
- `network_authority`: 6 signals
- `technical_infrastructure`: 6 signals

**Selection Rationale:**
- 8% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 |  | 0.75 | 0.25 | 0.25 | 0.25 |
| 2 |  | 0.75 | 0.25 | 0.25 | 0.25 |
| 3 |  | 0.75 | 0.25 | 0.25 | 0.25 |
| 4 |  | 0.75 | 0.25 | 0.25 | 0.25 |

**Primary Assessment Driver:** `` with combined weight of 0.75
**Secondary Driver:** `` with combined weight of 0.75

### Theoretical Premium Calculation (Tier 3 Standard)
> *Per the DSI Premium Calculation Methodology v2.0, the core formula is:*
> *P_final = (Base × Rate) × ILF_relativity × Deductible_Factor × Modifiers*

**1. The Pricing Anchor:** The Flat Premium of `$0` purchases exactly the `$1,000,000` Limit / `$50,000` Deductible Base Package.
**2. Theoretical Execution:**
  - Technical Premium = **$0**
  - *Scaling relies entirely on selecting a different Limit ID from the Bundled limit_configuration packages.*


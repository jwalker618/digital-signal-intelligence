# DSI Logic Document: `TEO`
*Generated: 2026-04-17*

## DSI Foundational Principles Adherence
This configuration is validated against the DSI Whitepaper & Vision Paper:
- **Objective Observation:** Signals derived from verifiable digital footprints, avoiding subjective interpretation.
- **Three-Layer Engine:** Modifiers explicitly target Risk, Loss, and Exposure dimensions.
- **Phase 5 Anchoring:** Polymorphic pricing limits scale from mathematically absolute anchor points.

---

## Model: `teo_saas`
*Multi-tenant SaaS platforms*

### Routing Protocol (Multiplexer)
- `business_model == saas`

### Three-Layer Weight Distribution
> *DSI requires that weights for Risk, Loss, and Exposure each sum to 1.0 across all signal groups.*

**Validation:** PASS

| Group | Risk | Loss | Exposure |
|-------|------|------|----------|
|  | 0.50 | 0.50 | 0.50 |
|  | 0.17 | 0.17 | 0.17 |
|  | 0.17 | 0.17 | 0.17 |
|  | 0.17 | 0.17 | 0.17 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

### Signal Architecture Rationale
This configuration contains **34 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `DIRECT_OBSERVABLE` (10 signals): Highest confidence
- `INFERRED_PROXY` (24 signals): Medium confidence

**Signal Count by Group:**
- `technical_infrastructure`: 14 signals
- `corporate_footprint`: 7 signals
- `structured_data`: 7 signals
- `network_authority`: 6 signals

**Selection Rationale:**
- 29% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 |  | 1.50 | 0.50 | 0.50 | 0.50 |
| 2 |  | 0.50 | 0.17 | 0.17 | 0.17 |
| 3 |  | 0.50 | 0.17 | 0.17 | 0.17 |
| 4 |  | 0.50 | 0.17 | 0.17 | 0.17 |

**Primary Assessment Driver:** `` with combined weight of 1.50
**Secondary Driver:** `` with combined weight of 0.50

### Theoretical Premium Calculation (Tier 3 Standard)
> *Per the DSI Premium Calculation Methodology v2.0, the core formula is:*
> *P_final = (Base × Rate) × ILF_relativity × Deductible_Factor × Modifiers*

**1. The Pricing Anchor:** The Flat Premium of `$0` purchases exactly the `$1,000,000` Limit / `$50,000` Deductible Base Package.
**2. Theoretical Execution:**
  - Technical Premium = **$0**
  - *Scaling relies entirely on selecting a different Limit ID from the Bundled limit_configuration packages.*

---

## Model: `teo_aiml_vendor`
*AI / ML / LLM vendor*

### Routing Protocol (Multiplexer)
- `business_model == aiml_vendor`

### Three-Layer Weight Distribution
> *DSI requires that weights for Risk, Loss, and Exposure each sum to 1.0 across all signal groups.*

**Validation:** PASS

| Group | Risk | Loss | Exposure |
|-------|------|------|----------|
|  | 0.50 | 0.50 | 0.50 |
|  | 0.17 | 0.17 | 0.17 |
|  | 0.17 | 0.17 | 0.17 |
|  | 0.17 | 0.17 | 0.17 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

### Signal Architecture Rationale
This configuration contains **34 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `DIRECT_OBSERVABLE` (10 signals): Highest confidence
- `INFERRED_PROXY` (24 signals): Medium confidence

**Signal Count by Group:**
- `technical_infrastructure`: 14 signals
- `corporate_footprint`: 7 signals
- `structured_data`: 7 signals
- `network_authority`: 6 signals

**Selection Rationale:**
- 29% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 |  | 1.50 | 0.50 | 0.50 | 0.50 |
| 2 |  | 0.50 | 0.17 | 0.17 | 0.17 |
| 3 |  | 0.50 | 0.17 | 0.17 | 0.17 |
| 4 |  | 0.50 | 0.17 | 0.17 | 0.17 |

**Primary Assessment Driver:** `` with combined weight of 1.50
**Secondary Driver:** `` with combined weight of 0.50

### Theoretical Premium Calculation (Tier 3 Standard)
> *Per the DSI Premium Calculation Methodology v2.0, the core formula is:*
> *P_final = (Base × Rate) × ILF_relativity × Deductible_Factor × Modifiers*

**1. The Pricing Anchor:** The Flat Premium of `$0` purchases exactly the `$1,000,000` Limit / `$50,000` Deductible Base Package.
**2. Theoretical Execution:**
  - Technical Premium = **$0**
  - *Scaling relies entirely on selecting a different Limit ID from the Bundled limit_configuration packages.*

---

## Model: `teo_systems_integrator`
*Systems integrator / consultancy*

### Routing Protocol (Multiplexer)
- `business_model == systems_integrator`

### Three-Layer Weight Distribution
> *DSI requires that weights for Risk, Loss, and Exposure each sum to 1.0 across all signal groups.*

**Validation:** PASS

| Group | Risk | Loss | Exposure |
|-------|------|------|----------|
|  | 0.50 | 0.50 | 0.50 |
|  | 0.17 | 0.17 | 0.17 |
|  | 0.17 | 0.17 | 0.17 |
|  | 0.17 | 0.17 | 0.17 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

### Signal Architecture Rationale
This configuration contains **34 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `DIRECT_OBSERVABLE` (10 signals): Highest confidence
- `INFERRED_PROXY` (24 signals): Medium confidence

**Signal Count by Group:**
- `technical_infrastructure`: 14 signals
- `corporate_footprint`: 7 signals
- `structured_data`: 7 signals
- `network_authority`: 6 signals

**Selection Rationale:**
- 29% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 |  | 1.50 | 0.50 | 0.50 | 0.50 |
| 2 |  | 0.50 | 0.17 | 0.17 | 0.17 |
| 3 |  | 0.50 | 0.17 | 0.17 | 0.17 |
| 4 |  | 0.50 | 0.17 | 0.17 | 0.17 |

**Primary Assessment Driver:** `` with combined weight of 1.50
**Secondary Driver:** `` with combined weight of 0.50

### Theoretical Premium Calculation (Tier 3 Standard)
> *Per the DSI Premium Calculation Methodology v2.0, the core formula is:*
> *P_final = (Base × Rate) × ILF_relativity × Deductible_Factor × Modifiers*

**1. The Pricing Anchor:** The Flat Premium of `$0` purchases exactly the `$1,000,000` Limit / `$50,000` Deductible Base Package.
**2. Theoretical Execution:**
  - Technical Premium = **$0**
  - *Scaling relies entirely on selecting a different Limit ID from the Bundled limit_configuration packages.*

---

## Model: `teo_managed_service_provider`
*Managed services provider*

### Routing Protocol (Multiplexer)
- `business_model == managed_services`

### Three-Layer Weight Distribution
> *DSI requires that weights for Risk, Loss, and Exposure each sum to 1.0 across all signal groups.*

**Validation:** PASS

| Group | Risk | Loss | Exposure |
|-------|------|------|----------|
|  | 0.50 | 0.50 | 0.50 |
|  | 0.17 | 0.17 | 0.17 |
|  | 0.17 | 0.17 | 0.17 |
|  | 0.17 | 0.17 | 0.17 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

### Signal Architecture Rationale
This configuration contains **34 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `DIRECT_OBSERVABLE` (10 signals): Highest confidence
- `INFERRED_PROXY` (24 signals): Medium confidence

**Signal Count by Group:**
- `technical_infrastructure`: 14 signals
- `corporate_footprint`: 7 signals
- `structured_data`: 7 signals
- `network_authority`: 6 signals

**Selection Rationale:**
- 29% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 |  | 1.50 | 0.50 | 0.50 | 0.50 |
| 2 |  | 0.50 | 0.17 | 0.17 | 0.17 |
| 3 |  | 0.50 | 0.17 | 0.17 | 0.17 |
| 4 |  | 0.50 | 0.17 | 0.17 | 0.17 |

**Primary Assessment Driver:** `` with combined weight of 1.50
**Secondary Driver:** `` with combined weight of 0.50

### Theoretical Premium Calculation (Tier 3 Standard)
> *Per the DSI Premium Calculation Methodology v2.0, the core formula is:*
> *P_final = (Base × Rate) × ILF_relativity × Deductible_Factor × Modifiers*

**1. The Pricing Anchor:** The Flat Premium of `$0` purchases exactly the `$1,000,000` Limit / `$50,000` Deductible Base Package.
**2. Theoretical Execution:**
  - Technical Premium = **$0**
  - *Scaling relies entirely on selecting a different Limit ID from the Bundled limit_configuration packages.*

---

## Model: `teo_sme`
*Revenue < $25M*

### Routing Protocol (Multiplexer)
- `revenue < 25000000`

### Three-Layer Weight Distribution
> *DSI requires that weights for Risk, Loss, and Exposure each sum to 1.0 across all signal groups.*

**Validation:** PASS

| Group | Risk | Loss | Exposure |
|-------|------|------|----------|
|  | 0.50 | 0.50 | 0.50 |
|  | 0.17 | 0.17 | 0.17 |
|  | 0.17 | 0.17 | 0.17 |
|  | 0.17 | 0.17 | 0.17 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

### Signal Architecture Rationale
This configuration contains **34 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `DIRECT_OBSERVABLE` (10 signals): Highest confidence
- `INFERRED_PROXY` (24 signals): Medium confidence

**Signal Count by Group:**
- `technical_infrastructure`: 14 signals
- `corporate_footprint`: 7 signals
- `structured_data`: 7 signals
- `network_authority`: 6 signals

**Selection Rationale:**
- 29% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 |  | 1.50 | 0.50 | 0.50 | 0.50 |
| 2 |  | 0.50 | 0.17 | 0.17 | 0.17 |
| 3 |  | 0.50 | 0.17 | 0.17 | 0.17 |
| 4 |  | 0.50 | 0.17 | 0.17 | 0.17 |

**Primary Assessment Driver:** `` with combined weight of 1.50
**Secondary Driver:** `` with combined weight of 0.50

### Theoretical Premium Calculation (Tier 3 Standard)
> *Per the DSI Premium Calculation Methodology v2.0, the core formula is:*
> *P_final = (Base × Rate) × ILF_relativity × Deductible_Factor × Modifiers*

**1. The Pricing Anchor:** The Flat Premium of `$0` purchases exactly the `$1,000,000` Limit / `$50,000` Deductible Base Package.
**2. Theoretical Execution:**
  - Technical Premium = **$0**
  - *Scaling relies entirely on selecting a different Limit ID from the Bundled limit_configuration packages.*


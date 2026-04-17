# DSI Logic Document: `EVENT`
*Generated: 2026-04-17*

## DSI Foundational Principles Adherence
This configuration is validated against the DSI Whitepaper & Vision Paper:
- **Objective Observation:** Signals derived from verifiable digital footprints, avoiding subjective interpretation.
- **Three-Layer Engine:** Modifiers explicitly target Risk, Loss, and Exposure dimensions.
- **Phase 5 Anchoring:** Polymorphic pricing limits scale from mathematically absolute anchor points.

---

## Model: `event_sports`
*Sports events / fixtures*

### Routing Protocol (Multiplexer)
- `event_type == sports`

### Three-Layer Weight Distribution
> *DSI requires that weights for Risk, Loss, and Exposure each sum to 1.0 across all signal groups.*

**Validation:** PASS

| Group | Risk | Loss | Exposure |
|-------|------|------|----------|
|  | 0.43 | 0.43 | 0.43 |
|  | 0.20 | 0.20 | 0.20 |
|  | 0.18 | 0.18 | 0.18 |
|  | 0.18 | 0.18 | 0.18 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

### Signal Architecture Rationale
This configuration contains **33 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `DIRECT_OBSERVABLE` (3 signals): Highest confidence
- `INFERRED_PROXY` (30 signals): Medium confidence

**Signal Count by Group:**
- `technical_infrastructure`: 13 signals
- `corporate_footprint`: 7 signals
- `structured_data`: 7 signals
- `network_authority`: 6 signals

**Selection Rationale:**
- 9% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 |  | 1.30 | 0.43 | 0.43 | 0.43 |
| 2 |  | 0.60 | 0.20 | 0.20 | 0.20 |
| 3 |  | 0.55 | 0.18 | 0.18 | 0.18 |
| 4 |  | 0.55 | 0.18 | 0.18 | 0.18 |

**Primary Assessment Driver:** `` with combined weight of 1.30
**Secondary Driver:** `` with combined weight of 0.60

### Theoretical Premium Calculation (Tier 3 Standard)
> *Per the DSI Premium Calculation Methodology v2.0, the core formula is:*
> *P_final = (Base × Rate) × ILF_relativity × Deductible_Factor × Modifiers*

**1. The Pricing Anchor:** The Flat Premium of `$0` purchases exactly the `$1,000,000` Limit / `$50,000` Deductible Base Package.
**2. Theoretical Execution:**
  - Technical Premium = **$0**
  - *Scaling relies entirely on selecting a different Limit ID from the Bundled limit_configuration packages.*

---

## Model: `event_concert`
*Concert, tour, festival*

### Routing Protocol (Multiplexer)
- `event_type == concert`

### Three-Layer Weight Distribution
> *DSI requires that weights for Risk, Loss, and Exposure each sum to 1.0 across all signal groups.*

**Validation:** PASS

| Group | Risk | Loss | Exposure |
|-------|------|------|----------|
|  | 0.43 | 0.43 | 0.43 |
|  | 0.20 | 0.20 | 0.20 |
|  | 0.18 | 0.18 | 0.18 |
|  | 0.18 | 0.18 | 0.18 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

### Signal Architecture Rationale
This configuration contains **33 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `DIRECT_OBSERVABLE` (3 signals): Highest confidence
- `INFERRED_PROXY` (30 signals): Medium confidence

**Signal Count by Group:**
- `technical_infrastructure`: 13 signals
- `corporate_footprint`: 7 signals
- `structured_data`: 7 signals
- `network_authority`: 6 signals

**Selection Rationale:**
- 9% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 |  | 1.30 | 0.43 | 0.43 | 0.43 |
| 2 |  | 0.60 | 0.20 | 0.20 | 0.20 |
| 3 |  | 0.55 | 0.18 | 0.18 | 0.18 |
| 4 |  | 0.55 | 0.18 | 0.18 | 0.18 |

**Primary Assessment Driver:** `` with combined weight of 1.30
**Secondary Driver:** `` with combined weight of 0.60

### Theoretical Premium Calculation (Tier 3 Standard)
> *Per the DSI Premium Calculation Methodology v2.0, the core formula is:*
> *P_final = (Base × Rate) × ILF_relativity × Deductible_Factor × Modifiers*

**1. The Pricing Anchor:** The Flat Premium of `$0` purchases exactly the `$1,000,000` Limit / `$50,000` Deductible Base Package.
**2. Theoretical Execution:**
  - Technical Premium = **$0**
  - *Scaling relies entirely on selecting a different Limit ID from the Bundled limit_configuration packages.*

---

## Model: `event_conference`
*Conference, trade show, convention*

### Routing Protocol (Multiplexer)
- `event_type == conference`

### Three-Layer Weight Distribution
> *DSI requires that weights for Risk, Loss, and Exposure each sum to 1.0 across all signal groups.*

**Validation:** PASS

| Group | Risk | Loss | Exposure |
|-------|------|------|----------|
|  | 0.43 | 0.43 | 0.43 |
|  | 0.20 | 0.20 | 0.20 |
|  | 0.18 | 0.18 | 0.18 |
|  | 0.18 | 0.18 | 0.18 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

### Signal Architecture Rationale
This configuration contains **33 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `DIRECT_OBSERVABLE` (3 signals): Highest confidence
- `INFERRED_PROXY` (30 signals): Medium confidence

**Signal Count by Group:**
- `technical_infrastructure`: 13 signals
- `corporate_footprint`: 7 signals
- `structured_data`: 7 signals
- `network_authority`: 6 signals

**Selection Rationale:**
- 9% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 |  | 1.30 | 0.43 | 0.43 | 0.43 |
| 2 |  | 0.60 | 0.20 | 0.20 | 0.20 |
| 3 |  | 0.55 | 0.18 | 0.18 | 0.18 |
| 4 |  | 0.55 | 0.18 | 0.18 | 0.18 |

**Primary Assessment Driver:** `` with combined weight of 1.30
**Secondary Driver:** `` with combined weight of 0.60

### Theoretical Premium Calculation (Tier 3 Standard)
> *Per the DSI Premium Calculation Methodology v2.0, the core formula is:*
> *P_final = (Base × Rate) × ILF_relativity × Deductible_Factor × Modifiers*

**1. The Pricing Anchor:** The Flat Premium of `$0` purchases exactly the `$1,000,000` Limit / `$50,000` Deductible Base Package.
**2. Theoretical Execution:**
  - Technical Premium = **$0**
  - *Scaling relies entirely on selecting a different Limit ID from the Bundled limit_configuration packages.*

---

## Model: `event_broadcast`
*Broadcast production / live transmission*

### Routing Protocol (Multiplexer)
- `event_type == broadcast`

### Three-Layer Weight Distribution
> *DSI requires that weights for Risk, Loss, and Exposure each sum to 1.0 across all signal groups.*

**Validation:** PASS

| Group | Risk | Loss | Exposure |
|-------|------|------|----------|
|  | 0.43 | 0.43 | 0.43 |
|  | 0.20 | 0.20 | 0.20 |
|  | 0.18 | 0.18 | 0.18 |
|  | 0.18 | 0.18 | 0.18 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

### Signal Architecture Rationale
This configuration contains **33 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `DIRECT_OBSERVABLE` (3 signals): Highest confidence
- `INFERRED_PROXY` (30 signals): Medium confidence

**Signal Count by Group:**
- `technical_infrastructure`: 13 signals
- `corporate_footprint`: 7 signals
- `structured_data`: 7 signals
- `network_authority`: 6 signals

**Selection Rationale:**
- 9% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 |  | 1.30 | 0.43 | 0.43 | 0.43 |
| 2 |  | 0.60 | 0.20 | 0.20 | 0.20 |
| 3 |  | 0.55 | 0.18 | 0.18 | 0.18 |
| 4 |  | 0.55 | 0.18 | 0.18 | 0.18 |

**Primary Assessment Driver:** `` with combined weight of 1.30
**Secondary Driver:** `` with combined weight of 0.60

### Theoretical Premium Calculation (Tier 3 Standard)
> *Per the DSI Premium Calculation Methodology v2.0, the core formula is:*
> *P_final = (Base × Rate) × ILF_relativity × Deductible_Factor × Modifiers*

**1. The Pricing Anchor:** The Flat Premium of `$0` purchases exactly the `$1,000,000` Limit / `$50,000` Deductible Base Package.
**2. Theoretical Execution:**
  - Technical Premium = **$0**
  - *Scaling relies entirely on selecting a different Limit ID from the Bundled limit_configuration packages.*

---

## Model: `event_sme`
*Gross ticket revenue < $1M*

### Routing Protocol (Multiplexer)
- `gross_ticket_revenue < 1000000`

### Three-Layer Weight Distribution
> *DSI requires that weights for Risk, Loss, and Exposure each sum to 1.0 across all signal groups.*

**Validation:** PASS

| Group | Risk | Loss | Exposure |
|-------|------|------|----------|
|  | 0.43 | 0.43 | 0.43 |
|  | 0.20 | 0.20 | 0.20 |
|  | 0.18 | 0.18 | 0.18 |
|  | 0.18 | 0.18 | 0.18 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

### Signal Architecture Rationale
This configuration contains **33 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `DIRECT_OBSERVABLE` (3 signals): Highest confidence
- `INFERRED_PROXY` (30 signals): Medium confidence

**Signal Count by Group:**
- `technical_infrastructure`: 13 signals
- `corporate_footprint`: 7 signals
- `structured_data`: 7 signals
- `network_authority`: 6 signals

**Selection Rationale:**
- 9% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 |  | 1.30 | 0.43 | 0.43 | 0.43 |
| 2 |  | 0.60 | 0.20 | 0.20 | 0.20 |
| 3 |  | 0.55 | 0.18 | 0.18 | 0.18 |
| 4 |  | 0.55 | 0.18 | 0.18 | 0.18 |

**Primary Assessment Driver:** `` with combined weight of 1.30
**Secondary Driver:** `` with combined weight of 0.60

### Theoretical Premium Calculation (Tier 3 Standard)
> *Per the DSI Premium Calculation Methodology v2.0, the core formula is:*
> *P_final = (Base × Rate) × ILF_relativity × Deductible_Factor × Modifiers*

**1. The Pricing Anchor:** The Flat Premium of `$0` purchases exactly the `$1,000,000` Limit / `$50,000` Deductible Base Package.
**2. Theoretical Execution:**
  - Technical Premium = **$0**
  - *Scaling relies entirely on selecting a different Limit ID from the Bundled limit_configuration packages.*


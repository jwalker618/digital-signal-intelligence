# DSI Logic Document: `FPR`
*Generated: 2026-04-17*

## DSI Foundational Principles Adherence
This configuration is validated against the DSI Whitepaper & Vision Paper:
- **Objective Observation:** Signals derived from verifiable digital footprints, avoiding subjective interpretation.
- **Three-Layer Engine:** Modifiers explicitly target Risk, Loss, and Exposure dimensions.
- **Phase 5 Anchoring:** Polymorphic pricing limits scale from mathematically absolute anchor points.

---

## Model: `fpr_trade_credit`
*Trade credit — buyer default, insolvency, protracted default, political risk on receivables*

### Routing Protocol (Multiplexer)
- `product_type == trade_credit`
- `turnover >= 5000000`

### Three-Layer Weight Distribution
> *DSI requires that weights for Risk, Loss, and Exposure each sum to 1.0 across all signal groups.*

**Validation:** PASS

| Group | Risk | Loss | Exposure |
|-------|------|------|----------|
| Trade Credit Risk | 0.40 | 0.40 | 0.35 |
| Political Risk | 0.25 | 0.25 | 0.30 |
| Corporate Footprint | 0.20 | 0.15 | 0.20 |
| Firm Stability | 0.15 | 0.20 | 0.15 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

### Signal Architecture Rationale
This configuration contains **11 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `DIRECT_OBSERVABLE` (5 signals): Highest confidence
- `INFERRED_PROXY` (5 signals): Medium confidence
- `COHORT_INFERENCE` (1 signals): Lowest confidence

**Signal Count by Group:**
- `structured_data`: 6 signals
- `public_record`: 5 signals

**Selection Rationale:**
- 45% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 | Trade Credit Risk | 1.15 | 0.40 | 0.40 | 0.35 |
| 2 | Political Risk | 0.80 | 0.25 | 0.25 | 0.30 |
| 3 | Corporate Footprint | 0.55 | 0.20 | 0.15 | 0.20 |
| 4 | Firm Stability | 0.50 | 0.15 | 0.20 | 0.15 |

**Primary Assessment Driver:** `Trade Credit Risk` with combined weight of 1.15
**Secondary Driver:** `Political Risk` with combined weight of 0.80

### Theoretical Premium Calculation (Tier 3 Standard)
> *Per the DSI Premium Calculation Methodology v2.0, the core formula is:*
> *P_final = (Base × Rate) × ILF_relativity × Deductible_Factor × Modifiers*

**1. The Pricing Anchor:** The Base Rate of `0.7000000000000001%` on `turnover` purchases exactly a `$5,000,000` Limit with a `$100,000` Deductible.
**2. Theoretical Execution:**
  - Assume `turnover` = $10,000,000
  - Base Premium = $10,000,000 × 0.007 = **$70,000**
  - If the client requests the Anchor Limit/Deductible, the factors are 1.00, resulting in a technical premium of **$70,000**.

---

## Model: `fpr_political_risk`
*Political risk — expropriation, currency inconvertibility, political violence, contract frustration*

### Routing Protocol (Multiplexer)
- `product_type in ['political_risk', 'political_violence']`

### Three-Layer Weight Distribution
> *DSI requires that weights for Risk, Loss, and Exposure each sum to 1.0 across all signal groups.*

**Validation:** PASS

| Group | Risk | Loss | Exposure |
|-------|------|------|----------|
| Political Risk | 0.65 | 0.70 | 0.60 |
| Corporate Footprint | 0.20 | 0.15 | 0.25 |
| Firm Stability | 0.15 | 0.15 | 0.15 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

### Signal Architecture Rationale
This configuration contains **5 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `DIRECT_OBSERVABLE` (1 signals): Highest confidence
- `INFERRED_PROXY` (4 signals): Medium confidence

**Signal Count by Group:**
- `public_record`: 5 signals

**Selection Rationale:**
- 20% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 | Political Risk | 1.95 | 0.65 | 0.70 | 0.60 |
| 2 | Corporate Footprint | 0.60 | 0.20 | 0.15 | 0.25 |
| 3 | Firm Stability | 0.45 | 0.15 | 0.15 | 0.15 |

**Primary Assessment Driver:** `Political Risk` with combined weight of 1.95
**Secondary Driver:** `Corporate Footprint` with combined weight of 0.60

### Theoretical Premium Calculation (Tier 3 Standard)
> *Per the DSI Premium Calculation Methodology v2.0, the core formula is:*
> *P_final = (Base × Rate) × ILF_relativity × Deductible_Factor × Modifiers*

**1. The Pricing Anchor:** The Base Rate of `2.1999999999999997%` on `limit` purchases exactly a `$5,000,000` Limit with a `$100,000` Deductible.
**2. Theoretical Execution:**
  - Assume `limit` = $10,000,000
  - Base Premium = $10,000,000 × 0.022 = **$220,000**
  - If the client requests the Anchor Limit/Deductible, the factors are 1.00, resulting in a technical premium of **$220,000**.

---

## Model: `fpr_surety`
*Surety bonds — performance, payment, bid, maintenance; contractor financial strength focus*

### Routing Protocol (Multiplexer)
- `product_type in ['surety_bond', 'contract_bond']`

### Three-Layer Weight Distribution
> *DSI requires that weights for Risk, Loss, and Exposure each sum to 1.0 across all signal groups.*

**Validation:** PASS

| Group | Risk | Loss | Exposure |
|-------|------|------|----------|
| Surety & Bond Risk | 0.45 | 0.45 | 0.35 |
| Corporate Footprint | 0.25 | 0.20 | 0.30 |
| Firm Stability | 0.20 | 0.20 | 0.20 |
| Regulatory Standing | 0.10 | 0.15 | 0.15 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

### Signal Architecture Rationale
This configuration contains **5 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `DIRECT_OBSERVABLE` (4 signals): Highest confidence
- `INFERRED_PROXY` (1 signals): Medium confidence

**Signal Count by Group:**
- `structured_data`: 5 signals

**Selection Rationale:**
- 80% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 | Surety & Bond Risk | 1.25 | 0.45 | 0.45 | 0.35 |
| 2 | Corporate Footprint | 0.75 | 0.25 | 0.20 | 0.30 |
| 3 | Firm Stability | 0.60 | 0.20 | 0.20 | 0.20 |
| 4 | Regulatory Standing | 0.40 | 0.10 | 0.15 | 0.15 |

**Primary Assessment Driver:** `Surety & Bond Risk` with combined weight of 1.25
**Secondary Driver:** `Corporate Footprint` with combined weight of 0.75

### Theoretical Premium Calculation (Tier 3 Standard)
> *Per the DSI Premium Calculation Methodology v2.0, the core formula is:*
> *P_final = (Base × Rate) × ILF_relativity × Deductible_Factor × Modifiers*

**1. The Pricing Anchor:** The Base Rate of `2.5%` on `bond_amount` purchases exactly a `$5,000,000` Limit with a `$50,000` Deductible.
**2. Theoretical Execution:**
  - Assume `bond_amount` = $10,000,000
  - Base Premium = $10,000,000 × 0.025 = **$250,000**
  - If the client requests the Anchor Limit/Deductible, the factors are 1.00, resulting in a technical premium of **$250,000**.

---

## Model: `fpr_kidnap_ransom`
*K&R — kidnap, ransom, extortion, detention, hijack; crisis response included*

### Routing Protocol (Multiplexer)
- `product_type == kidnap_ransom`

### Three-Layer Weight Distribution
> *DSI requires that weights for Risk, Loss, and Exposure each sum to 1.0 across all signal groups.*

**Validation:** PASS

| Group | Risk | Loss | Exposure |
|-------|------|------|----------|
| Kidnap & Ransom Risk | 0.70 | 0.65 | 0.60 |
| Corporate Footprint | 0.20 | 0.20 | 0.25 |
| Firm Stability | 0.10 | 0.15 | 0.15 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

### Signal Architecture Rationale
This configuration contains **10 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `DIRECT_OBSERVABLE` (4 signals): Highest confidence
- `INFERRED_PROXY` (6 signals): Medium confidence

**Signal Count by Group:**
- `public_record`: 10 signals

**Selection Rationale:**
- 40% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 | Kidnap & Ransom Risk | 1.95 | 0.70 | 0.65 | 0.60 |
| 2 | Corporate Footprint | 0.65 | 0.20 | 0.20 | 0.25 |
| 3 | Firm Stability | 0.40 | 0.10 | 0.15 | 0.15 |

**Primary Assessment Driver:** `Kidnap & Ransom Risk` with combined weight of 1.95
**Secondary Driver:** `Corporate Footprint` with combined weight of 0.65

### Theoretical Premium Calculation (Tier 3 Standard)
> *Per the DSI Premium Calculation Methodology v2.0, the core formula is:*
> *P_final = (Base × Rate) × ILF_relativity × Deductible_Factor × Modifiers*

**1. The Pricing Anchor:** The Base Rate of `1.7999999999999998%` on `limit` purchases exactly a `$5,000,000` Limit with a `$50,000` Deductible.
**2. Theoretical Execution:**
  - Assume `limit` = $10,000,000
  - Base Premium = $10,000,000 × 0.018 = **$180,000**
  - If the client requests the Anchor Limit/Deductible, the factors are 1.00, resulting in a technical premium of **$180,000**.

---

## Model: `fpr_sme`
*Simplified FPR for smaller exposures — trade credit + political risk combined*

### Routing Protocol (Multiplexer)
- `product_type in ['trade_credit', 'political_risk']`
- `limit < 5000000`

### Three-Layer Weight Distribution
> *DSI requires that weights for Risk, Loss, and Exposure each sum to 1.0 across all signal groups.*

**Validation:** PASS

| Group | Risk | Loss | Exposure |
|-------|------|------|----------|
| Trade Credit Risk | 0.30 | 0.30 | 0.25 |
| Political Risk | 0.35 | 0.35 | 0.35 |
| Corporate Footprint | 0.20 | 0.15 | 0.25 |
| Firm Stability | 0.15 | 0.20 | 0.15 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

### Signal Architecture Rationale
This configuration contains **11 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `DIRECT_OBSERVABLE` (5 signals): Highest confidence
- `INFERRED_PROXY` (5 signals): Medium confidence
- `COHORT_INFERENCE` (1 signals): Lowest confidence

**Signal Count by Group:**
- `structured_data`: 6 signals
- `public_record`: 5 signals

**Selection Rationale:**
- 45% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 | Political Risk | 1.05 | 0.35 | 0.35 | 0.35 |
| 2 | Trade Credit Risk | 0.85 | 0.30 | 0.30 | 0.25 |
| 3 | Corporate Footprint | 0.60 | 0.20 | 0.15 | 0.25 |
| 4 | Firm Stability | 0.50 | 0.15 | 0.20 | 0.15 |

**Primary Assessment Driver:** `Political Risk` with combined weight of 1.05
**Secondary Driver:** `Trade Credit Risk` with combined weight of 0.85

### Theoretical Premium Calculation (Tier 3 Standard)
> *Per the DSI Premium Calculation Methodology v2.0, the core formula is:*
> *P_final = (Base × Rate) × ILF_relativity × Deductible_Factor × Modifiers*

**1. The Pricing Anchor:** The Base Rate of `2.5%` on `limit` purchases exactly a `$1,000,000` Limit with a `$25,000` Deductible.
**2. Theoretical Execution:**
  - Assume `limit` = $10,000,000
  - Base Premium = $10,000,000 × 0.025 = **$250,000**
  - If the client requests the Anchor Limit/Deductible, the factors are 1.00, resulting in a technical premium of **$250,000**.


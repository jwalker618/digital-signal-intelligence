# DSI Logic Document: `DO`
*Generated: 2026-04-17*

## DSI Foundational Principles Adherence
This configuration is validated against the DSI Whitepaper & Vision Paper:
- **Objective Observation:** Signals derived from verifiable digital footprints, avoiding subjective interpretation.
- **Three-Layer Engine:** Modifiers explicitly target Risk, Loss, and Exposure dimensions.
- **Phase 5 Anchoring:** Polymorphic pricing limits scale from mathematically absolute anchor points.

---

## Model: `do_general`
*D&O liability coverage based on observable governance, financial, and litigation signals*

### Routing Protocol (Multiplexer)
- `revenue > 50000000`

### Three-Layer Weight Distribution
> *DSI requires that weights for Risk, Loss, and Exposure each sum to 1.0 across all signal groups.*

**Validation:** PASS

| Group | Risk | Loss | Exposure |
|-------|------|------|----------|
| Network Authority | 0.10 | 0.05 | 0.05 |
| Corporate Governance | 0.40 | 0.38 | 0.45 |
| Financial Integrity | 0.25 | 0.32 | 0.45 |
| Litigation Profile | 0.25 | 0.25 | 0.05 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

### Signal Architecture Rationale
This configuration contains **48 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `DIRECT_OBSERVABLE` (31 signals): Highest confidence
- `INFERRED_PROXY` (17 signals): Medium confidence

**Signal Count by Group:**
- `corporate_footprint`: 19 signals
- `structured_data`: 12 signals
- `network_authority`: 8 signals
- `public_record`: 6 signals
- `company_type`: 1 signals
- `industry`: 1 signals
- `stock_exchange`: 1 signals

**Selection Rationale:**
- 65% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 | Corporate Governance | 1.23 | 0.40 | 0.38 | 0.45 |
| 2 | Financial Integrity | 1.02 | 0.25 | 0.32 | 0.45 |
| 3 | Litigation Profile | 0.55 | 0.25 | 0.25 | 0.05 |
| 4 | Network Authority | 0.20 | 0.10 | 0.05 | 0.05 |

**Primary Assessment Driver:** `Corporate Governance` with combined weight of 1.23
**Secondary Driver:** `Financial Integrity` with combined weight of 1.02

### Theoretical Premium Calculation (Tier 3 Standard)
> *Per the DSI Premium Calculation Methodology v2.0, the core formula is:*
> *P_final = (Base × Rate) × ILF_relativity × Deductible_Factor × Modifiers*

**1. The Pricing Anchor:** The Base Rate of `0.008%` on `revenue` purchases exactly a `$1,000,000` Limit with a `$50,000` Deductible.
**2. Theoretical Execution:**
  - Assume `revenue` = $10,000,000
  - Base Premium = $10,000,000 × 8e-05 = **$800**
  - If the client requests the Anchor Limit/Deductible, the factors are 1.00, resulting in a technical premium of **$800**.

---

## Model: `do_sme`
*D&O coverage for private companies with revenue under $100M*

### Routing Protocol (Multiplexer)
- `revenue <= 50000000`

### Three-Layer Weight Distribution
> *DSI requires that weights for Risk, Loss, and Exposure each sum to 1.0 across all signal groups.*

**Validation:** PASS

| Group | Risk | Loss | Exposure |
|-------|------|------|----------|
| Governance | 0.45 | 0.40 | 0.55 |
| Financial Health | 0.25 | 0.35 | 0.25 |
| Litigation Profile | 0.30 | 0.25 | 0.20 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

### Signal Architecture Rationale
This configuration contains **15 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `INFERRED_PROXY` (15 signals): Medium confidence

**Signal Count by Group:**
- `corporate_footprint`: 6 signals
- `structured_data`: 4 signals
- `public_record`: 3 signals
- `company_type`: 1 signals
- `industry`: 1 signals

**Selection Rationale:**
- 0% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 | Governance | 1.40 | 0.45 | 0.40 | 0.55 |
| 2 | Financial Health | 0.85 | 0.25 | 0.35 | 0.25 |
| 3 | Litigation Profile | 0.75 | 0.30 | 0.25 | 0.20 |

**Primary Assessment Driver:** `Governance` with combined weight of 1.40
**Secondary Driver:** `Financial Health` with combined weight of 0.85

### Theoretical Premium Calculation (Tier 3 Standard)
> *Per the DSI Premium Calculation Methodology v2.0, the core formula is:*
> *P_final = (Base × Rate) × ILF_relativity × Deductible_Factor × Modifiers*

**1. The Pricing Anchor:** The Flat Premium of `$5,000` purchases exactly the `$1,000,000` Limit / `$10,000` Deductible Base Package.
**2. Theoretical Execution:**
  - Technical Premium = **$5,000**
  - *Scaling relies entirely on selecting a different Limit ID from the Bundled limit_configuration packages.*

---

## Model: `do_public`
*Publicly listed companies — SEC reporting, securities litigation, shareholder activism*

### Routing Protocol (Multiplexer)
- `company_segment == PUBLIC`
- `revenue >= 100000000`

### Three-Layer Weight Distribution
> *DSI requires that weights for Risk, Loss, and Exposure each sum to 1.0 across all signal groups.*

**Validation:** PASS

| Group | Risk | Loss | Exposure |
|-------|------|------|----------|
| Public Company Governance | 0.50 | 0.55 | 0.45 |
| Transaction & Event Risk | 0.20 | 0.20 | 0.20 |
| Corporate Footprint | 0.15 | 0.10 | 0.20 |
| Firm Stability | 0.15 | 0.15 | 0.15 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

### Signal Architecture Rationale
This configuration contains **24 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `DIRECT_OBSERVABLE` (16 signals): Highest confidence
- `INFERRED_PROXY` (7 signals): Medium confidence
- `COHORT_INFERENCE` (1 signals): Lowest confidence

**Signal Count by Group:**
- `public_record`: 19 signals
- `structured_data`: 5 signals

**Selection Rationale:**
- 67% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 | Public Company Governance | 1.50 | 0.50 | 0.55 | 0.45 |
| 2 | Transaction & Event Risk | 0.60 | 0.20 | 0.20 | 0.20 |
| 3 | Corporate Footprint | 0.45 | 0.15 | 0.10 | 0.20 |
| 4 | Firm Stability | 0.45 | 0.15 | 0.15 | 0.15 |

**Primary Assessment Driver:** `Public Company Governance` with combined weight of 1.50
**Secondary Driver:** `Transaction & Event Risk` with combined weight of 0.60

### Theoretical Premium Calculation (Tier 3 Standard)
> *Per the DSI Premium Calculation Methodology v2.0, the core formula is:*
> *P_final = (Base × Rate) × ILF_relativity × Deductible_Factor × Modifiers*

**1. The Pricing Anchor:** The Base Rate of `0.013999999999999999%` on `revenue` purchases exactly a `$10,000,000` Limit with a `$500,000` Deductible.
**2. Theoretical Execution:**
  - Assume `revenue` = $10,000,000
  - Base Premium = $10,000,000 × 0.00014 = **$1,400**
  - If the client requests the Anchor Limit/Deductible, the factors are 1.00, resulting in a technical premium of **$1,400**.

---

## Model: `do_pe_backed`
*PE/VC portfolio companies — sponsor dynamics, exit pressure, board composition*

### Routing Protocol (Multiplexer)
- `company_segment == PE_BACKED`

### Three-Layer Weight Distribution
> *DSI requires that weights for Risk, Loss, and Exposure each sum to 1.0 across all signal groups.*

**Validation:** PASS

| Group | Risk | Loss | Exposure |
|-------|------|------|----------|
| Transaction & Event Risk | 0.35 | 0.30 | 0.25 |
| Corporate Footprint | 0.20 | 0.20 | 0.25 |
| Firm Stability | 0.20 | 0.20 | 0.20 |
| Regulatory Standing | 0.25 | 0.30 | 0.30 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

### Signal Architecture Rationale
This configuration contains **5 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `DIRECT_OBSERVABLE` (3 signals): Highest confidence
- `INFERRED_PROXY` (2 signals): Medium confidence

**Signal Count by Group:**
- `structured_data`: 5 signals

**Selection Rationale:**
- 60% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 | Transaction & Event Risk | 0.90 | 0.35 | 0.30 | 0.25 |
| 2 | Regulatory Standing | 0.85 | 0.25 | 0.30 | 0.30 |
| 3 | Corporate Footprint | 0.65 | 0.20 | 0.20 | 0.25 |
| 4 | Firm Stability | 0.60 | 0.20 | 0.20 | 0.20 |

**Primary Assessment Driver:** `Transaction & Event Risk` with combined weight of 0.90
**Secondary Driver:** `Regulatory Standing` with combined weight of 0.85

### Theoretical Premium Calculation (Tier 3 Standard)
> *Per the DSI Premium Calculation Methodology v2.0, the core formula is:*
> *P_final = (Base × Rate) × ILF_relativity × Deductible_Factor × Modifiers*

**1. The Pricing Anchor:** The Base Rate of `0.013%` on `revenue` purchases exactly a `$5,000,000` Limit with a `$250,000` Deductible.
**2. Theoretical Execution:**
  - Assume `revenue` = $10,000,000
  - Base Premium = $10,000,000 × 0.00013 = **$1,300**
  - If the client requests the Anchor Limit/Deductible, the factors are 1.00, resulting in a technical premium of **$1,300**.

---

## Model: `do_nonprofit`
*Non-profit and charitable organisations — donor restrictions, fiduciary duties, regulatory compliance*

### Routing Protocol (Multiplexer)
- `company_segment == NONPROFIT`

### Three-Layer Weight Distribution
> *DSI requires that weights for Risk, Loss, and Exposure each sum to 1.0 across all signal groups.*

**Validation:** PASS

| Group | Risk | Loss | Exposure |
|-------|------|------|----------|
| Corporate Footprint | 0.25 | 0.20 | 0.25 |
| Firm Stability | 0.25 | 0.25 | 0.20 |
| Regulatory Standing | 0.40 | 0.45 | 0.40 |
| Transaction & Event Risk | 0.10 | 0.10 | 0.15 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

### Signal Architecture Rationale
This configuration contains **5 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `DIRECT_OBSERVABLE` (3 signals): Highest confidence
- `INFERRED_PROXY` (2 signals): Medium confidence

**Signal Count by Group:**
- `structured_data`: 5 signals

**Selection Rationale:**
- 60% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 | Regulatory Standing | 1.25 | 0.40 | 0.45 | 0.40 |
| 2 | Corporate Footprint | 0.70 | 0.25 | 0.20 | 0.25 |
| 3 | Firm Stability | 0.70 | 0.25 | 0.25 | 0.20 |
| 4 | Transaction & Event Risk | 0.35 | 0.10 | 0.10 | 0.15 |

**Primary Assessment Driver:** `Regulatory Standing` with combined weight of 1.25
**Secondary Driver:** `Corporate Footprint` with combined weight of 0.70

### Theoretical Premium Calculation (Tier 3 Standard)
> *Per the DSI Premium Calculation Methodology v2.0, the core formula is:*
> *P_final = (Base × Rate) × ILF_relativity × Deductible_Factor × Modifiers*

**1. The Pricing Anchor:** The Base Rate of `0.006%` on `revenue` purchases exactly a `$2,000,000` Limit with a `$25,000` Deductible.
**2. Theoretical Execution:**
  - Assume `revenue` = $10,000,000
  - Base Premium = $10,000,000 × 6e-05 = **$600**
  - If the client requests the Anchor Limit/Deductible, the factors are 1.00, resulting in a technical premium of **$600**.

---

## Model: `do_ipo_spac`
*IPO and SPAC de-SPAC transactions — elevated SCA risk, prospectus liability, short selling*

### Routing Protocol (Multiplexer)
- `company_segment in ['IPO', 'SPAC']`
- `revenue >= 10000000`

### Three-Layer Weight Distribution
> *DSI requires that weights for Risk, Loss, and Exposure each sum to 1.0 across all signal groups.*

**Validation:** PASS

| Group | Risk | Loss | Exposure |
|-------|------|------|----------|
| Transaction & Event Risk | 0.40 | 0.40 | 0.30 |
| Public Company Governance | 0.30 | 0.35 | 0.35 |
| Corporate Footprint | 0.15 | 0.10 | 0.20 |
| Firm Stability | 0.15 | 0.15 | 0.15 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

### Signal Architecture Rationale
This configuration contains **10 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `DIRECT_OBSERVABLE` (6 signals): Highest confidence
- `INFERRED_PROXY` (3 signals): Medium confidence
- `COHORT_INFERENCE` (1 signals): Lowest confidence

**Signal Count by Group:**
- `public_record`: 5 signals
- `structured_data`: 5 signals

**Selection Rationale:**
- 60% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 | Transaction & Event Risk | 1.10 | 0.40 | 0.40 | 0.30 |
| 2 | Public Company Governance | 1.00 | 0.30 | 0.35 | 0.35 |
| 3 | Corporate Footprint | 0.45 | 0.15 | 0.10 | 0.20 |
| 4 | Firm Stability | 0.45 | 0.15 | 0.15 | 0.15 |

**Primary Assessment Driver:** `Transaction & Event Risk` with combined weight of 1.10
**Secondary Driver:** `Public Company Governance` with combined weight of 1.00

### Theoretical Premium Calculation (Tier 3 Standard)
> *Per the DSI Premium Calculation Methodology v2.0, the core formula is:*
> *P_final = (Base × Rate) × ILF_relativity × Deductible_Factor × Modifiers*

**1. The Pricing Anchor:** The Base Rate of `0.03%` on `revenue` purchases exactly a `$10,000,000` Limit with a `$1,000,000` Deductible.
**2. Theoretical Execution:**
  - Assume `revenue` = $10,000,000
  - Base Premium = $10,000,000 × 0.0003 = **$3,000**
  - If the client requests the Anchor Limit/Deductible, the factors are 1.00, resulting in a technical premium of **$3,000**.


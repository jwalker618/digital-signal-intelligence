# DSI Logic Document: `CYBER`
*Generated: 2026-04-17*

## DSI Foundational Principles Adherence
This configuration is validated against the DSI Whitepaper & Vision Paper:
- **Objective Observation:** Signals derived from verifiable digital footprints, avoiding subjective interpretation.
- **Three-Layer Engine:** Modifiers explicitly target Risk, Loss, and Exposure dimensions.
- **Phase 5 Anchoring:** Polymorphic pricing limits scale from mathematically absolute anchor points.

---

## Model: `cyber_general`
*Cyber liability model based on externally observable technical signals*

### Routing Protocol (Multiplexer)
- `revenue > 50000000`

### Three-Layer Weight Distribution
> *DSI requires that weights for Risk, Loss, and Exposure each sum to 1.0 across all signal groups.*

**Validation:** PASS

| Group | Risk | Loss | Exposure |
|-------|------|------|----------|
| Network Authority | 0.15 | 0.15 | 0.15 |
| Technical Infrastructure | 0.35 | 0.35 | 0.35 |
| Corporate Footprint | 0.15 | 0.25 | 0.25 |
| Public Record | 0.25 | 0.15 | 0.15 |
| Structured Data | 0.10 | 0.10 | 0.10 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

### Signal Architecture Rationale
This configuration contains **44 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `DIRECT_OBSERVABLE` (23 signals): Highest confidence
- `INFERRED_PROXY` (21 signals): Medium confidence

**Signal Count by Group:**
- `corporate_footprint`: 15 signals
- `technical_infrastructure`: 10 signals
- `network_authority`: 8 signals
- `public_record`: 5 signals
- `structured_data`: 3 signals
- `industry_classification`: 1 signals
- `size_band`: 1 signals
- `geography`: 1 signals

**Selection Rationale:**
- 52% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 | Technical Infrastructure | 1.05 | 0.35 | 0.35 | 0.35 |
| 2 | Corporate Footprint | 0.65 | 0.15 | 0.25 | 0.25 |
| 3 | Public Record | 0.55 | 0.25 | 0.15 | 0.15 |
| 4 | Network Authority | 0.45 | 0.15 | 0.15 | 0.15 |
| 5 | Structured Data | 0.30 | 0.10 | 0.10 | 0.10 |

**Primary Assessment Driver:** `Technical Infrastructure` with combined weight of 1.05
**Secondary Driver:** `Corporate Footprint` with combined weight of 0.65

### Theoretical Premium Calculation (Tier 3 Standard)
> *Per the DSI Premium Calculation Methodology v2.0, the core formula is:*
> *P_final = (Base × Rate) × ILF_relativity × Deductible_Factor × Modifiers*

**1. The Pricing Anchor:** The Base Rate of `0.008%` on `revenue` purchases exactly a `$1,000,000` Limit with a `$50,000` Deductible.
**2. Theoretical Execution:**
  - Assume `revenue` = $10,000,000
  - Base Premium = $10,000,000 × 8e-05 = **$800**
  - If the client requests the Anchor Limit/Deductible, the factors are 1.00, resulting in a technical premium of **$800**.

---

## Model: `cyber_sme`
*Cyber liability model for SME segment - automated underwriting for small businesses*

### Routing Protocol (Multiplexer)
- `revenue <= 50000000`
- `limit <= 5000000`

### Three-Layer Weight Distribution
> *DSI requires that weights for Risk, Loss, and Exposure each sum to 1.0 across all signal groups.*

**Validation:** PASS

| Group | Risk | Loss | Exposure |
|-------|------|------|----------|
| Technical Security | 0.40 | 0.35 | 0.30 |
| Public Record | 0.35 | 0.40 | 0.40 |
| Corporate Footprint | 0.25 | 0.25 | 0.30 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

### Signal Architecture Rationale
This configuration contains **15 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `DIRECT_OBSERVABLE` (14 signals): Highest confidence
- `INFERRED_PROXY` (1 signals): Medium confidence

**Signal Count by Group:**
- `technical_infrastructure`: 6 signals
- `public_record`: 4 signals
- `corporate_footprint`: 3 signals
- `industry_classification`: 1 signals
- `company_size`: 1 signals

**Selection Rationale:**
- 93% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 | Public Record | 1.15 | 0.35 | 0.40 | 0.40 |
| 2 | Technical Security | 1.05 | 0.40 | 0.35 | 0.30 |
| 3 | Corporate Footprint | 0.80 | 0.25 | 0.25 | 0.30 |

**Primary Assessment Driver:** `Public Record` with combined weight of 1.15
**Secondary Driver:** `Technical Security` with combined weight of 1.05

### Theoretical Premium Calculation (Tier 3 Standard)
> *Per the DSI Premium Calculation Methodology v2.0, the core formula is:*
> *P_final = (Base × Rate) × ILF_relativity × Deductible_Factor × Modifiers*

**1. The Pricing Anchor:** The Flat Premium of `$4,000` purchases exactly the `$1,000,000` Limit / `$5,000` Deductible Base Package.
**2. Theoretical Execution:**
  - Technical Premium = **$4,000**
  - *Scaling relies entirely on selecting a different Limit ID from the Bundled limit_configuration packages.*

---

## Model: `cyber_healthcare`
*Health systems, hospitals, pharma, health tech*

### Routing Protocol (Multiplexer)
- `industry_sector == HEALTHCARE`
- `revenue > 50000000`

### Three-Layer Weight Distribution
> *DSI requires that weights for Risk, Loss, and Exposure each sum to 1.0 across all signal groups.*

**Validation:** PASS

| Group | Risk | Loss | Exposure |
|-------|------|------|----------|
| Health Data Security | 0.50 | 0.55 | 0.50 |
| Network Authority | 0.10 | 0.05 | 0.05 |
| Public Record | 0.20 | 0.20 | 0.15 |
| Structured Data | 0.10 | 0.10 | 0.15 |
| Corporate Footprint | 0.10 | 0.10 | 0.15 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

### Signal Architecture Rationale
This configuration contains **6 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `DIRECT_OBSERVABLE` (2 signals): Highest confidence
- `INFERRED_PROXY` (4 signals): Medium confidence

**Signal Count by Group:**
- `technical_infrastructure`: 6 signals

**Selection Rationale:**
- 33% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 | Health Data Security | 1.55 | 0.50 | 0.55 | 0.50 |
| 2 | Public Record | 0.55 | 0.20 | 0.20 | 0.15 |
| 3 | Structured Data | 0.35 | 0.10 | 0.10 | 0.15 |
| 4 | Corporate Footprint | 0.35 | 0.10 | 0.10 | 0.15 |
| 5 | Network Authority | 0.20 | 0.10 | 0.05 | 0.05 |

**Primary Assessment Driver:** `Health Data Security` with combined weight of 1.55
**Secondary Driver:** `Public Record` with combined weight of 0.55

### Theoretical Premium Calculation (Tier 3 Standard)
> *Per the DSI Premium Calculation Methodology v2.0, the core formula is:*
> *P_final = (Base × Rate) × ILF_relativity × Deductible_Factor × Modifiers*

**1. The Pricing Anchor:** The Base Rate of `0.3%` on `revenue` purchases exactly a `$10,000,000` Limit with a `$50,000` Deductible.
**2. Theoretical Execution:**
  - Assume `revenue` = $10,000,000
  - Base Premium = $10,000,000 × 0.003 = **$30,000**
  - If the client requests the Anchor Limit/Deductible, the factors are 1.00, resulting in a technical premium of **$30,000**.

---

## Model: `cyber_financial_services`
*Banks, insurers, payment processors, fintech*

### Routing Protocol (Multiplexer)
- `industry_sector == FINANCIAL_SERVICES`
- `revenue > 50000000`

### Three-Layer Weight Distribution
> *DSI requires that weights for Risk, Loss, and Exposure each sum to 1.0 across all signal groups.*

**Validation:** PASS

| Group | Risk | Loss | Exposure |
|-------|------|------|----------|
| Financial System Security | 0.50 | 0.55 | 0.50 |
| Network Authority | 0.10 | 0.05 | 0.05 |
| Public Record | 0.20 | 0.20 | 0.15 |
| Structured Data | 0.10 | 0.10 | 0.15 |
| Corporate Footprint | 0.10 | 0.10 | 0.15 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

### Signal Architecture Rationale
This configuration contains **6 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `DIRECT_OBSERVABLE` (2 signals): Highest confidence
- `INFERRED_PROXY` (4 signals): Medium confidence

**Signal Count by Group:**
- `technical_infrastructure`: 6 signals

**Selection Rationale:**
- 33% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 | Financial System Security | 1.55 | 0.50 | 0.55 | 0.50 |
| 2 | Public Record | 0.55 | 0.20 | 0.20 | 0.15 |
| 3 | Structured Data | 0.35 | 0.10 | 0.10 | 0.15 |
| 4 | Corporate Footprint | 0.35 | 0.10 | 0.10 | 0.15 |
| 5 | Network Authority | 0.20 | 0.10 | 0.05 | 0.05 |

**Primary Assessment Driver:** `Financial System Security` with combined weight of 1.55
**Secondary Driver:** `Public Record` with combined weight of 0.55

### Theoretical Premium Calculation (Tier 3 Standard)
> *Per the DSI Premium Calculation Methodology v2.0, the core formula is:*
> *P_final = (Base × Rate) × ILF_relativity × Deductible_Factor × Modifiers*

**1. The Pricing Anchor:** The Base Rate of `0.27999999999999997%` on `revenue` purchases exactly a `$10,000,000` Limit with a `$50,000` Deductible.
**2. Theoretical Execution:**
  - Assume `revenue` = $10,000,000
  - Base Premium = $10,000,000 × 0.0028 = **$28,000**
  - If the client requests the Anchor Limit/Deductible, the factors are 1.00, resulting in a technical premium of **$28,000**.

---

## Model: `cyber_critical_infrastructure`
*Utilities, telecom, water, transportation*

### Routing Protocol (Multiplexer)
- `industry_sector in ['UTILITIES', 'TELECOM', 'WATER', 'TRANSPORTATION']`
- `revenue > 50000000`

### Three-Layer Weight Distribution
> *DSI requires that weights for Risk, Loss, and Exposure each sum to 1.0 across all signal groups.*

**Validation:** PASS

| Group | Risk | Loss | Exposure |
|-------|------|------|----------|
| OT/ICS Security | 0.60 | 0.60 | 0.55 |
| Network Authority | 0.05 | 0.05 | 0.05 |
| Public Record | 0.15 | 0.15 | 0.10 |
| Structured Data | 0.10 | 0.10 | 0.15 |
| Corporate Footprint | 0.10 | 0.10 | 0.15 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

### Signal Architecture Rationale
This configuration contains **5 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `DIRECT_OBSERVABLE` (1 signals): Highest confidence
- `INFERRED_PROXY` (4 signals): Medium confidence

**Signal Count by Group:**
- `technical_infrastructure`: 5 signals

**Selection Rationale:**
- 20% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 | OT/ICS Security | 1.75 | 0.60 | 0.60 | 0.55 |
| 2 | Public Record | 0.40 | 0.15 | 0.15 | 0.10 |
| 3 | Structured Data | 0.35 | 0.10 | 0.10 | 0.15 |
| 4 | Corporate Footprint | 0.35 | 0.10 | 0.10 | 0.15 |
| 5 | Network Authority | 0.15 | 0.05 | 0.05 | 0.05 |

**Primary Assessment Driver:** `OT/ICS Security` with combined weight of 1.75
**Secondary Driver:** `Public Record` with combined weight of 0.40

### Theoretical Premium Calculation (Tier 3 Standard)
> *Per the DSI Premium Calculation Methodology v2.0, the core formula is:*
> *P_final = (Base × Rate) × ILF_relativity × Deductible_Factor × Modifiers*

**1. The Pricing Anchor:** The Base Rate of `0.35000000000000003%` on `revenue` purchases exactly a `$10,000,000` Limit with a `$50,000` Deductible.
**2. Theoretical Execution:**
  - Assume `revenue` = $10,000,000
  - Base Premium = $10,000,000 × 0.0035 = **$35,000**
  - If the client requests the Anchor Limit/Deductible, the factors are 1.00, resulting in a technical premium of **$35,000**.

---

## Model: `cyber_technology`
*SaaS, software vendors, MSPs, IT services*

### Routing Protocol (Multiplexer)
- `industry_sector in ['TECHNOLOGY', 'SOFTWARE', 'IT_SERVICES', 'MSP']`

### Three-Layer Weight Distribution
> *DSI requires that weights for Risk, Loss, and Exposure each sum to 1.0 across all signal groups.*

**Validation:** PASS

| Group | Risk | Loss | Exposure |
|-------|------|------|----------|
| Product & Supply Chain Security | 0.55 | 0.60 | 0.50 |
| Network Authority | 0.10 | 0.05 | 0.05 |
| Public Record | 0.15 | 0.15 | 0.15 |
| Structured Data | 0.10 | 0.10 | 0.15 |
| Corporate Footprint | 0.10 | 0.10 | 0.15 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

### Signal Architecture Rationale
This configuration contains **10 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `DIRECT_OBSERVABLE` (1 signals): Highest confidence
- `INFERRED_PROXY` (9 signals): Medium confidence

**Signal Count by Group:**
- `technical_infrastructure`: 6 signals
- `structured_data`: 3 signals
- `public_record`: 1 signals

**Selection Rationale:**
- 10% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 | Product & Supply Chain Security | 1.65 | 0.55 | 0.60 | 0.50 |
| 2 | Public Record | 0.45 | 0.15 | 0.15 | 0.15 |
| 3 | Structured Data | 0.35 | 0.10 | 0.10 | 0.15 |
| 4 | Corporate Footprint | 0.35 | 0.10 | 0.10 | 0.15 |
| 5 | Network Authority | 0.20 | 0.10 | 0.05 | 0.05 |

**Primary Assessment Driver:** `Product & Supply Chain Security` with combined weight of 1.65
**Secondary Driver:** `Public Record` with combined weight of 0.45

### Theoretical Premium Calculation (Tier 3 Standard)
> *Per the DSI Premium Calculation Methodology v2.0, the core formula is:*
> *P_final = (Base × Rate) × ILF_relativity × Deductible_Factor × Modifiers*

**1. The Pricing Anchor:** The Base Rate of `0.32%` on `revenue` purchases exactly a `$10,000,000` Limit with a `$50,000` Deductible.
**2. Theoretical Execution:**
  - Assume `revenue` = $10,000,000
  - Base Premium = $10,000,000 × 0.0032 = **$32,000**
  - If the client requests the Anchor Limit/Deductible, the factors are 1.00, resulting in a technical premium of **$32,000**.

---

## Model: `cyber_digital_platform`
*Marketplaces, social media, adtech, media platforms*

### Routing Protocol (Multiplexer)
- `industry_sector in ['DIGITAL_PLATFORM', 'MEDIA', 'ADTECH', 'SOCIAL']`

### Three-Layer Weight Distribution
> *DSI requires that weights for Risk, Loss, and Exposure each sum to 1.0 across all signal groups.*

**Validation:** PASS

| Group | Risk | Loss | Exposure |
|-------|------|------|----------|
| Platform User Security | 0.55 | 0.60 | 0.50 |
| Network Authority | 0.10 | 0.05 | 0.05 |
| Public Record | 0.15 | 0.15 | 0.15 |
| Structured Data | 0.10 | 0.10 | 0.15 |
| Corporate Footprint | 0.10 | 0.10 | 0.15 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

### Signal Architecture Rationale
This configuration contains **8 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `DIRECT_OBSERVABLE` (1 signals): Highest confidence
- `INFERRED_PROXY` (7 signals): Medium confidence

**Signal Count by Group:**
- `technical_infrastructure`: 6 signals
- `public_record`: 1 signals
- `structured_data`: 1 signals

**Selection Rationale:**
- 12% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 | Platform User Security | 1.65 | 0.55 | 0.60 | 0.50 |
| 2 | Public Record | 0.45 | 0.15 | 0.15 | 0.15 |
| 3 | Structured Data | 0.35 | 0.10 | 0.10 | 0.15 |
| 4 | Corporate Footprint | 0.35 | 0.10 | 0.10 | 0.15 |
| 5 | Network Authority | 0.20 | 0.10 | 0.05 | 0.05 |

**Primary Assessment Driver:** `Platform User Security` with combined weight of 1.65
**Secondary Driver:** `Public Record` with combined weight of 0.45

### Theoretical Premium Calculation (Tier 3 Standard)
> *Per the DSI Premium Calculation Methodology v2.0, the core formula is:*
> *P_final = (Base × Rate) × ILF_relativity × Deductible_Factor × Modifiers*

**1. The Pricing Anchor:** The Base Rate of `0.25%` on `revenue` purchases exactly a `$10,000,000` Limit with a `$50,000` Deductible.
**2. Theoretical Execution:**
  - Assume `revenue` = $10,000,000
  - Base Premium = $10,000,000 × 0.0025 = **$25,000**
  - If the client requests the Anchor Limit/Deductible, the factors are 1.00, resulting in a technical premium of **$25,000**.

---

## Model: `cyber_manufacturing`
*Manufacturing with OT/IT convergence risk*

### Routing Protocol (Multiplexer)
- `industry_sector in ['MANUFACTURING', 'INDUSTRIAL']`

### Three-Layer Weight Distribution
> *DSI requires that weights for Risk, Loss, and Exposure each sum to 1.0 across all signal groups.*

**Validation:** PASS

| Group | Risk | Loss | Exposure |
|-------|------|------|----------|
| Manufacturing Operations Security | 0.55 | 0.60 | 0.50 |
| Network Authority | 0.10 | 0.05 | 0.05 |
| Public Record | 0.15 | 0.15 | 0.15 |
| Structured Data | 0.10 | 0.10 | 0.15 |
| Corporate Footprint | 0.10 | 0.10 | 0.15 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

### Signal Architecture Rationale
This configuration contains **5 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `INFERRED_PROXY` (5 signals): Medium confidence

**Signal Count by Group:**
- `technical_infrastructure`: 5 signals

**Selection Rationale:**
- 0% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 | Manufacturing Operations Security | 1.65 | 0.55 | 0.60 | 0.50 |
| 2 | Public Record | 0.45 | 0.15 | 0.15 | 0.15 |
| 3 | Structured Data | 0.35 | 0.10 | 0.10 | 0.15 |
| 4 | Corporate Footprint | 0.35 | 0.10 | 0.10 | 0.15 |
| 5 | Network Authority | 0.20 | 0.10 | 0.05 | 0.05 |

**Primary Assessment Driver:** `Manufacturing Operations Security` with combined weight of 1.65
**Secondary Driver:** `Public Record` with combined weight of 0.45

### Theoretical Premium Calculation (Tier 3 Standard)
> *Per the DSI Premium Calculation Methodology v2.0, the core formula is:*
> *P_final = (Base × Rate) × ILF_relativity × Deductible_Factor × Modifiers*

**1. The Pricing Anchor:** The Base Rate of `0.3%` on `revenue` purchases exactly a `$10,000,000` Limit with a `$50,000` Deductible.
**2. Theoretical Execution:**
  - Assume `revenue` = $10,000,000
  - Base Premium = $10,000,000 × 0.003 = **$30,000**
  - If the client requests the Anchor Limit/Deductible, the factors are 1.00, resulting in a technical premium of **$30,000**.

---

## Model: `cyber_retail`
*Retail, e-commerce, hospitality*

### Routing Protocol (Multiplexer)
- `industry_sector in ['RETAIL', 'ECOMMERCE', 'HOSPITALITY']`

### Three-Layer Weight Distribution
> *DSI requires that weights for Risk, Loss, and Exposure each sum to 1.0 across all signal groups.*

**Validation:** PASS

| Group | Risk | Loss | Exposure |
|-------|------|------|----------|
| Retail Operations Security | 0.55 | 0.60 | 0.50 |
| Network Authority | 0.10 | 0.05 | 0.05 |
| Public Record | 0.15 | 0.15 | 0.15 |
| Structured Data | 0.10 | 0.10 | 0.15 |
| Corporate Footprint | 0.10 | 0.10 | 0.15 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

### Signal Architecture Rationale
This configuration contains **6 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `DIRECT_OBSERVABLE` (1 signals): Highest confidence
- `INFERRED_PROXY` (5 signals): Medium confidence

**Signal Count by Group:**
- `technical_infrastructure`: 6 signals

**Selection Rationale:**
- 17% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 | Retail Operations Security | 1.65 | 0.55 | 0.60 | 0.50 |
| 2 | Public Record | 0.45 | 0.15 | 0.15 | 0.15 |
| 3 | Structured Data | 0.35 | 0.10 | 0.10 | 0.15 |
| 4 | Corporate Footprint | 0.35 | 0.10 | 0.10 | 0.15 |
| 5 | Network Authority | 0.20 | 0.10 | 0.05 | 0.05 |

**Primary Assessment Driver:** `Retail Operations Security` with combined weight of 1.65
**Secondary Driver:** `Public Record` with combined weight of 0.45

### Theoretical Premium Calculation (Tier 3 Standard)
> *Per the DSI Premium Calculation Methodology v2.0, the core formula is:*
> *P_final = (Base × Rate) × ILF_relativity × Deductible_Factor × Modifiers*

**1. The Pricing Anchor:** The Base Rate of `0.22%` on `revenue` purchases exactly a `$10,000,000` Limit with a `$50,000` Deductible.
**2. Theoretical Execution:**
  - Assume `revenue` = $10,000,000
  - Base Premium = $10,000,000 × 0.0022 = **$22,000**
  - If the client requests the Anchor Limit/Deductible, the factors are 1.00, resulting in a technical premium of **$22,000**.

---

## Model: `cyber_public_sector`
*Government, education, nonprofits*

### Routing Protocol (Multiplexer)
- `industry_sector in ['GOVERNMENT', 'EDUCATION', 'NONPROFIT']`

### Three-Layer Weight Distribution
> *DSI requires that weights for Risk, Loss, and Exposure each sum to 1.0 across all signal groups.*

**Validation:** PASS

| Group | Risk | Loss | Exposure |
|-------|------|------|----------|
| Public Sector Cyber Posture | 0.55 | 0.60 | 0.50 |
| Network Authority | 0.10 | 0.05 | 0.05 |
| Public Record | 0.15 | 0.15 | 0.15 |
| Structured Data | 0.10 | 0.10 | 0.15 |
| Corporate Footprint | 0.10 | 0.10 | 0.15 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

### Signal Architecture Rationale
This configuration contains **6 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `DIRECT_OBSERVABLE` (1 signals): Highest confidence
- `INFERRED_PROXY` (5 signals): Medium confidence

**Signal Count by Group:**
- `technical_infrastructure`: 6 signals

**Selection Rationale:**
- 17% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 | Public Sector Cyber Posture | 1.65 | 0.55 | 0.60 | 0.50 |
| 2 | Public Record | 0.45 | 0.15 | 0.15 | 0.15 |
| 3 | Structured Data | 0.35 | 0.10 | 0.10 | 0.15 |
| 4 | Corporate Footprint | 0.35 | 0.10 | 0.10 | 0.15 |
| 5 | Network Authority | 0.20 | 0.10 | 0.05 | 0.05 |

**Primary Assessment Driver:** `Public Sector Cyber Posture` with combined weight of 1.65
**Secondary Driver:** `Public Record` with combined weight of 0.45

### Theoretical Premium Calculation (Tier 3 Standard)
> *Per the DSI Premium Calculation Methodology v2.0, the core formula is:*
> *P_final = (Base × Rate) × ILF_relativity × Deductible_Factor × Modifiers*

**1. The Pricing Anchor:** The Base Rate of `0.18%` on `revenue` purchases exactly a `$10,000,000` Limit with a `$50,000` Deductible.
**2. Theoretical Execution:**
  - Assume `revenue` = $10,000,000
  - Base Premium = $10,000,000 × 0.0018 = **$18,000**
  - If the client requests the Anchor Limit/Deductible, the factors are 1.00, resulting in a technical premium of **$18,000**.

---

## Model: `cyber_professional_services`
*Law firms, consultancies, accounting firms*

### Routing Protocol (Multiplexer)
- `industry_sector in ['LEGAL', 'CONSULTING', 'ACCOUNTING']`
- `revenue > 50000000`

### Three-Layer Weight Distribution
> *DSI requires that weights for Risk, Loss, and Exposure each sum to 1.0 across all signal groups.*

**Validation:** PASS

| Group | Risk | Loss | Exposure |
|-------|------|------|----------|
| Professional Data Security | 0.55 | 0.60 | 0.50 |
| Network Authority | 0.10 | 0.05 | 0.05 |
| Public Record | 0.15 | 0.15 | 0.15 |
| Structured Data | 0.10 | 0.10 | 0.15 |
| Corporate Footprint | 0.10 | 0.10 | 0.15 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

### Signal Architecture Rationale
This configuration contains **6 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `DIRECT_OBSERVABLE` (1 signals): Highest confidence
- `INFERRED_PROXY` (5 signals): Medium confidence

**Signal Count by Group:**
- `technical_infrastructure`: 6 signals

**Selection Rationale:**
- 17% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 | Professional Data Security | 1.65 | 0.55 | 0.60 | 0.50 |
| 2 | Public Record | 0.45 | 0.15 | 0.15 | 0.15 |
| 3 | Structured Data | 0.35 | 0.10 | 0.10 | 0.15 |
| 4 | Corporate Footprint | 0.35 | 0.10 | 0.10 | 0.15 |
| 5 | Network Authority | 0.20 | 0.10 | 0.05 | 0.05 |

**Primary Assessment Driver:** `Professional Data Security` with combined weight of 1.65
**Secondary Driver:** `Public Record` with combined weight of 0.45

### Theoretical Premium Calculation (Tier 3 Standard)
> *Per the DSI Premium Calculation Methodology v2.0, the core formula is:*
> *P_final = (Base × Rate) × ILF_relativity × Deductible_Factor × Modifiers*

**1. The Pricing Anchor:** The Base Rate of `0.22%` on `revenue` purchases exactly a `$10,000,000` Limit with a `$50,000` Deductible.
**2. Theoretical Execution:**
  - Assume `revenue` = $10,000,000
  - Base Premium = $10,000,000 × 0.0022 = **$22,000**
  - If the client requests the Anchor Limit/Deductible, the factors are 1.00, resulting in a technical premium of **$22,000**.

---

## Model: `cyber_aiml_vendor`
*AI / ML vendors — foundation-model providers, MLOps platforms, AI consultancies*

### Routing Protocol (Multiplexer)
- `industry_sector in ['AI_VENDOR', 'ML_VENDOR', 'AIML_PLATFORM']`

### Three-Layer Weight Distribution
> *DSI requires that weights for Risk, Loss, and Exposure each sum to 1.0 across all signal groups.*

**Validation:** PASS

| Group | Risk | Loss | Exposure |
|-------|------|------|----------|
| AI Governance & Documentation | 0.45 | 0.45 | 0.35 |
| AI Incident Record | 0.20 | 0.25 | 0.15 |
| Vendor Security Posture | 0.25 | 0.20 | 0.35 |
| Network Authority | 0.05 | 0.05 | 0.05 |
| Corporate Footprint | 0.05 | 0.05 | 0.10 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

### Signal Architecture Rationale
This configuration contains **7 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `DIRECT_OBSERVABLE` (2 signals): Highest confidence
- `INFERRED_PROXY` (5 signals): Medium confidence

**Signal Count by Group:**
- `structured_data`: 3 signals
- `technical_infrastructure`: 3 signals
- `public_record`: 1 signals

**Selection Rationale:**
- 29% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 | AI Governance & Documentation | 1.25 | 0.45 | 0.45 | 0.35 |
| 2 | Vendor Security Posture | 0.80 | 0.25 | 0.20 | 0.35 |
| 3 | AI Incident Record | 0.60 | 0.20 | 0.25 | 0.15 |
| 4 | Corporate Footprint | 0.20 | 0.05 | 0.05 | 0.10 |
| 5 | Network Authority | 0.15 | 0.05 | 0.05 | 0.05 |

**Primary Assessment Driver:** `AI Governance & Documentation` with combined weight of 1.25
**Secondary Driver:** `Vendor Security Posture` with combined weight of 0.80

### Theoretical Premium Calculation (Tier 3 Standard)
> *Per the DSI Premium Calculation Methodology v2.0, the core formula is:*
> *P_final = (Base × Rate) × ILF_relativity × Deductible_Factor × Modifiers*

**1. The Pricing Anchor:** The Base Rate of `0.32%` on `revenue` purchases exactly a `$10,000,000` Limit with a `$50,000` Deductible.
**2. Theoretical Execution:**
  - Assume `revenue` = $10,000,000
  - Base Premium = $10,000,000 × 0.0032 = **$32,000**
  - If the client requests the Anchor Limit/Deductible, the factors are 1.00, resulting in a technical premium of **$32,000**.


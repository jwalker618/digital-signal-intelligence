# DSI Logic Document: `PI`
*Generated: 2026-03-29*

## DSI Foundational Principles Adherence
This configuration is validated against the DSI Whitepaper & Vision Paper:
- **Objective Observation:** Signals derived from verifiable digital footprints, avoiding subjective interpretation.
- **Three-Layer Engine:** Modifiers explicitly target Risk, Loss, and Exposure dimensions.
- **Phase 5 Anchoring:** Polymorphic pricing limits scale from mathematically absolute anchor points.

---

## Model: `pi_general`
*PI/E&O coverage for mid-market and enterprise firms*

### Routing Protocol (Multiplexer)
- `revenue > 50000000`

### Three-Layer Weight Distribution
> *DSI requires that weights for Risk, Loss, and Exposure each sum to 1.0 across all signal groups.*

**Validation:** PASS

| Group | Risk | Loss | Exposure |
|-------|------|------|----------|
| Network Authority | 0.15 | 0.10 | 0.05 |
| Regulatory Standing | 0.25 | 0.25 | 0.10 |
| Firm Stability | 0.15 | 0.15 | 0.20 |
| Practice Quality | 0.15 | 0.20 | 0.15 |
| Technical Infrastructure | 0.10 | 0.10 | 0.10 |
| Corporate Footprint | 0.10 | 0.05 | 0.25 |
| Litigation History | 0.10 | 0.15 | 0.15 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

### Signal Architecture Rationale
This configuration contains **44 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `DIRECT_OBSERVABLE` (25 signals): Highest confidence
- `INFERRED_PROXY` (18 signals): Medium confidence
- `COHORT_INFERENCE` (1 signals): Lowest confidence

**Signal Count by Group:**
- `regulatory_standing`: 7 signals
- `network_authority`: 6 signals
- `firm_stability`: 6 signals
- `corporate_footprint`: 6 signals
- `practice_quality`: 5 signals
- `technical_infrastructure`: 5 signals
- `litigation_history`: 5 signals
- `profession_type`: 1 signals
- `sub_profession_type`: 1 signals
- `firm_size`: 1 signals
- `revenue_size`: 1 signals

**Selection Rationale:**
- 57% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 | Regulatory Standing | 0.60 | 0.25 | 0.25 | 0.10 |
| 2 | Firm Stability | 0.50 | 0.15 | 0.15 | 0.20 |
| 3 | Practice Quality | 0.50 | 0.15 | 0.20 | 0.15 |
| 4 | Corporate Footprint | 0.40 | 0.10 | 0.05 | 0.25 |
| 5 | Litigation History | 0.40 | 0.10 | 0.15 | 0.15 |
| 6 | Network Authority | 0.30 | 0.15 | 0.10 | 0.05 |
| 7 | Technical Infrastructure | 0.30 | 0.10 | 0.10 | 0.10 |

**Primary Assessment Driver:** `Regulatory Standing` with combined weight of 0.60
**Secondary Driver:** `Firm Stability` with combined weight of 0.50

### Theoretical Premium Calculation (Tier 3 Standard)
> *Per the DSI Premium Calculation Methodology v2.0, the core formula is:*
> *P_final = (Base × Rate) × ILF_relativity × Deductible_Factor × Modifiers*

**1. The Pricing Anchor:** The Base Rate of `0.018000000000000002%` on `revenue` purchases exactly a `$1,000,000` Limit with a `$50,000` Deductible.
**2. Theoretical Execution:**
  - Assume `revenue` = $10,000,000
  - Base Premium = $10,000,000 × 0.00018 = **$1,800**
  - If the client requests the Anchor Limit/Deductible, the factors are 1.00, resulting in a technical premium of **$1,800**.

---

## Model: `pi_sme`
*PI/E&O coverage for small practices*

### Routing Protocol (Multiplexer)
- `revenue <= 50000000`

### Three-Layer Weight Distribution
> *DSI requires that weights for Risk, Loss, and Exposure each sum to 1.0 across all signal groups.*

**Validation:** FAIL - Weights do not sum to 1.0

| Group | Risk | Loss | Exposure |
|-------|------|------|----------|
| **TOTAL** | **0.00** | **0.00** | **0.00** |

### Signal Architecture Rationale
This configuration contains **1 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `INFERRED_PROXY` (1 signals): Medium confidence

**Signal Count by Group:**
- `profession_type`: 1 signals

**Selection Rationale:**
- 0% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|


### Theoretical Premium Calculation (Tier 3 Standard)
> *Per the DSI Premium Calculation Methodology v2.0, the core formula is:*
> *P_final = (Base × Rate) × ILF_relativity × Deductible_Factor × Modifiers*

**1. The Pricing Anchor:** The Base Rate of `130.0%` on `categorical` purchases exactly a `$1,000,000` Limit with a `$10,000` Deductible.
**2. Theoretical Execution:**
  - Assume `categorical` = $10,000,000
  - Base Premium = $10,000,000 × 1.3 = **$13,000,000**
  - If the client requests the Anchor Limit/Deductible, the factors are 1.00, resulting in a technical premium of **$13,000,000**.

---

## Model: `pi_legal_large`
*Top-tier corporate/commercial practices — AmLaw 200, Magic Circle*

### Routing Protocol (Multiplexer)
- `profession_segment == LEGAL`
- `revenue > 100000000`

### Three-Layer Weight Distribution
> *DSI requires that weights for Risk, Loss, and Exposure each sum to 1.0 across all signal groups.*

**Validation:** PASS

| Group | Risk | Loss | Exposure |
|-------|------|------|----------|
| Network Authority | 0.10 | 0.05 | 0.05 |
| Regulatory Standing | 0.20 | 0.20 | 0.10 |
| Firm Stability | 0.20 | 0.15 | 0.20 |
| Practice Quality | 0.15 | 0.20 | 0.10 |
| Technical Infrastructure | 0.10 | 0.10 | 0.10 |
| Corporate Footprint | 0.05 | 0.05 | 0.10 |
| Litigation History | 0.10 | 0.15 | 0.10 |
| Partner Practice Mix | 0.10 | 0.10 | 0.25 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

### Signal Architecture Rationale
This configuration contains **7 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `DIRECT_OBSERVABLE` (3 signals): Highest confidence
- `INFERRED_PROXY` (4 signals): Medium confidence

**Signal Count by Group:**
- `partner_practice_mix`: 7 signals

**Selection Rationale:**
- 43% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 | Firm Stability | 0.55 | 0.20 | 0.15 | 0.20 |
| 2 | Regulatory Standing | 0.50 | 0.20 | 0.20 | 0.10 |
| 3 | Practice Quality | 0.45 | 0.15 | 0.20 | 0.10 |
| 4 | Partner Practice Mix | 0.45 | 0.10 | 0.10 | 0.25 |
| 5 | Litigation History | 0.35 | 0.10 | 0.15 | 0.10 |
| 6 | Technical Infrastructure | 0.30 | 0.10 | 0.10 | 0.10 |
| 7 | Network Authority | 0.20 | 0.10 | 0.05 | 0.05 |
| 8 | Corporate Footprint | 0.20 | 0.05 | 0.05 | 0.10 |

**Primary Assessment Driver:** `Firm Stability` with combined weight of 0.55
**Secondary Driver:** `Regulatory Standing` with combined weight of 0.50

### Theoretical Premium Calculation (Tier 3 Standard)
> *Per the DSI Premium Calculation Methodology v2.0, the core formula is:*
> *P_final = (Base × Rate) × ILF_relativity × Deductible_Factor × Modifiers*

**1. The Pricing Anchor:** The Base Rate of `0.27999999999999997%` on `revenue` purchases exactly a `$5,000,000` Limit with a `$250,000` Deductible.
**2. Theoretical Execution:**
  - Assume `revenue` = $10,000,000
  - Base Premium = $10,000,000 × 0.0028 = **$28,000**
  - If the client requests the Anchor Limit/Deductible, the factors are 1.00, resulting in a technical premium of **$28,000**.

---

## Model: `pi_legal_specialist`
*Specialist and plaintiff law firms; niche practices*

### Routing Protocol (Multiplexer)
- `profession_segment == LEGAL`

### Three-Layer Weight Distribution
> *DSI requires that weights for Risk, Loss, and Exposure each sum to 1.0 across all signal groups.*

**Validation:** PASS

| Group | Risk | Loss | Exposure |
|-------|------|------|----------|
| Network Authority | 0.10 | 0.05 | 0.05 |
| Regulatory Standing | 0.25 | 0.20 | 0.10 |
| Firm Stability | 0.15 | 0.10 | 0.15 |
| Practice Quality | 0.15 | 0.25 | 0.10 |
| Technical Infrastructure | 0.05 | 0.05 | 0.05 |
| Corporate Footprint | 0.05 | 0.05 | 0.05 |
| Litigation History | 0.15 | 0.20 | 0.15 |
| Case Portfolio | 0.10 | 0.10 | 0.35 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

### Signal Architecture Rationale
This configuration contains **5 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `DIRECT_OBSERVABLE` (1 signals): Highest confidence
- `INFERRED_PROXY` (4 signals): Medium confidence

**Signal Count by Group:**
- `case_portfolio`: 5 signals

**Selection Rationale:**
- 20% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 | Regulatory Standing | 0.55 | 0.25 | 0.20 | 0.10 |
| 2 | Case Portfolio | 0.55 | 0.10 | 0.10 | 0.35 |
| 3 | Practice Quality | 0.50 | 0.15 | 0.25 | 0.10 |
| 4 | Litigation History | 0.50 | 0.15 | 0.20 | 0.15 |
| 5 | Firm Stability | 0.40 | 0.15 | 0.10 | 0.15 |
| 6 | Network Authority | 0.20 | 0.10 | 0.05 | 0.05 |
| 7 | Technical Infrastructure | 0.15 | 0.05 | 0.05 | 0.05 |
| 8 | Corporate Footprint | 0.15 | 0.05 | 0.05 | 0.05 |

**Primary Assessment Driver:** `Regulatory Standing` with combined weight of 0.55
**Secondary Driver:** `Case Portfolio` with combined weight of 0.55

### Theoretical Premium Calculation (Tier 3 Standard)
> *Per the DSI Premium Calculation Methodology v2.0, the core formula is:*
> *P_final = (Base × Rate) × ILF_relativity × Deductible_Factor × Modifiers*

**1. The Pricing Anchor:** The Base Rate of `0.32%` on `revenue` purchases exactly a `$1,000,000` Limit with a `$50,000` Deductible.
**2. Theoretical Execution:**
  - Assume `revenue` = $10,000,000
  - Base Premium = $10,000,000 × 0.0032 = **$32,000**
  - If the client requests the Anchor Limit/Deductible, the factors are 1.00, resulting in a technical premium of **$32,000**.

---

## Model: `pi_audit`
*Public company audit — Big 4 and mid-tier audit firms*

### Routing Protocol (Multiplexer)
- `profession_segment == ACCOUNTING`
- `sub_profession_type IN ['AUDIT_PUBLIC', 'AUDIT_PRIVATE']`

### Three-Layer Weight Distribution
> *DSI requires that weights for Risk, Loss, and Exposure each sum to 1.0 across all signal groups.*

**Validation:** PASS

| Group | Risk | Loss | Exposure |
|-------|------|------|----------|
| Network Authority | 0.05 | 0.05 | 0.05 |
| Regulatory Standing | 0.30 | 0.30 | 0.15 |
| Firm Stability | 0.10 | 0.10 | 0.10 |
| Practice Quality | 0.10 | 0.10 | 0.10 |
| Technical Infrastructure | 0.10 | 0.05 | 0.05 |
| Corporate Footprint | 0.05 | 0.05 | 0.05 |
| Litigation History | 0.10 | 0.15 | 0.10 |
| Audit Quality | 0.20 | 0.20 | 0.40 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

### Signal Architecture Rationale
This configuration contains **7 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `DIRECT_OBSERVABLE` (4 signals): Highest confidence
- `INFERRED_PROXY` (3 signals): Medium confidence

**Signal Count by Group:**
- `audit_quality`: 7 signals

**Selection Rationale:**
- 57% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 | Audit Quality | 0.80 | 0.20 | 0.20 | 0.40 |
| 2 | Regulatory Standing | 0.75 | 0.30 | 0.30 | 0.15 |
| 3 | Litigation History | 0.35 | 0.10 | 0.15 | 0.10 |
| 4 | Firm Stability | 0.30 | 0.10 | 0.10 | 0.10 |
| 5 | Practice Quality | 0.30 | 0.10 | 0.10 | 0.10 |
| 6 | Technical Infrastructure | 0.20 | 0.10 | 0.05 | 0.05 |
| 7 | Network Authority | 0.15 | 0.05 | 0.05 | 0.05 |
| 8 | Corporate Footprint | 0.15 | 0.05 | 0.05 | 0.05 |

**Primary Assessment Driver:** `Audit Quality` with combined weight of 0.80
**Secondary Driver:** `Regulatory Standing` with combined weight of 0.75

### Theoretical Premium Calculation (Tier 3 Standard)
> *Per the DSI Premium Calculation Methodology v2.0, the core formula is:*
> *P_final = (Base × Rate) × ILF_relativity × Deductible_Factor × Modifiers*

**1. The Pricing Anchor:** The Base Rate of `0.44999999999999996%` on `revenue` purchases exactly a `$10,000,000` Limit with a `$500,000` Deductible.
**2. Theoretical Execution:**
  - Assume `revenue` = $10,000,000
  - Base Premium = $10,000,000 × 0.0045 = **$45,000**
  - If the client requests the Anchor Limit/Deductible, the factors are 1.00, resulting in a technical premium of **$45,000**.

---

## Model: `pi_accounting`
*Non-audit accounting: tax advisory, bookkeeping, estate planning, forensic*

### Routing Protocol (Multiplexer)
- `profession_segment == ACCOUNTING`

### Three-Layer Weight Distribution
> *DSI requires that weights for Risk, Loss, and Exposure each sum to 1.0 across all signal groups.*

**Validation:** PASS

| Group | Risk | Loss | Exposure |
|-------|------|------|----------|
| Network Authority | 0.10 | 0.05 | 0.05 |
| Regulatory Standing | 0.25 | 0.25 | 0.10 |
| Firm Stability | 0.15 | 0.15 | 0.20 |
| Practice Quality | 0.20 | 0.20 | 0.20 |
| Technical Infrastructure | 0.10 | 0.10 | 0.10 |
| Corporate Footprint | 0.10 | 0.05 | 0.15 |
| Litigation History | 0.10 | 0.20 | 0.20 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

### Signal Architecture Rationale
This configuration contains **0 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**

**Signal Count by Group:**

**Selection Rationale:**
- 0% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 | Regulatory Standing | 0.60 | 0.25 | 0.25 | 0.10 |
| 2 | Practice Quality | 0.60 | 0.20 | 0.20 | 0.20 |
| 3 | Firm Stability | 0.50 | 0.15 | 0.15 | 0.20 |
| 4 | Litigation History | 0.50 | 0.10 | 0.20 | 0.20 |
| 5 | Technical Infrastructure | 0.30 | 0.10 | 0.10 | 0.10 |
| 6 | Corporate Footprint | 0.30 | 0.10 | 0.05 | 0.15 |
| 7 | Network Authority | 0.20 | 0.10 | 0.05 | 0.05 |

**Primary Assessment Driver:** `Regulatory Standing` with combined weight of 0.60
**Secondary Driver:** `Practice Quality` with combined weight of 0.60

### Theoretical Premium Calculation (Tier 3 Standard)
> *Per the DSI Premium Calculation Methodology v2.0, the core formula is:*
> *P_final = (Base × Rate) × ILF_relativity × Deductible_Factor × Modifiers*

**1. The Pricing Anchor:** The Base Rate of `0.22%` on `revenue` purchases exactly a `$1,000,000` Limit with a `$25,000` Deductible.
**2. Theoretical Execution:**
  - Assume `revenue` = $10,000,000
  - Base Premium = $10,000,000 × 0.0022 = **$22,000**
  - If the client requests the Anchor Limit/Deductible, the factors are 1.00, resulting in a technical premium of **$22,000**.

---

## Model: `pi_architecture`
*Architecture and landscape design practices*

### Routing Protocol (Multiplexer)
- `profession_segment == DESIGN_CONSTRUCTION`
- `sub_profession_type IN ['ARCHITECTURE', 'LANDSCAPE', 'INTERIOR_DESIGN']`

### Three-Layer Weight Distribution
> *DSI requires that weights for Risk, Loss, and Exposure each sum to 1.0 across all signal groups.*

**Validation:** PASS

| Group | Risk | Loss | Exposure |
|-------|------|------|----------|
| Network Authority | 0.10 | 0.05 | 0.05 |
| Regulatory Standing | 0.15 | 0.15 | 0.05 |
| Firm Stability | 0.15 | 0.10 | 0.15 |
| Practice Quality | 0.15 | 0.15 | 0.10 |
| Technical Infrastructure | 0.05 | 0.05 | 0.05 |
| Corporate Footprint | 0.05 | 0.05 | 0.05 |
| Litigation History | 0.10 | 0.15 | 0.10 |
| Design Quality | 0.25 | 0.30 | 0.45 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

### Signal Architecture Rationale
This configuration contains **6 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `DIRECT_OBSERVABLE` (4 signals): Highest confidence
- `INFERRED_PROXY` (2 signals): Medium confidence

**Signal Count by Group:**
- `design_quality`: 6 signals

**Selection Rationale:**
- 67% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 | Design Quality | 1.00 | 0.25 | 0.30 | 0.45 |
| 2 | Firm Stability | 0.40 | 0.15 | 0.10 | 0.15 |
| 3 | Practice Quality | 0.40 | 0.15 | 0.15 | 0.10 |
| 4 | Regulatory Standing | 0.35 | 0.15 | 0.15 | 0.05 |
| 5 | Litigation History | 0.35 | 0.10 | 0.15 | 0.10 |
| 6 | Network Authority | 0.20 | 0.10 | 0.05 | 0.05 |
| 7 | Technical Infrastructure | 0.15 | 0.05 | 0.05 | 0.05 |
| 8 | Corporate Footprint | 0.15 | 0.05 | 0.05 | 0.05 |

**Primary Assessment Driver:** `Design Quality` with combined weight of 1.00
**Secondary Driver:** `Firm Stability` with combined weight of 0.40

### Theoretical Premium Calculation (Tier 3 Standard)
> *Per the DSI Premium Calculation Methodology v2.0, the core formula is:*
> *P_final = (Base × Rate) × ILF_relativity × Deductible_Factor × Modifiers*

**1. The Pricing Anchor:** The Base Rate of `0.26%` on `revenue` purchases exactly a `$1,000,000` Limit with a `$25,000` Deductible.
**2. Theoretical Execution:**
  - Assume `revenue` = $10,000,000
  - Base Premium = $10,000,000 × 0.0026 = **$26,000**
  - If the client requests the Anchor Limit/Deductible, the factors are 1.00, resulting in a technical premium of **$26,000**.

---

## Model: `pi_engineering`
*Structural, civil, geotechnical, and related engineering practices*

### Routing Protocol (Multiplexer)
- `profession_segment == DESIGN_CONSTRUCTION`
- `sub_profession_type IN ['STRUCTURAL', 'GEOTECHNICAL', 'CIVIL', 'MECHANICAL', 'ELECTRICAL', 'ENVIRONMENTAL_ENG']`

### Three-Layer Weight Distribution
> *DSI requires that weights for Risk, Loss, and Exposure each sum to 1.0 across all signal groups.*

**Validation:** PASS

| Group | Risk | Loss | Exposure |
|-------|------|------|----------|
| Network Authority | 0.05 | 0.05 | 0.05 |
| Regulatory Standing | 0.20 | 0.15 | 0.05 |
| Firm Stability | 0.10 | 0.10 | 0.10 |
| Practice Quality | 0.10 | 0.10 | 0.10 |
| Technical Infrastructure | 0.05 | 0.05 | 0.05 |
| Corporate Footprint | 0.05 | 0.05 | 0.05 |
| Litigation History | 0.10 | 0.15 | 0.10 |
| Engineering Quality | 0.35 | 0.35 | 0.50 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

### Signal Architecture Rationale
This configuration contains **6 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `DIRECT_OBSERVABLE` (4 signals): Highest confidence
- `INFERRED_PROXY` (2 signals): Medium confidence

**Signal Count by Group:**
- `engineering_quality`: 6 signals

**Selection Rationale:**
- 67% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 | Engineering Quality | 1.20 | 0.35 | 0.35 | 0.50 |
| 2 | Regulatory Standing | 0.40 | 0.20 | 0.15 | 0.05 |
| 3 | Litigation History | 0.35 | 0.10 | 0.15 | 0.10 |
| 4 | Firm Stability | 0.30 | 0.10 | 0.10 | 0.10 |
| 5 | Practice Quality | 0.30 | 0.10 | 0.10 | 0.10 |
| 6 | Network Authority | 0.15 | 0.05 | 0.05 | 0.05 |
| 7 | Technical Infrastructure | 0.15 | 0.05 | 0.05 | 0.05 |
| 8 | Corporate Footprint | 0.15 | 0.05 | 0.05 | 0.05 |

**Primary Assessment Driver:** `Engineering Quality` with combined weight of 1.20
**Secondary Driver:** `Regulatory Standing` with combined weight of 0.40

### Theoretical Premium Calculation (Tier 3 Standard)
> *Per the DSI Premium Calculation Methodology v2.0, the core formula is:*
> *P_final = (Base × Rate) × ILF_relativity × Deductible_Factor × Modifiers*

**1. The Pricing Anchor:** The Base Rate of `0.32%` on `revenue` purchases exactly a `$2,000,000` Limit with a `$50,000` Deductible.
**2. Theoretical Execution:**
  - Assume `revenue` = $10,000,000
  - Base Premium = $10,000,000 × 0.0032 = **$32,000**
  - If the client requests the Anchor Limit/Deductible, the factors are 1.00, resulting in a technical premium of **$32,000**.

---

## Model: `pi_technology`
*IT consulting, systems integration, managed services*

### Routing Protocol (Multiplexer)
- `profession_segment == TECHNOLOGY`

### Three-Layer Weight Distribution
> *DSI requires that weights for Risk, Loss, and Exposure each sum to 1.0 across all signal groups.*

**Validation:** PASS

| Group | Risk | Loss | Exposure |
|-------|------|------|----------|
| Network Authority | 0.10 | 0.05 | 0.05 |
| Regulatory Standing | 0.15 | 0.10 | 0.05 |
| Firm Stability | 0.15 | 0.10 | 0.15 |
| Practice Quality | 0.15 | 0.15 | 0.10 |
| Technical Infrastructure | 0.15 | 0.20 | 0.15 |
| Corporate Footprint | 0.05 | 0.05 | 0.05 |
| Litigation History | 0.10 | 0.15 | 0.10 |
| Delivery Quality | 0.15 | 0.20 | 0.35 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

### Signal Architecture Rationale
This configuration contains **6 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `DIRECT_OBSERVABLE` (3 signals): Highest confidence
- `INFERRED_PROXY` (3 signals): Medium confidence

**Signal Count by Group:**
- `delivery_quality`: 6 signals

**Selection Rationale:**
- 50% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 | Delivery Quality | 0.70 | 0.15 | 0.20 | 0.35 |
| 2 | Technical Infrastructure | 0.50 | 0.15 | 0.20 | 0.15 |
| 3 | Firm Stability | 0.40 | 0.15 | 0.10 | 0.15 |
| 4 | Practice Quality | 0.40 | 0.15 | 0.15 | 0.10 |
| 5 | Litigation History | 0.35 | 0.10 | 0.15 | 0.10 |
| 6 | Regulatory Standing | 0.30 | 0.15 | 0.10 | 0.05 |
| 7 | Network Authority | 0.20 | 0.10 | 0.05 | 0.05 |
| 8 | Corporate Footprint | 0.15 | 0.05 | 0.05 | 0.05 |

**Primary Assessment Driver:** `Delivery Quality` with combined weight of 0.70
**Secondary Driver:** `Technical Infrastructure` with combined weight of 0.50

### Theoretical Premium Calculation (Tier 3 Standard)
> *Per the DSI Premium Calculation Methodology v2.0, the core formula is:*
> *P_final = (Base × Rate) × ILF_relativity × Deductible_Factor × Modifiers*

**1. The Pricing Anchor:** The Base Rate of `0.22%` on `revenue` purchases exactly a `$2,000,000` Limit with a `$50,000` Deductible.
**2. Theoretical Execution:**
  - Assume `revenue` = $10,000,000
  - Base Premium = $10,000,000 × 0.0022 = **$22,000**
  - If the client requests the Anchor Limit/Deductible, the factors are 1.00, resulting in a technical premium of **$22,000**.

---

## Model: `pi_financial_advisory`
*Wealth managers, IFAs, RIAs, pension consultants*

### Routing Protocol (Multiplexer)
- `profession_segment == FINANCIAL_ADVISORY`

### Three-Layer Weight Distribution
> *DSI requires that weights for Risk, Loss, and Exposure each sum to 1.0 across all signal groups.*

**Validation:** PASS

| Group | Risk | Loss | Exposure |
|-------|------|------|----------|
| Network Authority | 0.10 | 0.05 | 0.05 |
| Regulatory Standing | 0.25 | 0.25 | 0.15 |
| Firm Stability | 0.15 | 0.10 | 0.15 |
| Practice Quality | 0.15 | 0.20 | 0.10 |
| Technical Infrastructure | 0.10 | 0.10 | 0.10 |
| Corporate Footprint | 0.05 | 0.05 | 0.05 |
| Litigation History | 0.10 | 0.15 | 0.10 |
| Advisory Quality | 0.10 | 0.10 | 0.30 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

### Signal Architecture Rationale
This configuration contains **5 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `DIRECT_OBSERVABLE` (3 signals): Highest confidence
- `INFERRED_PROXY` (2 signals): Medium confidence

**Signal Count by Group:**
- `advisory_quality`: 5 signals

**Selection Rationale:**
- 60% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 | Regulatory Standing | 0.65 | 0.25 | 0.25 | 0.15 |
| 2 | Advisory Quality | 0.50 | 0.10 | 0.10 | 0.30 |
| 3 | Practice Quality | 0.45 | 0.15 | 0.20 | 0.10 |
| 4 | Firm Stability | 0.40 | 0.15 | 0.10 | 0.15 |
| 5 | Litigation History | 0.35 | 0.10 | 0.15 | 0.10 |
| 6 | Technical Infrastructure | 0.30 | 0.10 | 0.10 | 0.10 |
| 7 | Network Authority | 0.20 | 0.10 | 0.05 | 0.05 |
| 8 | Corporate Footprint | 0.15 | 0.05 | 0.05 | 0.05 |

**Primary Assessment Driver:** `Regulatory Standing` with combined weight of 0.65
**Secondary Driver:** `Advisory Quality` with combined weight of 0.50

### Theoretical Premium Calculation (Tier 3 Standard)
> *Per the DSI Premium Calculation Methodology v2.0, the core formula is:*
> *P_final = (Base × Rate) × ILF_relativity × Deductible_Factor × Modifiers*

**1. The Pricing Anchor:** The Base Rate of `0.27999999999999997%` on `revenue` purchases exactly a `$2,000,000` Limit with a `$50,000` Deductible.
**2. Theoretical Execution:**
  - Assume `revenue` = $10,000,000
  - Base Premium = $10,000,000 × 0.0028 = **$28,000**
  - If the client requests the Anchor Limit/Deductible, the factors are 1.00, resulting in a technical premium of **$28,000**.

---

## Model: `pi_management_consulting`
*Strategy and management consulting firms*

### Routing Protocol (Multiplexer)
- `profession_segment == MANAGEMENT_CONSULTING`

### Three-Layer Weight Distribution
> *DSI requires that weights for Risk, Loss, and Exposure each sum to 1.0 across all signal groups.*

**Validation:** PASS

| Group | Risk | Loss | Exposure |
|-------|------|------|----------|
| Network Authority | 0.15 | 0.10 | 0.10 |
| Regulatory Standing | 0.15 | 0.15 | 0.05 |
| Firm Stability | 0.20 | 0.15 | 0.20 |
| Practice Quality | 0.20 | 0.25 | 0.15 |
| Technical Infrastructure | 0.10 | 0.10 | 0.15 |
| Corporate Footprint | 0.10 | 0.10 | 0.20 |
| Litigation History | 0.10 | 0.15 | 0.15 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

### Signal Architecture Rationale
This configuration contains **0 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**

**Signal Count by Group:**

**Selection Rationale:**
- 0% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 | Practice Quality | 0.60 | 0.20 | 0.25 | 0.15 |
| 2 | Firm Stability | 0.55 | 0.20 | 0.15 | 0.20 |
| 3 | Corporate Footprint | 0.40 | 0.10 | 0.10 | 0.20 |
| 4 | Litigation History | 0.40 | 0.10 | 0.15 | 0.15 |
| 5 | Network Authority | 0.35 | 0.15 | 0.10 | 0.10 |
| 6 | Regulatory Standing | 0.35 | 0.15 | 0.15 | 0.05 |
| 7 | Technical Infrastructure | 0.35 | 0.10 | 0.10 | 0.15 |

**Primary Assessment Driver:** `Practice Quality` with combined weight of 0.60
**Secondary Driver:** `Firm Stability` with combined weight of 0.55

### Theoretical Premium Calculation (Tier 3 Standard)
> *Per the DSI Premium Calculation Methodology v2.0, the core formula is:*
> *P_final = (Base × Rate) × ILF_relativity × Deductible_Factor × Modifiers*

**1. The Pricing Anchor:** The Base Rate of `0.15%` on `revenue` purchases exactly a `$1,000,000` Limit with a `$50,000` Deductible.
**2. Theoretical Execution:**
  - Assume `revenue` = $10,000,000
  - Base Premium = $10,000,000 × 0.0015 = **$15,000**
  - If the client requests the Anchor Limit/Deductible, the factors are 1.00, resulting in a technical premium of **$15,000**.

---

## Model: `pi_real_estate`
*Property valuers, surveyors, estate agents, appraisers*

### Routing Protocol (Multiplexer)
- `profession_segment == REAL_ESTATE_VALUATION`

### Three-Layer Weight Distribution
> *DSI requires that weights for Risk, Loss, and Exposure each sum to 1.0 across all signal groups.*

**Validation:** PASS

| Group | Risk | Loss | Exposure |
|-------|------|------|----------|
| Network Authority | 0.10 | 0.05 | 0.05 |
| Regulatory Standing | 0.20 | 0.20 | 0.10 |
| Firm Stability | 0.15 | 0.10 | 0.15 |
| Practice Quality | 0.15 | 0.15 | 0.10 |
| Technical Infrastructure | 0.05 | 0.05 | 0.05 |
| Corporate Footprint | 0.05 | 0.05 | 0.05 |
| Litigation History | 0.10 | 0.15 | 0.10 |
| Valuation Quality | 0.20 | 0.25 | 0.40 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

### Signal Architecture Rationale
This configuration contains **5 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `DIRECT_OBSERVABLE` (3 signals): Highest confidence
- `INFERRED_PROXY` (2 signals): Medium confidence

**Signal Count by Group:**
- `valuation_quality`: 5 signals

**Selection Rationale:**
- 60% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 | Valuation Quality | 0.85 | 0.20 | 0.25 | 0.40 |
| 2 | Regulatory Standing | 0.50 | 0.20 | 0.20 | 0.10 |
| 3 | Firm Stability | 0.40 | 0.15 | 0.10 | 0.15 |
| 4 | Practice Quality | 0.40 | 0.15 | 0.15 | 0.10 |
| 5 | Litigation History | 0.35 | 0.10 | 0.15 | 0.10 |
| 6 | Network Authority | 0.20 | 0.10 | 0.05 | 0.05 |
| 7 | Technical Infrastructure | 0.15 | 0.05 | 0.05 | 0.05 |
| 8 | Corporate Footprint | 0.15 | 0.05 | 0.05 | 0.05 |

**Primary Assessment Driver:** `Valuation Quality` with combined weight of 0.85
**Secondary Driver:** `Regulatory Standing` with combined weight of 0.50

### Theoretical Premium Calculation (Tier 3 Standard)
> *Per the DSI Premium Calculation Methodology v2.0, the core formula is:*
> *P_final = (Base × Rate) × ILF_relativity × Deductible_Factor × Modifiers*

**1. The Pricing Anchor:** The Base Rate of `0.22%` on `revenue` purchases exactly a `$1,000,000` Limit with a `$25,000` Deductible.
**2. Theoretical Execution:**
  - Assume `revenue` = $10,000,000
  - Base Premium = $10,000,000 × 0.0022 = **$22,000**
  - If the client requests the Anchor Limit/Deductible, the factors are 1.00, resulting in a technical premium of **$22,000**.

---

## Model: `pi_environmental`
*Environmental consulting: EIA, contaminated land, remediation advisory*

### Routing Protocol (Multiplexer)
- `profession_segment == ENVIRONMENTAL`

### Three-Layer Weight Distribution
> *DSI requires that weights for Risk, Loss, and Exposure each sum to 1.0 across all signal groups.*

**Validation:** PASS

| Group | Risk | Loss | Exposure |
|-------|------|------|----------|
| Network Authority | 0.05 | 0.05 | 0.05 |
| Regulatory Standing | 0.20 | 0.20 | 0.10 |
| Firm Stability | 0.10 | 0.10 | 0.10 |
| Practice Quality | 0.10 | 0.10 | 0.10 |
| Technical Infrastructure | 0.05 | 0.05 | 0.05 |
| Corporate Footprint | 0.05 | 0.05 | 0.05 |
| Litigation History | 0.10 | 0.15 | 0.10 |
| Environmental Assessment Quality | 0.35 | 0.30 | 0.45 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

### Signal Architecture Rationale
This configuration contains **5 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `DIRECT_OBSERVABLE` (3 signals): Highest confidence
- `INFERRED_PROXY` (2 signals): Medium confidence

**Signal Count by Group:**
- `environmental_assessment_quality`: 5 signals

**Selection Rationale:**
- 60% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 | Environmental Assessment Quality | 1.10 | 0.35 | 0.30 | 0.45 |
| 2 | Regulatory Standing | 0.50 | 0.20 | 0.20 | 0.10 |
| 3 | Litigation History | 0.35 | 0.10 | 0.15 | 0.10 |
| 4 | Firm Stability | 0.30 | 0.10 | 0.10 | 0.10 |
| 5 | Practice Quality | 0.30 | 0.10 | 0.10 | 0.10 |
| 6 | Network Authority | 0.15 | 0.05 | 0.05 | 0.05 |
| 7 | Technical Infrastructure | 0.15 | 0.05 | 0.05 | 0.05 |
| 8 | Corporate Footprint | 0.15 | 0.05 | 0.05 | 0.05 |

**Primary Assessment Driver:** `Environmental Assessment Quality` with combined weight of 1.10
**Secondary Driver:** `Regulatory Standing` with combined weight of 0.50

### Theoretical Premium Calculation (Tier 3 Standard)
> *Per the DSI Premium Calculation Methodology v2.0, the core formula is:*
> *P_final = (Base × Rate) × ILF_relativity × Deductible_Factor × Modifiers*

**1. The Pricing Anchor:** The Base Rate of `0.3%` on `revenue` purchases exactly a `$2,000,000` Limit with a `$50,000` Deductible.
**2. Theoretical Execution:**
  - Assume `revenue` = $10,000,000
  - Base Premium = $10,000,000 × 0.003 = **$30,000**
  - If the client requests the Anchor Limit/Deductible, the factors are 1.00, resulting in a technical premium of **$30,000**.


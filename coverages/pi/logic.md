# DSI Logic Document: `PI`
*Generated: 2026-05-14*

## DSI Foundational Principles Adherence
This configuration is validated against the DSI Whitepaper & Vision Paper:
- **Objective Observation:** Signals derived from verifiable digital footprints, avoiding subjective interpretation.
- **Three-Layer Engine:** Modifiers explicitly target Risk, Loss, and Exposure dimensions.
- **Phase 5 Anchoring:** Polymorphic pricing limits scale from mathematically absolute anchor points.

## The Three-Layer Assessment Engine
Every DSI model scores a risk across three independent pillars before any premium is calculated. Each pillar answers a distinct underwriting question and enters the pricing formula at a different point:

- **Risk** — *How likely is this account to behave badly?* Signal evidence is aggregated into a quality score that maps to an underwriting action (approve / refer / decline) and selects the base rate applied to the exposure basis.
- **Loss** — *If a loss occurs, how often and how severe?* Scored separately into frequency and severity modifiers, letting the model distinguish attritional-loss accounts from low-frequency / high-severity ones.
- **Exposure** — *How much value is at stake?* Scales premium to the size of the insured object, independent of risk quality.

Within each pillar, signals are organised into groups (e.g. Construction Quality, Occupancy Risk). The weight tables show how much each group contributes to each pillar; the signal detail tables show how each individual signal informs them. Critically, a single signal can carry very different weight across the three pillars — highly predictive of loss severity, say, yet barely moving the exposure score.

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
| Regulatory Standing | 0.35 | 0.40 | 0.25 |
| Firm Stability | 0.15 | 0.15 | 0.20 |
| Practice Quality | 0.25 | 0.30 | 0.25 |
| Corporate Footprint | 0.10 | 0.05 | 0.25 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

**Group Definitions:**
- **Network Authority:** Peer recognition, client quality, professional relationships
- **Regulatory Standing:** License status, disciplinary history, certifications
- **Firm Stability:** Tenure, partner retention, financial health
- **Practice Quality:** Client reviews, outcomes, complaint history
- **Corporate Footprint:** Website quality, thought leadership, transparency

*Reading the table: a group's three weights are independent. The same group can be a dominant driver of one pillar and a minor input to another — e.g. a group may carry most of the Exposure weight while contributing little to Risk.*

### Signal Architecture Rationale
This configuration contains **44 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `DIRECT_OBSERVABLE` (25 signals): Highest confidence
- `INFERRED_PROXY` (18 signals): Medium confidence
- `COHORT_INFERENCE` (1 signals): Lowest confidence

**Signal Count by Group:**
- `public_record`: 12 signals
- `technical_infrastructure`: 10 signals
- `network_authority`: 6 signals
- `behavioural`: 6 signals
- `corporate_footprint`: 6 signals
- `profession_type`: 1 signals
- `sub_profession_type`: 1 signals
- `firm_size`: 1 signals
- `revenue_size`: 1 signals

**Selection Rationale:**
- 57% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Detail by Group
> *Each signal is an objectively observable data point. The weights show how strongly that signal informs each assessment pillar; correlation direction indicates whether a higher observed value increases (+) or decreases (-) the assessed exposure.*

#### Network Authority
*Peer recognition, client quality, professional relationships*

| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `peer_ranking` | COHORT_INFERENCE | 0.25 | 0.15 / 0.10 | 0.00 | + |
| `client_quality` | INFERRED_PROXY | 0.20 | 0.00 / 0.15 | 0.10 | + |
| `referral_network` | INFERRED_PROXY | 0.15 | 0.10 / 0.00 | 0.00 | + |
| `association_leadership` | DIRECT_OBSERVABLE | 0.15 | 0.00 / 0.00 | 0.00 | + |
| `thought_leadership` | INFERRED_PROXY | 0.15 | 0.00 / 0.00 | 0.00 | + |
| `panel_membership` | DIRECT_OBSERVABLE | 0.10 | 0.00 / 0.00 | 0.00 | + |

#### Regulatory Standing
*License status, disciplinary history, certifications*

| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `license_status` | DIRECT_OBSERVABLE | 0.25 | 0.20 / 0.15 | 0.00 | + |
| `disciplinary_history` | DIRECT_OBSERVABLE | 0.30 | 0.30 / 0.25 | 0.00 | + |
| `malpractice_record` | DIRECT_OBSERVABLE | 0.15 | 0.25 / 0.30 | 0.00 | + |
| `ce_compliance` | DIRECT_OBSERVABLE | 0.05 | 0.00 / 0.00 | 0.00 | + |
| `specialty_certification` | DIRECT_OBSERVABLE | 0.10 | 0.00 / 0.00 | 0.00 | + |
| `peer_review` | DIRECT_OBSERVABLE | 0.10 | 0.15 / 0.10 | 0.00 | + |
| `pcaob_standing` | DIRECT_OBSERVABLE | 0.05 | 0.10 / 0.15 | 0.00 | + |
| `malpractice_suits` | DIRECT_OBSERVABLE | 0.35 | 0.35 / 0.40 | 0.25 | + |
| `fee_disputes_litigation` | DIRECT_OBSERVABLE | 0.15 | 0.15 / 0.00 | 0.00 | + |
| `regulatory_enforcement` | DIRECT_OBSERVABLE | 0.25 | 0.25 / 0.30 | 0.00 | + |
| `civil_litigation` | DIRECT_OBSERVABLE | 0.15 | 0.15 / 0.10 | 0.00 | + |
| `bankruptcy` | DIRECT_OBSERVABLE | 0.10 | 0.00 / 0.20 | 0.00 | + |

#### Firm Stability
*Tenure, partner retention, financial health*

| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `tenure` | INFERRED_PROXY | 0.20 | 0.10 / 0.00 | 0.00 | + |
| `partner_stability` | INFERRED_PROXY | 0.25 | 0.15 / 0.00 | 0.10 | + |
| `staff_retention` | INFERRED_PROXY | 0.15 | 0.10 / 0.00 | 0.00 | + |
| `office_stability` | INFERRED_PROXY | 0.10 | 0.00 / 0.00 | 0.00 | + |
| `financial_stability` | INFERRED_PROXY | 0.20 | 0.00 / 0.15 | 0.00 | + |
| `succession_planning` | INFERRED_PROXY | 0.10 | 0.00 / 0.00 | 0.00 | + |

#### Practice Quality
*Client reviews, outcomes, complaint history*

| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `outcome_patterns` | INFERRED_PROXY | 0.20 | 0.15 / 0.10 | 0.00 | + |
| `client_reviews` | DIRECT_OBSERVABLE | 0.25 | 0.20 / 0.00 | 0.00 | + |
| `work_quality` | INFERRED_PROXY | 0.15 | 0.15 / 0.10 | 0.00 | + |
| `fee_dispute` | DIRECT_OBSERVABLE | 0.15 | 0.15 / 0.00 | 0.00 | + |
| `complaint_history` | DIRECT_OBSERVABLE | 0.25 | 0.25 / 0.15 | 0.00 | + |
| `tls_score` | DIRECT_OBSERVABLE | 0.25 | 0.15 / 0.10 | 0.00 | + |
| `email_auth` | DIRECT_OBSERVABLE | 0.25 | 0.20 / 0.00 | 0.00 | + |
| `security_headers` | DIRECT_OBSERVABLE | 0.15 | 0.10 / 0.00 | 0.00 | + |
| `portal_security` | DIRECT_OBSERVABLE | 0.15 | 0.15 / 0.10 | 0.00 | + |
| `breach_history` | DIRECT_OBSERVABLE | 0.20 | 0.30 / 0.25 | 0.00 | + |

#### Corporate Footprint
*Website quality, thought leadership, transparency*

| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `website_quality` | DIRECT_OBSERVABLE | 0.25 | 0.00 / 0.00 | 0.00 | + |
| `bio_completeness` | DIRECT_OBSERVABLE | 0.20 | 0.00 / 0.00 | 0.10 | + |
| `practice_clarity` | INFERRED_PROXY | 0.15 | 0.00 / 0.00 | 0.00 | + |
| `publications` | DIRECT_OBSERVABLE | 0.15 | 0.00 / 0.00 | 0.00 | + |
| `community_involvement` | INFERRED_PROXY | 0.15 | 0.00 / 0.00 | 0.00 | + |
| `diversity` | INFERRED_PROXY | 0.10 | 0.00 / 0.00 | 0.00 | + |

#### profession_type
**Categorical signal `profession_type`** — proxy tier: `INFERRED_PROXY`, source: `metadata.profession_type`

| Category | Label | Applied Factor |
|----------|-------|----------------|
| `ACCOUNTING_FIRM` | Accounting Firm | 1.4 |
| `LAW_FIRM` | Law Firm | 1.3 |
| `ENGINEERING` | Engineering | 1.25 |
| `FINANCIAL_PLANNING` | Financial Planning | 1.2 |
| `ARCHITECTURE` | Architecture | 1.15 |
| `IT_CONSULTING` | IT Consulting | 1.05 |
| `ENVIRONMENTAL_CONSULTING` | Environmental Consulting | 1.05 |
| `APPRAISAL_VALUATION` | Appraisal/Valuation | 1.0 |
| `INSURANCE_BROKER` | Insurance Broker | 1.0 |
| `HEALTHCARE_ADMIN` | Healthcare Administration | 0.9 |
| `MANAGEMENT_CONSULTING` | Management Consulting | 0.9 |
| `HR_CONSULTING` | HR Consulting | 0.85 |
| `REAL_ESTATE` | Real Estate | 0.85 |
| `OTHER` | Other Professional | 1.0 |

#### sub_profession_type
**Categorical signal `sub_profession_type`** — proxy tier: `INFERRED_PROXY`, source: `metadata.sub_profession_type`

| Category | Label | Applied Factor |
|----------|-------|----------------|
| `SECURITIES` | Securities Law | 1.4 |
| `CORPORATE_MA` | Corporate M&A | 1.25 |
| `TRUSTS_ESTATES` | Trusts & Estates | 1.2 |
| `ENVIRONMENTAL` | Environmental Law | 1.2 |
| `TAX` | Tax Law | 1.15 |
| `BANKRUPTCY` | Bankruptcy | 1.15 |
| `HEALTHCARE` | Healthcare Law | 1.15 |
| `INTELLECTUAL_PROPERTY` | Intellectual Property | 1.15 |
| `LITIGATION_PLAINTIFF` | Plaintiff Litigation | 1.15 |
| `PERSONAL_INJURY_PLAINTIFF` | PI Plaintiff | 1.3 |
| `REAL_ESTATE` | Real Estate Law | 1.1 |
| `EMPLOYMENT` | Employment Law | 1.1 |
| `INSURANCE_COVERAGE` | Insurance Coverage | 1.05 |
| `GENERAL_PRACTICE` | General Practice | 1.05 |
| `LITIGATION_GENERAL` | General Litigation | 1.0 |
| `PERSONAL_INJURY_DEFENSE` | PI Defense | 0.95 |
| `FAMILY` | Family Law | 0.9 |
| `CRIMINAL` | Criminal Defense | 0.85 |
| `AUDIT_PUBLIC` | Public Company Audit | 1.5 |
| `ADVISORY_VALUATION` | Valuation Advisory | 1.35 |
| `ADVISORY_MA` | M&A Advisory | 1.3 |
| `FORENSIC` | Forensic Accounting | 1.2 |
| `AUDIT_PRIVATE` | Private Company Audit | 1.25 |
| `TAX_ESTATE` | Estate Tax | 1.2 |
| `TAX_CORPORATE` | Corporate Tax | 1.1 |
| `GENERAL_PRACTICE` | General Practice | 1.0 |
| `TAX_INDIVIDUAL` | Individual Tax | 0.9 |
| `BOOKKEEPING` | Bookkeeping | 0.8 |
| `STRUCTURAL` | Structural Design | 1.35 |
| `HEALTHCARE_FACILITIES` | Healthcare Facilities | 1.25 |
| `HIGH_RISE` | High-Rise Construction | 1.2 |
| `COMMERCIAL` | Commercial | 1.1 |
| `INSTITUTIONAL` | Institutional | 1.05 |
| `RESIDENTIAL_MULTI` | Multi-Family Residential | 1.0 |
| `RESIDENTIAL_SINGLE` | Single-Family Residential | 0.9 |
| `INTERIOR_DESIGN` | Interior Design | 0.85 |
| `STRUCTURAL` | Structural Engineering | 1.4 |
| `GEOTECHNICAL` | Geotechnical Engineering | 1.35 |
| `ENVIRONMENTAL` | Environmental Engineering | 1.25 |
| `CIVIL` | Civil Engineering | 1.15 |
| `MECHANICAL` | Mechanical Engineering | 1.1 |
| `ELECTRICAL` | Electrical Engineering | 1.05 |
| `SURVEYING` | Surveying | 1.0 |
| `CONSULTING` | Consulting Only | 0.9 |
| `OTHER` | UNKNOWN | 1.0 |

#### firm_size
**Categorical signal `firm_size`** — proxy tier: `INFERRED_PROXY`, source: `metadata.firm_size`

| Category | Label | Applied Factor |
|----------|-------|----------------|
| `SOLO` | Solo Practitioner | 1.2 |
| `MICRO` | Micro Firm (2 - 5) | 1.1 |
| `SMALL` | Small Firm (6 - 20) | 1.0 |
| `MEDIUM` | Medium Firm (21 - 100) | 0.95 |
| `LARGE` | Large Firm (101 - 500) | 0.9 |
| `MAJOR` | Major Firm (500+) | 0.85 |
| `OTHER` | UNKNOWN | 1.0 |

#### revenue_size
**Categorical signal `revenue_size`** — proxy tier: `INFERRED_PROXY`, source: `metadata.revenue_size`

| Category | Label | Applied Factor |
|----------|-------|----------------|
| `UNDER_500K` | Under $500K | 0.85 |
| `R_500K_1M` | $500K - $1M | 0.9 |
| `R_1M_5M` | $1M - $5M | 1.0 |
| `R_5M_25M` | $5M - $25M | 1.1 |
| `R_25M_100M` | $25M - $100M | 1.25 |
| `R_100M_500M` | $100M - $500M | 1.4 |
| `OVER_500M` | Over $500M | 1.6 |
| `OTHER` | UNKNOWN" | 1.0 |

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 | Regulatory Standing | 1.00 | 0.35 | 0.40 | 0.25 |
| 2 | Practice Quality | 0.80 | 0.25 | 0.30 | 0.25 |
| 3 | Firm Stability | 0.50 | 0.15 | 0.15 | 0.20 |
| 4 | Corporate Footprint | 0.40 | 0.10 | 0.05 | 0.25 |
| 5 | Network Authority | 0.30 | 0.15 | 0.10 | 0.05 |

**Primary Assessment Driver:** `Regulatory Standing` with combined weight of 1.00
**Secondary Driver:** `Practice Quality` with combined weight of 0.80

### Three-Layer Pricing Translation
> *How each pillar's tier score becomes a concrete underwriting action or pricing modifier. This is the bridge between signal observation and premium.*

**Risk -> Underwriting Action & Base Rate**

| Tier | Score Band | Action | Rate / Method |
|------|-----------|--------|---------------|
| PREFERRED | 800-1000 | APPROVE | 0.008% (MULTIPLIER) |
| STANDARD_PLUS | 650-799 | APPROVE | 0.012% (MULTIPLIER) |
| STANDARD | 500-649 | REFER | 0.018% (MULTIPLIER) |
| SUBSTANDARD | 350-499 | REFER | 0.028% (MULTIPLIER) |
| DECLINE | 0-349 | DECLINE | 0.045% (MULTIPLIER) |

**Loss -> Frequency & Severity Modifiers**

| Tier | Score Band | Frequency Modifier | Severity Modifier |
|------|-----------|--------------------|-------------------|
| VERY_LOW | 80-100 | 0.7 | 0.8 |
| LOW | 60-79 | 0.85 | 0.9 |
| MODERATE | 40-59 | 1.0 | 1.0 |
| ELEVATED | 20-39 | 1.15 | 1.15 |
| HIGH | 0-19 | 1.35 | 1.4 |

*Loss modifier is bounded: floor 0.55, cap 1.6.*

**Exposure (size) -> Scale Modifier**

| Band | Score Band | Modifier | Implied Value Range |
|------|-----------|----------|---------------------|
| MEDIUM | 0-33 | 1.0 | n/a |
| LARGE | 34-66 | 1.15 | n/a |
| VERY_LARGE | 67-100 | 1.35 | n/a |

**Exposure (complexity) -> Scale Modifier**

| Band | Score Band | Modifier | Implied Value Range |
|------|-----------|----------|---------------------|
| SIMPLE | 0-40 | 0.95 | n/a |
| COMPLEX | 41-75 | 1.1 | n/a |
| HIGHLY_COMPLEX | 76-100 | 1.3 | n/a |

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

**Validation:** PASS

| Group | Risk | Loss | Exposure |
|-------|------|------|----------|
| Network Authority | 0.15 | 0.10 | 0.05 |
| Regulatory Standing | 0.35 | 0.40 | 0.25 |
| Firm Stability | 0.15 | 0.15 | 0.20 |
| Practice Quality | 0.25 | 0.30 | 0.25 |
| Corporate Footprint | 0.10 | 0.05 | 0.25 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

**Group Definitions:**
- **Network Authority:** Peer recognition, client quality, professional relationships
- **Regulatory Standing:** License status, disciplinary history, certifications
- **Firm Stability:** Tenure, partner retention, financial health
- **Practice Quality:** Client reviews, outcomes, complaint history
- **Corporate Footprint:** Website quality, thought leadership, transparency

*Reading the table: a group's three weights are independent. The same group can be a dominant driver of one pillar and a minor input to another — e.g. a group may carry most of the Exposure weight while contributing little to Risk.*

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

### Signal Detail by Group
> *Each signal is an objectively observable data point. The weights show how strongly that signal informs each assessment pillar; correlation direction indicates whether a higher observed value increases (+) or decreases (-) the assessed exposure.*

#### profession_type
**Categorical signal `profession_type`** — proxy tier: `INFERRED_PROXY`, source: `metadata.profession_type`

| Category | Label | Applied Factor |
|----------|-------|----------------|
| `LAW_FIRM` | Law Firm |  |
| `ACCOUNTING_FIRM` | Accounting Firm |  |
| `ARCHITECTURE` | Architecture |  |
| `ENGINEERING` | Engineering |  |
| `MANAGEMENT_CONSULTING` | Management Consulting |  |
| `IT_CONSULTING` | IT Consulting |  |
| `HR_CONSULTING` | HR Consulting |  |
| `REAL_ESTATE` | Real Estate |  |
| `INSURANCE_BROKER` | Insurance Broker |  |
| `FINANCIAL_PLANNING` | Financial Planning |  |
| `HEALTHCARE_ADMIN` | Healthcare Administration |  |
| `APPRAISAL_VALUATION` | Appraisal/Valuation |  |
| `ENVIRONMENTAL_CONSULTING` | Environmental Consulting |  |
| `OTHER` | Other Professional |  |

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 | Regulatory Standing | 1.00 | 0.35 | 0.40 | 0.25 |
| 2 | Practice Quality | 0.80 | 0.25 | 0.30 | 0.25 |
| 3 | Firm Stability | 0.50 | 0.15 | 0.15 | 0.20 |
| 4 | Corporate Footprint | 0.40 | 0.10 | 0.05 | 0.25 |
| 5 | Network Authority | 0.30 | 0.15 | 0.10 | 0.05 |

**Primary Assessment Driver:** `Regulatory Standing` with combined weight of 1.00
**Secondary Driver:** `Practice Quality` with combined weight of 0.80

### Three-Layer Pricing Translation
> *How each pillar's tier score becomes a concrete underwriting action or pricing modifier. This is the bridge between signal observation and premium.*

**Risk -> Underwriting Action & Base Rate**

| Tier | Score Band | Action | Rate / Method |
|------|-----------|--------|---------------|
| PREFERRED | 800-1000 | APPROVE | 75% (MULTIPLIER) |
| STANDARD_PLUS | 650-799 | APPROVE | 100% (MULTIPLIER) |
| STANDARD | 500-649 | REFER | 130% (MULTIPLIER) |
| SUBSTANDARD | 350-499 | REFER | 175% (MULTIPLIER) |
| DECLINE | 0-349 | DECLINE | 250% (MULTIPLIER) |

**Loss -> Frequency & Severity Modifiers**

| Tier | Score Band | Frequency Modifier | Severity Modifier |
|------|-----------|--------------------|-------------------|
| VERY_LOW | 80-100 | 0.7 | 0.8 |
| LOW | 60-79 | 0.85 | 0.9 |
| MODERATE | 40-59 | 1.0 | 1.0 |
| ELEVATED | 20-39 | 1.15 | 1.15 |
| HIGH | 0-19 | 1.35 | 1.4 |

*Loss modifier is bounded: floor 0.55, cap 1.6.*

**Exposure (size) -> Scale Modifier**

| Band | Score Band | Modifier | Implied Value Range |
|------|-----------|----------|---------------------|
| MICRO | 0-33 | 0.75 | n/a |
| SMALL | 34-66 | 1.0 | n/a |
| MEDIUM | 67-100 | 1.25 | n/a |

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
| Regulatory Standing | 0.30 | 0.35 | 0.20 |
| Firm Stability | 0.20 | 0.15 | 0.20 |
| Practice Quality | 0.25 | 0.30 | 0.20 |
| Corporate Footprint | 0.15 | 0.15 | 0.35 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

*Reading the table: a group's three weights are independent. The same group can be a dominant driver of one pillar and a minor input to another — e.g. a group may carry most of the Exposure weight while contributing little to Risk.*

### Signal Architecture Rationale
This configuration contains **7 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `DIRECT_OBSERVABLE` (3 signals): Highest confidence
- `INFERRED_PROXY` (4 signals): Medium confidence

**Signal Count by Group:**
- `corporate_footprint`: 7 signals

**Selection Rationale:**
- 43% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Detail by Group
> *Each signal is an objectively observable data point. The weights show how strongly that signal informs each assessment pillar; correlation direction indicates whether a higher observed value increases (+) or decreases (-) the assessed exposure.*

#### Corporate Footprint
| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `lateral_hire_volume` | INFERRED_PROXY | 0.15 | 0.15 / 0.00 | 0.15 | + |
| `prior_acts_coverage` | DIRECT_OBSERVABLE | 0.20 | 0.00 / 0.20 | 0.20 | + |
| `conflict_system_quality` | INFERRED_PROXY | 0.20 | 0.20 / 0.00 | 0.15 | + |
| `trust_account_compliance` | DIRECT_OBSERVABLE | 0.15 | 0.10 / 0.00 | 0.00 | + |
| `class_action_exposure` | INFERRED_PROXY | 0.10 | 0.00 / 0.15 | 0.25 | + |
| `partner_departure_rate` | DIRECT_OBSERVABLE | 0.10 | 0.10 / 0.00 | 0.15 | + |
| `matter_concentration` | INFERRED_PROXY | 0.10 | 0.00 / 0.10 | 0.25 | + |

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 | Regulatory Standing | 0.85 | 0.30 | 0.35 | 0.20 |
| 2 | Practice Quality | 0.75 | 0.25 | 0.30 | 0.20 |
| 3 | Corporate Footprint | 0.65 | 0.15 | 0.15 | 0.35 |
| 4 | Firm Stability | 0.55 | 0.20 | 0.15 | 0.20 |
| 5 | Network Authority | 0.20 | 0.10 | 0.05 | 0.05 |

**Primary Assessment Driver:** `Regulatory Standing` with combined weight of 0.85
**Secondary Driver:** `Practice Quality` with combined weight of 0.75

### Three-Layer Pricing Translation
> *How each pillar's tier score becomes a concrete underwriting action or pricing modifier. This is the bridge between signal observation and premium.*

**Risk -> Underwriting Action & Base Rate**

| Tier | Score Band | Action | Rate / Method |
|------|-----------|--------|---------------|
| PREFERRED | 800-1000 | APPROVE | 0.12% (MULTIPLIER) |
| STANDARD_PLUS | 650-799 | APPROVE | 0.18% (MULTIPLIER) |
| STANDARD | 500-649 | REFER | 0.28% (MULTIPLIER) |
| SUBSTANDARD | 350-499 | REFER | 0.42% (MULTIPLIER) |
| DECLINE | 0-349 | DECLINE | 0.65% (MULTIPLIER) |

**Loss -> Frequency & Severity Modifiers**

| Tier | Score Band | Frequency Modifier | Severity Modifier |
|------|-----------|--------------------|-------------------|
| VERY_LOW | 80-100 | 0.7 | 0.8 |
| LOW | 60-79 | 0.85 | 0.9 |
| MODERATE | 40-59 | 1.0 | 1.0 |
| ELEVATED | 20-39 | 1.15 | 1.15 |
| HIGH | 0-19 | 1.35 | 1.4 |

*Loss modifier is bounded: floor 0.55, cap 1.6.*

**Exposure (size) -> Scale Modifier**

| Band | Score Band | Modifier | Implied Value Range |
|------|-----------|----------|---------------------|
| MICRO | 0-20 | 0.5 | $0 - $1,000,000 |
| SMALL | 21-40 | 0.75 | $1,000,000 - $10,000,000 |
| MEDIUM | 41-60 | 1.0 | $10,000,000 - $50,000,000 |
| LARGE | 61-80 | 1.5 | $50,000,000 - $250,000,000 |
| VERY_LARGE | 81-100 | 2.5 | $250,000,000 - $1,000,000,000 |

**Exposure (complexity) -> Scale Modifier**

| Band | Score Band | Modifier | Implied Value Range |
|------|-----------|----------|---------------------|
| SIMPLE | 0-20 | 0.85 | n/a |
| MODERATE | 21-40 | 0.95 | n/a |
| COMPLEX | 41-60 | 1.1 | n/a |
| HIGHLY_COMPLEX | 61-80 | 1.3 | n/a |
| EXTREMELY_COMPLEX | 81-100 | 1.6 | n/a |

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
| Regulatory Standing | 0.50 | 0.50 | 0.60 |
| Firm Stability | 0.15 | 0.10 | 0.15 |
| Practice Quality | 0.20 | 0.30 | 0.15 |
| Corporate Footprint | 0.05 | 0.05 | 0.05 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

*Reading the table: a group's three weights are independent. The same group can be a dominant driver of one pillar and a minor input to another — e.g. a group may carry most of the Exposure weight while contributing little to Risk.*

### Signal Architecture Rationale
This configuration contains **8 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `DIRECT_OBSERVABLE` (3 signals): Highest confidence
- `INFERRED_PROXY` (5 signals): Medium confidence

**Signal Count by Group:**
- `public_record`: 8 signals

**Selection Rationale:**
- 38% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Detail by Group
> *Each signal is an objectively observable data point. The weights show how strongly that signal informs each assessment pillar; correlation direction indicates whether a higher observed value increases (+) or decreases (-) the assessed exposure.*

#### Regulatory Standing
| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `case_concentration` | INFERRED_PROXY | 0.20 | 0.00 / 0.20 | 0.30 | + |
| `contingency_fee_ratio` | DIRECT_OBSERVABLE | 0.20 | 0.25 / 0.00 | 0.20 | + |
| `trial_success_rate` | INFERRED_PROXY | 0.20 | 0.20 / 0.00 | 0.15 | + |
| `statute_tracking_compliance` | INFERRED_PROXY | 0.25 | 0.25 / 0.00 | 0.15 | + |
| `case_value_distribution` | INFERRED_PROXY | 0.15 | 0.00 / 0.10 | 0.20 | + |
| `irb_registration` | DIRECT_OBSERVABLE | 0.03 | 0.00 / 0.03 | 0.00 | - |
| `clinical_trial_registry_compliance` | DIRECT_OBSERVABLE | 0.03 | 0.03 / 0.00 | 0.00 | - |
| `good_clinical_practice_score` | INFERRED_PROXY | 0.03 | 0.03 / 0.00 | 0.00 | - |

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 | Regulatory Standing | 1.60 | 0.50 | 0.50 | 0.60 |
| 2 | Practice Quality | 0.65 | 0.20 | 0.30 | 0.15 |
| 3 | Firm Stability | 0.40 | 0.15 | 0.10 | 0.15 |
| 4 | Network Authority | 0.20 | 0.10 | 0.05 | 0.05 |
| 5 | Corporate Footprint | 0.15 | 0.05 | 0.05 | 0.05 |

**Primary Assessment Driver:** `Regulatory Standing` with combined weight of 1.60
**Secondary Driver:** `Practice Quality` with combined weight of 0.65

### Three-Layer Pricing Translation
> *How each pillar's tier score becomes a concrete underwriting action or pricing modifier. This is the bridge between signal observation and premium.*

**Risk -> Underwriting Action & Base Rate**

| Tier | Score Band | Action | Rate / Method |
|------|-----------|--------|---------------|
| PREFERRED | 800-1000 | APPROVE | 0.15% (MULTIPLIER) |
| STANDARD_PLUS | 650-799 | APPROVE | 0.22% (MULTIPLIER) |
| STANDARD | 500-649 | REFER | 0.32% (MULTIPLIER) |
| SUBSTANDARD | 350-499 | REFER | 0.48% (MULTIPLIER) |
| DECLINE | 0-349 | DECLINE | 0.75% (MULTIPLIER) |

**Loss -> Frequency & Severity Modifiers**

| Tier | Score Band | Frequency Modifier | Severity Modifier |
|------|-----------|--------------------|-------------------|
| VERY_LOW | 80-100 | 0.7 | 0.8 |
| LOW | 60-79 | 0.85 | 0.9 |
| MODERATE | 40-59 | 1.0 | 1.0 |
| ELEVATED | 20-39 | 1.15 | 1.15 |
| HIGH | 0-19 | 1.35 | 1.4 |

*Loss modifier is bounded: floor 0.55, cap 1.6.*

**Exposure (size) -> Scale Modifier**

| Band | Score Band | Modifier | Implied Value Range |
|------|-----------|----------|---------------------|
| MICRO | 0-20 | 0.5 | $0 - $1,000,000 |
| SMALL | 21-40 | 0.75 | $1,000,000 - $10,000,000 |
| MEDIUM | 41-60 | 1.0 | $10,000,000 - $50,000,000 |
| LARGE | 61-80 | 1.5 | $50,000,000 - $250,000,000 |
| VERY_LARGE | 81-100 | 2.5 | $250,000,000 - $1,000,000,000 |

**Exposure (complexity) -> Scale Modifier**

| Band | Score Band | Modifier | Implied Value Range |
|------|-----------|----------|---------------------|
| SIMPLE | 0-20 | 0.85 | n/a |
| MODERATE | 21-40 | 0.95 | n/a |
| COMPLEX | 41-60 | 1.1 | n/a |
| HIGHLY_COMPLEX | 61-80 | 1.3 | n/a |
| EXTREMELY_COMPLEX | 81-100 | 1.6 | n/a |

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
- `sub_profession_type in ['AUDIT_PUBLIC', 'AUDIT_PRIVATE']`

### Three-Layer Weight Distribution
> *DSI requires that weights for Risk, Loss, and Exposure each sum to 1.0 across all signal groups.*

**Validation:** PASS

| Group | Risk | Loss | Exposure |
|-------|------|------|----------|
| Network Authority | 0.05 | 0.05 | 0.05 |
| Regulatory Standing | 0.40 | 0.45 | 0.25 |
| Firm Stability | 0.10 | 0.10 | 0.10 |
| Practice Quality | 0.40 | 0.35 | 0.55 |
| Corporate Footprint | 0.05 | 0.05 | 0.05 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

*Reading the table: a group's three weights are independent. The same group can be a dominant driver of one pillar and a minor input to another — e.g. a group may carry most of the Exposure weight while contributing little to Risk.*

### Signal Architecture Rationale
This configuration contains **7 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `DIRECT_OBSERVABLE` (4 signals): Highest confidence
- `INFERRED_PROXY` (3 signals): Medium confidence

**Signal Count by Group:**
- `technical_infrastructure`: 7 signals

**Selection Rationale:**
- 57% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Detail by Group
> *Each signal is an objectively observable data point. The weights show how strongly that signal informs each assessment pillar; correlation direction indicates whether a higher observed value increases (+) or decreases (-) the assessed exposure.*

#### Practice Quality
| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `pcaob_inspection_deficiency_rate` | DIRECT_OBSERVABLE | 0.25 | 0.20 / 0.00 | 0.20 | + |
| `restatement_rate` | DIRECT_OBSERVABLE | 0.20 | 0.00 / 0.25 | 0.20 | + |
| `going_concern_accuracy` | INFERRED_PROXY | 0.15 | 0.15 / 0.00 | 0.10 | + |
| `sec_enforcement_exposure` | DIRECT_OBSERVABLE | 0.15 | 0.00 / 0.20 | 0.15 | + |
| `audit_client_concentration` | INFERRED_PROXY | 0.10 | 0.00 / 0.10 | 0.25 | + |
| `audit_partner_rotation_compliance` | DIRECT_OBSERVABLE | 0.10 | 0.10 / 0.00 | 0.00 | + |
| `securities_litigation_exposure` | INFERRED_PROXY | 0.05 | 0.00 / 0.15 | 0.20 | + |

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 | Practice Quality | 1.30 | 0.40 | 0.35 | 0.55 |
| 2 | Regulatory Standing | 1.10 | 0.40 | 0.45 | 0.25 |
| 3 | Firm Stability | 0.30 | 0.10 | 0.10 | 0.10 |
| 4 | Network Authority | 0.15 | 0.05 | 0.05 | 0.05 |
| 5 | Corporate Footprint | 0.15 | 0.05 | 0.05 | 0.05 |

**Primary Assessment Driver:** `Practice Quality` with combined weight of 1.30
**Secondary Driver:** `Regulatory Standing` with combined weight of 1.10

### Three-Layer Pricing Translation
> *How each pillar's tier score becomes a concrete underwriting action or pricing modifier. This is the bridge between signal observation and premium.*

**Risk -> Underwriting Action & Base Rate**

| Tier | Score Band | Action | Rate / Method |
|------|-----------|--------|---------------|
| PREFERRED | 800-1000 | APPROVE | 0.2% (MULTIPLIER) |
| STANDARD_PLUS | 650-799 | APPROVE | 0.3% (MULTIPLIER) |
| STANDARD | 500-649 | REFER | 0.45% (MULTIPLIER) |
| SUBSTANDARD | 350-499 | REFER | 0.7% (MULTIPLIER) |
| DECLINE | 0-349 | DECLINE | 1.1% (MULTIPLIER) |

**Loss -> Frequency & Severity Modifiers**

| Tier | Score Band | Frequency Modifier | Severity Modifier |
|------|-----------|--------------------|-------------------|
| VERY_LOW | 80-100 | 0.7 | 0.8 |
| LOW | 60-79 | 0.85 | 0.9 |
| MODERATE | 40-59 | 1.0 | 1.0 |
| ELEVATED | 20-39 | 1.15 | 1.15 |
| HIGH | 0-19 | 1.35 | 1.4 |

*Loss modifier is bounded: floor 0.55, cap 1.6.*

**Exposure (size) -> Scale Modifier**

| Band | Score Band | Modifier | Implied Value Range |
|------|-----------|----------|---------------------|
| MICRO | 0-20 | 0.5 | $0 - $1,000,000 |
| SMALL | 21-40 | 0.75 | $1,000,000 - $10,000,000 |
| MEDIUM | 41-60 | 1.0 | $10,000,000 - $50,000,000 |
| LARGE | 61-80 | 1.5 | $50,000,000 - $250,000,000 |
| VERY_LARGE | 81-100 | 2.5 | $250,000,000 - $1,000,000,000 |

**Exposure (complexity) -> Scale Modifier**

| Band | Score Band | Modifier | Implied Value Range |
|------|-----------|----------|---------------------|
| SIMPLE | 0-20 | 0.85 | n/a |
| MODERATE | 21-40 | 0.95 | n/a |
| COMPLEX | 41-60 | 1.1 | n/a |
| HIGHLY_COMPLEX | 61-80 | 1.3 | n/a |
| EXTREMELY_COMPLEX | 81-100 | 1.6 | n/a |

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
| Regulatory Standing | 0.35 | 0.45 | 0.30 |
| Firm Stability | 0.15 | 0.15 | 0.20 |
| Practice Quality | 0.30 | 0.30 | 0.30 |
| Corporate Footprint | 0.10 | 0.05 | 0.15 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

*Reading the table: a group's three weights are independent. The same group can be a dominant driver of one pillar and a minor input to another — e.g. a group may carry most of the Exposure weight while contributing little to Risk.*

### Signal Architecture Rationale
This configuration contains **0 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**

**Signal Count by Group:**

**Selection Rationale:**
- 0% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Detail by Group
> *Each signal is an objectively observable data point. The weights show how strongly that signal informs each assessment pillar; correlation direction indicates whether a higher observed value increases (+) or decreases (-) the assessed exposure.*

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 | Regulatory Standing | 1.10 | 0.35 | 0.45 | 0.30 |
| 2 | Practice Quality | 0.90 | 0.30 | 0.30 | 0.30 |
| 3 | Firm Stability | 0.50 | 0.15 | 0.15 | 0.20 |
| 4 | Corporate Footprint | 0.30 | 0.10 | 0.05 | 0.15 |
| 5 | Network Authority | 0.20 | 0.10 | 0.05 | 0.05 |

**Primary Assessment Driver:** `Regulatory Standing` with combined weight of 1.10
**Secondary Driver:** `Practice Quality` with combined weight of 0.90

### Three-Layer Pricing Translation
> *How each pillar's tier score becomes a concrete underwriting action or pricing modifier. This is the bridge between signal observation and premium.*

**Risk -> Underwriting Action & Base Rate**

| Tier | Score Band | Action | Rate / Method |
|------|-----------|--------|---------------|
| PREFERRED | 800-1000 | APPROVE | 0.1% (MULTIPLIER) |
| STANDARD_PLUS | 650-799 | APPROVE | 0.15% (MULTIPLIER) |
| STANDARD | 500-649 | REFER | 0.22% (MULTIPLIER) |
| SUBSTANDARD | 350-499 | REFER | 0.35% (MULTIPLIER) |
| DECLINE | 0-349 | DECLINE | 0.55% (MULTIPLIER) |

**Loss -> Frequency & Severity Modifiers**

| Tier | Score Band | Frequency Modifier | Severity Modifier |
|------|-----------|--------------------|-------------------|
| VERY_LOW | 80-100 | 0.7 | 0.8 |
| LOW | 60-79 | 0.85 | 0.9 |
| MODERATE | 40-59 | 1.0 | 1.0 |
| ELEVATED | 20-39 | 1.15 | 1.15 |
| HIGH | 0-19 | 1.35 | 1.4 |

*Loss modifier is bounded: floor 0.55, cap 1.6.*

**Exposure (size) -> Scale Modifier**

| Band | Score Band | Modifier | Implied Value Range |
|------|-----------|----------|---------------------|
| MICRO | 0-20 | 0.5 | $0 - $1,000,000 |
| SMALL | 21-40 | 0.75 | $1,000,000 - $10,000,000 |
| MEDIUM | 41-60 | 1.0 | $10,000,000 - $50,000,000 |
| LARGE | 61-80 | 1.5 | $50,000,000 - $250,000,000 |
| VERY_LARGE | 81-100 | 2.5 | $250,000,000 - $1,000,000,000 |

**Exposure (complexity) -> Scale Modifier**

| Band | Score Band | Modifier | Implied Value Range |
|------|-----------|----------|---------------------|
| SIMPLE | 0-20 | 0.85 | n/a |
| MODERATE | 21-40 | 0.95 | n/a |
| COMPLEX | 41-60 | 1.1 | n/a |
| HIGHLY_COMPLEX | 61-80 | 1.3 | n/a |
| EXTREMELY_COMPLEX | 81-100 | 1.6 | n/a |

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
- `sub_profession_type in ['ARCHITECTURE', 'LANDSCAPE', 'INTERIOR_DESIGN']`

### Three-Layer Weight Distribution
> *DSI requires that weights for Risk, Loss, and Exposure each sum to 1.0 across all signal groups.*

**Validation:** PASS

| Group | Risk | Loss | Exposure |
|-------|------|------|----------|
| Network Authority | 0.10 | 0.05 | 0.05 |
| Regulatory Standing | 0.25 | 0.30 | 0.15 |
| Firm Stability | 0.15 | 0.10 | 0.15 |
| Practice Quality | 0.45 | 0.50 | 0.60 |
| Corporate Footprint | 0.05 | 0.05 | 0.05 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

*Reading the table: a group's three weights are independent. The same group can be a dominant driver of one pillar and a minor input to another — e.g. a group may carry most of the Exposure weight while contributing little to Risk.*

### Signal Architecture Rationale
This configuration contains **6 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `DIRECT_OBSERVABLE` (4 signals): Highest confidence
- `INFERRED_PROXY` (2 signals): Medium confidence

**Signal Count by Group:**
- `technical_infrastructure`: 6 signals

**Selection Rationale:**
- 67% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Detail by Group
> *Each signal is an objectively observable data point. The weights show how strongly that signal informs each assessment pillar; correlation direction indicates whether a higher observed value increases (+) or decreases (-) the assessed exposure.*

#### Practice Quality
| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `design_defect_claims` | DIRECT_OBSERVABLE | 0.25 | 0.25 / 0.00 | 0.20 | + |
| `building_code_compliance` | DIRECT_OBSERVABLE | 0.20 | 0.20 / 0.00 | 0.15 | + |
| `project_complexity_score` | INFERRED_PROXY | 0.15 | 0.00 / 0.15 | 0.25 | + |
| `latent_defect_exposure` | INFERRED_PROXY | 0.15 | 0.00 / 0.20 | 0.25 | + |
| `sustainability_certification` | DIRECT_OBSERVABLE | 0.15 | 0.10 / 0.00 | 0.00 | + |

**Categorical signal `pi_construction_phase`** — proxy tier: `DIRECT_OBSERVABLE`, source: `metadata.construction_phase`

| Category | Label | Applied Factor |
|----------|-------|----------------|
| `PRE_CONSTRUCTION` | Pre-Construction | 1.3 |
| `CONSTRUCTION` | Construction | 1.2 |
| `COMMISSIONING` | Commissioning | 1.1 |
| `EARLY_OPERATION` | Early Operation | 1.05 |
| `MATURE_OPERATION` | Mature Operation | 0.9 |
| `OTHER` | Other | 1.0 |

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 | Practice Quality | 1.55 | 0.45 | 0.50 | 0.60 |
| 2 | Regulatory Standing | 0.70 | 0.25 | 0.30 | 0.15 |
| 3 | Firm Stability | 0.40 | 0.15 | 0.10 | 0.15 |
| 4 | Network Authority | 0.20 | 0.10 | 0.05 | 0.05 |
| 5 | Corporate Footprint | 0.15 | 0.05 | 0.05 | 0.05 |

**Primary Assessment Driver:** `Practice Quality` with combined weight of 1.55
**Secondary Driver:** `Regulatory Standing` with combined weight of 0.70

### Three-Layer Pricing Translation
> *How each pillar's tier score becomes a concrete underwriting action or pricing modifier. This is the bridge between signal observation and premium.*

**Risk -> Underwriting Action & Base Rate**

| Tier | Score Band | Action | Rate / Method |
|------|-----------|--------|---------------|
| PREFERRED | 800-1000 | APPROVE | 0.12% (MULTIPLIER) |
| STANDARD_PLUS | 650-799 | APPROVE | 0.18% (MULTIPLIER) |
| STANDARD | 500-649 | REFER | 0.26% (MULTIPLIER) |
| SUBSTANDARD | 350-499 | REFER | 0.4% (MULTIPLIER) |
| DECLINE | 0-349 | DECLINE | 0.6% (MULTIPLIER) |

**Loss -> Frequency & Severity Modifiers**

| Tier | Score Band | Frequency Modifier | Severity Modifier |
|------|-----------|--------------------|-------------------|
| VERY_LOW | 80-100 | 0.7 | 0.8 |
| LOW | 60-79 | 0.85 | 0.9 |
| MODERATE | 40-59 | 1.0 | 1.0 |
| ELEVATED | 20-39 | 1.15 | 1.15 |
| HIGH | 0-19 | 1.35 | 1.4 |

*Loss modifier is bounded: floor 0.55, cap 1.6.*

**Exposure (size) -> Scale Modifier**

| Band | Score Band | Modifier | Implied Value Range |
|------|-----------|----------|---------------------|
| MICRO | 0-20 | 0.5 | $0 - $1,000,000 |
| SMALL | 21-40 | 0.75 | $1,000,000 - $10,000,000 |
| MEDIUM | 41-60 | 1.0 | $10,000,000 - $50,000,000 |
| LARGE | 61-80 | 1.5 | $50,000,000 - $250,000,000 |
| VERY_LARGE | 81-100 | 2.5 | $250,000,000 - $1,000,000,000 |

**Exposure (complexity) -> Scale Modifier**

| Band | Score Band | Modifier | Implied Value Range |
|------|-----------|----------|---------------------|
| SIMPLE | 0-20 | 0.85 | n/a |
| MODERATE | 21-40 | 0.95 | n/a |
| COMPLEX | 41-60 | 1.1 | n/a |
| HIGHLY_COMPLEX | 61-80 | 1.3 | n/a |
| EXTREMELY_COMPLEX | 81-100 | 1.6 | n/a |

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
- `sub_profession_type in ['STRUCTURAL', 'GEOTECHNICAL', 'CIVIL', 'MECHANICAL', 'ELECTRICAL', 'ENVIRONMENTAL_ENG']`

### Three-Layer Weight Distribution
> *DSI requires that weights for Risk, Loss, and Exposure each sum to 1.0 across all signal groups.*

**Validation:** PASS

| Group | Risk | Loss | Exposure |
|-------|------|------|----------|
| Network Authority | 0.05 | 0.05 | 0.05 |
| Regulatory Standing | 0.30 | 0.30 | 0.15 |
| Firm Stability | 0.10 | 0.10 | 0.10 |
| Practice Quality | 0.50 | 0.50 | 0.65 |
| Corporate Footprint | 0.05 | 0.05 | 0.05 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

*Reading the table: a group's three weights are independent. The same group can be a dominant driver of one pillar and a minor input to another — e.g. a group may carry most of the Exposure weight while contributing little to Risk.*

### Signal Architecture Rationale
This configuration contains **6 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `DIRECT_OBSERVABLE` (4 signals): Highest confidence
- `INFERRED_PROXY` (2 signals): Medium confidence

**Signal Count by Group:**
- `technical_infrastructure`: 6 signals

**Selection Rationale:**
- 67% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Detail by Group
> *Each signal is an objectively observable data point. The weights show how strongly that signal informs each assessment pillar; correlation direction indicates whether a higher observed value increases (+) or decreases (-) the assessed exposure.*

#### Practice Quality
| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `structural_failure_history` | DIRECT_OBSERVABLE | 0.25 | 0.00 / 0.30 | 0.25 | + |
| `pe_license_compliance` | DIRECT_OBSERVABLE | 0.20 | 0.15 / 0.00 | 0.00 | + |
| `geotechnical_claim_frequency` | DIRECT_OBSERVABLE | 0.20 | 0.20 / 0.00 | 0.20 | + |
| `infrastructure_project_exposure` | INFERRED_PROXY | 0.15 | 0.00 / 0.15 | 0.20 | + |
| `project_size_concentration` | INFERRED_PROXY | 0.10 | 0.00 / 0.10 | 0.25 | + |
| `remediation_cost_history` | DIRECT_OBSERVABLE | 0.10 | 0.00 / 0.10 | 0.10 | + |

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 | Practice Quality | 1.65 | 0.50 | 0.50 | 0.65 |
| 2 | Regulatory Standing | 0.75 | 0.30 | 0.30 | 0.15 |
| 3 | Firm Stability | 0.30 | 0.10 | 0.10 | 0.10 |
| 4 | Network Authority | 0.15 | 0.05 | 0.05 | 0.05 |
| 5 | Corporate Footprint | 0.15 | 0.05 | 0.05 | 0.05 |

**Primary Assessment Driver:** `Practice Quality` with combined weight of 1.65
**Secondary Driver:** `Regulatory Standing` with combined weight of 0.75

### Three-Layer Pricing Translation
> *How each pillar's tier score becomes a concrete underwriting action or pricing modifier. This is the bridge between signal observation and premium.*

**Risk -> Underwriting Action & Base Rate**

| Tier | Score Band | Action | Rate / Method |
|------|-----------|--------|---------------|
| PREFERRED | 800-1000 | APPROVE | 0.15% (MULTIPLIER) |
| STANDARD_PLUS | 650-799 | APPROVE | 0.22% (MULTIPLIER) |
| STANDARD | 500-649 | REFER | 0.32% (MULTIPLIER) |
| SUBSTANDARD | 350-499 | REFER | 0.5% (MULTIPLIER) |
| DECLINE | 0-349 | DECLINE | 0.8% (MULTIPLIER) |

**Loss -> Frequency & Severity Modifiers**

| Tier | Score Band | Frequency Modifier | Severity Modifier |
|------|-----------|--------------------|-------------------|
| VERY_LOW | 80-100 | 0.7 | 0.8 |
| LOW | 60-79 | 0.85 | 0.9 |
| MODERATE | 40-59 | 1.0 | 1.0 |
| ELEVATED | 20-39 | 1.15 | 1.15 |
| HIGH | 0-19 | 1.35 | 1.4 |

*Loss modifier is bounded: floor 0.55, cap 1.6.*

**Exposure (size) -> Scale Modifier**

| Band | Score Band | Modifier | Implied Value Range |
|------|-----------|----------|---------------------|
| MICRO | 0-20 | 0.5 | $0 - $1,000,000 |
| SMALL | 21-40 | 0.75 | $1,000,000 - $10,000,000 |
| MEDIUM | 41-60 | 1.0 | $10,000,000 - $50,000,000 |
| LARGE | 61-80 | 1.5 | $50,000,000 - $250,000,000 |
| VERY_LARGE | 81-100 | 2.5 | $250,000,000 - $1,000,000,000 |

**Exposure (complexity) -> Scale Modifier**

| Band | Score Band | Modifier | Implied Value Range |
|------|-----------|----------|---------------------|
| SIMPLE | 0-20 | 0.85 | n/a |
| MODERATE | 21-40 | 0.95 | n/a |
| COMPLEX | 41-60 | 1.1 | n/a |
| HIGHLY_COMPLEX | 61-80 | 1.3 | n/a |
| EXTREMELY_COMPLEX | 81-100 | 1.6 | n/a |

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
| Regulatory Standing | 0.25 | 0.25 | 0.15 |
| Firm Stability | 0.15 | 0.10 | 0.15 |
| Practice Quality | 0.45 | 0.55 | 0.60 |
| Corporate Footprint | 0.05 | 0.05 | 0.05 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

*Reading the table: a group's three weights are independent. The same group can be a dominant driver of one pillar and a minor input to another — e.g. a group may carry most of the Exposure weight while contributing little to Risk.*

### Signal Architecture Rationale
This configuration contains **8 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `DIRECT_OBSERVABLE` (3 signals): Highest confidence
- `INFERRED_PROXY` (5 signals): Medium confidence

**Signal Count by Group:**
- `technical_infrastructure`: 7 signals
- `public_record`: 1 signals

**Selection Rationale:**
- 38% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Detail by Group
> *Each signal is an objectively observable data point. The weights show how strongly that signal informs each assessment pillar; correlation direction indicates whether a higher observed value increases (+) or decreases (-) the assessed exposure.*

#### Regulatory Standing
| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `defamation_exposure` | INFERRED_PROXY | 0.03 | 0.03 / 0.00 | 0.00 | + |

#### Practice Quality
| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `project_failure_rate` | INFERRED_PROXY | 0.25 | 0.25 / 0.00 | 0.20 | + |
| `sla_compliance` | DIRECT_OBSERVABLE | 0.20 | 0.20 / 0.00 | 0.15 | + |
| `data_breach_exposure` | DIRECT_OBSERVABLE | 0.20 | 0.00 / 0.25 | 0.25 | + |
| `technology_stack_currency` | INFERRED_PROXY | 0.15 | 0.15 / 0.00 | 0.15 | + |
| `implementation_methodology` | INFERRED_PROXY | 0.10 | 0.15 / 0.00 | 0.15 | + |
| `client_data_encryption` | DIRECT_OBSERVABLE | 0.10 | 0.00 / 0.10 | 0.10 | + |
| `content_moderation_posture` | INFERRED_PROXY | 0.03 | 0.03 / 0.00 | 0.00 | - |

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 | Practice Quality | 1.60 | 0.45 | 0.55 | 0.60 |
| 2 | Regulatory Standing | 0.65 | 0.25 | 0.25 | 0.15 |
| 3 | Firm Stability | 0.40 | 0.15 | 0.10 | 0.15 |
| 4 | Network Authority | 0.20 | 0.10 | 0.05 | 0.05 |
| 5 | Corporate Footprint | 0.15 | 0.05 | 0.05 | 0.05 |

**Primary Assessment Driver:** `Practice Quality` with combined weight of 1.60
**Secondary Driver:** `Regulatory Standing` with combined weight of 0.65

### Three-Layer Pricing Translation
> *How each pillar's tier score becomes a concrete underwriting action or pricing modifier. This is the bridge between signal observation and premium.*

**Risk -> Underwriting Action & Base Rate**

| Tier | Score Band | Action | Rate / Method |
|------|-----------|--------|---------------|
| PREFERRED | 800-1000 | APPROVE | 0.1% (MULTIPLIER) |
| STANDARD_PLUS | 650-799 | APPROVE | 0.15% (MULTIPLIER) |
| STANDARD | 500-649 | REFER | 0.22% (MULTIPLIER) |
| SUBSTANDARD | 350-499 | REFER | 0.35% (MULTIPLIER) |
| DECLINE | 0-349 | DECLINE | 0.55% (MULTIPLIER) |

**Loss -> Frequency & Severity Modifiers**

| Tier | Score Band | Frequency Modifier | Severity Modifier |
|------|-----------|--------------------|-------------------|
| VERY_LOW | 80-100 | 0.7 | 0.8 |
| LOW | 60-79 | 0.85 | 0.9 |
| MODERATE | 40-59 | 1.0 | 1.0 |
| ELEVATED | 20-39 | 1.15 | 1.15 |
| HIGH | 0-19 | 1.35 | 1.4 |

*Loss modifier is bounded: floor 0.55, cap 1.6.*

**Exposure (size) -> Scale Modifier**

| Band | Score Band | Modifier | Implied Value Range |
|------|-----------|----------|---------------------|
| MICRO | 0-20 | 0.5 | $0 - $1,000,000 |
| SMALL | 21-40 | 0.75 | $1,000,000 - $10,000,000 |
| MEDIUM | 41-60 | 1.0 | $10,000,000 - $50,000,000 |
| LARGE | 61-80 | 1.5 | $50,000,000 - $250,000,000 |
| VERY_LARGE | 81-100 | 2.5 | $250,000,000 - $1,000,000,000 |

**Exposure (complexity) -> Scale Modifier**

| Band | Score Band | Modifier | Implied Value Range |
|------|-----------|----------|---------------------|
| SIMPLE | 0-20 | 0.85 | n/a |
| MODERATE | 21-40 | 0.95 | n/a |
| COMPLEX | 41-60 | 1.1 | n/a |
| HIGHLY_COMPLEX | 61-80 | 1.3 | n/a |
| EXTREMELY_COMPLEX | 81-100 | 1.6 | n/a |

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
| Regulatory Standing | 0.35 | 0.40 | 0.25 |
| Firm Stability | 0.15 | 0.10 | 0.15 |
| Practice Quality | 0.35 | 0.40 | 0.50 |
| Corporate Footprint | 0.05 | 0.05 | 0.05 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

*Reading the table: a group's three weights are independent. The same group can be a dominant driver of one pillar and a minor input to another — e.g. a group may carry most of the Exposure weight while contributing little to Risk.*

### Signal Architecture Rationale
This configuration contains **5 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `DIRECT_OBSERVABLE` (3 signals): Highest confidence
- `INFERRED_PROXY` (2 signals): Medium confidence

**Signal Count by Group:**
- `technical_infrastructure`: 5 signals

**Selection Rationale:**
- 60% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Detail by Group
> *Each signal is an objectively observable data point. The weights show how strongly that signal informs each assessment pillar; correlation direction indicates whether a higher observed value increases (+) or decreases (-) the assessed exposure.*

#### Practice Quality
| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `suitability_compliance` | DIRECT_OBSERVABLE | 0.30 | 0.30 / 0.00 | 0.25 | + |
| `complaint_per_aum` | DIRECT_OBSERVABLE | 0.20 | 0.25 / 0.00 | 0.20 | + |
| `regulatory_exam_results` | DIRECT_OBSERVABLE | 0.20 | 0.00 / 0.20 | 0.15 | + |
| `churning_indicators` | INFERRED_PROXY | 0.15 | 0.15 / 0.00 | 0.20 | + |
| `fee_transparency_score` | INFERRED_PROXY | 0.15 | 0.10 / 0.00 | 0.15 | + |

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 | Practice Quality | 1.25 | 0.35 | 0.40 | 0.50 |
| 2 | Regulatory Standing | 1.00 | 0.35 | 0.40 | 0.25 |
| 3 | Firm Stability | 0.40 | 0.15 | 0.10 | 0.15 |
| 4 | Network Authority | 0.20 | 0.10 | 0.05 | 0.05 |
| 5 | Corporate Footprint | 0.15 | 0.05 | 0.05 | 0.05 |

**Primary Assessment Driver:** `Practice Quality` with combined weight of 1.25
**Secondary Driver:** `Regulatory Standing` with combined weight of 1.00

### Three-Layer Pricing Translation
> *How each pillar's tier score becomes a concrete underwriting action or pricing modifier. This is the bridge between signal observation and premium.*

**Risk -> Underwriting Action & Base Rate**

| Tier | Score Band | Action | Rate / Method |
|------|-----------|--------|---------------|
| PREFERRED | 800-1000 | APPROVE | 0.12% (MULTIPLIER) |
| STANDARD_PLUS | 650-799 | APPROVE | 0.18% (MULTIPLIER) |
| STANDARD | 500-649 | REFER | 0.28% (MULTIPLIER) |
| SUBSTANDARD | 350-499 | REFER | 0.42% (MULTIPLIER) |
| DECLINE | 0-349 | DECLINE | 0.65% (MULTIPLIER) |

**Loss -> Frequency & Severity Modifiers**

| Tier | Score Band | Frequency Modifier | Severity Modifier |
|------|-----------|--------------------|-------------------|
| VERY_LOW | 80-100 | 0.7 | 0.8 |
| LOW | 60-79 | 0.85 | 0.9 |
| MODERATE | 40-59 | 1.0 | 1.0 |
| ELEVATED | 20-39 | 1.15 | 1.15 |
| HIGH | 0-19 | 1.35 | 1.4 |

*Loss modifier is bounded: floor 0.55, cap 1.6.*

**Exposure (size) -> Scale Modifier**

| Band | Score Band | Modifier | Implied Value Range |
|------|-----------|----------|---------------------|
| MICRO | 0-20 | 0.5 | $0 - $1,000,000 |
| SMALL | 21-40 | 0.75 | $1,000,000 - $10,000,000 |
| MEDIUM | 41-60 | 1.0 | $10,000,000 - $50,000,000 |
| LARGE | 61-80 | 1.5 | $50,000,000 - $250,000,000 |
| VERY_LARGE | 81-100 | 2.5 | $250,000,000 - $1,000,000,000 |

**Exposure (complexity) -> Scale Modifier**

| Band | Score Band | Modifier | Implied Value Range |
|------|-----------|----------|---------------------|
| SIMPLE | 0-20 | 0.85 | n/a |
| MODERATE | 21-40 | 0.95 | n/a |
| COMPLEX | 41-60 | 1.1 | n/a |
| HIGHLY_COMPLEX | 61-80 | 1.3 | n/a |
| EXTREMELY_COMPLEX | 81-100 | 1.6 | n/a |

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
| Regulatory Standing | 0.25 | 0.30 | 0.20 |
| Firm Stability | 0.20 | 0.15 | 0.20 |
| Practice Quality | 0.30 | 0.35 | 0.30 |
| Corporate Footprint | 0.10 | 0.10 | 0.20 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

*Reading the table: a group's three weights are independent. The same group can be a dominant driver of one pillar and a minor input to another — e.g. a group may carry most of the Exposure weight while contributing little to Risk.*

### Signal Architecture Rationale
This configuration contains **0 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**

**Signal Count by Group:**

**Selection Rationale:**
- 0% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Detail by Group
> *Each signal is an objectively observable data point. The weights show how strongly that signal informs each assessment pillar; correlation direction indicates whether a higher observed value increases (+) or decreases (-) the assessed exposure.*

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 | Practice Quality | 0.95 | 0.30 | 0.35 | 0.30 |
| 2 | Regulatory Standing | 0.75 | 0.25 | 0.30 | 0.20 |
| 3 | Firm Stability | 0.55 | 0.20 | 0.15 | 0.20 |
| 4 | Corporate Footprint | 0.40 | 0.10 | 0.10 | 0.20 |
| 5 | Network Authority | 0.35 | 0.15 | 0.10 | 0.10 |

**Primary Assessment Driver:** `Practice Quality` with combined weight of 0.95
**Secondary Driver:** `Regulatory Standing` with combined weight of 0.75

### Three-Layer Pricing Translation
> *How each pillar's tier score becomes a concrete underwriting action or pricing modifier. This is the bridge between signal observation and premium.*

**Risk -> Underwriting Action & Base Rate**

| Tier | Score Band | Action | Rate / Method |
|------|-----------|--------|---------------|
| PREFERRED | 800-1000 | APPROVE | 0.06% (MULTIPLIER) |
| STANDARD_PLUS | 650-799 | APPROVE | 0.1% (MULTIPLIER) |
| STANDARD | 500-649 | REFER | 0.15% (MULTIPLIER) |
| SUBSTANDARD | 350-499 | REFER | 0.24% (MULTIPLIER) |
| DECLINE | 0-349 | DECLINE | 0.38% (MULTIPLIER) |

**Loss -> Frequency & Severity Modifiers**

| Tier | Score Band | Frequency Modifier | Severity Modifier |
|------|-----------|--------------------|-------------------|
| VERY_LOW | 80-100 | 0.7 | 0.8 |
| LOW | 60-79 | 0.85 | 0.9 |
| MODERATE | 40-59 | 1.0 | 1.0 |
| ELEVATED | 20-39 | 1.15 | 1.15 |
| HIGH | 0-19 | 1.35 | 1.4 |

*Loss modifier is bounded: floor 0.55, cap 1.6.*

**Exposure (size) -> Scale Modifier**

| Band | Score Band | Modifier | Implied Value Range |
|------|-----------|----------|---------------------|
| MICRO | 0-20 | 0.5 | $0 - $1,000,000 |
| SMALL | 21-40 | 0.75 | $1,000,000 - $10,000,000 |
| MEDIUM | 41-60 | 1.0 | $10,000,000 - $50,000,000 |
| LARGE | 61-80 | 1.5 | $50,000,000 - $250,000,000 |
| VERY_LARGE | 81-100 | 2.5 | $250,000,000 - $1,000,000,000 |

**Exposure (complexity) -> Scale Modifier**

| Band | Score Band | Modifier | Implied Value Range |
|------|-----------|----------|---------------------|
| SIMPLE | 0-20 | 0.85 | n/a |
| MODERATE | 21-40 | 0.95 | n/a |
| COMPLEX | 41-60 | 1.1 | n/a |
| HIGHLY_COMPLEX | 61-80 | 1.3 | n/a |
| EXTREMELY_COMPLEX | 81-100 | 1.6 | n/a |

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
| Regulatory Standing | 0.30 | 0.35 | 0.20 |
| Firm Stability | 0.15 | 0.10 | 0.15 |
| Practice Quality | 0.40 | 0.45 | 0.55 |
| Corporate Footprint | 0.05 | 0.05 | 0.05 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

*Reading the table: a group's three weights are independent. The same group can be a dominant driver of one pillar and a minor input to another — e.g. a group may carry most of the Exposure weight while contributing little to Risk.*

### Signal Architecture Rationale
This configuration contains **5 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `DIRECT_OBSERVABLE` (3 signals): Highest confidence
- `INFERRED_PROXY` (2 signals): Medium confidence

**Signal Count by Group:**
- `technical_infrastructure`: 5 signals

**Selection Rationale:**
- 60% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Detail by Group
> *Each signal is an objectively observable data point. The weights show how strongly that signal informs each assessment pillar; correlation direction indicates whether a higher observed value increases (+) or decreases (-) the assessed exposure.*

#### Practice Quality
| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `valuation_accuracy` | DIRECT_OBSERVABLE | 0.30 | 0.25 / 0.00 | 0.25 | + |
| `negligent_misstatement_history` | DIRECT_OBSERVABLE | 0.25 | 0.00 / 0.30 | 0.25 | + |
| `property_type_concentration` | INFERRED_PROXY | 0.15 | 0.00 / 0.15 | 0.20 | + |
| `market_knowledge_currency` | INFERRED_PROXY | 0.15 | 0.15 / 0.00 | 0.15 | + |
| `rics_compliance` | DIRECT_OBSERVABLE | 0.15 | 0.10 / 0.00 | 0.10 | + |

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 | Practice Quality | 1.40 | 0.40 | 0.45 | 0.55 |
| 2 | Regulatory Standing | 0.85 | 0.30 | 0.35 | 0.20 |
| 3 | Firm Stability | 0.40 | 0.15 | 0.10 | 0.15 |
| 4 | Network Authority | 0.20 | 0.10 | 0.05 | 0.05 |
| 5 | Corporate Footprint | 0.15 | 0.05 | 0.05 | 0.05 |

**Primary Assessment Driver:** `Practice Quality` with combined weight of 1.40
**Secondary Driver:** `Regulatory Standing` with combined weight of 0.85

### Three-Layer Pricing Translation
> *How each pillar's tier score becomes a concrete underwriting action or pricing modifier. This is the bridge between signal observation and premium.*

**Risk -> Underwriting Action & Base Rate**

| Tier | Score Band | Action | Rate / Method |
|------|-----------|--------|---------------|
| PREFERRED | 800-1000 | APPROVE | 0.1% (MULTIPLIER) |
| STANDARD_PLUS | 650-799 | APPROVE | 0.15% (MULTIPLIER) |
| STANDARD | 500-649 | REFER | 0.22% (MULTIPLIER) |
| SUBSTANDARD | 350-499 | REFER | 0.35% (MULTIPLIER) |
| DECLINE | 0-349 | DECLINE | 0.55% (MULTIPLIER) |

**Loss -> Frequency & Severity Modifiers**

| Tier | Score Band | Frequency Modifier | Severity Modifier |
|------|-----------|--------------------|-------------------|
| VERY_LOW | 80-100 | 0.7 | 0.8 |
| LOW | 60-79 | 0.85 | 0.9 |
| MODERATE | 40-59 | 1.0 | 1.0 |
| ELEVATED | 20-39 | 1.15 | 1.15 |
| HIGH | 0-19 | 1.35 | 1.4 |

*Loss modifier is bounded: floor 0.55, cap 1.6.*

**Exposure (size) -> Scale Modifier**

| Band | Score Band | Modifier | Implied Value Range |
|------|-----------|----------|---------------------|
| MICRO | 0-20 | 0.5 | $0 - $1,000,000 |
| SMALL | 21-40 | 0.75 | $1,000,000 - $10,000,000 |
| MEDIUM | 41-60 | 1.0 | $10,000,000 - $50,000,000 |
| LARGE | 61-80 | 1.5 | $50,000,000 - $250,000,000 |
| VERY_LARGE | 81-100 | 2.5 | $250,000,000 - $1,000,000,000 |

**Exposure (complexity) -> Scale Modifier**

| Band | Score Band | Modifier | Implied Value Range |
|------|-----------|----------|---------------------|
| SIMPLE | 0-20 | 0.85 | n/a |
| MODERATE | 21-40 | 0.95 | n/a |
| COMPLEX | 41-60 | 1.1 | n/a |
| HIGHLY_COMPLEX | 61-80 | 1.3 | n/a |
| EXTREMELY_COMPLEX | 81-100 | 1.6 | n/a |

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
| Regulatory Standing | 0.30 | 0.35 | 0.20 |
| Firm Stability | 0.10 | 0.10 | 0.10 |
| Practice Quality | 0.50 | 0.45 | 0.60 |
| Corporate Footprint | 0.05 | 0.05 | 0.05 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

*Reading the table: a group's three weights are independent. The same group can be a dominant driver of one pillar and a minor input to another — e.g. a group may carry most of the Exposure weight while contributing little to Risk.*

### Signal Architecture Rationale
This configuration contains **5 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `DIRECT_OBSERVABLE` (3 signals): Highest confidence
- `INFERRED_PROXY` (2 signals): Medium confidence

**Signal Count by Group:**
- `technical_infrastructure`: 5 signals

**Selection Rationale:**
- 60% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Detail by Group
> *Each signal is an objectively observable data point. The weights show how strongly that signal informs each assessment pillar; correlation direction indicates whether a higher observed value increases (+) or decreases (-) the assessed exposure.*

#### Practice Quality
| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `contamination_assessment_accuracy` | DIRECT_OBSERVABLE | 0.30 | 0.25 / 0.00 | 0.25 | + |
| `regulatory_compliance_track` | DIRECT_OBSERVABLE | 0.20 | 0.20 / 0.00 | 0.15 | + |
| `remediation_effectiveness` | INFERRED_PROXY | 0.20 | 0.00 / 0.20 | 0.20 | + |
| `long_tail_exposure` | INFERRED_PROXY | 0.15 | 0.00 / 0.20 | 0.25 | + |
| `cercla_superfund_exposure` | DIRECT_OBSERVABLE | 0.15 | 0.00 / 0.15 | 0.15 | + |

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 | Practice Quality | 1.55 | 0.50 | 0.45 | 0.60 |
| 2 | Regulatory Standing | 0.85 | 0.30 | 0.35 | 0.20 |
| 3 | Firm Stability | 0.30 | 0.10 | 0.10 | 0.10 |
| 4 | Network Authority | 0.15 | 0.05 | 0.05 | 0.05 |
| 5 | Corporate Footprint | 0.15 | 0.05 | 0.05 | 0.05 |

**Primary Assessment Driver:** `Practice Quality` with combined weight of 1.55
**Secondary Driver:** `Regulatory Standing` with combined weight of 0.85

### Three-Layer Pricing Translation
> *How each pillar's tier score becomes a concrete underwriting action or pricing modifier. This is the bridge between signal observation and premium.*

**Risk -> Underwriting Action & Base Rate**

| Tier | Score Band | Action | Rate / Method |
|------|-----------|--------|---------------|
| PREFERRED | 800-1000 | APPROVE | 0.14% (MULTIPLIER) |
| STANDARD_PLUS | 650-799 | APPROVE | 0.2% (MULTIPLIER) |
| STANDARD | 500-649 | REFER | 0.3% (MULTIPLIER) |
| SUBSTANDARD | 350-499 | REFER | 0.46% (MULTIPLIER) |
| DECLINE | 0-349 | DECLINE | 0.72% (MULTIPLIER) |

**Loss -> Frequency & Severity Modifiers**

| Tier | Score Band | Frequency Modifier | Severity Modifier |
|------|-----------|--------------------|-------------------|
| VERY_LOW | 80-100 | 0.7 | 0.8 |
| LOW | 60-79 | 0.85 | 0.9 |
| MODERATE | 40-59 | 1.0 | 1.0 |
| ELEVATED | 20-39 | 1.15 | 1.15 |
| HIGH | 0-19 | 1.35 | 1.4 |

*Loss modifier is bounded: floor 0.55, cap 1.6.*

**Exposure (size) -> Scale Modifier**

| Band | Score Band | Modifier | Implied Value Range |
|------|-----------|----------|---------------------|
| MICRO | 0-20 | 0.5 | $0 - $1,000,000 |
| SMALL | 21-40 | 0.75 | $1,000,000 - $10,000,000 |
| MEDIUM | 41-60 | 1.0 | $10,000,000 - $50,000,000 |
| LARGE | 61-80 | 1.5 | $50,000,000 - $250,000,000 |
| VERY_LARGE | 81-100 | 2.5 | $250,000,000 - $1,000,000,000 |

**Exposure (complexity) -> Scale Modifier**

| Band | Score Band | Modifier | Implied Value Range |
|------|-----------|----------|---------------------|
| SIMPLE | 0-20 | 0.85 | n/a |
| MODERATE | 21-40 | 0.95 | n/a |
| COMPLEX | 41-60 | 1.1 | n/a |
| HIGHLY_COMPLEX | 61-80 | 1.3 | n/a |
| EXTREMELY_COMPLEX | 81-100 | 1.6 | n/a |

### Theoretical Premium Calculation (Tier 3 Standard)
> *Per the DSI Premium Calculation Methodology v2.0, the core formula is:*
> *P_final = (Base × Rate) × ILF_relativity × Deductible_Factor × Modifiers*

**1. The Pricing Anchor:** The Base Rate of `0.3%` on `revenue` purchases exactly a `$2,000,000` Limit with a `$50,000` Deductible.
**2. Theoretical Execution:**
  - Assume `revenue` = $10,000,000
  - Base Premium = $10,000,000 × 0.003 = **$30,000**
  - If the client requests the Anchor Limit/Deductible, the factors are 1.00, resulting in a technical premium of **$30,000**.

---

## Model: `pi_clinical_research`
*CROs, IRBs, clinical-trial sponsors, academic research institutions*

### Routing Protocol (Multiplexer)
- `industry_sector in ['CRO', 'IRB', 'CLINICAL_RESEARCH', 'CLINICAL_TRIAL_SPONSOR', 'ACADEMIC_MEDICAL_CENTER']`

### Three-Layer Weight Distribution
> *DSI requires that weights for Risk, Loss, and Exposure each sum to 1.0 across all signal groups.*

**Validation:** PASS

| Group | Risk | Loss | Exposure |
|-------|------|------|----------|
| Regulatory & GCP Compliance | 0.55 | 0.50 | 0.45 |
| Claim & Litigation Record | 0.30 | 0.35 | 0.30 |
| IT Security | 0.05 | 0.05 | 0.10 |
| Network Authority | 0.05 | 0.05 | 0.10 |
| Corporate Footprint | 0.05 | 0.05 | 0.05 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

**Group Definitions:**
- **Regulatory & GCP Compliance:** IRB, ClinicalTrials.gov, GCP maturity
- **Claim & Litigation Record:** Breach + litigation + FDA warning letters

*Reading the table: a group's three weights are independent. The same group can be a dominant driver of one pillar and a minor input to another — e.g. a group may carry most of the Exposure weight while contributing little to Risk.*

### Signal Architecture Rationale
This configuration contains **5 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `DIRECT_OBSERVABLE` (4 signals): Highest confidence
- `INFERRED_PROXY` (1 signals): Medium confidence

**Signal Count by Group:**
- `structured_data`: 3 signals
- `public_record`: 2 signals

**Selection Rationale:**
- 80% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Detail by Group
> *Each signal is an objectively observable data point. The weights show how strongly that signal informs each assessment pillar; correlation direction indicates whether a higher observed value increases (+) or decreases (-) the assessed exposure.*

#### Regulatory & GCP Compliance
*IRB, ClinicalTrials.gov, GCP maturity*

| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `irb_registration` | DIRECT_OBSERVABLE | 0.22 | 0.00 / 0.22 | 0.00 | - |
| `clinical_trial_registry_compliance` | DIRECT_OBSERVABLE | 0.18 | 0.18 / 0.00 | 0.00 | - |
| `good_clinical_practice_score` | INFERRED_PROXY | 0.18 | 0.15 / 0.00 | 0.00 | - |

#### Claim & Litigation Record
*Breach + litigation + FDA warning letters*

| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `breach_history` | DIRECT_OBSERVABLE | 0.15 | 0.00 / 0.15 | 0.00 | + |
| `litigation_history` | DIRECT_OBSERVABLE | 0.12 | 0.12 / 0.00 | 0.00 | + |

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 | Regulatory & GCP Compliance | 1.50 | 0.55 | 0.50 | 0.45 |
| 2 | Claim & Litigation Record | 0.95 | 0.30 | 0.35 | 0.30 |
| 3 | IT Security | 0.20 | 0.05 | 0.05 | 0.10 |
| 4 | Network Authority | 0.20 | 0.05 | 0.05 | 0.10 |
| 5 | Corporate Footprint | 0.15 | 0.05 | 0.05 | 0.05 |

**Primary Assessment Driver:** `Regulatory & GCP Compliance` with combined weight of 1.50
**Secondary Driver:** `Claim & Litigation Record` with combined weight of 0.95

### Three-Layer Pricing Translation
> *How each pillar's tier score becomes a concrete underwriting action or pricing modifier. This is the bridge between signal observation and premium.*

**Risk -> Underwriting Action & Base Rate**

| Tier | Score Band | Action | Rate / Method |
|------|-----------|--------|---------------|
| PREFERRED | 800-1000 | APPROVE | 0.12% (MULTIPLIER) |
| STANDARD_PLUS | 650-799 | APPROVE | 0.22% (MULTIPLIER) |
| STANDARD | 500-649 | REFER | 0.38% (MULTIPLIER) |
| SUBSTANDARD | 350-499 | REFER | 0.58% (MULTIPLIER) |
| DECLINE | 0-349 | DECLINE | 0.78% (MULTIPLIER) |

**Loss -> Frequency & Severity Modifiers**

| Tier | Score Band | Frequency Modifier | Severity Modifier |
|------|-----------|--------------------|-------------------|
| VERY_LOW | 80-100 | 0.7 | 0.8 |
| LOW | 60-79 | 0.85 | 0.9 |
| MODERATE | 40-59 | 1.0 | 1.0 |
| ELEVATED | 20-39 | 1.2 | 1.25 |
| HIGH | 0-19 | 1.5 | 1.6 |

*Loss modifier is bounded: floor 0.55, cap 1.7.*

**Exposure (size) -> Scale Modifier**

| Band | Score Band | Modifier | Implied Value Range |
|------|-----------|----------|---------------------|
| MICRO | 0-20 | 0.5 | $0 - $1,000,000 |
| SMALL | 21-40 | 0.75 | $1,000,000 - $10,000,000 |
| MEDIUM | 41-60 | 1.0 | $10,000,000 - $50,000,000 |
| LARGE | 61-80 | 1.5 | $50,000,000 - $250,000,000 |
| VERY_LARGE | 81-100 | 2.5 | $250,000,000 - $1,000,000,000 |

**Exposure (complexity) -> Scale Modifier**

| Band | Score Band | Modifier | Implied Value Range |
|------|-----------|----------|---------------------|
| SIMPLE | 0-20 | 0.85 | n/a |
| MODERATE | 21-40 | 0.95 | n/a |
| COMPLEX | 41-60 | 1.15 | n/a |
| HIGHLY_COMPLEX | 61-80 | 1.35 | n/a |
| EXTREMELY_COMPLEX | 81-100 | 1.7 | n/a |

### Theoretical Premium Calculation (Tier 3 Standard)
> *Per the DSI Premium Calculation Methodology v2.0, the core formula is:*
> *P_final = (Base × Rate) × ILF_relativity × Deductible_Factor × Modifiers*

**1. The Pricing Anchor:** The Base Rate of `0.38%` on `revenue` purchases exactly a `$10,000,000` Limit with a `$100,000` Deductible.
**2. Theoretical Execution:**
  - Assume `revenue` = $10,000,000
  - Base Premium = $10,000,000 × 0.0038 = **$38,000**
  - If the client requests the Anchor Limit/Deductible, the factors are 1.00, resulting in a technical premium of **$38,000**.

---

## Model: `pi_media_tech`
*Publishers, broadcasters, content creators, ad-tech firms*

### Routing Protocol (Multiplexer)
- `industry_sector in ['PUBLISHING', 'BROADCAST', 'CONTENT_CREATION', 'ADTECH', 'MEDIA']`

### Three-Layer Weight Distribution
> *DSI requires that weights for Risk, Loss, and Exposure each sum to 1.0 across all signal groups.*

**Validation:** PASS

| Group | Risk | Loss | Exposure |
|-------|------|------|----------|
| Editorial & Moderation Controls | 0.25 | 0.25 | 0.30 |
| Media-Liability Record | 0.55 | 0.55 | 0.40 |
| Platform Security | 0.10 | 0.10 | 0.15 |
| Network Authority | 0.05 | 0.05 | 0.05 |
| Corporate Footprint | 0.05 | 0.05 | 0.10 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

**Group Definitions:**
- **Editorial & Moderation Controls:** Editorial review, moderation posture, transparency practices
- **Media-Liability Record:** Defamation + litigation + breach history

*Reading the table: a group's three weights are independent. The same group can be a dominant driver of one pillar and a minor input to another — e.g. a group may carry most of the Exposure weight while contributing little to Risk.*

### Signal Architecture Rationale
This configuration contains **4 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `DIRECT_OBSERVABLE` (2 signals): Highest confidence
- `INFERRED_PROXY` (2 signals): Medium confidence

**Signal Count by Group:**
- `public_record`: 3 signals
- `structured_data`: 1 signals

**Selection Rationale:**
- 50% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Detail by Group
> *Each signal is an objectively observable data point. The weights show how strongly that signal informs each assessment pillar; correlation direction indicates whether a higher observed value increases (+) or decreases (-) the assessed exposure.*

#### Editorial & Moderation Controls
*Editorial review, moderation posture, transparency practices*

| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `content_moderation_posture` | INFERRED_PROXY | 0.20 | 0.20 / 0.00 | 0.00 | - |

#### Media-Liability Record
*Defamation + litigation + breach history*

| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `defamation_exposure` | INFERRED_PROXY | 0.25 | 0.00 / 0.28 | 0.00 | + |
| `litigation_history` | DIRECT_OBSERVABLE | 0.15 | 0.15 / 0.00 | 0.00 | + |
| `breach_history` | DIRECT_OBSERVABLE | 0.10 | 0.00 / 0.10 | 0.00 | + |

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 | Media-Liability Record | 1.50 | 0.55 | 0.55 | 0.40 |
| 2 | Editorial & Moderation Controls | 0.80 | 0.25 | 0.25 | 0.30 |
| 3 | Platform Security | 0.35 | 0.10 | 0.10 | 0.15 |
| 4 | Corporate Footprint | 0.20 | 0.05 | 0.05 | 0.10 |
| 5 | Network Authority | 0.15 | 0.05 | 0.05 | 0.05 |

**Primary Assessment Driver:** `Media-Liability Record` with combined weight of 1.50
**Secondary Driver:** `Editorial & Moderation Controls` with combined weight of 0.80

### Three-Layer Pricing Translation
> *How each pillar's tier score becomes a concrete underwriting action or pricing modifier. This is the bridge between signal observation and premium.*

**Risk -> Underwriting Action & Base Rate**

| Tier | Score Band | Action | Rate / Method |
|------|-----------|--------|---------------|
| PREFERRED | 800-1000 | APPROVE | 0.12% (MULTIPLIER) |
| STANDARD_PLUS | 650-799 | APPROVE | 0.22% (MULTIPLIER) |
| STANDARD | 500-649 | REFER | 0.38% (MULTIPLIER) |
| SUBSTANDARD | 350-499 | REFER | 0.58% (MULTIPLIER) |
| DECLINE | 0-349 | DECLINE | 0.78% (MULTIPLIER) |

**Loss -> Frequency & Severity Modifiers**

| Tier | Score Band | Frequency Modifier | Severity Modifier |
|------|-----------|--------------------|-------------------|
| VERY_LOW | 80-100 | 0.7 | 0.8 |
| LOW | 60-79 | 0.85 | 0.9 |
| MODERATE | 40-59 | 1.0 | 1.0 |
| ELEVATED | 20-39 | 1.2 | 1.25 |
| HIGH | 0-19 | 1.5 | 1.6 |

*Loss modifier is bounded: floor 0.55, cap 1.7.*

**Exposure (size) -> Scale Modifier**

| Band | Score Band | Modifier | Implied Value Range |
|------|-----------|----------|---------------------|
| MICRO | 0-20 | 0.5 | $0 - $1,000,000 |
| SMALL | 21-40 | 0.75 | $1,000,000 - $10,000,000 |
| MEDIUM | 41-60 | 1.0 | $10,000,000 - $50,000,000 |
| LARGE | 61-80 | 1.5 | $50,000,000 - $250,000,000 |
| VERY_LARGE | 81-100 | 2.5 | $250,000,000 - $1,000,000,000 |

**Exposure (complexity) -> Scale Modifier**

| Band | Score Band | Modifier | Implied Value Range |
|------|-----------|----------|---------------------|
| SIMPLE | 0-20 | 0.85 | n/a |
| MODERATE | 21-40 | 0.95 | n/a |
| COMPLEX | 41-60 | 1.15 | n/a |
| HIGHLY_COMPLEX | 61-80 | 1.35 | n/a |
| EXTREMELY_COMPLEX | 81-100 | 1.7 | n/a |

### Theoretical Premium Calculation (Tier 3 Standard)
> *Per the DSI Premium Calculation Methodology v2.0, the core formula is:*
> *P_final = (Base × Rate) × ILF_relativity × Deductible_Factor × Modifiers*

**1. The Pricing Anchor:** The Base Rate of `0.38%` on `revenue` purchases exactly a `$10,000,000` Limit with a `$100,000` Deductible.
**2. Theoretical Execution:**
  - Assume `revenue` = $10,000,000
  - Base Premium = $10,000,000 × 0.0038 = **$38,000**
  - If the client requests the Anchor Limit/Deductible, the factors are 1.00, resulting in a technical premium of **$38,000**.


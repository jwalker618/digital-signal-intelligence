# DSI Logic Document: `CYBER`
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

**Group Definitions:**
- **Network Authority:** Industry relationships, partnerships, and counterparty quality
- **Technical Infrastructure:** Observable technical security implementation
- **Corporate Footprint:** Signals from company's digital presence and security posture
- **Public Record:** Breach history, regulatory actions, and public disclosures
- **Structured Data:** Third-party security ratings and scores

*Reading the table: a group's three weights are independent. The same group can be a dominant driver of one pillar and a minor input to another — e.g. a group may carry most of the Exposure weight while contributing little to Risk.*

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

### Signal Detail by Group
> *Each signal is an objectively observable data point. The weights show how strongly that signal informs each assessment pillar; correlation direction indicates whether a higher observed value increases (+) or decreases (-) the assessed exposure.*

#### Network Authority
*Industry relationships, partnerships, and counterparty quality*

| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `security_vendor_presence` | INFERRED_PROXY | 0.25 | 0.35 / 0.35 | 0.15 | + |
| `customer_quality` | INFERRED_PROXY | 0.15 | 0.00 / 0.15 | 0.00 | + |
| `partner_quality` | INFERRED_PROXY | 0.10 | 0.20 / 0.20 | 0.00 | + |
| `industry_body_membership` | INFERRED_PROXY | 0.15 | 0.00 / 0.00 | 0.00 | + |
| `certification_authority_presence` | INFERRED_PROXY | 0.15 | 0.30 / 0.00 | 0.00 | + |
| `financial_relationships` | INFERRED_PROXY | 0.05 | 0.00 / 0.00 | 0.00 | + |
| `network_centrality` | INFERRED_PROXY | 0.10 | 0.00 / 0.00 | 0.10 | + |
| `second_degree_connections` | INFERRED_PROXY | 0.05 | 0.00 / 0.00 | 0.05 | + |

#### Technical Infrastructure
*Observable technical security implementation*

| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `tls_configuration` | DIRECT_OBSERVABLE | 0.12 | 0.25 / 0.00 | 0.10 | + |
| `security_headers` | DIRECT_OBSERVABLE | 0.10 | 0.30 / 0.30 | 0.00 | + |
| `email_authentication` | DIRECT_OBSERVABLE | 0.12 | 0.00 / 0.00 | 0.00 | + |
| `dnssec_status` | DIRECT_OBSERVABLE | 0.05 | 0.00 / 0.00 | 0.00 | + |
| `network_exposure` | DIRECT_OBSERVABLE | 0.18 | 0.00 / 0.00 | 0.15 | + |
| `software_currency` | INFERRED_PROXY | 0.10 | 0.25 / 0.25 | 0.00 | + |
| `cve_exposure` | DIRECT_OBSERVABLE | 0.18 | 0.20 / 0.00 | 0.00 | + |
| `cloud_infrastructure` | INFERRED_PROXY | 0.05 | 0.00 / 0.00 | 0.25 | + |
| `waf_presence` | DIRECT_OBSERVABLE | 0.05 | 0.00 / 0.00 | 0.00 | + |
| `cdn_usage` | DIRECT_OBSERVABLE | 0.05 | 0.00 / 0.00 | 0.05 | + |

#### Corporate Footprint
*Signals from company's digital presence and security posture*

| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `security_page_presence` | DIRECT_OBSERVABLE | 0.12 | 0.00 / 0.35 | 0.00 | + |
| `privacy_policy_presence` | DIRECT_OBSERVABLE | 0.08 | 0.00 / 0.00 | 0.00 | + |
| `security_txt_presence` | DIRECT_OBSERVABLE | 0.06 | 0.00 / 0.00 | 0.00 | + |
| `bug_bounty_presence` | DIRECT_OBSERVABLE | 0.12 | 0.00 / 0.00 | 0.00 | + |
| `security_hiring_activity` | INFERRED_PROXY | 0.10 | 0.00 / 0.00 | 0.10 | + |
| `technical_content_quality` | INFERRED_PROXY | 0.06 | 0.00 / 0.00 | 0.00 | + |
| `developer_resources` | INFERRED_PROXY | 0.06 | 0.00 / 0.00 | 0.08 | + |
| `security_leadership_presence` | INFERRED_PROXY | 0.12 | 0.40 / 0.25 | 0.00 | + |
| `compliance_badges` | DIRECT_OBSERVABLE | 0.08 | 0.25 / 0.00 | 0.10 | + |
| `dns_complexity` | DIRECT_OBSERVABLE | 0.05 | 0.00 / 0.00 | 0.12 | - |
| `subdomain_count` | DIRECT_OBSERVABLE | 0.05 | 0.00 / 0.00 | 0.20 | - |
| `ip_footprint` | DIRECT_OBSERVABLE | 0.05 | 0.00 / 0.00 | 0.10 | - |
| `ssl_certificate_count` | DIRECT_OBSERVABLE | 0.05 | 0.00 / 0.00 | 0.05 | + |
| `job_posting_volume` | INFERRED_PROXY | 0.05 | 0.00 / 0.00 | 0.10 | + |
| `funding_signals` | INFERRED_PROXY | 0.05 | 0.00 / 0.00 | 0.10 | + |

#### Public Record
*Breach history, regulatory actions, and public disclosures*

| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `breach_history` | DIRECT_OBSERVABLE | 0.35 | 0.40 / 0.30 | 0.00 | + |
| `regulatory_actions` | DIRECT_OBSERVABLE | 0.25 | 0.00 / 0.00 | 0.10 | + |
| `litigation_history` | DIRECT_OBSERVABLE | 0.20 | 0.00 / 0.30 | 0.00 | + |
| `credential_exposure` | DIRECT_OBSERVABLE | 0.20 | 0.20 / 0.00 | 0.00 | + |
| `dark_web_presence` | INFERRED_PROXY | 0.20 | 0.10 / 0.00 | 0.00 | + |

#### Structured Data
*Third-party security ratings and scores*

| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `security_rating` | DIRECT_OBSERVABLE | 0.40 | 0.35 / 0.35 | 0.00 | + |
| `esg_cyber_alignment` | INFERRED_PROXY | 0.30 | 0.00 / 0.00 | 0.00 | + |
| `credit_rating` | DIRECT_OBSERVABLE | 0.30 | 0.00 / 0.00 | 0.20 | + |

#### industry_classification
**Categorical signal `industry_classification`** — proxy tier: `INFERRED_PROXY`, source: `metadata.industry_classification`

| Category | Label | Applied Factor |
|----------|-------|----------------|
| `TECHNOLOGY` | Technology | 1.15 |
| `FINANCIAL_SERVICES` | Financial Services | 1.4 |
| `HEALTHCARE` | Healthcare | 1.5 |
| `RETAIL` | Retail | 1.25 |
| `MANUFACTURING` | Manufacturing | 0.95 |
| `PROFESSIONAL_SERVICES` | Professional Services | 1.1 |
| `EDUCATION` | Education | 1.05 |
| `GOVERNMENT` | Government | 0.9 |
| `ENERGY` | Energy | 1.2 |
| `OTHER` | Other | 1.0 |

#### size_band
**Categorical signal `size_band`** — proxy tier: `INFERRED_PROXY`, source: `metadata.size_band`

| Category | Label | Applied Factor |
|----------|-------|----------------|
| `MICRO` | Micro | 1.5 |
| `SMALL` | Small | 1.2 |
| `MEDIUM` | Medium | 1.0 |
| `LARGE` | Large | 0.4 |
| `ENTERPRISE` | Enterprise | 0.12 |
| `OTHER` | Other | 1.0 |

#### geography
**Categorical signal `geography`** — proxy tier: `INFERRED_PROXY`, source: `metadata.geography`

| Category | Label | Applied Factor |
|----------|-------|----------------|
| `US` | United States | 1.0 |
| `UK` | United Kingdom | 1.05 |
| `EU` | European Union | 1.1 |
| `APAC` | Asia Pacific | 1.15 |
| `OTHER` | Other | 1.25 |

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

### Three-Layer Pricing Translation
> *How each pillar's tier score becomes a concrete underwriting action or pricing modifier. This is the bridge between signal observation and premium.*

**Risk -> Underwriting Action & Base Rate**

| Tier | Score Band | Action | Rate / Method |
|------|-----------|--------|---------------|
| PREFERRED | 800-1000 | APPROVE | 0.004% (MULTIPLIER) |
| STANDARD_PLUS | 650-799 | APPROVE | 0.006% (MULTIPLIER) |
| STANDARD | 500-649 | REFER | 0.008% (MULTIPLIER) |
| SUBSTANDARD | 350-499 | REFER | 0.015% (MULTIPLIER) |
| DECLINE | 0-349 | DECLINE | 0.03% (MULTIPLIER) |

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
| MID_MARKET | 0-20 | 1.0 | $50,000,000 - $100,000,000 |
| LARGE_CORP | 21-60 | 0.9 | $100,000,001 - $500,000,000 |
| ENTERPRISE | 61-80 | 0.8 | $500,000,001 - $1,000,000,000 |
| GLOBAL | 81-100 | 0.7 | $1,000,000,001 - + |

**Exposure (complexity) -> Scale Modifier**

| Band | Score Band | Modifier | Implied Value Range |
|------|-----------|----------|---------------------|
| SIMPLE | 0-40 | 1.0 | n/a |
| COMPLEX | 41-70 | 1.15 | n/a |
| HIGHLY_COMPLEX | 71-100 | 1.3 | n/a |

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

**Group Definitions:**
- **Technical Security:** Core security posture signals
- **Public Record:** Historical incidents and ratings
- **Corporate Footprint:** Security page, privacy policy, compliance signals

*Reading the table: a group's three weights are independent. The same group can be a dominant driver of one pillar and a minor input to another — e.g. a group may carry most of the Exposure weight while contributing little to Risk.*

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

### Signal Detail by Group
> *Each signal is an objectively observable data point. The weights show how strongly that signal informs each assessment pillar; correlation direction indicates whether a higher observed value increases (+) or decreases (-) the assessed exposure.*

#### Technical Security
*Core security posture signals*

| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `tls_configuration` | DIRECT_OBSERVABLE | 0.35 | 0.25 / 0.20 | 0.25 | + |
| `email_authentication` | DIRECT_OBSERVABLE | 0.35 | 0.30 / 0.15 | 0.20 | + |
| `security_headers` | DIRECT_OBSERVABLE | 0.30 | 0.20 / 0.15 | 0.20 | + |
| `dnssec_status` | DIRECT_OBSERVABLE | 0.10 | 0.08 / 0.08 | 0.10 | + |
| `waf_presence` | DIRECT_OBSERVABLE | 0.10 | 0.05 / 0.05 | 0.10 | + |
| `cdn_usage` | DIRECT_OBSERVABLE | 0.05 | 0.04 / 0.04 | 0.10 | + |

#### Public Record
*Historical incidents and ratings*

| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `breach_history` | DIRECT_OBSERVABLE | 0.50 | 0.40 / 0.35 | 0.25 | - |
| `security_rating` | INFERRED_PROXY | 0.35 | 0.20 / 0.15 | 0.18 | + |
| `credential_exposure` | DIRECT_OBSERVABLE | 0.15 | 0.15 / 0.15 | 0.14 | + |
| `vulnerability_disclosure` | DIRECT_OBSERVABLE | 0.15 | 0.10 / 0.10 | 0.15 | + |

#### Corporate Footprint
*Security page, privacy policy, compliance signals*

| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `security_page_presence` | DIRECT_OBSERVABLE | 0.35 | 0.15 / 0.15 | 0.24 | + |
| `privacy_policy_presence` | DIRECT_OBSERVABLE | 0.30 | 0.10 / 0.10 | 0.16 | + |
| `compliance_badges` | DIRECT_OBSERVABLE | 0.30 | 0.08 / 0.08 | 0.16 | + |

#### industry_classification
**Categorical signal `industry_classification`** — proxy tier: `DIRECT_OBSERVABLE`, source: `metadata.industry_code`

| Category | Label | Applied Factor |
|----------|-------|----------------|
| `TECH` | Technology | 1.15 |
| `HEALTHCARE` | Healthcare | 1.25 |
| `RETAIL` | Retail | 1.1 |
| `SERVICES` | Professional Services | 1.0 |
| `MANUFACTURING` | Manufacturing | 0.95 |
| `OTHER` | Other | 1.0 |

#### company_size
**Categorical signal `company_size`** — proxy tier: `DIRECT_OBSERVABLE`, source: `metadata.employee_band`

| Category | Label | Applied Factor |
|----------|-------|----------------|
| `MICRO` | 1-10 employees | 0.85 |
| `SMALL` | 11-50 employees | 0.95 |
| `MEDIUM` | 51-250 employees | 1.1 |

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 | Public Record | 1.15 | 0.35 | 0.40 | 0.40 |
| 2 | Technical Security | 1.05 | 0.40 | 0.35 | 0.30 |
| 3 | Corporate Footprint | 0.80 | 0.25 | 0.25 | 0.30 |

**Primary Assessment Driver:** `Public Record` with combined weight of 1.15
**Secondary Driver:** `Technical Security` with combined weight of 1.05

### Three-Layer Pricing Translation
> *How each pillar's tier score becomes a concrete underwriting action or pricing modifier. This is the bridge between signal observation and premium.*

**Risk -> Underwriting Action & Base Rate**

| Tier | Score Band | Action | Rate / Method |
|------|-----------|--------|---------------|
| PREFERRED | 800-1000 | APPROVE | PREMIUM_BASE |
| STANDARD_PLUS | 650-799 | APPROVE | PREMIUM_BASE |
| STANDARD | 500-649 | APPROVE | PREMIUM_BASE |
| SUBSTANDARD | 350-499 | REFER | PREMIUM_BASE |
| DECLINE | 0-349 | DECLINE | PREMIUM_BASE |

**Loss -> Frequency & Severity Modifiers**

| Tier | Score Band | Frequency Modifier | Severity Modifier |
|------|-----------|--------------------|-------------------|
| VERY_LOW | 0-200 | 0.8 | 0.85 |
| LOW | 201-400 | 0.9 | 0.92 |
| MODERATE | 401-600 | 1.0 | 1.0 |
| HIGH | 601-800 | 1.15 | 1.2 |
| VERY_HIGH | 801-1000 | 1.35 | 1.45 |

*Loss modifier is bounded: floor 0.7, cap 1.6.*

**Exposure (size) -> Scale Modifier**

| Band | Score Band | Modifier | Implied Value Range |
|------|-----------|----------|---------------------|
| MICRO | 0-200 | 0.75 | n/a |
| SMALL | 201-500 | 0.9 | n/a |
| MEDIUM | 501-800 | 1.05 | n/a |
| LARGE | 801-1000 | 1.25 | n/a |

**Exposure (complexity) -> Scale Modifier**

| Band | Score Band | Modifier | Implied Value Range |
|------|-----------|----------|---------------------|
| SIMPLE | 0-300 | 0.9 | n/a |
| MODERATE | 301-600 | 1.0 | n/a |
| COMPLEX | 601-1000 | 1.15 | n/a |

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

**Group Definitions:**
- **Health Data Security:** Healthcare-specific data security signals: PHI, medical devices, EHR, HIPAA

*Reading the table: a group's three weights are independent. The same group can be a dominant driver of one pillar and a minor input to another — e.g. a group may carry most of the Exposure weight while contributing little to Risk.*

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

### Signal Detail by Group
> *Each signal is an objectively observable data point. The weights show how strongly that signal informs each assessment pillar; correlation direction indicates whether a higher observed value increases (+) or decreases (-) the assessed exposure.*

#### Health Data Security
*Healthcare-specific data security signals: PHI, medical devices, EHR, HIPAA*

| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `connected_medical_device_security` | INFERRED_PROXY | 0.20 | 0.15 / 0.20 | 0.30 | + |
| `ehr_system_resilience` | INFERRED_PROXY | 0.15 | 0.20 / 0.15 | 0.25 | + |
| `hipaa_compliance_depth` | DIRECT_OBSERVABLE | 0.20 | 0.15 / 0.25 | 0.20 | + |
| `clinical_system_segmentation` | INFERRED_PROXY | 0.25 | 0.10 / 0.10 | 0.35 | + |
| `phi_data_volume` | INFERRED_PROXY | 0.05 | 0.00 / 0.15 | 0.45 | + |
| `hhs_breach_portal_history` | DIRECT_OBSERVABLE | 0.15 | 0.20 / 0.15 | 0.10 | + |

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

### Three-Layer Pricing Translation
> *How each pillar's tier score becomes a concrete underwriting action or pricing modifier. This is the bridge between signal observation and premium.*

**Risk -> Underwriting Action & Base Rate**

| Tier | Score Band | Action | Rate / Method |
|------|-----------|--------|---------------|
| PREFERRED | 800-1000 | APPROVE | 0.1% (MULTIPLIER) |
| STANDARD_PLUS | 650-799 | APPROVE | 0.18% (MULTIPLIER) |
| STANDARD | 500-649 | REFER | 0.3% (MULTIPLIER) |
| SUBSTANDARD | 350-499 | REFER | 0.45% (MULTIPLIER) |
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

**Group Definitions:**
- **Financial System Security:** Payment systems, regulatory compliance, transaction controls

*Reading the table: a group's three weights are independent. The same group can be a dominant driver of one pillar and a minor input to another — e.g. a group may carry most of the Exposure weight while contributing little to Risk.*

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

### Signal Detail by Group
> *Each signal is an objectively observable data point. The weights show how strongly that signal informs each assessment pillar; correlation direction indicates whether a higher observed value increases (+) or decreases (-) the assessed exposure.*

#### Financial System Security
*Payment systems, regulatory compliance, transaction controls*

| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `payment_system_architecture` | INFERRED_PROXY | 0.20 | 0.15 / 0.20 | 0.35 | + |
| `swift_controls` | INFERRED_PROXY | 0.20 | 0.15 / 0.20 | 0.25 | + |
| `pci_compliance_depth` | DIRECT_OBSERVABLE | 0.15 | 0.20 / 0.15 | 0.25 | + |
| `transaction_fraud_controls` | INFERRED_PROXY | 0.15 | 0.20 / 0.15 | 0.25 | + |
| `core_banking_resilience` | INFERRED_PROXY | 0.10 | 0.15 / 0.20 | 0.35 | + |
| `regulatory_examination_history` | DIRECT_OBSERVABLE | 0.20 | 0.15 / 0.10 | 0.30 | + |

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

### Three-Layer Pricing Translation
> *How each pillar's tier score becomes a concrete underwriting action or pricing modifier. This is the bridge between signal observation and premium.*

**Risk -> Underwriting Action & Base Rate**

| Tier | Score Band | Action | Rate / Method |
|------|-----------|--------|---------------|
| PREFERRED | 800-1000 | APPROVE | 0.1% (MULTIPLIER) |
| STANDARD_PLUS | 650-799 | APPROVE | 0.16% (MULTIPLIER) |
| STANDARD | 500-649 | REFER | 0.28% (MULTIPLIER) |
| SUBSTANDARD | 350-499 | REFER | 0.42% (MULTIPLIER) |
| DECLINE | 0-349 | DECLINE | 0.56% (MULTIPLIER) |

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

**Group Definitions:**
- **OT/ICS Security:** Operational technology and industrial control system security

*Reading the table: a group's three weights are independent. The same group can be a dominant driver of one pillar and a minor input to another — e.g. a group may carry most of the Exposure weight while contributing little to Risk.*

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

### Signal Detail by Group
> *Each signal is an objectively observable data point. The weights show how strongly that signal informs each assessment pillar; correlation direction indicates whether a higher observed value increases (+) or decreases (-) the assessed exposure.*

#### OT/ICS Security
*Operational technology and industrial control system security*

| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `ot_network_segmentation` | INFERRED_PROXY | 0.30 | 0.15 / 0.15 | 0.35 | + |
| `scada_security_posture` | INFERRED_PROXY | 0.25 | 0.20 / 0.20 | 0.30 | + |
| `safety_instrumented_system` | INFERRED_PROXY | 0.20 | 0.00 / 0.30 | 0.25 | + |
| `ot_patching_cadence` | INFERRED_PROXY | 0.15 | 0.25 / 0.00 | 0.25 | + |
| `nerc_cip_compliance` | DIRECT_OBSERVABLE | 0.10 | 0.15 / 0.10 | 0.20 | + |

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

### Three-Layer Pricing Translation
> *How each pillar's tier score becomes a concrete underwriting action or pricing modifier. This is the bridge between signal observation and premium.*

**Risk -> Underwriting Action & Base Rate**

| Tier | Score Band | Action | Rate / Method |
|------|-----------|--------|---------------|
| PREFERRED | 800-1000 | APPROVE | 0.12% (MULTIPLIER) |
| STANDARD_PLUS | 650-799 | APPROVE | 0.2% (MULTIPLIER) |
| STANDARD | 500-649 | REFER | 0.35% (MULTIPLIER) |
| SUBSTANDARD | 350-499 | REFER | 0.52% (MULTIPLIER) |
| DECLINE | 0-349 | DECLINE | 0.7% (MULTIPLIER) |

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

**Group Definitions:**
- **Product & Supply Chain Security:** Software product security, SDLC, supply chain, tenant isolation

*Reading the table: a group's three weights are independent. The same group can be a dominant driver of one pillar and a minor input to another — e.g. a group may carry most of the Exposure weight while contributing little to Risk.*

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

### Signal Detail by Group
> *Each signal is an objectively observable data point. The weights show how strongly that signal informs each assessment pillar; correlation direction indicates whether a higher observed value increases (+) or decreases (-) the assessed exposure.*

#### Product & Supply Chain Security
*Software product security, SDLC, supply chain, tenant isolation*

| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `secure_sdlc_maturity` | INFERRED_PROXY | 0.25 | 0.20 / 0.15 | 0.25 | + |
| `sbom_coverage` | INFERRED_PROXY | 0.15 | 0.15 / 0.00 | 0.20 | + |
| `tenant_isolation_strength` | INFERRED_PROXY | 0.20 | 0.00 / 0.25 | 0.40 | + |
| `dependency_vulnerability_exposure` | INFERRED_PROXY | 0.15 | 0.20 / 0.00 | 0.15 | + |
| `api_security_posture` | INFERRED_PROXY | 0.15 | 0.15 / 0.15 | 0.15 | + |
| `incident_notification_capability` | INFERRED_PROXY | 0.10 | 0.00 / 0.15 | 0.10 | + |

#### Public Record
| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `ai_incident_history` | DIRECT_OBSERVABLE | 0.05 | 0.04 / 0.04 | 0.00 | + |

#### Structured Data
| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `model_card_quality` | INFERRED_PROXY | 0.03 | 0.03 / 0.00 | 0.00 | - |
| `training_data_provenance` | INFERRED_PROXY | 0.03 | 0.00 / 0.03 | 0.00 | - |
| `ai_governance_disclosure` | INFERRED_PROXY | 0.03 | 0.03 / 0.00 | 0.00 | - |

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

### Three-Layer Pricing Translation
> *How each pillar's tier score becomes a concrete underwriting action or pricing modifier. This is the bridge between signal observation and premium.*

**Risk -> Underwriting Action & Base Rate**

| Tier | Score Band | Action | Rate / Method |
|------|-----------|--------|---------------|
| PREFERRED | 800-1000 | APPROVE | 0.11% (MULTIPLIER) |
| STANDARD_PLUS | 650-799 | APPROVE | 0.19% (MULTIPLIER) |
| STANDARD | 500-649 | REFER | 0.32% (MULTIPLIER) |
| SUBSTANDARD | 350-499 | REFER | 0.48% (MULTIPLIER) |
| DECLINE | 0-349 | DECLINE | 0.64% (MULTIPLIER) |

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

**Group Definitions:**
- **Platform User Security:** User data protection, content moderation, platform integrity

*Reading the table: a group's three weights are independent. The same group can be a dominant driver of one pillar and a minor input to another — e.g. a group may carry most of the Exposure weight while contributing little to Risk.*

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

### Signal Detail by Group
> *Each signal is an objectively observable data point. The weights show how strongly that signal informs each assessment pillar; correlation direction indicates whether a higher observed value increases (+) or decreases (-) the assessed exposure.*

#### Platform User Security
*User data protection, content moderation, platform integrity*

| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `user_authentication_strength` | INFERRED_PROXY | 0.25 | 0.20 / 0.00 | 0.15 | + |
| `data_retention_practices` | INFERRED_PROXY | 0.15 | 0.00 / 0.20 | 0.35 | + |
| `credential_breach_monitoring` | INFERRED_PROXY | 0.20 | 0.25 / 0.00 | 0.10 | + |
| `content_moderation_capability` | INFERRED_PROXY | 0.10 | 0.00 / 0.15 | 0.25 | + |
| `user_data_encryption` | INFERRED_PROXY | 0.15 | 0.00 / 0.15 | 0.20 | + |
| `third_party_data_sharing` | INFERRED_PROXY | 0.15 | 0.00 / 0.15 | 0.20 | + |

#### Public Record
| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `ai_incident_history` | DIRECT_OBSERVABLE | 0.04 | 0.04 / 0.04 | 0.00 | + |

#### Structured Data
| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `ai_governance_disclosure` | INFERRED_PROXY | 0.03 | 0.03 / 0.00 | 0.00 | - |

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

### Three-Layer Pricing Translation
> *How each pillar's tier score becomes a concrete underwriting action or pricing modifier. This is the bridge between signal observation and premium.*

**Risk -> Underwriting Action & Base Rate**

| Tier | Score Band | Action | Rate / Method |
|------|-----------|--------|---------------|
| PREFERRED | 800-1000 | APPROVE | 0.08% (MULTIPLIER) |
| STANDARD_PLUS | 650-799 | APPROVE | 0.15% (MULTIPLIER) |
| STANDARD | 500-649 | REFER | 0.25% (MULTIPLIER) |
| SUBSTANDARD | 350-499 | REFER | 0.38% (MULTIPLIER) |
| DECLINE | 0-349 | DECLINE | 0.5% (MULTIPLIER) |

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

**Group Definitions:**
- **Manufacturing Operations Security:** OT/IT convergence, production continuity, IP protection

*Reading the table: a group's three weights are independent. The same group can be a dominant driver of one pillar and a minor input to another — e.g. a group may carry most of the Exposure weight while contributing little to Risk.*

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

### Signal Detail by Group
> *Each signal is an objectively observable data point. The weights show how strongly that signal informs each assessment pillar; correlation direction indicates whether a higher observed value increases (+) or decreases (-) the assessed exposure.*

#### Manufacturing Operations Security
*OT/IT convergence, production continuity, IP protection*

| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `production_ot_segmentation` | INFERRED_PROXY | 0.25 | 0.15 / 0.20 | 0.30 | + |
| `production_recovery_capability` | INFERRED_PROXY | 0.15 | 0.00 / 0.25 | 0.15 | + |
| `ip_protection_controls` | INFERRED_PROXY | 0.15 | 0.00 / 0.20 | 0.20 | + |
| `supply_chain_digital_risk` | INFERRED_PROXY | 0.20 | 0.15 / 0.00 | 0.35 | + |
| `ransomware_preparedness` | INFERRED_PROXY | 0.25 | 0.25 / 0.15 | 0.10 | + |

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

### Three-Layer Pricing Translation
> *How each pillar's tier score becomes a concrete underwriting action or pricing modifier. This is the bridge between signal observation and premium.*

**Risk -> Underwriting Action & Base Rate**

| Tier | Score Band | Action | Rate / Method |
|------|-----------|--------|---------------|
| PREFERRED | 800-1000 | APPROVE | 0.1% (MULTIPLIER) |
| STANDARD_PLUS | 650-799 | APPROVE | 0.18% (MULTIPLIER) |
| STANDARD | 500-649 | REFER | 0.3% (MULTIPLIER) |
| SUBSTANDARD | 350-499 | REFER | 0.45% (MULTIPLIER) |
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

**Group Definitions:**
- **Retail Operations Security:** PCI compliance, payment security, e-commerce, store networks

*Reading the table: a group's three weights are independent. The same group can be a dominant driver of one pillar and a minor input to another — e.g. a group may carry most of the Exposure weight while contributing little to Risk.*

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

### Signal Detail by Group
> *Each signal is an objectively observable data point. The weights show how strongly that signal informs each assessment pillar; correlation direction indicates whether a higher observed value increases (+) or decreases (-) the assessed exposure.*

#### Retail Operations Security
*PCI compliance, payment security, e-commerce, store networks*

| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `point_to_point_encryption` | INFERRED_PROXY | 0.20 | 0.20 / 0.15 | 0.15 | + |
| `ecommerce_security_posture` | INFERRED_PROXY | 0.20 | 0.15 / 0.15 | 0.35 | + |
| `store_network_isolation` | INFERRED_PROXY | 0.20 | 0.15 / 0.00 | 0.35 | + |
| `loyalty_data_protection` | INFERRED_PROXY | 0.15 | 0.00 / 0.20 | 0.20 | + |
| `pci_assessment_status` | DIRECT_OBSERVABLE | 0.15 | 0.15 / 0.10 | 0.15 | + |
| `access_provisioning_automation` | INFERRED_PROXY | 0.10 | 0.15 / 0.00 | 0.15 | + |

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

### Three-Layer Pricing Translation
> *How each pillar's tier score becomes a concrete underwriting action or pricing modifier. This is the bridge between signal observation and premium.*

**Risk -> Underwriting Action & Base Rate**

| Tier | Score Band | Action | Rate / Method |
|------|-----------|--------|---------------|
| PREFERRED | 800-1000 | APPROVE | 0.08% (MULTIPLIER) |
| STANDARD_PLUS | 650-799 | APPROVE | 0.13% (MULTIPLIER) |
| STANDARD | 500-649 | REFER | 0.22% (MULTIPLIER) |
| SUBSTANDARD | 350-499 | REFER | 0.33% (MULTIPLIER) |
| DECLINE | 0-349 | DECLINE | 0.44% (MULTIPLIER) |

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

**Group Definitions:**
- **Public Sector Cyber Posture:** Government/education cyber security, essential services, legacy systems

*Reading the table: a group's three weights are independent. The same group can be a dominant driver of one pillar and a minor input to another — e.g. a group may carry most of the Exposure weight while contributing little to Risk.*

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

### Signal Detail by Group
> *Each signal is an objectively observable data point. The weights show how strongly that signal informs each assessment pillar; correlation direction indicates whether a higher observed value increases (+) or decreases (-) the assessed exposure.*

#### Public Sector Cyber Posture
*Government/education cyber security, essential services, legacy systems*

| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `essential_services_continuity` | INFERRED_PROXY | 0.20 | 0.00 / 0.25 | 0.20 | + |
| `legacy_system_exposure` | INFERRED_PROXY | 0.25 | 0.25 / 0.00 | 0.25 | + |
| `ms_isac_participation` | DIRECT_OBSERVABLE | 0.15 | 0.10 / 0.00 | 0.10 | + |
| `citizen_data_volume` | INFERRED_PROXY | 0.10 | 0.00 / 0.20 | 0.30 | + |
| `ransomware_payment_governance` | INFERRED_PROXY | 0.15 | 0.00 / 0.15 | 0.15 | + |
| `cyber_incident_response_maturity` | INFERRED_PROXY | 0.15 | 0.15 / 0.15 | 0.00 | + |

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

### Three-Layer Pricing Translation
> *How each pillar's tier score becomes a concrete underwriting action or pricing modifier. This is the bridge between signal observation and premium.*

**Risk -> Underwriting Action & Base Rate**

| Tier | Score Band | Action | Rate / Method |
|------|-----------|--------|---------------|
| PREFERRED | 800-1000 | APPROVE | 0.06% (MULTIPLIER) |
| STANDARD_PLUS | 650-799 | APPROVE | 0.11% (MULTIPLIER) |
| STANDARD | 500-649 | REFER | 0.18% (MULTIPLIER) |
| SUBSTANDARD | 350-499 | REFER | 0.27% (MULTIPLIER) |
| DECLINE | 0-349 | DECLINE | 0.36% (MULTIPLIER) |

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

**Group Definitions:**
- **Professional Data Security:** Client confidentiality, ethical walls, privileged communication

*Reading the table: a group's three weights are independent. The same group can be a dominant driver of one pillar and a minor input to another — e.g. a group may carry most of the Exposure weight while contributing little to Risk.*

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

### Signal Detail by Group
> *Each signal is an objectively observable data point. The weights show how strongly that signal informs each assessment pillar; correlation direction indicates whether a higher observed value increases (+) or decreases (-) the assessed exposure.*

#### Professional Data Security
*Client confidentiality, ethical walls, privileged communication*

| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `client_data_classification` | INFERRED_PROXY | 0.20 | 0.00 / 0.20 | 0.30 | + |
| `ethical_wall_capability` | INFERRED_PROXY | 0.15 | 0.00 / 0.15 | 0.25 | + |
| `email_security_posture` | DIRECT_OBSERVABLE | 0.20 | 0.25 / 0.00 | 0.10 | + |
| `client_data_encryption_at_rest` | INFERRED_PROXY | 0.15 | 0.00 / 0.20 | 0.15 | + |
| `wire_transfer_controls` | INFERRED_PROXY | 0.15 | 0.20 / 0.20 | 0.00 | + |
| `remote_access_security` | INFERRED_PROXY | 0.15 | 0.15 / 0.00 | 0.15 | + |

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

### Three-Layer Pricing Translation
> *How each pillar's tier score becomes a concrete underwriting action or pricing modifier. This is the bridge between signal observation and premium.*

**Risk -> Underwriting Action & Base Rate**

| Tier | Score Band | Action | Rate / Method |
|------|-----------|--------|---------------|
| PREFERRED | 800-1000 | APPROVE | 0.08% (MULTIPLIER) |
| STANDARD_PLUS | 650-799 | APPROVE | 0.13% (MULTIPLIER) |
| STANDARD | 500-649 | REFER | 0.22% (MULTIPLIER) |
| SUBSTANDARD | 350-499 | REFER | 0.33% (MULTIPLIER) |
| DECLINE | 0-349 | DECLINE | 0.44% (MULTIPLIER) |

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

**Group Definitions:**
- **AI Governance & Documentation:** Model cards, data provenance, governance policy, responsible-AI posture
- **AI Incident Record:** AIIDR + regulator-published incident history for the vendor
- **Vendor Security Posture:** Secure SDLC, email hygiene, remote-access controls

*Reading the table: a group's three weights are independent. The same group can be a dominant driver of one pillar and a minor input to another — e.g. a group may carry most of the Exposure weight while contributing little to Risk.*

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

### Signal Detail by Group
> *Each signal is an objectively observable data point. The weights show how strongly that signal informs each assessment pillar; correlation direction indicates whether a higher observed value increases (+) or decreases (-) the assessed exposure.*

#### AI Governance & Documentation
*Model cards, data provenance, governance policy, responsible-AI posture*

| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `model_card_quality` | INFERRED_PROXY | 0.18 | 0.15 / 0.00 | 0.00 | - |
| `training_data_provenance` | INFERRED_PROXY | 0.14 | 0.00 / 0.18 | 0.00 | - |
| `ai_governance_disclosure` | INFERRED_PROXY | 0.13 | 0.12 / 0.00 | 0.00 | - |

#### AI Incident Record
*AIIDR + regulator-published incident history for the vendor*

| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `ai_incident_history` | DIRECT_OBSERVABLE | 0.20 | 0.20 / 0.18 | 0.00 | + |

#### Vendor Security Posture
*Secure SDLC, email hygiene, remote-access controls*

| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `secure_sdlc_maturity` | INFERRED_PROXY | 0.15 | 0.15 / 0.00 | 0.00 | - |
| `email_security_posture` | DIRECT_OBSERVABLE | 0.12 | 0.12 / 0.00 | 0.00 | + |
| `remote_access_security` | INFERRED_PROXY | 0.08 | 0.08 / 0.00 | 0.00 | + |

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

### Three-Layer Pricing Translation
> *How each pillar's tier score becomes a concrete underwriting action or pricing modifier. This is the bridge between signal observation and premium.*

**Risk -> Underwriting Action & Base Rate**

| Tier | Score Band | Action | Rate / Method |
|------|-----------|--------|---------------|
| PREFERRED | 800-1000 | APPROVE | 0.12% (MULTIPLIER) |
| STANDARD_PLUS | 650-799 | APPROVE | 0.2% (MULTIPLIER) |
| STANDARD | 500-649 | REFER | 0.32% (MULTIPLIER) |
| SUBSTANDARD | 350-499 | REFER | 0.48% (MULTIPLIER) |
| DECLINE | 0-349 | DECLINE | 0.65% (MULTIPLIER) |

**Loss -> Frequency & Severity Modifiers**

| Tier | Score Band | Frequency Modifier | Severity Modifier |
|------|-----------|--------------------|-------------------|
| VERY_LOW | 80-100 | 0.7 | 0.8 |
| LOW | 60-79 | 0.85 | 0.9 |
| MODERATE | 40-59 | 1.0 | 1.0 |
| ELEVATED | 20-39 | 1.2 | 1.2 |
| HIGH | 0-19 | 1.45 | 1.5 |

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

**1. The Pricing Anchor:** The Base Rate of `0.32%` on `revenue` purchases exactly a `$10,000,000` Limit with a `$50,000` Deductible.
**2. Theoretical Execution:**
  - Assume `revenue` = $10,000,000
  - Base Premium = $10,000,000 × 0.0032 = **$32,000**
  - If the client requests the Anchor Limit/Deductible, the factors are 1.00, resulting in a technical premium of **$32,000**.

---

## Model: `cyber_saas_platform`
*Multi-tenant SaaS platforms — B2B + B2C SaaS, PaaS, DBaaS providers*

### Routing Protocol (Multiplexer)
- `industry_sector in ['SAAS', 'PAAS', 'DBAAS', 'MULTI_TENANT_PLATFORM']`

### Three-Layer Weight Distribution
> *DSI requires that weights for Risk, Loss, and Exposure each sum to 1.0 across all signal groups.*

**Validation:** PASS

| Group | Risk | Loss | Exposure |
|-------|------|------|----------|
| Technical Security Posture | 0.45 | 0.40 | 0.35 |
| Compliance & Customer Quality | 0.20 | 0.20 | 0.25 |
| Breach & Litigation Record | 0.25 | 0.30 | 0.25 |
| Network Authority | 0.05 | 0.05 | 0.05 |
| Corporate Footprint | 0.05 | 0.05 | 0.10 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

**Group Definitions:**
- **Technical Security Posture:** Secure SDLC, email, remote access, credentials, DNS/TLS hygiene
- **Compliance & Customer Quality:** Compliance badges, customer-quality segment
- **Breach & Litigation Record:** Breach history, regulator actions, class-action exposure

*Reading the table: a group's three weights are independent. The same group can be a dominant driver of one pillar and a minor input to another — e.g. a group may carry most of the Exposure weight while contributing little to Risk.*

### Signal Architecture Rationale
This configuration contains **7 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `DIRECT_OBSERVABLE` (3 signals): Highest confidence
- `INFERRED_PROXY` (4 signals): Medium confidence

**Signal Count by Group:**
- `technical_infrastructure`: 4 signals
- `structured_data`: 2 signals
- `public_record`: 1 signals

**Selection Rationale:**
- 43% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Detail by Group
> *Each signal is an objectively observable data point. The weights show how strongly that signal informs each assessment pillar; correlation direction indicates whether a higher observed value increases (+) or decreases (-) the assessed exposure.*

#### Technical Security Posture
*Secure SDLC, email, remote access, credentials, DNS/TLS hygiene*

| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `secure_sdlc_maturity` | INFERRED_PROXY | 0.20 | 0.18 / 0.00 | 0.00 | - |
| `email_security_posture` | DIRECT_OBSERVABLE | 0.12 | 0.10 / 0.00 | 0.00 | + |
| `remote_access_security` | INFERRED_PROXY | 0.12 | 0.12 / 0.00 | 0.00 | + |
| `credential_exposure` | DIRECT_OBSERVABLE | 0.15 | 0.18 / 0.00 | 0.00 | + |

#### Compliance & Customer Quality
*Compliance badges, customer-quality segment*

| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `compliance_badges` | INFERRED_PROXY | 0.18 | 0.00 / 0.18 | 0.00 | - |
| `customer_quality` | INFERRED_PROXY | 0.05 | 0.00 / 0.00 | 0.00 | - |

#### Breach & Litigation Record
*Breach history, regulator actions, class-action exposure*

| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `breach_history` | DIRECT_OBSERVABLE | 0.18 | 0.15 / 0.18 | 0.00 | + |

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 | Technical Security Posture | 1.20 | 0.45 | 0.40 | 0.35 |
| 2 | Breach & Litigation Record | 0.80 | 0.25 | 0.30 | 0.25 |
| 3 | Compliance & Customer Quality | 0.65 | 0.20 | 0.20 | 0.25 |
| 4 | Corporate Footprint | 0.20 | 0.05 | 0.05 | 0.10 |
| 5 | Network Authority | 0.15 | 0.05 | 0.05 | 0.05 |

**Primary Assessment Driver:** `Technical Security Posture` with combined weight of 1.20
**Secondary Driver:** `Breach & Litigation Record` with combined weight of 0.80

### Three-Layer Pricing Translation
> *How each pillar's tier score becomes a concrete underwriting action or pricing modifier. This is the bridge between signal observation and premium.*

**Risk -> Underwriting Action & Base Rate**

| Tier | Score Band | Action | Rate / Method |
|------|-----------|--------|---------------|
| PREFERRED | 800-1000 | APPROVE | 0.1% (MULTIPLIER) |
| STANDARD_PLUS | 650-799 | APPROVE | 0.18% (MULTIPLIER) |
| STANDARD | 500-649 | REFER | 0.3% (MULTIPLIER) |
| SUBSTANDARD | 350-499 | REFER | 0.46% (MULTIPLIER) |
| DECLINE | 0-349 | DECLINE | 0.62% (MULTIPLIER) |

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

**1. The Pricing Anchor:** The Base Rate of `0.3%` on `revenue` purchases exactly a `$10,000,000` Limit with a `$100,000` Deductible.
**2. Theoretical Execution:**
  - Assume `revenue` = $10,000,000
  - Base Premium = $10,000,000 × 0.003 = **$30,000**
  - If the client requests the Anchor Limit/Deductible, the factors are 1.00, resulting in a technical premium of **$30,000**.

---

## Model: `cyber_media_tech`
*Media platforms, CMS vendors, video / audio streaming, publishing-tech*

### Routing Protocol (Multiplexer)
- `industry_sector in ['MEDIA', 'PUBLISHING', 'STREAMING', 'CONTENT_PLATFORM']`

### Three-Layer Weight Distribution
> *DSI requires that weights for Risk, Loss, and Exposure each sum to 1.0 across all signal groups.*

**Validation:** PASS

| Group | Risk | Loss | Exposure |
|-------|------|------|----------|
| Moderation & Governance | 0.35 | 0.35 | 0.30 |
| Legal & Reputational Record | 0.35 | 0.40 | 0.30 |
| Platform Security Posture | 0.20 | 0.15 | 0.30 |
| Network Authority | 0.05 | 0.05 | 0.05 |
| Corporate Footprint | 0.05 | 0.05 | 0.05 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

**Group Definitions:**
- **Moderation & Governance:** Content moderation, transparency, DMCA workflow
- **Legal & Reputational Record:** Defamation suits, breach record, class-action exposure
- **Platform Security Posture:** SDLC, email hygiene, remote-access + DNS/TLS surface

*Reading the table: a group's three weights are independent. The same group can be a dominant driver of one pillar and a minor input to another — e.g. a group may carry most of the Exposure weight while contributing little to Risk.*

### Signal Architecture Rationale
This configuration contains **5 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `DIRECT_OBSERVABLE` (2 signals): Highest confidence
- `INFERRED_PROXY` (3 signals): Medium confidence

**Signal Count by Group:**
- `public_record`: 2 signals
- `technical_infrastructure`: 2 signals
- `structured_data`: 1 signals

**Selection Rationale:**
- 40% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Detail by Group
> *Each signal is an objectively observable data point. The weights show how strongly that signal informs each assessment pillar; correlation direction indicates whether a higher observed value increases (+) or decreases (-) the assessed exposure.*

#### Moderation & Governance
*Content moderation, transparency, DMCA workflow*

| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `content_moderation_posture` | INFERRED_PROXY | 0.20 | 0.18 / 0.00 | 0.00 | - |

#### Legal & Reputational Record
*Defamation suits, breach record, class-action exposure*

| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `defamation_exposure` | INFERRED_PROXY | 0.18 | 0.00 / 0.22 | 0.00 | + |
| `breach_history` | DIRECT_OBSERVABLE | 0.15 | 0.12 / 0.12 | 0.00 | + |

#### Platform Security Posture
*SDLC, email hygiene, remote-access + DNS/TLS surface*

| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `secure_sdlc_maturity` | INFERRED_PROXY | 0.15 | 0.15 / 0.00 | 0.00 | - |
| `email_security_posture` | DIRECT_OBSERVABLE | 0.10 | 0.10 / 0.00 | 0.00 | + |

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 | Legal & Reputational Record | 1.05 | 0.35 | 0.40 | 0.30 |
| 2 | Moderation & Governance | 1.00 | 0.35 | 0.35 | 0.30 |
| 3 | Platform Security Posture | 0.65 | 0.20 | 0.15 | 0.30 |
| 4 | Network Authority | 0.15 | 0.05 | 0.05 | 0.05 |
| 5 | Corporate Footprint | 0.15 | 0.05 | 0.05 | 0.05 |

**Primary Assessment Driver:** `Legal & Reputational Record` with combined weight of 1.05
**Secondary Driver:** `Moderation & Governance` with combined weight of 1.00

### Three-Layer Pricing Translation
> *How each pillar's tier score becomes a concrete underwriting action or pricing modifier. This is the bridge between signal observation and premium.*

**Risk -> Underwriting Action & Base Rate**

| Tier | Score Band | Action | Rate / Method |
|------|-----------|--------|---------------|
| PREFERRED | 800-1000 | APPROVE | 0.1% (MULTIPLIER) |
| STANDARD_PLUS | 650-799 | APPROVE | 0.18% (MULTIPLIER) |
| STANDARD | 500-649 | REFER | 0.3% (MULTIPLIER) |
| SUBSTANDARD | 350-499 | REFER | 0.46% (MULTIPLIER) |
| DECLINE | 0-349 | DECLINE | 0.62% (MULTIPLIER) |

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

**1. The Pricing Anchor:** The Base Rate of `0.3%` on `revenue` purchases exactly a `$10,000,000` Limit with a `$100,000` Deductible.
**2. Theoretical Execution:**
  - Assume `revenue` = $10,000,000
  - Base Premium = $10,000,000 × 0.003 = **$30,000**
  - If the client requests the Anchor Limit/Deductible, the factors are 1.00, resulting in a technical premium of **$30,000**.


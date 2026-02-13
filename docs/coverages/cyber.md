# Cyber Coverage Configuration

**Coverage ID:** `cyber`
**Generated:** 2026-02-13 13:34
**Schema Version:** v2.2

This document describes the configuration, decision logic, and pricing structure
for the Cyber coverage vertical in the DSI platform.

## Table of Contents

1. [Configuration Overview](#configuration-overview)
2. [Signal Groups](#signal-groups)
3. [Scoring Logic](#scoring-logic)
4. [Pricing Structure](#pricing-structure)
5. [Direct Queries](#direct-queries)
6. [Decision Flow](#decision-flow)


---


## Configuration: Cyber General

### Metadata

- **Name:** DSI Cyber Technical Pricing Model
- **Version:** 2.3.0
- **Description:** Cyber liability model based on externally observable technical signals
- **Product Types:** `cyber_liability`, `network_security`, `privacy_liability`, `cyber_extortion`
- **Markets:** US, UK, EU, APAC
- **Minimum Premium:** $5,000
- **Currency:** USD

#### Multiplexer Configuration (V4)

- **Model Specificity:** 1 (General)
- **Routing Constraints:**
  - `revenue > 50000000` (required)

### Signal Registry

**Total Signals:** 44


#### Group: `corporate_footprint`

| Signal ID | Type | Weight | Direction | Proxy Tier |
|-----------|------|--------|-----------|------------|
| `security_page_presence` | Scoring | 12.00% | positive | DIRECT_OBSERVABLE |
| `privacy_policy_presence` | Scoring | 8.00% | positive | DIRECT_OBSERVABLE |
| `security_txt_presence` | Scoring | 6.00% | positive | DIRECT_OBSERVABLE |
| `bug_bounty_presence` | Scoring | 12.00% | positive | DIRECT_OBSERVABLE |
| `security_hiring_activity` | Scoring | 10.00% | positive | INFERRED_PROXY |
| `technical_content_quality` | Scoring | 6.00% | positive | INFERRED_PROXY |
| `developer_resources` | Scoring | 6.00% | positive | INFERRED_PROXY |
| `security_leadership_presence` | Scoring | 12.00% | positive | INFERRED_PROXY |
| `compliance_badges` | Scoring | 8.00% | positive | DIRECT_OBSERVABLE |
| `dns_complexity` | Scoring | 5.00% | negative | DIRECT_OBSERVABLE |
| `subdomain_count` | Scoring | 5.00% | negative | DIRECT_OBSERVABLE |
| `ip_footprint` | Scoring | 5.00% | negative | DIRECT_OBSERVABLE |
| `ssl_certificate_count` | Scoring | 5.00% | positive | DIRECT_OBSERVABLE |
| `job_posting_volume` | Scoring | 5.00% | positive | INFERRED_PROXY |
| `funding_signals` | Scoring | 5.00% | positive | INFERRED_PROXY |

#### Group: `geography`

| Signal ID | Type | Weight | Direction | Proxy Tier |
|-----------|------|--------|-----------|------------|
| `geography` | Categorical | N/A | modifier | INFERRED_PROXY |

#### Group: `industry_classification`

| Signal ID | Type | Weight | Direction | Proxy Tier |
|-----------|------|--------|-----------|------------|
| `industry_classification` | Categorical | N/A | modifier | INFERRED_PROXY |

#### Group: `network_authority`

| Signal ID | Type | Weight | Direction | Proxy Tier |
|-----------|------|--------|-----------|------------|
| `security_vendor_presence` | Scoring | 25.00% | positive | INFERRED_PROXY |
| `customer_quality` | Scoring | 15.00% | positive | INFERRED_PROXY |
| `partner_quality` | Scoring | 10.00% | positive | INFERRED_PROXY |
| `industry_body_membership` | Scoring | 15.00% | positive | INFERRED_PROXY |
| `certification_authority_presence` | Scoring | 15.00% | positive | INFERRED_PROXY |
| `financial_relationships` | Scoring | 5.00% | positive | INFERRED_PROXY |
| `network_centrality` | Scoring | 10.00% | positive | INFERRED_PROXY |
| `second_degree_connections` | Scoring | 5.00% | positive | INFERRED_PROXY |

#### Group: `public_record`

| Signal ID | Type | Weight | Direction | Proxy Tier |
|-----------|------|--------|-----------|------------|
| `breach_history` | Scoring | 35.00% | positive | DIRECT_OBSERVABLE |
| `regulatory_actions` | Scoring | 25.00% | positive | DIRECT_OBSERVABLE |
| `litigation_history` | Scoring | 20.00% | positive | DIRECT_OBSERVABLE |
| `credential_exposure` | Scoring | 20.00% | positive | DIRECT_OBSERVABLE |
| `dark_web_presence` | Scoring | 20.00% | positive | INFERRED_PROXY |

#### Group: `size_band`

| Signal ID | Type | Weight | Direction | Proxy Tier |
|-----------|------|--------|-----------|------------|
| `size_band` | Categorical | N/A | modifier | INFERRED_PROXY |

#### Group: `structured_data`

| Signal ID | Type | Weight | Direction | Proxy Tier |
|-----------|------|--------|-----------|------------|
| `security_rating` | Scoring | 40.00% | positive | DIRECT_OBSERVABLE |
| `esg_cyber_alignment` | Scoring | 30.00% | positive | INFERRED_PROXY |
| `credit_rating` | Scoring | 30.00% | positive | DIRECT_OBSERVABLE |

#### Group: `technical_infrastructure`

| Signal ID | Type | Weight | Direction | Proxy Tier |
|-----------|------|--------|-----------|------------|
| `tls_configuration` | Scoring | 12.00% | positive | DIRECT_OBSERVABLE |
| `security_headers` | Scoring | 10.00% | positive | DIRECT_OBSERVABLE |
| `email_authentication` | Scoring | 12.00% | positive | DIRECT_OBSERVABLE |
| `dnssec_status` | Scoring | 5.00% | positive | DIRECT_OBSERVABLE |
| `network_exposure` | Scoring | 18.00% | positive | DIRECT_OBSERVABLE |
| `software_currency` | Scoring | 10.00% | positive | INFERRED_PROXY |
| `cve_exposure` | Scoring | 18.00% | positive | DIRECT_OBSERVABLE |
| `cloud_infrastructure` | Scoring | 5.00% | positive | INFERRED_PROXY |
| `waf_presence` | Scoring | 5.00% | positive | DIRECT_OBSERVABLE |
| `cdn_usage` | Scoring | 5.00% | positive | DIRECT_OBSERVABLE |

### Signal Groups

#### Categorical Groups

These groups apply modifiers based on classification:

| Group ID | Label | Impact | Default |
|----------|-------|--------|---------|
| `industry_classification` | Industry Classification | MODIFIER | OTHER |
| `size_band` | Size Band | MODIFIER | OTHER |
| `geography` | Geography | MODIFIER | OTHER |

#### Three-Layer Assessment Groups

These groups contribute to Risk, Loss, and Exposure scoring:

| Group ID | Risk Weight | Loss Weight | Exposure Weight |
|----------|-------------|-------------|-----------------|
| `network_authority` | 15% | 15% | 15% |
| `technical_infrastructure` | 35% | 35% | 35% |
| `corporate_footprint` | 15% | 25% | 25% |
| `public_record` | 25% | 15% | 15% |
| `structured_data` | 10% | 10% | 10% |

### Risk Tier Bands

Risk tiers determine the base pricing and underwriting action:

| Tier | Label | Score Range | Action | Base Premium |
|------|-------|-------------|--------|--------------|
| 1 | PREFERRED | 800-1000 | APPROVE | 0.001x |
| 2 | STANDARD_PLUS | 650-799 | APPROVE | 0.0015x |
| 3 | STANDARD | 500-649 | REFER | 0.0025x |
| 4 | SUBSTANDARD | 350-499 | REFER | 0.004x |
| 5 | DECLINE | 0-349 | DECLINE | 0.01x |

**Decision Logic:**
- Scores 0-1000 (composite from weighted signals)
- Higher scores = better risk = lower tier number
- APPROVE: Automatic binding eligible
- REFER: Requires underwriter review
- DECLINE: Outside risk appetite

### Loss Tier Bands

Loss tiers adjust premium based on expected loss frequency and severity:

| Tier | Label | Score Range | Freq Modifier | Sev Modifier |
|------|-------|-------------|---------------|--------------|
| 1 | VERY_LOW | 80-100 | 0.70x | 0.80x |
| 2 | LOW | 60-79 | 0.85x | 0.90x |
| 3 | MODERATE | 40-59 | 1.00x | 1.00x |
| 4 | ELEVATED | 20-39 | 1.15x | 1.15x |
| 5 | HIGH | 0-19 | 1.35x | 1.40x |

**Constraints:** Floor = 0.55, Cap = 1.60

### Direct Queries

Binary questions that cannot be inferred from external signals:

| Query ID | Question | Trigger | Action | Impact |
|----------|----------|---------|--------|--------|
| `mfa_enabled` | Is multi-factor authentication enabled for all rem... | Answer = False | REFER | Override to Tier 4 |
| `security_training` | Do all employees complete annual cyber security tr... | Answer = False | REFER | Override to Tier 4 |
| `phi_handler` | Do you process Protected Health Information (PHI)? | Answer = True | MODIFIER | Modifier: 1.25x |
| `pci_scope` | Do you store payment card data (PCI scope)? | Answer = True | MODIFIER | Modifier: 1.15x |
| `incident_response_plan` | Do you have a documented incident response plan? | Answer = False | FLAG | No IR plan - extended breach impact likely |
| `edr_deployed` | Is endpoint detection and response (EDR) deployed ... | Answer = False | FLAG | No EDR - reduced threat detection |
| `immutable_backups` | Are backups maintained offline or immutable? | Answer = False | FLAG | No immutable backups - ransomware recovery risk |
| `recent_incident` | Have you experienced a material cyber incident in ... | Answer = True | REFER | Override to Tier 4 |

**Action Types:**
- **FLAG:** Adds note to underwriter; no pricing impact
- **MODIFIER:** Applies premium multiplier
- **REFER:** Forces underwriter review regardless of score

### Pricing Structure

Pricing varies by product type:


#### Cyber Liability

**Pricing Anchors (V5):**
- Base Limit Reference: $1,000,000
- Base Deductible Reference: $50,000

**Increased Limit Factors (ILF):**

| Limit | Factor | Premium Multiplier |
|-------|--------|-------------------|
| $1,000,000 (base) | 1.00 | 1.00x base |
| $2,000,000 | 1.75 | 1.75x base |
| $5,000,000 | 3.40 | 3.40x base |
| $10,000,000 | 5.50 | 5.50x base |
| $25,000,000 | 10.00 | 10.00x base |
| $50,000,000 | 16.00 | 16.00x base |
| $100,000,000 | 25.00 | 25.00x base |

**Deductible Factors (V5):**

| Deductible | Factor | Effect |
|------------|--------|--------|
| $10,000 | 1.50 | +50% loading |
| $25,000 | 1.15 | +15% loading |
| $50,000 (anchor) | 1.00 | Base price |
| $100,000 | 0.95 | -5% credit |
| $250,000 | 0.90 | -10% credit |
| $500,000 | 0.70 | -30% credit |
| $1,000,000 | 0.70 | -30% credit |


#### Network Security

**Pricing Anchors (V5):**
- Base Limit Reference: $1,000,000
- Base Deductible Reference: $50,000

**Increased Limit Factors (ILF):**

| Limit | Factor | Premium Multiplier |
|-------|--------|-------------------|
| $1,000,000 (base) | 1.00 | 1.00x base |
| $2,000,000 | 1.65 | 1.65x base |
| $5,000,000 | 3.00 | 3.00x base |
| $10,000,000 | 4.50 | 4.50x base |
| $25,000,000 | 8.00 | 8.00x base |
| $50,000,000 | 12.50 | 12.50x base |
| $100,000,000 | 19.00 | 19.00x base |

**Deductible Factors (V5):**

| Deductible | Factor | Effect |
|------------|--------|--------|
| $10,000 | 1.50 | +50% loading |
| $25,000 | 1.15 | +15% loading |
| $50,000 (anchor) | 1.00 | Base price |
| $100,000 | 0.95 | -5% credit |
| $250,000 | 0.92 | -8% credit |
| $500,000 | 0.70 | -30% credit |
| $1,000,000 | 0.70 | -30% credit |


#### Privacy Liability

**Pricing Anchors (V5):**
- Base Limit Reference: $1,000,000
- Base Deductible Reference: $50,000

**Increased Limit Factors (ILF):**

| Limit | Factor | Premium Multiplier |
|-------|--------|-------------------|
| $1,000,000 (base) | 1.00 | 1.00x base |
| $2,000,000 | 1.60 | 1.60x base |
| $5,000,000 | 2.80 | 2.80x base |
| $10,000,000 | 4.20 | 4.20x base |
| $25,000,000 | 7.50 | 7.50x base |
| $50,000,000 | 11.50 | 11.50x base |
| $100,000,000 | 17.00 | 17.00x base |

**Deductible Factors (V5):**

| Deductible | Factor | Effect |
|------------|--------|--------|
| $10,000 | 1.50 | +50% loading |
| $25,000 | 1.15 | +15% loading |
| $50,000 (anchor) | 1.00 | Base price |
| $100,000 | 0.96 | -4% credit |
| $250,000 | 0.92 | -8% credit |
| $500,000 | 0.70 | -30% credit |
| $1,000,000 | 0.70 | -30% credit |


#### Cyber Extortion

**Pricing Anchors (V5):**
- Base Limit Reference: $1,000,000
- Base Deductible Reference: $50,000

**Increased Limit Factors (ILF):**

| Limit | Factor | Premium Multiplier |
|-------|--------|-------------------|
| $1,000,000 (base) | 1.00 | 1.00x base |
| $2,000,000 | 1.85 | 1.85x base |
| $5,000,000 | 3.80 | 3.80x base |
| $10,000,000 | 6.50 | 6.50x base |
| $25,000,000 | 12.00 | 12.00x base |
| $50,000,000 | 20.00 | 20.00x base |
| $100,000,000 | 32.00 | 32.00x base |

**Deductible Factors (V5):**

| Deductible | Factor | Effect |
|------------|--------|--------|
| $10,000 | 1.50 | +50% loading |
| $25,000 | 1.15 | +15% loading |
| $50,000 (anchor) | 1.00 | Base price |
| $100,000 | 0.94 | -6% credit |
| $250,000 | 0.88 | -12% credit |
| $500,000 | 0.70 | -30% credit |
| $1,000,000 | 0.70 | -30% credit |


### Limit Bandings

Pre-configured limit/deductible packages:

| Package | Limit | Deductible |
|---------|-------|------------|
| 1 | $1,000,000 | $25,000 |
| 2 | $5,000,000 | $50,000 |
| 3 | $10,000,000 | $100,000 |
| 4 | $25,000,000 | $250,000 |
| 5 | $50,000,000 | $500,000 |


---


## Configuration: Cyber Sme

### Metadata

- **Name:** Cyber SME Automated Pricing Model
- **Version:** 2.3.0
- **Description:** Cyber liability model for SME segment - automated underwriting for small businesses
- **Product Types:** `cyber_liability`, `network_security`
- **Markets:** US, UK
- **Minimum Premium:** $2,500
- **Currency:** USD

#### Multiplexer Configuration (V4)

- **Model Specificity:** 2 (Segment)
- **Routing Constraints:**
  - `revenue <= 50000000` (required)
  - `limit <= 5000000` (required)

### Signal Registry

**Total Signals:** 7


#### Group: `company_size`

| Signal ID | Type | Weight | Direction | Proxy Tier |
|-----------|------|--------|-----------|------------|
| `company_size` | Categorical | N/A | modifier | DIRECT_OBSERVABLE |

#### Group: `industry_classification`

| Signal ID | Type | Weight | Direction | Proxy Tier |
|-----------|------|--------|-----------|------------|
| `industry_classification` | Categorical | N/A | modifier | DIRECT_OBSERVABLE |

#### Group: `public_record`

| Signal ID | Type | Weight | Direction | Proxy Tier |
|-----------|------|--------|-----------|------------|
| `breach_history` | Scoring | 50.00% | negative | DIRECT_OBSERVABLE |
| `security_rating` | Scoring | 50.00% | positive | INFERRED_PROXY |

#### Group: `technical_security`

| Signal ID | Type | Weight | Direction | Proxy Tier |
|-----------|------|--------|-----------|------------|
| `tls_configuration` | Scoring | 35.00% | positive | DIRECT_OBSERVABLE |
| `email_authentication` | Scoring | 35.00% | positive | DIRECT_OBSERVABLE |
| `security_headers` | Scoring | 30.00% | positive | DIRECT_OBSERVABLE |

### Signal Groups

#### Categorical Groups

These groups apply modifiers based on classification:

| Group ID | Label | Impact | Default |
|----------|-------|--------|---------|
| `industry_classification` | Industry Classification | MODIFIER | OTHER |
| `company_size` | Company Size | MODIFIER | SMALL |

#### Three-Layer Assessment Groups

These groups contribute to Risk, Loss, and Exposure scoring:

| Group ID | Risk Weight | Loss Weight | Exposure Weight |
|----------|-------------|-------------|-----------------|
| `technical_security` | 60% | 55% | 45% |
| `public_record` | 40% | 45% | 55% |

### Risk Tier Bands

Risk tiers determine the base pricing and underwriting action:

| Tier | Label | Score Range | Action | Base Premium |
|------|-------|-------------|--------|--------------|
| 1 | PREFERRED | 800-1000 | APPROVE | $0 |
| 2 | STANDARD_PLUS | 650-799 | APPROVE | $0 |
| 3 | STANDARD | 500-649 | APPROVE | $0 |
| 4 | SUBSTANDARD | 350-499 | REFER | $0 |
| 5 | DECLINE | 0-349 | DECLINE | $0 |

**Decision Logic:**
- Scores 0-1000 (composite from weighted signals)
- Higher scores = better risk = lower tier number
- APPROVE: Automatic binding eligible
- REFER: Requires underwriter review
- DECLINE: Outside risk appetite

### Loss Tier Bands

Loss tiers adjust premium based on expected loss frequency and severity:

| Tier | Label | Score Range | Freq Modifier | Sev Modifier |
|------|-------|-------------|---------------|--------------|
| 1 | VERY_LOW | 0-200 | 0.80x | 0.85x |
| 2 | LOW | 201-400 | 0.90x | 0.92x |
| 3 | MODERATE | 401-600 | 1.00x | 1.00x |
| 4 | HIGH | 601-800 | 1.15x | 1.20x |
| 5 | VERY_HIGH | 801-1000 | 1.35x | 1.45x |

**Constraints:** Floor = 0.70, Cap = 1.60

### Direct Queries

Binary questions that cannot be inferred from external signals:

| Query ID | Question | Trigger | Action | Impact |
|----------|----------|---------|--------|--------|
| `mfa_enabled` | Is multi-factor authentication enabled for all rem... | Answer = False | REFER | Override to Tier 4 |
| `backup_frequency` | Are critical systems backed up at least weekly wit... | Answer = False | MODIFIER | Modifier: 1.15x |

**Action Types:**
- **FLAG:** Adds note to underwriter; no pricing impact
- **MODIFIER:** Applies premium multiplier
- **REFER:** Forces underwriter review regardless of score

### Pricing Structure

Pricing varies by product type:


#### Cyber Liability

**Pricing Anchors (V5):**
- Base Limit Reference: $1,000,000
- Base Deductible Reference: $50,000

**Increased Limit Factors (ILF):**

| Limit | Factor | Premium Multiplier |
|-------|--------|-------------------|
| $250,000 | 0.45 | 0.45x base |
| $500,000 | 0.70 | 0.70x base |
| $1,000,000 (base) | 1.00 | 1.00x base |
| $2,000,000 | 1.65 | 1.65x base |
| $5,000,000 | 2.80 | 2.80x base |

**Deductible Factors (V5):**

| Deductible | Factor | Effect |
|------------|--------|--------|
| $10,000 | 1.50 | +50% loading |
| $25,000 | 1.15 | +15% loading |
| $50,000 (anchor) | 1.00 | Base price |
| $100,000 | 0.95 | -5% credit |
| $250,000 | 0.90 | -10% credit |
| $500,000 | 0.70 | -30% credit |
| $1,000,000 | 0.70 | -30% credit |


#### Network Security

**Pricing Anchors (V5):**
- Base Limit Reference: $1,000,000
- Base Deductible Reference: $50,000

**Increased Limit Factors (ILF):**

| Limit | Factor | Premium Multiplier |
|-------|--------|-------------------|
| $250,000 | 0.50 | 0.50x base |
| $500,000 | 0.75 | 0.75x base |
| $1,000,000 (base) | 1.00 | 1.00x base |
| $2,000,000 | 1.70 | 1.70x base |
| $5,000,000 | 2.90 | 2.90x base |

**Deductible Factors (V5):**

| Deductible | Factor | Effect |
|------------|--------|--------|
| $10,000 | 1.50 | +50% loading |
| $25,000 | 1.15 | +15% loading |
| $50,000 (anchor) | 1.00 | Base price |
| $100,000 | 0.95 | -5% credit |
| $250,000 | 0.90 | -10% credit |
| $500,000 | 0.70 | -30% credit |
| $1,000,000 | 0.70 | -30% credit |


### Limit Bandings

Pre-configured limit/deductible packages:

| Package | Limit | Deductible |
|---------|-------|------------|
| 1 | $250,000 | $2,500 |
| 2 | $500,000 | $5,000 |
| 3 | $1,000,000 | $10,000 |
| 4 | $2,000,000 | $15,000 |
| 5 | $5,000,000 | $25,000 |


---

## Decision Flow Summary

```
┌─────────────────────────────────────────────────────────────┐
│                    DSI Decision Flow                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. SIGNAL EXTRACTION                                       │
│     └─► External APIs → Normalized Scores (0-100)          │
│                                                             │
│  2. GROUP AGGREGATION                                       │
│     └─► Weighted combination within groups                  │
│                                                             │
│  3. THREE-LAYER ASSESSMENT                                  │
│     ├─► Risk Score (0-1000)                                │
│     ├─► Loss Score (frequency × severity)                  │
│     └─► Exposure Score (size × complexity)                 │
│                                                             │
│  4. TIER ASSIGNMENT                                         │
│     └─► Risk Score → Tier Band → Base Premium              │
│                                                             │
│  5. DIRECT QUERIES                                          │
│     └─► Binary answers → FLAGS / MODIFIERS / REFERS        │
│                                                             │
│  6. PRICING CALCULATION                                     │
│     └─► Base × ILF × Ded Factor × Modifiers × Tax          │
│                                                             │
│  7. DECISION OUTPUT                                         │
│     └─► APPROVE / REFER / DECLINE + Audit Trail            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

*Generated by DSI Coverage Documentation Generator*

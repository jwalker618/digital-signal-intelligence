# DSI Cyber Insurance Pricing Model v2.0

## Overview

This model implements Digital Signal Intelligence (DSI) for cyber insurance pricing, conforming to the Foundational Principles. It replaces traditional questionnaire-based underwriting with externally observable signals, enabling high straight-through processing rates and autonomous operation.

**Key Differentiator:** Unlike traditional cyber underwriting that relies on lengthy security questionnaires, this model derives risk assessment from observable digital behavior - what companies actually do, not what they claim.

---

## DSI Principles Compliance

| Principle | Implementation |
|-----------|----------------|
| External Observability | All primary signals obtainable without insured cooperation |
| Machine Readability | All signals have defined collection methods and scoring algorithms |
| Network Authority | PageRank-style relationship analysis with deep graph traversal |
| Behavioral Inference | Technical implementation and digital footprint reveal security culture |
| Absence as Signal | Missing security page, security.txt, bug bounty are negative signals |
| Structured Data Utilization | BitSight, ESG scores used as authority signals |
| Minimal Direct Inquiry | 8 optional Yes/No questions for critical factors |
| Organizational Assessment | Company-level signals, not asset-by-asset analysis |
| Simplicity in Scoring | Signal → Score → Tier → Price |
| Agentic Readiness | All components executable by AI without human interpretation |

---

## Signal Framework

### Signal Categories & Weights

```
Network Authority (15%)
├── Customer Quality (15%)
├── Partner Quality (10%)
├── Security Vendor Relationships (20%)    ← Important for cyber
├── Industry Body Membership (15%)
├── Certification Authority (15%)
├── Financial Relationships (5%)
├── Network Centrality (10%)
└── Second-Degree Quality (10%)

Technical Infrastructure (35%)              ← Critical for cyber
├── TLS Configuration (15%)
├── Security Headers (12%)
├── Email Authentication (12%)
├── DNSSEC (6%)
├── Network Exposure (20%)                  ← Attack surface
├── Software Currency (12%)
├── CVE Exposure (18%)                      ← Known vulnerabilities
└── Cloud Infrastructure (5%)

Corporate Digital Footprint (15%)
├── Security Page Presence (15%)
├── Privacy Policy Quality (10%)
├── security.txt Presence (10%)
├── Bug Bounty Program (20%)                ← Strong security signal
├── Security Hiring Activity (15%)
├── Technical Content (10%)
├── Developer Resources (5%)
└── Security Leadership Visibility (15%)

Public Records (25%)
├── Breach History (35%)                    ← Critical predictor
├── Regulatory Actions (20%)
├── Data Breach Litigation (15%)
├── Credential Exposure (20%)
└── Dark Web Exposure (10%)

Structured Data Feeds (10%)
├── Security Rating (BitSight etc.) (50%)
├── ESG Cyber Component (25%)
└── Credit Rating (25%)
```

---

## Signal Definitions

### Type 1: Network Authority Signals

#### Customer Quality Score

**What it measures:** Quality of the company's visible customer base.

**Collection method:** 
- Crawl case studies, customer logos, testimonials from company website
- Cross-reference detected customers against quality database
- Score based on Fortune 500 presence, industry leaders, regulated entities

**Scoring:**
| Score | Criteria |
|-------|----------|
| 85-100 | Fortune 500 / major enterprise customers visible |
| 70-84 | Mid-market enterprise customers |
| 50-69 | SMB customers only |
| 30-49 | Limited customer visibility |
| 0-29 | No customers visible or concerning customer base |

#### Security Vendor Relationships

**What it measures:** Partnerships with recognized security vendors.

**Collection method:**
- Check partner directories of major security vendors (CrowdStrike, Palo Alto, etc.)
- Crawl partnership announcements on company website
- Verify through vendor partnership badges/certifications

**Why it matters:** Companies partnered with top-tier security vendors are more likely to have mature security practices. This is network authority - being trusted by security experts.

**Scoring:**
| Score | Criteria |
|-------|----------|
| 90-100 | Multiple tier-1 security vendor partnerships |
| 75-89 | One tier-1 or multiple tier-2 partnerships |
| 50-74 | Tier-2 security vendor relationships |
| 25-49 | Security vendor relationships unclear |
| 0-24 | No visible security vendor relationships |

#### Industry Body Membership

**What it measures:** Participation in security-focused industry organizations.

**Collection method:**
- Query member directories of ISACs (FS-ISAC, Health-ISAC, etc.)
- Check Cloud Security Alliance membership
- Verify industry association participation

**Scoring:**
| Score | Criteria |
|-------|----------|
| 90-100 | Active ISAC member + other security bodies |
| 70-89 | ISAC member or equivalent |
| 50-69 | Industry association member (non-security focus) |
| 25-49 | Limited industry engagement visible |
| 0-24 | No industry body membership detected |

### Type 2: Technical Infrastructure Signals

#### TLS Configuration

**What it measures:** Quality of SSL/TLS implementation.

**Collection method:**
- Automated SSL Labs-style scanning
- Check certificate validity, chain, expiration
- Verify TLS version (1.3 preferred, 1.2 acceptable)
- Test cipher suite quality

**Scoring:**
| Score | Criteria |
|-------|----------|
| 95-100 | A+ rating: TLS 1.3, strong ciphers, HSTS preload |
| 85-94 | A rating: TLS 1.2+, good configuration |
| 70-84 | B rating: Acceptable, minor issues |
| 50-69 | C rating: Configuration problems |
| 0-49 | D/F rating: Serious vulnerabilities |

#### Network Exposure (Attack Surface)

**What it measures:** Exposed services, open ports, administrative interfaces.

**Collection method:**
- Shodan/Censys queries for company IP ranges
- Check for exposed admin panels, databases, development environments
- Identify unnecessary services

**Why it matters:** This is a direct measure of attack surface. Exposed databases, admin panels, and unnecessary services are primary attack vectors.

**Scoring:**
| Score | Criteria |
|-------|----------|
| 90-100 | Minimal exposure, only necessary services |
| 70-89 | Minor unnecessary services, no critical exposure |
| 50-69 | Some concerning exposure, managed risk |
| 30-49 | Significant exposure (databases, admin panels) |
| 0-29 | Critical exposure (unprotected databases, RDP, etc.) |

#### CVE Exposure

**What it measures:** Known vulnerabilities in detected software versions.

**Collection method:**
- Fingerprint software versions from banners, headers
- Cross-reference against NVD/CVE databases
- Weight by severity (CVSS score)

**Scoring:**
| Score | Criteria |
|-------|----------|
| 90-100 | No critical/high CVEs in detected software |
| 70-89 | Minor CVEs only, patches available |
| 50-69 | Some high-severity CVEs |
| 30-49 | Multiple high-severity CVEs |
| 0-29 | Critical CVEs actively exploited in the wild |

### Type 5: Corporate Digital Footprint Signals

#### Security Page Presence

**What it measures:** Existence and quality of dedicated security information.

**Collection method:**
- Check for /security, /trust, security center pages
- Analyze content depth and recency
- Verify certifications mentioned

**Why it matters:** Companies serious about security communicate it. Absence of a security page is a signal of lower maturity.

**Scoring:**
| Score | Criteria |
|-------|----------|
| 90-100 | Comprehensive security page with certifications, policies, contact |
| 70-89 | Good security page with key information |
| 50-69 | Basic security information present |
| 25-49 | Minimal security mention (footer only) |
| 0 | No security page or information |

#### Bug Bounty Program

**What it measures:** Presence and activity of bug bounty/vulnerability disclosure program.

**Collection method:**
- Check HackerOne, Bugcrowd, Intigriti directories
- Verify security.txt for bug bounty reference
- Assess program scope and responsiveness

**Why it matters:** Bug bounty programs indicate proactive security posture and willingness to engage security community.

**Scoring:**
| Score | Criteria |
|-------|----------|
| 95-100 | Active public bug bounty with good reputation |
| 80-94 | Private bug bounty or VDP with track record |
| 60-79 | Vulnerability disclosure policy only |
| 30-59 | Security contact exists but no formal program |
| 0-29 | No bug bounty or VDP |

### Type 6: Public Record Signals

#### Breach History

**What it measures:** History of reported data breaches.

**Collection method:**
- HHS breach portal (healthcare)
- State attorney general breach notifications
- SEC 8-K filings (material breaches)
- Privacy Rights Clearinghouse database
- Media monitoring for disclosed breaches

**Why it matters:** Prior breaches are the strongest predictor of future breaches. Companies with breach history have 3x higher probability of future incidents.

**Scoring:**
| Score | Criteria |
|-------|----------|
| 100 | No breach history found |
| 70-89 | Minor breach >5 years ago, remediated |
| 50-69 | Moderate breach 3-5 years ago |
| 30-49 | Significant breach in past 3 years |
| 0-29 | Multiple breaches or major recent breach |

#### Credential Exposure

**What it measures:** Exposure of corporate credentials in data breaches.

**Collection method:**
- HaveIBeenPwned API for corporate domain
- Dark web monitoring for corporate credentials
- Breach database cross-reference

**Scoring:**
| Score | Criteria |
|-------|----------|
| 90-100 | No credential exposure detected |
| 70-89 | Minor historical exposure, old breaches |
| 50-69 | Moderate exposure, some recent |
| 30-49 | Significant exposure including recent |
| 0-29 | Widespread exposure, credentials actively circulating |

---

## Direct Inquiry Questions (Optional)

These 8 questions are optional. The model produces a valid assessment without them, but responses improve accuracy for factors that cannot be externally observed.

| # | Question | Type | Impact |
|---|----------|------|--------|
| 1 | Is multi-factor authentication enabled for all remote access? | Yes/No | +30 if Yes, -50 if No |
| 2 | Do all employees complete annual cyber security training? | Yes/No | +20 if Yes |
| 3 | Do you process Protected Health Information (PHI)? | Yes/No | Pricing adjustment |
| 4 | Do you store payment card data (PCI scope)? | Yes/No | Pricing adjustment |
| 5 | Do you have a documented incident response plan? | Yes/No | +25 if Yes |
| 6 | Is EDR deployed on all endpoints? | Yes/No | +30 if Yes |
| 7 | Are backups maintained offline or immutable? | Yes/No | +35 if Yes |
| 8 | Have you experienced a material cyber incident in the past 3 years? | Yes/No | -100 if Yes |

**Constraint:** These are declarations subject to policy terms. Misrepresentation may void coverage.

---

## Risk Tier Structure

| Tier | Score Range | Label | Underwriting Action |
|------|-------------|-------|---------------------|
| 1 | 800-1000 | Preferred | Auto-approve at preferred pricing |
| 2 | 650-799 | Standard | Auto-approve at standard pricing |
| 3 | 500-649 | Elevated | Auto-approve with conditions |
| 4 | 350-499 | High Risk | Manual review required |
| 5 | 0-349 | Critical | Decline or senior review |

### Critical Overrides

Certain signals force minimum tier regardless of composite score:

| Condition | Minimum Tier |
|-----------|--------------|
| CVE exposure score < 30 | Tier 4 |
| Network exposure score < 30 | Tier 4 |
| Breach history score < 40 | Tier 4 |
| Dark web exposure score < 30 | Tier 4 |
| Recent incident disclosed | Tier 4 |

---

## Pricing Structure

### Base Premium by Tier

For $1M limit, medium-sized company:

| Tier | Base Premium |
|------|--------------|
| 1 (Preferred) | $8,000 |
| 2 (Standard) | $12,000 |
| 3 (Elevated) | $18,000 |
| 4 (High Risk) | $30,000 |
| 5 (Critical) | $50,000 |

### Industry Multipliers

| Industry | Multiplier |
|----------|------------|
| Healthcare | 1.50x |
| Financial Services | 1.40x |
| Retail | 1.25x |
| Energy | 1.20x |
| Technology | 1.15x |
| Professional Services | 1.10x |
| Education | 1.05x |
| Manufacturing | 0.95x |
| Government | 0.90x |

### Size Multipliers

| Size Band | Multiplier |
|-----------|------------|
| Small (<500 employees) | 0.60x |
| Medium (500-5,000) | 1.00x |
| Large (5,000-25,000) | 2.50x |
| Enterprise (>25,000) | 5.00x |

### Limit Factors

| Limit | Factor |
|-------|--------|
| $1M | 1.00x |
| $2M | 1.70x |
| $5M | 3.20x |
| $10M | 5.00x |
| $25M | 9.00x |
| $50M | 14.00x |
| $100M | 22.00x |

### Regulatory Multipliers

| Exposure | Multiplier |
|----------|------------|
| PHI Handler (HIPAA) | 1.30x |
| PCI Scope | 1.20x |
| Both | 1.56x (compound) |

---

## Confidence Levels

| Signal Coverage | Confidence | Treatment |
|-----------------|------------|-----------|
| ≥85% signals available | ≥0.90 | Full automation |
| 70-84% available | 0.75-0.89 | Automation with margin |
| 55-69% available | 0.60-0.74 | Manual review recommended |
| <55% available | <0.60 | Manual underwriting required |

---

## Example Outputs

### Strong Security Posture (Tier 1)

```
Company: SecureTech Corp
Domain: securetech.com
Industry: TECHNOLOGY
Size: LARGE

Composite Score: 920/1000
Confidence: 95%

Category Scores:
  network_authority: 89/100
  technical_infrastructure: 92/100
  corporate_footprint: 91/100
  public_records: 95/100
  structured_data: 86/100

Tier: 1 (Preferred)
Decision: APPROVE
Premium: $207,000 for $25M limit
Rate: 0.83% of limit
```

### Weak Security Posture (Tier 5)

```
Company: QuickMart Retail
Domain: quickmart.com
Industry: RETAIL
Size: MEDIUM

Composite Score: 259/1000
Confidence: 61%

Category Scores:
  network_authority: 38/100
  technical_infrastructure: 44/100
  corporate_footprint: 30/100
  public_records: 44/100
  structured_data: 42/100

Tier: 5 (Critical)
Decision: DECLINE
Reasoning: Recent breach history, critical CVE exposure, 
           no MFA, no EDR, recent incident disclosed
```

---

## Data Sources

| Source | Signals Provided | Update Frequency |
|--------|------------------|------------------|
| SSL Labs / Custom Scanner | TLS, certificates | On-demand |
| DNS Queries | SPF, DKIM, DMARC, DNSSEC | On-demand |
| Shodan / Censys | Network exposure, services | Daily |
| CVE/NVD Databases | Known vulnerabilities | Daily |
| HaveIBeenPwned | Credential exposure | Daily |
| Company Websites | Footprint signals | Weekly |
| HackerOne / Bugcrowd | Bug bounty presence | Weekly |
| HHS Breach Portal | Healthcare breaches | Daily |
| BitSight / SecurityScorecard | Security ratings | Daily |
| ISAC Directories | Membership | Monthly |

---

## API Integration

### Endpoints

```
POST /api/v2/cyber/assess
GET /api/v2/cyber/score/{domain}
GET /api/v2/cyber/signals/{domain}
```

### Sample Request

```json
{
  "domain": "example.com",
  "requested_limit": 10000000,
  "direct_inquiry": {
    "mfa_enabled": true,
    "security_training": true,
    "phi_handler": false,
    "pci_scope": true,
    "incident_response_plan": true,
    "edr_deployed": true,
    "immutable_backups": true,
    "recent_incident": false
  }
}
```

### Sample Response

```json
{
  "company_name": "Example Corp",
  "domain": "example.com",
  "composite_score": 782,
  "confidence": 0.88,
  "tier": 2,
  "tier_label": "Standard",
  "decision": "APPROVE",
  "recommended_limit": 10000000,
  "recommended_retention": 100000,
  "annual_premium": 62500,
  "conditions": [
    "Annual security assessment required",
    "Notify insurer of incidents within 72 hours"
  ],
  "category_scores": {
    "network_authority": 75,
    "technical_infrastructure": 82,
    "corporate_footprint": 70,
    "public_records": 88,
    "structured_data": 72
  }
}
```

---

## Comparison: DSI vs Traditional

| Aspect | Traditional | DSI |
|--------|-------------|-----|
| Data collection | 20+ page questionnaire | Automated signal collection |
| Processing time | Days to weeks | Minutes |
| Accuracy | Self-reported (unverified) | Observable behavior (verified) |
| Scalability | Manual review required | Full automation for Tier 1-3 |
| Cost per bind | High (analyst time) | Low (automated) |
| Consistency | Varies by underwriter | Algorithmic (consistent) |
| Refresh frequency | Annual renewal | Continuous monitoring possible |

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 2.0 | November 2025 | Complete rebuild for DSI Principles v1.0 compliance |
| 1.0 | October 2025 | Initial implementation (deprecated) |

---

*This model conforms to DSI Principles v1.0*

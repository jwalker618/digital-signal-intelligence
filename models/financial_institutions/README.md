# DSI Financial Institutions Insurance Pricing Model v2.0

## Overview

This model implements Digital Signal Intelligence (DSI) for financial institutions insurance pricing, conforming to DSI Principles v1.0. It replaces traditional application-based underwriting with observable signals from regulatory filings, examination records, and compliance databases.

**Coverage Types:**
- Financial Institution Bond (Fidelity)
- Professional Liability (E&O)  
- Directors & Officers
- Cyber Liability
- Employment Practices Liability

**Key DSI Principle:** We assess INSTITUTIONAL behavior patterns through regulatory compliance, examination results, and observable operational practices - not through self-reported questionnaires about internal controls.

**FI Insurance Suitability for DSI:**
- Call Reports/regulatory filings are comprehensive and structured
- Examination results and enforcement actions are public
- CFPB complaint data is publicly available
- Credit ratings provide third-party assessment
- Digital security posture is externally testable

---

## DSI Principles Compliance

| Principle | Implementation |
|-----------|----------------|
| External Observability | FFIEC, OCC, FDIC, NCUA, SEC databases |
| Machine Readability | Call Reports, enforcement databases are structured |
| Network Authority | Correspondent relationships, auditor quality |
| Behavioral Inference | CFPB complaints, examination patterns |
| Absence as Signal | Missing security page, no ESG reporting |
| Structured Data Utilization | Credit ratings, ESG scores |
| Minimal Direct Inquiry | 6 optional questions |
| Organizational Assessment | Institution-level, not product-level |
| Simplicity in Scoring | Signal → Score → Tier → Price |
| Agentic Readiness | All sources API-accessible |

---

## Signal Framework (48 Signals)

### Category Weights

| Category | Weight | Rationale |
|----------|--------|-----------|
| Network Authority | 10% | Quality of industry relationships |
| Regulatory Compliance | 25% | Exam results, enforcement - critical |
| Financial Condition | 20% | CAMELS proxies - capital, asset quality |
| Governance | 15% | Board quality, risk oversight |
| Operational Risk | 10% | Complaints, litigation, incidents |
| Cyber Security | 10% | Technical security posture |
| Corporate Footprint | 5% | Digital presence |
| Structured Data | 5% | Third-party ratings |

### Key Signal Categories

#### Regulatory Compliance (25%)
*From FFIEC, OCC, FDIC, Fed, SEC*

| Signal | Weight | What It Measures |
|--------|--------|------------------|
| Examination Rating | 20% | CAMELS indicators |
| Enforcement Actions | 25% | C&D, CMPs, formal agreements |
| Informal Actions | 10% | MOUs, board resolutions |
| CRA Rating | 10% | Community Reinvestment Act |
| BSA/AML | 15% | Anti-money laundering compliance |
| Fair Lending | 10% | ECOA, HMDA compliance |
| Consumer Compliance | 10% | UDAP/UDAAP |

#### Financial Condition (20%)
*From Call Reports, 10-K, regulatory filings*

| Signal | Weight | What It Measures |
|--------|--------|------------------|
| Capital Ratios | 20% | CET1, Tier 1, Total capital |
| Asset Quality | 20% | NPL ratio, charge-offs |
| Liquidity | 15% | Liquidity coverage |
| Earnings | 15% | Profitability stability |
| Concentration | 10% | Loan concentration risk |
| Interest Rate Risk | 10% | IRR exposure |
| Growth Rate | 10% | Rapid growth = higher risk |

---

## Network Authority Signals

### Auditor Quality

**What it measures:** Big 4 vs national vs regional auditor.

**Why it matters:** Big 4 auditors provide higher scrutiny and are trusted by regulators. Quality auditor relationships indicate institutional quality.

**Scoring:**
| Score | Criteria |
|-------|----------|
| 90-100 | Big 4 auditor, long relationship |
| 75-89 | Big 4, shorter tenure |
| 60-74 | National firm |
| 40-59 | Regional firm |
| 0-39 | Local/unknown firm |

### Correspondent Banking Relationships

**What it measures:** Quality of correspondent banking network.

**Why it matters:** Major banks only maintain correspondent relationships with well-managed institutions.

**Scoring:**
| Score | Criteria |
|-------|----------|
| 90-100 | Multiple money-center bank relationships |
| 75-89 | Major regional bank correspondents |
| 60-74 | Standard correspondent network |
| 40-59 | Limited correspondent access |
| 0-39 | Correspondent issues or restrictions |

---

## Regulatory Compliance Signals

### Enforcement Actions

**What it measures:** Formal regulatory enforcement (C&D orders, CMPs, formal agreements).

**Collection method:**
- OCC enforcement database
- FDIC enforcement decisions
- Federal Reserve enforcement actions
- NCUA enforcement actions
- SEC/FINRA actions

**Why it matters:** Enforcement actions are the strongest signal of institutional problems. They indicate issues serious enough to warrant regulatory intervention.

**Scoring:**
| Score | Criteria |
|-------|----------|
| 100 | No enforcement history |
| 70-89 | Minor action >5 years ago, resolved |
| 50-69 | Action 3-5 years ago, resolved |
| 30-49 | Recent action, in remediation |
| 0-29 | Active enforcement or multiple actions |

### BSA/AML Compliance

**What it measures:** Bank Secrecy Act/Anti-Money Laundering compliance.

**Collection method:**
- FinCEN enforcement actions
- OCC BSA-specific orders
- Independent audit findings (if disclosed)

**Why it matters:** BSA/AML violations result in severe penalties and can threaten charter. This is a critical compliance area.

**Scoring:**
| Score | Criteria |
|-------|----------|
| 95-100 | No BSA issues, strong program indicated |
| 80-94 | Minor findings, remediated |
| 60-79 | Moderate findings |
| 40-59 | Significant findings |
| 0-39 | BSA enforcement action |

---

## Cyber Security Signals

### Technical Infrastructure Assessment

Externally observable security posture:

| Signal | Weight | Collection Method |
|--------|--------|-------------------|
| TLS Configuration | 20% | SSL Labs-style scanning |
| Email Authentication | 20% | SPF, DKIM, DMARC verification |
| Security Headers | 15% | HTTP header analysis |
| Network Exposure | 20% | Shodan/Censys scanning |
| Vulnerabilities | 15% | CVE detection in software |
| Security Rating | 10% | BitSight if available |

**Why it matters:** FI cyber exposure is significant. Technical posture indicates security investment and operational discipline.

---

## Direct Inquiry Questions (6 Maximum)

| Question | Type | Impact |
|----------|------|--------|
| Pending/recent regulatory enforcement? | Yes/No | -150 if Yes, +25 if No |
| Outstanding MRAs/MRIAs from exam? | Yes/No | -75 if Yes |
| Material litigation pending? | Yes/No | -100 if Yes |
| Reportable cyber incidents (24 mo)? | Yes/No | -75 if Yes, +20 if No |
| Asset growth >20% in past year? | Yes/No | -25 if Yes |
| New product lines launched? | Yes/No | -15 if Yes |

---

## Pricing Structure

### Base Premium by Tier (per $1M combined limit)

| Tier | Score | Premium |
|------|-------|---------|
| 1 Preferred | 800+ | $1,500 |
| 2 Standard | 650-799 | $2,200 |
| 3 Elevated | 500-649 | $3,200 |
| 4 High Risk | 350-499 | $5,000 |
| 5 Critical | <350 | $8,000 |

### Institution Type Multipliers

| Type | Multiplier |
|------|------------|
| Credit Union | 0.85x |
| Savings Institution | 0.90x |
| Community Bank | 1.00x |
| Insurance Company | 1.10x |
| Regional Bank | 1.20x |
| Investment Adviser | 1.25x |
| Asset Manager | 1.30x |
| Mortgage Company | 1.35x |
| Broker-Dealer | 1.40x |
| Payment Processor | 1.40x |
| Money Center Bank | 1.50x |
| Fintech | 1.50x |

### Asset Size Multipliers

| Size Band | Assets | Multiplier |
|-----------|--------|------------|
| Community | <$1B | 0.80x |
| Small | $1B-$10B | 1.00x |
| Mid | $10B-$50B | 1.30x |
| Large | $50B-$250B | 1.80x |
| Mega | >$250B | 2.50x |

---

## Critical Overrides

| Condition | Result |
|-----------|--------|
| Enforcement action score < 40 | Tier 4 minimum |
| BSA/AML score < 40 | Tier 4 minimum |
| Capital ratio score < 40 | Tier 4 minimum |
| Asset quality score < 40 | Tier 3 minimum |
| Breach history score < 40 | Tier 3 minimum |
| Litigation score < 40 | Tier 4 minimum |
| Regulatory action disclosed | Tier 4 minimum |
| Examination issues disclosed | Tier 3 minimum |

---

## Data Sources

| Source | Data Provided |
|--------|---------------|
| FFIEC | Call Reports, UBPR data |
| OCC | Enforcement, examination data |
| FDIC | Institution data, enforcement |
| Federal Reserve | BHC data, enforcement |
| NCUA | Credit union data |
| SEC EDGAR | 10-K, proxy statements |
| CFPB | Consumer complaint database |
| FinCEN | BSA enforcement |
| SSL Labs | TLS configuration |
| Shodan/Censys | Network exposure |

---

## Example Output

```
Institution: Midwest Regional Bank
Type: REGIONAL_BANK | Size: MID
Total Assets: $25,000,000,000

Composite Score: 921/1000 | Confidence: 95%

Category Scores:
  regulatory_compliance: 91/100
  financial_condition: 85/100
  governance: 88/100
  cyber_security: 88/100
  operational_risk: 88/100

Tier: 1 (Preferred)
Decision: APPROVE

Combined Limit: $25,000,000
Annual Premium: $25,000
Deductible: $250,000
```

---

## Comparison: DSI vs Traditional FI Underwriting

| Aspect | Traditional | DSI |
|--------|-------------|-----|
| Primary data | 30+ page application | Regulatory filings |
| Compliance check | Self-reported | OCC/FDIC/Fed databases |
| Financial analysis | Submitted financials | Call Report data |
| Processing time | Weeks | Minutes |
| Exam results | Ask applicant | Enforcement database |
| Complaint data | Self-reported | CFPB database |
| Scalability | Manual intensive | Fully automated Tier 1-3 |

---

## FI-Specific Considerations

### Multi-Line Coverage

FI insurance typically bundles multiple coverages:
- Bond: Employee dishonesty, forgery, computer fraud
- E&O: Professional liability
- D&O: Directors and officers
- Cyber: Data breach, business interruption
- EPL: Employment practices

DSI assesses institution-wide risk that affects all coverages.

### Regulatory Sensitivity

FI is highly regulated; regulatory signals are exceptionally strong predictors:
- Enforcement actions predict bond losses
- Compliance issues predict E&O claims
- Governance problems predict D&O claims
- Operational weaknesses indicate cyber exposure

### Size Complexity

Larger institutions have:
- More complex operations
- Higher limits needed
- Greater regulatory scrutiny
- More sophisticated attackers

Asset size multipliers reflect this.

---

*Conforms to DSI Principles v1.0*

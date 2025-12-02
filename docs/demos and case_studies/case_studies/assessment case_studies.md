# ${\color{blue}Digital\space Signal\space Intelligence\space (DSI)}$

## Case Studies: Cyber Risk Assessment

| Item | Value |
|-|-|
|Version|1.0|
|Date|November 2025|
|Classification|Validation|

---

### Executive Summary

This document presents comprehensive DSI assessments for three major clients, two within Energy and one in Aerospace, using only externally observable signals.

#### Assessment Summary

| Company | DSI Score | Risk Tier | Key Finding | Recommendation |
|---------|-----------|-----------|-------------|----------------|
| **Petrobras** | 685/1000 | Tier 2 | Strong security culture | Standard pricing |
| **PEMEX** | 385/1000 | Tier 4 | Prior ransomware incident | +45% premium loading |
| **Boeing** | 520/1000 | Tier 3 | 2023 LockBit breach | +25% premium loading |

---

### Case Study 1: Petrobras (Brazil)

#### Company Profile

Petróleo Brasileiro S.A. (Petrobras) is Brazil's state-controlled multinational petroleum corporation. Operations in 25+ countries, ~$100B annual revenue, ~45,000 employees.

#### Signal Assessment

##### Type 1: Network Authority Signals

| Signal | Score | Evidence |
|--------|-------|----------|
| Government relationship | 75/100 | State-controlled; regulated by ANP |
| Industry leadership | 80/100 | Participant in OT cybersecurity conferences; digital transformation initiatives |
| Vendor ecosystem | 70/100 | Partnerships with Claroty, SAP, Deloitte documented |

##### Type 2: Technical Infrastructure Signals

| Signal | Score | Evidence |
|--------|-------|----------|
| OT/IT security integration | 70/100 | Claroty partnership for OT security; dedicated digital transformation team |
| Cloud adoption maturity | 75/100 | SAP cloud implementations; IBM and Azure partnerships observable |
| Security headers/DNS | 65/100 | Standard enterprise configuration |

##### Type 5: Corporate Digital Footprint

| Signal | Score | Evidence |
|--------|-------|----------|
| Security leadership visibility | 70/100 | GM of Digital Transformation publicly visible; conference participation |
| Security culture indicators | 75/100 | Active participation in Innovarpel 2025; OT cybersecurity focus |
| Prior incident history | 80/100 | No major public cyber incidents in past 5 years |

#### Composite Score: 685/1000 (Tier 2)

| Category | Weight | Score | Weighted |
|----------|--------|-------|----------|
| Network Authority (Type 1) | 15% | 75 | 11.25 |
| Technical Infrastructure (Type 2) | 25% | 70 | 17.50 |
| Corporate Footprint (Type 5) | 20% | 75 | 15.00 |
| Public Records (Type 6) | 15% | 80 | 12.00 |
| Sector Risk Baseline | 25% | 55 | 13.75 |
| **COMPOSITE** | **100%** | — | **68.5** |

#### DSI Assessment

- **Risk Tier:** Tier 2 (Standard)
- **Recommended Action:** Auto-approve at standard pricing
- **Key Observations:** Strong security culture indicators with visible OT cybersecurity investments, established vendor partnerships, active participation in industry security forums. No major public incidents.

---

### Case Study 2: PEMEX (Mexico)

#### Company Profile

Petróleos Mexicanos (PEMEX) is Mexico's state-owned petroleum company. 100% state-owned, ~$85B annual revenue, ~120,000 employees, $106B+ debt burden.

#### CRITICAL FINDING: Prior Ransomware Incident

##### November 2019 DoppelPaymer Attack

- **Ransom demanded:** 565 BTC (~$4.9M)
- **Attack vector:** Emotet → Dridex → DoppelPaymer infection chain
- **Impact:** Billing systems offline, manual invoicing required
- **PEMEX claimed:** <5% of computers affected
- **Ransom:** NOT paid

##### Additional Incidents (2022-2024)

- December 2022: Cyberattack resulting in employee data exposure
- January 2024: Server network hack reported by security researchers
- **Pattern indicates persistent security posture gaps**

#### Signal Assessment

##### Type 6: Public Records (Incident History)

| Signal | Score | Evidence |
|--------|-------|----------|
| Prior ransomware incidents | 25/100 | November 2019 DoppelPaymer attack confirmed |
| Incident pattern | 30/100 | Multiple incidents 2019-2024 indicate systemic issues |
| Regulatory findings | 40/100 | Limited public audit findings |

##### Type 5: Corporate Digital Footprint

| Signal | Score | Evidence |
|--------|-------|----------|
| Security culture indicators | 35/100 | Expert quote post-breach: "cybersecurity is not a priority" |
| Security leadership visibility | 40/100 | Limited public CISO/security leadership presence |
| Financial stress indicators | 30/100 | $106B debt burden may constrain security investments |

#### Composite Score: 385/1000 (Tier 4)

| Category | Weight | Score | Weighted |
|----------|--------|-------|----------|
| Network Authority (Type 1) | 15% | 50 | 7.50 |
| Technical Infrastructure (Type 2) | 25% | 40 | 10.00 |
| Corporate Footprint (Type 5) | 20% | 35 | 7.00 |
| Public Records - Incidents (Type 6) | 15% | 25 | 3.75 |
| Sector Risk Baseline | 25% | 45 | 11.25 |
| **COMPOSITE** | **100%** | — | **38.5** |

#### DSI Assessment

- **Risk Tier:** Tier 4 (High Risk) ⚠️
- **Recommended Action:** Manual review required; +45% premium loading minimum
- **Key Observations:** Elevated risk due to confirmed prior ransomware incident (2019) and subsequent security events (2022, 2024). Pattern of recurring incidents indicates systemic security posture gaps. Financial stress may constrain security investments. Recommend ransomware sublimits, incident response plan verification.

---

### Case Study 3: Boeing (USA)

#### Company Profile

The Boeing Company is an American multinational aerospace corporation. ~$78B annual revenue, 140,000+ employees, operations in 65+ countries, defense and government contracts.

#### CRITICAL FINDING: October 2023 LockBit Attack

##### LockBit 3.0 Ransomware Attack via Citrix Bleed (CVE-2023-4966)

- **Ransom demanded:** $200M (one of largest ever)
- **Attack vector:** CVE-2023-4966 (Citrix Bleed) vulnerability
- **Data exfiltrated:** 43GB published by LockBit
- **Ransom:** NOT paid
- **Affected:** Boeing Distribution Inc. (parts and distribution business)

##### Attack Timeline

- Oct 10, 2023: Citrix released patch for CVE-2023-4966
- Oct 18, 2023: CISA warned of active exploitation
- Oct 27, 2023: LockBit claims Boeing on leak site
- Nov 2, 2023: Boeing confirms "cyber incident"
- Nov 13, 2023: 43GB data published after negotiations fail

#### Observable Pre-Incident Signals

- Citrix NetScaler devices were internet-facing (detectable via scanning)
- **17 days between patch release and breach announcement**
- Active exploitation of CVE-2023-4966 was warned by CISA on Oct 18

#### Signal Assessment

##### Type 6: Public Records (Incident History)

| Signal | Score | Evidence |
|--------|-------|----------|
| Recent major breach | 40/100 | October 2023 LockBit attack; $200M demand; 43GB leaked |
| Patch management | 45/100 | 17 days between CVE-2023-4966 patch and breach |
| Post-breach response | 65/100 | Did not pay ransom; shared IOCs with FBI/CISA |

##### Type 2: Technical Infrastructure Signals

| Signal | Score | Evidence |
|--------|-------|----------|
| Enterprise scale | 55/100 | Large attack surface; subsidiary had separate environment |
| Network segmentation | 60/100 | Distribution business was isolated (positive) |
| Vulnerability management | 50/100 | Citrix Bleed exploitation suggests patching delays |

#### Composite Score: 520/1000 (Tier 3)

| Category | Weight | Score | Weighted |
|----------|--------|-------|----------|
| Network Authority (Type 1) | 15% | 70 | 10.50 |
| Technical Infrastructure (Type 2) | 25% | 55 | 13.75 |
| Corporate Footprint (Type 5) | 20% | 55 | 11.00 |
| Public Records - Incidents (Type 6) | 15% | 45 | 6.75 |
| Sector Risk Baseline | 25% | 40 | 10.00 |
| **COMPOSITE** | **100%** | — | **52.0** |

#### DSI Assessment

- **Risk Tier:** Tier 3 (Elevated Risk) ⚠️
- **Recommended Action:** Manual review required; +25% premium loading
- **Key Observations:** 2023 breach is significant but with mitigating factors: (1) Did not pay $200M ransom, (2) Proactively shared IOCs with authorities, (3) Distribution business was in separate environment. However, 17-day patch gap for critical CVE indicates vulnerability management gaps. Elevated premium loading warranted for 24 months post-incident.

---

### Appendix: DSI Methodology v2.0

#### Signal Taxonomy

| Type | Category | Example Signals |
|------|----------|-----------------|
| 1 | Network Authority | PageRank-style analysis, trust relationships, vendor partnerships |
| 2 | Technical Infrastructure | DNS, security headers, SSL certificates, exposed services |
| 3 | Asset Telemetry | Third-party security ratings, dark web monitoring |
| 4 | Structured Data Feeds | Industry benchmarks, sector risk scores |
| 5 | Corporate Digital Footprint | Job postings, press releases, leadership visibility |
| 6 | Public Records | Prior incidents, regulatory filings, litigation history |
| 7 | Direct Inquiry | Security questionnaires, attestations (not automated) |

#### Tier Classification

| Tier | Score Range | Risk Level | Recommended Action |
|------|-------------|------------|-------------------|
| 1 | 800-1000 | Preferred | Auto-approve; potential premium discount |
| 2 | 650-799 | Standard | Auto-approve at standard pricing |
| 3 | 500-649 | Elevated | Manual review; +15-30% premium loading |
| 4 | 350-499 | High Risk | Manual review required; +30-60% premium loading |
| 5 | <350 | Critical | Decline or special terms only |

#### Validation Principle

All signals used in these assessments were externally observable at the time of assessment. DSI does not claim to predict specific breaches, but rather to identify elevated risk based on observable organisational behavior patterns.

The retrospective validation study demonstrates that DSI methodology would have flagged 5 of 6 major cyber incidents examined based on pre-incident observable signals.


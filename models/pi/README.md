# DSI Professional Indemnity Insurance Pricing Model v2.0

## Overview

This model implements Digital Signal Intelligence (DSI) for professional indemnity insurance pricing, conforming to Foundational Principles. It replaces traditional application-based underwriting with observable signals from regulatory bodies, peer recognition platforms, public records, and digital infrastructure analysis.

**Professional Classes Covered:**
- Law Firms (all sizes and practice areas)
- Accounting Firms (audit, tax, advisory)
- Architects & Engineers
- Management & IT Consultants
- Real Estate Professionals
- Insurance Agents & Brokers
- Financial Planners

**Key DSI Principle:** We assess PROFESSIONAL COMPETENCE and OPERATIONAL DISCIPLINE through regulatory standing, peer recognition, and observable practice patterns—not through self-reported descriptions of internal procedures.

**PI Insurance Suitability for DSI:**
- Regulatory/licensing bodies maintain public disciplinary records
- Professional certifications and peer ratings are verifiable
- Litigation history is searchable in court records
- Client relationships visible through published matters
- Firm stability signals (partner turnover, growth patterns) are observable

---

## DSI Principles Compliance

| Principle | Implementation |
|-----------|----------------|
| External Observability | Bar records, PACER, licensing boards, peer review directories |
| Machine Readability | Structured disciplinary databases, court records |
| Network Authority | Chambers rankings, Best Lawyers, Martindale ratings |
| Behavioral Inference | Practice patterns, case outcomes, client reviews |
| Absence as Signal | Missing certifications, no peer recognition, sparse bios |
| Structured Data Utilisation | Am Law rankings, peer review ratings |
| Minimal Direct Inquiry | 6 optional questions maximum |
| Organisational Assessment | Firm-level, not individual attorney |
| Simplicity in Scoring | Signal → Score → Tier → Price |
| Agentic Readiness | All sources API-accessible or scrapeable |

---

## Signal Framework (45+ Signals)

### Category Weights by Profession

| Category | Law Firm | Accounting | Arch/Eng | Consulting |
|----------|----------|------------|----------|------------|
| Network Authority | 20% | 15% | 15% | 25% |
| Regulatory Standing | 25% | 30% | 20-25% | 10% |
| Firm Stability | 15% | 15% | 15% | 15% |
| Practice Quality | 15% | 15% | 20% | 20% |
| Technical Infrastructure | 5% | 5% | 5% | 10-20% |
| Corporate Footprint | 10% | 10% | 10% | 15% |
| Litigation History | 10% | 10% | 15% | 5% |

### Key Signal Categories

#### Network Authority (Type 1)
*From Chambers, Legal 500, Martindale, Best Lawyers, LinkedIn*

| Signal | What It Measures |
|--------|------------------|
| Peer Ranking | Chambers/Legal 500 band, Best Lawyers inclusion |
| Client Quality | Public client representations, notable matters |
| Referral Network | Quality of referring/referred relationships |
| Association Leadership | Bar association, professional body positions |
| Thought Leadership | Publications, CLE presentations, quoted in media |

#### Regulatory Standing (Type 6)
*From State Bar, AICPA, licensing boards, PACER*

| Signal | What It Measures |
|--------|------------------|
| License Status | Active, good standing across all jurisdictions |
| Disciplinary History | Sanctions, suspensions, censures, admonitions |
| Malpractice Record | Judgments and settlements on public record |
| CE Compliance | Continuing education requirements current |
| Specialty Certification | Board certifications, advanced designations |
| Peer Review (Accounting) | AICPA peer review results |

#### Firm Stability (Types 5 & 6)
*From website, LinkedIn, Glassdoor, court records*

| Signal | What It Measures |
|--------|------------------|
| Tenure | Years in continuous practice |
| Partner Stability | Partner/principal turnover rate |
| Staff Retention | Glassdoor scores, job posting patterns |
| Office Stability | Location changes, expansions, contractions |
| Financial Stability | Liens, judgments, bankruptcy indicators |
| Succession Planning | Evidence of next-generation development |

#### Practice Quality (Types 5 & 6)
*From court records, client reviews, professional platforms*

| Signal | What It Measures |
|--------|------------------|
| Outcome Patterns | Win rates, settlement outcomes (litigation) |
| Client Reviews | Ratings on Avvo, Google, professional platforms |
| Work Quality | Brief quality, transaction completion rate |
| Fee Disputes | Arbitration history with clients |
| Complaint History | Complaints filed with professional bodies |

#### Technical Infrastructure (Type 2)
*From SSL Labs, SecurityHeaders, DNS records*

| Signal | What It Measures |
|--------|------------------|
| TLS Configuration | Encryption strength, certificate validity |
| Email Authentication | SPF, DKIM, DMARC implementation |
| Security Headers | HSTS, CSP, X-Frame-Options presence |
| Breach History | Past data breaches affecting firm |

---

## Practice Area Risk Modifiers

### Law Firms

| Practice Area | Modifier | Rationale |
|---------------|----------|-----------|
| Securities | 1.40x | High regulatory exposure, large transactions |
| Personal Injury Plaintiff | 1.30x | Deadline sensitivity, statute of limitations |
| Corporate M&A | 1.25x | Large transaction exposure |
| Trusts & Estates | 1.20x | Fiduciary exposure |
| Environmental | 1.20x | Long-tail exposure |
| Tax | 1.15x | IRS exposure |
| Bankruptcy | 1.15x | Fiduciary duties |
| IP/Patent | 1.15x | Valuation disputes |
| Plaintiff Litigation | 1.15x | Deadline sensitivity |
| Employment | 1.10x | Regulatory complexity |
| Real Estate | 1.10x | Title issues |
| General Litigation | 1.00x | Baseline |
| Insurance Coverage | 1.05x | Specialized but manageable |
| Family Law | 0.90x | Lower severity typically |
| Criminal Defense | 0.85x | Lower malpractice frequency |

### Accounting Firms

| Service Type | Modifier | Rationale |
|--------------|----------|-----------|
| Public Company Audit | 1.50x | Highest exposure, SEC scrutiny |
| Valuation Advisory | 1.35x | Dispute-prone |
| M&A Advisory | 1.30x | Transaction exposure |
| Private Company Audit | 1.25x | Material exposure |
| Forensic Accounting | 1.25x | Expert testimony |
| Estate Tax | 1.20x | Complexity, family disputes |
| Corporate Tax | 1.10x | IRS exposure |
| Individual Tax | 0.90x | Lower exposure |
| Bookkeeping | 0.80x | Limited exposure |

---

## Pricing Structure

### Base Premium by Profession (per $1M limit)

| Profession | Base Rate |
|------------|-----------|
| Accounting Firm | $9,000 |
| Law Firm | $8,500 |
| Engineering | $8,000 |
| Financial Planning | $7,500 |
| Architecture | $7,500 |
| IT Consulting | $7,000 |
| Insurance Broker | $6,500 |
| Management Consulting | $6,000 |
| Real Estate | $5,500 |

### Tier Modifiers

| Tier | Score | Modifier |
|------|-------|----------|
| 1 Preferred | 800+ | 0.75x |
| 2 Standard | 650-799 | 1.00x |
| 3 Elevated | 500-649 | 1.30x |
| 4 High Risk | 350-499 | 1.75x |
| 5 Critical | <350 | 2.50x |

### Firm Size Modifiers

| Size | Professionals | Modifier |
|------|---------------|----------|
| Solo | 1 | 1.20x |
| Micro | 2-5 | 1.10x |
| Small | 6-20 | 1.00x |
| Medium | 21-100 | 0.95x |
| Large | 101-500 | 0.90x |
| Major | 500+ | 0.85x |

---

## Critical Overrides

| Condition | Result |
|-----------|--------|
| License status score < 50 | Tier 4 minimum |
| Disciplinary history score < 40 | Tier 4 minimum |
| Active malpractice suits | Tier 3 minimum |
| Pending claims disclosed | Refer to senior UW |
| Coverage declined/non-renewed | Refer to senior UW |
| Failed peer review (accounting) | Tier 4 minimum |

---

## Direct Inquiry Questions (6 Maximum)

| Question | Type | Impact |
|----------|------|--------|
| Pending/threatened malpractice claims? | Yes/No | Critical if Yes |
| Pending disciplinary proceedings? | Yes/No | Critical if Yes |
| PI coverage declined/non-renewed (3 years)? | Yes/No | Critical if Yes |
| Significant practice area change (2 years)? | Yes/No | Flag for review |
| Merger/acquisition/spin-off (2 years)? | Yes/No | Flag for review |
| Major client loss (>25% revenue)? | Yes/No | Flag for review |

---

## Data Sources

| Source | Data Provided |
|--------|---------------|
| State Bar websites | License status, disciplinary records |
| PACER | Federal court litigation history |
| State courts | Civil litigation records |
| Chambers & Partners | Peer rankings, practice area ratings |
| Legal 500 | Firm and attorney rankings |
| Martindale-Hubbell | Peer review ratings |
| Best Lawyers | Recognition lists |
| AICPA | Peer review directory |
| PCAOB | Audit firm registration |
| State licensing boards | Professional licenses |
| SSL Labs | TLS configuration |
| Glassdoor | Employee reviews, retention signals |
| LinkedIn | Firm size, tenure, network |

---

## Example Output

```
======================================================================
DSI PROFESSIONAL INDEMNITY ASSESSMENT
======================================================================

Entity: Smith & Associates LLP
Profession: law_firm
Size: medium | Revenue: 5m_25m

──────────────────────────────────────────────────────────────────────
COMPOSITE SCORE: 826/1000
TIER: TIER_1 (1)
CONFIDENCE: 95%
──────────────────────────────────────────────────────────────────────

CATEGORY SCORES:
  Network Authority          72.0/100 ██████████████░░░░░░
  Regulatory Standing        88.1/100 █████████████████░░░
  Firm Stability             82.1/100 ████████████████░░░░
  Practice Quality           83.6/100 ████████████████░░░░
  Technical Infrastructure   84.4/100 ████████████████░░░░
  Corporate Footprint        79.2/100 ███████████████░░░░░
  Litigation History         92.0/100 ██████████████████░░

──────────────────────────────────────────────────────────────────────
FLAGS:

  ✓ GREEN FLAGS:
    • High-quality client base
    • Long-established practice (20+ years)
    • No complaints to professional bodies

──────────────────────────────────────────────────────────────────────
DECISION:
  Action: APPROVE
  Rationale: Tier 1 risk with no red flags - auto-approve with preferred pricing

──────────────────────────────────────────────────────────────────────
PRICING:
  Base Premium:     $12,920
  Risk Modifier:    0.98x
  Adjusted Premium: $12,658
======================================================================
```

---

## Comparison: DSI vs Traditional PI Underwriting

| Aspect | Traditional | DSI |
|--------|-------------|-----|
| Primary data | Long-form application | Regulatory databases, public records |
| Disciplinary check | Self-reported | Bar/board database lookup |
| Malpractice history | Self-reported | Court records search |
| Peer recognition | Self-reported | Chambers, Martindale direct |
| Processing time | Days to weeks | Minutes |
| Consistency | Varies by underwriter | Algorithmic |
| Scalability | Manual-intensive | Fully automated Tier 1-2 |

---

## PI-Specific Considerations

### Multi-Professional Firms

Firms with multiple professional types (e.g., law + accounting) should be assessed for highest-risk professional class unless clear operational separation exists.

### Lateral Partner Acquisitions

When firms acquire laterals from other firms:
- Inherit prior acts exposure
- Check disciplinary history of incoming partners
- Consider claims-made implications

### Merger & Acquisition Situations

DSI can assess both:
- Current firm quality
- Historical trajectory (improving vs declining)

M&A activity should trigger review of:
- Combined disciplinary history
- Cultural integration signals
- Financial stability post-transaction

### Practice Area Concentration

High concentration in single risky practice area (e.g., >70% securities work) warrants additional loading beyond standard practice area modifier.


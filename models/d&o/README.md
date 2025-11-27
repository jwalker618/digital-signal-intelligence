# DSI Directors & Officers (D&O) Insurance Pricing Model v2.0

## Overview

This model implements Digital Signal Intelligence (DSI) for D&O insurance pricing, conforming to DSI Principles v1.0. It replaces traditional application-based underwriting with externally observable signals from SEC filings, court records, and public databases.

**Key Differentiator:** D&O is exceptionally suited to DSI because corporate governance creates extensive structured public records - SEC filings are machine-readable, court records are searchable, and governance metrics are quantifiable.

---

## DSI Principles Compliance

| Principle | Implementation |
|-----------|----------------|
| External Observability | All signals from SEC EDGAR, PACER, public databases |
| Machine Readability | SEC filings are structured; court records are searchable |
| Network Authority | Auditor quality, legal counsel, board networks, investor quality |
| Behavioral Inference | Insider trading patterns, filing timeliness, governance disclosure |
| Absence as Signal | Missing governance page, no ESG reporting, limited IR presence |
| Structured Data Utilization | Credit ratings, ESG scores, ISS governance scores |
| Minimal Direct Inquiry | 5 optional Yes/No questions for critical factors |
| Organizational Assessment | Company-level governance assessment |
| Simplicity in Scoring | Signal → Score → Tier → Price |
| Agentic Readiness | All components executable by AI |

---

## Signal Framework (42 Signals)

### Category Weights

| Category | Weight | Rationale |
|----------|--------|-----------|
| Network Authority | 10% | Quality of professional relationships |
| Governance | 25% | Board structure, independence, oversight |
| Financial | 20% | Accounting quality, controls, disclosure |
| Litigation | 25% | Prior claims predict future claims |
| Executive | 10% | Management stability and behavior |
| Corporate Footprint | 5% | Digital presence quality |
| Structured Data | 5% | Third-party ratings |

### Key Signals

**Governance (25%):**
- Board independence (% independent directors)
- CEO/Chair separation
- Committee structure
- Related party transactions
- Shareholder rights provisions

**Litigation (25%):**
- Securities class action history (35% of category)
- SEC enforcement history
- Derivative litigation
- Pending litigation disclosed

**Financial (20%):**
- Audit opinion (clean, qualified, going concern)
- Internal controls (SOX 404)
- Restatement history
- Filing timeliness

---

## Data Sources

| Source | Data Provided |
|--------|---------------|
| SEC EDGAR | 10-K, 10-Q, 8-K, DEF 14A, Form 4 |
| PACER | Federal litigation records |
| SCAC | Securities class action database |
| SEC AAER | Enforcement releases |
| ISS | Governance scores |
| MSCI/S&P | ESG and credit ratings |

---

## Direct Inquiry Questions (5 Maximum)

| Question | Impact |
|----------|--------|
| Pending or threatened securities claims? | -200 if Yes |
| Regulatory investigations in past 24 months? | -100 if Yes |
| Planned M&A/restructuring/capital raising? | -50 if Yes |
| In compliance with debt covenants? | -100 if No |
| Executive departures under dispute? | -75 if Yes |

---

## Pricing Structure

### Base Premium by Tier ($1M limit, mid-cap)

| Tier | Score | Premium |
|------|-------|---------|
| 1 Preferred | 800+ | $4,000 |
| 2 Standard | 650-799 | $6,000 |
| 3 Elevated | 500-649 | $9,000 |
| 4 High Risk | 350-499 | $15,000 |
| 5 Critical | <350 | $25,000 |

### Key Multipliers

| Factor | Range |
|--------|-------|
| Company Type | 0.40x (nonprofit) to 3.50x (SPAC) |
| Industry | 0.90x (manufacturing) to 2.50x (crypto) |
| Limit | 1.00x ($1M) to 16.00x ($100M) |

---

## Critical Overrides

| Condition | Minimum Tier |
|-----------|--------------|
| Securities litigation score < 40 | Tier 4 |
| SEC enforcement score < 40 | Tier 4 |
| Material weakness (controls < 40) | Tier 3 |
| Restatement history (< 50) | Tier 3 |
| Going concern (audit < 30) | Tier 4 |
| Pending claims disclosed | Tier 4 |

---

## Example Output

```
Company: TechGiant Corp (TGNT)
Type: PUBLIC_LARGE_CAP | Industry: TECHNOLOGY

Composite Score: 942/1000 | Confidence: 95%

Category Scores:
  governance: 90/100
  litigation: 95/100
  financial: 93/100
  network_authority: 89/100
  executive: 88/100

Tier: 1 (Preferred)
Decision: APPROVE
Limit: $100,000,000
Premium: $200,000
```

---

*Conforms to DSI Principles v1.0*

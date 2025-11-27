# DSI Energy Insurance Pricing Model v2.0

## Overview

This model implements Digital Signal Intelligence (DSI) for energy insurance pricing, conforming to DSI Principles v1.0. It replaces traditional asset-by-asset engineering assessments with operator-level behavioral analysis based on publicly observable safety and environmental signals.

**Key DSI Principle:** We assess OPERATOR safety culture and operational patterns, not individual asset characteristics. Good operators maintain all assets well; poor operators have systemic issues across their portfolio.

**Energy Insurance Suitability for DSI:**
- OSHA/BSEE safety records are public and structured
- EPA violations are searchable databases
- Satellite imagery reveals operational patterns (flaring, facility activity)
- SEC filings disclose environmental liabilities
- Industry benchmarking data is available

---

## DSI Principles Compliance

| Principle | Implementation |
|-----------|----------------|
| External Observability | OSHA, EPA, BSEE records; satellite imagery |
| Machine Readability | Regulatory databases are structured and API-accessible |
| Network Authority | JV partners, contractor quality, regulator relationships |
| Behavioral Inference | Safety metrics, spill history, maintenance patterns |
| Absence as Signal | Missing ESG reporting, no industry membership |
| Structured Data Utilization | ESG ratings, credit ratings |
| Minimal Direct Inquiry | 6 optional questions |
| Organizational Assessment | Operator-level, not asset-level |
| Simplicity in Scoring | Signal → Score → Tier → Price |
| Agentic Readiness | All sources programmatically accessible |

---

## The Operator-Level Approach

Traditional energy underwriting requires engineering surveys of individual assets. DSI inverts this:

| Traditional | DSI |
|-------------|-----|
| Individual asset surveys | Operator behavior patterns |
| Asset-by-asset pricing | Fleet-wide safety performance |
| Engineering reports | OSHA/EPA compliance records |
| On-site inspections | Satellite-derived operational patterns |
| One asset, one price | Operator profile → portfolio pricing |

**Why this works:** Operators with strong safety cultures don't have random unsafe assets. Poor operators have systemic issues that appear in regulatory records, incident rates, and observable behavior patterns.

---

## Signal Framework (43 Signals)

### Category Weights

| Category | Weight | Rationale |
|----------|--------|-----------|
| Network Authority | 10% | Quality of industry relationships |
| Safety Performance | 30% | OSHA, BSEE, process safety - critical |
| Environmental Compliance | 20% | EPA, spills - liability exposure |
| Operational Telemetry | 10% | Satellite, production patterns |
| Financial Stability | 10% | Affects maintenance investment |
| Asset Portfolio | 10% | Age, complexity, concentration |
| Corporate Footprint | 5% | Digital presence |
| Structured Data | 5% | Third-party ratings |

### Key Signal Categories

#### Safety Performance (30%)
*From OSHA, BSEE, industry databases*

| Signal | Weight | What It Measures |
|--------|--------|------------------|
| OSHA TRIR | 20% | Total Recordable Incident Rate vs benchmark |
| OSHA Violations | 15% | Serious/willful violations |
| BSEE Incidents | 10% | Offshore incidents (if applicable) |
| Process Safety | 20% | Tier 1/Tier 2 PSE rates |
| Fatality History | 15% | Work-related fatalities |
| Major Incidents | 15% | Explosions, blowouts, major spills |

#### Environmental Compliance (20%)
*From EPA, state agencies, satellite data*

| Signal | Weight | What It Measures |
|--------|--------|------------------|
| EPA Violations | 20% | CAA, CWA, RCRA violations |
| Spill History | 25% | NRC reports, state records |
| Emissions Compliance | 15% | Air permit compliance |
| Flaring | 15% | Satellite-derived flaring intensity |
| Methane | 15% | Satellite-derived methane emissions |
| Remediation | 10% | Remediation obligations |

---

## Network Authority Signals

Energy network authority captures who trusts the operator:

### JV Partner Quality

**What it measures:** Quality of joint venture partners.

**Why it matters:** Supermajors and quality NOCs only partner with operators meeting their HSE standards. Being trusted by Shell, Chevron, or Equinor is strong network authority.

**Scoring:**
| Score | Criteria |
|-------|----------|
| 90-100 | Supermajor JV partners, operated assets |
| 75-89 | Major independent JV partners |
| 60-74 | Regional operator partners |
| 40-59 | Limited JV activity |
| 0-39 | No quality JV relationships |

### Contractor Quality

**What it measures:** Relationships with tier-1 service companies.

**Why it matters:** Top service companies (Schlumberger, Halliburton, Baker Hughes) have HSE requirements for operators they work with.

**Scoring:**
| Score | Criteria |
|-------|----------|
| 90-100 | Exclusive tier-1 contractor relationships |
| 75-89 | Primarily tier-1 contractors |
| 60-74 | Mix of tier-1 and tier-2 |
| 40-59 | Primarily tier-2/3 contractors |
| 0-39 | Unknown or concerning contractors |

---

## Safety Performance Signals

### OSHA Total Recordable Incident Rate (TRIR)

**What it measures:** Recordable incidents per 200,000 hours worked.

**Collection method:**
- OSHA inspection database
- SEC filings (sustainability reports)
- Industry benchmarking databases

**Scoring:**
| Score | Criteria |
|-------|----------|
| 90-100 | TRIR <0.5 (top quartile) |
| 75-89 | TRIR 0.5-1.0 |
| 60-74 | TRIR 1.0-2.0 (industry average) |
| 40-59 | TRIR 2.0-4.0 |
| 0-39 | TRIR >4.0 or major concerns |

### Process Safety Events

**What it measures:** Tier 1 and Tier 2 process safety events.

**Why it matters:** Process safety events (releases, fires, explosions) are the primary source of major energy insurance claims.

**Scoring:**
| Score | Criteria |
|-------|----------|
| 95-100 | Zero Tier 1 PSE in past 5 years |
| 80-94 | Single Tier 1 PSE, no pattern |
| 60-79 | Multiple Tier 1 PSE, improving trend |
| 40-59 | Multiple Tier 1 PSE, no improvement |
| 0-39 | Major process safety concerns |

---

## Environmental Compliance Signals

### Spill History

**What it measures:** Reportable spills from NRC and state databases.

**Collection method:**
- National Response Center (NRC) reports
- State environmental agency records
- EPA enforcement database
- SEC environmental disclosures

**Scoring:**
| Score | Criteria |
|-------|----------|
| 95-100 | No reportable spills in 5 years |
| 80-94 | Minor spills only, rapid response |
| 60-79 | Moderate spills, remediated |
| 40-59 | Significant spill history |
| 0-39 | Major spills or ongoing issues |

### Flaring Intensity (Satellite-Derived)

**What it measures:** Gas flaring relative to production.

**Collection method:**
- VIIRS satellite nightfire data
- World Bank GGFR database
- Operator-reported data validation

**Why it matters:** Excessive flaring indicates poor operational practices and environmental performance.

**Scoring:**
| Score | Criteria |
|-------|----------|
| 90-100 | Near-zero flaring, gas capture |
| 75-89 | Below industry average |
| 60-74 | Industry average |
| 40-59 | Above average flaring |
| 0-39 | Excessive flaring |

---

## Direct Inquiry Questions (6 Maximum)

| Question | Type | Impact |
|----------|------|--------|
| Major incidents in past 5 years? | Yes/No | -150 if Yes, +50 if No |
| Fatalities in past 3 years? | Yes/No | -100 if Yes, +30 if No |
| Pending regulatory enforcement? | Yes/No | -75 if Yes |
| Unfunded decommissioning obligations? | Yes/No | -50 if Yes |
| JV operator status? | Yes/No | Informational |
| Third-party contractors for D&C? | Yes/No | Informational |

---

## Pricing Structure

### Base Rate by Tier (per $1M TIV)

| Tier | Score | Rate |
|------|-------|------|
| 1 Preferred | 800+ | 0.08% |
| 2 Standard | 650-799 | 0.12% |
| 3 Elevated | 500-649 | 0.18% |
| 4 High Risk | 350-499 | 0.28% |
| 5 Critical | <350 | 0.45% |

### Operator Type Multipliers

| Type | Multiplier |
|------|------------|
| Supermajor | 0.75x |
| Major Integrated | 0.85x |
| Large Independent | 0.95x |
| Mid Independent | 1.00x |
| Small Independent | 1.20x |
| Private Equity | 1.15x |
| National Oil | 0.90x |
| Unknown | 1.40x |

### Segment Multipliers

| Segment | Multiplier |
|---------|------------|
| Renewable | 0.70x |
| Midstream Pipeline | 0.80x |
| Midstream Storage | 0.85x |
| Power Generation | 0.90x |
| Upstream Unconventional | 0.95x |
| Upstream Conventional | 1.00x |
| Midstream Processing | 1.00x |
| Upstream Offshore | 1.20x |
| Downstream Petrochemical | 1.25x |
| Downstream Refining | 1.30x |
| Upstream Deepwater | 1.50x |

### Geography Multipliers

| Geography | Multiplier |
|-----------|------------|
| US Onshore | 1.00x |
| Global Diversified | 1.05x |
| Asia-Pacific | 1.10x |
| US Gulf Shelf | 1.10x |
| North Sea | 1.15x |
| Middle East | 1.20x |
| Latin America | 1.20x |
| West Africa | 1.25x |
| US Gulf Deepwater | 1.40x |

---

## Critical Overrides

| Condition | Result |
|-----------|--------|
| Major incident score < 40 | Tier 4 minimum |
| Fatality score < 50 | Tier 3 minimum |
| OSHA violations score < 40 | Tier 3 minimum |
| EPA violations score < 40 | Tier 3 minimum |
| Major spill history (< 40) | Tier 4 minimum |
| Restructuring history (< 40) | Tier 4 minimum |
| Major incidents disclosed | Tier 4 minimum |
| Fatalities disclosed | Tier 3 minimum |

---

## Data Sources

| Source | Data Provided |
|--------|---------------|
| OSHA | Inspection records, violations, incident rates |
| BSEE | Offshore incidents, INCs |
| EPA | Violations, enforcement actions, spills |
| NRC | Reportable spill reports |
| SEC EDGAR | 10-K environmental disclosures |
| VIIRS Satellite | Flaring intensity |
| GHGSat/Kayrros | Methane emissions |
| MSCI/Sustainalytics | ESG ratings |
| State Agencies | Permits, violations, remediation |

---

## Example Output

```
Operator: PetroCorp International
Type: MAJOR_INTEGRATED | Segment: MIXED
Geography: GLOBAL_DIVERSIFIED

Composite Score: 947/1000 | Confidence: 95%

Category Scores:
  safety_performance: 90/100
  environmental_compliance: 83/100
  financial_stability: 88/100
  network_authority: 88/100
  operational_telemetry: 86/100

Tier: 1 (Preferred)
Decision: APPROVE

Total Insured Value: $5,000,000,000
Annual Premium: $3,748,500
Rate: 0.075%
Deductible: $10,000,000
```

---

## Comparison: DSI vs Traditional Energy Underwriting

| Aspect | Traditional | DSI |
|--------|-------------|-----|
| Unit of assessment | Individual asset | Operator portfolio |
| Primary data | Engineering surveys | Regulatory records |
| Processing time | Weeks (survey scheduling) | Minutes |
| Safety assessment | Self-reported questionnaire | OSHA/BSEE databases |
| Environmental check | Application questions | EPA records + satellite |
| On-site requirement | Per major asset | Sample-based Tier 3+ |
| Scalability | Linear with assets | Constant per operator |

---

## Energy-Specific Considerations

### Segment Risk Variation

Energy covers widely different risk profiles:
- Deepwater offshore: High severity, complex operations
- Onshore unconventional: High frequency, lower severity
- Refining: Process safety, high values
- Midstream: Linear exposures, third-party liability

DSI handles this through segment multipliers while maintaining operator-level assessment.

### Financial Stability Impact

Unlike some lines, energy operator financial health directly affects:
- Maintenance investment levels
- Decommissioning obligation coverage
- Contractor quality affordable
- Response capability

Financial signals are weighted accordingly.

---

*Conforms to DSI Principles v1.0*

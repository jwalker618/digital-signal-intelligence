# DSI Aerospace Insurance Pricing Model v2.0

## Overview

This model implements Digital Signal Intelligence (DSI) for aerospace insurance pricing, conforming to Foundational Principles. It replaces traditional application-based aviation underwriting with observable signals from safety databases, regulatory bodies, fleet registries, and operational telemetry.

**Coverage Types:**
- Aviation Hull & Liability (Airlines)
- Aviation Hull & Liability (General Aviation)
- Aircraft Products Liability
- Airport Liability
- Aviation War & Terrorism
- Grounding/Loss of Use

**Key DSI Principle:** We assess OPERATOR safety culture and operational discipline, not individual aircraft. A well-managed operator's organisational behaviour indicates fleet-wide quality (DSI Principle 8: Parent-to-Subsidiary Inference).

---

## Why Aerospace is Ideal for DSI

Aviation is arguably the most documented industry in the world:

| Data Type | Availability | Source |
|-----------|--------------|--------|
| Accident/Incident Records | Comprehensive | NTSB, ICAO, ASN |
| Regulatory Standing | Complete | FAA, EASA, national CAAs |
| Safety Audits | Standardised | IOSA Registry |
| Fleet Data | Public | FAA/EASA registries |
| Ramp Inspections | Available | SAFA/SACA databases |
| Enforcement Actions | Public | FAA/EASA databases |
| Banned Carriers | Public | EU Air Safety List |

---

## Signal Framework (50+ Signals)

### Category Weights by Operator Type

| Category | Major Airline | Regional | Helicopter | Charter |
|----------|---------------|----------|------------|---------|
| Network Authority | 15% | 10% | 5% | 5% |
| Safety Record | 25% | 25% | 30% | 25% |
| Regulatory Compliance | 20% | 20% | 25% | 25% |
| Operational Quality | 15% | 15% | 15% | 15% |
| Fleet Quality | 10% | 15% | 10% | 15% |
| Financial Stability | 5% | 5% | 5% | 5% |
| Route Risk | 5% | 5% | 5% | 5% |
| Corporate Governance | 5% | 5% | 5% | 5% |

### Signal Categories

#### 1. Network Authority (Type 1)
*Who trusts this operator?*

| Signal | Source | What It Reveals |
|--------|--------|-----------------|
| Alliance Membership | Alliance websites | Quality endorsement from major carriers |
| Code-share Partners | OAG schedules | Operational trust from peers |
| Lessor Quality | Fleet databases | AerCap, GECAS = strong signal |
| MRO Relationships | Public announcements | Lufthansa Technik, SR Technics = quality |
| OEM Support | Press releases | Direct manufacturer relationships |

#### 2. Safety Record (Type 6)
*Observable safety performance*

| Signal | Source | What It Reveals |
|--------|--------|-----------------|
| Hull Losses | ASN, NTSB | Catastrophic events |
| Fatal Accidents | ICAO, NTSB | Worst outcomes |
| Serious Incidents | NTSB, EASA | Near-misses, precursor events |
| Accident Rate | JACDEC | Performance vs industry benchmark |
| Investigation Findings | Investigation reports | Systemic vs isolated issues |

#### 3. Regulatory Compliance (Type 6)
*Regulatory standing and audit results*

| Signal | Source | What It Reveals |
|--------|--------|-----------------|
| Certificate Status | FAA/EASA | Active, restricted, or suspended |
| IOSA Registration | IATA IOSA Registry | Third-party operational validation |
| Enforcement Actions | FAA/EASA databases | Fines, suspensions, restrictions |
| Ramp Inspections | SAFA/SACA | Real-world operational standards |
| EU Safety List | EC Transport | Banned or restricted operators |
| AD Compliance | FAA SDRs | Airworthiness directive response |

#### 4. Operational Quality (Type 3 & 6)
*Observable operational discipline*

| Signal | Source | What It Reveals |
|--------|--------|-----------------|
| On-Time Performance | Cirium, OAG | Operational discipline proxy |
| Dispatch Reliability | Industry data | Technical reliability |
| Training Programs | Regulatory filings | FAA AQP, EASA compliance |
| SMS Maturity | Audit reports | Safety management sophistication |
| Crew Experience | Public data | Captain hours, training standards |

#### 5. Fleet Quality (Type 6)
*Fleet composition and maintenance*

| Signal | Source | What It Reveals |
|--------|--------|-----------------|
| Average Fleet Age | Registry data | Older fleet = higher maintenance risk |
| Fleet Homogeneity | Fleet databases | Single type = operational efficiency |
| Aircraft Generation | OEM data | Current vs legacy technology |
| Maintenance Program | Regulatory filings | MSG-3 vs older programs |
| Heavy Check Currency | Airline disclosures | C/D check compliance |

---

## Risk Modifiers

### Regulatory Framework

| Framework | Modifier | Rationale |
|-----------|----------|-----------|
| FAA | 1.00x | Baseline |
| EASA | 1.00x | Equivalent |
| CAA UK | 1.00x | Equivalent |
| Other ICAO | 1.15x | Variable oversight |
| Non-ICAO | 1.40x | Significant concern |

### Fleet Category

| Category | Modifier | Rationale |
|----------|----------|-----------|
| Helicopter | 1.30x | Higher accident rates |
| Piston | 1.20x | GA risk profile |
| Business Jet | 1.15x | High utilization |
| Widebody | 1.10x | Higher values |
| Regional Jet | 1.05x | Baseline+ |
| Narrowbody | 1.00x | Baseline |
| Turboprop | 0.95x | Lower values |

### IOSA Status

| Status | Modifier | Rationale |
|--------|----------|-----------|
| Registered | 0.90x | Third-party validated |
| Expired | 1.15x | Lapsed validation |
| Never Registered | 1.25x | No external validation |

---

## Critical Overrides

| Condition | Result |
|-----------|--------|
| EU Air Safety List (banned) | Automatic decline |
| Fatal accident (recent) | Tier 4 minimum |
| Certificate suspended/restricted | Tier 4 minimum |
| Pending regulatory action | Refer to senior UW |
| Prior coverage declined | Refer to senior UW |

---

## Pricing Structure

### Base Rates (per $1M)

| Operator Type | Hull Rate | Liability Rate |
|---------------|-----------|----------------|
| Major Airline | $800 | $500 |
| Regional Airline | $1,200 | $700 |
| Low Cost Carrier | $1,000 | $600 |
| Cargo Airline | $1,500 | $400 |
| Charter Operator | $1,800 | $900 |
| Corporate Flight | $2,000 | $800 |
| Helicopter Operator | $4,000 | $2,000 |
| Flight School | $3,000 | $1,500 |

### Tier Modifiers

| Tier | Score | Modifier |
|------|-------|----------|
| 1 Preferred | 800+ | 0.75x |
| 2 Standard | 650-799 | 1.00x |
| 3 Elevated | 500-649 | 1.35x |
| 4 High Risk | 350-499 | 1.85x |
| 5 Critical | <350 | 2.75x |

---

## Data Sources

### Safety Data
- **NTSB** (ntsb.gov) — US accidents and incidents
- **Aviation Safety Network** (aviation-safety.net) — Global accident database
- **ICAO** (icao.int) — International safety statistics
- **JACDEC** — Accident rates and rankings

### Regulatory Data
- **FAA** (faa.gov) — Certificates, enforcement, airworthiness
- **EASA** (easa.europa.eu) — European certification and safety
- **EU Air Safety List** (transport.ec.europa.eu) — Banned carriers
- **IOSA Registry** (iata.org/iosa) — Operational safety audits
- **SAFA/SACA** — Ramp inspection results

### Fleet Data
- **FAA Registry** (registry.faa.gov) — US registrations
- **Planespotters.net** — Global fleet databases
- **ch-aviation.com** — Fleet and operations data

---

## Direct Inquiry Questions (6 Maximum)

| Question | Type | Impact |
|----------|------|--------|
| Pending/threatened aviation liability claims? | Yes/No | Critical |
| Pending regulatory enforcement action? | Yes/No | Critical |
| Aviation coverage declined/non-renewed (3 years)? | Yes/No | Critical |
| New aircraft type additions planned (12 months)? | Yes/No | Flag for review |
| Expansion to high-risk destinations planned? | Yes/No | Flag for review |
| Change in ownership/control (24 months)? | Yes/No | Flag for review |

---

## Example Output

```
======================================================================
DSI AEROSPACE INSURANCE ASSESSMENT
======================================================================

Entity: Horizon Regional Airlines
Operator: regional_airline | Fleet: regional_jet | Size: medium
Regulatory: faa | IOSA: registered

──────────────────────────────────────────────────────────────────────
COMPOSITE SCORE: 876/1000 | TIER: TIER_1 | CONFIDENCE: 85%
──────────────────────────────────────────────────────────────────────

CATEGORY SCORES:
  Network Authority          79.3/100 ███████████████░░░░░
  Safety Record              90.8/100 ██████████████████░░
  Regulatory Compliance      92.6/100 ██████████████████░░
  Operational Quality        86.2/100 █████████████████░░░
  Fleet Quality              86.7/100 █████████████████░░░
  Financial Stability        72.3/100 ██████████████░░░░░░
  Route Risk                 91.7/100 ██████████████████░░
  Corporate Governance       86.5/100 █████████████████░░░

  ✓ GREEN FLAGS: Tier 1 lessor relationships, Current IOSA registration

──────────────────────────────────────────────────────────────────────
DECISION: APPROVE - Tier 1 risk - auto-approve with preferred pricing

COVERAGE: Hull $750,000,000 | Liability $1,000,000,000
PRICING: Base $984,616 | Modifier 0.71x | Final $697,847
======================================================================
```

---

## Aerospace-Specific Considerations

### Lessor Relationships as Quality Signal
Aircraft lessors conduct extensive due diligence before placing aircraft. Tier 1 lessors (AerCap, SMBC, Avolon) only lease to operators meeting strict standards. Their willingness to place aircraft is a strong quality endorsement.

### IOSA as Third-Party Validation
The IATA Operational Safety Audit (IOSA) provides standardised, third-party operational assessment. IOSA registration is effectively a quality certification that's difficult to obtain and maintain.

### Fleet Homogeneity
Single-type fleets (all 737, all A320) indicate operational efficiency, simplified training, and maintenance advantages. Mixed fleets increase complexity and potential for error.

### Cargo Operators
Cargo airlines often operate older aircraft with more night operations. They require careful assessment but shouldn't automatically be penalised — well-managed cargo operators like FedEx and UPS have excellent safety records.

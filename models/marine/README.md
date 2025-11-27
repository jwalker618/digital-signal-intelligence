# DSI Marine Insurance Pricing Model v2.0

## Overview

This model implements Digital Signal Intelligence (DSI) for marine insurance pricing, conforming to DSI Principles v1.0. It replaces traditional vessel-by-vessel underwriting with operator-level assessment based on observable behavioral patterns.

**Key DSI Principle:** We assess OPERATOR behavior, not individual vessels. A well-managed operator's fleet-wide patterns indicate individual vessel quality. This enables scalable underwriting without vessel-by-vessel analysis.

**Unique Marine Advantage:** Marine insurance is exceptionally suited to DSI because:
- AIS provides real-time behavioral telemetry
- Port State Control databases are public and structured
- Classification society records are accessible
- IMO databases provide authoritative vessel/company data
- Sanctions screening is well-established

---

## DSI Principles Compliance

| Principle | Implementation |
|-----------|----------------|
| External Observability | AIS tracking, PSC databases, classification records |
| Machine Readability | IMO GISIS, Equasis, Paris/Tokyo MoU are structured |
| Network Authority | Class society, P&I club, charterer relationships |
| Behavioral Inference | Fleet AIS patterns reveal operational discipline |
| Absence as Signal | AIS gaps, missing class notations, no industry membership |
| Structured Data Utilization | RightShip scores, ESG ratings |
| Minimal Direct Inquiry | 5 optional questions |
| Organizational Assessment | Operator-level, not vessel-level |
| Simplicity in Scoring | Signal → Score → Tier → Price |
| Agentic Readiness | All data sources API-accessible |

---

## The Operator-Level Approach

Traditional marine underwriting prices individual vessels. DSI inverts this:

| Traditional | DSI |
|-------------|-----|
| Vessel survey | Operator behavior patterns |
| Individual vessel age | Fleet age profile |
| Single vessel PSC record | Fleet-wide PSC performance |
| Vessel-specific AIS | Fleet AIS compliance patterns |
| One vessel, one price | Operator profile → fleet pricing |

**Why this works:** Operators with strong safety cultures don't have random bad vessels. Poor operators don't have random good vessels. Organizational behavior propagates to assets.

---

## Signal Framework (39 Signals)

### Category Weights

| Category | Weight | Rationale |
|----------|--------|-----------|
| Network Authority | 15% | Quality of maritime relationships |
| Operational Telemetry | 20% | AIS behavioral patterns |
| Safety Compliance | 25% | PSC, class status - direct claims predictors |
| Fleet Profile | 10% | Age, quality, consistency |
| Sanctions Compliance | 15% | Critical - can void coverage |
| Environmental | 5% | Regulatory compliance |
| Corporate Footprint | 5% | Digital presence |
| Structured Data | 5% | Third-party ratings |

### Key Signal Categories

#### Operational Telemetry (20%)
*From AIS tracking - behavioral patterns at fleet level*

| Signal | Weight | What It Measures |
|--------|--------|------------------|
| AIS Compliance | 25% | Transmission consistency across fleet |
| Dark Activity | 25% | AIS gaps in suspicious locations |
| Route Risk | 20% | High-risk area exposure |
| Operational Efficiency | 10% | Speed/fuel patterns indicating discipline |

#### Safety Compliance (25%)
*From PSC databases, classification societies*

| Signal | Weight | What It Measures |
|--------|--------|------------------|
| PSC Detention Rate | 25% | Detentions per inspection |
| PSC Deficiency Rate | 20% | Deficiencies per inspection |
| Class Status | 20% | In class, conditions, recommendations |
| ISM Compliance | 15% | Document of Compliance status |
| Casualty History | 10% | Incidents, groundings, collisions |
| Total Loss History | 10% | Complete vessel losses |

#### Sanctions Compliance (15%)
*Critical for marine - violations void coverage*

| Signal | Weight | What It Measures |
|--------|--------|------------------|
| Sanctions Status | 30% | Direct OFAC/EU/UN sanctions |
| Ownership Transparency | 20% | Beneficial owner visibility |
| Jurisdiction Risk | 20% | High-risk country connections |
| STS Patterns | 15% | Ship-to-ship transfer activity |
| Historical Connections | 15% | Past sanctions involvement |

---

## Network Authority Signals

Marine network authority captures who trusts the operator:

### Classification Society Quality

**What it measures:** IACS membership and class society tier.

**Scoring:**
| Score | Criteria |
|-------|----------|
| 95-100 | Top IACS members (DNV, Lloyd's, BV, ABS) |
| 80-94 | Other IACS members |
| 60-79 | Recognized non-IACS societies |
| 40-59 | Lesser-known societies |
| 0-39 | Unknown or no classification |

### P&I Club Membership

**What it measures:** International Group membership vs fixed premium.

**Why it matters:** IG clubs (Gard, Britannia, UK Club, etc.) have rigorous entry standards. Fixed premium markets have lower barriers.

**Scoring:**
| Score | Criteria |
|-------|----------|
| 90-100 | Major IG club, long membership |
| 75-89 | IG club member |
| 60-74 | Smaller mutual clubs |
| 40-59 | Fixed premium market |
| 0-39 | Unknown or concerning coverage |

### Flag State Quality

**What it measures:** Paris MoU white/grey/black list status.

**Scoring:**
| Score | Criteria |
|-------|----------|
| 95-100 | White list flags (DK, NO, GB, SG, HK, JP) |
| 75-94 | Other white list flags |
| 50-74 | Grey list flags |
| 25-49 | Black list flags |
| 0-24 | Sanctioned or unknown flags |

---

## Operational Telemetry (AIS Behavioral Analysis)

### AIS Compliance

**What it measures:** Fleet-wide AIS transmission consistency.

**Collection method:**
- Aggregate AIS data for all fleet vessels
- Calculate transmission gap frequency and duration
- Identify systematic vs incidental gaps

**Why it matters:** Consistent AIS transmission indicates operational discipline. Systematic gaps suggest evasion.

**Scoring:**
| Score | Criteria |
|-------|----------|
| 95-100 | 99%+ transmission, no unexplained gaps |
| 85-94 | Minor gaps, all explainable |
| 70-84 | Moderate gaps, some concerns |
| 50-69 | Significant gaps |
| 0-49 | Systematic dark periods or manipulation |

### Dark Activity Patterns

**What it measures:** AIS disabling in suspicious locations.

**High-risk dark zones:**
- Near sanctioned waters (NK, Iran, Syria, Crimea)
- Known STS transfer areas
- Disputed maritime zones

**Scoring:**
| Score | Criteria |
|-------|----------|
| 95-100 | No dark activity in high-risk zones |
| 75-94 | Minimal dark activity, low-risk areas |
| 50-74 | Some concerning dark patterns |
| 25-49 | Significant high-risk dark activity |
| 0-24 | Systematic dark activity near sanctioned zones |

---

## Direct Inquiry Questions (5 Maximum)

| Question | Type | Impact |
|----------|------|--------|
| Total fleet size? | Number | Confidence adjustment |
| PSC detentions in past 36 months? | Yes/No | -75 if Yes, +25 if No |
| Total losses in past 5 years? | Yes/No | -150 if Yes, +50 if No |
| Third-party technical manager? | Yes/No | Informational |
| Trading to sanctioned regions? | Yes/No | -300 / DECLINE if Yes |

---

## Pricing Structure

### Base Rate by Tier (per $1M insured value)

| Tier | Score | Rate |
|------|-------|------|
| 1 Preferred | 800+ | 0.15% |
| 2 Standard | 650-799 | 0.22% |
| 3 Elevated | 500-649 | 0.32% |
| 4 High Risk | 350-499 | 0.50% |
| 5 Critical | <350 | 0.80% |

### Operator Type Multipliers

| Type | Multiplier |
|------|------------|
| Major Liner | 0.80x |
| Major Tanker | 0.90x |
| Major Bulk | 0.95x |
| Regional Operator | 1.00x |
| Independent | 1.25x |
| State-Owned | 1.10x |
| Unknown | 1.50x |

### Vessel Category Multipliers

| Category | Multiplier |
|----------|------------|
| LNG/LPG | 0.85x |
| Container | 0.90x |
| Dry Bulk | 1.00x |
| Tanker | 1.10x |
| General Cargo | 1.10x |
| Passenger | 1.25x |
| Offshore | 1.30x |

### Fleet Age Multipliers

| Average Age | Multiplier |
|-------------|------------|
| 0-5 years | 0.85x |
| 5-10 years | 0.95x |
| 10-15 years | 1.05x |
| 15-20 years | 1.20x |
| 20-25 years | 1.40x |
| 25+ years | 1.60x |

---

## Critical Overrides

| Condition | Result |
|-----------|--------|
| Sanctions status score < 30 | Tier 5 / Decline |
| Trading to sanctioned regions | Decline |
| Dark activity score < 30 | Tier 4 minimum |
| STS pattern score < 30 | Tier 4 minimum |
| PSC detention score < 40 | Tier 3 minimum |
| Total loss history | Tier 4 minimum |
| Class status score < 40 | Tier 4 minimum |

---

## Data Sources

| Source | Data Provided |
|--------|---------------|
| AIS Providers | Position, speed, transmission patterns |
| Paris MoU | European PSC inspections |
| Tokyo MoU | Asia-Pacific PSC inspections |
| Equasis | Vessel details, operator, fleet data |
| Classification Societies | Class status, surveys, notations |
| IMO GISIS | Ship particulars, DOC holder |
| OFAC/EU/UN | Sanctions designations |
| RightShip | Vetting scores |

---

## Example Output

```
Operator: Global Container Lines
Type: MAJOR_LINER | Category: CONTAINER
Fleet: 85 vessels | Avg Age: 8.5 years

Composite Score: 998/1000 | Confidence: 95%

Category Scores:
  network_authority: 91/100
  operational_telemetry: 91/100
  safety_compliance: 94/100
  fleet_profile: 89/100
  sanctions_compliance: 97/100

Tier: 1 (Preferred)
Decision: APPROVE

Total Insured Value: $2,500,000,000
Annual Premium: $2,180,250
Rate: 0.0872%
Deductible: $1,000,000
```

---

## Comparison: DSI vs Traditional Marine Underwriting

| Aspect | Traditional | DSI |
|--------|-------------|-----|
| Unit of assessment | Individual vessel | Operator fleet |
| Primary data | Survey reports, applications | AIS patterns, PSC records |
| Sanctions check | Vessel name screening | Behavioral pattern analysis |
| Processing | Days per vessel | Minutes per fleet |
| Survey requirement | Per vessel | Sample-based for Tier 3+ |
| Scalability | Linear with fleet size | Constant per operator |

---

## Marine-Specific Considerations

### Sanctions Risk

Sanctions are critical in marine insurance:
- Can void coverage entirely
- Create reinsurance issues
- Expose insurer to regulatory action

DSI addresses this through:
- Direct sanctions database screening
- AIS dark activity analysis
- STS transfer pattern detection
- Ownership transparency scoring

### Fleet vs Vessel Approach

DSI prices at operator level but conditions may require:
- Named vessel schedule for Tier 3+
- Individual surveys for vessels >15-20 years
- Specific values per vessel

This hybrid maintains DSI efficiency while allowing granularity where needed.

---

*Conforms to DSI Principles v1.0*

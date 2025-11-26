# DSI Marine Insurance Pricing Model

## Overview

The Marine Insurance pricing model applies Digital Signal Intelligence to hull & machinery, cargo, P&I, and marine liability coverages. Marine insurance is uniquely suited to DSI because vessel operations generate extensive digital footprints through AIS tracking, port state control databases, classification society records, and regulatory filings.

Unlike traditional marine underwriting that relies heavily on physical surveys and questionnaires, DSI continuously monitors observable digital signals that correlate with loss probability.

---

## Coverage Types Supported

| Coverage | Description | Key Risk Factors |
|----------|-------------|------------------|
| Hull & Machinery | Physical damage to vessel | Age, condition, operator quality |
| Cargo | Goods in transit | Trading routes, vessel type |
| Protection & Indemnity | Third-party liability | PSC record, crew quality |
| Marine Liability | Pollution, wreck removal | Environmental compliance |
| War Risks | War, piracy, terrorism | Trading areas, AIS patterns |
| Loss of Hire | Business interruption | Operator financials, maintenance |

---

## Signal Framework

### Signal Categories & Weights

```
Vessel Operations (25%)
├── AIS Compliance (8%)
├── Trading Pattern Risk (8%)
├── Port Call Risk (5%)
└── Dark Activity (4%)

Safety & Compliance (30%)
├── PSC Performance (10%)
├── Class Status (8%)
├── ISM Compliance (6%)
└── Vessel Age/Condition (6%)

Fleet/Operator (20%)
├── Operator Reputation (8%)
├── Technical Manager Quality (6%)
└── Fleet Performance (6%)

Financial & Sanctions (15%)
├── Owner Financial Stability (6%)
├── Sanctions Exposure (5%)
└── Beneficial Owner Transparency (4%)

Environmental (10%)
├── Environmental Compliance (5%)
├── Emissions Performance (3%)
└── Environmental Incidents (2%)
```

---

## Signal Definitions

### Vessel Operations Signals

#### AIS Compliance (8%)

**What it measures:** Automatic Identification System transmission patterns and compliance.

**Why it matters:** Vessels are legally required to transmit AIS continuously. Gaps or manipulation indicate potential regulatory evasion, sanctions violations, or illicit activity.

**Scoring rubric:**
| Score | Criteria |
|-------|----------|
| 95-100 | Continuous transmission, no gaps > 1 hour |
| 80-94 | Minor gaps (1-4 hours), explainable |
| 60-79 | Moderate gaps (4-24 hours) |
| 40-59 | Significant gaps (24-72 hours) |
| 0-39 | Extended dark periods or manipulation detected |

**Data source:** AIS tracking providers (MarineTraffic, VesselFinder, Spire)

#### Dark Activity (4%)

**What it measures:** Patterns of AIS disabling ("going dark") in suspicious locations.

**Why it matters:** Disabling AIS near sanctioned waters, during ship-to-ship transfers, or in unregulated zones is a major red flag for sanctions evasion, illegal fishing, or smuggling.

**High-risk dark zones:**
- North Korean EEZ
- Iranian waters
- Syrian waters
- Crimea region
- Known STS transfer hotspots

**Scoring rubric:**
| Score | Criteria |
|-------|----------|
| 90-100 | No suspicious dark activity |
| 70-89 | Minor dark events, explainable |
| 50-69 | Extended dark periods detected |
| 30-49 | Multiple extended dark periods |
| 0-29 | Dark events near high-risk zones |

### Safety & Compliance Signals

#### PSC Performance (10%)

**What it measures:** Port State Control inspection results from Paris MoU, Tokyo MoU, and other regional agreements.

**Why it matters:** PSC inspections are conducted by port authorities worldwide. Detentions and deficiency patterns are strong predictors of vessel condition and operator quality.

**Key metrics:**
- Detention ratio (detentions / inspections)
- Deficiency rate (deficiencies per inspection)
- Safety-critical deficiencies
- Trend (improving or deteriorating)

**Scoring rubric:**
| Score | Criteria |
|-------|----------|
| 90-100 | No detentions, < 1 deficiency/inspection |
| 75-89 | No detentions, < 2 deficiencies/inspection |
| 60-74 | < 5% detention rate |
| 40-59 | 5-15% detention rate |
| 20-39 | 15-30% detention rate |
| 0-19 | > 30% detention rate or safety-critical issues |

**Data source:** Paris MoU, Tokyo MoU, USCG PSC databases, Equasis

#### Class Status (8%)

**What it measures:** Classification society status, outstanding recommendations, and survey compliance.

**Why it matters:** Classification societies certify vessel seaworthiness. Class status is fundamental to insurability.

**Classification society tiers:**
- **IACS members:** LR, DNV, BV, ABS, NK, KR, CCS, RINA, RS, CRS, IRS, PRS
- **Recognized:** IRCLASS, VR, HR
- **Other:** Requires additional scrutiny

**Scoring rubric:**
| Score | Criteria |
|-------|----------|
| 90-100 | IACS class, in class, no conditions |
| 75-89 | IACS class, minor recommendations |
| 60-74 | Non-IACS or elevated recommendations |
| 40-59 | Conditions of class outstanding |
| 20-39 | Survey overdue |
| 0-19 | Class suspended or withdrawn |

**Data source:** Classification society records, Equasis

#### Vessel Age/Condition (6%)

**What it measures:** Vessel age combined with maintenance and condition indicators.

**Why it matters:** Age alone is not determinative—a well-maintained 20-year vessel may be better than a neglected 5-year vessel. DSI combines age with observable condition signals.

**Age baseline:**
| Age | Base Score |
|-----|------------|
| 0-5 years | 95 |
| 6-10 years | 85 |
| 11-15 years | 72 |
| 16-20 years | 58 |
| 21-25 years | 42 |
| 25+ years | 25 |

**Condition adjustments:**
- Dry dock overdue: -25 points
- Major repairs pending: -10 points each
- Machinery failures (12m): -8 points each

### Fleet/Operator Signals

#### Operator Reputation (8%)

**What it measures:** DOC (Document of Compliance) holder performance across their entire fleet.

**Why it matters:** The operator is often more important than the individual vessel. Poor operators have systemic issues that affect all vessels under their management.

**Key metrics:**
- Fleet detention rate (36 months)
- Total losses (5 years)
- Major incidents (5 years)
- Years in operation
- Fleet size (data confidence)

**Scoring rubric:**
| Score | Criteria |
|-------|----------|
| 85-100 | < 3% fleet detention rate, no losses |
| 70-84 | 3-8% detention rate |
| 55-69 | 8-15% detention rate or minor incidents |
| 40-54 | > 15% detention rate |
| 20-39 | Major incidents in fleet |
| 0-19 | Total losses in past 5 years |

**Data source:** Equasis fleet data, IMO GISIS

### Financial & Sanctions Signals

#### Sanctions Exposure (5%)

**What it measures:** Direct sanctions status, ownership opacity, and sanctions risk indicators.

**Why it matters:** Sanctions violations can void coverage and expose insurers to regulatory action. DSI identifies elevated risk before violations occur.

**Risk indicators:**
- Direct sanctions on vessel/owner
- STS transfers with sanctioned vessels
- Port calls to high-risk jurisdictions
- Opaque ownership structures (multiple layers)

**Scoring rubric:**
| Score | Criteria |
|-------|----------|
| 90-100 | Clean profile, transparent ownership |
| 70-89 | Complex ownership (2-3 layers) |
| 50-69 | Some high-risk port exposure |
| 30-49 | Opaque ownership (4+ layers) |
| 10-29 | Multiple high-risk indicators |
| 0 | Sanctioned—coverage not available |

**Data source:** OFAC, EU sanctions lists, UN sanctions, ownership databases

### Environmental Signals

#### Environmental Compliance (5%)

**What it measures:** Compliance with environmental regulations and incident history.

**Why it matters:** Environmental incidents create significant liability exposure and indicate operational quality.

**Key regulations:**
- IMO 2020 (sulphur cap)
- Ballast Water Management Convention
- MARPOL Annex I-VI
- CII (Carbon Intensity Indicator) ratings

**Scoring rubric:**
| Score | Criteria |
|-------|----------|
| 85-100 | Full compliance, CII A/B rating |
| 70-84 | Compliant, CII C rating |
| 55-69 | CII D/E rating |
| 40-54 | Compliance gaps (BWM, IMO 2020) |
| 20-39 | Environmental fines |
| 0-19 | Oil spill incidents |

---

## Risk Tier Classification

| Tier | Score | Classification | Premium Adjustment | Underwriting Action |
|------|-------|----------------|-------------------|---------------------|
| 1 | 750-1000 | Preferred | -25% | Auto-approve preferred |
| 2 | 600-749 | Standard | Baseline | Auto-approve standard |
| 3 | 450-599 | Elevated | +35% | Manual review required |
| 4 | 0-449 | High Risk | +100% | Decline or conditions |

---

## Pricing Model

### Base Rates (per $100 insured value, annual)

| Vessel Type | Base Rate |
|-------------|-----------|
| Container | $0.18 |
| Bulk Carrier | $0.20 |
| Crude Tanker | $0.25 |
| Product Tanker | $0.22 |
| Chemical Tanker | $0.28 |
| LNG Carrier | $0.15 |
| LPG Carrier | $0.18 |
| RoRo | $0.30 |
| General Cargo | $0.22 |
| Offshore | $0.35 |
| Passenger | $0.40 |
| Fishing | $0.45 |

### Trading Area Multipliers

| Trading Area | Multiplier |
|--------------|------------|
| Worldwide | 1.20x |
| Worldwide excl. War Zones | 1.00x |
| North Atlantic | 0.95x |
| Mediterranean | 0.90x |
| Asia Pacific | 1.00x |
| Middle East/Gulf | 1.15x |
| West Africa | 1.25x |
| Caribbean | 1.10x |
| Inland Waters | 0.85x |

### Premium Calculation

```
Final Premium = Base Premium × Trading Multiplier × DSI Adjustment × Age Loading

Where:
- Base Premium = (Insured Value / 100) × Base Rate
- DSI Adjustment = Tier-based multiplier (0.75x to 2.0x)
- Age Loading = 1.0x to 1.4x based on vessel age
```

---

## Data Sources

| Source | Data Provided | Update Frequency |
|--------|---------------|------------------|
| AIS Providers | Position, speed, course, gaps | Real-time |
| Paris MoU | PSC inspections (Europe) | Monthly |
| Tokyo MoU | PSC inspections (Asia-Pacific) | Monthly |
| Equasis | Vessel details, operator, fleet | Weekly |
| Classification Societies | Class status, surveys, recommendations | On change |
| IMO GISIS | Ship particulars, ISM, environmental | Monthly |
| Sanctions Lists | OFAC, EU, UN designations | Daily |
| Marine News | Incidents, casualties | Daily |

---

## API Integration

### Endpoints

```
POST /api/v2/marine/analyze
GET /api/v2/marine/score/{imo_number}
GET /api/v2/marine/signals/{imo_number}
POST /api/v2/marine/monitor
GET /api/v2/marine/fleet/{operator_id}
```

### Sample Request

```json
{
  "imo_number": "9876543",
  "coverage_types": ["hull_machinery", "pi"],
  "insured_value": 35000000,
  "trading_area": "worldwide_excluding_war_zones",
  "policy_period_days": 365
}
```

### Sample Response

```json
{
  "imo_number": "9876543",
  "vessel_name": "ATLANTIC PIONEER",
  "composite_score": 848,
  "tier": 1,
  "tier_label": "Preferred",
  "signals": {
    "ais_compliance": {"score": 85, "evidence": "Minor gaps detected"},
    "psc_performance": {"score": 92, "evidence": "Excellent record"},
    "class_status": {"score": 94, "evidence": "In class with DNV"}
  },
  "pricing": {
    "base_premium": 70000,
    "dsi_adjustment": 0.75,
    "final_premium": 52500,
    "rate_per_100": 0.15
  },
  "decision": "APPROVE",
  "action": "Auto-bind at preferred terms"
}
```

---

## Usage Example

```python
from marine_pricing_model import (
    MarinePricingModel, 
    MarineSignalScorer,
    VesselProfile, 
    MarineSubmission,
    VesselType,
    TradingArea,
    CoverageType
)
from datetime import datetime, timedelta

# Create vessel profile
vessel = VesselProfile(
    imo_number="9876543",
    vessel_name="ATLANTIC PIONEER",
    vessel_type=VesselType.BULK_CARRIER,
    flag_state="MH",
    gross_tonnage=45000,
    deadweight=82000,
    year_built=2015,
    classification_society="DNV",
    owner="Oceanic Shipping Ltd",
    operator="Global Bulk Carriers",
    technical_manager="Maritime Technical Services",
    insured_value=35000000,
    trading_area=TradingArea.WORLDWIDE_EXC_WAR
)

# Create submission
submission = MarineSubmission(
    submission_id="MAR-2025-001234",
    vessel=vessel,
    coverage_types=[CoverageType.HULL_MACHINERY],
    policy_period_start=datetime.now(),
    policy_period_end=datetime.now() + timedelta(days=365),
    deductible=150000,
    limit=35000000,
    broker="Marsh Marine"
)

# Score signals
scorer = MarineSignalScorer()
signals = {}

# Add signal data and score
ais_data = {"transmission_gaps": [], "manipulation_indicators": False}
signals["ais_compliance"] = scorer.score_ais_compliance(ais_data)

psc_data = {"inspections_36_months": 8, "detentions_36_months": 0, "deficiencies_36_months": 10}
signals["psc_performance"] = scorer.score_psc_performance(psc_data)

# Generate decision
model = MarinePricingModel()
composite, confidence = model.calculate_composite_score(signals)
decision = model.generate_underwriting_decision(submission, signals, composite)

print(f"Score: {composite:.0f}, Tier: {decision['tier']}, Premium: ${decision['pricing']['final_premium']:,.0f}")
```

---

## Flag State Risk Tiers

| Tier | Flag States | Treatment |
|------|-------------|-----------|
| Tier 1 (White List) | GB, NO, DK, NL, DE, FR, SG, JP, HK, AU | Standard terms |
| Tier 2 | MT, CY, GR, IT, US, CA, KR, TW | Standard terms |
| Tier 3 (Open Registry) | LR, MH, PA, BS | Additional scrutiny |
| Tier 4 (High Risk) | KH, TZ, TG, CM | Manual review required |

---

## Validation

The Marine DSI model has been validated against:

- **Historical loss data:** Correlation between DSI scores and claims frequency/severity
- **PSC detention prediction:** 85% accuracy in predicting vessels that will be detained
- **Operator performance:** Fleet-level scores correlate with operator loss ratios

---

## Contact

For implementation support or API access, contact John Walker.

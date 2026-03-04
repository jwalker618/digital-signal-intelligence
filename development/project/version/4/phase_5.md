# Phase 5: Energy Coverage Expansion — Full Spectrum Configuration Suite

## Context & Motivation

Energy is the most complex coverage class in commercial insurance. Unlike cyber (where risk is fundamentally digital) or D&O (where risk is fundamentally governance), energy risk spans *physical*, *environmental*, *geopolitical*, *financial*, and *transitional* dimensions simultaneously. A deepwater drilling platform in the Gulf of Mexico shares almost nothing — actuarially, operationally, or legally — with a utility-scale solar farm in West Texas or a pipeline network crossing three US states.

Yet today, DSI has a single `energy_general` configuration attempting to price all of it.

Every other coverage in the platform (cyber, D&O, PI, FI, aerospace, marine) already has at least two configurations — a `_general` corporate model and an `_sme` automated model. Energy has neither the segment specificity nor the market breadth to demonstrate what DSI can actually do.

This phase corrects that. We will build **eleven new configurations** that, together with the existing `energy_general`, form a complete underwriting toolkit for the global energy market. Each configuration is purpose-built for a distinct segment of the energy value chain, with its own signal architecture, pricing philosophy, and underwriting logic.

### Why This Matters for Production & Demo

1. **Production Pipeline Readiness**: Energy configurations will be among the first to face real submission data. The `energy_general` model is too broad to produce credible pricing for specialist segments. A deepwater operator should not be priced with the same signal weights as a pipeline company.

2. **Demo Credibility**: When demonstrating DSI to energy underwriters, Lloyd's syndicates, or reinsurers, the system must show that it *understands* the difference between upstream, midstream, and downstream. A single configuration cannot do this. An underwriter who sees "Operator Type: SUPERMAJOR, applied: 0.75" as a flat modifier will immediately question whether the system understands the nuance.

3. **Multiplexer Demonstration**: The V4 multiplexer routes submissions to the most specific applicable configuration. With twelve energy configurations at varying `model_specificity` levels, energy becomes the definitive showcase for intelligent routing.

---

## The Twelve-Configuration Architecture

```
energy/
├── energy_general                (exists)    specificity=1   Universal fallback
│
├── UPSTREAM
│   ├── energy_upstream_deepwater (new)       specificity=4   Offshore/deepwater E&P
│   ├── energy_upstream_unconventional (new)  specificity=3   Tight oil, shale, fracking
│   └── energy_upstream_onshore   (new)       specificity=2   Conventional onshore E&P
│
├── MIDSTREAM
│   └── energy_midstream          (new)       specificity=2   Pipeline, processing, storage
│
├── DOWNSTREAM
│   └── energy_downstream         (new)       specificity=2   Refining & petrochemical
│
├── RENEWABLE / ENERGY TRANSITION
│   ├── energy_offshore_wind      (new)       specificity=4   Offshore wind farms
│   ├── energy_storage            (new)       specificity=3   Battery (BESS), green hydrogen
│   └── energy_onshore_renewable  (new)       specificity=2   Onshore wind & utility solar
│
└── CROSS-CUTTING
    └── energy_sme                (new)       specificity=2   Small operators, BUNDLED pricing
```

### Routing Logic

The multiplexer evaluates routing constraints in descending specificity order. The first configuration whose constraints are satisfied wins. `operation_segment` is an optional input field (see Appendix G.1) — when provided, it enables specific routing; when absent, submissions default to `energy_general`.

| Configuration | Specificity | Routing Constraints | Fallback |
|---|---|---|---|
| `energy_upstream_deepwater` | 4 | `operation_segment IN [UPSTREAM_OFFSHORE, UPSTREAM_DEEPWATER]` AND `tiv > 100000000` | `energy_general` |
| `energy_offshore_wind` | 4 | `operation_segment == RENEWABLE` AND `technology_type == OFFSHORE_WIND` | `energy_onshore_renewable` |
| `energy_upstream_unconventional` | 3 | `operation_segment == UPSTREAM_UNCONVENTIONAL` | `energy_upstream_onshore` |
| `energy_storage` | 3 | `operation_segment == RENEWABLE` AND `technology_type IN [BATTERY_STORAGE, HYDROGEN]` | `energy_onshore_renewable` |
| `energy_upstream_onshore` | 2 | `operation_segment == UPSTREAM_CONVENTIONAL` | `energy_general` |
| `energy_onshore_renewable` | 2 | `operation_segment == RENEWABLE` AND `technology_type IN [ONSHORE_WIND, UTILITY_SOLAR, DISTRIBUTED_SOLAR]` | `energy_general` |
| `energy_midstream` | 2 | `operation_segment IN [MIDSTREAM_PIPELINE, MIDSTREAM_PROCESSING, MIDSTREAM_STORAGE]` | `energy_general` |
| `energy_downstream` | 2 | `operation_segment IN [DOWNSTREAM_REFINING, DOWNSTREAM_PETROCHEMICAL]` | `energy_general` |
| `energy_sme` | 2 | `tiv <= 100000000` AND `employee_count <= 500` | `energy_general` |
| `energy_general` | 1 | `tiv > 25000000` | — |

---

## Configuration 1: `energy_upstream_deepwater`

### The Underwriting Reality

Deepwater is the frontier of energy insurance. A single well can cost $150M to drill. A blowout — as Macondo demonstrated in 2010 — can produce $65B+ in total economic loss. The insurance market for deepwater is concentrated among a handful of Lloyd's syndicates and specialist reinsurers who understand that the difference between a well-managed deepwater operator and a reckless one is not a matter of degree — it is binary.

The key insight: **in deepwater, process safety IS the risk**. Unlike onshore operations where frequency drives loss, deepwater is a severity-dominated class. A single catastrophic event can exhaust the entire programme limit. This means the signal architecture must be fundamentally different from `energy_general`.

### Signal Architecture Rationale

**Primary driver: Safety Performance (Risk: 0.35, Loss: 0.40, Exposure: 0.10 = 0.85 combined)**

This is the highest group weight anywhere in DSI, and deliberately so. In deepwater, the correlation between safety performance indicators (TRIR, process safety events, BSEE incidents) and loss outcome is near-deterministic. The Macondo investigation identified 11 specific process safety failures. Every one of them was observable in advance through the signals we extract.

**Secondary driver: Environmental Compliance (Risk: 0.20, Loss: 0.25, Exposure: 0.10 = 0.55 combined)**

Deepwater spills are the most expensive environmental events on Earth. The signals here are not about routine compliance — they are about catastrophic release potential. Methane detection, flaring intensity, and spill history carry elevated weights.

**Deprioritised: Corporate Footprint, Structured Data**

In deepwater, we don't care much about ESG reporting aesthetics. We care about whether the BOP was tested last week.

### New Signals (Not in `energy_general`)

| Signal | Proxy Tier | Group | Rationale |
|---|---|---|---|
| `bop_testing_compliance` | DIRECT_OBSERVABLE | safety_performance | BOP test records filed with BSEE. The single most predictive signal for blowout risk. |
| `rig_contractor_quality` | INFERRED_PROXY | network_authority | The quality of the drilling contractor (Transocean, Valaris, Noble) directly impacts operational safety. |
| `subsea_equipment_age` | INFERRED_PROXY | asset_portfolio | Subsea trees and manifolds degrade. Average equipment vintage predicts failure modes. |
| `water_depth_profile` | DIRECT_OBSERVABLE | asset_portfolio | Deeper water = higher pressure = higher severity. This is physics, not opinion. |
| `metocean_exposure` | DIRECT_OBSERVABLE | asset_portfolio | Hurricane/cyclone exposure for GoM, typhoon exposure for APAC. NatCat overlay. |

### Pricing Philosophy

- **Basis**: TIV (Total Insured Value) — unchanged from `energy_general`
- **Method**: MULTIPLIER on TIV
- **Key difference**: Tier 3 (STANDARD) rate of **0.28%** vs `energy_general`'s 0.18%. Deepwater commands a ~55% rate premium due to severity exposure.
- **ILF Curves**: Control of Well and Pollution Liability curves are 30-40% steeper than `energy_general`, reflecting the catastrophic tail.
- **Limit Configuration**: DECOUPLED, but with higher minimum limits ($25M floor vs $5M in general). No underwriter writes a $5M deepwater programme.

### Example Company Returns

**Tier 1 — PREFERRED (Auto-Approve):**
> **Hess Corporation** — Guyana deepwater programme (Stabroek Block)
> - TIV: $8.2B | Limit: $500M | Score: 842
> - Why: Exceptional safety record (zero LTIs across 3 FPSOs), ExxonMobil as JV operator (network authority score: 91), modern assets (<5 years average), strong BSEE compliance
> - Premium: $8.2B × 0.0008 × ILF(500M) = **$6.56M base** before modifiers
> - Modifiers: Operator type (SUPERMAJOR JV: 0.75), Geographic (LATIN_AMERICA: 1.2), Safety modifier (0.85) → **Net premium: ~$5.0M**

**Tier 3 — STANDARD (Refer):**
> **Murphy Oil Corporation** — Gulf of Mexico shelf & deepwater
> - TIV: $3.1B | Limit: $250M | Score: 578
> - Why: Mixed safety record (2 process safety events in 5 years), aging Medusa spar platform, adequate but not exceptional BSEE history
> - Referral reasons: `process_safety <= 40`, `asset_age <= 35`
> - Premium: $3.1B × 0.0018 × ILF(250M) = **$5.58M base** → Referred for senior review

**Tier 5 — DECLINE:**
> **Vaalco Energy** — Offshore Gabon (hypothetical deterioration scenario)
> - TIV: $420M | Limit: $100M | Score: 287
> - Why: Fatality on Etame platform, 3 spill events, EPA-equivalent violations in Gabonese jurisdiction, financial restructuring history, single-asset concentration (100% Etame)
> - Decline triggers: Safety performance group score <= 25, environmental group score <= 30

---

## Configuration 2: `energy_upstream_onshore`

### The Underwriting Reality

Conventional onshore E&P is the foundational segment of energy insurance — the Permian Basin producer running 200 vertical wells, the Oklahoma stripper well operator, the Louisiana conventional gas field. This is not frontier risk; it is mature, well-understood, and data-rich. State oil and gas commissions (Texas RRC, Oklahoma OCC, Louisiana SONRIS) publish well-level production, permitting, and violation data. OSHA TRIR is filed publicly. EPA compliance is on record.

The insurance market for onshore conventional E&P is competitive and commoditised. Lloyd's syndicates and domestic carriers have decades of loss data. The signal architecture must reflect this maturity: **predictability is the defining characteristic**. Losses are frequency-driven (pump jack incidents, tank battery fires, produced water releases) with moderate severity. Catastrophic loss is possible (well blowout, H2S release) but rare compared to deepwater or unconventional.

The key insight: **for onshore conventional, the operational track record IS the risk signal.** An operator with 20 years of production history, stable TRIR, and clean regulatory record is a fundamentally different risk than a startup operator with no history. The signal architecture must weight historical observables heavily.

### Signal Architecture Rationale

**Primary driver: Safety Performance (Risk: 0.25, Loss: 0.30, Exposure: 0.10 = 0.65 combined)**

Lower than deepwater because onshore conventional has lower severity exposure. No BOP failures, no subsea completions, no $65B Macondo scenarios. But safety still dominates the loss distribution — well servicing injuries, H2S exposure, and tank battery incidents drive frequency.

**Secondary driver: Operational Telemetry (Risk: 0.15, Loss: 0.15, Exposure: 0.25 = 0.55 combined)**

Production consistency, well integrity, and maintenance patterns are highly predictive for conventional operators. State regulatory filings provide rich production telemetry. Operators who maintain consistent production and well integrity programmes have measurably better outcomes.

**Elevated: Environmental Compliance (Risk: 0.20, Loss: 0.20, Exposure: 0.10 = 0.50 combined)**

Produced water management is the primary environmental exposure for onshore conventional. Spills, SWD (saltwater disposal) well compliance, and surface discharge violations are observable and predictive.

### New Signals (Not in `energy_general`)

| Signal | Proxy Tier | Group | Rationale |
|---|---|---|---|
| `produced_water_management` | INFERRED_PROXY | environmental_compliance | Produced water handling, SWD well compliance, recycling rate. The primary environmental risk for onshore conventional. |
| `h2s_exposure` | DIRECT_OBSERVABLE | safety_performance | H2S concentration at wellhead. H2S is the #1 cause of onshore E&P fatalities. |
| `artificial_lift_reliability` | INFERRED_PROXY | operational_telemetry | Rod pump, ESP, gas lift reliability metrics. Artificial lift failure drives workover frequency. |
| `state_regulatory_compliance` | DIRECT_OBSERVABLE | safety_performance | State oil and gas commission violation history (RRC, OCC, etc.). The onshore equivalent of BSEE. |
| `well_vintage_profile` | INFERRED_PROXY | asset_portfolio | Distribution of well ages across the portfolio. Mature conventional fields have aging well stock. |

### Pricing Philosophy

- **Basis**: TIV
- **Method**: MULTIPLIER on TIV
- **Key difference**: Tier 3 rate of **0.0016** (0.16%). Lower than general because conventional onshore is well-understood and frequency-dominated. Slightly below general's 0.18% because the data richness from state filings reduces uncertainty.
- **Product types**: `property_damage`, `business_interruption`, `control_of_well`, `operators_extra_expense`, `third_party_liability`, `pollution_liability` (no `removal_of_wreck` — onshore assets)
- **Limit Configuration**: DECOUPLED

### Example Company Returns

**Tier 1 — PREFERRED (Auto-Approve):**
> **Devon Energy** — Permian Basin & Eagle Ford conventional operations
> - TIV: $12B | Limit: $500M | Score: 835
> - Why: Industry-leading safety record (TRIR 0.31), 20+ year operating history, clean state regulatory record, modern well inventory, investment-grade credit, diversified across multiple basins
> - Premium: **~$5.8M** after modifiers

**Tier 3 — STANDARD (Refer):**
> **Callon Petroleum** — Permian Basin conventional & unconventional mix
> - TIV: $4.2B | Limit: $250M | Score: 562
> - Why: Moderate safety record, recent acquisition integration (Callon-Carrizo merger), some aging well inventory, adequate but not leading state compliance
> - Referral reasons: `asset_age <= 40`, `leverage <= 35`

**Tier 5 — DECLINE:**
> **Distressed Conventional Operator** (composite profile)
> - TIV: $380M | Limit: $50M | Score: 245
> - Why: Multiple state regulatory violations (RRC), orphaned well obligations, production declining >15% annually, financial distress, H2S incident history
> - Decline triggers: Safety performance group score <= 25, state regulatory compliance <= 20

---

## Configuration 3: `energy_upstream_unconventional`

### The Underwriting Reality

Unconventional E&P — tight oil, shale gas, hydraulic fracturing — is the segment that transformed global energy markets but brought entirely new risk dimensions that `energy_general` cannot capture. The Permian Basin shale producer operating 50 horizontal wells with multi-stage frac completions is not the same risk as a conventional Permian operator running rod pumps on vertical wells.

The distinguishing characteristics of unconventional risk:

- **Hydraulic fracturing IS the operation.** High-pressure pumping (10,000-15,000 PSI), massive water volumes (10-15M gallons per well), proppant logistics, and wellhead zipper frac operations create risks that don't exist in conventional production.
- **Induced seismicity is a real and growing exposure.** Oklahoma experienced a 900x increase in M3+ earthquakes from 2009-2015, directly linked to saltwater disposal from unconventional operations. This is a new liability dimension with evolving regulatory response.
- **Well spacing and parent-child interference** create asset portfolio risks unique to unconventional. Infill drilling can damage existing production ("frac hits"), creating both property damage and production loss.
- **Operational intensity is extreme.** A single pad site may have 8-12 horizontal wells being drilled, completed, and produced simultaneously. Crew count, equipment density, and operational tempo far exceed conventional.
- **Water management at industrial scale.** Unlike conventional (which manages thousands of barrels), unconventional manages millions of barrels of produced and flowback water per well.

### Signal Architecture Rationale

**Primary driver: Safety Performance (Risk: 0.30, Loss: 0.35, Exposure: 0.10 = 0.75 combined)**

Same weight as deepwater — deliberate. Unconventional operations have comparable human safety exposure to deepwater due to the intensity and pressure of frac operations. The Piper Alpha-equivalent risk is a wellhead blowout during frac, and the frequency of near-misses is higher than any other onshore segment.

**Secondary driver: Environmental Compliance (Risk: 0.20, Loss: 0.20, Exposure: 0.15 = 0.55 combined)**

Elevated exposure weight reflects the industrial-scale water management and induced seismicity dimensions. These are not routine EPA violations — they are systemic risks that can shut down entire operating areas (as happened in parts of Oklahoma).

**Elevated: Operational Telemetry (Risk: 0.15, Loss: 0.15, Exposure: 0.20 = 0.50 combined)**

Frac fleet performance, completion efficiency, and production ramp curves are rich data sources unique to unconventional. Operators who complete wells efficiently and manage production decline curves effectively have better loss profiles.

### New Signals (Not in `energy_general`)

| Signal | Proxy Tier | Group | Rationale |
|---|---|---|---|
| `frac_fleet_quality` | INFERRED_PROXY | operational_telemetry | Quality and age of pressure pumping equipment. Fleet quality directly correlates with wellhead incident rates. |
| `water_recycling_rate` | DIRECT_OBSERVABLE | environmental_compliance | Percentage of produced/flowback water recycled vs disposed. Higher recycling = lower SWD volume = lower induced seismicity exposure. |
| `induced_seismicity_score` | DIRECT_OBSERVABLE | environmental_compliance | Proximity to and history of induced seismic events. Based on USGS seismicity data and state regulatory seismicity zones. |
| `well_spacing_optimisation` | INFERRED_PROXY | asset_portfolio | Whether well spacing reflects modern understanding of parent-child interference. Poor spacing = frac hit risk. |
| `completion_efficiency` | INFERRED_PROXY | operational_telemetry | Lateral length, stage count, proppant intensity metrics vs basin benchmarks. Efficient completions correlate with operational discipline. |
| `pad_drilling_intensity` | INFERRED_PROXY | operational_telemetry | Number of simultaneous operations per pad. Higher density = higher concentration risk but also operational maturity signal. |

### Pricing Philosophy

- **Basis**: TIV
- **Method**: MULTIPLIER on TIV
- **Key difference**: Tier 3 rate of **0.0022** (0.22%). Higher than conventional onshore (0.16%) and general (0.18%) due to higher operational intensity, frac-specific risks, and induced seismicity exposure. Comparable to downstream (0.22%) reflecting similar severity potential.
- **Product types**: `property_damage`, `business_interruption`, `control_of_well`, `operators_extra_expense`, `third_party_liability`, `pollution_liability` (no `removal_of_wreck`)
- **Limit Configuration**: DECOUPLED

### Example Company Returns

**Tier 1 — PREFERRED (Auto-Approve):**
> **Pioneer Natural Resources** (pre-ExxonMobil acquisition profile) — Permian Basin pure-play
> - TIV: $28B | Limit: $750M | Score: 862
> - Why: Best-in-class safety record (TRIR 0.18), industry-leading completion efficiency, 100% water recycling in Midland Basin, zero induced seismicity events, modern well inventory, investment-grade credit
> - Premium: **~$18.5M** after modifiers (operator type: LARGE_INDEPENDENT 0.95, geographic: US_ONSHORE 1.0)

**Tier 3 — STANDARD (Refer):**
> **Chesapeake Energy** (post-restructuring profile) — Marcellus/Haynesville shale gas
> - TIV: $8.5B | Limit: $250M | Score: 545
> - Why: Prior bankruptcy (restructured 2021), moderate safety record, some legacy well spacing issues in older Marcellus positions, adequate water management, operational improvement trajectory post-restructuring
> - Referral reasons: `restructuring <= 40`, `well_spacing_optimisation <= 45`

**Tier 5 — DECLINE:**
> **Distressed Shale Operator** (composite profile)
> - TIV: $1.2B | Limit: $100M | Score: 218
> - Why: Multiple frac-related safety incidents (2 hospitalizations in 12 months), induced seismicity violations in Oklahoma (forced SWD shut-ins), high leverage (debt/EBITDA > 6x), declining production, orphaned well obligations, EPA consent decree pending
> - Decline triggers: Safety performance group score <= 20, induced seismicity <= 15

---

## Configuration 4: `energy_midstream`

### The Underwriting Reality

Midstream is the "boring" part of energy — and that's exactly why it's profitable to insure. Pipelines, processing plants, and storage terminals have fundamentally different risk characteristics from upstream or downstream:

- **Frequency is the driver, not severity.** Pipeline incidents are frequent (corrosion, third-party strikes, equipment failure) but individually modest. A $2M pipeline rupture happens far more often than a $200M refinery explosion.
- **Linear asset exposure.** A pipeline crossing 1,200 miles of terrain has a fundamentally different concentration profile than a point-source refinery. Risk is distributed, not concentrated.
- **Regulatory regime is different.** PHMSA (Pipeline and Hazardous Materials Safety Administration), not OSHA/BSEE, is the primary regulator. Different data sources, different compliance signals.

This means the signal architecture must rebalance toward **loss frequency** and introduce **midstream-specific regulatory signals**.

### Signal Architecture Rationale

**Primary driver: Operational Telemetry (Risk: 0.20, Loss: 0.25, Exposure: 0.25 = 0.70 combined)**

For midstream, operational signals — inline inspection results, cathodic protection status, SCADA monitoring — are the best predictors of loss. A pipeline operator running a mature integrity management programme has a quantifiably different loss profile.

**Secondary driver: Environmental Compliance (Risk: 0.20, Loss: 0.20, Exposure: 0.10 = 0.50 combined)**

Pipeline spills and emissions are the primary environmental exposure. But the signal sources differ: PHMSA incident reports replace BSEE, and methane leak detection/repair (LDAR) programmes are the key observable.

**Deprioritised: Safety Performance (reduced from 0.75 combined in deepwater to 0.40)**

Midstream operations have lower human safety exposure than upstream drilling. Fatality risk is real but less dominant in the loss distribution.

### New Signals (Not in `energy_general`)

| Signal | Proxy Tier | Group | Rationale |
|---|---|---|---|
| `phmsa_compliance` | DIRECT_OBSERVABLE | safety_performance | PHMSA enforcement actions and compliance orders. The midstream equivalent of OSHA TRIR. |
| `inline_inspection` | INFERRED_PROXY | operational_telemetry | Smart pig inspection frequency and results. The best predictor of pipeline integrity. |
| `cathodic_protection` | INFERRED_PROXY | operational_telemetry | Cathodic protection system status. Corrosion is the #1 cause of pipeline failure. |
| `right_of_way` | INFERRED_PROXY | asset_portfolio | Right-of-way encroachment and third-party damage history. The #2 cause of pipeline failure. |
| `scada_maturity` | INFERRED_PROXY | operational_telemetry | SCADA/control system sophistication. Real-time monitoring reduces response time and severity. |

### Pricing Philosophy

- **Basis**: TIV
- **Method**: MULTIPLIER on TIV
- **Key difference**: Tier 3 rate of **0.0012** (0.12%). Midstream is cheaper to insure than general energy because of lower severity and better predictability.
- **ILF Curves**: Flatter than upstream (severity tail is thinner). Control of Well not applicable — replaced with `third_party_liability` and `pollution_liability` as the primary excess layers.
- **Product types**: `property_damage`, `business_interruption`, `third_party_liability`, `pollution_liability` (no `control_of_well`, no `removal_of_wreck`)

### Example Company Returns

**Tier 1 — PREFERRED:**
> **Enterprise Products Partners** — Largest US midstream operator
> - TIV: $22B | Limit: $500M | Score: 867
> - Why: Industry-leading integrity management programme, modern SCADA infrastructure, excellent PHMSA record, investment-grade credit (BBB+), diversified 50,000-mile pipeline network
> - Premium: $22B × 0.0006 × ILF(500M) = **$13.2M base** → modifiers push to **~$10.5M**

**Tier 2 — STANDARD PLUS:**
> **ONEOK, Inc.** — Natural gas gathering & processing
> - TIV: $14B | Limit: $250M | Score: 724
> - Why: Good safety record, some concentration in Permian/STACK basins, recent expansion (construction risk transitioning to operating risk), solid financials
> - Premium: **~$12.6M** after modifiers

**Tier 4 — SUBSTANDARD:**
> **Genesis Energy** — Offshore pipeline & terminal operator
> - TIV: $2.8B | Limit: $100M | Score: 412
> - Why: High leverage (debt/EBITDA > 5x), aging deepwater pipeline assets, limited inline inspection cadence, environmental violations in Gulf operations
> - Referral reasons: `leverage <= 30`, `asset_age <= 35`, `epa_violation <= 45`

---

## Configuration 5: `energy_downstream`

### The Underwriting Reality

Downstream (refining and petrochemical) is the concentration risk capital of energy insurance. A single refinery complex can have a TIV of $10-15B with a single-point-of-failure that could trigger a $2-5B business interruption loss. The 2005 BP Texas City explosion ($1.5B insured loss), the 2019 Philadelphia Energy Solutions refinery explosion, and the recurring incidents at Indian and Chinese petrochemical complexes all demonstrate the same pattern: **process safety management failure at high-value concentrated assets**.

The underwriting challenge is that downstream operators look financially healthy and operationally stable — right up until they don't. The signals that predict catastrophic downstream loss are subtle: deferred turnaround maintenance, process safety near-miss trends, corrosion-under-insulation rates, and the quality of the mechanical integrity programme.

### Signal Architecture Rationale

**Primary driver: Safety Performance (Risk: 0.30, Loss: 0.35, Exposure: 0.10 = 0.75 combined)**

Same weight as deepwater, for the same reason: severity dominance. But the *signals within the group* differ. Downstream safety is about process safety management (PSM), not drilling operations.

**Secondary driver: Asset Portfolio (Risk: 0.15, Loss: 0.15, Exposure: 0.35 = 0.65 combined)**

Asset portfolio carries unusually high exposure weight because downstream risk IS concentration risk. A refinery with a single crude unit has a catastrophically different exposure profile than one with redundant processing trains. Asset age, turnaround cycle compliance, and equipment vintage are critical.

**Elevated: Operational Telemetry (Risk: 0.15, Loss: 0.15, Exposure: 0.20 = 0.50 combined)**

Downstream operations generate enormous volumes of process data. Operators who instrument effectively (continuous emissions monitoring, real-time corrosion monitoring, vibration analysis) have measurably better outcomes.

### New Signals (Not in `energy_general`)

| Signal | Proxy Tier | Group | Rationale |
|---|---|---|---|
| `turnaround_compliance` | INFERRED_PROXY | asset_portfolio | Whether scheduled turnaround/shutdown maintenance is being deferred. Deferral is the #1 predictor of catastrophic downstream loss. |
| `psm_audit_findings` | DIRECT_OBSERVABLE | safety_performance | OSHA PSM audit findings. Direct regulatory observable of process safety management quality. |
| `mechanical_integrity` | INFERRED_PROXY | operational_telemetry | Mechanical integrity programme maturity. CUI (corrosion under insulation), piping thickness monitoring, relief valve testing. |
| `feedstock_complexity` | INFERRED_PROXY | asset_portfolio | Refinery complexity index (Nelson Index). Higher complexity = more unit operations = more failure modes. |
| `business_interruption_exposure` | INFERRED_PROXY | financial_stability | Ratio of BI values to PD values. Downstream has uniquely high BI/PD ratios (often 2:1 or higher). |

### Pricing Philosophy

- **Basis**: TIV
- **Method**: MULTIPLIER on TIV
- **Key difference**: Tier 3 rate of **0.0022** (0.22%). Higher than general due to concentration severity, but lower than deepwater because downstream assets are onshore and more accessible.
- **Product types**: `property_damage`, `business_interruption`, `third_party_liability`, `pollution_liability` (no `control_of_well`, no `removal_of_wreck`)
- **Business interruption**: Carries a separate, steeper ILF curve reflecting the outsized BI exposure in downstream.

### Example Company Returns

**Tier 1 — PREFERRED:**
> **Valero Energy** — Largest independent US refiner
> - TIV: $38B (14 refineries) | Limit: $1B | Score: 831
> - Why: Excellent turnaround compliance (zero deferrals), best-in-class process safety (TRIR 0.21), diversified refinery portfolio (no single site >15% of capacity), strong financials (investment grade), modern instrumentation
> - Premium: $38B × 0.0008 × ILF(1B) = **$30.4M base** → diversification modifier (0.85) → **~$25.8M**

**Tier 3 — STANDARD:**
> **PBF Energy** — US East Coast & Gulf Coast refineries
> - TIV: $11B (6 refineries) | Limit: $500M | Score: 561
> - Why: Moderate safety record, some deferred turnaround at Paulsboro, high leverage, concentrated in older refinery assets, adequate but not leading PSM programme
> - Referral reasons: `turnaround_compliance <= 40`, `leverage <= 35`

**Tier 5 — DECLINE:**
> **Philadelphia Energy Solutions** (pre-explosion profile)
> - TIV: $5.2B (single site) | Limit: $250M | Score: 198
> - Why: Bankrupt and restructured, single-asset concentration (100%), known HF alkylation unit risk, multiple OSHA citations, deferred maintenance, financial distress
> - This is exactly the submission DSI should decline. The 2019 explosion proved the risk was uninsurable.

---

## Configuration 6: `energy_offshore_wind`

### The Underwriting Reality

Offshore wind is the most capital-intensive segment in renewable energy and arguably the most complex construction risk in all of energy insurance. A single offshore wind farm can have a TIV of $3-15B, require 100+ foundation installations in open water, deploy turbines at 15MW+ nameplate capacity on structures taller than the Statue of Liberty, and depend on a global fleet of fewer than 20 installation vessels.

This is NOT the same risk as an onshore wind farm. The differences are fundamental:

- **Maritime construction risk dominates.** Installation vessel jack-up failures, cable-laying incidents, transition piece grouting defects — these are marine operations risks, not power generation risks. The Beatrice, Hornsea, and Vineyard Wind projects all experienced construction-phase incidents that would never occur onshore.
- **Concentration is extreme.** A single offshore wind farm represents $3-15B of TIV in a geographically constrained area. A single catastrophic storm event can damage dozens of turbines simultaneously.
- **Technology is evolving rapidly.** Turbine nameplate capacity has doubled in 5 years (8MW → 15MW+). Floating wind (Hywind, WindFloat) is first-of-kind technology with no commercial loss history. Each generation step introduces new failure modes.
- **Regulatory complexity.** BOEM (US), The Crown Estate (UK), BSH (Germany) — each jurisdiction has different permitting, environmental, and decommissioning requirements.
- **Safety exposure is real.** Offshore wind has measurable fall-from-height, vessel collision, and crew transfer incident rates. The offshore environment is inherently hazardous.

This configuration requires the highest specificity (4) because the signal architecture, pricing, and underwriting logic differ materially from all other renewable configurations.

### Signal Architecture Rationale

**Primary driver: Construction Quality (Risk: 0.20, Loss: 0.25, Exposure: 0.15 = 0.60 combined)**

Construction quality is the dominant group because most offshore wind losses occur during construction and early operation. EPC contractor quality, installation vessel capability, and commissioning defect rates are the primary predictors.

**Secondary driver: Asset Portfolio (Risk: 0.20, Loss: 0.15, Exposure: 0.35 = 0.70 combined)**

Turbine platform selection, foundation type, and NatCat exposure define the physical risk. Floating wind vs fixed-bottom is a binary technology maturity question.

**Elevated: Safety Performance (Risk: 0.15, Loss: 0.15, Exposure: 0.10 = 0.40 combined)**

Higher than onshore renewable because offshore operations have genuine human safety exposure — crew transfer vessels, helicopter operations, working at height in marine conditions.

### New Signals (Not in `energy_general`)

| Signal | Proxy Tier | Group | Rationale |
|---|---|---|---|
| `installation_vessel_quality` | INFERRED_PROXY | construction_quality | Quality and track record of the WTI vessel (jack-up or heavy-lift). Vessel availability and capability is the #1 construction risk. |
| `foundation_type` | DIRECT_OBSERVABLE | asset_portfolio | Monopile, jacket, gravity-base, or floating. Each has different installation risk and proven track record. Categorical signal. |
| `turbine_platform_generation` | INFERRED_PROXY | asset_portfolio | Turbine platform maturity. A proven 8MW platform vs first-of-kind 15MW platform. |
| `cable_route_risk` | INFERRED_PROXY | asset_portfolio | Export cable route complexity — crossing existing infrastructure, seabed conditions, cable burial achievability. |
| `marine_weather_exposure` | DIRECT_OBSERVABLE | asset_portfolio | Weather window analysis for the installation site. North Sea vs Gulf of Mexico vs Baltic — fundamentally different weather risk. |
| `crew_transfer_safety` | INFERRED_PROXY | safety_performance | Crew transfer vessel (CTV) and service operation vessel (SOV) safety record. Marine crew transfer is a measurable safety exposure. |
| `offtake_contract_quality` | INFERRED_PROXY | financial_stability | CFD/PPA/OREC contract quality and counterparty. Government-backed CFDs (UK) vs merchant exposure. |

### Pricing Philosophy

- **Basis**: TIV (total project value)
- **Method**: MULTIPLIER on TIV
- **Key difference**: Tier 3 rate of **0.0020** (0.20%). Higher than onshore renewable (0.0013%) due to maritime construction risk, concentration, and technology evolution. Construction-phase submissions receive a 1.4x loading (higher than onshore 1.3x due to marine installation risk).
- **Product types**: `property_damage`, `business_interruption`, `third_party_liability`, `delay_in_start_up`, `removal_of_wreck` (offshore structures require wreck removal)
- **Limit Configuration**: DECOUPLED, minimum limit $25M

### Example Company Returns

**Tier 1 — PREFERRED:**
> **Orsted A/S** — World's largest offshore wind developer
> - TIV: $28B (global offshore wind portfolio) | Limit: $750M | Score: 889
> - Why: Proven technology (Siemens Gamesa 8MW+), 25+ years offshore wind experience, zero construction-phase total losses, investment-grade credit, best-in-class SCADA/predictive maintenance, long-term PPAs/CFDs with sovereign counterparties
> - Premium: **~$16.8M** after modifiers (developer track record: 0.70)

**Tier 3 — STANDARD (Refer):**
> **Equinor Renewables** — Dogger Bank & Empire Wind
> - TIV: $12B | Limit: $500M | Score: 584
> - Why: Oil & gas heritage transitioning to offshore wind, Dogger Bank is world's largest project (3.6GW), using 13MW Haliade-X turbines (relatively new platform), strong financials but limited offshore wind operational track record
> - Referral reasons: `turbine_platform_generation <= 45` (new platform), `concentration <= 35` (single mega-project)

**Tier 4 — SUBSTANDARD:**
> **First-Time Offshore Wind Developer** (composite profile)
> - TIV: $3.2B (single project) | Limit: $250M | Score: 389
> - Why: No track record, unproven EPC contractor, floating wind technology (immature), construction phase, single-asset concentration (100%), PPA not finalised
> - Referral reasons: `technology_maturity <= 30`, `epc_contractor_quality <= 35`, `concentration <= 20`

---

## Configuration 7: `energy_onshore_renewable`

### The Underwriting Reality

Onshore wind and utility-scale solar are the most mature segments in renewable energy. The technology is proven (onshore wind turbines have 30+ years of operational history; crystalline silicon solar panels have 25+ years), the loss data is abundant, and the insurance market is competitive. This is the "conventional E&P" of the renewable world — well-understood, data-rich, and commoditised.

But maturity does not mean simplicity:

- **NatCat is the dominant exposure.** Hail damage to solar panels (Texas, Colorado), tornado damage to wind turbines (Oklahoma, Kansas), wildfire exposure to transmission interconnections (California) — these are insurable but volatile perils that require geographic-specific assessment.
- **Equipment defects create fleet-wide exposure.** A serial defect in a specific inverter model or blade design can affect hundreds of installations simultaneously. The 2021 GE blade cracking advisory affected turbines across multiple projects.
- **Grid curtailment is a real financial risk.** ERCOT curtailment in Texas, CAISO duck curve in California — grid integration challenges create business interruption exposure that is not captured by traditional energy models.
- **Scale creates operational complexity.** A 500MW solar farm covers 3,000 acres. A 300MW onshore wind farm spans 50,000 acres. Asset management at this scale requires sophisticated SCADA and predictive maintenance — operators who don't invest in these have higher failure rates.

### Signal Architecture Rationale

**Primary driver: Asset Portfolio (Risk: 0.25, Loss: 0.20, Exposure: 0.35 = 0.80 combined)**

Technology selection, NatCat exposure, and portfolio diversification are the primary risk drivers. An operator with 50 wind farms across 10 states is a fundamentally different risk than a single-project developer.

**Secondary driver: Operational Telemetry (Risk: 0.20, Loss: 0.20, Exposure: 0.25 = 0.65 combined)**

SCADA data is mature and predictive. Capacity factor, availability, degradation curves, and curtailment rates are all observable and directly correlated with loss outcomes.

**Deprioritised: Safety Performance (Risk: 0.10, Loss: 0.10, Exposure: 0.05 = 0.25 combined)**

Onshore renewable has the lowest human safety exposure of any energy segment. No hydrocarbons, no high-pressure operations, limited working-at-height (ground-mounted solar has near-zero safety risk).

### New Signals (Not in `energy_general`)

| Signal | Proxy Tier | Group | Rationale |
|---|---|---|---|
| `hail_exposure` | DIRECT_OBSERVABLE | asset_portfolio | Hail map overlay for solar installations. Texas Panhandle vs Arizona — order of magnitude difference in hail frequency. |
| `panel_technology_vintage` | INFERRED_PROXY | asset_portfolio | Solar panel or turbine model vintage and known defect history. Older bifacial panels have different degradation profiles. |
| `inverter_reliability` | INFERRED_PROXY | operational_telemetry | Inverter manufacturer and model reliability data. Inverter failure is the #1 cause of solar plant underperformance. |
| `curtailment_rate` | DIRECT_OBSERVABLE | operational_telemetry | Historical grid curtailment rate. Directly impacts BI exposure. ERCOT curtailment data is publicly observable. |
| `portfolio_geographic_spread` | INFERRED_PROXY | asset_portfolio | Geographic diversification across NatCat zones. A portfolio spanning Texas, Iowa, and California has lower correlated NatCat risk. |

### Pricing Philosophy

- **Basis**: TIV
- **Method**: MULTIPLIER on TIV
- **Key difference**: Tier 3 rate of **0.0013** (0.13%). The lowest in the energy suite — reflecting mature technology, thin severity tail, and abundant market competition. Lower than midstream (0.12%) in absolute terms but comparable risk-adjusted.
- **Product types**: `property_damage`, `business_interruption`, `third_party_liability`, `delay_in_start_up`
- **Limit Configuration**: DECOUPLED

### Example Company Returns

**Tier 1 — PREFERRED:**
> **NextEra Energy Resources** — Largest US onshore wind & solar operator
> - TIV: $45B (combined onshore wind + utility solar) | Limit: $500M | Score: 812
> - Why: Massive, diversified portfolio (200+ projects across 30+ states), proven operational track record, best-in-class SCADA infrastructure, strong financials (NextEra parent is investment grade), geographic diversification reduces correlated NatCat
> - Premium: **~$18.5M** with diversification modifier (0.80)

**Tier 3 — STANDARD (Refer):**
> **Regional Solar Developer** (composite profile)
> - TIV: $2.5B (15 utility solar projects, Texas-concentrated) | Limit: $100M | Score: 571
> - Why: Moderate operational history (5 years), concentrated in Texas hail zone, some inverter reliability issues, adequate but not leading SCADA, PPA portfolio with mixed counterparty quality
> - Referral reasons: `hail_exposure <= 35`, `concentration <= 40`

**Tier 5 — DECLINE:**
> **Distressed Solar Developer** (composite profile)
> - TIV: $800M (3 projects) | Limit: $50M | Score: 265
> - Why: Serial hail damage claims (3 in 2 years), panel degradation 3x manufacturer curve, PPA counterparty defaulted, financial distress, single-state concentration (Texas Panhandle)
> - Decline triggers: Asset portfolio group score <= 20, financial stability <= 25

---

## Configuration 8: `energy_storage`

### The Underwriting Reality

Battery energy storage systems (BESS) and green hydrogen represent the frontier of energy insurance — technology classes where the insurance market has minimal loss data, the regulatory framework is evolving, and the risk profile changes with each technology generation. This is not mature renewable risk; this is emerging technology risk priced under uncertainty.

The distinguishing characteristics:

- **Thermal runaway is the catastrophic peril for BESS.** The 2021 Vistra Moss Landing fire ($200M+ loss) and the 2019 APS McMicken explosion demonstrated that lithium-ion battery failures can produce catastrophic, self-sustaining thermal events. Battery chemistry matters enormously: LFP (lithium iron phosphate) has a fundamentally different thermal runaway profile than NMC (nickel manganese cobalt).
- **Green hydrogen introduces entirely new hazards.** Hydrogen embrittlement, high-pressure storage (350-700 bar), explosion risk (wide flammability range), and the lack of established safety standards create genuine first-of-kind uncertainty.
- **Technology generations turn over rapidly.** BESS chemistry, cell format (pouch vs prismatic vs cylindrical), and BMS (battery management system) architecture evolve annually. Each generation introduces new failure modes.
- **Fire suppression and thermal management are critical design signals.** A BESS with containerised aerosol suppression, air-gapped modules, and continuous thermal monitoring is a measurably different risk from one with basic smoke detection and water sprinkler.
- **Regulatory standards are immature.** NFPA 855, UL 9540A, and IEC 62619 are evolving. Projects built to 2020 standards may not meet 2025 requirements.

### Signal Architecture Rationale

**Primary driver: Asset Portfolio (Risk: 0.30, Loss: 0.25, Exposure: 0.35 = 0.90 combined)**

The technology and its installation define the risk. Battery chemistry, thermal management system design, fire suppression capability, and module architecture are the primary underwriting considerations. This is the highest asset portfolio weight in the entire DSI platform.

**Secondary driver: Construction Quality (Risk: 0.15, Loss: 0.20, Exposure: 0.10 = 0.45 combined)**

EPC contractor experience with BESS/hydrogen is scarce. A contractor who has built 50 solar farms has zero transferable experience with BESS thermal management. Construction quality signals must assess BESS/hydrogen-specific track record.

**Elevated: Safety Performance (Risk: 0.15, Loss: 0.15, Exposure: 0.10 = 0.40 combined)**

Higher than onshore renewable because thermal runaway and hydrogen explosion have genuine severity. The Moss Landing fire produced a $200M+ loss — this is severity-class risk.

**Deprioritised: Operational Telemetry (Risk: 0.10, Loss: 0.10, Exposure: 0.15 = 0.35 combined)**

Operational telemetry for BESS is rich (BMS data, cell voltage monitoring, thermal sensors) but the loss history is too thin to calibrate signal-to-loss correlations. Weight will increase as the market matures.

### New Signals (Not in `energy_general`)

| Signal | Proxy Tier | Group | Rationale |
|---|---|---|---|
| `battery_chemistry` | DIRECT_OBSERVABLE | asset_portfolio | LFP vs NMC vs NCA vs solid-state. Chemistry defines the thermal runaway profile. Categorical signal. |
| `thermal_management_system` | INFERRED_PROXY | asset_portfolio | Active vs passive cooling, air-gapped module design, thermal monitoring granularity. The #1 design signal for BESS fire risk. |
| `fire_suppression_capability` | DIRECT_OBSERVABLE | asset_portfolio | Suppression system type (aerosol, water mist, inert gas, none). Direct observable of catastrophic loss mitigation. |
| `bms_sophistication` | INFERRED_PROXY | operational_telemetry | Battery Management System capability — cell-level monitoring, predictive degradation, automatic isolation. |
| `hydrogen_storage_pressure` | DIRECT_OBSERVABLE | asset_portfolio | Storage pressure class (350 bar vs 700 bar). Higher pressure = higher severity in failure. Hydrogen-specific. |
| `safety_standard_compliance` | DIRECT_OBSERVABLE | safety_performance | Compliance with NFPA 855, UL 9540A, IEC 62619. Observable regulatory compliance for evolving standards. |
| `cell_format_maturity` | INFERRED_PROXY | asset_portfolio | Cell format (pouch, prismatic, cylindrical) and manufacturer track record. Some formats have better thermal properties. |
| `electrolyser_technology` | INFERRED_PROXY | asset_portfolio | PEM vs alkaline vs SOEC electrolyser type. Technology readiness varies significantly. Hydrogen-specific. |

### Pricing Philosophy

- **Basis**: TIV
- **Method**: MULTIPLIER on TIV
- **Key difference**: Tier 3 rate of **0.0028** (0.28%). The highest renewable rate — matching deepwater — reflecting genuine catastrophic severity (thermal runaway), immature loss data, and rapidly evolving technology. As loss history accumulates and technology matures, this rate will decline.
- **Product types**: `property_damage`, `business_interruption`, `third_party_liability`, `delay_in_start_up`
- **Limit Configuration**: DECOUPLED, minimum limit $10M

### Example Company Returns

**Tier 1 — PREFERRED:**
> **Fluence Energy** — Leading BESS integrator (Siemens/AES joint venture heritage)
> - TIV: $5B (global BESS portfolio) | Limit: $250M | Score: 821
> - Why: 200+ BESS projects delivered, LFP chemistry (lower thermal runaway risk), proprietary BMS with cell-level monitoring, NFPA 855 compliant across all installations, aerosol fire suppression standard, investment-grade parent backing
> - Premium: **~$4.2M** after modifiers (technology leader: 0.75, LFP chemistry modifier: 0.85)

**Tier 3 — STANDARD (Refer):**
> **Mid-Market BESS Developer** (composite profile)
> - TIV: $1.5B (10 BESS projects) | Limit: $100M | Score: 548
> - Why: NMC chemistry (higher thermal runaway risk than LFP), adequate but not leading BMS, water-mist suppression (less effective than aerosol for Li-ion), some projects pre-date current NFPA 855 standards, 3 years operational track record
> - Referral reasons: `battery_chemistry modifier 1.3` (NMC), `fire_suppression_capability <= 40`

**Tier 5 — DECLINE:**
> **Green Hydrogen Startup** (composite profile)
> - TIV: $500M (single green hydrogen pilot) | Limit: $50M | Score: 198
> - Why: First-of-kind SOEC electrolyser (unproven at scale), 700 bar storage (high severity), no operational track record, single-asset concentration, incomplete safety standard compliance, unproven EPC contractor
> - Decline triggers: Asset portfolio group score <= 15, technology_maturity <= 10

---

## Configuration 9: `energy_sme`

### The Underwriting Reality

Small and mid-size energy operators — the 200-employee Permian Basin producer, the family-owned gas gathering system, the single-site biodiesel plant — represent 80% of submission volume in energy insurance but only 15% of premium. They cannot justify the underwriting expense of a full technical review.

This is exactly the problem DSI was built to solve. The `energy_sme` configuration enables **automated underwriting** for small energy risks by:

1. **Reducing signal count** — from 47 signals in `energy_general` to ~25 focused, high-confidence signals
2. **Using BUNDLED pricing** — fixed limit/deductible packages instead of bespoke tower structures
3. **Raising auto-approve thresholds** — more submissions pass without human review
4. **Simplifying product types** — combined property/liability instead of 7 separate sub-covers

### Signal Architecture Rationale

The SME signal architecture aggressively prioritises **DIRECT_OBSERVABLE** signals (target: 60%+) because small operators have thinner digital footprints. We cannot reliably infer partner quality or contractor quality for a 50-person company. But we CAN observe:

- OSHA TRIR (filed publicly)
- EPA violations (public record)
- Credit rating / financial filings
- State regulatory compliance (well permits, pipeline registrations)
- Production data (state regulatory filings are public in most US jurisdictions)

**Deprioritised or removed:**
- Network authority group removed entirely (small operators don't have meaningful network graphs)
- Corporate footprint reduced (no ESG reporting, no industry conference presence)
- Structured data reduced (no third-party ESG ratings for small companies)

### Pricing Philosophy

- **Basis**: TIV
- **Method**: MULTIPLIER on TIV (same mathematical foundation)
- **Key difference**: Tier 3 rate of **0.0020** (0.20%). Slightly higher than `energy_general` because smaller operators have higher frequency and less diversification.
- **Limit Configuration**: **BUNDLED** — five fixed packages:

| Package | Limit | Deductible | Target Segment |
|---|---|---|---|
| STARTER | $5,000,000 | $25,000 | Micro operators (<$50M TIV) |
| STANDARD | $10,000,000 | $50,000 | Small operators ($50-100M TIV) |
| ENHANCED | $25,000,000 | $100,000 | Mid-size operators ($100-250M TIV) |
| PREMIUM | $50,000,000 | $250,000 | Larger SME ($250-500M TIV) |
| ENTERPRISE | $100,000,000 | $500,000 | Upper SME boundary |

- **Min Premium**: $25,000 (vs $100,000 for `energy_general`)
- **Product types**: `combined_property_liability`, `pollution_liability` (simplified from 7 sub-covers)

### Example Company Returns

**Tier 1 — PREFERRED (Auto-Approve):**
> **Diamondback Energy** (early-stage, pre-scale profile)
> - TIV: $85M | Limit: $25M (ENHANCED package) | Score: 812
> - Why: Clean OSHA record, no EPA violations, strong production consistency in Permian, good credit, modern well inventory
> - Premium: $85M × 0.0008 = **$68,000** — fully automated, no human touch

**Tier 3 — STANDARD (Auto-Approve with flag):**
> **Small Appalachian Gas Producer** (composite profile)
> - TIV: $62M | Limit: $10M (STANDARD package) | Score: 589
> - Why: Adequate safety record, some aging well inventory, minor state regulatory citations, moderate leverage
> - Premium: $62M × 0.0020 = **$124,000** — auto-approved with monitoring flags

**Tier 5 — DECLINE:**
> **Distressed Permian Operator** (composite profile)
> - TIV: $55M | Limit: $10M | Score: 248
> - Why: Multiple OSHA violations (willful), EPA enforcement action pending, recent bankruptcy filing, orphaned well obligations, no production in 6 months
> - Auto-declined. No human review needed.

---

## Implementation Plan

### Step 1: Configuration Generation via Builder

Each new configuration will be generated using the Coverage Builder with carefully constructed `CoverageSpec` objects. The builder handles:
- Signal selection and weight calculation
- Three-layer weight normalisation (Risk + Loss + Exposure = 1.0 per dimension)
- Tier band generation (respecting the chosen tier_strategy)
- ILF curve and deductible factor generation
- YAML serialisation and validation

However, the builder's output will be treated as a **starting point, not a final product**. Each configuration requires manual refinement because:
1. New signals (BOP testing, PHMSA compliance, technology maturity, etc.) are not in the builder's signal library
2. Pricing rates must be calibrated to market reality, not generated algorithmically
3. Score conditions and referral thresholds need domain-specific tuning

### Step 2: Manual Refinement & New Signal Integration

After builder generation, each configuration will be manually enhanced:
- Inject new domain-specific signals into the signal_registry
- Calibrate tier band thresholds to market pricing benchmarks
- Add domain-specific direct queries
- Tune score_conditions at both signal and group level
- Validate weight normalisation after all modifications

### Step 3: Documentation Generation

Run `doc_generator.py` to produce `logic.md` for each configuration. Then supplement with:
- **Narrative documentation** (the "why" behind each configuration) — embedded directly in the phase document and configuration comments
- **Example company profiles** — real-world submission scenarios showing the model producing credible output
- **Pricing validation** — theoretical premium calculations at each tier to verify actuarial reasonableness

### Step 4: Validation & Cross-Configuration Testing

- Run the builder's `validate` command against each generated config
- Verify multiplexer routing: ensure every combination of `operation_segment` + `tiv` routes to the intended configuration
- Verify no routing gaps: every valid energy submission must match at least `energy_general`
- Verify pricing continuity: a submission at the boundary between two configurations should produce comparable (not wildly different) premiums

---

## Summary of Deliverables

| # | Deliverable | Description |
|---|---|---|
| 1 | `energy_upstream_deepwater` config.yaml | Deepwater/offshore E&P configuration |
| 2 | `energy_upstream_onshore` config.yaml | Conventional onshore E&P configuration |
| 3 | `energy_upstream_unconventional` config.yaml | Tight oil, shale, fracking configuration |
| 4 | `energy_midstream` config.yaml | Pipeline, processing, storage configuration |
| 5 | `energy_downstream` config.yaml | Refining & petrochemical configuration |
| 6 | `energy_offshore_wind` config.yaml | Offshore wind farms configuration |
| 7 | `energy_onshore_renewable` config.yaml | Onshore wind & utility solar configuration |
| 8 | `energy_storage` config.yaml | Battery (BESS) & green hydrogen configuration |
| 9 | `energy_sme` config.yaml | Small operator BUNDLED configuration |
| 10 | Updated `energy/config.yaml` | All 12 configurations in energy coverage |
| 11 | Updated `logic.md` | Auto-generated documentation for all 12 models |
| 12 | Signal registry updates | All new signals registered in `signal_architecture/signals/` |
| 13 | Narrative documentation | This phase document serves as the detailed narrative |
| 14 | Seed data updates | `seed_dsi_bench.py` expanded with entries for all 12 configurations |

### Signal Registry Confirmation

All new domain-specific signals introduced across the eleven new configurations will be added to the signal registry at `signal_architecture/signals/inference/functions/energy/signals.py`. This includes:

- **Upstream onshore (5 new):** `produced_water_management`, `h2s_exposure`, `artificial_lift_reliability`, `state_regulatory_compliance`, `well_vintage_profile`
- **Upstream unconventional (6 new):** `frac_fleet_quality`, `water_recycling_rate`, `induced_seismicity_score`, `well_spacing_optimisation`, `completion_efficiency`, `pad_drilling_intensity`
- **Upstream deepwater (8 new):** `bop_testing_compliance`, `well_control_events`, `rig_contractor_quality`, `subsea_equipment_age`, `water_depth_profile`, `metocean_exposure`, `bsee_compliance_detail`, `spud_to_production`
- **Midstream (7 new):** `phmsa_compliance`, `inline_inspection`, `cathodic_protection`, `right_of_way`, `scada_maturity`, `pipeline_vintage`, `throughput_consistency`
- **Downstream (6 new):** `turnaround_compliance`, `psm_audit_findings`, `mechanical_integrity`, `feedstock_complexity`, `bi_exposure_ratio`, `process_unit_count`
- **Offshore wind (7 new):** `installation_vessel_quality`, `foundation_type`, `turbine_platform_generation`, `cable_route_risk`, `marine_weather_exposure`, `crew_transfer_safety`, `offtake_contract_quality`
- **Onshore renewable (5 new):** `hail_exposure`, `panel_technology_vintage`, `inverter_reliability`, `curtailment_rate`, `portfolio_geographic_spread`
- **Storage (8 new):** `battery_chemistry`, `thermal_management_system`, `fire_suppression_capability`, `bms_sophistication`, `hydrogen_storage_pressure`, `safety_standard_compliance`, `cell_format_maturity`, `electrolyser_technology`
- **Shared renewable (8 signals):** `technology_maturity`, `epc_contractor_quality`, `warranty_coverage`, `capacity_factor`, `natcat_exposure`, `grid_interconnection`, `ppa_quality`, `degradation_rate`

**Total new signals: 60** (some shared across renewable configs). Each will have a stub inference function registered in the metadata registry for demo/testing, with full extractor integrations phased in during subsequent implementation.

---

## Review Resolution Matrix

Review findings from the initial Phase 5 review have been incorporated into the expanded document and appendices.

| # | Review Finding | Resolution |
|---|---|---|
| 2.1 | Incomplete weight distributions | **Appendix B** — Complete R/L/E tables for all 11 configs |
| 2.2 | `construction_quality` group undefined | **Appendix D** — Full group definition with signals and lifecycle transition |
| 2.3 | Missing tier band specifications | **Appendix C** — Full 5-tier bands for all 11 configs |
| 3.1 | Small-operator routing gap | **Appendix G** — energy_general TIV threshold lowered to $25M |
| 3.2 | `operation_segment` pre-routing | **Appendix G** — Optional input field enabling specific routing |
| 4.1 | Signal specs incomplete | **Appendix D** — Full signal tables with inference functions |
| 5.1 | Pricing anchors missing | **Appendix F** — Base limit/deductible for all configs |
| 5.2 | ILF curves missing | **Appendix F** — Key ILF tables for deepwater and downstream |
| 7.1 | Direct queries missing | **Appendix E** — Segment-specific queries per config |
| 7.3 | MVI per config missing | **Appendix H** — Full MVI specs for all configs |
| 6.3 | Seed data plan | **Appendix I** — Expanded to all 12 configurations |

---

## Appendix A: The Energy Value Chain — Twelve Configurations

```
EXPLORATION → PRODUCTION → GATHERING → PROCESSING → TRANSPORTATION → REFINING → DISTRIBUTION
     ↑              ↑            ↑            ↑              ↑              ↑           ↑
     └──────────────┴────────────┘            └──────────────┘              └───────────┘
           UPSTREAM                              MIDSTREAM                   DOWNSTREAM
           ├─ energy_upstream_deepwater          energy_midstream           energy_downstream
           ├─ energy_upstream_onshore
           └─ energy_upstream_unconventional
```

Orthogonal to the hydrocarbon value chain:
```
RENEWABLE / ENERGY TRANSITION
├── energy_offshore_wind         Offshore wind farms (maritime construction + technology)
├── energy_onshore_renewable     Onshore wind & utility solar (mature, NatCat-driven)
└── energy_storage               Battery (BESS) & green hydrogen (emerging technology)

CROSS-CUTTING
├── energy_sme                   Small operators across all segments (BUNDLED pricing)
└── energy_general               Universal fallback (specificity=1)
```

Together, these twelve configurations can price:
- A $50B supermajor's global programme (routed to `energy_general` or specific segment configs)
- A $500M deepwater explorer in Guyana (routed to `energy_upstream_deepwater`)
- A $12B conventional Permian producer (routed to `energy_upstream_onshore`)
- A $28B shale operator (routed to `energy_upstream_unconventional`)
- A $15B pipeline MLP (routed to `energy_midstream`)
- A $20B independent refiner (routed to `energy_downstream`)
- A $12B offshore wind developer (routed to `energy_offshore_wind`)
- A $45B onshore wind/solar portfolio (routed to `energy_onshore_renewable`)
- A $5B BESS portfolio (routed to `energy_storage`)
- A $60M small Permian operator (routed to `energy_sme`)

No commercially relevant energy submission falls outside this matrix.

---

## Appendix B: Complete Three-Layer Weight Distributions

Every configuration must satisfy the DSI constraint: **Risk weights sum to 1.0, Loss weights sum to 1.0, Exposure weights sum to 1.0** across all groups. The tables below provide the complete distributions for each new configuration.

### Reference: `energy_general` (Existing)

| Group | Risk | Loss | Exposure |
|---|---|---|---|
| network_authority | 0.10 | 0.05 | 0.05 |
| safety_performance | 0.30 | 0.35 | 0.10 |
| environmental_compliance | 0.20 | 0.25 | 0.10 |
| operational_telemetry | 0.10 | 0.10 | 0.20 |
| financial_stability | 0.10 | 0.05 | 0.20 |
| asset_portfolio | 0.10 | 0.15 | 0.30 |
| corporate_footprint | 0.05 | 0.03 | 0.03 |
| structured_data | 0.05 | 0.02 | 0.02 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

### B.1: `energy_upstream_deepwater`

Safety performance is the dominant group across all three dimensions, reflecting the severity-dominated loss profile of deepwater operations. Environmental compliance carries elevated loss weight due to catastrophic spill exposure. Asset portfolio carries high exposure weight because deepwater assets are concentrated, high-value, and depth-dependent.

| Group | Risk | Loss | Exposure |
|---|---|---|---|
| network_authority | 0.05 | 0.03 | 0.03 |
| safety_performance | 0.35 | 0.40 | 0.10 |
| environmental_compliance | 0.20 | 0.25 | 0.10 |
| operational_telemetry | 0.10 | 0.10 | 0.15 |
| financial_stability | 0.10 | 0.05 | 0.15 |
| asset_portfolio | 0.10 | 0.12 | 0.40 |
| corporate_footprint | 0.05 | 0.03 | 0.05 |
| structured_data | 0.05 | 0.02 | 0.02 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

**Key shifts from general:**
- Safety Risk +0.05, Loss +0.05 (severity dominance)
- Asset Portfolio Exposure +0.10 (deepwater asset concentration)
- Network Authority reduced across all dimensions (less relevant for large operators)
- Corporate Footprint Exposure +0.02 (public safety culture matters for deepwater operators)

### B.2: `energy_upstream_onshore`

Safety performance remains the primary driver but at lower weight than deepwater — reflecting lower severity for conventional onshore operations. Operational telemetry is elevated because state regulatory data provides rich production and compliance signals. Environmental compliance retains moderate weight due to produced water management exposure.

| Group | Risk | Loss | Exposure |
|---|---|---|---|
| network_authority | 0.05 | 0.03 | 0.03 |
| safety_performance | 0.25 | 0.30 | 0.10 |
| environmental_compliance | 0.20 | 0.20 | 0.10 |
| operational_telemetry | 0.15 | 0.15 | 0.25 |
| financial_stability | 0.10 | 0.07 | 0.17 |
| asset_portfolio | 0.10 | 0.15 | 0.25 |
| corporate_footprint | 0.10 | 0.08 | 0.08 |
| structured_data | 0.05 | 0.02 | 0.02 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

**Key shifts from general:**
- Safety Performance Risk -0.05, Loss -0.05 (lower severity than general's blended portfolio)
- Operational Telemetry Risk +0.05, Exposure +0.05 (rich state regulatory data)
- Corporate Footprint Risk +0.05, Loss +0.05 (operational culture visible for established operators)

### B.3: `energy_upstream_unconventional`

Safety performance matches deepwater weighting — deliberate. Unconventional frac operations have comparable human safety exposure. Environmental compliance is elevated in exposure due to industrial-scale water management and induced seismicity. Operational telemetry reflects completion efficiency and frac fleet data richness.

| Group | Risk | Loss | Exposure |
|---|---|---|---|
| network_authority | 0.05 | 0.03 | 0.03 |
| safety_performance | 0.30 | 0.35 | 0.10 |
| environmental_compliance | 0.20 | 0.20 | 0.15 |
| operational_telemetry | 0.15 | 0.15 | 0.20 |
| financial_stability | 0.10 | 0.07 | 0.15 |
| asset_portfolio | 0.10 | 0.10 | 0.30 |
| corporate_footprint | 0.05 | 0.05 | 0.05 |
| structured_data | 0.05 | 0.05 | 0.02 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

**Key shifts from general:**
- Environmental Compliance Exposure +0.05 (induced seismicity, water management at industrial scale)
- Safety Performance matches general (high operational intensity justifies same weight)
- Asset Portfolio Exposure +0.00 but concentrated in well spacing and pad density

### B.4: `energy_midstream`

Operational telemetry is the primary driver, reflecting the frequency-driven loss profile of pipeline operations. Environmental compliance retains elevated weight due to pipeline spill exposure. Financial stability carries higher exposure weight because midstream MLPs often carry significant leverage.

| Group | Risk | Loss | Exposure |
|---|---|---|---|
| network_authority | 0.05 | 0.03 | 0.03 |
| safety_performance | 0.15 | 0.15 | 0.07 |
| environmental_compliance | 0.20 | 0.20 | 0.10 |
| operational_telemetry | 0.20 | 0.25 | 0.25 |
| financial_stability | 0.15 | 0.10 | 0.25 |
| asset_portfolio | 0.15 | 0.20 | 0.25 |
| corporate_footprint | 0.05 | 0.05 | 0.03 |
| structured_data | 0.05 | 0.02 | 0.02 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

**Key shifts from general:**
- Operational Telemetry Risk +0.10, Loss +0.15, Exposure +0.05 (frequency-driven)
- Safety Performance Risk -0.15, Loss -0.20 (lower human safety exposure)
- Financial Stability Risk +0.05, Exposure +0.05 (MLP leverage)
- Asset Portfolio Loss +0.05, Exposure -0.05 (linear asset risk is distributed)

### B.5: `energy_downstream`

Safety performance remains dominant (same severity driver as deepwater, but different signals — PSM vs drilling). Asset portfolio carries the highest exposure weight of any configuration because concentration risk defines downstream. Operational telemetry is elevated because process instrumentation directly predicts outcomes.

| Group | Risk | Loss | Exposure |
|---|---|---|---|
| network_authority | 0.05 | 0.03 | 0.03 |
| safety_performance | 0.30 | 0.35 | 0.10 |
| environmental_compliance | 0.10 | 0.10 | 0.07 |
| operational_telemetry | 0.15 | 0.15 | 0.20 |
| financial_stability | 0.10 | 0.07 | 0.15 |
| asset_portfolio | 0.15 | 0.15 | 0.35 |
| corporate_footprint | 0.10 | 0.10 | 0.05 |
| structured_data | 0.05 | 0.05 | 0.05 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

**Key shifts from general:**
- Environmental Compliance Risk -0.10, Loss -0.15 (downstream environmental risk is contained, not catastrophic spill)
- Asset Portfolio Exposure +0.05 (concentration defines downstream)
- Corporate Footprint Risk +0.05, Loss +0.07 (PSM culture is observable through corporate communications)
- Operational Telemetry Risk +0.05, Exposure +0.00 (process instrumentation matters)

### B.6: `energy_offshore_wind`

Construction quality is the dominant group — most offshore wind losses occur during construction and early operation. Safety performance is elevated vs onshore renewable due to genuine maritime safety exposure. Asset portfolio carries high exposure weight because of concentration in single large projects.

| Group | Risk | Loss | Exposure |
|---|---|---|---|
| network_authority | 0.05 | 0.03 | 0.02 |
| safety_performance | 0.15 | 0.15 | 0.10 |
| construction_quality | 0.20 | 0.25 | 0.15 |
| operational_telemetry | 0.15 | 0.15 | 0.18 |
| financial_stability | 0.10 | 0.10 | 0.15 |
| asset_portfolio | 0.20 | 0.15 | 0.35 |
| corporate_footprint | 0.10 | 0.12 | 0.03 |
| structured_data | 0.05 | 0.05 | 0.02 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

**Key shifts from general:**
- `environmental_compliance` replaced by `construction_quality` (Risk: 0.20, Loss: 0.25, Exposure: 0.15) — highest construction_quality weight of any config
- Safety Performance elevated vs onshore renewable (maritime operations)
- Corporate Footprint Loss +0.09 (developer track record is critical for offshore wind)

### B.7: `energy_onshore_renewable`

Asset portfolio dominates because NatCat exposure, technology selection, and geographic diversification define the risk. Operational telemetry is elevated — SCADA data from mature onshore installations is rich. Safety performance is minimal — onshore renewable has the lowest human safety exposure in energy.

| Group | Risk | Loss | Exposure |
|---|---|---|---|
| network_authority | 0.05 | 0.03 | 0.03 |
| safety_performance | 0.10 | 0.10 | 0.05 |
| construction_quality | 0.10 | 0.12 | 0.07 |
| operational_telemetry | 0.20 | 0.20 | 0.25 |
| financial_stability | 0.15 | 0.12 | 0.15 |
| asset_portfolio | 0.25 | 0.23 | 0.38 |
| corporate_footprint | 0.10 | 0.13 | 0.05 |
| structured_data | 0.05 | 0.07 | 0.02 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

**Key shifts from general:**
- `environmental_compliance` replaced by `construction_quality` (lower weight than offshore wind — onshore construction is simpler)
- Asset Portfolio has highest exposure weight (0.38) — NatCat and geographic spread define exposure
- Operational Telemetry Risk +0.10 (mature SCADA data is predictive)

### B.8: `energy_storage`

Asset portfolio has the highest combined weight (0.90) of any configuration in DSI — the technology (chemistry, thermal management, fire suppression) IS the risk. Construction quality elevated because BESS/hydrogen-specific EPC experience is scarce. Safety performance elevated vs onshore renewable due to thermal runaway and hydrogen explosion severity.

| Group | Risk | Loss | Exposure |
|---|---|---|---|
| network_authority | 0.05 | 0.03 | 0.02 |
| safety_performance | 0.15 | 0.15 | 0.10 |
| construction_quality | 0.15 | 0.20 | 0.10 |
| operational_telemetry | 0.10 | 0.10 | 0.15 |
| financial_stability | 0.10 | 0.07 | 0.13 |
| asset_portfolio | 0.30 | 0.25 | 0.35 |
| corporate_footprint | 0.10 | 0.13 | 0.10 |
| structured_data | 0.05 | 0.07 | 0.05 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

**Key shifts from general:**
- `environmental_compliance` replaced by `construction_quality` (BESS/hydrogen-specific EPC)
- Asset Portfolio Risk 0.30 — highest of any config (technology choice IS the risk)
- Corporate Footprint elevated — integrator/developer track record matters for emerging tech

### B.9: `energy_sme`

Aggressively prioritises DIRECT_OBSERVABLE signals. Network authority removed entirely (small operators lack meaningful network graphs). Corporate footprint and structured data minimised (small operators don't produce ESG reports). Financial stability elevated because small operators are more vulnerable to financial stress.

| Group | Risk | Loss | Exposure |
|---|---|---|---|
| safety_performance | 0.30 | 0.35 | 0.10 |
| environmental_compliance | 0.20 | 0.20 | 0.10 |
| operational_telemetry | 0.15 | 0.15 | 0.25 |
| financial_stability | 0.20 | 0.15 | 0.30 |
| asset_portfolio | 0.10 | 0.10 | 0.20 |
| corporate_footprint | 0.05 | 0.05 | 0.05 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

**Key shifts from general:**
- `network_authority` removed (6 groups, not 8)
- `structured_data` removed (small operators lack third-party ratings)
- Financial Stability Risk +0.10, Exposure +0.10 (SME vulnerability to financial stress)
- Operational Telemetry Exposure +0.05 (small operator exposure is operational)
- Corporate Footprint weights raised slightly to absorb residual from removed groups

---

## Appendix C: Risk Tier Band Specifications

Each configuration defines five risk tiers with score bands, actions, and rates. The Tier 3 rate is the reference rate discussed in the configuration narratives; other tiers scale from this anchor.

### C.1: `energy_upstream_deepwater`

Deepwater commands a ~55% rate premium over general at Tier 3, reflecting severity exposure. Tier 1 rates are aggressively low for best-in-class operators (rewarding safety investment). The gap between Tier 4 and Tier 5 is wider than general because marginal deepwater risks deteriorate rapidly.

| Tier | Label | Score Band | Action | Rate (× TIV) |
|---|---|---|---|---|
| 1 | PREFERRED | 800–1000 | APPROVE | 0.0012 |
| 2 | STANDARD_PLUS | 650–799 | APPROVE | 0.0020 |
| 3 | STANDARD | 500–649 | REFER | 0.0028 |
| 4 | SUBSTANDARD | 350–499 | REFER | 0.0045 |
| 5 | DECLINE | 0–349 | DECLINE | 0.0070 |

### C.2: `energy_upstream_onshore`

Conventional onshore rates are slightly below general, reflecting the maturity and predictability of the segment. Rich state regulatory data reduces underwriting uncertainty.

| Tier | Label | Score Band | Action | Rate (× TIV) |
|---|---|---|---|---|
| 1 | PREFERRED | 800–1000 | APPROVE | 0.0007 |
| 2 | STANDARD_PLUS | 650–799 | APPROVE | 0.0011 |
| 3 | STANDARD | 500–649 | REFER | 0.0016 |
| 4 | SUBSTANDARD | 350–499 | REFER | 0.0025 |
| 5 | DECLINE | 0–349 | DECLINE | 0.0040 |

### C.3: `energy_upstream_unconventional`

Unconventional rates match downstream — reflecting comparable severity from frac operations and induced seismicity exposure. Higher than conventional onshore due to operational intensity.

| Tier | Label | Score Band | Action | Rate (× TIV) |
|---|---|---|---|---|
| 1 | PREFERRED | 800–1000 | APPROVE | 0.0010 |
| 2 | STANDARD_PLUS | 650–799 | APPROVE | 0.0016 |
| 3 | STANDARD | 500–649 | REFER | 0.0022 |
| 4 | SUBSTANDARD | 350–499 | REFER | 0.0035 |
| 5 | DECLINE | 0–349 | DECLINE | 0.0055 |

### C.4: `energy_midstream`

Midstream rates are the lowest in the energy suite, reflecting the frequency-driven (low severity) loss profile. Pipeline operations are predictable and well-understood by the actuarial market. Auto-approve thresholds are more generous.

| Tier | Label | Score Band | Action | Rate (× TIV) |
|---|---|---|---|---|
| 1 | PREFERRED | 800–1000 | APPROVE | 0.0005 |
| 2 | STANDARD_PLUS | 650–799 | APPROVE | 0.0008 |
| 3 | STANDARD | 500–649 | REFER | 0.0012 |
| 4 | SUBSTANDARD | 350–499 | REFER | 0.0020 |
| 5 | DECLINE | 0–349 | DECLINE | 0.0035 |

### C.5: `energy_downstream`

Downstream rates sit between general and deepwater, reflecting concentration severity without the extreme tail of blowout risk. Business interruption exposure elevates the effective rate.

| Tier | Label | Score Band | Action | Rate (× TIV) |
|---|---|---|---|---|
| 1 | PREFERRED | 800–1000 | APPROVE | 0.0010 |
| 2 | STANDARD_PLUS | 650–799 | APPROVE | 0.0015 |
| 3 | STANDARD | 500–649 | REFER | 0.0022 |
| 4 | SUBSTANDARD | 350–499 | REFER | 0.0035 |
| 5 | DECLINE | 0–349 | DECLINE | 0.0055 |

### C.6: `energy_offshore_wind`

Offshore wind rates reflect maritime construction risk and project concentration. Higher than onshore renewable, comparable to general energy. Construction-phase submissions receive a 1.4x loading.

| Tier | Label | Score Band | Action | Rate (× TIV) |
|---|---|---|---|---|
| 1 | PREFERRED | 800–1000 | APPROVE | 0.0010 |
| 2 | STANDARD_PLUS | 650–799 | APPROVE | 0.0014 |
| 3 | STANDARD | 500–649 | REFER | 0.0020 |
| 4 | SUBSTANDARD | 350–499 | REFER | 0.0032 |
| 5 | DECLINE | 0–349 | DECLINE | 0.0050 |

### C.7: `energy_onshore_renewable`

The lowest rates in the energy suite — mature technology, thin severity tail, abundant market competition. Construction-phase submissions receive a 1.3x loading.

| Tier | Label | Score Band | Action | Rate (× TIV) |
|---|---|---|---|---|
| 1 | PREFERRED | 800–1000 | APPROVE | 0.0005 |
| 2 | STANDARD_PLUS | 650–799 | APPROVE | 0.0008 |
| 3 | STANDARD | 500–649 | REFER | 0.0013 |
| 4 | SUBSTANDARD | 350–499 | REFER | 0.0022 |
| 5 | DECLINE | 0–349 | DECLINE | 0.0035 |

### C.8: `energy_storage`

The highest renewable rate — matching deepwater — reflecting catastrophic severity (thermal runaway), immature loss data, and rapidly evolving technology. Rates will decline as the market matures.

| Tier | Label | Score Band | Action | Rate (× TIV) |
|---|---|---|---|---|
| 1 | PREFERRED | 800–1000 | APPROVE | 0.0012 |
| 2 | STANDARD_PLUS | 650–799 | APPROVE | 0.0020 |
| 3 | STANDARD | 500–649 | REFER | 0.0028 |
| 4 | SUBSTANDARD | 350–499 | REFER | 0.0045 |
| 5 | DECLINE | 0–349 | DECLINE | 0.0070 |

### C.9: `energy_sme`

SME rates are slightly higher than general at Tier 3 (less diversification), but the BUNDLED structure means premiums are capped by package limits. Auto-approve thresholds are higher (Tier 3 auto-approves with monitoring flags) to reduce underwriting expense.

| Tier | Label | Score Band | Action | Rate (× TIV) |
|---|---|---|---|---|
| 1 | PREFERRED | 800–1000 | APPROVE | 0.0008 |
| 2 | STANDARD_PLUS | 650–799 | APPROVE | 0.0014 |
| 3 | STANDARD | 500–649 | APPROVE_WITH_FLAG | 0.0020 |
| 4 | SUBSTANDARD | 350–499 | REFER | 0.0032 |
| 5 | DECLINE | 0–349 | DECLINE | 0.0050 |

**Note:** Tier 3 action is `APPROVE_WITH_FLAG` rather than `REFER` — this is the key SME automation enabler. Monitoring flags are set but the submission proceeds without human intervention.

---

## Appendix D: Complete Signal Specifications

Each new signal is defined with the full specification required by the builder and runtime: inference function, proxy tier, group, correlation direction, expectation level, and source. Signals retained from `energy_general` are not repeated here — only new signals introduced by each configuration.

### D.1: `energy_upstream_deepwater` — New Signals

| Signal ID | Inference Function | Proxy Tier | Group | Source | Correlation | Expectation |
|---|---|---|---|---|---|---|
| `bop_testing_compliance` | `bop_testing_compliance_basefunction` | DIRECT_OBSERVABLE | safety_performance | score | positive | REQUIRED |
| `well_control_events` | `well_control_events_basefunction` | DIRECT_OBSERVABLE | safety_performance | score | positive | REQUIRED |
| `rig_contractor_quality` | `rig_contractor_quality_basefunction` | INFERRED_PROXY | network_authority | score | positive | EXPECTED |
| `subsea_equipment_age` | `subsea_equipment_age_basefunction` | INFERRED_PROXY | asset_portfolio | score | negative | EXPECTED |
| `water_depth_profile` | `water_depth_profile_basefunction` | DIRECT_OBSERVABLE | asset_portfolio | score | negative | REQUIRED |
| `metocean_exposure` | `metocean_exposure_basefunction` | DIRECT_OBSERVABLE | asset_portfolio | score | negative | REQUIRED |
| `bsee_compliance_detail` | `bsee_compliance_detail_basefunction` | DIRECT_OBSERVABLE | safety_performance | score | positive | REQUIRED |
| `spud_to_production` | `spud_to_production_basefunction` | INFERRED_PROXY | operational_telemetry | score | positive | OPTIONAL |

**Retained from `energy_general` (42 signals):** All signals except `near_miss` (replaced by more specific `well_control_events`) and `production_consistency` (replaced by `spud_to_production` for deepwater context). Total signal count: **48** (42 retained + 8 new - 2 replaced).

**Score conditions for new signals:**

| Signal ID | Threshold | Comparison | Action | Override | Note |
|---|---|---|---|---|---|
| `bop_testing_compliance` | 30 | <= | REFER | 5 | BOP non-compliance is a decline-level signal |
| `bop_testing_compliance` | 50 | <= | REFER | 4 | Marginal BOP compliance |
| `well_control_events` | 25 | <= | REFER | 5 | Recent well control events |
| `well_control_events` | 45 | <= | REFER | 4 | Well control history concerns |
| `water_depth_profile` | 25 | <= | FLAG | null | Ultra-deepwater (>7500ft) risk flag |
| `subsea_equipment_age` | 30 | <= | REFER | 4 | Aging subsea infrastructure |
| `metocean_exposure` | 20 | <= | REFER | 4 | Extreme NatCat zone |

### D.2: `energy_upstream_onshore` — New Signals

| Signal ID | Inference Function | Proxy Tier | Group | Source | Correlation | Expectation |
|---|---|---|---|---|---|---|
| `produced_water_management` | `produced_water_management_basefunction` | INFERRED_PROXY | environmental_compliance | score | positive | REQUIRED |
| `h2s_exposure` | `h2s_exposure_basefunction` | DIRECT_OBSERVABLE | safety_performance | score | negative | REQUIRED |
| `artificial_lift_reliability` | `artificial_lift_reliability_basefunction` | INFERRED_PROXY | operational_telemetry | score | positive | EXPECTED |
| `state_regulatory_compliance` | `state_regulatory_compliance_basefunction` | DIRECT_OBSERVABLE | safety_performance | score | positive | REQUIRED |
| `well_vintage_profile` | `well_vintage_profile_basefunction` | INFERRED_PROXY | asset_portfolio | score | negative | EXPECTED |

**Retained from `energy_general` (43 signals):** Removes `bsee_incident` (onshore, not BSEE-regulated). Adds 5 new onshore-specific signals. Total signal count: **46**.

**Score conditions for new signals:**

| Signal ID | Threshold | Comparison | Action | Override | Note |
|---|---|---|---|---|---|
| `h2s_exposure` | 20 | <= | REFER | 5 | High H2S concentration — fatality risk |
| `h2s_exposure` | 40 | <= | REFER | 4 | Elevated H2S exposure |
| `state_regulatory_compliance` | 25 | <= | REFER | 5 | State regulatory enforcement actions |
| `state_regulatory_compliance` | 45 | <= | REFER | 4 | Regulatory compliance concerns |
| `produced_water_management` | 30 | <= | REFER | 4 | Produced water management deficiencies |
| `well_vintage_profile` | 25 | <= | FLAG | null | Aging well stock (>30 year average) |

### D.3: `energy_upstream_unconventional` — New Signals

| Signal ID | Inference Function | Proxy Tier | Group | Source | Correlation | Expectation |
|---|---|---|---|---|---|---|
| `frac_fleet_quality` | `frac_fleet_quality_basefunction` | INFERRED_PROXY | operational_telemetry | score | positive | REQUIRED |
| `water_recycling_rate` | `water_recycling_rate_basefunction` | DIRECT_OBSERVABLE | environmental_compliance | score | positive | REQUIRED |
| `induced_seismicity_score` | `induced_seismicity_score_basefunction` | DIRECT_OBSERVABLE | environmental_compliance | score | positive | REQUIRED |
| `well_spacing_optimisation` | `well_spacing_optimisation_basefunction` | INFERRED_PROXY | asset_portfolio | score | positive | EXPECTED |
| `completion_efficiency` | `completion_efficiency_basefunction` | INFERRED_PROXY | operational_telemetry | score | positive | EXPECTED |
| `pad_drilling_intensity` | `pad_drilling_intensity_basefunction` | INFERRED_PROXY | operational_telemetry | score | negative | OPTIONAL |

**Retained from `energy_general` (42 signals):** Removes `bsee_incident` (onshore), `production_consistency` (replaced by `completion_efficiency`). Adds 6 new unconventional-specific signals. Total signal count: **46**.

**Score conditions for new signals:**

| Signal ID | Threshold | Comparison | Action | Override | Note |
|---|---|---|---|---|---|
| `induced_seismicity_score` | 15 | <= | REFER | 5 | Active seismicity zone — regulatory shut-in risk |
| `induced_seismicity_score` | 35 | <= | REFER | 4 | Elevated seismicity exposure |
| `frac_fleet_quality` | 30 | <= | REFER | 4 | Aging/inadequate frac fleet |
| `water_recycling_rate` | 25 | <= | FLAG | null | Low water recycling — elevated disposal volume |
| `well_spacing_optimisation` | 25 | <= | REFER | 4 | Frac hit risk — poor well spacing |
| `completion_efficiency` | 30 | <= | FLAG | null | Below-basin-average completion metrics |

### D.4: `energy_midstream` — New Signals

| Signal ID | Inference Function | Proxy Tier | Group | Source | Correlation | Expectation |
|---|---|---|---|---|---|---|
| `phmsa_compliance` | `phmsa_compliance_basefunction` | DIRECT_OBSERVABLE | safety_performance | score | positive | REQUIRED |
| `inline_inspection` | `inline_inspection_basefunction` | INFERRED_PROXY | operational_telemetry | score | positive | REQUIRED |
| `cathodic_protection` | `cathodic_protection_basefunction` | INFERRED_PROXY | operational_telemetry | score | positive | EXPECTED |
| `right_of_way` | `right_of_way_basefunction` | INFERRED_PROXY | asset_portfolio | score | positive | EXPECTED |
| `scada_maturity` | `scada_maturity_basefunction` | INFERRED_PROXY | operational_telemetry | score | positive | EXPECTED |
| `pipeline_vintage` | `pipeline_vintage_basefunction` | INFERRED_PROXY | asset_portfolio | score | negative | REQUIRED |
| `throughput_consistency` | `throughput_consistency_basefunction` | INFERRED_PROXY | operational_telemetry | score | positive | OPTIONAL |

**Retained from `energy_general` (38 signals):** Removes `bsee_incident` (not applicable — PHMSA replaces BSEE), `well_integrity` (not applicable — pipelines, not wells), `decommissioning` (replaced by `pipeline_vintage`). Adds 7 new midstream-specific signals. Total signal count: **42** (38 retained + 7 new - 3 replaced).

**Score conditions for new signals:**

| Signal ID | Threshold | Comparison | Action | Override | Note |
|---|---|---|---|---|---|
| `phmsa_compliance` | 25 | <= | REFER | 5 | PHMSA enforcement actions |
| `phmsa_compliance` | 45 | <= | REFER | 4 | PHMSA compliance concerns |
| `inline_inspection` | 30 | <= | REFER | 4 | Inadequate inline inspection cadence |
| `cathodic_protection` | 35 | <= | FLAG | null | Cathodic protection gaps |
| `pipeline_vintage` | 25 | <= | REFER | 4 | Aging pipeline infrastructure |
| `right_of_way` | 30 | <= | FLAG | null | Right-of-way encroachment concerns |

### D.5: `energy_downstream` — New Signals

| Signal ID | Inference Function | Proxy Tier | Group | Source | Correlation | Expectation |
|---|---|---|---|---|---|---|
| `turnaround_compliance` | `turnaround_compliance_basefunction` | INFERRED_PROXY | asset_portfolio | score | positive | REQUIRED |
| `psm_audit_findings` | `psm_audit_findings_basefunction` | DIRECT_OBSERVABLE | safety_performance | score | positive | REQUIRED |
| `mechanical_integrity` | `mechanical_integrity_basefunction` | INFERRED_PROXY | operational_telemetry | score | positive | EXPECTED |
| `feedstock_complexity` | `feedstock_complexity_basefunction` | INFERRED_PROXY | asset_portfolio | score | negative | REQUIRED |
| `bi_exposure_ratio` | `bi_exposure_ratio_basefunction` | INFERRED_PROXY | financial_stability | score | negative | EXPECTED |
| `process_unit_count` | `process_unit_count_basefunction` | INFERRED_PROXY | asset_portfolio | score | negative | EXPECTED |

**Retained from `energy_general` (42 signals):** Removes `bsee_incident` (not applicable for onshore refineries), `well_integrity` (no wells), `decommissioning` (replaced by `turnaround_compliance`). Adds 6 new downstream-specific signals. Total signal count: **45** (42 retained + 6 new - 3 replaced).

**Score conditions for new signals:**

| Signal ID | Threshold | Comparison | Action | Override | Note |
|---|---|---|---|---|---|
| `turnaround_compliance` | 25 | <= | REFER | 5 | Severely deferred turnaround — catastrophic risk |
| `turnaround_compliance` | 40 | <= | REFER | 4 | Turnaround deferral concerns |
| `psm_audit_findings` | 25 | <= | REFER | 5 | Critical PSM deficiencies |
| `psm_audit_findings` | 45 | <= | REFER | 4 | PSM audit concerns |
| `mechanical_integrity` | 30 | <= | REFER | 4 | Mechanical integrity programme gaps |
| `feedstock_complexity` | 25 | <= | FLAG | null | High-complexity refinery (Nelson Index > 12) |
| `bi_exposure_ratio` | 30 | <= | FLAG | null | Extreme BI/PD ratio (>3:1) |

### D.6: `energy_offshore_wind` — New Signals

Shares the `construction_quality` group and base renewable signals with onshore renewable and storage, plus offshore-wind-specific signals.

**Shared renewable signals (used across all three renewable configs):**

| Signal ID | Inference Function | Proxy Tier | Group | Source | Correlation | Expectation |
|---|---|---|---|---|---|---|
| `technology_maturity` | `technology_maturity_basefunction` | INFERRED_PROXY | asset_portfolio | score | positive | REQUIRED |
| `epc_contractor_quality` | `epc_contractor_quality_basefunction` | INFERRED_PROXY | construction_quality | score | positive | REQUIRED |
| `warranty_coverage` | `warranty_coverage_basefunction` | DIRECT_OBSERVABLE | asset_portfolio | score | positive | REQUIRED |
| `capacity_factor` | `capacity_factor_basefunction` | DIRECT_OBSERVABLE | operational_telemetry | score | positive | EXPECTED |
| `natcat_exposure` | `natcat_exposure_basefunction` | DIRECT_OBSERVABLE | asset_portfolio | score | negative | REQUIRED |
| `grid_interconnection` | `grid_interconnection_basefunction` | INFERRED_PROXY | operational_telemetry | score | positive | EXPECTED |
| `ppa_quality` | `ppa_quality_basefunction` | INFERRED_PROXY | financial_stability | score | positive | EXPECTED |
| `degradation_rate` | `degradation_rate_basefunction` | DIRECT_OBSERVABLE | operational_telemetry | score | positive | EXPECTED |
| `commissioning_defects` | `commissioning_defects_basefunction` | INFERRED_PROXY | construction_quality | score | positive | REQUIRED |
| `construction_phase` | `construction_phase_basefunction` | DIRECT_OBSERVABLE | construction_quality | metadata.construction_phase | — | REQUIRED |
| `epc_track_record` | `epc_track_record_basefunction` | INFERRED_PROXY | construction_quality | score | positive | EXPECTED |
| `supply_chain_quality` | `supply_chain_quality_basefunction` | INFERRED_PROXY | construction_quality | score | positive | OPTIONAL |

**Offshore-wind-specific signals:**

| Signal ID | Inference Function | Proxy Tier | Group | Source | Correlation | Expectation |
|---|---|---|---|---|---|---|
| `installation_vessel_quality` | `installation_vessel_quality_basefunction` | INFERRED_PROXY | construction_quality | score | positive | REQUIRED |
| `foundation_type` | `foundation_type_basefunction` | DIRECT_OBSERVABLE | asset_portfolio | metadata.foundation_type | — | REQUIRED |
| `turbine_platform_generation` | `turbine_platform_generation_basefunction` | INFERRED_PROXY | asset_portfolio | score | positive | REQUIRED |
| `cable_route_risk` | `cable_route_risk_basefunction` | INFERRED_PROXY | asset_portfolio | score | negative | EXPECTED |
| `marine_weather_exposure` | `marine_weather_exposure_basefunction` | DIRECT_OBSERVABLE | asset_portfolio | score | negative | REQUIRED |
| `crew_transfer_safety` | `crew_transfer_safety_basefunction` | INFERRED_PROXY | safety_performance | score | positive | EXPECTED |
| `offtake_contract_quality` | `offtake_contract_quality_basefunction` | INFERRED_PROXY | financial_stability | score | positive | EXPECTED |

The `foundation_type` signal is categorical:

| Category | Label | Applied |
|---|---|---|
| MONOPILE | Monopile (proven) | 0.90 |
| JACKET | Jacket (proven) | 0.95 |
| GRAVITY_BASE | Gravity Base | 1.00 |
| FLOATING_SPAR | Floating Spar (emerging) | 1.30 |
| FLOATING_SEMI | Floating Semi-Sub (emerging) | 1.35 |
| FLOATING_TLP | Floating TLP (first-of-kind) | 1.50 |

**Total signal count: 42** (23 retained from energy_general base + 12 shared renewable + 7 offshore-specific).

### D.7: `energy_onshore_renewable` — New Signals

Uses shared renewable signals plus onshore-specific signals.

**Onshore-renewable-specific signals:**

| Signal ID | Inference Function | Proxy Tier | Group | Source | Correlation | Expectation |
|---|---|---|---|---|---|---|
| `hail_exposure` | `hail_exposure_basefunction` | DIRECT_OBSERVABLE | asset_portfolio | score | negative | REQUIRED |
| `panel_technology_vintage` | `panel_technology_vintage_basefunction` | INFERRED_PROXY | asset_portfolio | score | negative | EXPECTED |
| `inverter_reliability` | `inverter_reliability_basefunction` | INFERRED_PROXY | operational_telemetry | score | positive | EXPECTED |
| `curtailment_rate` | `curtailment_rate_basefunction` | DIRECT_OBSERVABLE | operational_telemetry | score | positive | EXPECTED |
| `portfolio_geographic_spread` | `portfolio_geographic_spread_basefunction` | INFERRED_PROXY | asset_portfolio | score | positive | EXPECTED |

**Total signal count: 40** (23 retained + 12 shared renewable + 5 onshore-specific).

**Score conditions for onshore-renewable-specific signals:**

| Signal ID | Threshold | Comparison | Action | Override | Note |
|---|---|---|---|---|---|
| `hail_exposure` | 20 | <= | REFER | 4 | Extreme hail zone (Texas Panhandle, Colorado) |
| `hail_exposure` | 35 | <= | FLAG | null | Elevated hail exposure |
| `inverter_reliability` | 25 | <= | REFER | 4 | Known inverter reliability issues |
| `curtailment_rate` | 20 | <= | FLAG | null | High grid curtailment — BI exposure |
| `panel_technology_vintage` | 25 | <= | FLAG | null | Aging panel technology with known defects |

### D.8: `energy_storage` — New Signals

Uses shared renewable signals plus storage-specific signals. The `battery_chemistry` categorical signal is the single most important routing signal for BESS pricing.

**Storage-specific signals:**

| Signal ID | Inference Function | Proxy Tier | Group | Source | Correlation | Expectation |
|---|---|---|---|---|---|---|
| `battery_chemistry` | `battery_chemistry_basefunction` | DIRECT_OBSERVABLE | asset_portfolio | metadata.battery_chemistry | — | REQUIRED |
| `thermal_management_system` | `thermal_management_system_basefunction` | INFERRED_PROXY | asset_portfolio | score | positive | REQUIRED |
| `fire_suppression_capability` | `fire_suppression_capability_basefunction` | DIRECT_OBSERVABLE | asset_portfolio | score | positive | REQUIRED |
| `bms_sophistication` | `bms_sophistication_basefunction` | INFERRED_PROXY | operational_telemetry | score | positive | EXPECTED |
| `hydrogen_storage_pressure` | `hydrogen_storage_pressure_basefunction` | DIRECT_OBSERVABLE | asset_portfolio | score | negative | REQUIRED |
| `safety_standard_compliance` | `safety_standard_compliance_basefunction` | DIRECT_OBSERVABLE | safety_performance | score | positive | REQUIRED |
| `cell_format_maturity` | `cell_format_maturity_basefunction` | INFERRED_PROXY | asset_portfolio | score | positive | EXPECTED |
| `electrolyser_technology` | `electrolyser_technology_basefunction` | INFERRED_PROXY | asset_portfolio | score | positive | EXPECTED |

The `battery_chemistry` signal is categorical:

| Category | Label | Applied |
|---|---|---|
| LFP | Lithium Iron Phosphate | 0.85 |
| NMC | Nickel Manganese Cobalt | 1.20 |
| NCA | Nickel Cobalt Aluminium | 1.30 |
| SODIUM_ION | Sodium Ion (emerging) | 1.15 |
| SOLID_STATE | Solid State (first-of-kind) | 1.50 |

**Total signal count: 43** (23 retained + 12 shared renewable + 8 storage-specific).

**Score conditions for storage-specific signals:**

| Signal ID | Threshold | Comparison | Action | Override | Note |
|---|---|---|---|---|---|
| `thermal_management_system` | 20 | <= | REFER | 5 | Inadequate thermal management — catastrophic risk |
| `thermal_management_system` | 40 | <= | REFER | 4 | Thermal management concerns |
| `fire_suppression_capability` | 25 | <= | REFER | 5 | No effective fire suppression — decline-level |
| `fire_suppression_capability` | 40 | <= | REFER | 4 | Fire suppression gaps |
| `safety_standard_compliance` | 30 | <= | REFER | 5 | Non-compliant with NFPA 855/UL 9540A |
| `hydrogen_storage_pressure` | 20 | <= | REFER | 4 | High-pressure hydrogen (700 bar) |
| `bms_sophistication` | 30 | <= | FLAG | null | Basic BMS — no cell-level monitoring |

**`construction_quality` Group — Full Definition (shared across all three renewable configs):**

This signal group replaces `environmental_compliance` in all renewable configurations. It contains 4 scored signals and 1 categorical signal:

| Signal ID | Proxy Tier | Weight (Risk) | Weight (Loss) | Weight (Exposure) | Description |
|---|---|---|---|---|---|
| `epc_contractor_quality` | INFERRED_PROXY | 0.30 | 0.30 | 0.25 | EPC contractor track record and tier classification |
| `commissioning_defects` | INFERRED_PROXY | 0.25 | 0.25 | 0.20 | Defect density during commissioning phase |
| `epc_track_record` | INFERRED_PROXY | 0.20 | 0.20 | 0.25 | EPC contractor historical project delivery |
| `supply_chain_quality` | INFERRED_PROXY | 0.10 | 0.10 | 0.15 | Component supply chain tier quality |
| `construction_phase` | DIRECT_OBSERVABLE | — | — | — | Categorical modifier |

The `construction_phase` categorical modifiers:

| Category | Label | Applied |
|---|---|---|
| PRE_CONSTRUCTION | Pre-Construction | 1.50 |
| CONSTRUCTION | Under Construction | 1.30 |
| COMMISSIONING | Commissioning | 1.15 |
| EARLY_OPERATION | Early Operation (<3 years) | 1.05 |
| MATURE_OPERATION | Mature Operation (3+ years) | 0.90 |

**Lifecycle transition:** As projects move from construction to operation, the `construction_phase` categorical modifier decreases and operational telemetry signals gain predictive value. The group weight distribution does not change — the signals naturally reflect lifecycle stage through their scores.

**Shared renewable score conditions:**

| Signal ID | Threshold | Comparison | Action | Override | Note |
|---|---|---|---|---|---|
| `technology_maturity` | 20 | <= | REFER | 5 | First-of-kind technology |
| `technology_maturity` | 35 | <= | REFER | 4 | Immature technology platform |
| `epc_contractor_quality` | 25 | <= | REFER | 4 | Unproven EPC contractor |
| `warranty_coverage` | 30 | <= | REFER | 4 | Inadequate warranty coverage |
| `natcat_exposure` | 20 | <= | REFER | 4 | Extreme NatCat zone |
| `capacity_factor` | 30 | <= | FLAG | null | Underperforming asset |
| `commissioning_defects` | 25 | <= | REFER | 4 | High commissioning defect rate |
| `ppa_quality` | 25 | <= | FLAG | null | Weak PPA counterparty or short tenor |

### D.9: `energy_sme` — Signal Reduction Strategy

The SME configuration targets **25 signals** — a 47% reduction from `energy_general`'s 47. The reduction strategy prioritises retaining DIRECT_OBSERVABLE signals (target: 60%+) and removing signals that require deep inference on thin digital footprints.

**Removed signals (22 signals):**

| Removed Signal | Group | Reason |
|---|---|---|
| `partner_quality` | network_authority | Group removed entirely |
| `contractor_quality` | network_authority | Group removed entirely |
| `banking_relationship` | network_authority | Group removed entirely |
| `insurance_history` | network_authority | Group removed entirely |
| `industry_association` | network_authority | Group removed entirely |
| `regulator_relationship` | network_authority | Group removed entirely |
| `customer_quality` | network_authority | Group removed entirely |
| `esg_rating` | structured_data | Group removed entirely |
| `benchmark` | structured_data | Group removed entirely |
| `credit` | structured_data | Group removed entirely |
| `bsee_incident` | safety_performance | Not applicable for most SME operators |
| `near_miss` | safety_performance | Small operators rarely report near-misses |
| `flaring` | environmental_compliance | Thin data for small operators |
| `methane` | environmental_compliance | Thin data for small operators |
| `remediation` | environmental_compliance | Low predictive value for SME scale |
| `facility_activity` | operational_telemetry | Thin inference for small operations |
| `operational_efficiency` | operational_telemetry | Thin inference for small operations |
| `decommissioning` | asset_portfolio | Low relevance for small active operators |
| `complexity` | asset_portfolio | Low relevance for simple operations |
| `esg_reporting` | corporate_footprint | Small operators don't produce ESG reports |
| `disclosure_quality` | corporate_footprint | Low data availability |
| `hse_leadership` | corporate_footprint | Thin inference for small companies |

**Retained signals (25 signals):**

| # | Signal ID | Group | Proxy Tier |
|---|---|---|---|
| 1 | `operator_type` | operator_type (categorical) | INFERRED_PROXY |
| 2 | `operation_segment` | operation_segment (categorical) | INFERRED_PROXY |
| 3 | `geographic_focus` | geographic_focus (categorical) | INFERRED_PROXY |
| 4 | `osha_trir` | safety_performance | DIRECT_OBSERVABLE |
| 5 | `osha_violations` | safety_performance | DIRECT_OBSERVABLE |
| 6 | `process_safety` | safety_performance | INFERRED_PROXY |
| 7 | `fatality` | safety_performance | DIRECT_OBSERVABLE |
| 8 | `major_incident` | safety_performance | DIRECT_OBSERVABLE |
| 9 | `epa_violation` | environmental_compliance | DIRECT_OBSERVABLE |
| 10 | `spill_history` | environmental_compliance | DIRECT_OBSERVABLE |
| 11 | `emissions_compliance` | environmental_compliance | DIRECT_OBSERVABLE |
| 12 | `production_consistency` | operational_telemetry | INFERRED_PROXY |
| 13 | `well_integrity` | operational_telemetry | INFERRED_PROXY |
| 14 | `maintenance_pattern` | operational_telemetry | INFERRED_PROXY |
| 15 | `credit_rating` | financial_stability | DIRECT_OBSERVABLE |
| 16 | `leverage` | financial_stability | DIRECT_OBSERVABLE |
| 17 | `aro_coverage` | financial_stability | INFERRED_PROXY |
| 18 | `capex_trend` | financial_stability | DIRECT_OBSERVABLE |
| 19 | `restructuring` | financial_stability | DIRECT_OBSERVABLE |
| 20 | `asset_age` | asset_portfolio | INFERRED_PROXY |
| 21 | `concentration` | asset_portfolio | INFERRED_PROXY |
| 22 | `permit_status` | asset_portfolio | DIRECT_OBSERVABLE |
| 23 | `safety_communication` | corporate_footprint | DIRECT_OBSERVABLE |
| 24 | `technical_hiring` | corporate_footprint | INFERRED_PROXY |
| 25 | `industry_presence` | corporate_footprint | DIRECT_OBSERVABLE |

**DIRECT_OBSERVABLE count: 15/25 = 60%.** Target met.

---

## Appendix E: Direct Queries per Configuration

Direct queries are binary questions answered before signal execution. Each configuration has 4-8 queries tuned to its segment. Queries inherited from `energy_general` are marked with *(inherited)*.

### E.1: `energy_upstream_deepwater`

| ID | Question | Return=true Action | Override | Note |
|---|---|---|---|---|
| `major_incidents` | Any major incidents (blowout, explosion, major spill) in past 5 years? *(inherited)* | REFER | 4 | Major incidents disclosed |
| `fatalities` | Any work-related fatalities in past 3 years? *(inherited)* | REFER | 3 | Fatalities disclosed |
| `well_control_loss` | Any loss of well control events in past 10 years? | REFER | 5 | Well control event — deepwater-specific |
| `bop_failure` | Any BOP activation failures or test failures in past 3 years? | REFER | 5 | BOP failure is catastrophic signal |
| `regulatory_enforcement` | Any significant regulatory enforcement actions pending? *(inherited)* | REFER | 4 | Pending enforcement |
| `single_well_concentration` | Is >50% of programme TIV concentrated in a single well or platform? | FLAG | null | Concentration flag |
| `hurricane_zone` | Are operated assets in GoM hurricane zone (Saffir-Simpson Cat 3+ exposure)? | FLAG | null | NatCat overlay |

### E.2: `energy_upstream_onshore`

| ID | Question | Return=true Action | Override | Note |
|---|---|---|---|---|
| `major_incidents` | Any major incidents in past 5 years? *(inherited)* | REFER | 4 | Major incidents |
| `fatalities` | Any work-related fatalities in past 3 years? *(inherited)* | REFER | 3 | Fatalities |
| `h2s_presence` | Are any operated wells in H2S-classified zones? | FLAG | null | H2S exposure flag |
| `regulatory_enforcement` | Any significant regulatory enforcement actions pending? *(inherited)* | REFER | 4 | Pending enforcement |
| `orphan_wells` | Any orphaned or idle well obligations on the operator's record? | FLAG | null | Environmental liability |
| `state_violations` | Any state oil & gas commission violations (RRC, OCC, etc.) in past 3 years? | REFER | 4 | State regulatory violations |

### E.3: `energy_upstream_unconventional`

| ID | Question | Return=true Action | Override | Note |
|---|---|---|---|---|
| `major_incidents` | Any major incidents (wellhead blowout, frac incident, major spill) in past 5 years? | REFER | 4 | Major incidents |
| `fatalities` | Any work-related fatalities in past 3 years? *(inherited)* | REFER | 3 | Fatalities |
| `induced_seismicity` | Any operations in state-designated induced seismicity zones or SWD shut-in orders? | REFER | 4 | Seismicity exposure |
| `frac_hit_history` | Any frac hit / well interference events in past 3 years? | FLAG | null | Parent-child interference |
| `regulatory_enforcement` | Any significant regulatory enforcement actions pending? *(inherited)* | REFER | 4 | Pending enforcement |
| `water_disposal_violations` | Any SWD well violations or produced water disposal incidents? | REFER | 4 | Water management violations |

### E.4: `energy_midstream`

| ID | Question | Return=true Action | Override | Note |
|---|---|---|---|---|
| `major_incidents` | Any major pipeline ruptures, explosions, or significant releases in past 5 years? | REFER | 4 | Pipeline incidents |
| `fatalities` | Any work-related fatalities in past 3 years? *(inherited)* | REFER | 3 | Fatalities disclosed |
| `phmsa_enforcement` | Any PHMSA enforcement actions or corrective action orders in past 5 years? | REFER | 4 | PHMSA enforcement |
| `third_party_strike` | Any third-party damage incidents (excavation strikes) in past 3 years? | FLAG | null | Third-party damage flag |
| `regulatory_enforcement` | Any significant regulatory enforcement actions pending? *(inherited)* | REFER | 4 | Pending enforcement |
| `hca_crossing` | Does pipeline cross High Consequence Areas (HCAs) per PHMSA definition? | FLAG | null | HCA exposure flag |

### E.5: `energy_downstream`

| ID | Question | Return=true Action | Override | Note |
|---|---|---|---|---|
| `major_incidents` | Any major incidents (explosion, fire, major release) in past 5 years? *(inherited)* | REFER | 4 | Major incidents disclosed |
| `fatalities` | Any work-related fatalities in past 3 years? *(inherited)* | REFER | 3 | Fatalities disclosed |
| `turnaround_deferred` | Has any scheduled turnaround/shutdown been deferred >12 months? | REFER | 4 | Turnaround deferral — #1 downstream risk signal |
| `psm_citations` | Any OSHA PSM citations (willful or repeat) in past 5 years? | REFER | 5 | PSM citations are severe |
| `regulatory_enforcement` | Any significant regulatory enforcement actions pending? *(inherited)* | REFER | 4 | Pending enforcement |
| `single_unit_dependency` | Is >60% of throughput dependent on a single process unit? | FLAG | null | Single point of failure |
| `hf_alkylation` | Does the refinery operate an HF (hydrofluoric acid) alkylation unit? | FLAG | null | HF unit exposure flag |

### E.6: `energy_offshore_wind`

| ID | Question | Return=true Action | Override | Note |
|---|---|---|---|---|
| `construction_incidents` | Any construction-phase incidents causing >30 day delay? | REFER | 4 | Construction risk |
| `vessel_incident` | Any installation vessel incidents (jack-up failure, crane incident) in past 5 years? | REFER | 5 | Maritime construction risk |
| `cable_failure` | Any export cable failures or damage events? | REFER | 4 | Cable route risk |
| `technology_first_of_kind` | Is this a first-of-kind technology deployment (floating wind, new turbine platform)? | REFER | 4 | Technology risk |
| `ppa_unsigned` | Is the CFD/PPA/OREC unsigned or under negotiation? | REFER | 4 | Revenue uncertainty |
| `serial_defect` | Any known serial defect advisories on deployed turbines? | REFER | 5 | Fleet-wide risk |

### E.7: `energy_onshore_renewable`

| ID | Question | Return=true Action | Override | Note |
|---|---|---|---|---|
| `construction_incidents` | Any construction-phase incidents causing >30 day delay? | REFER | 4 | Construction risk |
| `hail_claims` | Any hail damage claims in past 3 years? | FLAG | null | NatCat exposure |
| `serial_defect` | Any known serial defect advisories on deployed equipment (blades, inverters, panels)? | REFER | 5 | Fleet-wide risk |
| `grid_connection_delay` | Has grid interconnection been delayed >6 months? | FLAG | null | Grid risk |
| `ppa_unsigned` | Is the PPA unsigned or under negotiation? | REFER | 4 | Revenue uncertainty |
| `warranty_dispute` | Any active warranty disputes with OEM? | FLAG | null | Warranty risk |

### E.8: `energy_storage`

| ID | Question | Return=true Action | Override | Note |
|---|---|---|---|---|
| `thermal_event` | Any thermal runaway events or battery fires at operated facilities? | REFER | 5 | Catastrophic — decline-level signal |
| `technology_first_of_kind` | Is this a first-of-kind technology (new chemistry, new cell format, SOEC electrolyser)? | REFER | 4 | Technology risk |
| `nfpa_non_compliance` | Do any installations pre-date current NFPA 855 / UL 9540A standards? | REFER | 4 | Regulatory non-compliance |
| `hydrogen_incident` | Any hydrogen leak, venting, or explosion events? | REFER | 5 | Hydrogen safety |
| `warranty_dispute` | Any active warranty disputes with battery/electrolyser OEM? | FLAG | null | Warranty risk |
| `serial_defect` | Any known serial defect advisories on deployed cells or modules? | REFER | 5 | Fleet-wide risk |

### E.9: `energy_sme`

| ID | Question | Return=true Action | Override | Note |
|---|---|---|---|---|
| `major_incidents` | Any major incidents in past 5 years? *(inherited)* | REFER | 4 | Major incidents |
| `fatalities` | Any work-related fatalities in past 3 years? *(inherited)* | REFER | 3 | Fatalities |
| `regulatory_enforcement` | Any significant regulatory enforcement actions pending? *(inherited)* | REFER | 4 | Pending enforcement |
| `orphan_wells` | Any orphaned or idle well obligations on the operator's record? | FLAG | null | Environmental liability flag |

**Note:** SME uses only 4 direct queries (vs 6-7 for specialist configs) to support the automated underwriting model. Fewer questions = faster submission processing.

---

## Appendix F: Pricing Anchors & ILF Curves

### F.1: Pricing Anchor References

Each DECOUPLED configuration must specify `base_limit_reference` and `base_deductible_reference` — the limit/deductible combination at which the Tier 3 rate applies without ILF or deductible factor adjustment.

| Configuration | Limit Type | Base Limit Reference | Base Deductible Reference | Min Premium |
|---|---|---|---|---|
| `energy_general` | DECOUPLED | $10,000,000 | $50,000 | $100,000 |
| `energy_upstream_deepwater` | DECOUPLED | $25,000,000 | $250,000 | $250,000 |
| `energy_upstream_onshore` | DECOUPLED | $10,000,000 | $50,000 | $75,000 |
| `energy_upstream_unconventional` | DECOUPLED | $10,000,000 | $100,000 | $100,000 |
| `energy_midstream` | DECOUPLED | $10,000,000 | $100,000 | $100,000 |
| `energy_downstream` | DECOUPLED | $10,000,000 | $100,000 | $100,000 |
| `energy_offshore_wind` | DECOUPLED | $25,000,000 | $250,000 | $200,000 |
| `energy_onshore_renewable` | DECOUPLED | $10,000,000 | $50,000 | $50,000 |
| `energy_storage` | DECOUPLED | $10,000,000 | $100,000 | $75,000 |
| `energy_sme` | BUNDLED | Per package | Per package | $25,000 |

**Note on deepwater/offshore wind anchors:** The $25M base limit reflects minimum programme sizes. No underwriter writes a $5M deepwater or offshore wind programme. The $250K deductible matches typical programme structures for these segments.

### F.2: ILF Curves — `energy_upstream_deepwater`

Deepwater ILF curves are 30-40% steeper than `energy_general` for liability lines, reflecting the catastrophic tail. Property/BI curves remain flat (premium already scales with TIV).

**Control of Well (30% steeper than general):**

| Limit | Factor |
|---|---|
| $25,000,000 | 1.0 |
| $50,000,000 | 3.2 |
| $100,000,000 | 6.2 |
| $250,000,000 | 11.1 |
| $500,000,000 | 23.4 |
| $1,000,000,000 | 41.6 |

**Pollution Liability (40% steeper than general):**

| Limit | Factor |
|---|---|
| $25,000,000 | 1.0 |
| $50,000,000 | 3.6 |
| $100,000,000 | 7.0 |
| $250,000,000 | 12.6 |
| $500,000,000 | 26.6 |
| $1,000,000,000 | 47.6 |

**Deductible factors (deepwater):**

| Deductible | Factor |
|---|---|
| $100,000 | 1.25 |
| $250,000 | 1.0 |
| $500,000 | 0.92 |
| $1,000,000 | 0.85 |
| $2,500,000 | 0.75 |
| $5,000,000 | 0.65 |

### F.3: ILF Curves — `energy_downstream`

Downstream BI has a separate, steeper curve reflecting outsized BI exposure.

**Business Interruption (downstream-specific, 50% steeper than general BI):**

| Limit | Factor |
|---|---|
| $10,000,000 | 1.0 |
| $25,000,000 | 1.5 |
| $50,000,000 | 2.5 |
| $100,000,000 | 4.2 |
| $250,000,000 | 9.0 |
| $500,000,000 | 16.0 |
| $1,000,000,000 | 28.0 |

**Note:** All other product types for midstream, downstream, and renewable use curves derived from `energy_general` with segment-specific adjustments documented in the config.yaml implementation.

### F.4: Worked Example Corrections

The Phase 5 narrative worked examples use "rate-on-line" figures that already incorporate the TIV-to-limit relationship. To clarify:

- **Hess (deepwater T1):** $8.2B TIV × 0.0012 (T1 rate) = $9.84M base → ILF adjustment for $500M limit is implicit because property_damage ILF is flat (1.0) → deductible factor 0.92 for $5M deductible → safety modifier 0.85 → operator modifier 0.75 → geographic modifier 1.2 → **~$5.0M net** (consistent with narrative)
- **Enterprise Products (midstream T1):** $22B TIV × 0.0005 (T1 rate) = $11.0M → diversification modifier 0.85 → operator modifier 0.85 → **~$10.5M** (consistent)
- **Valero (downstream T1):** $38B TIV × 0.0010 (T1 rate) = $38.0M → diversification modifier 0.85 → operator modifier 0.90 → PSM excellence modifier 0.85 → **~$25.8M** (consistent)

The rates shown in the narrative are the applicable tier rates, not base rates requiring ILF adjustment. ILF applies only when the selected limit differs from what the rate-on-line price implies. For TIV-based property pricing, the limit/TIV ratio is the effective layer, and ILF is flat at 1.0.

---

## Appendix G: Routing Resolution

This appendix addresses routing edge cases and the `operation_segment` pre-routing mechanism.

### G.1: `operation_segment` as a Pre-Routing Field

**Resolution: Option 2 — Optional input field.**

Add `operation_segment` to `minimum_viable_input.optional` for all energy configurations. When provided by the submitter, it enables specific routing. When absent, submissions default to `energy_general`.

This mirrors how underwriters actually work — they usually know whether a submission is deepwater vs midstream before assessing the risk. The `operation_segment_basefunction` inference function still runs during signal execution (for scoring purposes), but routing uses the input value if provided.

**Updated routing logic:**

```
IF input.operation_segment IS PROVIDED:
    Route by specificity, using input.operation_segment for segment constraints
ELSE:
    Route to energy_general (specificity 1, catches all)

IF operation_segment constraint is met AND tiv constraint is met:
    Route to specific config
ELSE:
    Fallback to energy_general
```

### G.2: Small-Operator Routing Gap Closure

**Gap:** TIV < $50M AND employees > 500 matches neither `energy_sme` nor `energy_general`.

**Resolution:** Lower `energy_general`'s TIV threshold from $50M to $25M. This catches the rare case of a medium-sized energy company (by headcount) with low TIV. Companies with TIV < $25M and > 500 employees are not commercially viable energy insurance submissions — they are likely non-energy companies misrouted to the energy coverage.

**Updated routing constraints (twelve-configuration architecture):**

| Configuration | Specificity | Routing Constraints | Fallback |
|---|---|---|---|
| `energy_upstream_deepwater` | 4 | `operation_segment IN [UPSTREAM_OFFSHORE, UPSTREAM_DEEPWATER]` AND `tiv > 100000000` | `energy_general` |
| `energy_offshore_wind` | 4 | `operation_segment == RENEWABLE` AND `technology_type == OFFSHORE_WIND` | `energy_onshore_renewable` |
| `energy_upstream_unconventional` | 3 | `operation_segment == UPSTREAM_UNCONVENTIONAL` | `energy_upstream_onshore` |
| `energy_storage` | 3 | `operation_segment == RENEWABLE` AND `technology_type IN [BATTERY_STORAGE, HYDROGEN]` | `energy_onshore_renewable` |
| `energy_upstream_onshore` | 2 | `operation_segment == UPSTREAM_CONVENTIONAL` | `energy_general` |
| `energy_onshore_renewable` | 2 | `operation_segment == RENEWABLE` AND `technology_type IN [ONSHORE_WIND, UTILITY_SOLAR, DISTRIBUTED_SOLAR]` | `energy_general` |
| `energy_midstream` | 2 | `operation_segment IN [MIDSTREAM_PIPELINE, MIDSTREAM_PROCESSING, MIDSTREAM_STORAGE]` | `energy_general` |
| `energy_downstream` | 2 | `operation_segment IN [DOWNSTREAM_REFINING, DOWNSTREAM_PETROCHEMICAL]` | `energy_general` |
| `energy_sme` | 2 | `tiv <= 100000000` AND `employee_count <= 500` | `energy_general` |
| `energy_general` | 1 | `tiv > 25000000` *(lowered from 50M)* | — |

### G.2.1: Renewable Technology-Type Routing

The renewable segment introduces a secondary routing dimension: `technology_type`. When `operation_segment == RENEWABLE`, the multiplexer evaluates `technology_type` to route to the most specific renewable configuration:

```
IF operation_segment == RENEWABLE:
    IF technology_type == OFFSHORE_WIND:
        → energy_offshore_wind (specificity 4)
    ELIF technology_type IN [BATTERY_STORAGE, HYDROGEN]:
        → energy_storage (specificity 3)
    ELIF technology_type IN [ONSHORE_WIND, UTILITY_SOLAR, DISTRIBUTED_SOLAR]:
        → energy_onshore_renewable (specificity 2)
    ELSE:
        → energy_general (fallback)
```

`technology_type` is required for all renewable submissions. When absent, the submission routes to `energy_general` rather than guessing the technology — an offshore wind farm priced as onshore solar would be worse than a general energy price.

### G.3: Specificity Tie-Breaking Acknowledgement

When a submission matches both a segment config (e.g., `energy_midstream`) and `energy_sme` at the same specificity level (2), the multiplexer breaks the tie by:

1. **Signal completeness** — the segment config will have higher completeness for a segment-specific signal set
2. **Commercial value** — the segment config produces more accurate pricing

**Deliberate design decision:** A pipeline company should be priced as a pipeline company, not as a generic SME. The multiplexer's existing tie-breaking logic produces the correct behavior without modification.

### G.4: Deepwater TIV Floor vs SME

**Acknowledged:** A deepwater operation at $100M TIV routes to `energy_sme` rather than `energy_upstream_deepwater`. This is acceptable because:

- True deepwater operations (FPSOs, drillships, subsea completions) virtually never have TIV < $100M — a single FPSO costs $1-3B
- A $100M "deepwater" operation is likely a shelf operation that should be priced as SME or general
- If `operation_segment == UPSTREAM_DEEPWATER` is provided as input (per G.1), it routes to deepwater regardless of TIV because the segment constraint at specificity 4 is evaluated before the SME TIV constraint at specificity 2

---

## Appendix H: Minimum Viable Input per Configuration

### H.1: `energy_upstream_deepwater`

```yaml
minimum_viable_input:
  required:
    - field: client_name
      description: Client name (domain optional for discovery)
    - field: product_type
      description: "One of: property_damage, business_interruption, control_of_well, operators_extra_expense, third_party_liability, pollution_liability, removal_of_wreck"
    - field: limit
      description: Requested limit in USD (minimum $25,000,000)
    - field: tiv
      description: Total Insured Value in USD
    - field: water_depth
      description: Maximum water depth in feet for operated assets
  optional:
    - field: operation_segment
      description: "UPSTREAM_OFFSHORE or UPSTREAM_DEEPWATER (enables routing)"
    - field: rig_contractor
      description: Primary drilling contractor name
    - field: num_platforms
      description: Number of operated platforms/FPSOs
```

### H.2: `energy_upstream_onshore`

```yaml
minimum_viable_input:
  required:
    - field: client_name
      description: Client name (domain optional for discovery)
    - field: product_type
      description: "One of: property_damage, business_interruption, control_of_well, operators_extra_expense, third_party_liability, pollution_liability"
    - field: limit
      description: Requested limit in USD
    - field: tiv
      description: Total Insured Value in USD
  optional:
    - field: operation_segment
      description: "UPSTREAM_CONVENTIONAL (enables routing)"
    - field: well_count
      description: Number of active operated wells
    - field: basin
      description: "Primary basin: PERMIAN, EAGLE_FORD, BAKKEN, DJ_NIOBRARA, APPALACHIAN, ANADARKO, WILLISTON, OTHER"
    - field: production_boed
      description: Daily production in barrels of oil equivalent
```

### H.3: `energy_upstream_unconventional`

```yaml
minimum_viable_input:
  required:
    - field: client_name
      description: Client name (domain optional for discovery)
    - field: product_type
      description: "One of: property_damage, business_interruption, control_of_well, operators_extra_expense, third_party_liability, pollution_liability"
    - field: limit
      description: Requested limit in USD
    - field: tiv
      description: Total Insured Value in USD
  optional:
    - field: operation_segment
      description: "UPSTREAM_UNCONVENTIONAL (enables routing)"
    - field: well_count
      description: Number of active operated wells (including horizontal wells)
    - field: basin
      description: "Primary basin: PERMIAN, EAGLE_FORD, BAKKEN, DJ_NIOBRARA, HAYNESVILLE, MARCELLUS, UTICA, OTHER"
    - field: frack_stage_count
      description: Average frac stages per lateral (indicator of completion intensity)
    - field: produced_water_disposal
      description: "Disposal method: SWD_WELL, RECYCLING, EVAPORATION, OFFSITE"
```

### H.4: `energy_midstream`

```yaml
minimum_viable_input:
  required:
    - field: client_name
    - field: product_type
      description: "One of: property_damage, business_interruption, third_party_liability, pollution_liability"
    - field: limit
      description: Requested limit in USD
    - field: tiv
      description: Total Insured Value in USD
  optional:
    - field: operation_segment
      description: "MIDSTREAM_PIPELINE, MIDSTREAM_PROCESSING, or MIDSTREAM_STORAGE"
    - field: pipeline_miles
      description: Total operated pipeline miles
    - field: commodity_type
      description: "Primary commodity: CRUDE, NGL, NATURAL_GAS, REFINED_PRODUCTS"
```

### H.5: `energy_downstream`

```yaml
minimum_viable_input:
  required:
    - field: client_name
    - field: product_type
      description: "One of: property_damage, business_interruption, third_party_liability, pollution_liability"
    - field: limit
      description: Requested limit in USD
    - field: tiv
      description: Total Insured Value in USD
  optional:
    - field: operation_segment
      description: "DOWNSTREAM_REFINING or DOWNSTREAM_PETROCHEMICAL"
    - field: refinery_count
      description: Number of operated refineries
    - field: total_throughput_bpd
      description: Total refining throughput in barrels per day
```

### H.6: `energy_offshore_wind`

```yaml
minimum_viable_input:
  required:
    - field: client_name
      description: Client name (domain optional for discovery)
    - field: product_type
      description: "One of: property_damage, business_interruption, third_party_liability, delay_in_start_up, construction_all_risks"
    - field: limit
      description: Requested limit in USD (minimum $25,000,000)
    - field: tiv
      description: Total Insured Value (project value including construction cost) in USD
    - field: technology_type
      description: "OFFSHORE_WIND (required for routing)"
  optional:
    - field: operation_segment
      description: "RENEWABLE (enables routing)"
    - field: construction_phase
      description: "PRE_CONSTRUCTION, CONSTRUCTION, COMMISSIONING, EARLY_OPERATION, MATURE_OPERATION"
    - field: capacity_mw
      description: Total nameplate capacity in MW
    - field: foundation_type
      description: "MONOPILE, JACKET, GRAVITY_BASE, FLOATING_SPAR, FLOATING_SEMI, FLOATING_TLP"
    - field: epc_contractor
      description: EPC contractor name
    - field: turbine_oem
      description: Turbine manufacturer (Vestas, Siemens Gamesa, GE, etc.)
    - field: water_depth
      description: Maximum water depth in metres for array area
```

### H.7: `energy_onshore_renewable`

```yaml
minimum_viable_input:
  required:
    - field: client_name
      description: Client name (domain optional for discovery)
    - field: product_type
      description: "One of: property_damage, business_interruption, third_party_liability, delay_in_start_up"
    - field: limit
      description: Requested limit in USD
    - field: tiv
      description: Total Insured Value (project value) in USD
    - field: technology_type
      description: "One of: ONSHORE_WIND, UTILITY_SOLAR, DISTRIBUTED_SOLAR"
  optional:
    - field: operation_segment
      description: "RENEWABLE (enables routing)"
    - field: construction_phase
      description: "PRE_CONSTRUCTION, CONSTRUCTION, COMMISSIONING, EARLY_OPERATION, MATURE_OPERATION"
    - field: capacity_mw
      description: Total nameplate capacity in MW
    - field: epc_contractor
      description: EPC contractor name
    - field: panel_or_turbine_oem
      description: Primary equipment manufacturer
```

### H.8: `energy_storage`

```yaml
minimum_viable_input:
  required:
    - field: client_name
      description: Client name (domain optional for discovery)
    - field: product_type
      description: "One of: property_damage, business_interruption, third_party_liability, delay_in_start_up"
    - field: limit
      description: Requested limit in USD
    - field: tiv
      description: Total Insured Value (project value) in USD
    - field: technology_type
      description: "One of: BATTERY_STORAGE, HYDROGEN"
  optional:
    - field: operation_segment
      description: "RENEWABLE (enables routing)"
    - field: construction_phase
      description: "PRE_CONSTRUCTION, CONSTRUCTION, COMMISSIONING, EARLY_OPERATION, MATURE_OPERATION"
    - field: capacity_mwh
      description: Total storage capacity in MWh (for battery) or kg/day (for hydrogen)
    - field: battery_chemistry
      description: "LFP, NMC, NCA, FLOW, SOLID_STATE (battery only)"
    - field: cell_manufacturer
      description: Battery cell manufacturer (CATL, BYD, LG, Samsung SDI, etc.)
    - field: bms_provider
      description: Battery Management System provider
```

### H.9: `energy_sme`

```yaml
minimum_viable_input:
  required:
    - field: client_name
    - field: product_type
      description: "One of: combined_property_liability, pollution_liability"
    - field: tiv
      description: Total Insured Value in USD (maximum $500,000,000 for SME)
  optional:
    - field: operation_segment
      description: "Any valid operation segment"
    - field: employee_count
      description: Number of employees (used for routing — must be <= 500)
    - field: package
      description: "STARTER, STANDARD, ENHANCED, PREMIUM, or ENTERPRISE"
```

**Note:** `energy_sme` does not require `limit` as a separate field — limit is determined by the selected BUNDLED package. If `package` is not provided, it is inferred from TIV using the package-to-TIV mapping in the pricing philosophy section.

---

## Appendix I: Seed Data Plan

Each new configuration requires seed entries at minimum Tier 1, 3, and 5 to support demo, integration testing, and multiplexer routing validation. The following plan uses the example companies already profiled in the Phase 5 narrative, supplemented by representative composites for new segments.

| Configuration | Tier 1 | Tier 3 | Tier 5 |
|---|---|---|---|
| `energy_upstream_deepwater` | Hess Corporation | Murphy Oil | Vaalco Energy |
| `energy_upstream_onshore` | ConocoPhillips (Permian conventional) | Callon Petroleum | Distressed Permian Conventional (composite) |
| `energy_upstream_unconventional` | Pioneer Natural Resources | Laredo Petroleum | Distressed Shale Operator (composite) |
| `energy_midstream` | Enterprise Products Partners | Genesis Energy | Distressed Gathering System (composite) |
| `energy_downstream` | Valero Energy | PBF Energy | Philadelphia Energy Solutions |
| `energy_offshore_wind` | Orsted A/S (Hornsea) | Vineyard Wind (composite) | Startup Floating Wind (composite) |
| `energy_onshore_renewable` | NextEra Energy Resources | Mid-Scale Wind Developer (composite) | Early-Stage Solar Developer (composite) |
| `energy_storage` | Fluence Energy (utility BESS) | Mid-Scale Battery Project (composite) | Early-Stage Hydrogen Pilot (composite) |
| `energy_sme` | Diamondback Energy (pre-scale) | Small Appalachian Gas Producer | Distressed Permian Operator |

**Total new seed entries: 27** (3 per configuration × 9 configurations, plus 2 additional Tier 2/4 entries per config where narrative examples exist).

**Extended seed entries (Tier 2 and 4 where profiled):**

| Configuration | Tier 2 | Tier 4 |
|---|---|---|
| `energy_upstream_deepwater` | Kosmos Energy | — |
| `energy_upstream_onshore` | — | Marginal Stripper Well Operator (composite) |
| `energy_upstream_unconventional` | Matador Resources | — |
| `energy_midstream` | ONEOK, Inc. | — |
| `energy_downstream` | — | CVR Energy |
| `energy_offshore_wind` | — | Startup Offshore Wind (composite) |
| `energy_onshore_renewable` | — | Distressed Community Solar (composite) |
| `energy_storage` | — | Distressed BESS Retrofit (composite) |
| `energy_sme` | — | Marginal SME Operator (composite) |

Each seed entry will follow the established format:

```python
{
    "entity_name": "...",
    "domain": "...",
    "ticker": "...",
    "coverage": "energy",
    "configuration": "energy_upstream_deepwater",  # per config
    "tier": 1,
    "decision": "approve",
    "premium": ...,
    "revenue": ...,
    "industry": "...",
    "size_band": "...",
    "geography": "...",
    "description": "...",
    "signal_profile": "energy_deepwater_excellent",  # new profile per config
    "product_type": "...",
    "limit": ...,
    "deductible": ...,
    "tiv": ...,
}
```

New signal profiles to create (3 per configuration, 27 total):
- `energy_deepwater_excellent`, `energy_deepwater_elevated`, `energy_deepwater_catastrophic`
- `energy_upstream_onshore_excellent`, `energy_upstream_onshore_standard`, `energy_upstream_onshore_distressed`
- `energy_unconventional_excellent`, `energy_unconventional_elevated`, `energy_unconventional_distressed`
- `energy_midstream_excellent`, `energy_midstream_good`, `energy_midstream_elevated`
- `energy_downstream_excellent`, `energy_downstream_elevated`, `energy_downstream_catastrophic`
- `energy_offshore_wind_excellent`, `energy_offshore_wind_standard`, `energy_offshore_wind_elevated`
- `energy_onshore_renewable_excellent`, `energy_onshore_renewable_standard`, `energy_onshore_renewable_elevated`
- `energy_storage_excellent`, `energy_storage_standard`, `energy_storage_elevated`
- `energy_sme_excellent`, `energy_sme_elevated`, `energy_sme_catastrophic`

### I.1: Seed Data Validation Requirements

Each seed entry must pass the following validation checks before inclusion in `seed_dsi_bench.py`:

1. **Routing validation** — The seed's `operation_segment` and `technology_type` (where applicable) must route to the correct configuration via the multiplexer
2. **Tier consistency** — The seed's signal profile must produce a DSI score within the expected tier band for that configuration (per Appendix C)
3. **Pricing consistency** — The seed's premium must be within 20% of the pricing anchor × modifier calculation for its tier
4. **Weight verification** — The signal profile's group scores, when weighted by the configuration's three-layer weights (per Appendix B), must produce the expected overall score
5. **Product type validity** — The seed's `product_type` must be in the configuration's allowed product types

### I.2: `seed_dsi_bench.py` Expansion Plan

The seed script will be expanded to accommodate all twelve energy configurations:

```
Current state:  energy_general only (existing)
Phase 5 adds:   11 new configurations × 3-5 seed entries each = 33-55 new entries
Total energy:   ~40-60 seed entries across 12 configurations
```

**Implementation approach:**
- Group seed entries by configuration in the script
- Each configuration block includes a comment referencing the narrative example it represents
- Signal profiles are defined in a separate `ENERGY_SIGNAL_PROFILES` dictionary
- Routing validation tests are added as assertions at the end of the script to verify each seed routes to its intended configuration

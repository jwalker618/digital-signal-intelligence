# Phase 5: Energy Coverage Expansion — Full Spectrum Configuration Suite

## Context & Motivation

Energy is the most complex coverage class in commercial insurance. Unlike cyber (where risk is fundamentally digital) or D&O (where risk is fundamentally governance), energy risk spans *physical*, *environmental*, *geopolitical*, *financial*, and *transitional* dimensions simultaneously. A deepwater drilling platform in the Gulf of Mexico shares almost nothing — actuarially, operationally, or legally — with a utility-scale solar farm in West Texas or a pipeline network crossing three US states.

Yet today, DSI has a single `energy_general` configuration attempting to price all of it.

Every other coverage in the platform (cyber, D&O, PI, FI, aerospace, marine) already has at least two configurations — a `_general` corporate model and an `_sme` automated model. Energy has neither the segment specificity nor the market breadth to demonstrate what DSI can actually do.

This phase corrects that. We will build **five new configurations** that, together with the existing `energy_general`, form a complete underwriting toolkit for the global energy market. Each configuration is purpose-built for a distinct segment of the energy value chain, with its own signal architecture, pricing philosophy, and underwriting logic.

### Why This Matters for Production & Demo

1. **Production Pipeline Readiness**: Energy configurations will be among the first to face real submission data. The `energy_general` model is too broad to produce credible pricing for specialist segments. A deepwater operator should not be priced with the same signal weights as a pipeline company.

2. **Demo Credibility**: When demonstrating DSI to energy underwriters, Lloyd's syndicates, or reinsurers, the system must show that it *understands* the difference between upstream, midstream, and downstream. A single configuration cannot do this. An underwriter who sees "Operator Type: SUPERMAJOR, applied: 0.75" as a flat modifier will immediately question whether the system understands the nuance.

3. **Multiplexer Demonstration**: The V4 multiplexer routes submissions to the most specific applicable configuration. With six energy configurations at varying `model_specificity` levels, energy becomes the definitive showcase for intelligent routing.

---

## The Six-Configuration Architecture

```
energy/
├── energy_general              (exists)    specificity=1   Universal fallback
├── energy_upstream_deepwater   (new)       specificity=3   Offshore/deepwater E&P
├── energy_midstream            (new)       specificity=2   Pipeline, processing, storage
├── energy_downstream           (new)       specificity=2   Refining & petrochemical
├── energy_renewable            (new)       specificity=3   Wind, solar, battery, hydrogen
└── energy_sme                  (new)       specificity=2   Small operators, BUNDLED pricing
```

### Routing Logic

The multiplexer evaluates routing constraints in descending specificity order. The first configuration whose constraints are satisfied wins.

| Configuration | Specificity | Routing Constraints | Fallback |
|---|---|---|---|
| `energy_upstream_deepwater` | 3 | `operation_segment IN [UPSTREAM_OFFSHORE, UPSTREAM_DEEPWATER]` AND `tiv > 100000000` | `energy_general` |
| `energy_renewable` | 3 | `operation_segment == RENEWABLE` | `energy_general` |
| `energy_midstream` | 2 | `operation_segment IN [MIDSTREAM_PIPELINE, MIDSTREAM_PROCESSING, MIDSTREAM_STORAGE]` | `energy_general` |
| `energy_downstream` | 2 | `operation_segment IN [DOWNSTREAM_REFINING, DOWNSTREAM_PETROCHEMICAL]` | `energy_general` |
| `energy_sme` | 2 | `tiv <= 100000000` AND `employee_count <= 500` | `energy_general` |
| `energy_general` | 1 | `tiv > 50000000` (existing) | — |

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

## Configuration 2: `energy_midstream`

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

## Configuration 3: `energy_downstream`

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

## Configuration 4: `energy_renewable`

### The Underwriting Reality

Renewable energy is the fastest-growing segment in energy insurance — and the least understood. Traditional energy underwriters know how to price a refinery. They do not know how to price an offshore wind farm, a 500MW battery energy storage system, or a green hydrogen electrolyser.

The risk profile is fundamentally different:

- **No hydrocarbon exposure.** Pollution liability is near-zero. Control of well is irrelevant. The entire environmental compliance signal group from `energy_general` must be replaced.
- **Construction risk dominates.** Most renewable projects are in construction or early operation. The loss distribution is front-loaded — the first 3 years carry 70% of the lifetime risk.
- **Technology risk is real.** Battery thermal runaway, blade delamination, inverter failure — these are *technology* failures, not *operational* failures. The signal architecture must assess technology maturity.
- **Weather is the exposure driver.** NatCat (hurricanes for offshore wind, hail for solar, wildfire for transmission) replaces operational complexity as the primary exposure dimension.

This configuration is strategically important because it demonstrates that DSI's signal architecture is not limited to hydrocarbon risk — it can adapt to entirely new risk paradigms.

### Signal Architecture Rationale

**Primary driver: Asset Portfolio (Risk: 0.25, Loss: 0.20, Exposure: 0.35 = 0.80 combined)**

For renewables, the asset itself IS the risk. Technology selection (which turbine platform, which battery chemistry, which inverter technology), installation quality, and equipment warranty coverage are the primary underwriting considerations.

**Secondary driver: Operational Telemetry (Risk: 0.20, Loss: 0.20, Exposure: 0.25 = 0.65 combined)**

SCADA data from wind turbines and solar plants is rich and predictive. Availability factors, degradation curves, and curtailment patterns reveal operational quality in near-real-time.

**Replaced groups:**
- `environmental_compliance` → `construction_quality` (new group): Environmental signals are irrelevant. Construction phase risk (EPC contractor quality, commissioning defects) is the primary loss driver.
- `safety_performance` weight reduced to 0.25 combined: Human safety risk is lower (no drilling, no high-pressure hydrocarbons), though still present (offshore wind has real fall-from-height and vessel collision exposure).

### New Signals (Not in `energy_general`)

| Signal | Proxy Tier | Group | Rationale |
|---|---|---|---|
| `technology_maturity` | INFERRED_PROXY | asset_portfolio | Technology readiness level of the primary generation technology. First-of-a-kind risk vs proven platform. |
| `epc_contractor_quality` | INFERRED_PROXY | construction_quality | EPC contractor track record. A Tier 1 contractor (Orsted/Siemens partnership) vs unknown developer. |
| `warranty_coverage` | DIRECT_OBSERVABLE | asset_portfolio | OEM warranty scope and duration. Full-service vs basic warranty fundamentally changes the risk transfer. |
| `capacity_factor` | DIRECT_OBSERVABLE | operational_telemetry | Actual vs predicted capacity factor. The best single metric for operational performance. |
| `natcat_exposure` | DIRECT_OBSERVABLE | asset_portfolio | Natural catastrophe exposure score based on location. Hurricane, hail, wildfire, flood. |
| `grid_interconnection` | INFERRED_PROXY | operational_telemetry | Grid connection status and curtailment history. Curtailment = revenue loss = BI exposure. |
| `ppa_quality` | INFERRED_PROXY | financial_stability | Power Purchase Agreement counterparty quality and tenor. Revenue certainty drives financial stability. |
| `degradation_rate` | DIRECT_OBSERVABLE | operational_telemetry | Panel/turbine degradation rate vs manufacturer curve. Early degradation signals manufacturing defects. |

### Pricing Philosophy

- **Basis**: TIV (project value including construction cost)
- **Method**: MULTIPLIER on TIV
- **Key difference**: Tier 3 rate of **0.0015** (0.15%). Lower than hydrocarbon energy because severity tail is thinner (no blowout, no explosion), but higher than midstream because technology risk and NatCat add uncertainty.
- **Product types**: `property_damage`, `business_interruption`, `third_party_liability` (no pollution, no control_of_well, no removal_of_wreck)
- **New product type**: `delay_in_start_up` — unique to construction/early-operation renewable projects
- **Limit Configuration**: DECOUPLED but with project-finance-friendly limit structures

### Example Company Returns

**Tier 1 — PREFERRED:**
> **Orsted A/S** — World's largest offshore wind developer
> - TIV: $28B (global offshore wind portfolio) | Limit: $750M | Score: 889
> - Why: Proven technology (Siemens Gamesa 8MW+), 25+ years offshore wind experience, zero construction-phase total losses, investment-grade credit, best-in-class SCADA/predictive maintenance, long-term PPAs with sovereign/utility counterparties
> - Premium: **~$16.8M** after modifiers (operator type: 0.70 for industry leader)

**Tier 2 — STANDARD PLUS:**
> **NextEra Energy Resources** — Largest US wind & solar operator
> - TIV: $45B (combined onshore wind + utility solar) | Limit: $500M | Score: 761
> - Why: Massive, diversified portfolio reduces concentration, proven operational track record, strong financials (NextEra parent is investment grade), some hail exposure in Texas solar portfolio, NatCat exposure in Florida operations
> - Premium: **~$24.3M** with geographic diversification modifier

**Tier 4 — SUBSTANDARD:**
> **Startup Offshore Wind Developer** (composite profile)
> - TIV: $3.2B (single project, first development) | Limit: $250M | Score: 389
> - Why: First-of-kind developer (no track record), unproven EPC contractor, single-asset concentration (100%), floating wind technology (immature), construction phase, limited financial track record, PPA not yet finalised
> - Referral reasons: `technology_maturity <= 30`, `epc_contractor_quality <= 35`, `concentration <= 20`

---

## Configuration 5: `energy_sme`

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
| 1 | `energy_upstream_deepwater` config.yaml | Deepwater/offshore E&P configuration with 50+ signals |
| 2 | `energy_midstream` config.yaml | Pipeline/processing/storage configuration |
| 3 | `energy_downstream` config.yaml | Refining & petrochemical configuration |
| 4 | `energy_renewable` config.yaml | Wind, solar, battery, hydrogen configuration |
| 5 | `energy_sme` config.yaml | Small operator BUNDLED configuration |
| 6 | Updated `energy/config.yaml` | All 6 configurations in a single file (per convention) |
| 7 | Updated `logic.md` | Auto-generated documentation for all 6 models |
| 8 | Narrative documentation | This phase document serves as the detailed narrative |
| 9 | Seed data updates | Example companies for each configuration in `seed_dsi_bench.py` |

---

## Appendix: Why These Five Configurations Cover Energy "In All Its Glory"

The energy value chain is a pipeline (metaphorically and literally):

```
EXPLORATION → PRODUCTION → GATHERING → PROCESSING → TRANSPORTATION → REFINING → DISTRIBUTION
     ↑              ↑            ↑            ↑              ↑              ↑           ↑
     └──────────────┴────────────┘            └──────────────┘              └───────────┘
           UPSTREAM                              MIDSTREAM                   DOWNSTREAM
           (energy_upstream_deepwater)           (energy_midstream)         (energy_downstream)
           (energy_general for onshore)
```

And orthogonal to this chain:
```
RENEWABLES (energy_renewable) — entirely separate technology, risk profile, and regulatory regime
SME (energy_sme) — cross-cutting segment based on size, not value chain position
```

Together, these six configurations can price:
- A $50B supermajor's global programme (routed to `energy_general` or specific segment configs)
- A $500M deepwater explorer in Guyana (routed to `energy_upstream_deepwater`)
- A $15B pipeline MLP (routed to `energy_midstream`)
- A $20B independent refiner (routed to `energy_downstream`)
- A $3B offshore wind developer (routed to `energy_renewable`)
- A $60M Permian Basin operator (routed to `energy_sme`)

No commercially relevant energy submission falls outside this matrix. That is the definition of covering the coverage "in all its glory."

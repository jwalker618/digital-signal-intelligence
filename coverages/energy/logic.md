# DSI Logic Document: `ENERGY`
*Generated: 2026-05-14*

## DSI Foundational Principles Adherence
This configuration is validated against the DSI Whitepaper & Vision Paper:
- **Objective Observation:** Signals derived from verifiable digital footprints, avoiding subjective interpretation.
- **Three-Layer Engine:** Modifiers explicitly target Risk, Loss, and Exposure dimensions.
- **Phase 5 Anchoring:** Polymorphic pricing limits scale from mathematically absolute anchor points.

## The Three-Layer Assessment Engine
Every DSI model scores a risk across three independent pillars before any premium is calculated. Each pillar answers a distinct underwriting question and enters the pricing formula at a different point:

- **Risk** — *How likely is this account to behave badly?* Signal evidence is aggregated into a quality score that maps to an underwriting action (approve / refer / decline) and selects the base rate applied to the exposure basis.
- **Loss** — *If a loss occurs, how often and how severe?* Scored separately into frequency and severity modifiers, letting the model distinguish attritional-loss accounts from low-frequency / high-severity ones.
- **Exposure** — *How much value is at stake?* Scales premium to the size of the insured object, independent of risk quality.

Within each pillar, signals are organised into groups (e.g. Construction Quality, Occupancy Risk). The weight tables show how much each group contributes to each pillar; the signal detail tables show how each individual signal informs them. Critically, a single signal can carry very different weight across the three pillars — highly predictive of loss severity, say, yet barely moving the exposure score.

---

## Model: `energy_general`
*Energy property and liability coverage based on observable safety, environmental, and operational signals*

### Routing Protocol (Multiplexer)
- `tiv > 25000000`

### Three-Layer Weight Distribution
> *DSI requires that weights for Risk, Loss, and Exposure each sum to 1.0 across all signal groups.*

**Validation:** PASS

| Group | Risk | Loss | Exposure |
|-------|------|------|----------|
| Network Authority | 0.10 | 0.05 | 0.05 |
| Safety Performance | 0.50 | 0.60 | 0.20 |
| Operational Telemetry | 0.10 | 0.10 | 0.20 |
| Financial Stability | 0.10 | 0.05 | 0.20 |
| Asset Portfolio | 0.15 | 0.18 | 0.33 |
| Structured Data | 0.05 | 0.02 | 0.02 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

**Group Definitions:**
- **Network Authority:** Quality of partnerships, contractors, and industry relationships
- **Safety Performance:** OSHA metrics, incidents, process safety events
- **Operational Telemetry:** Production patterns, facility activity, maintenance signals
- **Financial Stability:** Credit rating, leverage, ARO coverage, capex trends
- **Asset Portfolio:** Asset age, concentration, complexity, permit status
- **Structured Data:** Third-party ESG ratings and industry benchmarks

*Reading the table: a group's three weights are independent. The same group can be a dominant driver of one pillar and a minor input to another — e.g. a group may carry most of the Exposure weight while contributing little to Risk.*

### Signal Architecture Rationale
This configuration contains **49 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `DIRECT_OBSERVABLE` (22 signals): Highest confidence
- `INFERRED_PROXY` (26 signals): Medium confidence
- `COHORT_INFERENCE` (1 signals): Lowest confidence

**Signal Count by Group:**
- `public_record`: 13 signals
- `corporate_footprint`: 11 signals
- `network_authority`: 7 signals
- `technical_infrastructure`: 5 signals
- `behavioural`: 5 signals
- `structured_data`: 5 signals
- `operator_type`: 1 signals
- `operation_segment`: 1 signals
- `geographic_focus`: 1 signals

**Selection Rationale:**
- 45% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Detail by Group
> *Each signal is an objectively observable data point. The weights show how strongly that signal informs each assessment pillar; correlation direction indicates whether a higher observed value increases (+) or decreases (-) the assessed exposure.*

#### Network Authority
*Quality of partnerships, contractors, and industry relationships*

| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `partner_quality` | INFERRED_PROXY | 0.20 | 0.10 / 0.15 | 0.00 | + |
| `contractor_quality` | INFERRED_PROXY | 0.15 | 0.15 / 0.00 | 0.00 | + |
| `banking_relationship` | INFERRED_PROXY | 0.15 | 0.00 / 0.10 | 0.00 | + |
| `insurance_history` | INFERRED_PROXY | 0.15 | 0.15 / 0.10 | 0.00 | + |
| `industry_association` | DIRECT_OBSERVABLE | 0.10 | 0.00 / 0.00 | 0.00 | + |
| `regulator_relationship` | INFERRED_PROXY | 0.15 | 0.10 / 0.00 | 0.00 | + |
| `customer_quality` | INFERRED_PROXY | 0.10 | 0.00 / 0.00 | 0.10 | + |

#### Safety Performance
*OSHA metrics, incidents, process safety events*

| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `osha_trir` | DIRECT_OBSERVABLE | 0.20 | 0.25 / 0.15 | 0.00 | + |
| `osha_violations` | DIRECT_OBSERVABLE | 0.15 | 0.20 / 0.15 | 0.00 | + |
| `bsee_incident` | DIRECT_OBSERVABLE | 0.10 | 0.15 / 0.20 | 0.00 | + |
| `process_safety` | INFERRED_PROXY | 0.20 | 0.25 / 0.30 | 0.00 | + |
| `fatality` | DIRECT_OBSERVABLE | 0.15 | 0.10 / 0.35 | 0.00 | + |
| `major_incident` | DIRECT_OBSERVABLE | 0.15 | 0.20 / 0.40 | 0.25 | + |
| `near_miss` | INFERRED_PROXY | 0.05 | 0.10 / 0.00 | 0.00 | + |
| `epa_violation` | DIRECT_OBSERVABLE | 0.20 | 0.20 / 0.25 | 0.00 | + |
| `spill_history` | DIRECT_OBSERVABLE | 0.25 | 0.25 / 0.35 | 0.35 | + |
| `emissions_compliance` | DIRECT_OBSERVABLE | 0.15 | 0.15 / 0.00 | 0.00 | + |
| `flaring` | DIRECT_OBSERVABLE | 0.15 | 0.10 / 0.00 | 0.00 | - |
| `methane` | DIRECT_OBSERVABLE | 0.15 | 0.10 / 0.10 | 0.00 | - |
| `remediation` | INFERRED_PROXY | 0.10 | 0.00 / 0.15 | 0.00 | + |

#### Operational Telemetry
*Production patterns, facility activity, maintenance signals*

| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `production_consistency` | INFERRED_PROXY | 0.20 | 0.15 / 0.00 | 0.10 | + |
| `facility_activity` | INFERRED_PROXY | 0.20 | 0.10 / 0.00 | 0.00 | + |
| `well_integrity` | INFERRED_PROXY | 0.20 | 0.20 / 0.25 | 0.00 | + |
| `maintenance_pattern` | INFERRED_PROXY | 0.20 | 0.15 / 0.00 | 0.00 | + |
| `operational_efficiency` | INFERRED_PROXY | 0.20 | 0.00 / 0.00 | 0.10 | + |

#### Financial Stability
*Credit rating, leverage, ARO coverage, capex trends*

| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `credit_rating` | DIRECT_OBSERVABLE | 0.25 | 0.00 / 0.20 | 0.00 | + |
| `leverage` | DIRECT_OBSERVABLE | 0.20 | 0.00 / 0.15 | 0.00 | - |
| `aro_coverage` | INFERRED_PROXY | 0.20 | 0.00 / 0.15 | 0.10 | + |
| `capex_trend` | DIRECT_OBSERVABLE | 0.20 | 0.00 / 0.00 | 0.10 | + |
| `restructuring` | DIRECT_OBSERVABLE | 0.15 | 0.00 / 0.25 | 0.00 | + |

#### Asset Portfolio
*Asset age, concentration, complexity, permit status*

| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `asset_age` | INFERRED_PROXY | 0.25 | 0.20 / 0.15 | 0.15 | - |
| `concentration` | INFERRED_PROXY | 0.20 | 0.00 / 0.25 | 0.15 | - |
| `complexity` | INFERRED_PROXY | 0.20 | 0.15 / 0.20 | 0.25 | - |
| `decommissioning` | INFERRED_PROXY | 0.20 | 0.00 / 0.15 | 0.15 | + |
| `permit_status` | DIRECT_OBSERVABLE | 0.15 | 0.00 / 0.00 | 0.00 | + |
| `safety_communication` | DIRECT_OBSERVABLE | 0.20 | 0.10 / 0.00 | 0.00 | + |
| `esg_reporting` | DIRECT_OBSERVABLE | 0.20 | 0.00 / 0.00 | 0.00 | + |
| `technical_hiring` | INFERRED_PROXY | 0.15 | 0.00 / 0.00 | 0.10 | + |
| `industry_presence` | DIRECT_OBSERVABLE | 0.15 | 0.00 / 0.00 | 0.00 | + |
| `disclosure_quality` | INFERRED_PROXY | 0.15 | 0.00 / 0.00 | 0.00 | + |
| `hse_leadership` | INFERRED_PROXY | 0.15 | 0.10 / 0.00 | 0.00 | + |

#### Structured Data
*Third-party ESG ratings and industry benchmarks*

| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `esg_rating` | DIRECT_OBSERVABLE | 0.40 | 0.00 / 0.00 | 0.00 | + |
| `benchmark` | COHORT_INFERENCE | 0.35 | 0.15 / 0.15 | 0.00 | + |
| `credit` | DIRECT_OBSERVABLE | 0.25 | 0.00 / 0.20 | 0.00 | + |
| `electrolyser_technology_maturity` | INFERRED_PROXY | 0.03 | 0.03 / 0.00 | 0.00 | - |
| `offtake_counterparty_quality` | DIRECT_OBSERVABLE | 0.03 | 0.00 / 0.03 | 0.00 | - |

#### operator_type
**Categorical signal `operator_type`** — proxy tier: `INFERRED_PROXY`, source: `metadata.operator_type`

| Category | Label | Applied Factor |
|----------|-------|----------------|
| `SUPERMAJOR` | Supermajor | 0.75 |
| `MAJOR_INTEGRATED` | Major Integrated | 0.85 |
| `LARGE_INDEPENDENT` | Large Independent | 0.95 |
| `MID_INDEPENDENT` | Mid-Size Independent | 1.0 |
| `SMALL_INDEPENDENT` | Small Independent | 1.2 |
| `NATIONAL_OIL` | National Oil Company | 0.9 |
| `MIDSTREAM_MAJOR` | Major Midstream | 0.85 |
| `DOWNSTREAM_MAJOR` | Major Downstream | 0.9 |
| `PRIVATE_EQUITY` | Private Equity Backed | 1.15 |
| `UNKNOWN` | Unknown/New Operator | 1.4 |
| `OTHER` | UNKNOWN | 1.0 |

#### operation_segment
**Categorical signal `operation_segment`** — proxy tier: `INFERRED_PROXY`, source: `metadata.operation_segment`

| Category | Label | Applied Factor |
|----------|-------|----------------|
| `UPSTREAM_CONVENTIONAL` | Upstream Conventional | 1.0 |
| `UPSTREAM_UNCONVENTIONAL` | Upstream Unconventional | 0.95 |
| `UPSTREAM_OFFSHORE` | Upstream Offshore (Shelf) | 1.2 |
| `UPSTREAM_DEEPWATER` | Upstream Deepwater | 1.5 |
| `MIDSTREAM_PIPELINE` | Midstream Pipeline | 0.8 |
| `MIDSTREAM_PROCESSING` | Midstream Processing | 1.0 |
| `MIDSTREAM_STORAGE` | Midstream Storage | 0.85 |
| `DOWNSTREAM_REFINING` | Downstream Refining | 1.3 |
| `DOWNSTREAM_PETROCHEMICAL` | Downstream Petrochemical | 1.25 |
| `POWER_GENERATION` | Power Generation | 0.9 |
| `RENEWABLE` | Renewable Energy | 0.7 |
| `MIXED` | Mixed Operations | 1.05 |
| `OTHER` | UNKNOWN | 1.0 |

#### geographic_focus
**Categorical signal `geographic_focus`** — proxy tier: `INFERRED_PROXY`, source: `metadata.geographic_focus`

| Category | Label | Applied Factor |
|----------|-------|----------------|
| `US_ONSHORE` | US Onshore | 1.0 |
| `US_GULF_SHELF` | US Gulf Shelf | 1.1 |
| `US_GULF_DEEPWATER` | US Gulf Deepwater | 1.4 |
| `NORTH_SEA` | North Sea | 1.15 |
| `WEST_AFRICA` | West Africa | 1.25 |
| `MIDDLE_EAST` | Middle East | 1.2 |
| `ASIA_PACIFIC` | Asia Pacific | 1.1 |
| `LATIN_AMERICA` | Latin America | 1.2 |
| `GLOBAL_DIVERSIFIED` | Global Diversified | 1.05 |
| `OTHER` | Other | 1.15 |

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 | Safety Performance | 1.30 | 0.50 | 0.60 | 0.20 |
| 2 | Asset Portfolio | 0.66 | 0.15 | 0.18 | 0.33 |
| 3 | Operational Telemetry | 0.40 | 0.10 | 0.10 | 0.20 |
| 4 | Financial Stability | 0.35 | 0.10 | 0.05 | 0.20 |
| 5 | Network Authority | 0.20 | 0.10 | 0.05 | 0.05 |
| 6 | Structured Data | 0.09 | 0.05 | 0.02 | 0.02 |

**Primary Assessment Driver:** `Safety Performance` with combined weight of 1.30
**Secondary Driver:** `Asset Portfolio` with combined weight of 0.66

### Three-Layer Pricing Translation
> *How each pillar's tier score becomes a concrete underwriting action or pricing modifier. This is the bridge between signal observation and premium.*

**Risk -> Underwriting Action & Base Rate**

| Tier | Score Band | Action | Rate / Method |
|------|-----------|--------|---------------|
| PREFERRED | 800-1000 | APPROVE | 0.08% (MULTIPLIER) |
| STANDARD_PLUS | 650-799 | APPROVE | 0.12% (MULTIPLIER) |
| STANDARD | 500-649 | REFER | 0.18% (MULTIPLIER) |
| SUBSTANDARD | 350-499 | REFER | 0.28% (MULTIPLIER) |
| DECLINE | 0-349 | DECLINE | 0.45% (MULTIPLIER) |

**Loss -> Frequency & Severity Modifiers**

| Tier | Score Band | Frequency Modifier | Severity Modifier |
|------|-----------|--------------------|-------------------|
| VERY_LOW | 80-100 | 0.7 | 0.8 |
| LOW | 60-79 | 0.85 | 0.9 |
| MODERATE | 40-59 | 1.0 | 1.0 |
| ELEVATED | 20-39 | 1.15 | 1.15 |
| HIGH | 0-19 | 1.35 | 1.4 |

*Loss modifier is bounded: floor 0.55, cap 1.6.*

**Exposure (size) -> Scale Modifier**

| Band | Score Band | Modifier | Implied Value Range |
|------|-----------|----------|---------------------|
| MICRO | 0-20 | 0.5 | $0 - $1,000,000 |
| SMALL | 21-40 | 0.75 | $1,000,000 - $10,000,000 |
| MEDIUM | 41-60 | 1.0 | $10,000,000 - $50,000,000 |
| LARGE | 61-80 | 1.5 | $50,000,000 - $250,000,000 |
| VERY_LARGE | 81-100 | 1.3 | $250,000,000 - $1,000,000,000 |

**Exposure (complexity) -> Scale Modifier**

| Band | Score Band | Modifier | Implied Value Range |
|------|-----------|----------|---------------------|
| SIMPLE | 0-20 | 0.85 | n/a |
| MODERATE | 21-40 | 0.95 | n/a |
| COMPLEX | 41-60 | 1.1 | n/a |
| HIGHLY_COMPLEX | 61-80 | 1.3 | n/a |
| EXTREMELY_COMPLEX | 81-100 | 1.6 | n/a |

### Theoretical Premium Calculation (Tier 3 Standard)
> *Per the DSI Premium Calculation Methodology v2.0, the core formula is:*
> *P_final = (Base × Rate) × ILF_relativity × Deductible_Factor × Modifiers*

**1. The Pricing Anchor:** The Base Rate of `0.18%` on `tiv` purchases exactly a `$10,000,000` Limit with a `$50,000` Deductible.
**2. Theoretical Execution:**
  - Assume `tiv` = $10,000,000
  - Base Premium = $10,000,000 × 0.0018 = **$18,000**
  - If the client requests the Anchor Limit/Deductible, the factors are 1.00, resulting in a technical premium of **$18,000**.

---

## Model: `energy_upstream_deepwater`
*Deepwater upstream energy operations — subsea, floating, and fixed platform risks*

### Routing Protocol (Multiplexer)
- `tiv > 100000000`
- `operation_segment == UPSTREAM_DEEPWATER`

### Three-Layer Weight Distribution
> *DSI requires that weights for Risk, Loss, and Exposure each sum to 1.0 across all signal groups.*

**Validation:** PASS

| Group | Risk | Loss | Exposure |
|-------|------|------|----------|
| Network Authority | 0.10 | 0.05 | 0.00 |
| Safety Performance | 0.40 | 0.55 | 0.00 |
| Deepwater Operations | 0.20 | 0.15 | 0.35 |
| Financial Stability | 0.10 | 0.05 | 0.15 |
| Asset Portfolio | 0.20 | 0.20 | 0.50 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

**Group Definitions:**
- **Network Authority:** Quality of partnerships, contractors, and industry relationships
- **Safety Performance:** OSHA metrics, BSEE incidents, BOP reliability, process safety
- **Deepwater Operations:** Subsea integrity, dynamic positioning, mooring, riser systems, hurricane preparedness
- **Financial Stability:** Credit rating, leverage, ARO coverage, capex trends
- **Asset Portfolio:** Asset age, concentration, platform complexity, decommissioning

*Reading the table: a group's three weights are independent. The same group can be a dominant driver of one pillar and a minor input to another — e.g. a group may carry most of the Exposure weight while contributing little to Risk.*

### Signal Architecture Rationale
This configuration contains **35 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `DIRECT_OBSERVABLE` (14 signals): Highest confidence
- `INFERRED_PROXY` (21 signals): Medium confidence

**Signal Count by Group:**
- `public_record`: 11 signals
- `network_authority`: 6 signals
- `technical_infrastructure`: 5 signals
- `behavioural`: 5 signals
- `corporate_footprint`: 5 signals
- `operator_type`: 1 signals
- `water_depth_class`: 1 signals
- `geographic_focus`: 1 signals

**Selection Rationale:**
- 40% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Detail by Group
> *Each signal is an objectively observable data point. The weights show how strongly that signal informs each assessment pillar; correlation direction indicates whether a higher observed value increases (+) or decreases (-) the assessed exposure.*

#### Network Authority
*Quality of partnerships, contractors, and industry relationships*

| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `partner_quality` | INFERRED_PROXY | 0.25 | 0.10 / 0.15 | 0.00 | + |
| `contractor_quality` | INFERRED_PROXY | 0.20 | 0.15 / 0.00 | 0.00 | + |
| `insurance_history` | INFERRED_PROXY | 0.20 | 0.10 / 0.10 | 0.00 | + |
| `regulator_relationship` | INFERRED_PROXY | 0.15 | 0.10 / 0.00 | 0.00 | + |
| `industry_association` | DIRECT_OBSERVABLE | 0.10 | 0.00 / 0.00 | 0.00 | + |
| `banking_relationship` | INFERRED_PROXY | 0.10 | 0.00 / 0.00 | 0.00 | + |

#### Safety Performance
*OSHA metrics, BSEE incidents, BOP reliability, process safety*

| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `osha_trir` | DIRECT_OBSERVABLE | 0.20 | 0.20 / 0.10 | 0.00 | + |
| `bsee_incident` | DIRECT_OBSERVABLE | 0.15 | 0.15 / 0.20 | 0.00 | + |
| `process_safety` | INFERRED_PROXY | 0.20 | 0.20 / 0.30 | 0.00 | + |
| `fatality` | DIRECT_OBSERVABLE | 0.15 | 0.00 / 0.30 | 0.00 | + |
| `major_incident` | DIRECT_OBSERVABLE | 0.15 | 0.15 / 0.35 | 0.00 | + |
| `near_miss` | INFERRED_PROXY | 0.05 | 0.10 / 0.00 | 0.00 | + |
| `bop_reliability` | DIRECT_OBSERVABLE | 0.10 | 0.00 / 0.25 | 0.00 | + |
| `epa_violation` | DIRECT_OBSERVABLE | 0.25 | 0.20 / 0.25 | 0.00 | + |
| `spill_history` | DIRECT_OBSERVABLE | 0.30 | 0.20 / 0.35 | 0.00 | + |
| `emissions_compliance` | DIRECT_OBSERVABLE | 0.15 | 0.10 / 0.00 | 0.00 | + |
| `remediation` | INFERRED_PROXY | 0.10 | 0.00 / 0.15 | 0.00 | + |

#### Deepwater Operations
*Subsea integrity, dynamic positioning, mooring, riser systems, hurricane preparedness*

| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `subsea_integrity` | INFERRED_PROXY | 0.25 | 0.20 / 0.25 | 0.15 | + |
| `dynamic_positioning` | INFERRED_PROXY | 0.20 | 0.15 / 0.15 | 0.00 | + |
| `mooring_integrity` | INFERRED_PROXY | 0.20 | 0.10 / 0.20 | 0.10 | + |
| `riser_integrity` | INFERRED_PROXY | 0.20 | 0.15 / 0.20 | 0.00 | + |
| `hurricane_preparedness` | INFERRED_PROXY | 0.15 | 0.00 / 0.15 | 0.10 | + |

#### Financial Stability
*Credit rating, leverage, ARO coverage, capex trends*

| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `credit_rating` | DIRECT_OBSERVABLE | 0.30 | 0.00 / 0.20 | 0.00 | + |
| `leverage` | DIRECT_OBSERVABLE | 0.25 | 0.00 / 0.15 | 0.00 | - |
| `capex_trend` | DIRECT_OBSERVABLE | 0.20 | 0.00 / 0.00 | 0.10 | + |
| `restructuring` | DIRECT_OBSERVABLE | 0.15 | 0.00 / 0.20 | 0.00 | + |
| `aro_coverage` | INFERRED_PROXY | 0.10 | 0.00 / 0.00 | 0.05 | + |

#### Asset Portfolio
*Asset age, concentration, platform complexity, decommissioning*

| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `asset_age` | INFERRED_PROXY | 0.30 | 0.20 / 0.15 | 0.10 | - |
| `concentration` | INFERRED_PROXY | 0.25 | 0.00 / 0.25 | 0.15 | - |
| `platform_complexity` | INFERRED_PROXY | 0.20 | 0.15 / 0.15 | 0.20 | - |
| `decommissioning` | INFERRED_PROXY | 0.15 | 0.00 / 0.10 | 0.10 | + |
| `permit_status` | DIRECT_OBSERVABLE | 0.10 | 0.00 / 0.00 | 0.00 | + |

#### operator_type
**Categorical signal `operator_type`** — proxy tier: `INFERRED_PROXY`, source: `metadata.operator_type`

| Category | Label | Applied Factor |
|----------|-------|----------------|
| `SUPERMAJOR` | Supermajor | 0.75 |
| `MAJOR_INTEGRATED` | Major Integrated | 0.85 |
| `LARGE_INDEPENDENT` | Large Independent | 0.95 |
| `MID_INDEPENDENT` | Mid-Size Independent | 1.15 |
| `NATIONAL_OIL` | National Oil Company | 0.9 |
| `UNKNOWN` | Unknown/New Operator | 1.5 |
| `OTHER` | UNKNOWN | 1.0 |

#### water_depth_class
**Categorical signal `water_depth_class`** — proxy tier: `INFERRED_PROXY`, source: `metadata.water_depth_class`

| Category | Label | Applied Factor |
|----------|-------|----------------|
| `SHELF` | Continental Shelf (<400ft) | 0.85 |
| `MID_WATER` | Mid-Water (400-3000ft) | 1.0 |
| `DEEPWATER` | Deepwater (3000-7000ft) | 1.25 |
| `ULTRA_DEEP` | Ultra-Deepwater (>7000ft) | 1.5 |
| `OTHER` | Unknown | 1.3 |

#### geographic_focus
**Categorical signal `geographic_focus`** — proxy tier: `INFERRED_PROXY`, source: `metadata.geographic_focus`

| Category | Label | Applied Factor |
|----------|-------|----------------|
| `US_GULF_SHELF` | US Gulf Shelf | 1.0 |
| `US_GULF_DEEPWATER` | US Gulf Deepwater | 1.2 |
| `NORTH_SEA` | North Sea | 1.1 |
| `WEST_AFRICA` | West Africa | 1.3 |
| `BRAZIL` | Brazil Pre-Salt | 1.25 |
| `ASIA_PACIFIC` | Asia Pacific | 1.15 |
| `OTHER` | Other | 1.2 |

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 | Safety Performance | 0.95 | 0.40 | 0.55 | 0.00 |
| 2 | Asset Portfolio | 0.90 | 0.20 | 0.20 | 0.50 |
| 3 | Deepwater Operations | 0.70 | 0.20 | 0.15 | 0.35 |
| 4 | Financial Stability | 0.30 | 0.10 | 0.05 | 0.15 |
| 5 | Network Authority | 0.15 | 0.10 | 0.05 | 0.00 |

**Primary Assessment Driver:** `Safety Performance` with combined weight of 0.95
**Secondary Driver:** `Asset Portfolio` with combined weight of 0.90

### Three-Layer Pricing Translation
> *How each pillar's tier score becomes a concrete underwriting action or pricing modifier. This is the bridge between signal observation and premium.*

**Risk -> Underwriting Action & Base Rate**

| Tier | Score Band | Action | Rate / Method |
|------|-----------|--------|---------------|
| PREFERRED | 800-1000 | APPROVE | 0.06% (MULTIPLIER) |
| STANDARD_PLUS | 650-799 | APPROVE | 0.1% (MULTIPLIER) |
| STANDARD | 500-649 | REFER | 0.16% (MULTIPLIER) |
| SUBSTANDARD | 350-499 | REFER | 0.26% (MULTIPLIER) |
| DECLINE | 0-349 | DECLINE | 0.4% (MULTIPLIER) |

**Loss -> Frequency & Severity Modifiers**

| Tier | Score Band | Frequency Modifier | Severity Modifier |
|------|-----------|--------------------|-------------------|
| VERY_LOW | 80-100 | 0.7 | 0.8 |
| LOW | 60-79 | 0.85 | 0.9 |
| MODERATE | 40-59 | 1.0 | 1.0 |
| ELEVATED | 20-39 | 1.15 | 1.15 |
| HIGH | 0-19 | 1.35 | 1.4 |

*Loss modifier is bounded: floor 0.55, cap 1.6.*

**Exposure (size) -> Scale Modifier**

| Band | Score Band | Modifier | Implied Value Range |
|------|-----------|----------|---------------------|
| SMALL | 0-20 | 0.75 | $0 - $500,000,000 |
| MEDIUM | 21-40 | 1.0 | $500,000,000 - $2,000,000,000 |
| LARGE | 41-60 | 1.3 | $2,000,000,000 - $5,000,000,000 |
| VERY_LARGE | 61-80 | 1.8 | $5,000,000,000 - $15,000,000,000 |
| MEGA | 81-100 | 2.5 | $15,000,000,000 - $50,000,000,000 |

**Exposure (complexity) -> Scale Modifier**

| Band | Score Band | Modifier | Implied Value Range |
|------|-----------|----------|---------------------|
| SIMPLE | 0-20 | 0.85 | n/a |
| MODERATE | 21-40 | 0.95 | n/a |
| COMPLEX | 41-60 | 1.1 | n/a |
| HIGHLY_COMPLEX | 61-80 | 1.3 | n/a |
| EXTREMELY_COMPLEX | 81-100 | 1.6 | n/a |

### Theoretical Premium Calculation (Tier 3 Standard)
> *Per the DSI Premium Calculation Methodology v2.0, the core formula is:*
> *P_final = (Base × Rate) × ILF_relativity × Deductible_Factor × Modifiers*

**1. The Pricing Anchor:** The Base Rate of `0.16%` on `tiv` purchases exactly a `$10,000,000` Limit with a `$1,000,000` Deductible.
**2. Theoretical Execution:**
  - Assume `tiv` = $10,000,000
  - Base Premium = $10,000,000 × 0.0016 = **$16,000**
  - If the client requests the Anchor Limit/Deductible, the factors are 1.00, resulting in a technical premium of **$16,000**.

---

## Model: `energy_upstream_onshore`
*Conventional onshore E&P — Permian, Oklahoma, Louisiana conventional operations*

### Routing Protocol (Multiplexer)
- `operation_segment == UPSTREAM_CONVENTIONAL`

### Three-Layer Weight Distribution
> *DSI requires that weights for Risk, Loss, and Exposure each sum to 1.0 across all signal groups.*

**Validation:** PASS

| Group | Risk | Loss | Exposure |
|-------|------|------|----------|
| Network Authority | 0.05 | 0.03 | 0.03 |
| Safety Performance | 0.45 | 0.50 | 0.20 |
| Operational Telemetry | 0.15 | 0.15 | 0.25 |
| Financial Stability | 0.10 | 0.07 | 0.17 |
| Asset Portfolio | 0.20 | 0.23 | 0.33 |
| Structured Data | 0.05 | 0.02 | 0.02 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

**Group Definitions:**
- **Network Authority:** Quality of partnerships, contractors, and industry relationships
- **Safety Performance:** OSHA metrics, state regulatory compliance, H2S exposure, process safety
- **Operational Telemetry:** Production consistency, well integrity, artificial lift reliability
- **Financial Stability:** Credit rating, leverage, ARO coverage, capex trends
- **Asset Portfolio:** Asset age, concentration, well vintage, decommissioning
- **Structured Data:** Third-party ESG ratings and benchmarks

*Reading the table: a group's three weights are independent. The same group can be a dominant driver of one pillar and a minor input to another — e.g. a group may carry most of the Exposure weight while contributing little to Risk.*

### Signal Architecture Rationale
This configuration contains **49 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `DIRECT_OBSERVABLE` (19 signals): Highest confidence
- `INFERRED_PROXY` (30 signals): Medium confidence

**Signal Count by Group:**
- `public_record`: 14 signals
- `corporate_footprint`: 12 signals
- `network_authority`: 6 signals
- `technical_infrastructure`: 6 signals
- `behavioural`: 5 signals
- `structured_data`: 3 signals
- `operator_type`: 1 signals
- `operation_segment`: 1 signals
- `geographic_focus`: 1 signals

**Selection Rationale:**
- 39% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Detail by Group
> *Each signal is an objectively observable data point. The weights show how strongly that signal informs each assessment pillar; correlation direction indicates whether a higher observed value increases (+) or decreases (-) the assessed exposure.*

#### Network Authority
*Quality of partnerships, contractors, and industry relationships*

| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `partner_quality` | INFERRED_PROXY | 0.25 | 0.15 / 0.10 | 0.00 | + |
| `contractor_quality` | INFERRED_PROXY | 0.20 | 0.15 / 0.00 | 0.00 | + |
| `insurance_history` | INFERRED_PROXY | 0.20 | 0.10 / 0.10 | 0.00 | + |
| `regulator_relationship` | INFERRED_PROXY | 0.15 | 0.10 / 0.00 | 0.00 | + |
| `industry_association` | DIRECT_OBSERVABLE | 0.10 | 0.00 / 0.00 | 0.00 | + |
| `banking_relationship` | INFERRED_PROXY | 0.10 | 0.00 / 0.00 | 0.00 | + |

#### Safety Performance
*OSHA metrics, state regulatory compliance, H2S exposure, process safety*

| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `osha_trir` | DIRECT_OBSERVABLE | 0.20 | 0.20 / 0.10 | 0.00 | + |
| `process_safety` | INFERRED_PROXY | 0.15 | 0.15 / 0.20 | 0.00 | + |
| `fatality` | DIRECT_OBSERVABLE | 0.10 | 0.00 / 0.20 | 0.00 | + |
| `major_incident` | DIRECT_OBSERVABLE | 0.10 | 0.10 / 0.20 | 0.00 | + |
| `near_miss` | INFERRED_PROXY | 0.05 | 0.05 / 0.00 | 0.00 | + |
| `h2s_exposure` | DIRECT_OBSERVABLE | 0.15 | 0.00 / 0.15 | 0.00 | - |
| `state_regulatory_compliance` | DIRECT_OBSERVABLE | 0.25 | 0.15 / 0.15 | 0.00 | + |
| `epa_violation` | DIRECT_OBSERVABLE | 0.20 | 0.15 / 0.20 | 0.00 | + |
| `spill_history` | DIRECT_OBSERVABLE | 0.20 | 0.15 / 0.20 | 0.00 | + |
| `emissions_compliance` | DIRECT_OBSERVABLE | 0.10 | 0.10 / 0.00 | 0.00 | + |
| `flaring` | DIRECT_OBSERVABLE | 0.10 | 0.10 / 0.00 | 0.00 | + |
| `methane` | INFERRED_PROXY | 0.10 | 0.05 / 0.00 | 0.00 | + |
| `remediation` | INFERRED_PROXY | 0.05 | 0.00 / 0.10 | 0.00 | + |
| `produced_water_management` | INFERRED_PROXY | 0.25 | 0.20 / 0.25 | 0.00 | + |

#### Operational Telemetry
*Production consistency, well integrity, artificial lift reliability*

| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `production_consistency` | INFERRED_PROXY | 0.20 | 0.15 / 0.00 | 0.15 | + |
| `well_integrity` | INFERRED_PROXY | 0.20 | 0.15 / 0.15 | 0.15 | + |
| `maintenance_pattern` | INFERRED_PROXY | 0.15 | 0.15 / 0.00 | 0.10 | + |
| `facility_activity` | INFERRED_PROXY | 0.10 | 0.00 / 0.00 | 0.15 | + |
| `operational_efficiency` | INFERRED_PROXY | 0.10 | 0.10 / 0.00 | 0.10 | + |
| `artificial_lift_reliability` | INFERRED_PROXY | 0.25 | 0.20 / 0.10 | 0.15 | + |

#### Financial Stability
*Credit rating, leverage, ARO coverage, capex trends*

| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `credit_rating` | DIRECT_OBSERVABLE | 0.30 | 0.00 / 0.20 | 0.00 | + |
| `leverage` | DIRECT_OBSERVABLE | 0.25 | 0.00 / 0.15 | 0.00 | - |
| `capex_trend` | DIRECT_OBSERVABLE | 0.20 | 0.00 / 0.00 | 0.10 | + |
| `restructuring` | DIRECT_OBSERVABLE | 0.15 | 0.00 / 0.20 | 0.00 | + |
| `aro_coverage` | INFERRED_PROXY | 0.10 | 0.00 / 0.00 | 0.05 | + |

#### Asset Portfolio
*Asset age, concentration, well vintage, decommissioning*

| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `asset_age` | INFERRED_PROXY | 0.20 | 0.15 / 0.10 | 0.10 | - |
| `concentration` | INFERRED_PROXY | 0.15 | 0.00 / 0.15 | 0.15 | - |
| `technology_profile` | INFERRED_PROXY | 0.15 | 0.10 / 0.10 | 0.15 | - |
| `decommissioning` | INFERRED_PROXY | 0.10 | 0.00 / 0.10 | 0.10 | + |
| `permit_status` | DIRECT_OBSERVABLE | 0.10 | 0.00 / 0.00 | 0.00 | + |
| `well_vintage_profile` | INFERRED_PROXY | 0.30 | 0.20 / 0.20 | 0.20 | - |
| `esg_reporting` | INFERRED_PROXY | 0.20 | 0.15 / 0.00 | 0.00 | + |
| `safety_communication` | DIRECT_OBSERVABLE | 0.25 | 0.20 / 0.00 | 0.00 | + |
| `disclosure_quality` | INFERRED_PROXY | 0.15 | 0.15 / 0.00 | 0.00 | + |
| `hse_leadership` | INFERRED_PROXY | 0.15 | 0.00 / 0.15 | 0.00 | + |
| `technical_hiring` | INFERRED_PROXY | 0.15 | 0.00 / 0.00 | 0.10 | + |
| `industry_presence` | DIRECT_OBSERVABLE | 0.10 | 0.00 / 0.00 | 0.00 | + |

#### Structured Data
*Third-party ESG ratings and benchmarks*

| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `esg_rating` | DIRECT_OBSERVABLE | 0.40 | 0.00 / 0.30 | 0.00 | + |
| `benchmark` | INFERRED_PROXY | 0.35 | 0.00 / 0.35 | 0.00 | + |
| `credit` | DIRECT_OBSERVABLE | 0.25 | 0.00 / 0.35 | 0.00 | + |

#### operator_type
**Categorical signal `operator_type`** — proxy tier: `INFERRED_PROXY`, source: `metadata.operator_type`

| Category | Label | Applied Factor |
|----------|-------|----------------|
| `SUPERMAJOR` | Supermajor | 0.75 |
| `MAJOR_INTEGRATED` | Major Integrated | 0.85 |
| `LARGE_INDEPENDENT` | Large Independent | 0.95 |
| `MID_INDEPENDENT` | Mid-Size Independent | 1.1 |
| `SMALL_INDEPENDENT` | Small Independent | 1.25 |
| `NATIONAL_OIL` | National Oil Company | 0.9 |
| `OTHER` | Unknown | 1.0 |

#### operation_segment
**Categorical signal `operation_segment`** — proxy tier: `INFERRED_PROXY`, source: `metadata.operation_segment`

| Category | Label | Applied Factor |
|----------|-------|----------------|
| `UPSTREAM_CONVENTIONAL` | Conventional Upstream | 1.0 |
| `OTHER` | Other | 1.1 |

#### geographic_focus
**Categorical signal `geographic_focus`** — proxy tier: `INFERRED_PROXY`, source: `metadata.geographic_focus`

| Category | Label | Applied Factor |
|----------|-------|----------------|
| `US_ONSHORE` | US Onshore | 1.0 |
| `NORTH_SEA` | North Sea | 1.1 |
| `LATIN_AMERICA` | Latin America | 1.15 |
| `MIDDLE_EAST` | Middle East | 1.1 |
| `ASIA_PACIFIC` | Asia Pacific | 1.1 |
| `OTHER` | Other | 1.1 |

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 | Safety Performance | 1.15 | 0.45 | 0.50 | 0.20 |
| 2 | Asset Portfolio | 0.76 | 0.20 | 0.23 | 0.33 |
| 3 | Operational Telemetry | 0.55 | 0.15 | 0.15 | 0.25 |
| 4 | Financial Stability | 0.34 | 0.10 | 0.07 | 0.17 |
| 5 | Network Authority | 0.11 | 0.05 | 0.03 | 0.03 |
| 6 | Structured Data | 0.09 | 0.05 | 0.02 | 0.02 |

**Primary Assessment Driver:** `Safety Performance` with combined weight of 1.15
**Secondary Driver:** `Asset Portfolio` with combined weight of 0.76

### Three-Layer Pricing Translation
> *How each pillar's tier score becomes a concrete underwriting action or pricing modifier. This is the bridge between signal observation and premium.*

**Risk -> Underwriting Action & Base Rate**

| Tier | Score Band | Action | Rate / Method |
|------|-----------|--------|---------------|
| PREFERRED | 800-1000 | APPROVE | 0.07% (MULTIPLIER) |
| STANDARD_PLUS | 650-799 | APPROVE | 0.11% (MULTIPLIER) |
| STANDARD | 500-649 | REFER | 0.16% (MULTIPLIER) |
| SUBSTANDARD | 350-499 | REFER | 0.25% (MULTIPLIER) |
| DECLINE | 0-349 | DECLINE | 0.4% (MULTIPLIER) |

**Loss -> Frequency & Severity Modifiers**

| Tier | Score Band | Frequency Modifier | Severity Modifier |
|------|-----------|--------------------|-------------------|
| VERY_LOW | 80-100 | 0.75 | 0.8 |
| LOW | 60-79 | 0.88 | 0.9 |
| MODERATE | 40-59 | 1.0 | 1.0 |
| ELEVATED | 20-39 | 1.12 | 1.1 |
| HIGH | 0-19 | 1.3 | 1.3 |

*Loss modifier is bounded: floor 0.6, cap 1.5.*

**Exposure (size) -> Scale Modifier**

| Band | Score Band | Modifier | Implied Value Range |
|------|-----------|----------|---------------------|
| MICRO | 0-20 | 0.7 | n/a |
| SMALL | 21-40 | 0.85 | n/a |
| MEDIUM | 41-60 | 1.0 | n/a |
| LARGE | 61-80 | 1.3 | n/a |
| VERY_LARGE | 81-100 | 1.8 | n/a |

**Exposure (complexity) -> Scale Modifier**

| Band | Score Band | Modifier | Implied Value Range |
|------|-----------|----------|---------------------|
| SIMPLE | 0-20 | 0.85 | n/a |
| MODERATE | 21-40 | 0.95 | n/a |
| COMPLEX | 41-60 | 1.05 | n/a |
| HIGHLY_COMPLEX | 61-80 | 1.2 | n/a |
| EXTREMELY_COMPLEX | 81-100 | 1.4 | n/a |

### Theoretical Premium Calculation (Tier 3 Standard)
> *Per the DSI Premium Calculation Methodology v2.0, the core formula is:*
> *P_final = (Base × Rate) × ILF_relativity × Deductible_Factor × Modifiers*

**1. The Pricing Anchor:** The Base Rate of `0.16%` on `tiv` purchases exactly a `$10,000,000` Limit with a `$50,000` Deductible.
**2. Theoretical Execution:**
  - Assume `tiv` = $10,000,000
  - Base Premium = $10,000,000 × 0.0016 = **$16,000**
  - If the client requests the Anchor Limit/Deductible, the factors are 1.00, resulting in a technical premium of **$16,000**.

---

## Model: `energy_upstream_unconventional`
*Tight oil, shale gas, and hydraulic fracturing operations*

### Routing Protocol (Multiplexer)
- `operation_segment == UPSTREAM_UNCONVENTIONAL`

### Three-Layer Weight Distribution
> *DSI requires that weights for Risk, Loss, and Exposure each sum to 1.0 across all signal groups.*

**Validation:** PASS

| Group | Risk | Loss | Exposure |
|-------|------|------|----------|
| Network Authority | 0.05 | 0.03 | 0.03 |
| Safety Performance | 0.50 | 0.55 | 0.25 |
| Operational Telemetry | 0.15 | 0.15 | 0.20 |
| Financial Stability | 0.10 | 0.07 | 0.15 |
| Asset Portfolio | 0.15 | 0.15 | 0.35 |
| Structured Data | 0.05 | 0.05 | 0.02 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

**Group Definitions:**
- **Network Authority:** Quality of partnerships, contractors, and industry relationships
- **Safety Performance:** OSHA metrics, process safety, fatality history
- **Operational Telemetry:** Frac fleet quality, completion efficiency, pad drilling
- **Financial Stability:** Credit rating, leverage, ARO coverage, capex trends
- **Asset Portfolio:** Asset age, well spacing, concentration, technology profile
- **Structured Data:** Third-party ESG ratings and benchmarks

*Reading the table: a group's three weights are independent. The same group can be a dominant driver of one pillar and a minor input to another — e.g. a group may carry most of the Exposure weight while contributing little to Risk.*

### Signal Architecture Rationale
This configuration contains **52 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `DIRECT_OBSERVABLE` (20 signals): Highest confidence
- `INFERRED_PROXY` (32 signals): Medium confidence

**Signal Count by Group:**
- `public_record`: 14 signals
- `corporate_footprint`: 13 signals
- `technical_infrastructure`: 8 signals
- `network_authority`: 6 signals
- `behavioural`: 5 signals
- `structured_data`: 3 signals
- `operator_type`: 1 signals
- `operation_segment`: 1 signals
- `geographic_focus`: 1 signals

**Selection Rationale:**
- 38% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Detail by Group
> *Each signal is an objectively observable data point. The weights show how strongly that signal informs each assessment pillar; correlation direction indicates whether a higher observed value increases (+) or decreases (-) the assessed exposure.*

#### Network Authority
*Quality of partnerships, contractors, and industry relationships*

| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `partner_quality` | INFERRED_PROXY | 0.25 | 0.15 / 0.10 | 0.00 | + |
| `contractor_quality` | INFERRED_PROXY | 0.20 | 0.15 / 0.00 | 0.00 | + |
| `insurance_history` | INFERRED_PROXY | 0.20 | 0.10 / 0.10 | 0.00 | + |
| `regulator_relationship` | INFERRED_PROXY | 0.15 | 0.10 / 0.00 | 0.00 | + |
| `industry_association` | DIRECT_OBSERVABLE | 0.10 | 0.00 / 0.00 | 0.00 | + |
| `banking_relationship` | INFERRED_PROXY | 0.10 | 0.00 / 0.00 | 0.00 | + |

#### Safety Performance
*OSHA metrics, process safety, fatality history*

| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `osha_trir` | DIRECT_OBSERVABLE | 0.20 | 0.20 / 0.10 | 0.00 | + |
| `process_safety` | INFERRED_PROXY | 0.20 | 0.20 / 0.25 | 0.00 | + |
| `fatality` | DIRECT_OBSERVABLE | 0.15 | 0.00 / 0.25 | 0.00 | + |
| `major_incident` | DIRECT_OBSERVABLE | 0.15 | 0.15 / 0.30 | 0.00 | + |
| `near_miss` | INFERRED_PROXY | 0.05 | 0.10 / 0.00 | 0.00 | + |
| `osha_violations` | DIRECT_OBSERVABLE | 0.25 | 0.15 / 0.10 | 0.00 | + |
| `epa_violation` | DIRECT_OBSERVABLE | 0.15 | 0.10 / 0.15 | 0.00 | + |
| `spill_history` | DIRECT_OBSERVABLE | 0.15 | 0.10 / 0.15 | 0.00 | + |
| `emissions_compliance` | DIRECT_OBSERVABLE | 0.10 | 0.05 / 0.00 | 0.00 | + |
| `flaring` | DIRECT_OBSERVABLE | 0.05 | 0.05 / 0.00 | 0.00 | + |
| `methane` | INFERRED_PROXY | 0.05 | 0.00 / 0.00 | 0.00 | + |
| `remediation` | INFERRED_PROXY | 0.05 | 0.00 / 0.05 | 0.00 | + |
| `water_recycling_rate` | DIRECT_OBSERVABLE | 0.20 | 0.15 / 0.15 | 0.00 | + |
| `induced_seismicity_score` | DIRECT_OBSERVABLE | 0.25 | 0.20 / 0.30 | 0.00 | + |

#### Operational Telemetry
*Frac fleet quality, completion efficiency, pad drilling*

| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `production_consistency` | INFERRED_PROXY | 0.10 | 0.10 / 0.00 | 0.10 | + |
| `well_integrity` | INFERRED_PROXY | 0.10 | 0.10 / 0.10 | 0.10 | + |
| `maintenance_pattern` | INFERRED_PROXY | 0.10 | 0.10 / 0.00 | 0.10 | + |
| `facility_activity` | INFERRED_PROXY | 0.05 | 0.00 / 0.00 | 0.10 | + |
| `operational_efficiency` | INFERRED_PROXY | 0.05 | 0.05 / 0.00 | 0.00 | + |
| `frac_fleet_quality` | INFERRED_PROXY | 0.20 | 0.15 / 0.15 | 0.15 | + |
| `completion_efficiency` | INFERRED_PROXY | 0.20 | 0.15 / 0.10 | 0.15 | + |
| `pad_drilling_intensity` | INFERRED_PROXY | 0.20 | 0.10 / 0.00 | 0.30 | - |

#### Financial Stability
*Credit rating, leverage, ARO coverage, capex trends*

| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `credit_rating` | DIRECT_OBSERVABLE | 0.30 | 0.00 / 0.20 | 0.00 | + |
| `leverage` | DIRECT_OBSERVABLE | 0.25 | 0.00 / 0.15 | 0.00 | - |
| `capex_trend` | DIRECT_OBSERVABLE | 0.20 | 0.00 / 0.00 | 0.10 | + |
| `restructuring` | DIRECT_OBSERVABLE | 0.15 | 0.00 / 0.20 | 0.00 | + |
| `aro_coverage` | INFERRED_PROXY | 0.10 | 0.00 / 0.00 | 0.05 | + |

#### Asset Portfolio
*Asset age, well spacing, concentration, technology profile*

| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `asset_age` | INFERRED_PROXY | 0.15 | 0.15 / 0.10 | 0.10 | - |
| `concentration` | INFERRED_PROXY | 0.15 | 0.00 / 0.15 | 0.15 | - |
| `technology_profile` | INFERRED_PROXY | 0.10 | 0.10 / 0.00 | 0.15 | - |
| `decommissioning` | INFERRED_PROXY | 0.05 | 0.00 / 0.05 | 0.00 | + |
| `permit_status` | DIRECT_OBSERVABLE | 0.10 | 0.00 / 0.00 | 0.00 | + |
| `well_spacing_optimisation` | INFERRED_PROXY | 0.25 | 0.20 / 0.15 | 0.20 | + |
| `complexity` | INFERRED_PROXY | 0.20 | 0.15 / 0.15 | 0.20 | - |
| `esg_reporting` | INFERRED_PROXY | 0.20 | 0.15 / 0.00 | 0.00 | + |
| `safety_communication` | DIRECT_OBSERVABLE | 0.25 | 0.20 / 0.00 | 0.00 | + |
| `disclosure_quality` | INFERRED_PROXY | 0.15 | 0.15 / 0.00 | 0.00 | + |
| `hse_leadership` | INFERRED_PROXY | 0.15 | 0.00 / 0.15 | 0.00 | + |
| `technical_hiring` | INFERRED_PROXY | 0.15 | 0.00 / 0.00 | 0.10 | + |
| `industry_presence` | DIRECT_OBSERVABLE | 0.10 | 0.00 / 0.00 | 0.00 | + |

#### Structured Data
*Third-party ESG ratings and benchmarks*

| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `esg_rating` | DIRECT_OBSERVABLE | 0.40 | 0.00 / 0.30 | 0.00 | + |
| `benchmark` | INFERRED_PROXY | 0.35 | 0.00 / 0.35 | 0.00 | + |
| `credit` | DIRECT_OBSERVABLE | 0.25 | 0.00 / 0.35 | 0.00 | + |

#### operator_type
**Categorical signal `operator_type`** — proxy tier: `INFERRED_PROXY`, source: `metadata.operator_type`

| Category | Label | Applied Factor |
|----------|-------|----------------|
| `SUPERMAJOR` | Supermajor | 0.75 |
| `MAJOR_INTEGRATED` | Major Integrated | 0.85 |
| `LARGE_INDEPENDENT` | Large Independent | 0.95 |
| `MID_INDEPENDENT` | Mid-Size Independent | 1.1 |
| `SMALL_INDEPENDENT` | Small Independent | 1.25 |
| `NATIONAL_OIL` | National Oil Company | 0.9 |
| `OTHER` | Unknown | 1.0 |

#### operation_segment
**Categorical signal `operation_segment`** — proxy tier: `INFERRED_PROXY`, source: `metadata.operation_segment`

| Category | Label | Applied Factor |
|----------|-------|----------------|
| `UPSTREAM_UNCONVENTIONAL` | Unconventional Upstream | 1.0 |
| `OTHER` | Other | 1.1 |

#### geographic_focus
**Categorical signal `geographic_focus`** — proxy tier: `INFERRED_PROXY`, source: `metadata.geographic_focus`

| Category | Label | Applied Factor |
|----------|-------|----------------|
| `US_ONSHORE` | US Onshore | 1.0 |
| `NORTH_SEA` | North Sea | 1.1 |
| `LATIN_AMERICA` | Latin America | 1.2 |
| `ASIA_PACIFIC` | Asia Pacific | 1.15 |
| `OTHER` | Other | 1.1 |

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 | Safety Performance | 1.30 | 0.50 | 0.55 | 0.25 |
| 2 | Asset Portfolio | 0.65 | 0.15 | 0.15 | 0.35 |
| 3 | Operational Telemetry | 0.50 | 0.15 | 0.15 | 0.20 |
| 4 | Financial Stability | 0.32 | 0.10 | 0.07 | 0.15 |
| 5 | Structured Data | 0.12 | 0.05 | 0.05 | 0.02 |
| 6 | Network Authority | 0.11 | 0.05 | 0.03 | 0.03 |

**Primary Assessment Driver:** `Safety Performance` with combined weight of 1.30
**Secondary Driver:** `Asset Portfolio` with combined weight of 0.65

### Three-Layer Pricing Translation
> *How each pillar's tier score becomes a concrete underwriting action or pricing modifier. This is the bridge between signal observation and premium.*

**Risk -> Underwriting Action & Base Rate**

| Tier | Score Band | Action | Rate / Method |
|------|-----------|--------|---------------|
| PREFERRED | 800-1000 | APPROVE | 0.1% (MULTIPLIER) |
| STANDARD_PLUS | 650-799 | APPROVE | 0.16% (MULTIPLIER) |
| STANDARD | 500-649 | REFER | 0.22% (MULTIPLIER) |
| SUBSTANDARD | 350-499 | REFER | 0.35% (MULTIPLIER) |
| DECLINE | 0-349 | DECLINE | 0.55% (MULTIPLIER) |

**Loss -> Frequency & Severity Modifiers**

| Tier | Score Band | Frequency Modifier | Severity Modifier |
|------|-----------|--------------------|-------------------|
| VERY_LOW | 80-100 | 0.75 | 0.8 |
| LOW | 60-79 | 0.88 | 0.9 |
| MODERATE | 40-59 | 1.0 | 1.0 |
| ELEVATED | 20-39 | 1.15 | 1.15 |
| HIGH | 0-19 | 1.35 | 1.35 |

*Loss modifier is bounded: floor 0.6, cap 1.55.*

**Exposure (size) -> Scale Modifier**

| Band | Score Band | Modifier | Implied Value Range |
|------|-----------|----------|---------------------|
| SMALL | 0-20 | 0.75 | n/a |
| MEDIUM | 21-40 | 1.0 | n/a |
| LARGE | 41-60 | 1.3 | n/a |
| VERY_LARGE | 61-80 | 1.7 | n/a |
| MEGA | 81-100 | 2.3 | n/a |

**Exposure (complexity) -> Scale Modifier**

| Band | Score Band | Modifier | Implied Value Range |
|------|-----------|----------|---------------------|
| SIMPLE | 0-20 | 0.85 | n/a |
| MODERATE | 21-40 | 0.95 | n/a |
| COMPLEX | 41-60 | 1.1 | n/a |
| HIGHLY_COMPLEX | 61-80 | 1.3 | n/a |
| EXTREMELY_COMPLEX | 81-100 | 1.55 | n/a |

### Theoretical Premium Calculation (Tier 3 Standard)
> *Per the DSI Premium Calculation Methodology v2.0, the core formula is:*
> *P_final = (Base × Rate) × ILF_relativity × Deductible_Factor × Modifiers*

**1. The Pricing Anchor:** The Base Rate of `0.22%` on `tiv` purchases exactly a `$10,000,000` Limit with a `$100,000` Deductible.
**2. Theoretical Execution:**
  - Assume `tiv` = $10,000,000
  - Base Premium = $10,000,000 × 0.0022 = **$22,000**
  - If the client requests the Anchor Limit/Deductible, the factors are 1.00, resulting in a technical premium of **$22,000**.

---

## Model: `energy_midstream`
*Pipeline, processing, and storage operations*

### Routing Protocol (Multiplexer)
- `operation_segment in ['MIDSTREAM_PIPELINE', 'MIDSTREAM_PROCESSING', 'MIDSTREAM_STORAGE']`

### Three-Layer Weight Distribution
> *DSI requires that weights for Risk, Loss, and Exposure each sum to 1.0 across all signal groups.*

**Validation:** PASS

| Group | Risk | Loss | Exposure |
|-------|------|------|----------|
| Network Authority | 0.05 | 0.03 | 0.03 |
| Safety Performance | 0.35 | 0.35 | 0.17 |
| Operational Telemetry | 0.20 | 0.25 | 0.25 |
| Financial Stability | 0.15 | 0.10 | 0.25 |
| Asset Portfolio | 0.20 | 0.25 | 0.28 |
| Structured Data | 0.05 | 0.02 | 0.02 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

**Group Definitions:**
- **Network Authority:** Quality of partnerships and industry relationships
- **Safety Performance:** OSHA metrics
- **Operational Telemetry:** Inline inspection
- **Financial Stability:** Credit rating
- **Asset Portfolio:** Pipeline vintage
- **Structured Data:** Third-party ESG ratings and benchmarks

*Reading the table: a group's three weights are independent. The same group can be a dominant driver of one pillar and a minor input to another — e.g. a group may carry most of the Exposure weight while contributing little to Risk.*

### Signal Architecture Rationale
This configuration contains **51 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `DIRECT_OBSERVABLE` (21 signals): Highest confidence
- `INFERRED_PROXY` (30 signals): Medium confidence

**Signal Count by Group:**
- `public_record`: 14 signals
- `corporate_footprint`: 13 signals
- `network_authority`: 6 signals
- `technical_infrastructure`: 6 signals
- `behavioural`: 5 signals
- `structured_data`: 4 signals
- `operator_type`: 1 signals
- `operation_segment`: 1 signals
- `geographic_focus`: 1 signals

**Selection Rationale:**
- 41% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Detail by Group
> *Each signal is an objectively observable data point. The weights show how strongly that signal informs each assessment pillar; correlation direction indicates whether a higher observed value increases (+) or decreases (-) the assessed exposure.*

#### Network Authority
*Quality of partnerships and industry relationships*

| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `partner_quality` | INFERRED_PROXY | 0.25 | 0.15 / 0.10 | 0.00 | + |
| `contractor_quality` | INFERRED_PROXY | 0.20 | 0.15 / 0.00 | 0.00 | + |
| `insurance_history` | INFERRED_PROXY | 0.20 | 0.10 / 0.10 | 0.00 | + |
| `regulator_relationship` | INFERRED_PROXY | 0.15 | 0.10 / 0.00 | 0.00 | + |
| `industry_association` | DIRECT_OBSERVABLE | 0.10 | 0.00 / 0.00 | 0.00 | + |
| `banking_relationship` | INFERRED_PROXY | 0.10 | 0.00 / 0.00 | 0.00 | + |

#### Safety Performance
*OSHA metrics*

| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `osha_trir` | DIRECT_OBSERVABLE | 0.20 | 0.20 / 0.10 | 0.00 | + |
| `phmsa_compliance` | DIRECT_OBSERVABLE | 0.30 | 0.20 / 0.20 | 0.00 | + |
| `process_safety` | INFERRED_PROXY | 0.15 | 0.15 / 0.15 | 0.00 | + |
| `fatality` | DIRECT_OBSERVABLE | 0.15 | 0.00 / 0.25 | 0.00 | + |
| `major_incident` | DIRECT_OBSERVABLE | 0.10 | 0.10 / 0.20 | 0.00 | + |
| `near_miss` | INFERRED_PROXY | 0.10 | 0.10 / 0.00 | 0.00 | + |
| `epa_violation` | DIRECT_OBSERVABLE | 0.20 | 0.15 / 0.20 | 0.00 | + |
| `spill_history` | DIRECT_OBSERVABLE | 0.25 | 0.20 / 0.30 | 0.00 | + |
| `emissions_compliance` | DIRECT_OBSERVABLE | 0.15 | 0.10 / 0.00 | 0.00 | + |
| `methane` | INFERRED_PROXY | 0.20 | 0.10 / 0.00 | 0.00 | + |
| `flaring` | DIRECT_OBSERVABLE | 0.10 | 0.05 / 0.00 | 0.00 | + |
| `remediation` | INFERRED_PROXY | 0.10 | 0.00 / 0.15 | 0.00 | + |
| `nrc_inspection_findings` | DIRECT_OBSERVABLE | 0.03 | 0.03 / 0.03 | 0.00 | + |
| `nrc_enforcement_action_history` | DIRECT_OBSERVABLE | 0.03 | 0.03 / 0.00 | 0.00 | + |

#### Operational Telemetry
*Inline inspection*

| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `inline_inspection` | INFERRED_PROXY | 0.25 | 0.20 / 0.15 | 0.15 | + |
| `cathodic_protection` | INFERRED_PROXY | 0.20 | 0.15 / 0.10 | 0.10 | + |
| `scada_maturity` | INFERRED_PROXY | 0.20 | 0.15 / 0.00 | 0.15 | + |
| `throughput_consistency` | INFERRED_PROXY | 0.10 | 0.10 / 0.00 | 0.15 | + |
| `maintenance_pattern` | INFERRED_PROXY | 0.15 | 0.15 / 0.00 | 0.10 | + |
| `facility_activity` | INFERRED_PROXY | 0.10 | 0.00 / 0.00 | 0.15 | + |

#### Financial Stability
*Credit rating*

| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `credit_rating` | DIRECT_OBSERVABLE | 0.30 | 0.00 / 0.20 | 0.00 | + |
| `leverage` | DIRECT_OBSERVABLE | 0.25 | 0.00 / 0.20 | 0.00 | - |
| `capex_trend` | DIRECT_OBSERVABLE | 0.20 | 0.00 / 0.00 | 0.10 | + |
| `restructuring` | DIRECT_OBSERVABLE | 0.15 | 0.00 / 0.20 | 0.00 | + |
| `aro_coverage` | INFERRED_PROXY | 0.10 | 0.00 / 0.00 | 0.05 | + |

#### Asset Portfolio
*Pipeline vintage*

| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `asset_age` | INFERRED_PROXY | 0.15 | 0.15 / 0.10 | 0.10 | - |
| `concentration` | INFERRED_PROXY | 0.10 | 0.00 / 0.10 | 0.15 | - |
| `technology_profile` | INFERRED_PROXY | 0.10 | 0.10 / 0.00 | 0.10 | - |
| `permit_status` | DIRECT_OBSERVABLE | 0.10 | 0.00 / 0.00 | 0.00 | + |
| `right_of_way` | INFERRED_PROXY | 0.20 | 0.15 / 0.10 | 0.15 | + |
| `pipeline_vintage` | INFERRED_PROXY | 0.25 | 0.20 / 0.15 | 0.20 | - |
| `complexity` | INFERRED_PROXY | 0.10 | 0.10 / 0.10 | 0.15 | - |
| `esg_reporting` | INFERRED_PROXY | 0.20 | 0.15 / 0.00 | 0.00 | + |
| `safety_communication` | DIRECT_OBSERVABLE | 0.25 | 0.20 / 0.00 | 0.00 | + |
| `disclosure_quality` | INFERRED_PROXY | 0.15 | 0.15 / 0.00 | 0.00 | + |
| `hse_leadership` | INFERRED_PROXY | 0.15 | 0.00 / 0.15 | 0.00 | + |
| `technical_hiring` | INFERRED_PROXY | 0.15 | 0.00 / 0.00 | 0.00 | + |
| `industry_presence` | DIRECT_OBSERVABLE | 0.10 | 0.00 / 0.00 | 0.00 | + |

#### Structured Data
*Third-party ESG ratings and benchmarks*

| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `esg_rating` | DIRECT_OBSERVABLE | 0.40 | 0.00 / 0.30 | 0.00 | + |
| `benchmark` | INFERRED_PROXY | 0.35 | 0.00 / 0.35 | 0.00 | + |
| `credit` | DIRECT_OBSERVABLE | 0.25 | 0.00 / 0.35 | 0.00 | + |
| `decommissioning_trust_funding` | DIRECT_OBSERVABLE | 0.03 | 0.00 / 0.03 | 0.00 | - |

#### operator_type
**Categorical signal `operator_type`** — proxy tier: `INFERRED_PROXY`, source: `metadata.operator_type`

| Category | Label | Applied Factor |
|----------|-------|----------------|
| `MIDSTREAM_MLP` | Midstream MLP | 0.9 |
| `MIDSTREAM_CORP` | Midstream Corporation | 0.95 |
| `INTEGRATED` | Integrated Energy | 0.85 |
| `UTILITY` | Utility | 0.9 |
| `INDEPENDENT` | Independent | 1.1 |
| `OTHER` | Unknown | 1.0 |

#### operation_segment
**Categorical signal `operation_segment`** — proxy tier: `INFERRED_PROXY`, source: `metadata.operation_segment`

| Category | Label | Applied Factor |
|----------|-------|----------------|
| `MIDSTREAM_PIPELINE` | Pipeline | 1.0 |
| `MIDSTREAM_PROCESSING` | Processing | 1.1 |
| `MIDSTREAM_STORAGE` | Storage | 0.95 |
| `OTHER` | Other | 1.1 |

#### geographic_focus
**Categorical signal `geographic_focus`** — proxy tier: `INFERRED_PROXY`, source: `metadata.geographic_focus`

| Category | Label | Applied Factor |
|----------|-------|----------------|
| `US_ONSHORE` | US Onshore | 1.0 |
| `US_OFFSHORE` | US Offshore | 1.2 |
| `NORTH_SEA` | North Sea | 1.1 |
| `ASIA_PACIFIC` | Asia Pacific | 1.1 |
| `OTHER` | Other | 1.1 |

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 | Safety Performance | 0.87 | 0.35 | 0.35 | 0.17 |
| 2 | Asset Portfolio | 0.73 | 0.20 | 0.25 | 0.28 |
| 3 | Operational Telemetry | 0.70 | 0.20 | 0.25 | 0.25 |
| 4 | Financial Stability | 0.50 | 0.15 | 0.10 | 0.25 |
| 5 | Network Authority | 0.11 | 0.05 | 0.03 | 0.03 |
| 6 | Structured Data | 0.09 | 0.05 | 0.02 | 0.02 |

**Primary Assessment Driver:** `Safety Performance` with combined weight of 0.87
**Secondary Driver:** `Asset Portfolio` with combined weight of 0.73

### Three-Layer Pricing Translation
> *How each pillar's tier score becomes a concrete underwriting action or pricing modifier. This is the bridge between signal observation and premium.*

**Risk -> Underwriting Action & Base Rate**

| Tier | Score Band | Action | Rate / Method |
|------|-----------|--------|---------------|
| PREFERRED | 800-1000 | APPROVE | 0.05% (MULTIPLIER) |
| STANDARD_PLUS | 650-799 | APPROVE | 0.08% (MULTIPLIER) |
| STANDARD | 500-649 | REFER | 0.12% (MULTIPLIER) |
| SUBSTANDARD | 350-499 | REFER | 0.2% (MULTIPLIER) |
| DECLINE | 0-349 | DECLINE | 0.35% (MULTIPLIER) |

**Loss -> Frequency & Severity Modifiers**

| Tier | Score Band | Frequency Modifier | Severity Modifier |
|------|-----------|--------------------|-------------------|
| VERY_LOW | 80-100 | 0.75 | 0.8 |
| LOW | 60-79 | 0.88 | 0.9 |
| MODERATE | 40-59 | 1.0 | 1.0 |
| ELEVATED | 20-39 | 1.12 | 1.1 |
| HIGH | 0-19 | 1.25 | 1.25 |

*Loss modifier is bounded: floor 0.6, cap 1.45.*

**Exposure (size) -> Scale Modifier**

| Band | Score Band | Modifier | Implied Value Range |
|------|-----------|----------|---------------------|
| SMALL | 0-20 | 0.7 | n/a |
| MEDIUM | 21-40 | 0.9 | n/a |
| LARGE | 41-60 | 1.1 | n/a |
| VERY_LARGE | 61-80 | 1.4 | n/a |
| MEGA | 81-100 | 1.9 | n/a |

**Exposure (complexity) -> Scale Modifier**

| Band | Score Band | Modifier | Implied Value Range |
|------|-----------|----------|---------------------|
| SIMPLE | 0-20 | 0.85 | n/a |
| MODERATE | 21-40 | 0.95 | n/a |
| COMPLEX | 41-60 | 1.05 | n/a |
| HIGHLY_COMPLEX | 61-80 | 1.2 | n/a |
| EXTREMELY_COMPLEX | 81-100 | 1.4 | n/a |

### Theoretical Premium Calculation (Tier 3 Standard)
> *Per the DSI Premium Calculation Methodology v2.0, the core formula is:*
> *P_final = (Base × Rate) × ILF_relativity × Deductible_Factor × Modifiers*

**1. The Pricing Anchor:** The Base Rate of `0.12%` on `tiv` purchases exactly a `$10,000,000` Limit with a `$100,000` Deductible.
**2. Theoretical Execution:**
  - Assume `tiv` = $10,000,000
  - Base Premium = $10,000,000 × 0.0012 = **$12,000**
  - If the client requests the Anchor Limit/Deductible, the factors are 1.00, resulting in a technical premium of **$12,000**.

---

## Model: `energy_downstream`
*Refining and petrochemical operations*

### Routing Protocol (Multiplexer)
- `operation_segment in ['DOWNSTREAM_REFINING', 'DOWNSTREAM_PETROCHEMICAL']`

### Three-Layer Weight Distribution
> *DSI requires that weights for Risk, Loss, and Exposure each sum to 1.0 across all signal groups.*

**Validation:** PASS

| Group | Risk | Loss | Exposure |
|-------|------|------|----------|
| Network Authority | 0.05 | 0.03 | 0.03 |
| Safety Performance | 0.40 | 0.45 | 0.17 |
| Operational Telemetry | 0.15 | 0.15 | 0.20 |
| Financial Stability | 0.10 | 0.07 | 0.15 |
| Asset Portfolio | 0.25 | 0.25 | 0.40 |
| Structured Data | 0.05 | 0.05 | 0.05 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

**Group Definitions:**
- **Network Authority:** Quality of partnerships and industry relationships
- **Safety Performance:** OSHA metrics
- **Operational Telemetry:** Mechanical integrity
- **Financial Stability:** Credit rating
- **Asset Portfolio:** Turnaround compliance
- **Structured Data:** Third-party ESG ratings and benchmarks

*Reading the table: a group's three weights are independent. The same group can be a dominant driver of one pillar and a minor input to another — e.g. a group may carry most of the Exposure weight while contributing little to Risk.*

### Signal Architecture Rationale
This configuration contains **49 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `DIRECT_OBSERVABLE` (18 signals): Highest confidence
- `INFERRED_PROXY` (31 signals): Medium confidence

**Signal Count by Group:**
- `corporate_footprint`: 13 signals
- `public_record`: 12 signals
- `network_authority`: 6 signals
- `technical_infrastructure`: 6 signals
- `behavioural`: 6 signals
- `structured_data`: 3 signals
- `operator_type`: 1 signals
- `operation_segment`: 1 signals
- `geographic_focus`: 1 signals

**Selection Rationale:**
- 37% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Detail by Group
> *Each signal is an objectively observable data point. The weights show how strongly that signal informs each assessment pillar; correlation direction indicates whether a higher observed value increases (+) or decreases (-) the assessed exposure.*

#### Network Authority
*Quality of partnerships and industry relationships*

| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `partner_quality` | INFERRED_PROXY | 0.25 | 0.15 / 0.10 | 0.00 | + |
| `contractor_quality` | INFERRED_PROXY | 0.20 | 0.15 / 0.00 | 0.00 | + |
| `insurance_history` | INFERRED_PROXY | 0.20 | 0.10 / 0.10 | 0.00 | + |
| `regulator_relationship` | INFERRED_PROXY | 0.15 | 0.10 / 0.00 | 0.00 | + |
| `industry_association` | DIRECT_OBSERVABLE | 0.10 | 0.00 / 0.00 | 0.00 | + |
| `banking_relationship` | INFERRED_PROXY | 0.10 | 0.00 / 0.00 | 0.00 | + |

#### Safety Performance
*OSHA metrics*

| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `osha_trir` | DIRECT_OBSERVABLE | 0.15 | 0.15 / 0.10 | 0.00 | + |
| `psm_audit_findings` | DIRECT_OBSERVABLE | 0.25 | 0.20 / 0.25 | 0.00 | + |
| `process_safety` | INFERRED_PROXY | 0.20 | 0.20 / 0.30 | 0.00 | + |
| `fatality` | DIRECT_OBSERVABLE | 0.15 | 0.00 / 0.25 | 0.00 | + |
| `major_incident` | DIRECT_OBSERVABLE | 0.15 | 0.15 / 0.30 | 0.00 | + |
| `near_miss` | INFERRED_PROXY | 0.10 | 0.10 / 0.00 | 0.00 | + |
| `epa_violation` | DIRECT_OBSERVABLE | 0.25 | 0.20 / 0.25 | 0.00 | + |
| `spill_history` | DIRECT_OBSERVABLE | 0.20 | 0.15 / 0.20 | 0.00 | + |
| `emissions_compliance` | DIRECT_OBSERVABLE | 0.20 | 0.15 / 0.00 | 0.00 | + |
| `flaring` | DIRECT_OBSERVABLE | 0.15 | 0.10 / 0.00 | 0.00 | + |
| `methane` | INFERRED_PROXY | 0.10 | 0.00 / 0.00 | 0.00 | + |
| `remediation` | INFERRED_PROXY | 0.10 | 0.00 / 0.15 | 0.00 | + |

#### Operational Telemetry
*Mechanical integrity*

| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `mechanical_integrity` | INFERRED_PROXY | 0.25 | 0.20 / 0.20 | 0.20 | + |
| `production_consistency` | INFERRED_PROXY | 0.15 | 0.10 / 0.00 | 0.15 | + |
| `maintenance_pattern` | INFERRED_PROXY | 0.20 | 0.15 / 0.00 | 0.15 | + |
| `facility_activity` | INFERRED_PROXY | 0.15 | 0.00 / 0.00 | 0.15 | + |
| `operational_efficiency` | INFERRED_PROXY | 0.15 | 0.10 / 0.00 | 0.15 | + |
| `scada_maturity` | INFERRED_PROXY | 0.10 | 0.10 / 0.00 | 0.10 | + |

#### Financial Stability
*Credit rating*

| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `credit_rating` | DIRECT_OBSERVABLE | 0.30 | 0.00 / 0.20 | 0.00 | + |
| `leverage` | DIRECT_OBSERVABLE | 0.25 | 0.00 / 0.15 | 0.00 | - |
| `capex_trend` | DIRECT_OBSERVABLE | 0.15 | 0.00 / 0.00 | 0.10 | + |
| `restructuring` | DIRECT_OBSERVABLE | 0.15 | 0.00 / 0.20 | 0.00 | + |
| `aro_coverage` | INFERRED_PROXY | 0.10 | 0.00 / 0.00 | 0.05 | + |
| `bi_exposure_ratio` | INFERRED_PROXY | 0.05 | 0.00 / 0.15 | 0.10 | - |

#### Asset Portfolio
*Turnaround compliance*

| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `asset_age` | INFERRED_PROXY | 0.15 | 0.10 / 0.10 | 0.10 | - |
| `concentration` | INFERRED_PROXY | 0.15 | 0.00 / 0.20 | 0.15 | - |
| `technology_profile` | INFERRED_PROXY | 0.10 | 0.10 / 0.00 | 0.15 | - |
| `permit_status` | DIRECT_OBSERVABLE | 0.05 | 0.00 / 0.00 | 0.00 | + |
| `turnaround_compliance` | INFERRED_PROXY | 0.20 | 0.15 / 0.20 | 0.15 | + |
| `feedstock_complexity` | INFERRED_PROXY | 0.20 | 0.15 / 0.15 | 0.20 | - |
| `process_unit_count` | INFERRED_PROXY | 0.15 | 0.10 / 0.00 | 0.15 | - |
| `esg_reporting` | INFERRED_PROXY | 0.20 | 0.15 / 0.00 | 0.00 | + |
| `safety_communication` | DIRECT_OBSERVABLE | 0.25 | 0.20 / 0.00 | 0.00 | + |
| `disclosure_quality` | INFERRED_PROXY | 0.15 | 0.15 / 0.00 | 0.00 | + |
| `hse_leadership` | INFERRED_PROXY | 0.15 | 0.00 / 0.15 | 0.00 | + |
| `technical_hiring` | INFERRED_PROXY | 0.15 | 0.00 / 0.00 | 0.00 | + |
| `industry_presence` | DIRECT_OBSERVABLE | 0.10 | 0.00 / 0.00 | 0.00 | + |

#### Structured Data
*Third-party ESG ratings and benchmarks*

| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `esg_rating` | DIRECT_OBSERVABLE | 0.40 | 0.00 / 0.30 | 0.00 | + |
| `benchmark` | INFERRED_PROXY | 0.35 | 0.00 / 0.35 | 0.00 | + |
| `credit` | DIRECT_OBSERVABLE | 0.25 | 0.00 / 0.35 | 0.00 | + |

#### operator_type
**Categorical signal `operator_type`** — proxy tier: `INFERRED_PROXY`, source: `metadata.operator_type`

| Category | Label | Applied Factor |
|----------|-------|----------------|
| `SUPERMAJOR` | Supermajor | 0.8 |
| `MAJOR_INTEGRATED` | Major Integrated | 0.85 |
| `LARGE_INDEPENDENT` | Large Independent Refiner | 0.95 |
| `MID_INDEPENDENT` | Mid-Size Refiner | 1.1 |
| `PETROCHEMICAL` | Petrochemical Specialist | 1.05 |
| `NATIONAL_OIL` | National Oil Company | 0.9 |
| `OTHER` | Unknown | 1.0 |

#### operation_segment
**Categorical signal `operation_segment`** — proxy tier: `INFERRED_PROXY`, source: `metadata.operation_segment`

| Category | Label | Applied Factor |
|----------|-------|----------------|
| `DOWNSTREAM_REFINING` | Refining | 1.0 |
| `DOWNSTREAM_PETROCHEMICAL` | Petrochemical | 1.15 |
| `OTHER` | Other | 1.1 |

#### geographic_focus
**Categorical signal `geographic_focus`** — proxy tier: `INFERRED_PROXY`, source: `metadata.geographic_focus`

| Category | Label | Applied Factor |
|----------|-------|----------------|
| `US_GULF_COAST` | US Gulf Coast | 1.0 |
| `US_OTHER` | US Other | 1.05 |
| `EUROPE` | Europe | 0.95 |
| `ASIA_PACIFIC` | Asia Pacific | 1.1 |
| `MIDDLE_EAST` | Middle East | 1.05 |
| `OTHER` | Other | 1.1 |

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 | Safety Performance | 1.02 | 0.40 | 0.45 | 0.17 |
| 2 | Asset Portfolio | 0.90 | 0.25 | 0.25 | 0.40 |
| 3 | Operational Telemetry | 0.50 | 0.15 | 0.15 | 0.20 |
| 4 | Financial Stability | 0.32 | 0.10 | 0.07 | 0.15 |
| 5 | Structured Data | 0.15 | 0.05 | 0.05 | 0.05 |
| 6 | Network Authority | 0.11 | 0.05 | 0.03 | 0.03 |

**Primary Assessment Driver:** `Safety Performance` with combined weight of 1.02
**Secondary Driver:** `Asset Portfolio` with combined weight of 0.90

### Three-Layer Pricing Translation
> *How each pillar's tier score becomes a concrete underwriting action or pricing modifier. This is the bridge between signal observation and premium.*

**Risk -> Underwriting Action & Base Rate**

| Tier | Score Band | Action | Rate / Method |
|------|-----------|--------|---------------|
| PREFERRED | 800-1000 | APPROVE | 0.1% (MULTIPLIER) |
| STANDARD_PLUS | 650-799 | APPROVE | 0.15% (MULTIPLIER) |
| STANDARD | 500-649 | REFER | 0.22% (MULTIPLIER) |
| SUBSTANDARD | 350-499 | REFER | 0.35% (MULTIPLIER) |
| DECLINE | 0-349 | DECLINE | 0.55% (MULTIPLIER) |

**Loss -> Frequency & Severity Modifiers**

| Tier | Score Band | Frequency Modifier | Severity Modifier |
|------|-----------|--------------------|-------------------|
| VERY_LOW | 80-100 | 0.7 | 0.75 |
| LOW | 60-79 | 0.85 | 0.88 |
| MODERATE | 40-59 | 1.0 | 1.0 |
| ELEVATED | 20-39 | 1.15 | 1.2 |
| HIGH | 0-19 | 1.35 | 1.4 |

*Loss modifier is bounded: floor 0.5, cap 1.6.*

**Exposure (size) -> Scale Modifier**

| Band | Score Band | Modifier | Implied Value Range |
|------|-----------|----------|---------------------|
| SMALL | 0-20 | 0.75 | n/a |
| MEDIUM | 21-40 | 1.0 | n/a |
| LARGE | 41-60 | 1.3 | n/a |
| VERY_LARGE | 61-80 | 1.8 | n/a |
| MEGA | 81-100 | 2.5 | n/a |

**Exposure (complexity) -> Scale Modifier**

| Band | Score Band | Modifier | Implied Value Range |
|------|-----------|----------|---------------------|
| SIMPLE | 0-20 | 0.85 | n/a |
| MODERATE | 21-40 | 0.95 | n/a |
| COMPLEX | 41-60 | 1.1 | n/a |
| HIGHLY_COMPLEX | 61-80 | 1.3 | n/a |
| EXTREMELY_COMPLEX | 81-100 | 1.6 | n/a |

### Theoretical Premium Calculation (Tier 3 Standard)
> *Per the DSI Premium Calculation Methodology v2.0, the core formula is:*
> *P_final = (Base × Rate) × ILF_relativity × Deductible_Factor × Modifiers*

**1. The Pricing Anchor:** The Base Rate of `0.22%` on `tiv` purchases exactly a `$10,000,000` Limit with a `$100,000` Deductible.
**2. Theoretical Execution:**
  - Assume `tiv` = $10,000,000
  - Base Premium = $10,000,000 × 0.0022 = **$22,000**
  - If the client requests the Anchor Limit/Deductible, the factors are 1.00, resulting in a technical premium of **$22,000**.

---

## Model: `energy_offshore_wind`
*Offshore wind farms — maritime construction + technology risk*

### Routing Protocol (Multiplexer)
- `operation_segment == RENEWABLE`
- `technology_type == OFFSHORE_WIND`

### Three-Layer Weight Distribution
> *DSI requires that weights for Risk, Loss, and Exposure each sum to 1.0 across all signal groups.*

**Validation:** PASS

| Group | Risk | Loss | Exposure |
|-------|------|------|----------|
| Network Authority | 0.05 | 0.03 | 0.02 |
| Safety Performance | 0.15 | 0.15 | 0.10 |
| Construction Quality | 0.35 | 0.40 | 0.33 |
| Financial Stability | 0.10 | 0.10 | 0.15 |
| Asset Portfolio | 0.30 | 0.27 | 0.38 |
| Structured Data | 0.05 | 0.05 | 0.02 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

**Group Definitions:**
- **Network Authority:** Quality of partnerships, contractors, and industry relationships
- **Safety Performance:** OSHA metrics, incidents, crew transfer safety, process safety
- **Construction Quality:** EPC contractor quality, commissioning defects, installation vessel quality
- **Financial Stability:** Credit rating, leverage, PPA quality, offtake contract quality
- **Asset Portfolio:** Technology maturity, turbine platform, cable route, marine weather, NatCat exposure
- **Structured Data:** Third-party ESG ratings and industry benchmarks

*Reading the table: a group's three weights are independent. The same group can be a dominant driver of one pillar and a minor input to another — e.g. a group may carry most of the Exposure weight while contributing little to Risk.*

### Signal Architecture Rationale
This configuration contains **46 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `DIRECT_OBSERVABLE` (20 signals): Highest confidence
- `INFERRED_PROXY` (25 signals): Medium confidence
- `COHORT_INFERENCE` (1 signals): Lowest confidence

**Signal Count by Group:**
- `corporate_footprint`: 12 signals
- `technical_infrastructure`: 8 signals
- `behavioural`: 7 signals
- `network_authority`: 6 signals
- `public_record`: 6 signals
- `structured_data`: 3 signals
- `operator_type`: 1 signals
- `foundation_type`: 1 signals
- `construction_phase`: 1 signals
- `geographic_focus`: 1 signals

**Selection Rationale:**
- 43% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Detail by Group
> *Each signal is an objectively observable data point. The weights show how strongly that signal informs each assessment pillar; correlation direction indicates whether a higher observed value increases (+) or decreases (-) the assessed exposure.*

#### Network Authority
*Quality of partnerships, contractors, and industry relationships*

| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `partner_quality` | INFERRED_PROXY | 0.25 | 0.10 / 0.15 | 0.00 | + |
| `contractor_quality` | INFERRED_PROXY | 0.20 | 0.15 / 0.00 | 0.00 | + |
| `insurance_history` | INFERRED_PROXY | 0.20 | 0.10 / 0.10 | 0.00 | + |
| `regulator_relationship` | INFERRED_PROXY | 0.15 | 0.10 / 0.00 | 0.00 | + |
| `industry_association` | DIRECT_OBSERVABLE | 0.10 | 0.00 / 0.00 | 0.00 | + |
| `banking_relationship` | INFERRED_PROXY | 0.10 | 0.00 / 0.00 | 0.00 | + |

#### Safety Performance
*OSHA metrics, incidents, crew transfer safety, process safety*

| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `osha_trir` | DIRECT_OBSERVABLE | 0.20 | 0.20 / 0.10 | 0.00 | + |
| `process_safety` | INFERRED_PROXY | 0.20 | 0.20 / 0.30 | 0.00 | + |
| `fatality` | DIRECT_OBSERVABLE | 0.15 | 0.00 / 0.30 | 0.00 | + |
| `major_incident` | DIRECT_OBSERVABLE | 0.15 | 0.15 / 0.35 | 0.00 | + |
| `near_miss` | INFERRED_PROXY | 0.05 | 0.10 / 0.00 | 0.00 | + |
| `crew_transfer_safety` | INFERRED_PROXY | 0.25 | 0.15 / 0.15 | 0.00 | + |

#### Construction Quality
*EPC contractor quality, commissioning defects, installation vessel quality*

| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `epc_contractor_quality` | INFERRED_PROXY | 0.30 | 0.30 / 0.25 | 0.00 | + |
| `commissioning_defects` | INFERRED_PROXY | 0.25 | 0.25 / 0.20 | 0.00 | + |
| `epc_track_record` | INFERRED_PROXY | 0.20 | 0.20 / 0.25 | 0.00 | + |
| `supply_chain_quality` | INFERRED_PROXY | 0.10 | 0.10 / 0.15 | 0.00 | + |
| `installation_vessel_quality` | INFERRED_PROXY | 0.15 | 0.15 / 0.15 | 0.00 | + |
| `capacity_factor` | DIRECT_OBSERVABLE | 0.25 | 0.25 / 0.00 | 0.00 | + |
| `grid_interconnection` | INFERRED_PROXY | 0.25 | 0.25 / 0.00 | 0.00 | + |
| `degradation_rate` | DIRECT_OBSERVABLE | 0.25 | 0.25 / 0.00 | 0.00 | + |

#### Financial Stability
*Credit rating, leverage, PPA quality, offtake contract quality*

| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `credit_rating` | DIRECT_OBSERVABLE | 0.30 | 0.00 / 0.20 | 0.00 | + |
| `leverage` | DIRECT_OBSERVABLE | 0.25 | 0.00 / 0.15 | 0.00 | - |
| `capex_trend` | DIRECT_OBSERVABLE | 0.15 | 0.00 / 0.00 | 0.10 | + |
| `restructuring` | DIRECT_OBSERVABLE | 0.10 | 0.00 / 0.20 | 0.00 | + |
| `aro_coverage` | INFERRED_PROXY | 0.05 | 0.00 / 0.00 | 0.05 | + |
| `ppa_quality` | INFERRED_PROXY | 0.10 | 0.00 / 0.15 | 0.00 | + |
| `offtake_contract_quality` | INFERRED_PROXY | 0.05 | 0.00 / 0.15 | 0.00 | + |

#### Asset Portfolio
*Technology maturity, turbine platform, cable route, marine weather, NatCat exposure*

| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `technology_maturity` | INFERRED_PROXY | 0.20 | 0.15 / 0.15 | 0.00 | + |
| `warranty_coverage` | DIRECT_OBSERVABLE | 0.10 | 0.00 / 0.10 | 0.00 | + |
| `natcat_exposure` | DIRECT_OBSERVABLE | 0.15 | 0.15 / 0.10 | 0.15 | - |
| `turbine_platform_generation` | INFERRED_PROXY | 0.20 | 0.15 / 0.15 | 0.15 | + |
| `cable_route_risk` | INFERRED_PROXY | 0.15 | 0.15 / 0.10 | 0.10 | - |
| `marine_weather_exposure` | DIRECT_OBSERVABLE | 0.20 | 0.20 / 0.15 | 0.10 | - |
| `esg_reporting` | DIRECT_OBSERVABLE | 0.20 | 0.00 / 0.00 | 0.00 | + |
| `safety_communication` | DIRECT_OBSERVABLE | 0.20 | 0.10 / 0.00 | 0.00 | + |
| `disclosure_quality` | INFERRED_PROXY | 0.15 | 0.00 / 0.00 | 0.00 | + |
| `hse_leadership` | INFERRED_PROXY | 0.15 | 0.10 / 0.00 | 0.00 | + |
| `technical_hiring` | INFERRED_PROXY | 0.15 | 0.00 / 0.00 | 0.10 | + |
| `industry_presence` | DIRECT_OBSERVABLE | 0.15 | 0.00 / 0.00 | 0.00 | + |

#### Structured Data
*Third-party ESG ratings and industry benchmarks*

| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `esg_rating` | DIRECT_OBSERVABLE | 0.40 | 0.00 / 0.00 | 0.00 | + |
| `benchmark` | COHORT_INFERENCE | 0.35 | 0.15 / 0.15 | 0.00 | + |
| `credit` | DIRECT_OBSERVABLE | 0.25 | 0.00 / 0.20 | 0.00 | + |

#### operator_type
**Categorical signal `operator_type`** — proxy tier: `INFERRED_PROXY`, source: `metadata.operator_type`

| Category | Label | Applied Factor |
|----------|-------|----------------|
| `UTILITY_DEVELOPER` | Utility Developer | 0.85 |
| `SPECIALIST_DEVELOPER` | Specialist Developer | 0.9 |
| `OIL_GAS_TRANSITION` | Oil & Gas Transition | 1.1 |
| `FINANCIAL_SPONSOR` | Financial Sponsor | 1.2 |
| `FIRST_TIME_DEVELOPER` | First-Time Developer | 1.5 |
| `OTHER` | UNKNOWN | 1.0 |

#### foundation_type
**Categorical signal `foundation_type`** — proxy tier: `DIRECT_OBSERVABLE`, source: `metadata.foundation_type`

| Category | Label | Applied Factor |
|----------|-------|----------------|
| `MONOPILE` | Monopile (proven) | 0.9 |
| `JACKET` | Jacket (proven) | 0.95 |
| `GRAVITY_BASE` | Gravity Base | 1.0 |
| `FLOATING_SPAR` | Floating Spar (emerging) | 1.3 |
| `FLOATING_SEMI` | Floating Semi-Sub (emerging) | 1.35 |
| `FLOATING_TLP` | Floating TLP (first-of-kind) | 1.5 |
| `OTHER` | Unknown | 1.0 |

#### construction_phase
**Categorical signal `construction_phase`** — proxy tier: `DIRECT_OBSERVABLE`, source: `metadata.construction_phase`

| Category | Label | Applied Factor |
|----------|-------|----------------|
| `PRE_CONSTRUCTION` | Pre-Construction | 1.5 |
| `CONSTRUCTION` | Under Construction | 1.3 |
| `COMMISSIONING` | Commissioning | 1.15 |
| `EARLY_OPERATION` | Early Operation (<3 years) | 1.05 |
| `MATURE_OPERATION` | Mature Operation (3+ years) | 0.9 |
| `OTHER` | Unknown | 1.0 |

#### geographic_focus
**Categorical signal `geographic_focus`** — proxy tier: `INFERRED_PROXY`, source: `metadata.geographic_focus`

| Category | Label | Applied Factor |
|----------|-------|----------------|
| `NORTH_SEA` | North Sea | 1.0 |
| `BALTIC` | Baltic | 0.95 |
| `US_ATLANTIC` | US Atlantic | 1.1 |
| `US_PACIFIC` | US Pacific | 1.15 |
| `ASIA_PACIFIC` | Asia Pacific | 1.05 |
| `OTHER` | Other | 1.1 |

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 | Construction Quality | 1.08 | 0.35 | 0.40 | 0.33 |
| 2 | Asset Portfolio | 0.95 | 0.30 | 0.27 | 0.38 |
| 3 | Safety Performance | 0.40 | 0.15 | 0.15 | 0.10 |
| 4 | Financial Stability | 0.35 | 0.10 | 0.10 | 0.15 |
| 5 | Structured Data | 0.12 | 0.05 | 0.05 | 0.02 |
| 6 | Network Authority | 0.10 | 0.05 | 0.03 | 0.02 |

**Primary Assessment Driver:** `Construction Quality` with combined weight of 1.08
**Secondary Driver:** `Asset Portfolio` with combined weight of 0.95

### Three-Layer Pricing Translation
> *How each pillar's tier score becomes a concrete underwriting action or pricing modifier. This is the bridge between signal observation and premium.*

**Risk -> Underwriting Action & Base Rate**

| Tier | Score Band | Action | Rate / Method |
|------|-----------|--------|---------------|
| PREFERRED | 800-1000 | APPROVE | 0.1% (MULTIPLIER) |
| STANDARD_PLUS | 650-799 | APPROVE | 0.14% (MULTIPLIER) |
| STANDARD | 500-649 | REFER | 0.2% (MULTIPLIER) |
| SUBSTANDARD | 350-499 | REFER | 0.32% (MULTIPLIER) |
| DECLINE | 0-349 | DECLINE | 0.5% (MULTIPLIER) |

**Loss -> Frequency & Severity Modifiers**

| Tier | Score Band | Frequency Modifier | Severity Modifier |
|------|-----------|--------------------|-------------------|
| VERY_LOW | 80-100 | 0.7 | 0.8 |
| LOW | 60-79 | 0.85 | 0.9 |
| MODERATE | 40-59 | 1.0 | 1.0 |
| ELEVATED | 20-39 | 1.15 | 1.15 |
| HIGH | 0-19 | 1.35 | 1.4 |

*Loss modifier is bounded: floor 0.55, cap 1.6.*

**Exposure (size) -> Scale Modifier**

| Band | Score Band | Modifier | Implied Value Range |
|------|-----------|----------|---------------------|
| SMALL | 0-20 | 0.75 | $0 - $500,000,000 |
| MEDIUM | 21-40 | 1.0 | $500,000,000 - $2,000,000,000 |
| LARGE | 41-60 | 1.3 | $2,000,000,000 - $5,000,000,000 |
| VERY_LARGE | 61-80 | 1.8 | $5,000,000,000 - $15,000,000,000 |
| MEGA | 81-100 | 2.5 | $15,000,000,000 - $50,000,000,000 |

**Exposure (complexity) -> Scale Modifier**

| Band | Score Band | Modifier | Implied Value Range |
|------|-----------|----------|---------------------|
| SIMPLE | 0-20 | 0.85 | n/a |
| MODERATE | 21-40 | 0.95 | n/a |
| COMPLEX | 41-60 | 1.1 | n/a |
| HIGHLY_COMPLEX | 61-80 | 1.3 | n/a |
| EXTREMELY_COMPLEX | 81-100 | 1.6 | n/a |

### Theoretical Premium Calculation (Tier 3 Standard)
> *Per the DSI Premium Calculation Methodology v2.0, the core formula is:*
> *P_final = (Base × Rate) × ILF_relativity × Deductible_Factor × Modifiers*

**1. The Pricing Anchor:** The Base Rate of `0.2%` on `tiv` purchases exactly a `$25,000,000` Limit with a `$250,000` Deductible.
**2. Theoretical Execution:**
  - Assume `tiv` = $10,000,000
  - Base Premium = $10,000,000 × 0.002 = **$20,000**
  - If the client requests the Anchor Limit/Deductible, the factors are 1.00, resulting in a technical premium of **$20,000**.

---

## Model: `energy_onshore_renewable`
*Onshore wind and utility-scale solar*

### Routing Protocol (Multiplexer)
- `operation_segment == RENEWABLE`
- `technology_type in ['ONSHORE_WIND', 'UTILITY_SOLAR', 'DISTRIBUTED_SOLAR']`

### Three-Layer Weight Distribution
> *DSI requires that weights for Risk, Loss, and Exposure each sum to 1.0 across all signal groups.*

**Validation:** PASS

| Group | Risk | Loss | Exposure |
|-------|------|------|----------|
| Network Authority | 0.05 | 0.03 | 0.03 |
| Safety Performance | 0.10 | 0.10 | 0.05 |
| Construction Quality | 0.30 | 0.32 | 0.32 |
| Financial Stability | 0.15 | 0.12 | 0.15 |
| Asset Portfolio | 0.35 | 0.36 | 0.43 |
| Structured Data | 0.05 | 0.07 | 0.02 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

**Group Definitions:**
- **Network Authority:** Quality of partnerships, contractors, and industry relationships
- **Safety Performance:** OSHA metrics, incidents, process safety events
- **Construction Quality:** EPC contractor quality, commissioning defects, construction track record
- **Financial Stability:** Credit rating, leverage, PPA quality, capex trends
- **Asset Portfolio:** Technology maturity, NatCat exposure, hail exposure, geographic spread
- **Structured Data:** Third-party ESG ratings and industry benchmarks

*Reading the table: a group's three weights are independent. The same group can be a dominant driver of one pillar and a minor input to another — e.g. a group may carry most of the Exposure weight while contributing little to Risk.*

### Signal Architecture Rationale
This configuration contains **45 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `DIRECT_OBSERVABLE` (21 signals): Highest confidence
- `INFERRED_PROXY` (23 signals): Medium confidence
- `COHORT_INFERENCE` (1 signals): Lowest confidence

**Signal Count by Group:**
- `corporate_footprint`: 12 signals
- `technical_infrastructure`: 9 signals
- `network_authority`: 6 signals
- `behavioural`: 6 signals
- `public_record`: 5 signals
- `structured_data`: 3 signals
- `operator_type`: 1 signals
- `technology_type`: 1 signals
- `construction_phase`: 1 signals
- `geographic_focus`: 1 signals

**Selection Rationale:**
- 47% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Detail by Group
> *Each signal is an objectively observable data point. The weights show how strongly that signal informs each assessment pillar; correlation direction indicates whether a higher observed value increases (+) or decreases (-) the assessed exposure.*

#### Network Authority
*Quality of partnerships, contractors, and industry relationships*

| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `partner_quality` | INFERRED_PROXY | 0.25 | 0.10 / 0.15 | 0.00 | + |
| `contractor_quality` | INFERRED_PROXY | 0.20 | 0.15 / 0.00 | 0.00 | + |
| `insurance_history` | INFERRED_PROXY | 0.20 | 0.10 / 0.10 | 0.00 | + |
| `regulator_relationship` | INFERRED_PROXY | 0.15 | 0.10 / 0.00 | 0.00 | + |
| `industry_association` | DIRECT_OBSERVABLE | 0.10 | 0.00 / 0.00 | 0.00 | + |
| `banking_relationship` | INFERRED_PROXY | 0.10 | 0.00 / 0.00 | 0.00 | + |

#### Safety Performance
*OSHA metrics, incidents, process safety events*

| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `osha_trir` | DIRECT_OBSERVABLE | 0.20 | 0.20 / 0.10 | 0.00 | + |
| `process_safety` | INFERRED_PROXY | 0.20 | 0.20 / 0.30 | 0.00 | + |
| `fatality` | DIRECT_OBSERVABLE | 0.15 | 0.00 / 0.30 | 0.00 | + |
| `major_incident` | DIRECT_OBSERVABLE | 0.15 | 0.15 / 0.35 | 0.00 | + |
| `near_miss` | INFERRED_PROXY | 0.30 | 0.10 / 0.00 | 0.00 | + |

#### Construction Quality
*EPC contractor quality, commissioning defects, construction track record*

| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `epc_contractor_quality` | INFERRED_PROXY | 0.30 | 0.30 / 0.25 | 0.00 | + |
| `commissioning_defects` | INFERRED_PROXY | 0.25 | 0.25 / 0.20 | 0.00 | + |
| `epc_track_record` | INFERRED_PROXY | 0.20 | 0.20 / 0.25 | 0.00 | + |
| `supply_chain_quality` | INFERRED_PROXY | 0.25 | 0.25 / 0.30 | 0.00 | + |
| `capacity_factor` | DIRECT_OBSERVABLE | 0.25 | 0.25 / 0.00 | 0.00 | + |
| `grid_interconnection` | INFERRED_PROXY | 0.20 | 0.20 / 0.00 | 0.00 | + |
| `degradation_rate` | DIRECT_OBSERVABLE | 0.15 | 0.15 / 0.00 | 0.00 | + |
| `inverter_reliability` | INFERRED_PROXY | 0.20 | 0.20 / 0.00 | 0.00 | + |
| `curtailment_rate` | DIRECT_OBSERVABLE | 0.20 | 0.20 / 0.00 | 0.00 | + |

#### Financial Stability
*Credit rating, leverage, PPA quality, capex trends*

| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `credit_rating` | DIRECT_OBSERVABLE | 0.30 | 0.00 / 0.20 | 0.00 | + |
| `leverage` | DIRECT_OBSERVABLE | 0.25 | 0.00 / 0.15 | 0.00 | - |
| `capex_trend` | DIRECT_OBSERVABLE | 0.20 | 0.00 / 0.00 | 0.10 | + |
| `restructuring` | DIRECT_OBSERVABLE | 0.10 | 0.00 / 0.20 | 0.00 | + |
| `aro_coverage` | INFERRED_PROXY | 0.05 | 0.00 / 0.00 | 0.05 | + |
| `ppa_quality` | INFERRED_PROXY | 0.10 | 0.00 / 0.15 | 0.00 | + |

#### Asset Portfolio
*Technology maturity, NatCat exposure, hail exposure, geographic spread*

| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `technology_maturity` | INFERRED_PROXY | 0.15 | 0.15 / 0.10 | 0.00 | + |
| `warranty_coverage` | DIRECT_OBSERVABLE | 0.10 | 0.00 / 0.10 | 0.00 | + |
| `natcat_exposure` | DIRECT_OBSERVABLE | 0.15 | 0.15 / 0.10 | 0.15 | - |
| `hail_exposure` | DIRECT_OBSERVABLE | 0.20 | 0.20 / 0.15 | 0.10 | - |
| `panel_technology_vintage` | INFERRED_PROXY | 0.15 | 0.15 / 0.10 | 0.00 | - |
| `portfolio_geographic_spread` | INFERRED_PROXY | 0.25 | 0.15 / 0.15 | 0.15 | + |
| `esg_reporting` | DIRECT_OBSERVABLE | 0.20 | 0.00 / 0.00 | 0.00 | + |
| `safety_communication` | DIRECT_OBSERVABLE | 0.20 | 0.10 / 0.00 | 0.00 | + |
| `disclosure_quality` | INFERRED_PROXY | 0.15 | 0.00 / 0.00 | 0.00 | + |
| `hse_leadership` | INFERRED_PROXY | 0.15 | 0.10 / 0.00 | 0.00 | + |
| `technical_hiring` | INFERRED_PROXY | 0.15 | 0.00 / 0.00 | 0.10 | + |
| `industry_presence` | DIRECT_OBSERVABLE | 0.15 | 0.00 / 0.00 | 0.00 | + |

#### Structured Data
*Third-party ESG ratings and industry benchmarks*

| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `esg_rating` | DIRECT_OBSERVABLE | 0.40 | 0.00 / 0.00 | 0.00 | + |
| `benchmark` | COHORT_INFERENCE | 0.35 | 0.15 / 0.15 | 0.00 | + |
| `credit` | DIRECT_OBSERVABLE | 0.25 | 0.00 / 0.20 | 0.00 | + |

#### operator_type
**Categorical signal `operator_type`** — proxy tier: `INFERRED_PROXY`, source: `metadata.operator_type`

| Category | Label | Applied Factor |
|----------|-------|----------------|
| `UTILITY_DEVELOPER` | Utility Developer | 0.85 |
| `IPP` | Independent Power Producer | 0.9 |
| `COMMUNITY_DEVELOPER` | Community Developer | 1.1 |
| `FINANCIAL_SPONSOR` | Financial Sponsor | 1.15 |
| `OTHER` | UNKNOWN | 1.0 |

#### technology_type
**Categorical signal `technology_type`** — proxy tier: `DIRECT_OBSERVABLE`, source: `metadata.technology_type`

| Category | Label | Applied Factor |
|----------|-------|----------------|
| `ONSHORE_WIND` | Onshore Wind | 1.0 |
| `UTILITY_SOLAR` | Utility-Scale Solar | 0.95 |
| `DISTRIBUTED_SOLAR` | Distributed Solar | 1.1 |
| `OTHER` | Unknown | 1.0 |

#### construction_phase
**Categorical signal `construction_phase`** — proxy tier: `DIRECT_OBSERVABLE`, source: `metadata.construction_phase`

| Category | Label | Applied Factor |
|----------|-------|----------------|
| `PRE_CONSTRUCTION` | Pre-Construction | 1.5 |
| `CONSTRUCTION` | Under Construction | 1.3 |
| `COMMISSIONING` | Commissioning | 1.15 |
| `EARLY_OPERATION` | Early Operation (<3 years) | 1.05 |
| `MATURE_OPERATION` | Mature Operation (3+ years) | 0.9 |
| `OTHER` | Unknown | 1.0 |

#### geographic_focus
**Categorical signal `geographic_focus`** — proxy tier: `INFERRED_PROXY`, source: `metadata.geographic_focus`

| Category | Label | Applied Factor |
|----------|-------|----------------|
| `US_SOUTHWEST` | US Southwest | 0.95 |
| `US_MIDWEST` | US Midwest | 1.0 |
| `US_SOUTHEAST` | US Southeast | 1.05 |
| `US_NORTHEAST` | US Northeast | 1.0 |
| `EUROPE` | Europe | 0.95 |
| `OTHER` | Other | 1.0 |

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 | Asset Portfolio | 1.14 | 0.35 | 0.36 | 0.43 |
| 2 | Construction Quality | 0.94 | 0.30 | 0.32 | 0.32 |
| 3 | Financial Stability | 0.42 | 0.15 | 0.12 | 0.15 |
| 4 | Safety Performance | 0.25 | 0.10 | 0.10 | 0.05 |
| 5 | Structured Data | 0.14 | 0.05 | 0.07 | 0.02 |
| 6 | Network Authority | 0.11 | 0.05 | 0.03 | 0.03 |

**Primary Assessment Driver:** `Asset Portfolio` with combined weight of 1.14
**Secondary Driver:** `Construction Quality` with combined weight of 0.94

### Three-Layer Pricing Translation
> *How each pillar's tier score becomes a concrete underwriting action or pricing modifier. This is the bridge between signal observation and premium.*

**Risk -> Underwriting Action & Base Rate**

| Tier | Score Band | Action | Rate / Method |
|------|-----------|--------|---------------|
| PREFERRED | 800-1000 | APPROVE | 0.05% (MULTIPLIER) |
| STANDARD_PLUS | 650-799 | APPROVE | 0.08% (MULTIPLIER) |
| STANDARD | 500-649 | REFER | 0.13% (MULTIPLIER) |
| SUBSTANDARD | 350-499 | REFER | 0.22% (MULTIPLIER) |
| DECLINE | 0-349 | DECLINE | 0.35% (MULTIPLIER) |

**Loss -> Frequency & Severity Modifiers**

| Tier | Score Band | Frequency Modifier | Severity Modifier |
|------|-----------|--------------------|-------------------|
| VERY_LOW | 80-100 | 0.7 | 0.8 |
| LOW | 60-79 | 0.85 | 0.9 |
| MODERATE | 40-59 | 1.0 | 1.0 |
| ELEVATED | 20-39 | 1.15 | 1.15 |
| HIGH | 0-19 | 1.35 | 1.4 |

*Loss modifier is bounded: floor 0.55, cap 1.6.*

**Exposure (size) -> Scale Modifier**

| Band | Score Band | Modifier | Implied Value Range |
|------|-----------|----------|---------------------|
| SMALL | 0-20 | 0.75 | $0 - $500,000,000 |
| MEDIUM | 21-40 | 1.0 | $500,000,000 - $2,000,000,000 |
| LARGE | 41-60 | 1.3 | $2,000,000,000 - $5,000,000,000 |
| VERY_LARGE | 61-80 | 1.8 | $5,000,000,000 - $15,000,000,000 |
| MEGA | 81-100 | 2.5 | $15,000,000,000 - $50,000,000,000 |

**Exposure (complexity) -> Scale Modifier**

| Band | Score Band | Modifier | Implied Value Range |
|------|-----------|----------|---------------------|
| SIMPLE | 0-20 | 0.85 | n/a |
| MODERATE | 21-40 | 0.95 | n/a |
| COMPLEX | 41-60 | 1.1 | n/a |
| HIGHLY_COMPLEX | 61-80 | 1.3 | n/a |
| EXTREMELY_COMPLEX | 81-100 | 1.6 | n/a |

### Theoretical Premium Calculation (Tier 3 Standard)
> *Per the DSI Premium Calculation Methodology v2.0, the core formula is:*
> *P_final = (Base × Rate) × ILF_relativity × Deductible_Factor × Modifiers*

**1. The Pricing Anchor:** The Base Rate of `0.13%` on `tiv` purchases exactly a `$10,000,000` Limit with a `$500,000` Deductible.
**2. Theoretical Execution:**
  - Assume `tiv` = $10,000,000
  - Base Premium = $10,000,000 × 0.0013 = **$13,000**
  - If the client requests the Anchor Limit/Deductible, the factors are 1.00, resulting in a technical premium of **$13,000**.

---

## Model: `energy_storage`
*Battery energy storage systems (BESS) and green hydrogen — emerging technology risk with catastrophic severity potential*

### Routing Protocol (Multiplexer)
- `operation_segment == RENEWABLE`
- `technology_type in ['BATTERY_STORAGE', 'HYDROGEN']`

### Three-Layer Weight Distribution
> *DSI requires that weights for Risk, Loss, and Exposure each sum to 1.0 across all signal groups.*

**Validation:** PASS

| Group | Risk | Loss | Exposure |
|-------|------|------|----------|
| Network Authority | 0.05 | 0.03 | 0.02 |
| Safety Performance | 0.15 | 0.15 | 0.10 |
| Construction Quality | 0.25 | 0.30 | 0.25 |
| Financial Stability | 0.10 | 0.07 | 0.13 |
| Asset Portfolio | 0.40 | 0.38 | 0.45 |
| Structured Data | 0.05 | 0.07 | 0.05 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

**Group Definitions:**
- **Network Authority:** Quality of partnerships, contractors, and industry relationships
- **Safety Performance:** OSHA metrics, process safety, NFPA/UL safety standard compliance
- **Construction Quality:** EPC contractor experience, technology maturity, warranty coverage, commissioning quality
- **Financial Stability:** Credit rating, leverage, ARO coverage, capex trends
- **Asset Portfolio:** Thermal management, fire suppression, battery chemistry, hydrogen storage, cell format, NatCat exposure
- **Structured Data:** Third-party ESG ratings and industry benchmarks

*Reading the table: a group's three weights are independent. The same group can be a dominant driver of one pillar and a minor input to another — e.g. a group may carry most of the Exposure weight while contributing little to Risk.*

### Signal Architecture Rationale
This configuration contains **52 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `DIRECT_OBSERVABLE` (19 signals): Highest confidence
- `INFERRED_PROXY` (32 signals): Medium confidence
- `COHORT_INFERENCE` (1 signals): Lowest confidence

**Signal Count by Group:**
- `corporate_footprint`: 15 signals
- `technical_infrastructure`: 11 signals
- `network_authority`: 7 signals
- `public_record`: 7 signals
- `behavioural`: 5 signals
- `structured_data`: 3 signals
- `operator_type`: 1 signals
- `battery_chemistry`: 1 signals
- `construction_phase`: 1 signals
- `geographic_focus`: 1 signals

**Selection Rationale:**
- 37% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Detail by Group
> *Each signal is an objectively observable data point. The weights show how strongly that signal informs each assessment pillar; correlation direction indicates whether a higher observed value increases (+) or decreases (-) the assessed exposure.*

#### Network Authority
*Quality of partnerships, contractors, and industry relationships*

| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `partner_quality` | INFERRED_PROXY | 0.20 | 0.10 / 0.15 | 0.00 | + |
| `contractor_quality` | INFERRED_PROXY | 0.15 | 0.15 / 0.00 | 0.00 | + |
| `banking_relationship` | INFERRED_PROXY | 0.15 | 0.00 / 0.10 | 0.00 | + |
| `insurance_history` | INFERRED_PROXY | 0.15 | 0.15 / 0.10 | 0.00 | + |
| `industry_association` | DIRECT_OBSERVABLE | 0.10 | 0.00 / 0.00 | 0.00 | + |
| `regulator_relationship` | INFERRED_PROXY | 0.15 | 0.10 / 0.00 | 0.00 | + |
| `customer_quality` | INFERRED_PROXY | 0.10 | 0.00 / 0.00 | 0.10 | + |

#### Safety Performance
*OSHA metrics, process safety, NFPA/UL safety standard compliance*

| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `osha_trir` | DIRECT_OBSERVABLE | 0.15 | 0.20 / 0.10 | 0.00 | + |
| `osha_violations` | DIRECT_OBSERVABLE | 0.10 | 0.15 / 0.10 | 0.00 | + |
| `process_safety` | INFERRED_PROXY | 0.15 | 0.20 / 0.25 | 0.00 | + |
| `fatality` | DIRECT_OBSERVABLE | 0.10 | 0.00 / 0.25 | 0.00 | + |
| `major_incident` | DIRECT_OBSERVABLE | 0.10 | 0.15 / 0.30 | 0.00 | + |
| `near_miss` | INFERRED_PROXY | 0.05 | 0.10 / 0.00 | 0.00 | + |
| `safety_standard_compliance` | DIRECT_OBSERVABLE | 0.35 | 0.20 / 0.25 | 0.00 | + |

#### Construction Quality
*EPC contractor experience, technology maturity, warranty coverage, commissioning quality*

| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `technology_maturity` | INFERRED_PROXY | 0.20 | 0.15 / 0.15 | 0.00 | + |
| `epc_contractor_quality` | INFERRED_PROXY | 0.25 | 0.20 / 0.15 | 0.00 | + |
| `warranty_coverage` | INFERRED_PROXY | 0.15 | 0.00 / 0.15 | 0.00 | + |
| `commissioning_defects` | INFERRED_PROXY | 0.15 | 0.20 / 0.15 | 0.00 | + |
| `epc_track_record` | INFERRED_PROXY | 0.15 | 0.15 / 0.00 | 0.00 | + |
| `supply_chain_quality` | INFERRED_PROXY | 0.10 | 0.10 / 0.10 | 0.00 | + |
| `capacity_factor` | INFERRED_PROXY | 0.20 | 0.15 / 0.00 | 0.10 | + |
| `grid_interconnection` | INFERRED_PROXY | 0.15 | 0.10 / 0.00 | 0.00 | + |
| `degradation_rate` | INFERRED_PROXY | 0.20 | 0.15 / 0.10 | 0.00 | - |
| `bms_sophistication` | INFERRED_PROXY | 0.25 | 0.20 / 0.15 | 0.00 | + |
| `production_consistency` | INFERRED_PROXY | 0.20 | 0.15 / 0.00 | 0.10 | + |

#### Financial Stability
*Credit rating, leverage, ARO coverage, capex trends*

| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `credit_rating` | DIRECT_OBSERVABLE | 0.25 | 0.00 / 0.20 | 0.00 | + |
| `leverage` | DIRECT_OBSERVABLE | 0.20 | 0.00 / 0.15 | 0.00 | - |
| `aro_coverage` | INFERRED_PROXY | 0.20 | 0.00 / 0.15 | 0.10 | + |
| `capex_trend` | DIRECT_OBSERVABLE | 0.20 | 0.00 / 0.00 | 0.10 | + |
| `restructuring` | DIRECT_OBSERVABLE | 0.15 | 0.00 / 0.25 | 0.00 | + |

#### Asset Portfolio
*Thermal management, fire suppression, battery chemistry, hydrogen storage, cell format, NatCat exposure*

| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `thermal_management_system` | INFERRED_PROXY | 0.20 | 0.15 / 0.25 | 0.00 | + |
| `fire_suppression_capability` | DIRECT_OBSERVABLE | 0.15 | 0.00 / 0.25 | 0.00 | + |
| `hydrogen_storage_pressure` | DIRECT_OBSERVABLE | 0.10 | 0.00 / 0.20 | 0.00 | - |
| `cell_format_maturity` | INFERRED_PROXY | 0.10 | 0.10 / 0.00 | 0.00 | + |
| `electrolyser_technology` | INFERRED_PROXY | 0.10 | 0.10 / 0.10 | 0.00 | + |
| `natcat_exposure` | DIRECT_OBSERVABLE | 0.10 | 0.00 / 0.15 | 0.15 | - |
| `ppa_quality` | INFERRED_PROXY | 0.10 | 0.00 / 0.00 | 0.10 | + |
| `asset_age` | INFERRED_PROXY | 0.10 | 0.10 / 0.10 | 0.00 | - |
| `concentration` | INFERRED_PROXY | 0.05 | 0.00 / 0.15 | 0.10 | - |
| `safety_communication` | DIRECT_OBSERVABLE | 0.20 | 0.10 / 0.00 | 0.00 | + |
| `esg_reporting` | DIRECT_OBSERVABLE | 0.20 | 0.00 / 0.00 | 0.00 | + |
| `technical_hiring` | INFERRED_PROXY | 0.15 | 0.00 / 0.00 | 0.10 | + |
| `industry_presence` | DIRECT_OBSERVABLE | 0.15 | 0.00 / 0.00 | 0.00 | + |
| `disclosure_quality` | INFERRED_PROXY | 0.15 | 0.00 / 0.00 | 0.00 | + |
| `hse_leadership` | INFERRED_PROXY | 0.15 | 0.10 / 0.00 | 0.00 | + |

#### Structured Data
*Third-party ESG ratings and industry benchmarks*

| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `esg_rating` | DIRECT_OBSERVABLE | 0.40 | 0.00 / 0.00 | 0.00 | + |
| `benchmark` | COHORT_INFERENCE | 0.35 | 0.15 / 0.15 | 0.00 | + |
| `credit` | DIRECT_OBSERVABLE | 0.25 | 0.00 / 0.20 | 0.00 | + |

#### operator_type
**Categorical signal `operator_type`** — proxy tier: `INFERRED_PROXY`, source: `metadata.operator_type`

| Category | Label | Applied Factor |
|----------|-------|----------------|
| `UTILITY_DEVELOPER` | Utility Developer | 0.85 |
| `BESS_INTEGRATOR` | BESS Integrator | 0.9 |
| `OIL_GAS_TRANSITION` | Oil & Gas Transition | 1.1 |
| `FINANCIAL_SPONSOR` | Financial Sponsor | 1.2 |
| `FIRST_TIME_DEVELOPER` | First-Time Developer | 1.5 |
| `OTHER` | UNKNOWN | 1.0 |

#### battery_chemistry
**Categorical signal `battery_chemistry`** — proxy tier: `DIRECT_OBSERVABLE`, source: `metadata.battery_chemistry`

| Category | Label | Applied Factor |
|----------|-------|----------------|
| `LFP` | Lithium Iron Phosphate | 0.85 |
| `NMC` | Nickel Manganese Cobalt | 1.2 |
| `NCA` | Nickel Cobalt Aluminium | 1.3 |
| `SODIUM_ION` | Sodium Ion | 1.15 |
| `SOLID_STATE` | Solid State | 1.5 |
| `OTHER` | Unknown | 1.0 |

#### construction_phase
**Categorical signal `construction_phase`** — proxy tier: `INFERRED_PROXY`, source: `metadata.construction_phase`

| Category | Label | Applied Factor |
|----------|-------|----------------|
| `PRE_CONSTRUCTION` | Pre-Construction | 1.5 |
| `CONSTRUCTION` | Construction | 1.3 |
| `COMMISSIONING` | Commissioning | 1.15 |
| `EARLY_OPERATION` | Early Operation | 1.05 |
| `MATURE_OPERATION` | Mature Operation | 0.9 |
| `OTHER` | Unknown | 1.0 |

#### geographic_focus
**Categorical signal `geographic_focus`** — proxy tier: `INFERRED_PROXY`, source: `metadata.geographic_focus`

| Category | Label | Applied Factor |
|----------|-------|----------------|
| `US` | United States | 1.0 |
| `UK` | United Kingdom | 0.95 |
| `EU` | European Union | 0.95 |
| `APAC` | Asia Pacific | 1.1 |
| `OTHER` | Other | 1.05 |

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 | Asset Portfolio | 1.23 | 0.40 | 0.38 | 0.45 |
| 2 | Construction Quality | 0.80 | 0.25 | 0.30 | 0.25 |
| 3 | Safety Performance | 0.40 | 0.15 | 0.15 | 0.10 |
| 4 | Financial Stability | 0.30 | 0.10 | 0.07 | 0.13 |
| 5 | Structured Data | 0.17 | 0.05 | 0.07 | 0.05 |
| 6 | Network Authority | 0.10 | 0.05 | 0.03 | 0.02 |

**Primary Assessment Driver:** `Asset Portfolio` with combined weight of 1.23
**Secondary Driver:** `Construction Quality` with combined weight of 0.80

### Three-Layer Pricing Translation
> *How each pillar's tier score becomes a concrete underwriting action or pricing modifier. This is the bridge between signal observation and premium.*

**Risk -> Underwriting Action & Base Rate**

| Tier | Score Band | Action | Rate / Method |
|------|-----------|--------|---------------|
| PREFERRED | 800-1000 | APPROVE | 0.12% (MULTIPLIER) |
| STANDARD_PLUS | 650-799 | APPROVE | 0.2% (MULTIPLIER) |
| STANDARD | 500-649 | REFER | 0.28% (MULTIPLIER) |
| SUBSTANDARD | 350-499 | REFER | 0.45% (MULTIPLIER) |
| DECLINE | 0-349 | DECLINE | 0.7% (MULTIPLIER) |

**Loss -> Frequency & Severity Modifiers**

| Tier | Score Band | Frequency Modifier | Severity Modifier |
|------|-----------|--------------------|-------------------|
| VERY_LOW | 80-100 | 0.7 | 0.8 |
| LOW | 60-79 | 0.85 | 0.9 |
| MODERATE | 40-59 | 1.0 | 1.0 |
| ELEVATED | 20-39 | 1.15 | 1.15 |
| HIGH | 0-19 | 1.35 | 1.4 |

*Loss modifier is bounded: floor 0.55, cap 1.6.*

**Exposure (size) -> Scale Modifier**

| Band | Score Band | Modifier | Implied Value Range |
|------|-----------|----------|---------------------|
| SMALL | 0-20 | 0.75 | $0 - $500,000,000 |
| MEDIUM | 21-40 | 1.0 | $500,000,000 - $2,000,000,000 |
| LARGE | 41-60 | 1.3 | $2,000,000,000 - $5,000,000,000 |
| VERY_LARGE | 61-80 | 1.8 | $5,000,000,000 - $15,000,000,000 |
| MEGA | 81-100 | 2.5 | $15,000,000,000 - $50,000,000,000 |

**Exposure (complexity) -> Scale Modifier**

| Band | Score Band | Modifier | Implied Value Range |
|------|-----------|----------|---------------------|
| SIMPLE | 0-20 | 0.85 | n/a |
| MODERATE | 21-40 | 0.95 | n/a |
| COMPLEX | 41-60 | 1.1 | n/a |
| HIGHLY_COMPLEX | 61-80 | 1.3 | n/a |
| EXTREMELY_COMPLEX | 81-100 | 1.6 | n/a |

### Theoretical Premium Calculation (Tier 3 Standard)
> *Per the DSI Premium Calculation Methodology v2.0, the core formula is:*
> *P_final = (Base × Rate) × ILF_relativity × Deductible_Factor × Modifiers*

**1. The Pricing Anchor:** The Base Rate of `0.27999999999999997%` on `tiv` purchases exactly a `$10,000,000` Limit with a `$100,000` Deductible.
**2. Theoretical Execution:**
  - Assume `tiv` = $10,000,000
  - Base Premium = $10,000,000 × 0.0028 = **$28,000**
  - If the client requests the Anchor Limit/Deductible, the factors are 1.00, resulting in a technical premium of **$28,000**.

---

## Model: `energy_sme`
*Small energy operators — automated underwriting, BUNDLED pricing*

### Routing Protocol (Multiplexer)
- `tiv <= 100000000`
- `employee_count <= 500`

### Three-Layer Weight Distribution
> *DSI requires that weights for Risk, Loss, and Exposure each sum to 1.0 across all signal groups.*

**Validation:** PASS

| Group | Risk | Loss | Exposure |
|-------|------|------|----------|
| Safety Performance | 0.50 | 0.55 | 0.20 |
| Operational Telemetry | 0.15 | 0.15 | 0.25 |
| Financial Stability | 0.20 | 0.15 | 0.30 |
| Asset Portfolio | 0.15 | 0.15 | 0.25 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

**Group Definitions:**
- **Safety Performance:** OSHA metrics, incidents, process safety events
- **Operational Telemetry:** Production consistency, well integrity, maintenance patterns
- **Financial Stability:** Credit rating, leverage, ARO coverage, capex trends
- **Asset Portfolio:** Asset age, concentration, permit status

*Reading the table: a group's three weights are independent. The same group can be a dominant driver of one pillar and a minor input to another — e.g. a group may carry most of the Exposure weight while contributing little to Risk.*

### Signal Architecture Rationale
This configuration contains **25 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `DIRECT_OBSERVABLE` (14 signals): Highest confidence
- `INFERRED_PROXY` (11 signals): Medium confidence

**Signal Count by Group:**
- `public_record`: 8 signals
- `corporate_footprint`: 6 signals
- `behavioural`: 5 signals
- `technical_infrastructure`: 3 signals
- `operator_type`: 1 signals
- `operation_segment`: 1 signals
- `geographic_focus`: 1 signals

**Selection Rationale:**
- 56% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Detail by Group
> *Each signal is an objectively observable data point. The weights show how strongly that signal informs each assessment pillar; correlation direction indicates whether a higher observed value increases (+) or decreases (-) the assessed exposure.*

#### Safety Performance
*OSHA metrics, incidents, process safety events*

| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `osha_trir` | DIRECT_OBSERVABLE | 0.25 | 0.25 / 0.10 | 0.00 | + |
| `osha_violations` | DIRECT_OBSERVABLE | 0.15 | 0.20 / 0.10 | 0.00 | + |
| `process_safety` | INFERRED_PROXY | 0.25 | 0.20 / 0.30 | 0.00 | + |
| `fatality` | DIRECT_OBSERVABLE | 0.15 | 0.00 / 0.35 | 0.00 | + |
| `major_incident` | DIRECT_OBSERVABLE | 0.20 | 0.15 / 0.40 | 0.00 | + |
| `epa_violation` | DIRECT_OBSERVABLE | 0.35 | 0.25 / 0.25 | 0.00 | + |
| `spill_history` | DIRECT_OBSERVABLE | 0.35 | 0.25 / 0.35 | 0.00 | + |
| `emissions_compliance` | DIRECT_OBSERVABLE | 0.30 | 0.15 / 0.00 | 0.00 | + |

#### Operational Telemetry
*Production consistency, well integrity, maintenance patterns*

| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `production_consistency` | INFERRED_PROXY | 0.35 | 0.20 / 0.00 | 0.15 | + |
| `well_integrity` | INFERRED_PROXY | 0.35 | 0.25 / 0.20 | 0.00 | + |
| `maintenance_pattern` | INFERRED_PROXY | 0.30 | 0.20 / 0.00 | 0.00 | + |

#### Financial Stability
*Credit rating, leverage, ARO coverage, capex trends*

| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `credit_rating` | DIRECT_OBSERVABLE | 0.25 | 0.00 / 0.20 | 0.00 | + |
| `leverage` | DIRECT_OBSERVABLE | 0.20 | 0.00 / 0.15 | 0.00 | - |
| `aro_coverage` | INFERRED_PROXY | 0.20 | 0.00 / 0.15 | 0.00 | + |
| `capex_trend` | DIRECT_OBSERVABLE | 0.20 | 0.00 / 0.00 | 0.10 | + |
| `restructuring` | DIRECT_OBSERVABLE | 0.15 | 0.00 / 0.25 | 0.00 | + |

#### Asset Portfolio
*Asset age, concentration, permit status*

| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `asset_age` | INFERRED_PROXY | 0.35 | 0.25 / 0.15 | 0.00 | - |
| `concentration` | INFERRED_PROXY | 0.35 | 0.00 / 0.30 | 0.20 | - |
| `permit_status` | DIRECT_OBSERVABLE | 0.30 | 0.00 / 0.00 | 0.00 | + |
| `safety_communication` | DIRECT_OBSERVABLE | 0.35 | 0.15 / 0.00 | 0.00 | + |
| `technical_hiring` | INFERRED_PROXY | 0.35 | 0.00 / 0.00 | 0.10 | + |
| `industry_presence` | DIRECT_OBSERVABLE | 0.30 | 0.00 / 0.00 | 0.00 | + |

#### operator_type
**Categorical signal `operator_type`** — proxy tier: `INFERRED_PROXY`, source: `metadata.operator_type`

| Category | Label | Applied Factor |
|----------|-------|----------------|
| `SMALL_INDEPENDENT` | Small Independent | 1.0 |
| `FAMILY_OPERATOR` | Family Operator | 1.05 |
| `STARTUP_OPERATOR` | Startup Operator | 1.25 |
| `OTHER` | UNKNOWN | 1.0 |

#### operation_segment
**Categorical signal `operation_segment`** — proxy tier: `INFERRED_PROXY`, source: `metadata.operation_segment`

| Category | Label | Applied Factor |
|----------|-------|----------------|
| `UPSTREAM_CONVENTIONAL` | Upstream Conventional | 1.0 |
| `UPSTREAM_UNCONVENTIONAL` | Upstream Unconventional | 0.95 |
| `UPSTREAM_OFFSHORE` | Upstream Offshore (Shelf) | 1.2 |
| `UPSTREAM_DEEPWATER` | Upstream Deepwater | 1.5 |
| `MIDSTREAM_PIPELINE` | Midstream Pipeline | 0.8 |
| `MIDSTREAM_PROCESSING` | Midstream Processing | 1.0 |
| `MIDSTREAM_STORAGE` | Midstream Storage | 0.85 |
| `DOWNSTREAM_REFINING` | Downstream Refining | 1.3 |
| `DOWNSTREAM_PETROCHEMICAL` | Downstream Petrochemical | 1.25 |
| `POWER_GENERATION` | Power Generation | 0.9 |
| `RENEWABLE` | Renewable Energy | 0.7 |
| `MIXED` | Mixed Operations | 1.05 |
| `OTHER` | UNKNOWN | 1.0 |

#### geographic_focus
**Categorical signal `geographic_focus`** — proxy tier: `INFERRED_PROXY`, source: `metadata.geographic_focus`

| Category | Label | Applied Factor |
|----------|-------|----------------|
| `US_ONSHORE` | US Onshore | 1.0 |
| `US_OFFSHORE` | US Offshore | 1.15 |
| `INTERNATIONAL` | International | 1.2 |
| `OTHER` | Other | 1.05 |

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 | Safety Performance | 1.25 | 0.50 | 0.55 | 0.20 |
| 2 | Financial Stability | 0.65 | 0.20 | 0.15 | 0.30 |
| 3 | Operational Telemetry | 0.55 | 0.15 | 0.15 | 0.25 |
| 4 | Asset Portfolio | 0.55 | 0.15 | 0.15 | 0.25 |

**Primary Assessment Driver:** `Safety Performance` with combined weight of 1.25
**Secondary Driver:** `Financial Stability` with combined weight of 0.65

### Three-Layer Pricing Translation
> *How each pillar's tier score becomes a concrete underwriting action or pricing modifier. This is the bridge between signal observation and premium.*

**Risk -> Underwriting Action & Base Rate**

| Tier | Score Band | Action | Rate / Method |
|------|-----------|--------|---------------|
| PREFERRED | 800-1000 | APPROVE | 0.08% (MULTIPLIER) |
| STANDARD_PLUS | 650-799 | APPROVE | 0.14% (MULTIPLIER) |
| STANDARD | 500-649 | APPROVE_WITH_FLAG | 0.2% (MULTIPLIER) |
| SUBSTANDARD | 350-499 | REFER | 0.32% (MULTIPLIER) |
| DECLINE | 0-349 | DECLINE | 0.5% (MULTIPLIER) |

**Loss -> Frequency & Severity Modifiers**

| Tier | Score Band | Frequency Modifier | Severity Modifier |
|------|-----------|--------------------|-------------------|
| VERY_LOW | 80-100 | 0.7 | 0.8 |
| LOW | 60-79 | 0.85 | 0.9 |
| MODERATE | 40-59 | 1.0 | 1.0 |
| ELEVATED | 20-39 | 1.15 | 1.15 |
| HIGH | 0-19 | 1.35 | 1.4 |

*Loss modifier is bounded: floor 0.55, cap 1.6.*

**Exposure (size) -> Scale Modifier**

| Band | Score Band | Modifier | Implied Value Range |
|------|-----------|----------|---------------------|
| MICRO | 0-20 | 0.5 | $0 - $10,000,000 |
| SMALL | 21-40 | 0.75 | $10,000,000 - $25,000,000 |
| MEDIUM | 41-60 | 1.0 | $25,000,000 - $50,000,000 |
| LARGE | 61-80 | 1.3 | $50,000,000 - $75,000,000 |
| MAX_SME | 81-100 | 1.6 | $75,000,000 - $100,000,000 |

**Exposure (complexity) -> Scale Modifier**

| Band | Score Band | Modifier | Implied Value Range |
|------|-----------|----------|---------------------|
| SIMPLE | 0-20 | 0.85 | n/a |
| MODERATE | 21-40 | 0.95 | n/a |
| COMPLEX | 41-60 | 1.1 | n/a |
| HIGHLY_COMPLEX | 61-80 | 1.3 | n/a |
| EXTREMELY_COMPLEX | 81-100 | 1.6 | n/a |

### Theoretical Premium Calculation (Tier 3 Standard)
> *Per the DSI Premium Calculation Methodology v2.0, the core formula is:*
> *P_final = (Base × Rate) × ILF_relativity × Deductible_Factor × Modifiers*

**1. The Pricing Anchor:** The Base Rate of `0.2%` on `tiv` purchases exactly a `$0` Limit with a `$0` Deductible.
**2. Theoretical Execution:**
  - Assume `tiv` = $10,000,000
  - Base Premium = $10,000,000 × 0.002 = **$20,000**
  - If the client requests the Anchor Limit/Deductible, the factors are 1.00, resulting in a technical premium of **$20,000**.

---

## Model: `energy_hydrogen`
*Hydrogen producers, electrolyser plants, green/blue/grey H2 supply chain*

### Routing Protocol (Multiplexer)
- `industry_sector in ['HYDROGEN', 'H2_PRODUCTION', 'ELECTROLYSER']`

### Three-Layer Weight Distribution
> *DSI requires that weights for Risk, Loss, and Exposure each sum to 1.0 across all signal groups.*

**Validation:** PASS

| Group | Risk | Loss | Exposure |
|-------|------|------|----------|
| Technology Readiness | 0.35 | 0.35 | 0.30 |
| Commercial Structure | 0.25 | 0.25 | 0.30 |
| Environmental & Regulatory Record | 0.30 | 0.30 | 0.30 |
| Corporate Footprint | 0.05 | 0.05 | 0.05 |
| Firm Stability | 0.05 | 0.05 | 0.05 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

**Group Definitions:**
- **Technology Readiness:** Electrolyser TRL, plant design maturity, vendor track record
- **Commercial Structure:** Offtake counterparty quality, PPA + take-or-pay coverage
- **Environmental & Regulatory Record:** EPA ECHO, TRI, Superfund proximity — industrial-hydrogen adjacency

*Reading the table: a group's three weights are independent. The same group can be a dominant driver of one pillar and a minor input to another — e.g. a group may carry most of the Exposure weight while contributing little to Risk.*

### Signal Architecture Rationale
This configuration contains **5 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `DIRECT_OBSERVABLE` (4 signals): Highest confidence
- `INFERRED_PROXY` (1 signals): Medium confidence

**Signal Count by Group:**
- `public_record`: 3 signals
- `technical_infrastructure`: 1 signals
- `structured_data`: 1 signals

**Selection Rationale:**
- 80% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Detail by Group
> *Each signal is an objectively observable data point. The weights show how strongly that signal informs each assessment pillar; correlation direction indicates whether a higher observed value increases (+) or decreases (-) the assessed exposure.*

#### Technology Readiness
*Electrolyser TRL, plant design maturity, vendor track record*

| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `electrolyser_technology_maturity` | INFERRED_PROXY | 0.25 | 0.20 / 0.15 | 0.00 | - |

#### Commercial Structure
*Offtake counterparty quality, PPA + take-or-pay coverage*

| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `offtake_counterparty_quality` | DIRECT_OBSERVABLE | 0.18 | 0.00 / 0.20 | 0.00 | - |

#### Environmental & Regulatory Record
*EPA ECHO, TRI, Superfund proximity — industrial-hydrogen adjacency*

| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `epa_echo_violation_depth` | DIRECT_OBSERVABLE | 0.15 | 0.15 / 0.15 | 0.00 | + |
| `superfund_proximity` | DIRECT_OBSERVABLE | 0.10 | 0.00 / 0.12 | 0.00 | + |
| `tri_reportable_volume` | DIRECT_OBSERVABLE | 0.08 | 0.00 / 0.08 | 0.00 | + |

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 | Technology Readiness | 1.00 | 0.35 | 0.35 | 0.30 |
| 2 | Environmental & Regulatory Record | 0.90 | 0.30 | 0.30 | 0.30 |
| 3 | Commercial Structure | 0.80 | 0.25 | 0.25 | 0.30 |
| 4 | Corporate Footprint | 0.15 | 0.05 | 0.05 | 0.05 |
| 5 | Firm Stability | 0.15 | 0.05 | 0.05 | 0.05 |

**Primary Assessment Driver:** `Technology Readiness` with combined weight of 1.00
**Secondary Driver:** `Environmental & Regulatory Record` with combined weight of 0.90

### Three-Layer Pricing Translation
> *How each pillar's tier score becomes a concrete underwriting action or pricing modifier. This is the bridge between signal observation and premium.*

**Risk -> Underwriting Action & Base Rate**

| Tier | Score Band | Action | Rate / Method |
|------|-----------|--------|---------------|
| PREFERRED | 800-1000 | APPROVE | 0.2% (MULTIPLIER) |
| STANDARD_PLUS | 650-799 | APPROVE | 0.35% (MULTIPLIER) |
| STANDARD | 500-649 | REFER | 0.55% (MULTIPLIER) |
| SUBSTANDARD | 350-499 | REFER | 0.8% (MULTIPLIER) |
| DECLINE | 0-349 | DECLINE | 1.2% (MULTIPLIER) |

**Loss -> Frequency & Severity Modifiers**

| Tier | Score Band | Frequency Modifier | Severity Modifier |
|------|-----------|--------------------|-------------------|
| VERY_LOW | 80-100 | 0.7 | 0.8 |
| LOW | 60-79 | 0.85 | 0.9 |
| MODERATE | 40-59 | 1.0 | 1.0 |
| ELEVATED | 20-39 | 1.25 | 1.3 |
| HIGH | 0-19 | 1.6 | 1.7 |

*Loss modifier is bounded: floor 0.55, cap 1.8.*

**Exposure (size) -> Scale Modifier**

| Band | Score Band | Modifier | Implied Value Range |
|------|-----------|----------|---------------------|
| MICRO | 0-20 | 0.5 | $0 - $10,000,000 |
| SMALL | 21-40 | 0.75 | $10,000,000 - $100,000,000 |
| MEDIUM | 41-60 | 1.0 | $100,000,000 - $500,000,000 |
| LARGE | 61-80 | 1.5 | $500,000,000 - $2,500,000,000 |
| VERY_LARGE | 81-100 | 2.5 | $2,500,000,000 - $100,000,000,000 |

**Exposure (complexity) -> Scale Modifier**

| Band | Score Band | Modifier | Implied Value Range |
|------|-----------|----------|---------------------|
| SIMPLE | 0-20 | 0.85 | n/a |
| MODERATE | 21-40 | 0.95 | n/a |
| COMPLEX | 41-60 | 1.15 | n/a |
| HIGHLY_COMPLEX | 61-80 | 1.4 | n/a |
| EXTREMELY_COMPLEX | 81-100 | 1.75 | n/a |

### Theoretical Premium Calculation (Tier 3 Standard)
> *Per the DSI Premium Calculation Methodology v2.0, the core formula is:*
> *P_final = (Base × Rate) × ILF_relativity × Deductible_Factor × Modifiers*

**1. The Pricing Anchor:** The Base Rate of `0.5499999999999999%` on `tiv` purchases exactly a `$10,000,000` Limit with a `$100,000` Deductible.
**2. Theoretical Execution:**
  - Assume `tiv` = $10,000,000
  - Base Premium = $10,000,000 × 0.0055 = **$55,000**
  - If the client requests the Anchor Limit/Deductible, the factors are 1.00, resulting in a technical premium of **$55,000**.

---

## Model: `energy_nuclear`
*Nuclear-plant operators, decommissioning operators, SMR operators*

### Routing Protocol (Multiplexer)
- `industry_sector in ['NUCLEAR', 'SMR', 'NUCLEAR_DECOMMISSIONING']`

### Three-Layer Weight Distribution
> *DSI requires that weights for Risk, Loss, and Exposure each sum to 1.0 across all signal groups.*

**Validation:** PASS

| Group | Risk | Loss | Exposure |
|-------|------|------|----------|
| Regulatory Record | 0.50 | 0.50 | 0.35 |
| Financial Assurance | 0.25 | 0.25 | 0.30 |
| Plant Engineering | 0.15 | 0.15 | 0.25 |
| Corporate Footprint | 0.05 | 0.05 | 0.05 |
| Firm Stability | 0.05 | 0.05 | 0.05 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

**Group Definitions:**
- **Regulatory Record:** NRC findings, enforcement actions, EPA ECHO
- **Financial Assurance:** Decommissioning trust funding + NRC funding formula compliance
- **Plant Engineering:** Reactor generation, safety-system redundancy, digital-I&C maturity

*Reading the table: a group's three weights are independent. The same group can be a dominant driver of one pillar and a minor input to another — e.g. a group may carry most of the Exposure weight while contributing little to Risk.*

### Signal Architecture Rationale
This configuration contains **5 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `DIRECT_OBSERVABLE` (5 signals): Highest confidence

**Signal Count by Group:**
- `public_record`: 4 signals
- `structured_data`: 1 signals

**Selection Rationale:**
- 100% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Detail by Group
> *Each signal is an objectively observable data point. The weights show how strongly that signal informs each assessment pillar; correlation direction indicates whether a higher observed value increases (+) or decreases (-) the assessed exposure.*

#### Regulatory Record
*NRC findings, enforcement actions, EPA ECHO*

| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `nrc_inspection_findings` | DIRECT_OBSERVABLE | 0.22 | 0.20 / 0.22 | 0.00 | + |
| `nrc_enforcement_action_history` | DIRECT_OBSERVABLE | 0.18 | 0.18 / 0.00 | 0.00 | + |
| `epa_echo_violation_depth` | DIRECT_OBSERVABLE | 0.10 | 0.00 / 0.10 | 0.00 | + |
| `superfund_proximity` | DIRECT_OBSERVABLE | 0.08 | 0.00 / 0.08 | 0.00 | + |

#### Financial Assurance
*Decommissioning trust funding + NRC funding formula compliance*

| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `decommissioning_trust_funding` | DIRECT_OBSERVABLE | 0.20 | 0.00 / 0.22 | 0.00 | - |

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 | Regulatory Record | 1.35 | 0.50 | 0.50 | 0.35 |
| 2 | Financial Assurance | 0.80 | 0.25 | 0.25 | 0.30 |
| 3 | Plant Engineering | 0.55 | 0.15 | 0.15 | 0.25 |
| 4 | Corporate Footprint | 0.15 | 0.05 | 0.05 | 0.05 |
| 5 | Firm Stability | 0.15 | 0.05 | 0.05 | 0.05 |

**Primary Assessment Driver:** `Regulatory Record` with combined weight of 1.35
**Secondary Driver:** `Financial Assurance` with combined weight of 0.80

### Three-Layer Pricing Translation
> *How each pillar's tier score becomes a concrete underwriting action or pricing modifier. This is the bridge between signal observation and premium.*

**Risk -> Underwriting Action & Base Rate**

| Tier | Score Band | Action | Rate / Method |
|------|-----------|--------|---------------|
| PREFERRED | 800-1000 | APPROVE | 0.15% (MULTIPLIER) |
| STANDARD_PLUS | 650-799 | APPROVE | 0.28% (MULTIPLIER) |
| STANDARD | 500-649 | REFER | 0.48% (MULTIPLIER) |
| SUBSTANDARD | 350-499 | REFER | 0.75% (MULTIPLIER) |
| DECLINE | 0-349 | DECLINE | 1.1% (MULTIPLIER) |

**Loss -> Frequency & Severity Modifiers**

| Tier | Score Band | Frequency Modifier | Severity Modifier |
|------|-----------|--------------------|-------------------|
| VERY_LOW | 80-100 | 0.7 | 0.8 |
| LOW | 60-79 | 0.85 | 0.9 |
| MODERATE | 40-59 | 1.0 | 1.0 |
| ELEVATED | 20-39 | 1.3 | 1.4 |
| HIGH | 0-19 | 1.7 | 1.9 |

*Loss modifier is bounded: floor 0.55, cap 2.0.*

**Exposure (size) -> Scale Modifier**

| Band | Score Band | Modifier | Implied Value Range |
|------|-----------|----------|---------------------|
| MICRO | 0-20 | 0.5 | $0 - $100,000,000 |
| SMALL | 21-40 | 0.75 | $100,000,000 - $1,000,000,000 |
| MEDIUM | 41-60 | 1.0 | $1,000,000,000 - $5,000,000,000 |
| LARGE | 61-80 | 1.5 | $5,000,000,000 - $20,000,000,000 |
| VERY_LARGE | 81-100 | 2.5 | $20,000,000,000 - $200,000,000,000 |

**Exposure (complexity) -> Scale Modifier**

| Band | Score Band | Modifier | Implied Value Range |
|------|-----------|----------|---------------------|
| SIMPLE | 0-20 | 0.85 | n/a |
| MODERATE | 21-40 | 0.95 | n/a |
| COMPLEX | 41-60 | 1.2 | n/a |
| HIGHLY_COMPLEX | 61-80 | 1.5 | n/a |
| EXTREMELY_COMPLEX | 81-100 | 1.9 | n/a |

### Theoretical Premium Calculation (Tier 3 Standard)
> *Per the DSI Premium Calculation Methodology v2.0, the core formula is:*
> *P_final = (Base × Rate) × ILF_relativity × Deductible_Factor × Modifiers*

**1. The Pricing Anchor:** The Base Rate of `0.48%` on `tiv` purchases exactly a `$100,000,000` Limit with a `$500,000` Deductible.
**2. Theoretical Execution:**
  - Assume `tiv` = $10,000,000
  - Base Premium = $10,000,000 × 0.0048 = **$48,000**
  - If the client requests the Anchor Limit/Deductible, the factors are 1.00, resulting in a technical premium of **$48,000**.


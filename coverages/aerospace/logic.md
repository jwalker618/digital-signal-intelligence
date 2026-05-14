# DSI Logic Document: `AEROSPACE`
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

## Model: `aerospace_general`
*Aviation hull and liability coverage based on observable safety and operational signals*

### Routing Protocol (Multiplexer)
- `hull_value > 50000000`

### Three-Layer Weight Distribution
> *DSI requires that weights for Risk, Loss, and Exposure each sum to 1.0 across all signal groups.*

**Validation:** PASS

| Group | Risk | Loss | Exposure |
|-------|------|------|----------|
| Network Authority | 0.10 | 0.05 | 0.05 |
| Safety Record | 0.50 | 0.60 | 0.20 |
| Operational Quality | 0.30 | 0.30 | 0.60 |
| Financial Stability | 0.05 | 0.03 | 0.10 |
| Corporate Governance | 0.05 | 0.02 | 0.05 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

**Group Definitions:**
- **Network Authority:** Industry relationships and counterparty quality
- **Safety Record:** Historical safety performance from public databases
- **Operational Quality:** Observable operational metrics
- **Financial Stability:** Public financial indicators
- **Corporate Governance:** Management quality and safety culture indicators

*Reading the table: a group's three weights are independent. The same group can be a dominant driver of one pillar and a minor input to another — e.g. a group may carry most of the Exposure weight while contributing little to Risk.*

### Signal Architecture Rationale
This configuration contains **48 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `DIRECT_OBSERVABLE` (23 signals): Highest confidence
- `INFERRED_PROXY` (24 signals): Medium confidence
- `COHORT_INFERENCE` (1 signals): Lowest confidence

**Signal Count by Group:**
- `technical_infrastructure`: 17 signals
- `public_record`: 12 signals
- `network_authority`: 5 signals
- `corporate_footprint`: 5 signals
- `behavioural`: 4 signals
- `operator_type`: 1 signals
- `fleet_category`: 1 signals
- `fleet_size`: 1 signals
- `regulatory_framework`: 1 signals
- `iosa_status`: 1 signals

**Selection Rationale:**
- 48% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Detail by Group
> *Each signal is an objectively observable data point. The weights show how strongly that signal informs each assessment pillar; correlation direction indicates whether a higher observed value increases (+) or decreases (-) the assessed exposure.*

#### Network Authority
*Industry relationships and counterparty quality*

| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `alliance_membership` | DIRECT_OBSERVABLE | 0.25 | 0.15 / 0.10 | 0.00 | + |
| `codeshare_quality` | INFERRED_PROXY | 0.20 | 0.00 / 0.10 | 0.00 | + |
| `lessor_quality` | INFERRED_PROXY | 0.20 | 0.00 / 0.10 | 0.00 | + |
| `oem_relationship` | INFERRED_PROXY | 0.15 | 0.10 / 0.00 | 0.00 | + |
| `mro_quality` | INFERRED_PROXY | 0.20 | 0.15 / 0.00 | 0.00 | + |

#### Safety Record
*Historical safety performance from public databases*

| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `accident_history` | DIRECT_OBSERVABLE | 0.30 | 0.30 / 0.35 | 0.15 | + |
| `incident_history` | DIRECT_OBSERVABLE | 0.20 | 0.25 / 0.15 | 0.00 | + |
| `accident_rate` | COHORT_INFERENCE | 0.20 | 0.25 / 0.20 | 0.00 | + |
| `fatality_history` | DIRECT_OBSERVABLE | 0.20 | 0.15 / 0.40 | 0.00 | + |
| `investigation_findings` | DIRECT_OBSERVABLE | 0.10 | 0.15 / 0.00 | 0.00 | + |
| `certificate_status` | DIRECT_OBSERVABLE | 0.25 | 0.20 / 0.15 | 0.00 | + |
| `enforcement_actions` | DIRECT_OBSERVABLE | 0.20 | 0.25 / 0.20 | 0.00 | + |
| `iosa_audit_status` | DIRECT_OBSERVABLE | 0.15 | 0.15 / 0.00 | 0.00 | + |
| `ramp_inspection` | DIRECT_OBSERVABLE | 0.15 | 0.15 / 0.00 | 0.00 | + |
| `eu_safety_list` | DIRECT_OBSERVABLE | 0.15 | 0.20 / 0.25 | 0.00 | + |
| `state_safety_rating` | DIRECT_OBSERVABLE | 0.05 | 0.00 / 0.00 | 0.00 | + |
| `certification_transparency` | INFERRED_PROXY | 0.05 | 0.00 / 0.00 | 0.00 | + |

#### Operational Quality
*Observable operational metrics*

| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `otp_score` | DIRECT_OBSERVABLE | 0.20 | 0.10 / 0.00 | 0.00 | + |
| `dispatch_reliability` | DIRECT_OBSERVABLE | 0.20 | 0.15 / 0.00 | 0.00 | + |
| `crew_experience` | INFERRED_PROXY | 0.15 | 0.15 / 0.10 | 0.00 | + |
| `training_indicators` | INFERRED_PROXY | 0.15 | 0.15 / 0.00 | 0.00 | + |
| `operational_complexity` | INFERRED_PROXY | 0.15 | 0.15 / 0.00 | 0.20 | - |
| `growth_rate` | DIRECT_OBSERVABLE | 0.15 | 0.10 / 0.00 | 0.15 | - |
| `fleet_age` | INFERRED_PROXY | 0.30 | 0.20 / 0.15 | 0.10 | - |
| `fleet_homogeneity` | INFERRED_PROXY | 0.20 | 0.10 / 0.00 | 0.10 | + |
| `aircraft_generation` | INFERRED_PROXY | 0.25 | 0.15 / 0.10 | 0.00 | + |
| `order_backlog` | DIRECT_OBSERVABLE | 0.15 | 0.00 / 0.00 | 0.10 | + |
| `maintenance_indicators` | INFERRED_PROXY | 0.05 | 0.10 / 0.00 | 0.00 | + |
| `supply_chain_quality` | INFERRED_PROXY | 0.05 | 0.00 / 0.00 | 0.00 | + |
| `conflict_zone_exposure` | DIRECT_OBSERVABLE | 0.30 | 0.20 / 0.30 | 0.15 | - |
| `challenging_airports` | DIRECT_OBSERVABLE | 0.20 | 0.15 / 0.00 | 0.00 | - |
| `high_risk_destinations` | DIRECT_OBSERVABLE | 0.25 | 0.15 / 0.20 | 0.00 | - |
| `weather_exposure` | INFERRED_PROXY | 0.15 | 0.10 / 0.00 | 0.00 | - |
| `terrain_exposure` | INFERRED_PROXY | 0.10 | 0.10 / 0.00 | 0.00 | - |

#### Financial Stability
*Public financial indicators*

| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `credit_rating` | DIRECT_OBSERVABLE | 0.35 | 0.00 / 0.20 | 0.00 | + |
| `public_financials` | DIRECT_OBSERVABLE | 0.30 | 0.00 / 0.15 | 0.00 | + |
| `market_position` | INFERRED_PROXY | 0.20 | 0.00 / 0.00 | 0.15 | + |
| `government_support` | DIRECT_OBSERVABLE | 0.15 | 0.00 / 0.10 | 0.00 | + |

#### Corporate Governance
*Management quality and safety culture indicators*

| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `management_stability` | INFERRED_PROXY | 0.25 | 0.15 / 0.00 | 0.00 | + |
| `safety_leadership` | INFERRED_PROXY | 0.25 | 0.20 / 0.15 | 0.00 | + |
| `safety_reporting` | DIRECT_OBSERVABLE | 0.20 | 0.15 / 0.00 | 0.00 | + |
| `corporate_structure` | INFERRED_PROXY | 0.15 | 0.00 / 0.00 | 0.10 | + |
| `industry_engagement` | DIRECT_OBSERVABLE | 0.15 | 0.00 / 0.00 | 0.00 | + |

#### operator_type
**Categorical signal `operator_type`** — proxy tier: `INFERRED_PROXY`, source: `metadata.operator_type`

| Category | Label | Applied Factor |
|----------|-------|----------------|
| `MAJOR_AIRLINE` | Major Airline | 0.85 |
| `REGIONAL_AIRLINE` | Regional Airline | 1.0 |
| `LOW_COST_CARRIER` | Low Cost Carrier | 0.95 |
| `CARGO_AIRLINE` | Cargo Airline | 1.1 |
| `CHARTER_OPERATOR` | Charter Operator | 1.25 |
| `CORPORATE_FLIGHT` | Corporate Flight Department | 1.15 |
| `HELICOPTER_OPERATOR` | Helicopter Operator | 1.4 |
| `FLIGHT_SCHOOL` | Flight Training Organization | 1.5 |
| `PRIVATE_OWNER` | Private Owner/Operator | 1.35 |
| `OTHER` | UNKNOWN | 1.0 |

#### fleet_category
**Categorical signal `fleet_category`** — proxy tier: `INFERRED_PROXY`, source: `metadata.fleet_category`

| Category | Label | Applied Factor |
|----------|-------|----------------|
| `WIDEBODY` | Widebody | 1.15 |
| `NARROWBODY` | Narrowbody | 1.0 |
| `REGIONAL_JET` | Regional Jet | 1.05 |
| `TURBOPROP` | Turboprop | 0.95 |
| `BUSINESS_JET` | Business Jet | 1.2 |
| `HELICOPTER` | Helicopter | 1.35 |
| `PISTON` | Piston Aircraft | 1.25 |
| `OTHER` | UNKNOWN | 1.0 |

#### fleet_size
**Categorical signal `fleet_size`** — proxy tier: `INFERRED_PROXY`, source: `metadata.fleet_size`

| Category | Label | Applied Factor |
|----------|-------|----------------|
| `SINGLE` | Single Aircraft | 1.3 |
| `MICRO` | Micro Fleet (2-5) | 1.2 |
| `SMALL` | Small Fleet (6-20) | 1.1 |
| `MEDIUM` | Medium Fleet (21-50) | 1.0 |
| `LARGE` | Large Fleet (51-150) | 0.95 |
| `MAJOR` | Major Fleet (150+) | 0.9 |
| `OTHER` | UNKNOWN | 1.0 |

#### regulatory_framework
**Categorical signal `regulatory_framework`** — proxy tier: `INFERRED_PROXY`, source: `metadata.regulatory_framework`

| Category | Label | Applied Factor |
|----------|-------|----------------|
| `FAA` | FAA (United States) | 1.0 |
| `EASA` | EASA (European Union) | 1.0 |
| `CAA_UK` | CAA (United Kingdom) | 1.0 |
| `TCCA` | TCCA (Canada) | 1.0 |
| `CASA` | CASA (Australia) | 1.05 |
| `CAAC` | CAAC (China) | 1.15 |
| `DGCA_INDIA` | DGCA (India) | 1.15 |
| `OTHER_ICAO` | Other ICAO Compliant | 1.2 |
| `NON_ICAO` | Non-ICAO Compliant | 1.5 |
| `OTHER` | UNKNOWN | 1.0 |

#### iosa_status
**Categorical signal `iosa_status`** — proxy tier: `INFERRED_PROXY`, source: `metadata.iosa_status`

| Category | Label | Applied Factor |
|----------|-------|----------------|
| `REGISTERED` | IOSA Registered | 0.9 |
| `EXPIRED` | IOSA Expired | 1.15 |
| `NEVER_REGISTERED` | Never Registered | 1.25 |
| `NOT_APPLICABLE` | Not Applicable | 1.0 |

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 | Safety Record | 1.30 | 0.50 | 0.60 | 0.20 |
| 2 | Operational Quality | 1.20 | 0.30 | 0.30 | 0.60 |
| 3 | Network Authority | 0.20 | 0.10 | 0.05 | 0.05 |
| 4 | Financial Stability | 0.18 | 0.05 | 0.03 | 0.10 |
| 5 | Corporate Governance | 0.12 | 0.05 | 0.02 | 0.05 |

**Primary Assessment Driver:** `Safety Record` with combined weight of 1.30
**Secondary Driver:** `Operational Quality` with combined weight of 1.20

### Three-Layer Pricing Translation
> *How each pillar's tier score becomes a concrete underwriting action or pricing modifier. This is the bridge between signal observation and premium.*

**Risk -> Underwriting Action & Base Rate**

| Tier | Score Band | Action | Rate / Method |
|------|-----------|--------|---------------|
| PREFERRED | 800-1000 | APPROVE | 0.12% (MULTIPLIER) |
| STANDARD_PLUS | 650-799 | APPROVE | 0.18% (MULTIPLIER) |
| STANDARD | 500-649 | REFER | 0.28% (MULTIPLIER) |
| SUBSTANDARD | 350-499 | REFER | 0.45% (MULTIPLIER) |
| DECLINE | 0-349 | DECLINE | 1.5% (MULTIPLIER) |

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
| MICRO | 0-20 | 1.0 | $0 - $1,000,000 |
| SMALL | 21-40 | 0.95 | $1,000,001 - $10,000,000 |
| MEDIUM | 41-60 | 0.9 | $10,000,001 - $50,000,000 |
| LARGE | 61-80 | 0.85 | $50,000,001 - $250,000,000 |
| VERY_LARGE | 81-100 | 0.8 | $250,000,001 - $1,000,000,000 |

**Exposure (complexity) -> Scale Modifier**

| Band | Score Band | Modifier | Implied Value Range |
|------|-----------|----------|---------------------|
| SIMPLE | 0-20 | 0.8 | n/a |
| MODERATE | 21-40 | 0.95 | n/a |
| COMPLEX | 41-60 | 1.1 | n/a |
| HIGHLY_COMPLEX | 61-80 | 1.3 | n/a |
| EXTREMELY_COMPLEX | 81-100 | 1.6 | n/a |

### Theoretical Premium Calculation (Worked Example)
> *Per the DSI Premium Calculation Methodology v2.0, the full factor chain is:*
> *P_final = (Basis × Base Rate) × ILF_relativity × Deductible_Factor × Loss_Modifier × Exposure_Modifier*

**Worked example — Risk Tier 3 (STANDARD), Loss Tier 4 (ELEVATED), requesting the anchor limit/deductible:**

| Factor | Source | Value |
|--------|--------|-------|
| `hull_value` (rating basis) | Routing-valid assumption | $150,000,000 |
| Base Rate | Risk Tier 3 (STANDARD) | 0.28% |
| **Base Premium** | `hull_value` × Base Rate | **$420,000** |
| ILF relativity | Limit = anchor ($10,000,000) | 1.00 |
| Deductible factor | Deductible = anchor ($50,000) | 1.00 |
| Loss frequency modifier | Loss Tier 4 (ELEVATED) | 1.15 |
| Loss severity modifier | Loss Tier 4 (ELEVATED) | 1.15 |
| **Loss modifier** | Frequency × Severity, bounded [0.55, 1.6] | **1.32** |
| Exposure modifier | Size band LARGE | 0.85 |
| **Technical Premium** | Product of all factors | **$472,132** |

*Basis vs. limit: `hull_value` is the total insured value the rate is applied to — a Base Rate of 0.28% on `hull_value` is the rated cost of risk, not the policy limit. The policy Limit (anchored at $10,000,000) is the maximum payout and scales premium independently via the ILF curve; requesting a limit above the anchor lifts the ILF relativity above 1.00.*

**Loss Tier Sensitivity** — holding Risk Tier 3 and the Exposure modifier constant, the technical premium moves with the Loss tier:

| Loss Tier | Freq Mod | Sev Mod | Loss Modifier | Technical Premium |
|-----------|----------|---------|---------------|-------------------|
| 1 VERY_LOW | 0.70 | 0.80 | 0.56 | $199,920 |
| 2 LOW | 0.85 | 0.90 | 0.77 | $273,105 |
| 3 MODERATE | 1.00 | 1.00 | 1.00 | $357,000 |
| 4 ELEVATED  *(example)* | 1.15 | 1.15 | 1.32 | $472,132 |
| 5 HIGH | 1.35 | 1.40 | 1.60 | $571,200 |


---

## Model: `aerospace_sme`
*Aviation coverage for small/medium operators with hull value under $50M*

### Routing Protocol (Multiplexer)
- `hull_value <= 50000000`
- `limit <= 10000000`

### Three-Layer Weight Distribution
> *DSI requires that weights for Risk, Loss, and Exposure each sum to 1.0 across all signal groups.*

**Validation:** PASS

| Group | Risk | Loss | Exposure |
|-------|------|------|----------|
| Safety Record | 0.60 | 0.65 | 0.20 |
| Operational Quality | 0.35 | 0.30 | 0.70 |
| Corporate Governance | 0.05 | 0.05 | 0.10 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

**Group Definitions:**
- **Safety Record:** Historical safety performance
- **Operational Quality:** Crew and operational standards
- **Corporate Governance:** Management and safety culture

*Reading the table: a group's three weights are independent. The same group can be a dominant driver of one pillar and a minor input to another — e.g. a group may carry most of the Exposure weight while contributing little to Risk.*

### Signal Architecture Rationale
This configuration contains **22 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `DIRECT_OBSERVABLE` (9 signals): Highest confidence
- `INFERRED_PROXY` (13 signals): Medium confidence

**Signal Count by Group:**
- `public_record`: 8 signals
- `technical_infrastructure`: 7 signals
- `corporate_footprint`: 3 signals
- `operator_type`: 1 signals
- `fleet_category`: 1 signals
- `fleet_size`: 1 signals
- `regulatory_framework`: 1 signals

**Selection Rationale:**
- 41% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Detail by Group
> *Each signal is an objectively observable data point. The weights show how strongly that signal informs each assessment pillar; correlation direction indicates whether a higher observed value increases (+) or decreases (-) the assessed exposure.*

#### Safety Record
*Historical safety performance*

| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `accident_history` | DIRECT_OBSERVABLE | 0.35 | 0.35 / 0.40 | 0.00 | + |
| `incident_history` | DIRECT_OBSERVABLE | 0.25 | 0.30 / 0.00 | 0.00 | + |
| `fatality_history` | DIRECT_OBSERVABLE | 0.25 | 0.00 / 0.45 | 0.00 | + |
| `investigation_findings` | DIRECT_OBSERVABLE | 0.15 | 0.15 / 0.00 | 0.00 | + |
| `certificate_status` | DIRECT_OBSERVABLE | 0.35 | 0.25 / 0.00 | 0.00 | + |
| `enforcement_actions` | DIRECT_OBSERVABLE | 0.30 | 0.30 / 0.00 | 0.00 | + |
| `ramp_inspection` | DIRECT_OBSERVABLE | 0.20 | 0.20 / 0.00 | 0.00 | + |
| `state_safety_rating` | DIRECT_OBSERVABLE | 0.15 | 0.00 / 0.00 | 0.00 | + |

#### Operational Quality
*Crew and operational standards*

| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `crew_experience` | INFERRED_PROXY | 0.35 | 0.30 / 0.20 | 0.00 | + |
| `training_indicators` | INFERRED_PROXY | 0.30 | 0.25 / 0.00 | 0.00 | + |
| `operational_complexity` | INFERRED_PROXY | 0.20 | 0.20 / 0.00 | 0.00 | - |
| `growth_rate` | DIRECT_OBSERVABLE | 0.15 | 0.00 / 0.00 | 0.20 | - |
| `fleet_age` | INFERRED_PROXY | 0.40 | 0.30 / 0.20 | 0.00 | - |
| `fleet_homogeneity` | INFERRED_PROXY | 0.25 | 0.15 / 0.00 | 0.00 | + |
| `maintenance_indicators` | INFERRED_PROXY | 0.35 | 0.25 / 0.00 | 0.00 | + |

#### Corporate Governance
*Management and safety culture*

| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `management_stability` | INFERRED_PROXY | 0.40 | 0.25 / 0.00 | 0.00 | + |
| `safety_leadership` | INFERRED_PROXY | 0.35 | 0.30 / 0.20 | 0.00 | + |
| `corporate_structure` | INFERRED_PROXY | 0.25 | 0.00 / 0.00 | 0.00 | + |

#### operator_type
**Categorical signal `operator_type`** — proxy tier: `INFERRED_PROXY`, source: `metadata.operator_type`

| Category | Label | Applied Factor |
|----------|-------|----------------|
| `CHARTER_OPERATOR` | Charter Operator | 1.15 |
| `CORPORATE_FLIGHT` | Corporate Flight Department | 1.05 |
| `HELICOPTER_OPERATOR` | Helicopter Operator | 1.3 |
| `FLIGHT_SCHOOL` | Flight Training Organization | 1.4 |
| `PRIVATE_OWNER` | Private Owner/Operator | 1.25 |
| `OTHER` | UNKNOWN | 1.0 |

#### fleet_category
**Categorical signal `fleet_category`** — proxy tier: `INFERRED_PROXY`, source: `metadata.fleet_category`

| Category | Label | Applied Factor |
|----------|-------|----------------|
| `TURBOPROP` | Turboprop | 0.95 |
| `BUSINESS_JET` | Business Jet | 1.1 |
| `HELICOPTER` | Helicopter | 1.25 |
| `PISTON` | Piston Aircraft | 1.15 |
| `OTHER` | UNKNOWN | 1.0 |

#### fleet_size
**Categorical signal `fleet_size`** — proxy tier: `INFERRED_PROXY`, source: `metadata.fleet_size`

| Category | Label | Applied Factor |
|----------|-------|----------------|
| `SINGLE` | Single Aircraft | 1.2 |
| `MICRO` | Micro Fleet (2-5) | 1.1 |
| `SMALL` | Small Fleet (6-20) | 1.0 |
| `OTHER` | UNKNOWN | 1.0 |

#### regulatory_framework
**Categorical signal `regulatory_framework`** — proxy tier: `INFERRED_PROXY`, source: `metadata.regulatory_framework`

| Category | Label | Applied Factor |
|----------|-------|----------------|
| `FAA` | FAA (United States) | 1.0 |
| `EASA` | EASA (European Union) | 1.0 |
| `CAA_UK` | CAA (United Kingdom) | 1.0 |
| `TCCA` | TCCA (Canada) | 1.0 |
| `CASA` | CASA (Australia) | 1.05 |
| `OTHER_ICAO` | Other ICAO Compliant | 1.15 |
| `OTHER` | UNKNOWN | 1.0 |

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 | Safety Record | 1.45 | 0.60 | 0.65 | 0.20 |
| 2 | Operational Quality | 1.35 | 0.35 | 0.30 | 0.70 |
| 3 | Corporate Governance | 0.20 | 0.05 | 0.05 | 0.10 |

**Primary Assessment Driver:** `Safety Record` with combined weight of 1.45
**Secondary Driver:** `Operational Quality` with combined weight of 1.35

### Three-Layer Pricing Translation
> *How each pillar's tier score becomes a concrete underwriting action or pricing modifier. This is the bridge between signal observation and premium.*

**Risk -> Underwriting Action & Base Rate**

| Tier | Score Band | Action | Rate / Method |
|------|-----------|--------|---------------|
| PREFERRED | 800-1000 | APPROVE | PREMIUM_BASE |
| STANDARD_PLUS | 650-799 | APPROVE | PREMIUM_BASE |
| STANDARD | 500-649 | APPROVE | PREMIUM_BASE |
| SUBSTANDARD | 350-499 | REFER | PREMIUM_BASE |
| DECLINE | 0-349 | DECLINE | PREMIUM_BASE |

**Loss -> Frequency & Severity Modifiers**

| Tier | Score Band | Frequency Modifier | Severity Modifier |
|------|-----------|--------------------|-------------------|
| VERY_LOW | 80-100 | 0.7 | 0.8 |
| LOW | 60-79 | 0.85 | 0.9 |
| MODERATE | 40-59 | 1.0 | 1.0 |
| ELEVATED | 20-39 | 1.15 | 1.15 |
| HIGH | 0-19 | 1.3 | 1.35 |

*Loss modifier is bounded: floor 0.6, cap 1.5.*

**Exposure (size) -> Scale Modifier**

| Band | Score Band | Modifier | Implied Value Range |
|------|-----------|----------|---------------------|
| MICRO | 0-25 | 0.6 | $0 - $1,000,000 |
| SMALL | 26-50 | 0.8 | $1,000,000 - $10,000,000 |
| MEDIUM | 51-75 | 1.0 | $10,000,000 - $25,000,000 |
| MEDIUM_LARGE | 76-100 | 1.2 | $25,000,000 - $50,000,000 |

**Exposure (complexity) -> Scale Modifier**

| Band | Score Band | Modifier | Implied Value Range |
|------|-----------|----------|---------------------|
| SIMPLE | 0-33 | 0.9 | n/a |
| MODERATE | 34-66 | 1.0 | n/a |
| COMPLEX | 67-100 | 1.15 | n/a |

### Theoretical Premium Calculation (Worked Example)
> *Per the DSI Premium Calculation Methodology v2.0, the core formula is:*
> *P_final = Base Package Premium × Modifiers*

**1. The Pricing Anchor:** The Flat Premium of `$7,500` purchases exactly the `$5,000,000` Limit / `$10,000` Deductible Base Package.
**2. Theoretical Execution:**
  - Technical Premium = **$7,500**
  - *Scaling relies entirely on selecting a different Limit ID from the Bundled limit_configuration packages.*

---

## Model: `aerospace_space`
*Space risk — launch vehicles, satellites, in-orbit operations*

### Routing Protocol (Multiplexer)
- `aviation_segment == SPACE`
- `hull_value >= 50000000`

### Three-Layer Weight Distribution
> *DSI requires that weights for Risk, Loss, and Exposure each sum to 1.0 across all signal groups.*

**Validation:** PASS

| Group | Risk | Loss | Exposure |
|-------|------|------|----------|
| Space Risk | 0.55 | 0.55 | 0.45 |
| Regulatory Framework | 0.15 | 0.10 | 0.15 |
| Corporate Footprint | 0.20 | 0.20 | 0.25 |
| Firm Stability | 0.10 | 0.15 | 0.15 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

**Group Definitions:**
- **Space Risk:** Launch vehicle reliability, satellite technology, orbital debris, in-orbit anomaly history

*Reading the table: a group's three weights are independent. The same group can be a dominant driver of one pillar and a minor input to another — e.g. a group may carry most of the Exposure weight while contributing little to Risk.*

### Signal Architecture Rationale
This configuration contains **7 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `DIRECT_OBSERVABLE` (3 signals): Highest confidence
- `INFERRED_PROXY` (4 signals): Medium confidence

**Signal Count by Group:**
- `technical_infrastructure`: 7 signals

**Selection Rationale:**
- 43% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Detail by Group
> *Each signal is an objectively observable data point. The weights show how strongly that signal informs each assessment pillar; correlation direction indicates whether a higher observed value increases (+) or decreases (-) the assessed exposure.*

#### Space Risk
*Launch vehicle reliability, satellite technology, orbital debris, in-orbit anomaly history*

| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `launch_vehicle_reliability` | DIRECT_OBSERVABLE | 0.30 | 0.25 / 0.20 | 0.00 | + |
| `satellite_technology_maturity` | INFERRED_PROXY | 0.20 | 0.15 / 0.15 | 0.00 | + |
| `orbital_debris_exposure` | INFERRED_PROXY | 0.15 | 0.15 / 0.15 | 0.10 | + |
| `in_orbit_anomaly_history` | DIRECT_OBSERVABLE | 0.15 | 0.20 / 0.10 | 0.00 | + |
| `ground_segment_quality` | INFERRED_PROXY | 0.10 | 0.10 / 0.10 | 0.00 | + |
| `space_launch_cadence` | DIRECT_OBSERVABLE | 0.05 | 0.04 / 0.05 | 0.00 | + |
| `fleet_age_distribution` | INFERRED_PROXY | 0.03 | 0.03 / 0.00 | 0.00 | + |

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 | Space Risk | 1.55 | 0.55 | 0.55 | 0.45 |
| 2 | Corporate Footprint | 0.65 | 0.20 | 0.20 | 0.25 |
| 3 | Regulatory Framework | 0.40 | 0.15 | 0.10 | 0.15 |
| 4 | Firm Stability | 0.40 | 0.10 | 0.15 | 0.15 |

**Primary Assessment Driver:** `Space Risk` with combined weight of 1.55
**Secondary Driver:** `Corporate Footprint` with combined weight of 0.65

### Three-Layer Pricing Translation
> *How each pillar's tier score becomes a concrete underwriting action or pricing modifier. This is the bridge between signal observation and premium.*

**Risk -> Underwriting Action & Base Rate**

| Tier | Score Band | Action | Rate / Method |
|------|-----------|--------|---------------|
| PREFERRED | 800-1000 | APPROVE | 3.5% (MULTIPLIER) |
| STANDARD_PLUS | 650-799 | APPROVE | 5.5% (MULTIPLIER) |
| STANDARD | 500-649 | REFER | 8.5% (MULTIPLIER) |
| SUBSTANDARD | 350-499 | REFER | 13% (MULTIPLIER) |
| DECLINE | 0-349 | DECLINE | 20% (MULTIPLIER) |

**Loss -> Frequency & Severity Modifiers**

| Tier | Score Band | Frequency Modifier | Severity Modifier |
|------|-----------|--------------------|-------------------|
| VERY_LOW | 80-100 | 0.7 | 0.8 |
| LOW | 60-79 | 0.85 | 0.9 |
| MODERATE | 40-59 | 1.0 | 1.0 |
| ELEVATED | 20-39 | 1.15 | 1.15 |
| HIGH | 0-19 | 1.35 | 1.4 |

*Loss modifier is bounded: floor 0.5, cap 1.8.*

**Exposure (size) -> Scale Modifier**

| Band | Score Band | Modifier | Implied Value Range |
|------|-----------|----------|---------------------|
| MICRO | 0-20 | 0.5 | $0 - $10,000,000 |
| SMALL | 21-40 | 0.75 | $10,000,000 - $50,000,000 |
| MEDIUM | 41-60 | 1.0 | $50,000,000 - $250,000,000 |
| LARGE | 61-80 | 1.5 | $250,000,000 - $1,000,000,000 |
| VERY_LARGE | 81-100 | 2.5 | $1,000,000,000 - $5,000,000,000 |

**Exposure (complexity) -> Scale Modifier**

| Band | Score Band | Modifier | Implied Value Range |
|------|-----------|----------|---------------------|
| SIMPLE | 0-20 | 0.85 | n/a |
| MODERATE | 21-40 | 0.95 | n/a |
| COMPLEX | 41-60 | 1.1 | n/a |
| HIGHLY_COMPLEX | 61-80 | 1.3 | n/a |
| EXTREMELY_COMPLEX | 81-100 | 1.6 | n/a |

### Theoretical Premium Calculation (Worked Example)
> *Per the DSI Premium Calculation Methodology v2.0, the full factor chain is:*
> *P_final = (Basis × Base Rate) × ILF_relativity × Deductible_Factor × Loss_Modifier × Exposure_Modifier*

**Worked example — Risk Tier 3 (STANDARD), Loss Tier 4 (ELEVATED), requesting the anchor limit/deductible:**

| Factor | Source | Value |
|--------|--------|-------|
| `hull_value` (rating basis) | Routing-valid assumption | $150,000,000 |
| Base Rate | Risk Tier 3 (STANDARD) | 8.5% |
| **Base Premium** | `hull_value` × Base Rate | **$12,750,000** |
| ILF relativity | Limit = anchor ($50,000,000) | 1.00 |
| Deductible factor | Deductible = anchor ($5,000,000) | 1.00 |
| Loss frequency modifier | Loss Tier 4 (ELEVATED) | 1.15 |
| Loss severity modifier | Loss Tier 4 (ELEVATED) | 1.15 |
| **Loss modifier** | Frequency × Severity, bounded [0.5, 1.8] | **1.32** |
| Exposure modifier | Size band MEDIUM | 1.00 |
| **Technical Premium** | Product of all factors | **$16,861,875** |

*Basis vs. limit: `hull_value` is the total insured value the rate is applied to — a Base Rate of 8.5% on `hull_value` is the rated cost of risk, not the policy limit. The policy Limit (anchored at $50,000,000) is the maximum payout and scales premium independently via the ILF curve; requesting a limit above the anchor lifts the ILF relativity above 1.00.*

**Loss Tier Sensitivity** — holding Risk Tier 3 and the Exposure modifier constant, the technical premium moves with the Loss tier:

| Loss Tier | Freq Mod | Sev Mod | Loss Modifier | Technical Premium |
|-----------|----------|---------|---------------|-------------------|
| 1 VERY_LOW | 0.70 | 0.80 | 0.56 | $7,140,000 |
| 2 LOW | 0.85 | 0.90 | 0.77 | $9,753,750 |
| 3 MODERATE | 1.00 | 1.00 | 1.00 | $12,750,000 |
| 4 ELEVATED  *(example)* | 1.15 | 1.15 | 1.32 | $16,861,875 |
| 5 HIGH | 1.35 | 1.40 | 1.80 | $22,950,000 |


---

## Model: `aerospace_rotary`
*Helicopter operations — mission-specific, EMS, offshore, utility, corporate*

### Routing Protocol (Multiplexer)
- `aviation_segment == ROTARY_WING`

### Three-Layer Weight Distribution
> *DSI requires that weights for Risk, Loss, and Exposure each sum to 1.0 across all signal groups.*

**Validation:** PASS

| Group | Risk | Loss | Exposure |
|-------|------|------|----------|
| Rotary Wing Risk | 0.45 | 0.45 | 0.40 |
| Iosa Status | 0.25 | 0.20 | 0.25 |
| Corporate Footprint | 0.15 | 0.20 | 0.20 |
| Firm Stability | 0.15 | 0.15 | 0.15 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

**Group Definitions:**
- **Rotary Wing Risk:** Helicopter mission profile, pilot experience, maintenance programme, landing zone quality

*Reading the table: a group's three weights are independent. The same group can be a dominant driver of one pillar and a minor input to another — e.g. a group may carry most of the Exposure weight while contributing little to Risk.*

### Signal Architecture Rationale
This configuration contains **7 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `DIRECT_OBSERVABLE` (2 signals): Highest confidence
- `INFERRED_PROXY` (5 signals): Medium confidence

**Signal Count by Group:**
- `technical_infrastructure`: 7 signals

**Selection Rationale:**
- 29% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Detail by Group
> *Each signal is an objectively observable data point. The weights show how strongly that signal informs each assessment pillar; correlation direction indicates whether a higher observed value increases (+) or decreases (-) the assessed exposure.*

#### Rotary Wing Risk
*Helicopter mission profile, pilot experience, maintenance programme, landing zone quality*

| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `rotary_pilot_experience` | DIRECT_OBSERVABLE | 0.25 | 0.25 / 0.10 | 0.00 | + |
| `rotary_maintenance_quality` | INFERRED_PROXY | 0.20 | 0.15 / 0.10 | 0.00 | + |
| `landing_zone_quality` | INFERRED_PROXY | 0.15 | 0.15 / 0.10 | 0.10 | + |
| `passenger_liability_exposure` | INFERRED_PROXY | 0.10 | 0.00 / 0.20 | 0.15 | + |
| `rotary_mro_history` | INFERRED_PROXY | 0.04 | 0.04 / 0.00 | 0.00 | - |
| `fleet_age_distribution` | INFERRED_PROXY | 0.04 | 0.04 / 0.03 | 0.00 | + |

**Categorical signal `mission_profile`** — proxy tier: `DIRECT_OBSERVABLE`, source: `metadata.rotary_mission_profile`

| Category | Label | Applied Factor |
|----------|-------|----------------|
| `CORPORATE` | Corporate/VIP Transport | 0.75 |
| `CHARTER` | Charter/Air Taxi | 0.9 |
| `OFFSHORE` | Offshore Oil & Gas | 1.1 |
| `EMS` | Emergency Medical Services | 1.25 |
| `UTILITY` | Utility/External Load | 1.3 |
| `SAR` | Search and Rescue | 1.2 |
| `TRAINING` | Flight Training | 1.15 |

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 | Rotary Wing Risk | 1.30 | 0.45 | 0.45 | 0.40 |
| 2 | Iosa Status | 0.70 | 0.25 | 0.20 | 0.25 |
| 3 | Corporate Footprint | 0.55 | 0.15 | 0.20 | 0.20 |
| 4 | Firm Stability | 0.45 | 0.15 | 0.15 | 0.15 |

**Primary Assessment Driver:** `Rotary Wing Risk` with combined weight of 1.30
**Secondary Driver:** `Iosa Status` with combined weight of 0.70

### Three-Layer Pricing Translation
> *How each pillar's tier score becomes a concrete underwriting action or pricing modifier. This is the bridge between signal observation and premium.*

**Risk -> Underwriting Action & Base Rate**

| Tier | Score Band | Action | Rate / Method |
|------|-----------|--------|---------------|
| PREFERRED | 800-1000 | APPROVE | 0.2% (MULTIPLIER) |
| STANDARD_PLUS | 650-799 | APPROVE | 0.35% (MULTIPLIER) |
| STANDARD | 500-649 | REFER | 0.55% (MULTIPLIER) |
| SUBSTANDARD | 350-499 | REFER | 0.85% (MULTIPLIER) |
| DECLINE | 0-349 | DECLINE | 1.3% (MULTIPLIER) |

**Loss -> Frequency & Severity Modifiers**

| Tier | Score Band | Frequency Modifier | Severity Modifier |
|------|-----------|--------------------|-------------------|
| VERY_LOW | 80-100 | 0.7 | 0.8 |
| LOW | 60-79 | 0.85 | 0.9 |
| MODERATE | 40-59 | 1.0 | 1.0 |
| ELEVATED | 20-39 | 1.15 | 1.15 |
| HIGH | 0-19 | 1.35 | 1.4 |

*Loss modifier is bounded: floor 0.5, cap 1.8.*

**Exposure (size) -> Scale Modifier**

| Band | Score Band | Modifier | Implied Value Range |
|------|-----------|----------|---------------------|
| MICRO | 0-20 | 0.5 | $0 - $10,000,000 |
| SMALL | 21-40 | 0.75 | $10,000,000 - $50,000,000 |
| MEDIUM | 41-60 | 1.0 | $50,000,000 - $250,000,000 |
| LARGE | 61-80 | 1.5 | $250,000,000 - $1,000,000,000 |
| VERY_LARGE | 81-100 | 2.5 | $1,000,000,000 - $5,000,000,000 |

**Exposure (complexity) -> Scale Modifier**

| Band | Score Band | Modifier | Implied Value Range |
|------|-----------|----------|---------------------|
| SIMPLE | 0-20 | 0.85 | n/a |
| MODERATE | 21-40 | 0.95 | n/a |
| COMPLEX | 41-60 | 1.1 | n/a |
| HIGHLY_COMPLEX | 61-80 | 1.3 | n/a |
| EXTREMELY_COMPLEX | 81-100 | 1.6 | n/a |

### Theoretical Premium Calculation (Worked Example)
> *Per the DSI Premium Calculation Methodology v2.0, the full factor chain is:*
> *P_final = (Basis × Base Rate) × ILF_relativity × Deductible_Factor × Loss_Modifier × Exposure_Modifier*

**Worked example — Risk Tier 3 (STANDARD), Loss Tier 4 (ELEVATED), requesting the anchor limit/deductible:**

| Factor | Source | Value |
|--------|--------|-------|
| `hull_value` (rating basis) | Routing-valid assumption | $10,000,000 |
| Base Rate | Risk Tier 3 (STANDARD) | 0.55% |
| **Base Premium** | `hull_value` × Base Rate | **$55,000** |
| ILF relativity | Limit = anchor ($5,000,000) | 1.00 |
| Deductible factor | Deductible = anchor ($100,000) | 1.00 |
| Loss frequency modifier | Loss Tier 4 (ELEVATED) | 1.15 |
| Loss severity modifier | Loss Tier 4 (ELEVATED) | 1.15 |
| **Loss modifier** | Frequency × Severity, bounded [0.5, 1.8] | **1.32** |
| Exposure modifier | Size band SMALL | 0.75 |
| **Technical Premium** | Product of all factors | **$54,553** |

*Basis vs. limit: `hull_value` is the total insured value the rate is applied to — a Base Rate of 0.55% on `hull_value` is the rated cost of risk, not the policy limit. The policy Limit (anchored at $5,000,000) is the maximum payout and scales premium independently via the ILF curve; requesting a limit above the anchor lifts the ILF relativity above 1.00.*

**Loss Tier Sensitivity** — holding Risk Tier 3 and the Exposure modifier constant, the technical premium moves with the Loss tier:

| Loss Tier | Freq Mod | Sev Mod | Loss Modifier | Technical Premium |
|-----------|----------|---------|---------------|-------------------|
| 1 VERY_LOW | 0.70 | 0.80 | 0.56 | $23,100 |
| 2 LOW | 0.85 | 0.90 | 0.77 | $31,556 |
| 3 MODERATE | 1.00 | 1.00 | 1.00 | $41,250 |
| 4 ELEVATED  *(example)* | 1.15 | 1.15 | 1.32 | $54,553 |
| 5 HIGH | 1.35 | 1.40 | 1.80 | $74,250 |


---

## Model: `aerospace_unmanned`
*UAS/drone operations — VLOS, BVLOS, autonomous, commercial drone fleets*

### Routing Protocol (Multiplexer)
- `aviation_segment == UNMANNED`

### Three-Layer Weight Distribution
> *DSI requires that weights for Risk, Loss, and Exposure each sum to 1.0 across all signal groups.*

**Validation:** PASS

| Group | Risk | Loss | Exposure |
|-------|------|------|----------|
| Unmanned Aircraft Systems | 0.50 | 0.55 | 0.50 |
| Regulatory Framework | 0.20 | 0.15 | 0.15 |
| Corporate Footprint | 0.15 | 0.15 | 0.20 |
| Firm Stability | 0.15 | 0.15 | 0.15 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

**Group Definitions:**
- **Unmanned Aircraft Systems:** UAS/drone operations — BVLOS capability, airspace integration, payload risk, regulatory compliance

*Reading the table: a group's three weights are independent. The same group can be a dominant driver of one pillar and a minor input to another — e.g. a group may carry most of the Exposure weight while contributing little to Risk.*

### Signal Architecture Rationale
This configuration contains **7 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `DIRECT_OBSERVABLE` (4 signals): Highest confidence
- `INFERRED_PROXY` (3 signals): Medium confidence

**Signal Count by Group:**
- `technical_infrastructure`: 5 signals
- `public_record`: 2 signals

**Selection Rationale:**
- 57% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Detail by Group
> *Each signal is an objectively observable data point. The weights show how strongly that signal informs each assessment pillar; correlation direction indicates whether a higher observed value increases (+) or decreases (-) the assessed exposure.*

#### Unmanned Aircraft Systems
*UAS/drone operations — BVLOS capability, airspace integration, payload risk, regulatory compliance*

| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `uas_regulatory_compliance` | DIRECT_OBSERVABLE | 0.25 | 0.15 / 0.00 | 0.00 | + |
| `airspace_integration` | INFERRED_PROXY | 0.20 | 0.15 / 0.15 | 0.00 | + |
| `uas_payload_risk` | INFERRED_PROXY | 0.15 | 0.00 / 0.20 | 0.15 | + |
| `uas_fleet_reliability` | DIRECT_OBSERVABLE | 0.20 | 0.20 / 0.10 | 0.00 | + |

**Categorical signal `uas_operational_scope`** — proxy tier: `DIRECT_OBSERVABLE`, source: `metadata.uas_operational_scope`

| Category | Label | Applied Factor |
|----------|-------|----------------|
| `VLOS_RURAL` | Visual Line of Sight — Rural | 0.7 |
| `VLOS_URBAN` | Visual Line of Sight — Urban | 0.9 |
| `BVLOS_RURAL` | Beyond VLOS — Rural | 1.1 |
| `BVLOS_URBAN` | Beyond VLOS — Urban | 1.4 |
| `AUTONOMOUS` | Autonomous Operations | 1.6 |

#### Regulatory Framework
| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `uas_part107_compliance` | DIRECT_OBSERVABLE | 0.04 | 0.04 / 0.00 | 0.00 | - |
| `icao_annex19_sms_proxy` | INFERRED_PROXY | 0.03 | 0.03 / 0.00 | 0.00 | - |

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 | Unmanned Aircraft Systems | 1.55 | 0.50 | 0.55 | 0.50 |
| 2 | Regulatory Framework | 0.50 | 0.20 | 0.15 | 0.15 |
| 3 | Corporate Footprint | 0.50 | 0.15 | 0.15 | 0.20 |
| 4 | Firm Stability | 0.45 | 0.15 | 0.15 | 0.15 |

**Primary Assessment Driver:** `Unmanned Aircraft Systems` with combined weight of 1.55
**Secondary Driver:** `Regulatory Framework` with combined weight of 0.50

### Three-Layer Pricing Translation
> *How each pillar's tier score becomes a concrete underwriting action or pricing modifier. This is the bridge between signal observation and premium.*

**Risk -> Underwriting Action & Base Rate**

| Tier | Score Band | Action | Rate / Method |
|------|-----------|--------|---------------|
| PREFERRED | 800-1000 | APPROVE | 1.5% (MULTIPLIER) |
| STANDARD_PLUS | 650-799 | APPROVE | 2.5% (MULTIPLIER) |
| STANDARD | 500-649 | REFER | 4% (MULTIPLIER) |
| SUBSTANDARD | 350-499 | REFER | 6.5% (MULTIPLIER) |
| DECLINE | 0-349 | DECLINE | 10% (MULTIPLIER) |

**Loss -> Frequency & Severity Modifiers**

| Tier | Score Band | Frequency Modifier | Severity Modifier |
|------|-----------|--------------------|-------------------|
| VERY_LOW | 80-100 | 0.7 | 0.8 |
| LOW | 60-79 | 0.85 | 0.9 |
| MODERATE | 40-59 | 1.0 | 1.0 |
| ELEVATED | 20-39 | 1.15 | 1.15 |
| HIGH | 0-19 | 1.35 | 1.4 |

*Loss modifier is bounded: floor 0.5, cap 1.8.*

**Exposure (size) -> Scale Modifier**

| Band | Score Band | Modifier | Implied Value Range |
|------|-----------|----------|---------------------|
| MICRO | 0-20 | 0.5 | $0 - $10,000,000 |
| SMALL | 21-40 | 0.75 | $10,000,000 - $50,000,000 |
| MEDIUM | 41-60 | 1.0 | $50,000,000 - $250,000,000 |
| LARGE | 61-80 | 1.5 | $250,000,000 - $1,000,000,000 |
| VERY_LARGE | 81-100 | 2.5 | $1,000,000,000 - $5,000,000,000 |

**Exposure (complexity) -> Scale Modifier**

| Band | Score Band | Modifier | Implied Value Range |
|------|-----------|----------|---------------------|
| SIMPLE | 0-20 | 0.85 | n/a |
| MODERATE | 21-40 | 0.95 | n/a |
| COMPLEX | 41-60 | 1.1 | n/a |
| HIGHLY_COMPLEX | 61-80 | 1.3 | n/a |
| EXTREMELY_COMPLEX | 81-100 | 1.6 | n/a |

### Theoretical Premium Calculation (Worked Example)
> *Per the DSI Premium Calculation Methodology v2.0, the full factor chain is:*
> *P_final = (Basis × Base Rate) × ILF_relativity × Deductible_Factor × Loss_Modifier × Exposure_Modifier*

**Worked example — Risk Tier 3 (STANDARD), Loss Tier 4 (ELEVATED), requesting the anchor limit/deductible:**

| Factor | Source | Value |
|--------|--------|-------|
| `hull_value` (rating basis) | Routing-valid assumption | $10,000,000 |
| Base Rate | Risk Tier 3 (STANDARD) | 4% |
| **Base Premium** | `hull_value` × Base Rate | **$400,000** |
| ILF relativity | Limit = anchor ($1,000,000) | 1.00 |
| Deductible factor | Deductible = anchor ($10,000) | 1.00 |
| Loss frequency modifier | Loss Tier 4 (ELEVATED) | 1.15 |
| Loss severity modifier | Loss Tier 4 (ELEVATED) | 1.15 |
| **Loss modifier** | Frequency × Severity, bounded [0.5, 1.8] | **1.32** |
| Exposure modifier | Size band SMALL | 0.75 |
| **Technical Premium** | Product of all factors | **$396,750** |

*Basis vs. limit: `hull_value` is the total insured value the rate is applied to — a Base Rate of 4% on `hull_value` is the rated cost of risk, not the policy limit. The policy Limit (anchored at $1,000,000) is the maximum payout and scales premium independently via the ILF curve; requesting a limit above the anchor lifts the ILF relativity above 1.00.*

**Loss Tier Sensitivity** — holding Risk Tier 3 and the Exposure modifier constant, the technical premium moves with the Loss tier:

| Loss Tier | Freq Mod | Sev Mod | Loss Modifier | Technical Premium |
|-----------|----------|---------|---------------|-------------------|
| 1 VERY_LOW | 0.70 | 0.80 | 0.56 | $168,000 |
| 2 LOW | 0.85 | 0.90 | 0.77 | $229,500 |
| 3 MODERATE | 1.00 | 1.00 | 1.00 | $300,000 |
| 4 ELEVATED  *(example)* | 1.15 | 1.15 | 1.32 | $396,750 |
| 5 HIGH | 1.35 | 1.40 | 1.80 | $540,000 |


---

## Model: `aerospace_mro`
*MRO facility liability — workmanship, hangarkeepers, products/completed operations*

### Routing Protocol (Multiplexer)
- `aviation_segment == MRO`
- `revenue >= 5000000`

### Three-Layer Weight Distribution
> *DSI requires that weights for Risk, Loss, and Exposure each sum to 1.0 across all signal groups.*

**Validation:** PASS

| Group | Risk | Loss | Exposure |
|-------|------|------|----------|
| MRO Facility Risk | 0.50 | 0.55 | 0.45 |
| Regulatory Framework | 0.15 | 0.10 | 0.15 |
| Corporate Footprint | 0.20 | 0.20 | 0.25 |
| Firm Stability | 0.15 | 0.15 | 0.15 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

**Group Definitions:**
- **MRO Facility Risk:** MRO workmanship liability, hangarkeepers exposure, certification compliance, product return risk

*Reading the table: a group's three weights are independent. The same group can be a dominant driver of one pillar and a minor input to another — e.g. a group may carry most of the Exposure weight while contributing little to Risk.*

### Signal Architecture Rationale
This configuration contains **8 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `DIRECT_OBSERVABLE` (4 signals): Highest confidence
- `INFERRED_PROXY` (4 signals): Medium confidence

**Signal Count by Group:**
- `technical_infrastructure`: 6 signals
- `public_record`: 2 signals

**Selection Rationale:**
- 50% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Detail by Group
> *Each signal is an objectively observable data point. The weights show how strongly that signal informs each assessment pillar; correlation direction indicates whether a higher observed value increases (+) or decreases (-) the assessed exposure.*

#### MRO Facility Risk
*MRO workmanship liability, hangarkeepers exposure, certification compliance, product return risk*

| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `mro_certification_scope` | DIRECT_OBSERVABLE | 0.20 | 0.10 / 0.00 | 0.15 | + |
| `workmanship_claims_history` | DIRECT_OBSERVABLE | 0.25 | 0.25 / 0.20 | 0.00 | + |
| `hangarkeepers_exposure` | DIRECT_OBSERVABLE | 0.15 | 0.00 / 0.20 | 0.20 | + |
| `quality_system_maturity` | INFERRED_PROXY | 0.20 | 0.15 / 0.10 | 0.00 | + |
| `parts_traceability` | INFERRED_PROXY | 0.15 | 0.10 / 0.15 | 0.00 | + |
| `rotary_mro_history` | INFERRED_PROXY | 0.03 | 0.03 / 0.00 | 0.00 | - |

#### Regulatory Framework
| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `part_145_repair_station_band` | DIRECT_OBSERVABLE | 0.05 | 0.04 / 0.00 | 0.00 | - |
| `fsims_training_depth` | INFERRED_PROXY | 0.03 | 0.03 / 0.00 | 0.00 | - |

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 | MRO Facility Risk | 1.50 | 0.50 | 0.55 | 0.45 |
| 2 | Corporate Footprint | 0.65 | 0.20 | 0.20 | 0.25 |
| 3 | Firm Stability | 0.45 | 0.15 | 0.15 | 0.15 |
| 4 | Regulatory Framework | 0.40 | 0.15 | 0.10 | 0.15 |

**Primary Assessment Driver:** `MRO Facility Risk` with combined weight of 1.50
**Secondary Driver:** `Corporate Footprint` with combined weight of 0.65

### Three-Layer Pricing Translation
> *How each pillar's tier score becomes a concrete underwriting action or pricing modifier. This is the bridge between signal observation and premium.*

**Risk -> Underwriting Action & Base Rate**

| Tier | Score Band | Action | Rate / Method |
|------|-----------|--------|---------------|
| PREFERRED | 800-1000 | APPROVE | 0.2% (MULTIPLIER) |
| STANDARD_PLUS | 650-799 | APPROVE | 0.35% (MULTIPLIER) |
| STANDARD | 500-649 | REFER | 0.55% (MULTIPLIER) |
| SUBSTANDARD | 350-499 | REFER | 0.85% (MULTIPLIER) |
| DECLINE | 0-349 | DECLINE | 1.3% (MULTIPLIER) |

**Loss -> Frequency & Severity Modifiers**

| Tier | Score Band | Frequency Modifier | Severity Modifier |
|------|-----------|--------------------|-------------------|
| VERY_LOW | 80-100 | 0.7 | 0.8 |
| LOW | 60-79 | 0.85 | 0.9 |
| MODERATE | 40-59 | 1.0 | 1.0 |
| ELEVATED | 20-39 | 1.15 | 1.15 |
| HIGH | 0-19 | 1.35 | 1.4 |

*Loss modifier is bounded: floor 0.5, cap 1.8.*

**Exposure (size) -> Scale Modifier**

| Band | Score Band | Modifier | Implied Value Range |
|------|-----------|----------|---------------------|
| MICRO | 0-20 | 0.5 | $0 - $10,000,000 |
| SMALL | 21-40 | 0.75 | $10,000,000 - $50,000,000 |
| MEDIUM | 41-60 | 1.0 | $50,000,000 - $250,000,000 |
| LARGE | 61-80 | 1.5 | $250,000,000 - $1,000,000,000 |
| VERY_LARGE | 81-100 | 2.5 | $1,000,000,000 - $5,000,000,000 |

**Exposure (complexity) -> Scale Modifier**

| Band | Score Band | Modifier | Implied Value Range |
|------|-----------|----------|---------------------|
| SIMPLE | 0-20 | 0.85 | n/a |
| MODERATE | 21-40 | 0.95 | n/a |
| COMPLEX | 41-60 | 1.1 | n/a |
| HIGHLY_COMPLEX | 61-80 | 1.3 | n/a |
| EXTREMELY_COMPLEX | 81-100 | 1.6 | n/a |

### Theoretical Premium Calculation (Worked Example)
> *Per the DSI Premium Calculation Methodology v2.0, the full factor chain is:*
> *P_final = (Basis × Base Rate) × ILF_relativity × Deductible_Factor × Loss_Modifier × Exposure_Modifier*

**Worked example — Risk Tier 3 (STANDARD), Loss Tier 4 (ELEVATED), requesting the anchor limit/deductible:**

| Factor | Source | Value |
|--------|--------|-------|
| `revenue` (rating basis) | Routing-valid assumption | $15,000,000 |
| Base Rate | Risk Tier 3 (STANDARD) | 0.55% |
| **Base Premium** | `revenue` × Base Rate | **$82,500** |
| ILF relativity | Limit = anchor ($5,000,000) | 1.00 |
| Deductible factor | Deductible = anchor ($100,000) | 1.00 |
| Loss frequency modifier | Loss Tier 4 (ELEVATED) | 1.15 |
| Loss severity modifier | Loss Tier 4 (ELEVATED) | 1.15 |
| **Loss modifier** | Frequency × Severity, bounded [0.5, 1.8] | **1.32** |
| Exposure modifier | Size band SMALL | 0.75 |
| **Technical Premium** | Product of all factors | **$81,830** |

*Basis vs. limit: `revenue` is the total insured value the rate is applied to — a Base Rate of 0.55% on `revenue` is the rated cost of risk, not the policy limit. The policy Limit (anchored at $5,000,000) is the maximum payout and scales premium independently via the ILF curve; requesting a limit above the anchor lifts the ILF relativity above 1.00.*

**Loss Tier Sensitivity** — holding Risk Tier 3 and the Exposure modifier constant, the technical premium moves with the Loss tier:

| Loss Tier | Freq Mod | Sev Mod | Loss Modifier | Technical Premium |
|-----------|----------|---------|---------------|-------------------|
| 1 VERY_LOW | 0.70 | 0.80 | 0.56 | $34,650 |
| 2 LOW | 0.85 | 0.90 | 0.77 | $47,334 |
| 3 MODERATE | 1.00 | 1.00 | 1.00 | $61,875 |
| 4 ELEVATED  *(example)* | 1.15 | 1.15 | 1.32 | $81,830 |
| 5 HIGH | 1.35 | 1.40 | 1.80 | $111,375 |


---

## Model: `aerospace_high_value`
*High-value aviation fleet — airlines, major operators, hull value >$500M*

### Routing Protocol (Multiplexer)
- `hull_value >= 500000000`

### Three-Layer Weight Distribution
> *DSI requires that weights for Risk, Loss, and Exposure each sum to 1.0 across all signal groups.*

**Validation:** PASS

| Group | Risk | Loss | Exposure |
|-------|------|------|----------|
| Iosa Status | 0.40 | 0.30 | 0.25 |
| Fleet Size | 0.25 | 0.30 | 0.35 |
| Corporate Footprint | 0.25 | 0.25 | 0.25 |
| Firm Stability | 0.10 | 0.15 | 0.15 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

*Reading the table: a group's three weights are independent. The same group can be a dominant driver of one pillar and a minor input to another — e.g. a group may carry most of the Exposure weight while contributing little to Risk.*

### Signal Architecture Rationale
This configuration contains **5 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `DIRECT_OBSERVABLE` (2 signals): Highest confidence
- `INFERRED_PROXY` (3 signals): Medium confidence

**Signal Count by Group:**
- `public_record`: 3 signals
- `technical_infrastructure`: 2 signals

**Selection Rationale:**
- 40% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Detail by Group
> *Each signal is an objectively observable data point. The weights show how strongly that signal informs each assessment pillar; correlation direction indicates whether a higher observed value increases (+) or decreases (-) the assessed exposure.*

#### Iosa Status
| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `icao_annex19_sms_proxy` | INFERRED_PROXY | 0.04 | 0.04 / 0.00 | 0.00 | - |
| `asias_incident_count` | DIRECT_OBSERVABLE | 0.05 | 0.04 / 0.04 | 0.00 | + |
| `part_121_135_cert_band` | DIRECT_OBSERVABLE | 0.03 | 0.00 / 0.03 | 0.00 | + |

#### Fleet Size
| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `opensky_route_telemetry` | INFERRED_PROXY | 0.04 | 0.04 / 0.00 | 0.00 | + |
| `fleet_age_distribution` | INFERRED_PROXY | 0.05 | 0.04 / 0.04 | 0.00 | + |

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 | Iosa Status | 0.95 | 0.40 | 0.30 | 0.25 |
| 2 | Fleet Size | 0.90 | 0.25 | 0.30 | 0.35 |
| 3 | Corporate Footprint | 0.75 | 0.25 | 0.25 | 0.25 |
| 4 | Firm Stability | 0.40 | 0.10 | 0.15 | 0.15 |

**Primary Assessment Driver:** `Iosa Status` with combined weight of 0.95
**Secondary Driver:** `Fleet Size` with combined weight of 0.90

### Three-Layer Pricing Translation
> *How each pillar's tier score becomes a concrete underwriting action or pricing modifier. This is the bridge between signal observation and premium.*

**Risk -> Underwriting Action & Base Rate**

| Tier | Score Band | Action | Rate / Method |
|------|-----------|--------|---------------|
| PREFERRED | 800-1000 | APPROVE | 0.06% (MULTIPLIER) |
| STANDARD_PLUS | 650-799 | APPROVE | 0.1% (MULTIPLIER) |
| STANDARD | 500-649 | REFER | 0.16% (MULTIPLIER) |
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

*Loss modifier is bounded: floor 0.5, cap 1.8.*

**Exposure (size) -> Scale Modifier**

| Band | Score Band | Modifier | Implied Value Range |
|------|-----------|----------|---------------------|
| MICRO | 0-20 | 0.5 | $0 - $10,000,000 |
| SMALL | 21-40 | 0.75 | $10,000,000 - $50,000,000 |
| MEDIUM | 41-60 | 1.0 | $50,000,000 - $250,000,000 |
| LARGE | 61-80 | 1.5 | $250,000,000 - $1,000,000,000 |
| VERY_LARGE | 81-100 | 2.5 | $1,000,000,000 - $5,000,000,000 |

**Exposure (complexity) -> Scale Modifier**

| Band | Score Band | Modifier | Implied Value Range |
|------|-----------|----------|---------------------|
| SIMPLE | 0-20 | 0.85 | n/a |
| MODERATE | 21-40 | 0.95 | n/a |
| COMPLEX | 41-60 | 1.1 | n/a |
| HIGHLY_COMPLEX | 61-80 | 1.3 | n/a |
| EXTREMELY_COMPLEX | 81-100 | 1.6 | n/a |

### Theoretical Premium Calculation (Worked Example)
> *Per the DSI Premium Calculation Methodology v2.0, the full factor chain is:*
> *P_final = (Basis × Base Rate) × ILF_relativity × Deductible_Factor × Loss_Modifier × Exposure_Modifier*

**Worked example — Risk Tier 3 (STANDARD), Loss Tier 4 (ELEVATED), requesting the anchor limit/deductible:**

| Factor | Source | Value |
|--------|--------|-------|
| `hull_value` (rating basis) | Routing-valid assumption | $1,500,000,000 |
| Base Rate | Risk Tier 3 (STANDARD) | 0.16% |
| **Base Premium** | `hull_value` × Base Rate | **$2,400,000** |
| ILF relativity | Limit = anchor ($100,000,000) | 1.00 |
| Deductible factor | Deductible = anchor ($2,500,000) | 1.00 |
| Loss frequency modifier | Loss Tier 4 (ELEVATED) | 1.15 |
| Loss severity modifier | Loss Tier 4 (ELEVATED) | 1.15 |
| **Loss modifier** | Frequency × Severity, bounded [0.5, 1.8] | **1.32** |
| Exposure modifier | Size band VERY_LARGE | 2.50 |
| **Technical Premium** | Product of all factors | **$7,935,000** |

*Basis vs. limit: `hull_value` is the total insured value the rate is applied to — a Base Rate of 0.16% on `hull_value` is the rated cost of risk, not the policy limit. The policy Limit (anchored at $100,000,000) is the maximum payout and scales premium independently via the ILF curve; requesting a limit above the anchor lifts the ILF relativity above 1.00.*

**Loss Tier Sensitivity** — holding Risk Tier 3 and the Exposure modifier constant, the technical premium moves with the Loss tier:

| Loss Tier | Freq Mod | Sev Mod | Loss Modifier | Technical Premium |
|-----------|----------|---------|---------------|-------------------|
| 1 VERY_LOW | 0.70 | 0.80 | 0.56 | $3,360,000 |
| 2 LOW | 0.85 | 0.90 | 0.77 | $4,590,000 |
| 3 MODERATE | 1.00 | 1.00 | 1.00 | $6,000,000 |
| 4 ELEVATED  *(example)* | 1.15 | 1.15 | 1.32 | $7,935,000 |
| 5 HIGH | 1.35 | 1.40 | 1.80 | $10,800,000 |



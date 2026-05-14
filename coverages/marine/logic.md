# DSI Logic Document: `MARINE`
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

## Model: `marine_general`
*Marine hull and liability coverage based on observable operator behavior, safety records, and fleet patterns*

### Routing Protocol (Multiplexer)
- `hull_value > 50000000`

### Three-Layer Weight Distribution
> *DSI requires that weights for Risk, Loss, and Exposure each sum to 1.0 across all signal groups.*

**Validation:** PASS

| Group | Risk | Loss | Exposure |
|-------|------|------|----------|
| Network Authority | 0.15 | 0.10 | 0.05 |
| Operational Telemetry | 0.30 | 0.30 | 0.50 |
| Safety Compliance | 0.45 | 0.50 | 0.30 |
| Corporate Footprint | 0.05 | 0.05 | 0.10 |
| Structured Data | 0.05 | 0.05 | 0.05 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

**Group Definitions:**
- **Network Authority:** Classification society, P&I Club, charterer relationships
- **Operational Telemetry:** AIS behavior patterns, dark activity, route risk
- **Safety Compliance:** PSC performance, class status, incident history
- **Corporate Footprint:** Transparency, sustainability reporting, safety culture
- **Structured Data:** RightShip vetting, ESG ratings, credit ratings

*Reading the table: a group's three weights are independent. The same group can be a dominant driver of one pillar and a minor input to another — e.g. a group may carry most of the Exposure weight while contributing little to Risk.*

### Signal Architecture Rationale
This configuration contains **50 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `DIRECT_OBSERVABLE` (32 signals): Highest confidence
- `INFERRED_PROXY` (18 signals): Medium confidence

**Signal Count by Group:**
- `public_record`: 15 signals
- `technical_infrastructure`: 11 signals
- `network_authority`: 10 signals
- `corporate_footprint`: 6 signals
- `structured_data`: 3 signals
- `operator_type`: 1 signals
- `vessel_category`: 1 signals
- `trading_pattern`: 1 signals
- `flag_state_quality`: 1 signals
- `fleet_age_band`: 1 signals

**Selection Rationale:**
- 64% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Detail by Group
> *Each signal is an objectively observable data point. The weights show how strongly that signal informs each assessment pillar; correlation direction indicates whether a higher observed value increases (+) or decreases (-) the assessed exposure.*

#### Network Authority
*Classification society, P&I Club, charterer relationships*

| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `classification_society` | DIRECT_OBSERVABLE | 0.15 | 0.15 / 0.10 | 0.00 | + |
| `pi_club` | DIRECT_OBSERVABLE | 0.15 | 0.00 / 0.15 | 0.00 | + |
| `charterer_quality` | INFERRED_PROXY | 0.15 | 0.00 / 0.00 | 0.10 | + |
| `banking_relationship` | INFERRED_PROXY | 0.10 | 0.00 / 0.10 | 0.00 | + |
| `flag_state` | DIRECT_OBSERVABLE | 0.15 | 0.10 / 0.00 | 0.00 | + |
| `industry_association` | DIRECT_OBSERVABLE | 0.10 | 0.00 / 0.00 | 0.00 | + |
| `technical_manager` | INFERRED_PROXY | 0.10 | 0.10 / 0.00 | 0.00 | + |
| `port_relationship` | INFERRED_PROXY | 0.00 | 0.00 / 0.00 | 0.00 | + |
| `port_state_control` | DIRECT_OBSERVABLE | 0.05 | 0.10 / 0.00 | 0.00 | + |
| `classification_society_quality` | DIRECT_OBSERVABLE | 0.05 | 0.00 / 0.00 | 0.00 | + |

#### Operational Telemetry
*AIS behavior patterns, dark activity, route risk*

| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `ais_compliance` | DIRECT_OBSERVABLE | 0.25 | 0.20 / 0.15 | 0.00 | + |
| `dark_activity` | DIRECT_OBSERVABLE | 0.25 | 0.25 / 0.20 | 0.15 | - |
| `route_risk` | DIRECT_OBSERVABLE | 0.20 | 0.15 / 0.20 | 0.10 | - |
| `psc_region_exposure` | DIRECT_OBSERVABLE | 0.10 | 0.10 / 0.00 | 0.00 | + |
| `operational_efficiency` | INFERRED_PROXY | 0.10 | 0.00 / 0.00 | 0.00 | + |
| `weather_routing` | INFERRED_PROXY | 0.10 | 0.10 / 0.00 | 0.00 | + |
| `fleet_age` | INFERRED_PROXY | 0.30 | 0.25 / 0.15 | 0.10 | - |
| `fleet_stability` | INFERRED_PROXY | 0.20 | 0.10 / 0.00 | 0.00 | + |
| `vessel_quality` | INFERRED_PROXY | 0.20 | 0.20 / 0.15 | 0.00 | + |
| `crew_certification` | DIRECT_OBSERVABLE | 0.15 | 0.15 / 0.00 | 0.00 | + |
| `management_consistency` | INFERRED_PROXY | 0.15 | 0.10 / 0.00 | 0.00 | + |

#### Safety Compliance
*PSC performance, class status, incident history*

| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `psc_detention` | DIRECT_OBSERVABLE | 0.25 | 0.25 / 0.15 | 0.00 | + |
| `psc_deficiency` | DIRECT_OBSERVABLE | 0.20 | 0.20 / 0.00 | 0.00 | + |
| `class_status` | DIRECT_OBSERVABLE | 0.20 | 0.20 / 0.25 | 0.00 | + |
| `ism_compliance` | DIRECT_OBSERVABLE | 0.15 | 0.15 / 0.00 | 0.00 | + |
| `casualty_history` | DIRECT_OBSERVABLE | 0.10 | 0.20 / 0.30 | 0.15 | + |
| `total_loss` | DIRECT_OBSERVABLE | 0.10 | 0.15 / 0.40 | 0.00 | + |
| `sanctions_status` | DIRECT_OBSERVABLE | 0.30 | 0.00 / 0.40 | 0.00 | + |
| `ownership_transparency` | INFERRED_PROXY | 0.20 | 0.00 / 0.00 | 0.15 | + |
| `jurisdiction_risk` | DIRECT_OBSERVABLE | 0.20 | 0.15 / 0.20 | 0.00 | - |
| `sts_pattern` | DIRECT_OBSERVABLE | 0.15 | 0.15 / 0.00 | 0.00 | - |
| `historical_sanctions` | DIRECT_OBSERVABLE | 0.15 | 0.00 / 0.15 | 0.00 | + |
| `imo2020_compliance` | DIRECT_OBSERVABLE | 0.30 | 0.10 / 0.00 | 0.00 | + |
| `bwm_compliance` | DIRECT_OBSERVABLE | 0.25 | 0.10 / 0.00 | 0.00 | + |
| `cii_rating` | DIRECT_OBSERVABLE | 0.25 | 0.00 / 0.00 | 0.00 | + |
| `environmental_incident` | DIRECT_OBSERVABLE | 0.20 | 0.20 / 0.30 | 0.15 | + |

#### Corporate Footprint
*Transparency, sustainability reporting, safety culture*

| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `website_quality` | DIRECT_OBSERVABLE | 0.15 | 0.00 / 0.00 | 0.00 | + |
| `fleet_disclosure` | DIRECT_OBSERVABLE | 0.20 | 0.00 / 0.00 | 0.15 | + |
| `sustainability_reporting` | DIRECT_OBSERVABLE | 0.20 | 0.00 / 0.00 | 0.00 | + |
| `safety_communication` | INFERRED_PROXY | 0.20 | 0.10 / 0.00 | 0.00 | + |
| `crew_welfare` | INFERRED_PROXY | 0.10 | 0.00 / 0.00 | 0.00 | + |
| `industry_presence` | DIRECT_OBSERVABLE | 0.15 | 0.00 / 0.00 | 0.00 | + |

#### Structured Data
*RightShip vetting, ESG ratings, credit ratings*

| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `vetting` | DIRECT_OBSERVABLE | 0.50 | 0.25 / 0.20 | 0.00 | + |
| `esg_rating` | DIRECT_OBSERVABLE | 0.30 | 0.00 / 0.00 | 0.00 | + |
| `credit_rating` | DIRECT_OBSERVABLE | 0.20 | 0.00 / 0.15 | 0.00 | + |

#### operator_type
**Categorical signal `operator_type`** — proxy tier: `INFERRED_PROXY`, source: `metadata.operator_type`

| Category | Label | Applied Factor |
|----------|-------|----------------|
| `MAJOR_LINER` | Major Liner Operator | 0.8 |
| `MAJOR_TANKER` | Major Tanker Operator | 0.9 |
| `MAJOR_BULK` | Major Bulk Operator | 0.95 |
| `REGIONAL_OPERATOR` | Regional Fleet Operator | 1.0 |
| `INDEPENDENT` | Independent Operator | 1.25 |
| `STATE_OWNED` | State-Owned Operator | 1.1 |
| `UNKNOWN` | Unknown Operator | 1.5 |

#### vessel_category
**Categorical signal `vessel_category`** — proxy tier: `INFERRED_PROXY`, source: `metadata.vessel_category`

| Category | Label | Applied Factor |
|----------|-------|----------------|
| `CONTAINER` | Container | 0.9 |
| `TANKER` | Tanker | 1.1 |
| `DRY_BULK` | Dry Bulk | 1.0 |
| `LNG_LPG` | LNG/LPG Carrier | 0.85 |
| `OFFSHORE` | Offshore | 1.3 |
| `PASSENGER` | Passenger | 1.25 |
| `GENERAL_CARGO` | General Cargo | 1.1 |
| `MIXED` | Mixed Fleet | 1.05 |
| `OTHER` | UNKNOWN | 1.0 |

#### trading_pattern
**Categorical signal `trading_pattern`** — proxy tier: `INFERRED_PROXY`, source: `metadata.trading_pattern`

| Category | Label | Applied Factor |
|----------|-------|----------------|
| `LINER_REGULAR` | Liner/Regular Service | 0.85 |
| `SPOT_TRAMP` | Spot/Tramp Trading | 1.15 |
| `INDUSTRIAL` | Industrial Shipping | 0.9 |
| `MIXED` | Mixed Trading | 1.0 |
| `OTHER` | UNKNOWN | 1.0 |

#### flag_state_quality
**Categorical signal `flag_state_quality`** — proxy tier: `INFERRED_PROXY`, source: `n/a`

| Category | Label | Applied Factor |
|----------|-------|----------------|
| `WHITE_LIST` | Paris MoU White List | 0.95 |
| `GREY_LIST` | Paris MoU Grey List | 1.1 |
| `BLACK_LIST` | Paris MoU Black List | 1.4 |
| `OTHER` | UNKNOWN | 1.0 |

#### fleet_age_band
**Categorical signal `fleet_age_band`** — proxy tier: `INFERRED_PROXY`, source: `n/a`

| Category | Label | Applied Factor |
|----------|-------|----------------|
| `AGE_0_5` | 0-5 Years | 0.85 |
| `AGE_5_10` | 5-10 Years | 0.95 |
| `AGE_10_15` | 10-15 Years | 1.05 |
| `AGE_15_20` | 15-20 Years | 1.2 |
| `AGE_20_25` | 20-25 Years | 1.4 |
| `AGE_25_PLUS` | 25+ Years | 1.6 |
| `OTHER` | UNKNOWN | 1.0 |

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 | Safety Compliance | 1.25 | 0.45 | 0.50 | 0.30 |
| 2 | Operational Telemetry | 1.10 | 0.30 | 0.30 | 0.50 |
| 3 | Network Authority | 0.30 | 0.15 | 0.10 | 0.05 |
| 4 | Corporate Footprint | 0.20 | 0.05 | 0.05 | 0.10 |
| 5 | Structured Data | 0.15 | 0.05 | 0.05 | 0.05 |

**Primary Assessment Driver:** `Safety Compliance` with combined weight of 1.25
**Secondary Driver:** `Operational Telemetry` with combined weight of 1.10

### Three-Layer Pricing Translation
> *How each pillar's tier score becomes a concrete underwriting action or pricing modifier. This is the bridge between signal observation and premium.*

**Risk -> Underwriting Action & Base Rate**

| Tier | Score Band | Action | Rate / Method |
|------|-----------|--------|---------------|
| PREFERRED | 800-1000 | APPROVE | 0.15% (MULTIPLIER) |
| STANDARD_PLUS | 650-799 | APPROVE | 0.22% (MULTIPLIER) |
| STANDARD | 500-649 | REFER | 0.32% (MULTIPLIER) |
| SUBSTANDARD | 350-499 | REFER | 0.5% (MULTIPLIER) |
| DECLINE | 0-349 | DECLINE | 0.8% (MULTIPLIER) |

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

### Theoretical Premium Calculation (Worked Example)
> *Per the DSI Premium Calculation Methodology v2.0, the full factor chain is:*
> *P_final = (Basis × Base Rate) × ILF_relativity × Deductible_Factor × Loss_Modifier × Exposure_Modifier*

**Worked example — Risk Tier 3 (STANDARD), Loss Tier 4 (ELEVATED), requesting the anchor limit/deductible:**

| Factor | Source | Value |
|--------|--------|-------|
| `tiv` (rating basis) | Routing-valid assumption | $10,000,000 |
| Base Rate | Risk Tier 3 (STANDARD) | 0.32% |
| **Base Premium** | `tiv` × Base Rate | **$32,000** |
| ILF relativity | Limit = anchor ($10,000,000) | 1.00 |
| Deductible factor | Deductible = anchor ($50,000) | 1.00 |
| Loss frequency modifier | Loss Tier 4 (ELEVATED) | 1.15 |
| Loss severity modifier | Loss Tier 4 (ELEVATED) | 1.15 |
| **Loss modifier** | Frequency × Severity, bounded [0.55, 1.6] | **1.32** |
| Exposure modifier | Size band MEDIUM | 1.00 |
| **Technical Premium** | Product of all factors | **$42,320** |

*Basis vs. limit: `tiv` is the total insured value the rate is applied to — a Base Rate of 0.32% on `tiv` is the rated cost of risk, not the policy limit. The policy Limit (anchored at $10,000,000) is the maximum payout and scales premium independently via the ILF curve; requesting a limit above the anchor lifts the ILF relativity above 1.00.*

**Loss Tier Sensitivity** — holding Risk Tier 3 and the Exposure modifier constant, the technical premium moves with the Loss tier:

| Loss Tier | Freq Mod | Sev Mod | Loss Modifier | Technical Premium |
|-----------|----------|---------|---------------|-------------------|
| 1 VERY_LOW | 0.70 | 0.80 | 0.56 | $17,920 |
| 2 LOW | 0.85 | 0.90 | 0.77 | $24,480 |
| 3 MODERATE | 1.00 | 1.00 | 1.00 | $32,000 |
| 4 ELEVATED  *(example)* | 1.15 | 1.15 | 1.32 | $42,320 |
| 5 HIGH | 1.35 | 1.40 | 1.60 | $51,200 |


---

## Model: `marine_sme`
*Marine coverage for regional fleets, brown-water, and light commercial*

### Routing Protocol (Multiplexer)
- `hull_value <= 50000000`

### Three-Layer Weight Distribution
> *DSI requires that weights for Risk, Loss, and Exposure each sum to 1.0 across all signal groups.*

**Validation:** PASS

| Group | Risk | Loss | Exposure |
|-------|------|------|----------|
| Safety Compliance | 0.30 | 0.35 | 0.20 |
| Operational Telemetry | 0.45 | 0.40 | 0.50 |
| Network Authority | 0.25 | 0.25 | 0.30 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

*Reading the table: a group's three weights are independent. The same group can be a dominant driver of one pillar and a minor input to another — e.g. a group may carry most of the Exposure weight while contributing little to Risk.*

### Signal Architecture Rationale
This configuration contains **15 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `DIRECT_OBSERVABLE` (10 signals): Highest confidence
- `INFERRED_PROXY` (5 signals): Medium confidence

**Signal Count by Group:**
- `technical_infrastructure`: 6 signals
- `public_record`: 4 signals
- `network_authority`: 3 signals
- `vessel_category`: 1 signals
- `fleet_age_band`: 1 signals

**Selection Rationale:**
- 67% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Detail by Group
> *Each signal is an objectively observable data point. The weights show how strongly that signal informs each assessment pillar; correlation direction indicates whether a higher observed value increases (+) or decreases (-) the assessed exposure.*

#### Safety Compliance
| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `psc_detention` | DIRECT_OBSERVABLE | 0.50 | 0.60 / 0.00 | 0.00 | + |
| `casualty_history` | DIRECT_OBSERVABLE | 0.50 | 0.00 / 0.40 | 0.00 | + |
| `class_status` | DIRECT_OBSERVABLE | 0.30 | 0.00 / 0.30 | 0.00 | + |
| `ism_compliance` | DIRECT_OBSERVABLE | 0.20 | 0.30 / 0.00 | 0.00 | + |

#### Operational Telemetry
| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `ais_compliance` | DIRECT_OBSERVABLE | 0.35 | 0.35 / 0.00 | 0.20 | + |
| `route_risk` | DIRECT_OBSERVABLE | 0.35 | 0.35 / 0.00 | 0.30 | - |
| `operational_efficiency` | INFERRED_PROXY | 0.30 | 0.30 / 0.00 | 0.25 | + |
| `fleet_stability` | INFERRED_PROXY | 0.50 | 0.50 / 0.00 | 0.50 | + |
| `crew_certification` | DIRECT_OBSERVABLE | 0.45 | 0.45 / 0.00 | 0.45 | + |
| `vessel_quality` | INFERRED_PROXY | 0.05 | 0.05 / 0.00 | 0.05 | + |

#### Network Authority
| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `flag_state` | DIRECT_OBSERVABLE | 0.35 | 0.35 / 0.00 | 0.30 | + |
| `classification_society` | DIRECT_OBSERVABLE | 0.35 | 0.00 / 0.35 | 0.20 | + |
| `pi_club` | DIRECT_OBSERVABLE | 0.30 | 0.00 / 0.30 | 0.25 | + |

#### vessel_category
**Categorical signal `vessel_category`** — proxy tier: `INFERRED_PROXY`, source: `metadata.vessel_category`

| Category | Label | Applied Factor |
|----------|-------|----------------|
| `WORKBOAT_TUG` | Workboat/Tug | 0.85 |
| `FISHING` | Commercial Fishing | 1.3 |
| `PASSENGER_FERRY` | Passenger/Ferry | 1.2 |
| `COASTAL_CARGO` | Coastal Cargo | 1.0 |
| `OTHER` | Other | 1.1 |

#### fleet_age_band
**Categorical signal `fleet_age_band`** — proxy tier: `INFERRED_PROXY`, source: `n/a`

| Category | Label | Applied Factor |
|----------|-------|----------------|
| `AGE_0_10` | 0-10 Years | 0.9 |
| `AGE_10_20` | 10-20 Years | 1.0 |
| `AGE_20_PLUS` | 20+ Years | 1.35 |
| `OTHER` | UNKNOWN | 1.1 |

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 | Operational Telemetry | 1.35 | 0.45 | 0.40 | 0.50 |
| 2 | Safety Compliance | 0.85 | 0.30 | 0.35 | 0.20 |
| 3 | Network Authority | 0.80 | 0.25 | 0.25 | 0.30 |

**Primary Assessment Driver:** `Operational Telemetry` with combined weight of 1.35
**Secondary Driver:** `Safety Compliance` with combined weight of 0.85

### Three-Layer Pricing Translation
> *How each pillar's tier score becomes a concrete underwriting action or pricing modifier. This is the bridge between signal observation and premium.*

**Risk -> Underwriting Action & Base Rate**

| Tier | Score Band | Action | Rate / Method |
|------|-----------|--------|---------------|
| PREFERRED | 800-1000 | APPROVE | 0.35% (MULTIPLIER) |
| STANDARD_PLUS | 650-799 | APPROVE | 0.5% (MULTIPLIER) |
| STANDARD | 500-649 | REFER | 0.8% (MULTIPLIER) |
| SUBSTANDARD | 350-499 | REFER | 1.25% (MULTIPLIER) |
| DECLINE | 0-349 | DECLINE | 2% (MULTIPLIER) |

**Loss -> Frequency & Severity Modifiers**

| Tier | Score Band | Frequency Modifier | Severity Modifier |
|------|-----------|--------------------|-------------------|
| VERY_LOW | 80-100 | 0.7 | 0.8 |
| LOW | 60-79 | 0.85 | 0.9 |
| MODERATE | 40-59 | 1.0 | 1.0 |
| ELEVATED | 20-39 | 1.15 | 1.15 |
| HIGH | 0-19 | 1.35 | 1.4 |

*Loss modifier is bounded: floor 0.6, cap 1.5.*

**Exposure (size) -> Scale Modifier**

| Band | Score Band | Modifier | Implied Value Range |
|------|-----------|----------|---------------------|
| MICRO | 0-33 | 0.85 | n/a |
| SMALL | 34-66 | 1.0 | n/a |
| MEDIUM | 67-100 | 1.15 | n/a |

**Exposure (complexity) -> Scale Modifier**

| Band | Score Band | Modifier | Implied Value Range |
|------|-----------|----------|---------------------|
| SIMPLE | 0-40 | 0.9 | n/a |
| MODERATE | 41-70 | 1.0 | n/a |
| COMPLEX | 71-100 | 1.15 | n/a |

### Theoretical Premium Calculation (Worked Example)
> *Per the DSI Premium Calculation Methodology v2.0, the full factor chain is:*
> *P_final = (Basis × Base Rate) × ILF_relativity × Deductible_Factor × Loss_Modifier × Exposure_Modifier*

**Worked example — Risk Tier 3 (STANDARD), Loss Tier 4 (ELEVATED), requesting the anchor limit/deductible:**

| Factor | Source | Value |
|--------|--------|-------|
| `hull_value` (rating basis) | Routing-valid assumption | $25,000,000 |
| Base Rate | Risk Tier 3 (STANDARD) | 0.8% |
| **Base Premium** | `hull_value` × Base Rate | **$200,000** |
| ILF relativity | Limit = anchor ($5,000,000) | 1.00 |
| Deductible factor | Deductible = anchor ($10,000) | 1.00 |
| Loss frequency modifier | Loss Tier 4 (ELEVATED) | 1.15 |
| Loss severity modifier | Loss Tier 4 (ELEVATED) | 1.15 |
| **Loss modifier** | Frequency × Severity, bounded [0.6, 1.5] | **1.32** |
| Exposure modifier | Size band n/a | 1.00 |
| **Technical Premium** | Product of all factors | **$264,500** |

*Basis vs. limit: `hull_value` is the total insured value the rate is applied to — a Base Rate of 0.8% on `hull_value` is the rated cost of risk, not the policy limit. The policy Limit (anchored at $5,000,000) is the maximum payout and scales premium independently via the ILF curve; requesting a limit above the anchor lifts the ILF relativity above 1.00.*

**Loss Tier Sensitivity** — holding Risk Tier 3 and the Exposure modifier constant, the technical premium moves with the Loss tier:

| Loss Tier | Freq Mod | Sev Mod | Loss Modifier | Technical Premium |
|-----------|----------|---------|---------------|-------------------|
| 1 VERY_LOW | 0.70 | 0.80 | 0.60 | $120,000 |
| 2 LOW | 0.85 | 0.90 | 0.77 | $153,000 |
| 3 MODERATE | 1.00 | 1.00 | 1.00 | $200,000 |
| 4 ELEVATED  *(example)* | 1.15 | 1.15 | 1.32 | $264,500 |
| 5 HIGH | 1.35 | 1.40 | 1.50 | $300,000 |


---

## Model: `marine_cargo`
*Marine cargo insurance — commodity-specific, transit risk, storage exposure*

### Routing Protocol (Multiplexer)
- `product_type == cargo`
- `tiv >= 5000000`

### Three-Layer Weight Distribution
> *DSI requires that weights for Risk, Loss, and Exposure each sum to 1.0 across all signal groups.*

**Validation:** PASS

| Group | Risk | Loss | Exposure |
|-------|------|------|----------|
| Cargo Quality | 0.45 | 0.45 | 0.40 |
| Port State & Regulatory Compliance | 0.25 | 0.25 | 0.20 |
| Trading Pattern | 0.20 | 0.20 | 0.30 |
| Corporate Footprint | 0.10 | 0.10 | 0.10 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

**Group Definitions:**
- **Cargo Quality:** Cargo type, packaging, transit mode, storage conditions, and theft/pilferage exposure
- **Port State & Regulatory Compliance:** PSC detention history, ISM/ISPS audit quality, sanctions screening, class survey status

*Reading the table: a group's three weights are independent. The same group can be a dominant driver of one pillar and a minor input to another — e.g. a group may carry most of the Exposure weight while contributing little to Risk.*

### Signal Architecture Rationale
This configuration contains **15 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `DIRECT_OBSERVABLE` (8 signals): Highest confidence
- `INFERRED_PROXY` (7 signals): Medium confidence

**Signal Count by Group:**
- `public_record`: 8 signals
- `technical_infrastructure`: 7 signals

**Selection Rationale:**
- 53% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Detail by Group
> *Each signal is an objectively observable data point. The weights show how strongly that signal informs each assessment pillar; correlation direction indicates whether a higher observed value increases (+) or decreases (-) the assessed exposure.*

#### Cargo Quality
*Cargo type, packaging, transit mode, storage conditions, and theft/pilferage exposure*

| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `packaging_quality` | INFERRED_PROXY | 0.15 | 0.20 / 0.10 | 0.00 | + |
| `storage_exposure` | INFERRED_PROXY | 0.10 | 0.15 / 0.10 | 0.10 | + |
| `theft_pilferage_exposure` | INFERRED_PROXY | 0.15 | 0.20 / 0.15 | 0.00 | + |
| `temperature_control` | INFERRED_PROXY | 0.10 | 0.15 / 0.15 | 0.00 | + |
| `vessel_age_profile_curve` | INFERRED_PROXY | 0.04 | 0.04 / 0.04 | 0.00 | + |

**Categorical signal `cargo_commodity_class`** — proxy tier: `DIRECT_OBSERVABLE`, source: `metadata.cargo_commodity_class`

| Category | Label | Applied Factor |
|----------|-------|----------------|
| `LOW_HAZARD` | Low Hazard (Finished Goods/Dry Cargo) | 0.8 |
| `MODERATE` | Moderate (Machinery/Electronics/Vehicles) | 1.0 |
| `HIGH_VALUE` | High Value (Pharmaceuticals/Fine Art/Bullion) | 1.3 |
| `PERISHABLE` | Perishable (Reefer Cargo/Livestock) | 1.25 |
| `HAZMAT` | Hazardous Materials (IMO Classes) | 1.5 |
| `PROJECT` | Project Cargo (Oversized/Heavy Lift) | 1.35 |

**Categorical signal `transit_mode`** — proxy tier: `DIRECT_OBSERVABLE`, source: `metadata.transit_mode`

| Category | Label | Applied Factor |
|----------|-------|----------------|
| `OCEAN_DIRECT` | Direct Ocean (Port-to-Port) | 0.85 |
| `OCEAN_TRANSHIP` | Ocean with Transhipment | 1.1 |
| `MULTIMODAL` | Multimodal (Ocean + Land) | 1.15 |
| `INLAND` | Inland Waterway Only | 0.9 |
| `AIR_SEA` | Air-Sea Combined | 1.05 |

#### Port State & Regulatory Compliance
*PSC detention history, ISM/ISPS audit quality, sanctions screening, class survey status*

| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `psc_detention_rate` | DIRECT_OBSERVABLE | 0.25 | 0.20 / 0.10 | 0.00 | + |
| `ism_audit_quality` | DIRECT_OBSERVABLE | 0.25 | 0.15 / 0.00 | 0.00 | + |
| `isps_compliance` | DIRECT_OBSERVABLE | 0.15 | 0.10 / 0.00 | 0.00 | + |
| `sanctions_screening_depth` | INFERRED_PROXY | 0.20 | 0.00 / 0.15 | 0.00 | + |
| `class_survey_currency` | DIRECT_OBSERVABLE | 0.15 | 0.10 / 0.00 | 0.00 | + |
| `paris_mou_detention_history` | DIRECT_OBSERVABLE | 0.04 | 0.04 / 0.03 | 0.00 | + |
| `tokyo_mou_detention_history` | DIRECT_OBSERVABLE | 0.04 | 0.04 / 0.03 | 0.00 | + |
| `flag_of_convenience_proxy` | INFERRED_PROXY | 0.03 | 0.03 / 0.00 | 0.00 | + |

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 | Cargo Quality | 1.30 | 0.45 | 0.45 | 0.40 |
| 2 | Port State & Regulatory Compliance | 0.70 | 0.25 | 0.25 | 0.20 |
| 3 | Trading Pattern | 0.70 | 0.20 | 0.20 | 0.30 |
| 4 | Corporate Footprint | 0.30 | 0.10 | 0.10 | 0.10 |

**Primary Assessment Driver:** `Cargo Quality` with combined weight of 1.30
**Secondary Driver:** `Port State & Regulatory Compliance` with combined weight of 0.70

### Three-Layer Pricing Translation
> *How each pillar's tier score becomes a concrete underwriting action or pricing modifier. This is the bridge between signal observation and premium.*

**Risk -> Underwriting Action & Base Rate**

| Tier | Score Band | Action | Rate / Method |
|------|-----------|--------|---------------|
| PREFERRED | 800-1000 | APPROVE | 0.1% (MULTIPLIER) |
| STANDARD_PLUS | 650-799 | APPROVE | 0.18% (MULTIPLIER) |
| STANDARD | 500-649 | REFER | 0.3% (MULTIPLIER) |
| SUBSTANDARD | 350-499 | REFER | 0.5% (MULTIPLIER) |
| DECLINE | 0-349 | DECLINE | 0.75% (MULTIPLIER) |

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
| `tiv` (rating basis) | Routing-valid assumption | $15,000,000 |
| Base Rate | Risk Tier 3 (STANDARD) | 0.3% |
| **Base Premium** | `tiv` × Base Rate | **$45,000** |
| ILF relativity | Limit = anchor ($5,000,000) | 1.00 |
| Deductible factor | Deductible = anchor ($50,000) | 1.00 |
| Loss frequency modifier | Loss Tier 4 (ELEVATED) | 1.15 |
| Loss severity modifier | Loss Tier 4 (ELEVATED) | 1.15 |
| **Loss modifier** | Frequency × Severity, bounded [0.5, 1.8] | **1.32** |
| Exposure modifier | Size band SMALL | 0.75 |
| **Technical Premium** | Product of all factors | **$44,634** |

*Basis vs. limit: `tiv` is the total insured value the rate is applied to — a Base Rate of 0.3% on `tiv` is the rated cost of risk, not the policy limit. The policy Limit (anchored at $5,000,000) is the maximum payout and scales premium independently via the ILF curve; requesting a limit above the anchor lifts the ILF relativity above 1.00.*

**Loss Tier Sensitivity** — holding Risk Tier 3 and the Exposure modifier constant, the technical premium moves with the Loss tier:

| Loss Tier | Freq Mod | Sev Mod | Loss Modifier | Technical Premium |
|-----------|----------|---------|---------------|-------------------|
| 1 VERY_LOW | 0.70 | 0.80 | 0.56 | $18,900 |
| 2 LOW | 0.85 | 0.90 | 0.77 | $25,819 |
| 3 MODERATE | 1.00 | 1.00 | 1.00 | $33,750 |
| 4 ELEVATED  *(example)* | 1.15 | 1.15 | 1.32 | $44,634 |
| 5 HIGH | 1.35 | 1.40 | 1.80 | $60,750 |


---

## Model: `marine_tanker`
*Tanker fleet hull & liability — crude, product, chemical, gas carriers*

### Routing Protocol (Multiplexer)
- `operation_segment == TANKER`
- `hull_value >= 50000000`

### Three-Layer Weight Distribution
> *DSI requires that weights for Risk, Loss, and Exposure each sum to 1.0 across all signal groups.*

**Validation:** PASS

| Group | Risk | Loss | Exposure |
|-------|------|------|----------|
| Tanker Risk | 0.45 | 0.45 | 0.40 |
| Port State & Regulatory Compliance | 0.30 | 0.25 | 0.25 |
| Trading Pattern | 0.15 | 0.20 | 0.25 |
| Corporate Footprint | 0.10 | 0.10 | 0.10 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

**Group Definitions:**
- **Tanker Risk:** Tanker-specific risk — vetting status, pollution exposure, cargo compatibility, hull construction
- **Port State & Regulatory Compliance:** PSC detention history, ISM/ISPS audit quality, sanctions screening, class survey status

*Reading the table: a group's three weights are independent. The same group can be a dominant driver of one pillar and a minor input to another — e.g. a group may carry most of the Exposure weight while contributing little to Risk.*

### Signal Architecture Rationale
This configuration contains **14 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `DIRECT_OBSERVABLE` (7 signals): Highest confidence
- `INFERRED_PROXY` (7 signals): Medium confidence

**Signal Count by Group:**
- `public_record`: 8 signals
- `technical_infrastructure`: 6 signals

**Selection Rationale:**
- 50% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Detail by Group
> *Each signal is an objectively observable data point. The weights show how strongly that signal informs each assessment pillar; correlation direction indicates whether a higher observed value increases (+) or decreases (-) the assessed exposure.*

#### Tanker Risk
*Tanker-specific risk — vetting status, pollution exposure, cargo compatibility, hull construction*

| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `tanker_vetting_status` | DIRECT_OBSERVABLE | 0.25 | 0.15 / 0.10 | 0.00 | + |
| `pollution_liability_exposure` | INFERRED_PROXY | 0.20 | 0.00 / 0.30 | 0.20 | + |
| `double_hull_compliance` | DIRECT_OBSERVABLE | 0.20 | 0.15 / 0.20 | 0.00 | + |
| `cargo_compatibility` | INFERRED_PROXY | 0.10 | 0.20 / 0.10 | 0.00 | + |
| `sts_operations` | INFERRED_PROXY | 0.10 | 0.15 / 0.10 | 0.00 | + |
| `sts_transfer_density` | INFERRED_PROXY | 0.04 | 0.04 / 0.00 | 0.00 | + |

#### Port State & Regulatory Compliance
*PSC detention history, ISM/ISPS audit quality, sanctions screening, class survey status*

| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `psc_detention_rate` | DIRECT_OBSERVABLE | 0.25 | 0.20 / 0.10 | 0.00 | + |
| `ism_audit_quality` | DIRECT_OBSERVABLE | 0.25 | 0.15 / 0.00 | 0.00 | + |
| `isps_compliance` | DIRECT_OBSERVABLE | 0.15 | 0.10 / 0.00 | 0.00 | + |
| `sanctions_screening_depth` | INFERRED_PROXY | 0.20 | 0.00 / 0.15 | 0.00 | + |
| `class_survey_currency` | DIRECT_OBSERVABLE | 0.15 | 0.10 / 0.00 | 0.00 | + |
| `ais_dark_activity_rate` | INFERRED_PROXY | 0.05 | 0.04 / 0.05 | 0.00 | + |
| `ais_spoofing_signal` | INFERRED_PROXY | 0.04 | 0.04 / 0.00 | 0.00 | + |
| `paris_mou_detention_history` | DIRECT_OBSERVABLE | 0.05 | 0.04 / 0.04 | 0.00 | + |

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 | Tanker Risk | 1.30 | 0.45 | 0.45 | 0.40 |
| 2 | Port State & Regulatory Compliance | 0.80 | 0.30 | 0.25 | 0.25 |
| 3 | Trading Pattern | 0.60 | 0.15 | 0.20 | 0.25 |
| 4 | Corporate Footprint | 0.30 | 0.10 | 0.10 | 0.10 |

**Primary Assessment Driver:** `Tanker Risk` with combined weight of 1.30
**Secondary Driver:** `Port State & Regulatory Compliance` with combined weight of 0.80

### Three-Layer Pricing Translation
> *How each pillar's tier score becomes a concrete underwriting action or pricing modifier. This is the bridge between signal observation and premium.*

**Risk -> Underwriting Action & Base Rate**

| Tier | Score Band | Action | Rate / Method |
|------|-----------|--------|---------------|
| PREFERRED | 800-1000 | APPROVE | 0.18% (MULTIPLIER) |
| STANDARD_PLUS | 650-799 | APPROVE | 0.28% (MULTIPLIER) |
| STANDARD | 500-649 | REFER | 0.42% (MULTIPLIER) |
| SUBSTANDARD | 350-499 | REFER | 0.65% (MULTIPLIER) |
| DECLINE | 0-349 | DECLINE | 0.95% (MULTIPLIER) |

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
| Base Rate | Risk Tier 3 (STANDARD) | 0.42% |
| **Base Premium** | `hull_value` × Base Rate | **$630,000** |
| ILF relativity | Limit = anchor ($10,000,000) | 1.00 |
| Deductible factor | Deductible = anchor ($250,000) | 1.00 |
| Loss frequency modifier | Loss Tier 4 (ELEVATED) | 1.15 |
| Loss severity modifier | Loss Tier 4 (ELEVATED) | 1.15 |
| **Loss modifier** | Frequency × Severity, bounded [0.5, 1.8] | **1.32** |
| Exposure modifier | Size band MEDIUM | 1.00 |
| **Technical Premium** | Product of all factors | **$833,175** |

*Basis vs. limit: `hull_value` is the total insured value the rate is applied to — a Base Rate of 0.42% on `hull_value` is the rated cost of risk, not the policy limit. The policy Limit (anchored at $10,000,000) is the maximum payout and scales premium independently via the ILF curve; requesting a limit above the anchor lifts the ILF relativity above 1.00.*

**Loss Tier Sensitivity** — holding Risk Tier 3 and the Exposure modifier constant, the technical premium moves with the Loss tier:

| Loss Tier | Freq Mod | Sev Mod | Loss Modifier | Technical Premium |
|-----------|----------|---------|---------------|-------------------|
| 1 VERY_LOW | 0.70 | 0.80 | 0.56 | $352,800 |
| 2 LOW | 0.85 | 0.90 | 0.77 | $481,950 |
| 3 MODERATE | 1.00 | 1.00 | 1.00 | $630,000 |
| 4 ELEVATED  *(example)* | 1.15 | 1.15 | 1.32 | $833,175 |
| 5 HIGH | 1.35 | 1.40 | 1.80 | $1,134,000 |


---

## Model: `marine_offshore`
*Offshore marine units — FPSOs, rigs, OSVs, construction vessels, wind installation*

### Routing Protocol (Multiplexer)
- `operation_segment == OFFSHORE`
- `hull_value >= 50000000`

### Three-Layer Weight Distribution
> *DSI requires that weights for Risk, Loss, and Exposure each sum to 1.0 across all signal groups.*

**Validation:** PASS

| Group | Risk | Loss | Exposure |
|-------|------|------|----------|
| Offshore Marine | 0.50 | 0.45 | 0.45 |
| Port State & Regulatory Compliance | 0.25 | 0.25 | 0.20 |
| Trading Pattern | 0.10 | 0.15 | 0.20 |
| Corporate Footprint | 0.15 | 0.15 | 0.15 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

**Group Definitions:**
- **Offshore Marine:** Offshore unit risk — FPSO, jack-up, semi-sub, construction vessel, mooring integrity
- **Port State & Regulatory Compliance:** PSC detention history, ISM/ISPS audit quality, sanctions screening, class survey status

*Reading the table: a group's three weights are independent. The same group can be a dominant driver of one pillar and a minor input to another — e.g. a group may carry most of the Exposure weight while contributing little to Risk.*

### Signal Architecture Rationale
This configuration contains **13 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `DIRECT_OBSERVABLE` (9 signals): Highest confidence
- `INFERRED_PROXY` (4 signals): Medium confidence

**Signal Count by Group:**
- `public_record`: 7 signals
- `technical_infrastructure`: 6 signals

**Selection Rationale:**
- 69% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Detail by Group
> *Each signal is an objectively observable data point. The weights show how strongly that signal informs each assessment pillar; correlation direction indicates whether a higher observed value increases (+) or decreases (-) the assessed exposure.*

#### Offshore Marine
*Offshore unit risk — FPSO, jack-up, semi-sub, construction vessel, mooring integrity*

| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `mooring_integrity` | INFERRED_PROXY | 0.20 | 0.15 / 0.20 | 0.00 | + |
| `dp_system_reliability` | DIRECT_OBSERVABLE | 0.20 | 0.20 / 0.15 | 0.00 | + |
| `metocean_exposure` | DIRECT_OBSERVABLE | 0.15 | 0.15 / 0.15 | 0.15 | + |
| `offshore_class_compliance` | DIRECT_OBSERVABLE | 0.15 | 0.10 / 0.00 | 0.00 | + |
| `vessel_age_profile_curve` | INFERRED_PROXY | 0.03 | 0.03 / 0.03 | 0.00 | + |

**Categorical signal `unit_type`** — proxy tier: `DIRECT_OBSERVABLE`, source: `metadata.offshore_unit_type`

| Category | Label | Applied Factor |
|----------|-------|----------------|
| `FPSO` | FPSO/FSO | 1.2 |
| `JACKUP` | Jack-Up Rig | 1.1 |
| `SEMI_SUB` | Semi-Submersible | 1.25 |
| `DRILL_SHIP` | Drill Ship | 1.15 |
| `OSV` | Offshore Supply Vessel | 0.9 |
| `CONSTRUCTION` | Construction/Pipe-Lay Vessel | 1.3 |
| `WIND_INSTALLATION` | Wind Turbine Installation Vessel | 1.15 |

#### Port State & Regulatory Compliance
*PSC detention history, ISM/ISPS audit quality, sanctions screening, class survey status*

| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `psc_detention_rate` | DIRECT_OBSERVABLE | 0.25 | 0.20 / 0.10 | 0.00 | + |
| `ism_audit_quality` | DIRECT_OBSERVABLE | 0.25 | 0.15 / 0.00 | 0.00 | + |
| `isps_compliance` | DIRECT_OBSERVABLE | 0.15 | 0.10 / 0.00 | 0.00 | + |
| `sanctions_screening_depth` | INFERRED_PROXY | 0.20 | 0.00 / 0.15 | 0.00 | + |
| `class_survey_currency` | DIRECT_OBSERVABLE | 0.15 | 0.10 / 0.00 | 0.00 | + |
| `class_society_transfer_frequency` | INFERRED_PROXY | 0.04 | 0.00 / 0.04 | 0.00 | + |
| `imo_cic_campaign_results` | DIRECT_OBSERVABLE | 0.04 | 0.03 / 0.00 | 0.00 | + |

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 | Offshore Marine | 1.40 | 0.50 | 0.45 | 0.45 |
| 2 | Port State & Regulatory Compliance | 0.70 | 0.25 | 0.25 | 0.20 |
| 3 | Trading Pattern | 0.45 | 0.10 | 0.15 | 0.20 |
| 4 | Corporate Footprint | 0.45 | 0.15 | 0.15 | 0.15 |

**Primary Assessment Driver:** `Offshore Marine` with combined weight of 1.40
**Secondary Driver:** `Port State & Regulatory Compliance` with combined weight of 0.70

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
| Base Rate | Risk Tier 3 (STANDARD) | 0.55% |
| **Base Premium** | `hull_value` × Base Rate | **$825,000** |
| ILF relativity | Limit = anchor ($25,000,000) | 1.00 |
| Deductible factor | Deductible = anchor ($500,000) | 1.00 |
| Loss frequency modifier | Loss Tier 4 (ELEVATED) | 1.15 |
| Loss severity modifier | Loss Tier 4 (ELEVATED) | 1.15 |
| **Loss modifier** | Frequency × Severity, bounded [0.5, 1.8] | **1.32** |
| Exposure modifier | Size band MEDIUM | 1.00 |
| **Technical Premium** | Product of all factors | **$1,091,062** |

*Basis vs. limit: `hull_value` is the total insured value the rate is applied to — a Base Rate of 0.55% on `hull_value` is the rated cost of risk, not the policy limit. The policy Limit (anchored at $25,000,000) is the maximum payout and scales premium independently via the ILF curve; requesting a limit above the anchor lifts the ILF relativity above 1.00.*

**Loss Tier Sensitivity** — holding Risk Tier 3 and the Exposure modifier constant, the technical premium moves with the Loss tier:

| Loss Tier | Freq Mod | Sev Mod | Loss Modifier | Technical Premium |
|-----------|----------|---------|---------------|-------------------|
| 1 VERY_LOW | 0.70 | 0.80 | 0.56 | $462,000 |
| 2 LOW | 0.85 | 0.90 | 0.77 | $631,125 |
| 3 MODERATE | 1.00 | 1.00 | 1.00 | $825,000 |
| 4 ELEVATED  *(example)* | 1.15 | 1.15 | 1.32 | $1,091,062 |
| 5 HIGH | 1.35 | 1.40 | 1.80 | $1,485,000 |


---

## Model: `marine_war_risk`
*Marine war risk — hull war, strikes, piracy, confiscation, terrorism*

### Routing Protocol (Multiplexer)
- `product_type == war_risks`

### Three-Layer Weight Distribution
> *DSI requires that weights for Risk, Loss, and Exposure each sum to 1.0 across all signal groups.*

**Validation:** PASS

| Group | Risk | Loss | Exposure |
|-------|------|------|----------|
| Trading Pattern | 0.45 | 0.45 | 0.45 |
| Port State & Regulatory Compliance | 0.35 | 0.30 | 0.25 |
| Fleet Age Band | 0.10 | 0.10 | 0.15 |
| Corporate Footprint | 0.10 | 0.15 | 0.15 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

**Group Definitions:**
- **Port State & Regulatory Compliance:** PSC detention history, ISM/ISPS audit quality, sanctions screening, class survey status

*Reading the table: a group's three weights are independent. The same group can be a dominant driver of one pillar and a minor input to another — e.g. a group may carry most of the Exposure weight while contributing little to Risk.*

### Signal Architecture Rationale
This configuration contains **8 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `DIRECT_OBSERVABLE` (4 signals): Highest confidence
- `INFERRED_PROXY` (4 signals): Medium confidence

**Signal Count by Group:**
- `public_record`: 8 signals

**Selection Rationale:**
- 50% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Detail by Group
> *Each signal is an objectively observable data point. The weights show how strongly that signal informs each assessment pillar; correlation direction indicates whether a higher observed value increases (+) or decreases (-) the assessed exposure.*

#### Port State & Regulatory Compliance
*PSC detention history, ISM/ISPS audit quality, sanctions screening, class survey status*

| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `psc_detention_rate` | DIRECT_OBSERVABLE | 0.25 | 0.20 / 0.10 | 0.00 | + |
| `ism_audit_quality` | DIRECT_OBSERVABLE | 0.25 | 0.15 / 0.00 | 0.00 | + |
| `isps_compliance` | DIRECT_OBSERVABLE | 0.15 | 0.10 / 0.00 | 0.00 | + |
| `sanctions_screening_depth` | INFERRED_PROXY | 0.20 | 0.00 / 0.15 | 0.00 | + |
| `class_survey_currency` | DIRECT_OBSERVABLE | 0.15 | 0.10 / 0.00 | 0.00 | + |
| `piracy_corridor_exposure` | INFERRED_PROXY | 0.06 | 0.05 / 0.05 | 0.00 | + |
| `ais_dark_activity_rate` | INFERRED_PROXY | 0.04 | 0.04 / 0.00 | 0.00 | + |
| `flag_of_convenience_proxy` | INFERRED_PROXY | 0.03 | 0.00 / 0.03 | 0.00 | + |

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 | Trading Pattern | 1.35 | 0.45 | 0.45 | 0.45 |
| 2 | Port State & Regulatory Compliance | 0.90 | 0.35 | 0.30 | 0.25 |
| 3 | Corporate Footprint | 0.40 | 0.10 | 0.15 | 0.15 |
| 4 | Fleet Age Band | 0.35 | 0.10 | 0.10 | 0.15 |

**Primary Assessment Driver:** `Trading Pattern` with combined weight of 1.35
**Secondary Driver:** `Port State & Regulatory Compliance` with combined weight of 0.90

### Three-Layer Pricing Translation
> *How each pillar's tier score becomes a concrete underwriting action or pricing modifier. This is the bridge between signal observation and premium.*

**Risk -> Underwriting Action & Base Rate**

| Tier | Score Band | Action | Rate / Method |
|------|-----------|--------|---------------|
| PREFERRED | 800-1000 | APPROVE | 0.05% (MULTIPLIER) |
| STANDARD_PLUS | 650-799 | APPROVE | 0.12% (MULTIPLIER) |
| STANDARD | 500-649 | REFER | 0.25% (MULTIPLIER) |
| SUBSTANDARD | 350-499 | REFER | 0.5% (MULTIPLIER) |
| DECLINE | 0-349 | DECLINE | 0.8% (MULTIPLIER) |

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
| Base Rate | Risk Tier 3 (STANDARD) | 0.25% |
| **Base Premium** | `hull_value` × Base Rate | **$25,000** |
| ILF relativity | Limit = anchor ($5,000,000) | 1.00 |
| Deductible factor | Deductible = anchor ($100,000) | 1.00 |
| Loss frequency modifier | Loss Tier 4 (ELEVATED) | 1.15 |
| Loss severity modifier | Loss Tier 4 (ELEVATED) | 1.15 |
| **Loss modifier** | Frequency × Severity, bounded [0.5, 1.8] | **1.32** |
| Exposure modifier | Size band SMALL | 0.75 |
| **Technical Premium** | Product of all factors | **$24,797** |

*Basis vs. limit: `hull_value` is the total insured value the rate is applied to — a Base Rate of 0.25% on `hull_value` is the rated cost of risk, not the policy limit. The policy Limit (anchored at $5,000,000) is the maximum payout and scales premium independently via the ILF curve; requesting a limit above the anchor lifts the ILF relativity above 1.00.*

**Loss Tier Sensitivity** — holding Risk Tier 3 and the Exposure modifier constant, the technical premium moves with the Loss tier:

| Loss Tier | Freq Mod | Sev Mod | Loss Modifier | Technical Premium |
|-----------|----------|---------|---------------|-------------------|
| 1 VERY_LOW | 0.70 | 0.80 | 0.56 | $10,500 |
| 2 LOW | 0.85 | 0.90 | 0.77 | $14,344 |
| 3 MODERATE | 1.00 | 1.00 | 1.00 | $18,750 |
| 4 ELEVATED  *(example)* | 1.15 | 1.15 | 1.32 | $24,797 |
| 5 HIGH | 1.35 | 1.40 | 1.80 | $33,750 |


---

## Model: `marine_high_value`
*High-value fleet hull & liability — modern tonnage, top-tier operators, fleet value >$1B*

### Routing Protocol (Multiplexer)
- `hull_value >= 250000000`

### Three-Layer Weight Distribution
> *DSI requires that weights for Risk, Loss, and Exposure each sum to 1.0 across all signal groups.*

**Validation:** PASS

| Group | Risk | Loss | Exposure |
|-------|------|------|----------|
| Port State & Regulatory Compliance | 0.40 | 0.35 | 0.25 |
| Fleet Age Band | 0.20 | 0.20 | 0.20 |
| Trading Pattern | 0.20 | 0.25 | 0.30 |
| Corporate Footprint | 0.20 | 0.20 | 0.25 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

**Group Definitions:**
- **Port State & Regulatory Compliance:** PSC detention history, ISM/ISPS audit quality, sanctions screening, class survey status

*Reading the table: a group's three weights are independent. The same group can be a dominant driver of one pillar and a minor input to another — e.g. a group may carry most of the Exposure weight while contributing little to Risk.*

### Signal Architecture Rationale
This configuration contains **9 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `DIRECT_OBSERVABLE` (6 signals): Highest confidence
- `INFERRED_PROXY` (3 signals): Medium confidence

**Signal Count by Group:**
- `public_record`: 8 signals
- `technical_infrastructure`: 1 signals

**Selection Rationale:**
- 67% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Detail by Group
> *Each signal is an objectively observable data point. The weights show how strongly that signal informs each assessment pillar; correlation direction indicates whether a higher observed value increases (+) or decreases (-) the assessed exposure.*

#### Port State & Regulatory Compliance
*PSC detention history, ISM/ISPS audit quality, sanctions screening, class survey status*

| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `psc_detention_rate` | DIRECT_OBSERVABLE | 0.25 | 0.20 / 0.10 | 0.00 | + |
| `ism_audit_quality` | DIRECT_OBSERVABLE | 0.25 | 0.15 / 0.00 | 0.00 | + |
| `isps_compliance` | DIRECT_OBSERVABLE | 0.15 | 0.10 / 0.00 | 0.00 | + |
| `sanctions_screening_depth` | INFERRED_PROXY | 0.20 | 0.00 / 0.15 | 0.00 | + |
| `class_survey_currency` | DIRECT_OBSERVABLE | 0.15 | 0.10 / 0.00 | 0.00 | + |
| `paris_mou_detention_history` | DIRECT_OBSERVABLE | 0.04 | 0.04 / 0.04 | 0.00 | + |
| `tokyo_mou_detention_history` | DIRECT_OBSERVABLE | 0.04 | 0.04 / 0.04 | 0.00 | + |
| `class_society_transfer_frequency` | INFERRED_PROXY | 0.03 | 0.00 / 0.03 | 0.00 | + |

#### Fleet Age Band
| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `vessel_age_profile_curve` | INFERRED_PROXY | 0.04 | 0.03 / 0.04 | 0.00 | + |

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 | Port State & Regulatory Compliance | 1.00 | 0.40 | 0.35 | 0.25 |
| 2 | Trading Pattern | 0.75 | 0.20 | 0.25 | 0.30 |
| 3 | Corporate Footprint | 0.65 | 0.20 | 0.20 | 0.25 |
| 4 | Fleet Age Band | 0.60 | 0.20 | 0.20 | 0.20 |

**Primary Assessment Driver:** `Port State & Regulatory Compliance` with combined weight of 1.00
**Secondary Driver:** `Trading Pattern` with combined weight of 0.75

### Three-Layer Pricing Translation
> *How each pillar's tier score becomes a concrete underwriting action or pricing modifier. This is the bridge between signal observation and premium.*

**Risk -> Underwriting Action & Base Rate**

| Tier | Score Band | Action | Rate / Method |
|------|-----------|--------|---------------|
| PREFERRED | 800-1000 | APPROVE | 0.1% (MULTIPLIER) |
| STANDARD_PLUS | 650-799 | APPROVE | 0.18% (MULTIPLIER) |
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
| `hull_value` (rating basis) | Routing-valid assumption | $750,000,000 |
| Base Rate | Risk Tier 3 (STANDARD) | 0.28% |
| **Base Premium** | `hull_value` × Base Rate | **$2,100,000** |
| ILF relativity | Limit = anchor ($50,000,000) | 1.00 |
| Deductible factor | Deductible = anchor ($1,000,000) | 1.00 |
| Loss frequency modifier | Loss Tier 4 (ELEVATED) | 1.15 |
| Loss severity modifier | Loss Tier 4 (ELEVATED) | 1.15 |
| **Loss modifier** | Frequency × Severity, bounded [0.5, 1.8] | **1.32** |
| Exposure modifier | Size band LARGE | 1.50 |
| **Technical Premium** | Product of all factors | **$4,165,875** |

*Basis vs. limit: `hull_value` is the total insured value the rate is applied to — a Base Rate of 0.28% on `hull_value` is the rated cost of risk, not the policy limit. The policy Limit (anchored at $50,000,000) is the maximum payout and scales premium independently via the ILF curve; requesting a limit above the anchor lifts the ILF relativity above 1.00.*

**Loss Tier Sensitivity** — holding Risk Tier 3 and the Exposure modifier constant, the technical premium moves with the Loss tier:

| Loss Tier | Freq Mod | Sev Mod | Loss Modifier | Technical Premium |
|-----------|----------|---------|---------------|-------------------|
| 1 VERY_LOW | 0.70 | 0.80 | 0.56 | $1,764,000 |
| 2 LOW | 0.85 | 0.90 | 0.77 | $2,409,750 |
| 3 MODERATE | 1.00 | 1.00 | 1.00 | $3,150,000 |
| 4 ELEVATED  *(example)* | 1.15 | 1.15 | 1.32 | $4,165,875 |
| 5 HIGH | 1.35 | 1.40 | 1.80 | $5,670,000 |



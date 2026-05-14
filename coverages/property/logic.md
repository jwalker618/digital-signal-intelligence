# DSI Logic Document: `PROPERTY`
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

## Model: `property_general`
*General commercial property — offices, retail, light industrial, multi-tenant*

### Routing Protocol (Multiplexer)
- `tiv >= 5000000`
- `tiv < 500000000`

### Three-Layer Weight Distribution
> *DSI requires that weights for Risk, Loss, and Exposure each sum to 1.0 across all signal groups.*

**Validation:** PASS

| Group | Risk | Loss | Exposure |
|-------|------|------|----------|
| Construction Quality | 0.50 | 0.45 | 0.20 |
| Occupancy Risk | 0.40 | 0.45 | 0.65 |
| Corporate Footprint | 0.05 | 0.05 | 0.10 |
| Firm Stability | 0.05 | 0.05 | 0.05 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

**Group Definitions:**
- **Construction Quality:** Structural integrity, construction class, age, maintenance, and building code compliance
- **Occupancy Risk:** Tenant type, hazard grade, contents value density, and vacancy exposure

*Reading the table: a group's three weights are independent. The same group can be a dominant driver of one pillar and a minor input to another — e.g. a group may carry most of the Exposure weight while contributing little to Risk.*

### Signal Architecture Rationale
This configuration contains **40 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `DIRECT_OBSERVABLE` (20 signals): Highest confidence
- `INFERRED_PROXY` (19 signals): Medium confidence
- `COHORT_INFERENCE` (1 signals): Lowest confidence

**Signal Count by Group:**
- `technical_infrastructure`: 23 signals
- `structured_data`: 17 signals

**Selection Rationale:**
- 50% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Detail by Group
> *Each signal is an objectively observable data point. The weights show how strongly that signal informs each assessment pillar; correlation direction indicates whether a higher observed value increases (+) or decreases (-) the assessed exposure.*

#### Construction Quality
*Structural integrity, construction class, age, maintenance, and building code compliance*

| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `building_age_condition` | DIRECT_OBSERVABLE | 0.25 | 0.20 / 0.10 | 0.05 | + |
| `building_code_compliance` | INFERRED_PROXY | 0.20 | 0.15 / 0.10 | 0.00 | + |
| `roof_condition` | DIRECT_OBSERVABLE | 0.15 | 0.25 / 0.10 | 0.00 | + |
| `electrical_system_quality` | INFERRED_PROXY | 0.15 | 0.20 / 0.10 | 0.00 | + |
| `renovation_history` | INFERRED_PROXY | 0.10 | 0.05 / 0.00 | 0.10 | + |
| `fire_alarm_quality` | DIRECT_OBSERVABLE | 0.15 | 0.20 / 0.15 | 0.00 | + |
| `fire_department_response` | DIRECT_OBSERVABLE | 0.15 | 0.00 / 0.20 | 0.00 | + |
| `fire_separation` | INFERRED_PROXY | 0.10 | 0.00 / 0.15 | 0.00 | + |
| `water_supply_adequacy` | DIRECT_OBSERVABLE | 0.10 | 0.00 / 0.10 | 0.00 | + |
| `fema_flood_zone` | DIRECT_OBSERVABLE | 0.05 | 0.05 / 0.05 | 0.00 | + |
| `noaa_hail_history` | DIRECT_OBSERVABLE | 0.04 | 0.05 / 0.03 | 0.00 | + |
| `usfs_wildfire_hazard` | DIRECT_OBSERVABLE | 0.05 | 0.04 / 0.05 | 0.00 | + |
| `usgs_seismic_vs30` | DIRECT_OBSERVABLE | 0.04 | 0.00 / 0.05 | 0.00 | + |
| `nhc_track_proximity` | DIRECT_OBSERVABLE | 0.03 | 0.04 / 0.04 | 0.00 | + |
| `iso_caf_bceg_code_compliance` | INFERRED_PROXY | 0.04 | 0.00 / 0.04 | 0.00 | - |
| `energy_star_score` | INFERRED_PROXY | 0.03 | 0.03 / 0.00 | 0.00 | - |
| `building_permit_trail` | INFERRED_PROXY | 0.03 | 0.03 / 0.00 | 0.00 | - |
| `overhead_imagery_condition_score` | INFERRED_PROXY | 0.04 | 0.00 / 0.03 | 0.00 | - |
| `property_primary_derived_01` | INFERRED_PROXY | 0.01 | 0.01 / 0.00 | 0.00 | + |
| `property_primary_derived_02` | INFERRED_PROXY | 0.01 | 0.00 / 0.00 | 0.00 | + |
| `property_primary_derived_03` | INFERRED_PROXY | 0.01 | 0.00 / 0.01 | 0.00 | + |

**Categorical signal `construction_class`** — proxy tier: `DIRECT_OBSERVABLE`, source: `metadata.construction_class`

| Category | Label | Applied Factor |
|----------|-------|----------------|
| `FR` | Fire Resistive | 0.7 |
| `MFR` | Modified Fire Resistive | 0.8 |
| `MNC` | Masonry Non-Combustible | 0.9 |
| `NC` | Non-Combustible | 0.95 |
| `JM` | Joisted Masonry | 1.1 |
| `F` | Frame | 1.4 |

**Categorical signal `sprinkler_coverage`** — proxy tier: `DIRECT_OBSERVABLE`, source: `metadata.sprinkler_coverage`

| Category | Label | Applied Factor |
|----------|-------|----------------|
| `FULL_WET` | Full Wet Sprinkler | 0.55 |
| `FULL_DRY` | Full Dry Sprinkler | 0.65 |
| `PARTIAL` | Partial Sprinkler | 0.85 |
| `NONE` | No Sprinklers | 1.3 |

#### Occupancy Risk
*Tenant type, hazard grade, contents value density, and vacancy exposure*

| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `tenant_concentration` | INFERRED_PROXY | 0.15 | 0.00 / 0.15 | 0.10 | - |
| `contents_value_density` | INFERRED_PROXY | 0.10 | 0.00 / 0.25 | 0.15 | + |
| `vacancy_rate` | DIRECT_OBSERVABLE | 0.20 | 0.20 / 0.00 | 0.00 | + |
| `housekeeping_quality` | INFERRED_PROXY | 0.15 | 0.15 / 0.00 | 0.00 | + |
| `wind_zone` | DIRECT_OBSERVABLE | 0.10 | 0.15 / 0.25 | 0.20 | + |
| `earthquake_zone` | DIRECT_OBSERVABLE | 0.10 | 0.10 / 0.25 | 0.20 | + |
| `flood_zone` | DIRECT_OBSERVABLE | 0.10 | 0.20 / 0.15 | 0.15 | + |
| `wildfire_zone` | DIRECT_OBSERVABLE | 0.10 | 0.15 / 0.15 | 0.10 | + |
| `convective_storm_exposure` | INFERRED_PROXY | 0.05 | 0.15 / 0.10 | 0.00 | + |
| `geographic_concentration` | DIRECT_OBSERVABLE | 0.05 | 0.00 / 0.00 | 0.30 | + |
| `revenue_concentration` | INFERRED_PROXY | 0.10 | 0.00 / 0.25 | 0.20 | + |
| `recovery_time_estimate` | INFERRED_PROXY | 0.10 | 0.00 / 0.30 | 0.15 | + |
| `supply_chain_dependency` | INFERRED_PROXY | 0.05 | 0.00 / 0.15 | 0.20 | + |
| `contingent_bi_exposure` | COHORT_INFERENCE | 0.05 | 0.00 / 0.15 | 0.15 | + |
| `business_continuity_planning` | INFERRED_PROXY | 0.10 | 0.00 / 0.10 | 0.00 | + |
| `nfip_participation` | DIRECT_OBSERVABLE | 0.03 | 0.03 / 0.00 | 0.00 | - |

**Categorical signal `occupancy_hazard_grade`** — proxy tier: `DIRECT_OBSERVABLE`, source: `metadata.occupancy_hazard_grade`

| Category | Label | Applied Factor |
|----------|-------|----------------|
| `LOW` | Low Hazard (Office/Residential) | 0.75 |
| `MOD` | Moderate Hazard (Retail/Light Mfg) | 1.0 |
| `HIGH` | High Hazard (Heavy Mfg/Woodworking) | 1.35 |
| `SPECIAL` | Special Hazard (Chemical/Explosive) | 1.8 |

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 | Occupancy Risk | 1.50 | 0.40 | 0.45 | 0.65 |
| 2 | Construction Quality | 1.15 | 0.50 | 0.45 | 0.20 |
| 3 | Corporate Footprint | 0.20 | 0.05 | 0.05 | 0.10 |
| 4 | Firm Stability | 0.15 | 0.05 | 0.05 | 0.05 |

**Primary Assessment Driver:** `Occupancy Risk` with combined weight of 1.50
**Secondary Driver:** `Construction Quality` with combined weight of 1.15

### Three-Layer Pricing Translation
> *How each pillar's tier score becomes a concrete underwriting action or pricing modifier. This is the bridge between signal observation and premium.*

**Risk -> Underwriting Action & Base Rate**

| Tier | Score Band | Action | Rate / Method |
|------|-----------|--------|---------------|
| PREFERRED | 800-1000 | APPROVE | 0.08% (MULTIPLIER) |
| STANDARD_PLUS | 650-799 | APPROVE | 0.15% (MULTIPLIER) |
| STANDARD | 500-649 | REFER | 0.25% (MULTIPLIER) |
| SUBSTANDARD | 350-499 | REFER | 0.4% (MULTIPLIER) |
| DECLINE | 0-349 | DECLINE | 0.6% (MULTIPLIER) |

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
| MICRO | 0-20 | 0.5 | $0 - $5,000,000 |
| SMALL | 21-40 | 0.75 | $5,000,000 - $25,000,000 |
| MEDIUM | 41-60 | 1.0 | $25,000,000 - $100,000,000 |
| LARGE | 61-80 | 1.5 | $100,000,000 - $500,000,000 |
| VERY_LARGE | 81-100 | 2.5 | $500,000,000 - $5,000,000,000 |

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
| Base Rate | Risk Tier 3 (STANDARD) | 0.25% |
| **Base Premium** | `tiv` × Base Rate | **$37,500** |
| ILF relativity | Limit = anchor ($1,000,000) | 1.00 |
| Deductible factor | Deductible = anchor ($25,000) | 1.00 |
| Loss frequency modifier | Loss Tier 4 (ELEVATED) | 1.15 |
| Loss severity modifier | Loss Tier 4 (ELEVATED) | 1.15 |
| **Loss modifier** | Frequency × Severity, bounded [0.5, 1.8] | **1.32** |
| Exposure modifier | Size band SMALL | 0.75 |
| **Technical Premium** | Product of all factors | **$37,195** |

*Basis vs. limit: `tiv` is the total insured value the rate is applied to — a Base Rate of 0.25% on `tiv` is the rated cost of risk, not the policy limit. The policy Limit (anchored at $1,000,000) is the maximum payout and scales premium independently via the ILF curve; requesting a limit above the anchor lifts the ILF relativity above 1.00.*

**Loss Tier Sensitivity** — holding Risk Tier 3 and the Exposure modifier constant, the technical premium moves with the Loss tier:

| Loss Tier | Freq Mod | Sev Mod | Loss Modifier | Technical Premium |
|-----------|----------|---------|---------------|-------------------|
| 1 VERY_LOW | 0.70 | 0.80 | 0.56 | $15,750 |
| 2 LOW | 0.85 | 0.90 | 0.77 | $21,516 |
| 3 MODERATE | 1.00 | 1.00 | 1.00 | $28,125 |
| 4 ELEVATED  *(example)* | 1.15 | 1.15 | 1.32 | $37,195 |
| 5 HIGH | 1.35 | 1.40 | 1.80 | $50,625 |


---

## Model: `property_high_value`
*High-value commercial property — TIV >$500M, landmark, data centre, critical infrastructure*

### Routing Protocol (Multiplexer)
- `tiv >= 500000000`

### Three-Layer Weight Distribution
> *DSI requires that weights for Risk, Loss, and Exposure each sum to 1.0 across all signal groups.*

**Validation:** PASS

| Group | Risk | Loss | Exposure |
|-------|------|------|----------|
| Construction Quality | 0.40 | 0.35 | 0.20 |
| Occupancy Risk | 0.45 | 0.50 | 0.70 |
| Corporate Footprint | 0.10 | 0.10 | 0.05 |
| Firm Stability | 0.05 | 0.05 | 0.05 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

**Group Definitions:**
- **Construction Quality:** Structural integrity, construction class, age, maintenance, and building code compliance
- **Occupancy Risk:** Tenant type, hazard grade, contents value density, and vacancy exposure

*Reading the table: a group's three weights are independent. The same group can be a dominant driver of one pillar and a minor input to another — e.g. a group may carry most of the Exposure weight while contributing little to Risk.*

### Signal Architecture Rationale
This configuration contains **37 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `DIRECT_OBSERVABLE` (20 signals): Highest confidence
- `INFERRED_PROXY` (16 signals): Medium confidence
- `COHORT_INFERENCE` (1 signals): Lowest confidence

**Signal Count by Group:**
- `technical_infrastructure`: 20 signals
- `structured_data`: 17 signals

**Selection Rationale:**
- 54% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Detail by Group
> *Each signal is an objectively observable data point. The weights show how strongly that signal informs each assessment pillar; correlation direction indicates whether a higher observed value increases (+) or decreases (-) the assessed exposure.*

#### Construction Quality
*Structural integrity, construction class, age, maintenance, and building code compliance*

| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `building_age_condition` | DIRECT_OBSERVABLE | 0.25 | 0.20 / 0.10 | 0.05 | + |
| `building_code_compliance` | INFERRED_PROXY | 0.20 | 0.15 / 0.10 | 0.00 | + |
| `roof_condition` | DIRECT_OBSERVABLE | 0.15 | 0.25 / 0.10 | 0.00 | + |
| `electrical_system_quality` | INFERRED_PROXY | 0.15 | 0.20 / 0.10 | 0.00 | + |
| `renovation_history` | INFERRED_PROXY | 0.10 | 0.05 / 0.00 | 0.10 | + |
| `fire_alarm_quality` | DIRECT_OBSERVABLE | 0.15 | 0.20 / 0.15 | 0.00 | + |
| `fire_department_response` | DIRECT_OBSERVABLE | 0.15 | 0.00 / 0.20 | 0.00 | + |
| `fire_separation` | INFERRED_PROXY | 0.10 | 0.00 / 0.15 | 0.00 | + |
| `water_supply_adequacy` | DIRECT_OBSERVABLE | 0.10 | 0.00 / 0.10 | 0.00 | + |
| `fema_flood_zone` | DIRECT_OBSERVABLE | 0.05 | 0.05 / 0.05 | 0.00 | + |
| `noaa_hail_history` | DIRECT_OBSERVABLE | 0.04 | 0.05 / 0.03 | 0.00 | + |
| `usfs_wildfire_hazard` | DIRECT_OBSERVABLE | 0.05 | 0.04 / 0.05 | 0.00 | + |
| `usgs_seismic_vs30` | DIRECT_OBSERVABLE | 0.04 | 0.00 / 0.05 | 0.00 | + |
| `nhc_track_proximity` | DIRECT_OBSERVABLE | 0.03 | 0.04 / 0.04 | 0.00 | + |
| `iso_caf_bceg_code_compliance` | INFERRED_PROXY | 0.04 | 0.00 / 0.04 | 0.00 | - |
| `energy_star_score` | INFERRED_PROXY | 0.03 | 0.03 / 0.00 | 0.00 | - |
| `building_permit_trail` | INFERRED_PROXY | 0.03 | 0.03 / 0.00 | 0.00 | - |
| `overhead_imagery_condition_score` | INFERRED_PROXY | 0.04 | 0.00 / 0.03 | 0.00 | - |

**Categorical signal `construction_class`** — proxy tier: `DIRECT_OBSERVABLE`, source: `metadata.construction_class`

| Category | Label | Applied Factor |
|----------|-------|----------------|
| `FR` | Fire Resistive | 0.7 |
| `MFR` | Modified Fire Resistive | 0.8 |
| `MNC` | Masonry Non-Combustible | 0.9 |
| `NC` | Non-Combustible | 0.95 |
| `JM` | Joisted Masonry | 1.1 |
| `F` | Frame | 1.4 |

**Categorical signal `sprinkler_coverage`** — proxy tier: `DIRECT_OBSERVABLE`, source: `metadata.sprinkler_coverage`

| Category | Label | Applied Factor |
|----------|-------|----------------|
| `FULL_WET` | Full Wet Sprinkler | 0.55 |
| `FULL_DRY` | Full Dry Sprinkler | 0.65 |
| `PARTIAL` | Partial Sprinkler | 0.85 |
| `NONE` | No Sprinklers | 1.3 |

#### Occupancy Risk
*Tenant type, hazard grade, contents value density, and vacancy exposure*

| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `tenant_concentration` | INFERRED_PROXY | 0.15 | 0.00 / 0.15 | 0.10 | - |
| `contents_value_density` | INFERRED_PROXY | 0.10 | 0.00 / 0.25 | 0.15 | + |
| `vacancy_rate` | DIRECT_OBSERVABLE | 0.20 | 0.20 / 0.00 | 0.00 | + |
| `housekeeping_quality` | INFERRED_PROXY | 0.15 | 0.15 / 0.00 | 0.00 | + |
| `wind_zone` | DIRECT_OBSERVABLE | 0.10 | 0.15 / 0.25 | 0.20 | + |
| `earthquake_zone` | DIRECT_OBSERVABLE | 0.10 | 0.10 / 0.25 | 0.20 | + |
| `flood_zone` | DIRECT_OBSERVABLE | 0.10 | 0.20 / 0.15 | 0.15 | + |
| `wildfire_zone` | DIRECT_OBSERVABLE | 0.10 | 0.15 / 0.15 | 0.10 | + |
| `convective_storm_exposure` | INFERRED_PROXY | 0.05 | 0.15 / 0.10 | 0.00 | + |
| `geographic_concentration` | DIRECT_OBSERVABLE | 0.05 | 0.00 / 0.00 | 0.30 | + |
| `revenue_concentration` | INFERRED_PROXY | 0.10 | 0.00 / 0.25 | 0.20 | + |
| `recovery_time_estimate` | INFERRED_PROXY | 0.10 | 0.00 / 0.30 | 0.15 | + |
| `supply_chain_dependency` | INFERRED_PROXY | 0.05 | 0.00 / 0.15 | 0.20 | + |
| `contingent_bi_exposure` | COHORT_INFERENCE | 0.05 | 0.00 / 0.15 | 0.15 | + |
| `business_continuity_planning` | INFERRED_PROXY | 0.10 | 0.00 / 0.10 | 0.00 | + |
| `nfip_participation` | DIRECT_OBSERVABLE | 0.03 | 0.03 / 0.00 | 0.00 | - |

**Categorical signal `occupancy_hazard_grade`** — proxy tier: `DIRECT_OBSERVABLE`, source: `metadata.occupancy_hazard_grade`

| Category | Label | Applied Factor |
|----------|-------|----------------|
| `LOW` | Low Hazard (Office/Residential) | 0.75 |
| `MOD` | Moderate Hazard (Retail/Light Mfg) | 1.0 |
| `HIGH` | High Hazard (Heavy Mfg/Woodworking) | 1.35 |
| `SPECIAL` | Special Hazard (Chemical/Explosive) | 1.8 |

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 | Occupancy Risk | 1.65 | 0.45 | 0.50 | 0.70 |
| 2 | Construction Quality | 0.95 | 0.40 | 0.35 | 0.20 |
| 3 | Corporate Footprint | 0.25 | 0.10 | 0.10 | 0.05 |
| 4 | Firm Stability | 0.15 | 0.05 | 0.05 | 0.05 |

**Primary Assessment Driver:** `Occupancy Risk` with combined weight of 1.65
**Secondary Driver:** `Construction Quality` with combined weight of 0.95

### Three-Layer Pricing Translation
> *How each pillar's tier score becomes a concrete underwriting action or pricing modifier. This is the bridge between signal observation and premium.*

**Risk -> Underwriting Action & Base Rate**

| Tier | Score Band | Action | Rate / Method |
|------|-----------|--------|---------------|
| PREFERRED | 800-1000 | APPROVE | 0.05% (MULTIPLIER) |
| STANDARD_PLUS | 650-799 | APPROVE | 0.1% (MULTIPLIER) |
| STANDARD | 500-649 | REFER | 0.18% (MULTIPLIER) |
| SUBSTANDARD | 350-499 | REFER | 0.3% (MULTIPLIER) |
| DECLINE | 0-349 | DECLINE | 0.5% (MULTIPLIER) |

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
| MICRO | 0-20 | 0.5 | $0 - $5,000,000 |
| SMALL | 21-40 | 0.75 | $5,000,000 - $25,000,000 |
| MEDIUM | 41-60 | 1.0 | $25,000,000 - $100,000,000 |
| LARGE | 61-80 | 1.5 | $100,000,000 - $500,000,000 |
| VERY_LARGE | 81-100 | 2.5 | $500,000,000 - $5,000,000,000 |

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
| `tiv` (rating basis) | Routing-valid assumption | $1,500,000,000 |
| Base Rate | Risk Tier 3 (STANDARD) | 0.18% |
| **Base Premium** | `tiv` × Base Rate | **$2,700,000** |
| ILF relativity | Limit = anchor ($25,000,000) | 1.00 |
| Deductible factor | Deductible = anchor ($500,000) | 1.00 |
| Loss frequency modifier | Loss Tier 4 (ELEVATED) | 1.15 |
| Loss severity modifier | Loss Tier 4 (ELEVATED) | 1.15 |
| **Loss modifier** | Frequency × Severity, bounded [0.5, 1.8] | **1.32** |
| Exposure modifier | Size band VERY_LARGE | 2.50 |
| **Technical Premium** | Product of all factors | **$8,926,875** |

*Basis vs. limit: `tiv` is the total insured value the rate is applied to — a Base Rate of 0.18% on `tiv` is the rated cost of risk, not the policy limit. The policy Limit (anchored at $25,000,000) is the maximum payout and scales premium independently via the ILF curve; requesting a limit above the anchor lifts the ILF relativity above 1.00.*

**Loss Tier Sensitivity** — holding Risk Tier 3 and the Exposure modifier constant, the technical premium moves with the Loss tier:

| Loss Tier | Freq Mod | Sev Mod | Loss Modifier | Technical Premium |
|-----------|----------|---------|---------------|-------------------|
| 1 VERY_LOW | 0.70 | 0.80 | 0.56 | $3,780,000 |
| 2 LOW | 0.85 | 0.90 | 0.77 | $5,163,750 |
| 3 MODERATE | 1.00 | 1.00 | 1.00 | $6,750,000 |
| 4 ELEVATED  *(example)* | 1.15 | 1.15 | 1.32 | $8,926,875 |
| 5 HIGH | 1.35 | 1.40 | 1.80 | $12,150,000 |


---

## Model: `property_cat_exposed`
*CAT-exposed commercial property — coastal wind, earthquake, wildfire zones*

### Routing Protocol (Multiplexer)
- `tiv >= 5000000`
- `cat_zone in ['HIGH_WIND', 'HIGH_EQ', 'HIGH_WILDFIRE', 'HIGH_FLOOD']`

### Three-Layer Weight Distribution
> *DSI requires that weights for Risk, Loss, and Exposure each sum to 1.0 across all signal groups.*

**Validation:** PASS

| Group | Risk | Loss | Exposure |
|-------|------|------|----------|
| Construction Quality | 0.30 | 0.30 | 0.10 |
| Occupancy Risk | 0.55 | 0.55 | 0.80 |
| Corporate Footprint | 0.10 | 0.10 | 0.05 |
| Firm Stability | 0.05 | 0.05 | 0.05 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

**Group Definitions:**
- **Construction Quality:** Structural integrity, construction class, age, maintenance, and building code compliance
- **Occupancy Risk:** Tenant type, hazard grade, contents value density, and vacancy exposure

*Reading the table: a group's three weights are independent. The same group can be a dominant driver of one pillar and a minor input to another — e.g. a group may carry most of the Exposure weight while contributing little to Risk.*

### Signal Architecture Rationale
This configuration contains **37 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `DIRECT_OBSERVABLE` (20 signals): Highest confidence
- `INFERRED_PROXY` (16 signals): Medium confidence
- `COHORT_INFERENCE` (1 signals): Lowest confidence

**Signal Count by Group:**
- `technical_infrastructure`: 20 signals
- `structured_data`: 17 signals

**Selection Rationale:**
- 54% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Detail by Group
> *Each signal is an objectively observable data point. The weights show how strongly that signal informs each assessment pillar; correlation direction indicates whether a higher observed value increases (+) or decreases (-) the assessed exposure.*

#### Construction Quality
*Structural integrity, construction class, age, maintenance, and building code compliance*

| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `building_age_condition` | DIRECT_OBSERVABLE | 0.25 | 0.20 / 0.10 | 0.05 | + |
| `building_code_compliance` | INFERRED_PROXY | 0.20 | 0.15 / 0.10 | 0.00 | + |
| `roof_condition` | DIRECT_OBSERVABLE | 0.15 | 0.25 / 0.10 | 0.00 | + |
| `electrical_system_quality` | INFERRED_PROXY | 0.15 | 0.20 / 0.10 | 0.00 | + |
| `renovation_history` | INFERRED_PROXY | 0.10 | 0.05 / 0.00 | 0.10 | + |
| `fire_alarm_quality` | DIRECT_OBSERVABLE | 0.15 | 0.20 / 0.15 | 0.00 | + |
| `fire_department_response` | DIRECT_OBSERVABLE | 0.15 | 0.00 / 0.20 | 0.00 | + |
| `fire_separation` | INFERRED_PROXY | 0.10 | 0.00 / 0.15 | 0.00 | + |
| `water_supply_adequacy` | DIRECT_OBSERVABLE | 0.10 | 0.00 / 0.10 | 0.00 | + |
| `fema_flood_zone` | DIRECT_OBSERVABLE | 0.05 | 0.05 / 0.05 | 0.00 | + |
| `noaa_hail_history` | DIRECT_OBSERVABLE | 0.04 | 0.05 / 0.03 | 0.00 | + |
| `usfs_wildfire_hazard` | DIRECT_OBSERVABLE | 0.05 | 0.04 / 0.05 | 0.00 | + |
| `usgs_seismic_vs30` | DIRECT_OBSERVABLE | 0.04 | 0.00 / 0.05 | 0.00 | + |
| `nhc_track_proximity` | DIRECT_OBSERVABLE | 0.03 | 0.04 / 0.04 | 0.00 | + |
| `iso_caf_bceg_code_compliance` | INFERRED_PROXY | 0.04 | 0.00 / 0.04 | 0.00 | - |
| `energy_star_score` | INFERRED_PROXY | 0.03 | 0.03 / 0.00 | 0.00 | - |
| `building_permit_trail` | INFERRED_PROXY | 0.03 | 0.03 / 0.00 | 0.00 | - |
| `overhead_imagery_condition_score` | INFERRED_PROXY | 0.04 | 0.00 / 0.03 | 0.00 | - |

**Categorical signal `construction_class`** — proxy tier: `DIRECT_OBSERVABLE`, source: `metadata.construction_class`

| Category | Label | Applied Factor |
|----------|-------|----------------|
| `FR` | Fire Resistive | 0.7 |
| `MFR` | Modified Fire Resistive | 0.8 |
| `MNC` | Masonry Non-Combustible | 0.9 |
| `NC` | Non-Combustible | 0.95 |
| `JM` | Joisted Masonry | 1.1 |
| `F` | Frame | 1.4 |

**Categorical signal `sprinkler_coverage`** — proxy tier: `DIRECT_OBSERVABLE`, source: `metadata.sprinkler_coverage`

| Category | Label | Applied Factor |
|----------|-------|----------------|
| `FULL_WET` | Full Wet Sprinkler | 0.55 |
| `FULL_DRY` | Full Dry Sprinkler | 0.65 |
| `PARTIAL` | Partial Sprinkler | 0.85 |
| `NONE` | No Sprinklers | 1.3 |

#### Occupancy Risk
*Tenant type, hazard grade, contents value density, and vacancy exposure*

| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `tenant_concentration` | INFERRED_PROXY | 0.15 | 0.00 / 0.15 | 0.10 | - |
| `contents_value_density` | INFERRED_PROXY | 0.10 | 0.00 / 0.25 | 0.15 | + |
| `vacancy_rate` | DIRECT_OBSERVABLE | 0.20 | 0.20 / 0.00 | 0.00 | + |
| `housekeeping_quality` | INFERRED_PROXY | 0.15 | 0.15 / 0.00 | 0.00 | + |
| `wind_zone` | DIRECT_OBSERVABLE | 0.10 | 0.15 / 0.25 | 0.20 | + |
| `earthquake_zone` | DIRECT_OBSERVABLE | 0.10 | 0.10 / 0.25 | 0.20 | + |
| `flood_zone` | DIRECT_OBSERVABLE | 0.10 | 0.20 / 0.15 | 0.15 | + |
| `wildfire_zone` | DIRECT_OBSERVABLE | 0.10 | 0.15 / 0.15 | 0.10 | + |
| `convective_storm_exposure` | INFERRED_PROXY | 0.05 | 0.15 / 0.10 | 0.00 | + |
| `geographic_concentration` | DIRECT_OBSERVABLE | 0.05 | 0.00 / 0.00 | 0.30 | + |
| `revenue_concentration` | INFERRED_PROXY | 0.10 | 0.00 / 0.25 | 0.20 | + |
| `recovery_time_estimate` | INFERRED_PROXY | 0.10 | 0.00 / 0.30 | 0.15 | + |
| `supply_chain_dependency` | INFERRED_PROXY | 0.05 | 0.00 / 0.15 | 0.20 | + |
| `contingent_bi_exposure` | COHORT_INFERENCE | 0.05 | 0.00 / 0.15 | 0.15 | + |
| `business_continuity_planning` | INFERRED_PROXY | 0.10 | 0.00 / 0.10 | 0.00 | + |
| `nfip_participation` | DIRECT_OBSERVABLE | 0.03 | 0.03 / 0.00 | 0.00 | - |

**Categorical signal `occupancy_hazard_grade`** — proxy tier: `DIRECT_OBSERVABLE`, source: `metadata.occupancy_hazard_grade`

| Category | Label | Applied Factor |
|----------|-------|----------------|
| `LOW` | Low Hazard (Office/Residential) | 0.75 |
| `MOD` | Moderate Hazard (Retail/Light Mfg) | 1.0 |
| `HIGH` | High Hazard (Heavy Mfg/Woodworking) | 1.35 |
| `SPECIAL` | Special Hazard (Chemical/Explosive) | 1.8 |

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 | Occupancy Risk | 1.90 | 0.55 | 0.55 | 0.80 |
| 2 | Construction Quality | 0.70 | 0.30 | 0.30 | 0.10 |
| 3 | Corporate Footprint | 0.25 | 0.10 | 0.10 | 0.05 |
| 4 | Firm Stability | 0.15 | 0.05 | 0.05 | 0.05 |

**Primary Assessment Driver:** `Occupancy Risk` with combined weight of 1.90
**Secondary Driver:** `Construction Quality` with combined weight of 0.70

### Three-Layer Pricing Translation
> *How each pillar's tier score becomes a concrete underwriting action or pricing modifier. This is the bridge between signal observation and premium.*

**Risk -> Underwriting Action & Base Rate**

| Tier | Score Band | Action | Rate / Method |
|------|-----------|--------|---------------|
| PREFERRED | 800-1000 | APPROVE | 0.18% (MULTIPLIER) |
| STANDARD_PLUS | 650-799 | APPROVE | 0.3% (MULTIPLIER) |
| STANDARD | 500-649 | REFER | 0.45% (MULTIPLIER) |
| SUBSTANDARD | 350-499 | REFER | 0.65% (MULTIPLIER) |
| DECLINE | 0-349 | DECLINE | 0.9% (MULTIPLIER) |

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
| MICRO | 0-20 | 0.5 | $0 - $5,000,000 |
| SMALL | 21-40 | 0.75 | $5,000,000 - $25,000,000 |
| MEDIUM | 41-60 | 1.0 | $25,000,000 - $100,000,000 |
| LARGE | 61-80 | 1.5 | $100,000,000 - $500,000,000 |
| VERY_LARGE | 81-100 | 2.5 | $500,000,000 - $5,000,000,000 |

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
| Base Rate | Risk Tier 3 (STANDARD) | 0.45% |
| **Base Premium** | `tiv` × Base Rate | **$67,500** |
| ILF relativity | Limit = anchor ($1,000,000) | 1.00 |
| Deductible factor | Deductible = anchor ($50,000) | 1.00 |
| Loss frequency modifier | Loss Tier 4 (ELEVATED) | 1.15 |
| Loss severity modifier | Loss Tier 4 (ELEVATED) | 1.15 |
| **Loss modifier** | Frequency × Severity, bounded [0.5, 1.8] | **1.32** |
| Exposure modifier | Size band SMALL | 0.75 |
| **Technical Premium** | Product of all factors | **$66,952** |

*Basis vs. limit: `tiv` is the total insured value the rate is applied to — a Base Rate of 0.45% on `tiv` is the rated cost of risk, not the policy limit. The policy Limit (anchored at $1,000,000) is the maximum payout and scales premium independently via the ILF curve; requesting a limit above the anchor lifts the ILF relativity above 1.00.*

**Loss Tier Sensitivity** — holding Risk Tier 3 and the Exposure modifier constant, the technical premium moves with the Loss tier:

| Loss Tier | Freq Mod | Sev Mod | Loss Modifier | Technical Premium |
|-----------|----------|---------|---------------|-------------------|
| 1 VERY_LOW | 0.70 | 0.80 | 0.56 | $28,350 |
| 2 LOW | 0.85 | 0.90 | 0.77 | $38,728 |
| 3 MODERATE | 1.00 | 1.00 | 1.00 | $50,625 |
| 4 ELEVATED  *(example)* | 1.15 | 1.15 | 1.32 | $66,952 |
| 5 HIGH | 1.35 | 1.40 | 1.80 | $91,125 |


---

## Model: `property_builders_risk`
*Construction-phase property coverage — new build, renovation, fit-out*

### Routing Protocol (Multiplexer)
- `product_type == builders_risk`

### Three-Layer Weight Distribution
> *DSI requires that weights for Risk, Loss, and Exposure each sum to 1.0 across all signal groups.*

**Validation:** PASS

| Group | Risk | Loss | Exposure |
|-------|------|------|----------|
| Construction Quality | 0.55 | 0.50 | 0.30 |
| Occupancy Risk | 0.35 | 0.40 | 0.60 |
| Corporate Footprint | 0.05 | 0.05 | 0.05 |
| Firm Stability | 0.05 | 0.05 | 0.05 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

**Group Definitions:**
- **Construction Quality:** Structural integrity, construction class, age, maintenance, and building code compliance
- **Occupancy Risk:** Tenant type, hazard grade, contents value density, and vacancy exposure

*Reading the table: a group's three weights are independent. The same group can be a dominant driver of one pillar and a minor input to another — e.g. a group may carry most of the Exposure weight while contributing little to Risk.*

### Signal Architecture Rationale
This configuration contains **37 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `DIRECT_OBSERVABLE` (20 signals): Highest confidence
- `INFERRED_PROXY` (16 signals): Medium confidence
- `COHORT_INFERENCE` (1 signals): Lowest confidence

**Signal Count by Group:**
- `technical_infrastructure`: 20 signals
- `structured_data`: 17 signals

**Selection Rationale:**
- 54% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Detail by Group
> *Each signal is an objectively observable data point. The weights show how strongly that signal informs each assessment pillar; correlation direction indicates whether a higher observed value increases (+) or decreases (-) the assessed exposure.*

#### Construction Quality
*Structural integrity, construction class, age, maintenance, and building code compliance*

| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `building_age_condition` | DIRECT_OBSERVABLE | 0.25 | 0.20 / 0.10 | 0.05 | + |
| `building_code_compliance` | INFERRED_PROXY | 0.20 | 0.15 / 0.10 | 0.00 | + |
| `roof_condition` | DIRECT_OBSERVABLE | 0.15 | 0.25 / 0.10 | 0.00 | + |
| `electrical_system_quality` | INFERRED_PROXY | 0.15 | 0.20 / 0.10 | 0.00 | + |
| `renovation_history` | INFERRED_PROXY | 0.10 | 0.05 / 0.00 | 0.10 | + |
| `fire_alarm_quality` | DIRECT_OBSERVABLE | 0.15 | 0.20 / 0.15 | 0.00 | + |
| `fire_department_response` | DIRECT_OBSERVABLE | 0.15 | 0.00 / 0.20 | 0.00 | + |
| `fire_separation` | INFERRED_PROXY | 0.10 | 0.00 / 0.15 | 0.00 | + |
| `water_supply_adequacy` | DIRECT_OBSERVABLE | 0.10 | 0.00 / 0.10 | 0.00 | + |
| `fema_flood_zone` | DIRECT_OBSERVABLE | 0.05 | 0.05 / 0.05 | 0.00 | + |
| `noaa_hail_history` | DIRECT_OBSERVABLE | 0.04 | 0.05 / 0.03 | 0.00 | + |
| `usfs_wildfire_hazard` | DIRECT_OBSERVABLE | 0.05 | 0.04 / 0.05 | 0.00 | + |
| `usgs_seismic_vs30` | DIRECT_OBSERVABLE | 0.04 | 0.00 / 0.05 | 0.00 | + |
| `nhc_track_proximity` | DIRECT_OBSERVABLE | 0.03 | 0.04 / 0.04 | 0.00 | + |
| `iso_caf_bceg_code_compliance` | INFERRED_PROXY | 0.04 | 0.00 / 0.04 | 0.00 | - |
| `energy_star_score` | INFERRED_PROXY | 0.03 | 0.03 / 0.00 | 0.00 | - |
| `building_permit_trail` | INFERRED_PROXY | 0.03 | 0.03 / 0.00 | 0.00 | - |
| `overhead_imagery_condition_score` | INFERRED_PROXY | 0.04 | 0.00 / 0.03 | 0.00 | - |

**Categorical signal `construction_class`** — proxy tier: `DIRECT_OBSERVABLE`, source: `metadata.construction_class`

| Category | Label | Applied Factor |
|----------|-------|----------------|
| `FR` | Fire Resistive | 0.7 |
| `MFR` | Modified Fire Resistive | 0.8 |
| `MNC` | Masonry Non-Combustible | 0.9 |
| `NC` | Non-Combustible | 0.95 |
| `JM` | Joisted Masonry | 1.1 |
| `F` | Frame | 1.4 |

**Categorical signal `sprinkler_coverage`** — proxy tier: `DIRECT_OBSERVABLE`, source: `metadata.sprinkler_coverage`

| Category | Label | Applied Factor |
|----------|-------|----------------|
| `FULL_WET` | Full Wet Sprinkler | 0.55 |
| `FULL_DRY` | Full Dry Sprinkler | 0.65 |
| `PARTIAL` | Partial Sprinkler | 0.85 |
| `NONE` | No Sprinklers | 1.3 |

#### Occupancy Risk
*Tenant type, hazard grade, contents value density, and vacancy exposure*

| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `tenant_concentration` | INFERRED_PROXY | 0.15 | 0.00 / 0.15 | 0.10 | - |
| `contents_value_density` | INFERRED_PROXY | 0.10 | 0.00 / 0.25 | 0.15 | + |
| `vacancy_rate` | DIRECT_OBSERVABLE | 0.20 | 0.20 / 0.00 | 0.00 | + |
| `housekeeping_quality` | INFERRED_PROXY | 0.15 | 0.15 / 0.00 | 0.00 | + |
| `wind_zone` | DIRECT_OBSERVABLE | 0.10 | 0.15 / 0.25 | 0.20 | + |
| `earthquake_zone` | DIRECT_OBSERVABLE | 0.10 | 0.10 / 0.25 | 0.20 | + |
| `flood_zone` | DIRECT_OBSERVABLE | 0.10 | 0.20 / 0.15 | 0.15 | + |
| `wildfire_zone` | DIRECT_OBSERVABLE | 0.10 | 0.15 / 0.15 | 0.10 | + |
| `convective_storm_exposure` | INFERRED_PROXY | 0.05 | 0.15 / 0.10 | 0.00 | + |
| `geographic_concentration` | DIRECT_OBSERVABLE | 0.05 | 0.00 / 0.00 | 0.30 | + |
| `revenue_concentration` | INFERRED_PROXY | 0.10 | 0.00 / 0.25 | 0.20 | + |
| `recovery_time_estimate` | INFERRED_PROXY | 0.10 | 0.00 / 0.30 | 0.15 | + |
| `supply_chain_dependency` | INFERRED_PROXY | 0.05 | 0.00 / 0.15 | 0.20 | + |
| `contingent_bi_exposure` | COHORT_INFERENCE | 0.05 | 0.00 / 0.15 | 0.15 | + |
| `business_continuity_planning` | INFERRED_PROXY | 0.10 | 0.00 / 0.10 | 0.00 | + |
| `nfip_participation` | DIRECT_OBSERVABLE | 0.03 | 0.03 / 0.00 | 0.00 | - |

**Categorical signal `occupancy_hazard_grade`** — proxy tier: `DIRECT_OBSERVABLE`, source: `metadata.occupancy_hazard_grade`

| Category | Label | Applied Factor |
|----------|-------|----------------|
| `LOW` | Low Hazard (Office/Residential) | 0.75 |
| `MOD` | Moderate Hazard (Retail/Light Mfg) | 1.0 |
| `HIGH` | High Hazard (Heavy Mfg/Woodworking) | 1.35 |
| `SPECIAL` | Special Hazard (Chemical/Explosive) | 1.8 |

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 | Construction Quality | 1.35 | 0.55 | 0.50 | 0.30 |
| 2 | Occupancy Risk | 1.35 | 0.35 | 0.40 | 0.60 |
| 3 | Corporate Footprint | 0.15 | 0.05 | 0.05 | 0.05 |
| 4 | Firm Stability | 0.15 | 0.05 | 0.05 | 0.05 |

**Primary Assessment Driver:** `Construction Quality` with combined weight of 1.35
**Secondary Driver:** `Occupancy Risk` with combined weight of 1.35

### Three-Layer Pricing Translation
> *How each pillar's tier score becomes a concrete underwriting action or pricing modifier. This is the bridge between signal observation and premium.*

**Risk -> Underwriting Action & Base Rate**

| Tier | Score Band | Action | Rate / Method |
|------|-----------|--------|---------------|
| PREFERRED | 800-1000 | APPROVE | 0.2% (MULTIPLIER) |
| STANDARD_PLUS | 650-799 | APPROVE | 0.35% (MULTIPLIER) |
| STANDARD | 500-649 | REFER | 0.55% (MULTIPLIER) |
| SUBSTANDARD | 350-499 | REFER | 0.8% (MULTIPLIER) |
| DECLINE | 0-349 | DECLINE | 1.1% (MULTIPLIER) |

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
| MICRO | 0-20 | 0.5 | $0 - $5,000,000 |
| SMALL | 21-40 | 0.75 | $5,000,000 - $25,000,000 |
| MEDIUM | 41-60 | 1.0 | $25,000,000 - $100,000,000 |
| LARGE | 61-80 | 1.5 | $100,000,000 - $500,000,000 |
| VERY_LARGE | 81-100 | 2.5 | $500,000,000 - $5,000,000,000 |

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
| Base Rate | Risk Tier 3 (STANDARD) | 0.55% |
| **Base Premium** | `tiv` × Base Rate | **$55,000** |
| ILF relativity | Limit = anchor ($1,000,000) | 1.00 |
| Deductible factor | Deductible = anchor ($25,000) | 1.00 |
| Loss frequency modifier | Loss Tier 4 (ELEVATED) | 1.15 |
| Loss severity modifier | Loss Tier 4 (ELEVATED) | 1.15 |
| **Loss modifier** | Frequency × Severity, bounded [0.5, 1.8] | **1.32** |
| Exposure modifier | Size band SMALL | 0.75 |
| **Technical Premium** | Product of all factors | **$54,553** |

*Basis vs. limit: `tiv` is the total insured value the rate is applied to — a Base Rate of 0.55% on `tiv` is the rated cost of risk, not the policy limit. The policy Limit (anchored at $1,000,000) is the maximum payout and scales premium independently via the ILF curve; requesting a limit above the anchor lifts the ILF relativity above 1.00.*

**Loss Tier Sensitivity** — holding Risk Tier 3 and the Exposure modifier constant, the technical premium moves with the Loss tier:

| Loss Tier | Freq Mod | Sev Mod | Loss Modifier | Technical Premium |
|-----------|----------|---------|---------------|-------------------|
| 1 VERY_LOW | 0.70 | 0.80 | 0.56 | $23,100 |
| 2 LOW | 0.85 | 0.90 | 0.77 | $31,556 |
| 3 MODERATE | 1.00 | 1.00 | 1.00 | $41,250 |
| 4 ELEVATED  *(example)* | 1.15 | 1.15 | 1.32 | $54,553 |
| 5 HIGH | 1.35 | 1.40 | 1.80 | $74,250 |


---

## Model: `property_sme`
*Small-to-medium commercial property — TIV under $5M, simplified assessment*

### Routing Protocol (Multiplexer)
- `tiv < 5000000`

### Three-Layer Weight Distribution
> *DSI requires that weights for Risk, Loss, and Exposure each sum to 1.0 across all signal groups.*

**Validation:** PASS

| Group | Risk | Loss | Exposure |
|-------|------|------|----------|
| Construction Quality | 0.55 | 0.50 | 0.30 |
| Occupancy Risk | 0.45 | 0.50 | 0.70 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

**Group Definitions:**
- **Construction Quality:** Structural integrity, construction class, age, maintenance, and building code compliance
- **Occupancy Risk:** Tenant type, hazard grade, contents value density, and vacancy exposure

*Reading the table: a group's three weights are independent. The same group can be a dominant driver of one pillar and a minor input to another — e.g. a group may carry most of the Exposure weight while contributing little to Risk.*

### Signal Architecture Rationale
This configuration contains **37 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `DIRECT_OBSERVABLE` (20 signals): Highest confidence
- `INFERRED_PROXY` (16 signals): Medium confidence
- `COHORT_INFERENCE` (1 signals): Lowest confidence

**Signal Count by Group:**
- `technical_infrastructure`: 20 signals
- `structured_data`: 17 signals

**Selection Rationale:**
- 54% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Detail by Group
> *Each signal is an objectively observable data point. The weights show how strongly that signal informs each assessment pillar; correlation direction indicates whether a higher observed value increases (+) or decreases (-) the assessed exposure.*

#### Construction Quality
*Structural integrity, construction class, age, maintenance, and building code compliance*

| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `building_age_condition` | DIRECT_OBSERVABLE | 0.25 | 0.20 / 0.10 | 0.05 | + |
| `building_code_compliance` | INFERRED_PROXY | 0.20 | 0.15 / 0.10 | 0.00 | + |
| `roof_condition` | DIRECT_OBSERVABLE | 0.15 | 0.25 / 0.10 | 0.00 | + |
| `electrical_system_quality` | INFERRED_PROXY | 0.15 | 0.20 / 0.10 | 0.00 | + |
| `renovation_history` | INFERRED_PROXY | 0.10 | 0.05 / 0.00 | 0.10 | + |
| `fire_alarm_quality` | DIRECT_OBSERVABLE | 0.15 | 0.20 / 0.15 | 0.00 | + |
| `fire_department_response` | DIRECT_OBSERVABLE | 0.15 | 0.00 / 0.20 | 0.00 | + |
| `fire_separation` | INFERRED_PROXY | 0.10 | 0.00 / 0.15 | 0.00 | + |
| `water_supply_adequacy` | DIRECT_OBSERVABLE | 0.10 | 0.00 / 0.10 | 0.00 | + |
| `fema_flood_zone` | DIRECT_OBSERVABLE | 0.05 | 0.05 / 0.05 | 0.00 | + |
| `noaa_hail_history` | DIRECT_OBSERVABLE | 0.04 | 0.05 / 0.03 | 0.00 | + |
| `usfs_wildfire_hazard` | DIRECT_OBSERVABLE | 0.05 | 0.04 / 0.05 | 0.00 | + |
| `usgs_seismic_vs30` | DIRECT_OBSERVABLE | 0.04 | 0.00 / 0.05 | 0.00 | + |
| `nhc_track_proximity` | DIRECT_OBSERVABLE | 0.03 | 0.04 / 0.04 | 0.00 | + |
| `iso_caf_bceg_code_compliance` | INFERRED_PROXY | 0.04 | 0.00 / 0.04 | 0.00 | - |
| `energy_star_score` | INFERRED_PROXY | 0.03 | 0.03 / 0.00 | 0.00 | - |
| `building_permit_trail` | INFERRED_PROXY | 0.03 | 0.03 / 0.00 | 0.00 | - |
| `overhead_imagery_condition_score` | INFERRED_PROXY | 0.04 | 0.00 / 0.03 | 0.00 | - |

**Categorical signal `construction_class`** — proxy tier: `DIRECT_OBSERVABLE`, source: `metadata.construction_class`

| Category | Label | Applied Factor |
|----------|-------|----------------|
| `FR` | Fire Resistive | 0.7 |
| `MFR` | Modified Fire Resistive | 0.8 |
| `MNC` | Masonry Non-Combustible | 0.9 |
| `NC` | Non-Combustible | 0.95 |
| `JM` | Joisted Masonry | 1.1 |
| `F` | Frame | 1.4 |

**Categorical signal `sprinkler_coverage`** — proxy tier: `DIRECT_OBSERVABLE`, source: `metadata.sprinkler_coverage`

| Category | Label | Applied Factor |
|----------|-------|----------------|
| `FULL_WET` | Full Wet Sprinkler | 0.55 |
| `FULL_DRY` | Full Dry Sprinkler | 0.65 |
| `PARTIAL` | Partial Sprinkler | 0.85 |
| `NONE` | No Sprinklers | 1.3 |

#### Occupancy Risk
*Tenant type, hazard grade, contents value density, and vacancy exposure*

| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `tenant_concentration` | INFERRED_PROXY | 0.15 | 0.00 / 0.15 | 0.10 | - |
| `contents_value_density` | INFERRED_PROXY | 0.10 | 0.00 / 0.25 | 0.15 | + |
| `vacancy_rate` | DIRECT_OBSERVABLE | 0.20 | 0.20 / 0.00 | 0.00 | + |
| `housekeeping_quality` | INFERRED_PROXY | 0.15 | 0.15 / 0.00 | 0.00 | + |
| `wind_zone` | DIRECT_OBSERVABLE | 0.10 | 0.15 / 0.25 | 0.20 | + |
| `earthquake_zone` | DIRECT_OBSERVABLE | 0.10 | 0.10 / 0.25 | 0.20 | + |
| `flood_zone` | DIRECT_OBSERVABLE | 0.10 | 0.20 / 0.15 | 0.15 | + |
| `wildfire_zone` | DIRECT_OBSERVABLE | 0.10 | 0.15 / 0.15 | 0.10 | + |
| `convective_storm_exposure` | INFERRED_PROXY | 0.05 | 0.15 / 0.10 | 0.00 | + |
| `geographic_concentration` | DIRECT_OBSERVABLE | 0.05 | 0.00 / 0.00 | 0.30 | + |
| `revenue_concentration` | INFERRED_PROXY | 0.10 | 0.00 / 0.25 | 0.20 | + |
| `recovery_time_estimate` | INFERRED_PROXY | 0.10 | 0.00 / 0.30 | 0.15 | + |
| `supply_chain_dependency` | INFERRED_PROXY | 0.05 | 0.00 / 0.15 | 0.20 | + |
| `contingent_bi_exposure` | COHORT_INFERENCE | 0.05 | 0.00 / 0.15 | 0.15 | + |
| `business_continuity_planning` | INFERRED_PROXY | 0.10 | 0.00 / 0.10 | 0.00 | + |
| `nfip_participation` | DIRECT_OBSERVABLE | 0.03 | 0.03 / 0.00 | 0.00 | - |

**Categorical signal `occupancy_hazard_grade`** — proxy tier: `DIRECT_OBSERVABLE`, source: `metadata.occupancy_hazard_grade`

| Category | Label | Applied Factor |
|----------|-------|----------------|
| `LOW` | Low Hazard (Office/Residential) | 0.75 |
| `MOD` | Moderate Hazard (Retail/Light Mfg) | 1.0 |
| `HIGH` | High Hazard (Heavy Mfg/Woodworking) | 1.35 |
| `SPECIAL` | Special Hazard (Chemical/Explosive) | 1.8 |

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 | Occupancy Risk | 1.65 | 0.45 | 0.50 | 0.70 |
| 2 | Construction Quality | 1.35 | 0.55 | 0.50 | 0.30 |

**Primary Assessment Driver:** `Occupancy Risk` with combined weight of 1.65
**Secondary Driver:** `Construction Quality` with combined weight of 1.35

### Three-Layer Pricing Translation
> *How each pillar's tier score becomes a concrete underwriting action or pricing modifier. This is the bridge between signal observation and premium.*

**Risk -> Underwriting Action & Base Rate**

| Tier | Score Band | Action | Rate / Method |
|------|-----------|--------|---------------|
| PREFERRED | 800-1000 | APPROVE | 0.12% (MULTIPLIER) |
| STANDARD_PLUS | 650-799 | APPROVE | 0.2% (MULTIPLIER) |
| STANDARD | 500-649 | REFER | 0.32% (MULTIPLIER) |
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
| MICRO | 0-20 | 0.5 | $0 - $5,000,000 |
| SMALL | 21-40 | 0.75 | $5,000,000 - $25,000,000 |
| MEDIUM | 41-60 | 1.0 | $25,000,000 - $100,000,000 |
| LARGE | 61-80 | 1.5 | $100,000,000 - $500,000,000 |
| VERY_LARGE | 81-100 | 2.5 | $500,000,000 - $5,000,000,000 |

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
| `tiv` (rating basis) | Routing-valid assumption | $2,500,000 |
| Base Rate | Risk Tier 3 (STANDARD) | 0.32% |
| **Base Premium** | `tiv` × Base Rate | **$8,000** |
| ILF relativity | Limit = anchor ($500,000) | 1.00 |
| Deductible factor | Deductible = anchor ($10,000) | 1.00 |
| Loss frequency modifier | Loss Tier 4 (ELEVATED) | 1.15 |
| Loss severity modifier | Loss Tier 4 (ELEVATED) | 1.15 |
| **Loss modifier** | Frequency × Severity, bounded [0.5, 1.8] | **1.32** |
| Exposure modifier | Size band MICRO | 0.50 |
| **Technical Premium** | Product of all factors | **$5,290** |

*Basis vs. limit: `tiv` is the total insured value the rate is applied to — a Base Rate of 0.32% on `tiv` is the rated cost of risk, not the policy limit. The policy Limit (anchored at $500,000) is the maximum payout and scales premium independently via the ILF curve; requesting a limit above the anchor lifts the ILF relativity above 1.00.*

**Loss Tier Sensitivity** — holding Risk Tier 3 and the Exposure modifier constant, the technical premium moves with the Loss tier:

| Loss Tier | Freq Mod | Sev Mod | Loss Modifier | Technical Premium |
|-----------|----------|---------|---------------|-------------------|
| 1 VERY_LOW | 0.70 | 0.80 | 0.56 | $2,240 |
| 2 LOW | 0.85 | 0.90 | 0.77 | $3,060 |
| 3 MODERATE | 1.00 | 1.00 | 1.00 | $4,000 |
| 4 ELEVATED  *(example)* | 1.15 | 1.15 | 1.32 | $5,290 |
| 5 HIGH | 1.35 | 1.40 | 1.80 | $7,200 |


---

## Model: `property_habitational`
*Habitational property — apartments, condos, senior living, hotels*

### Routing Protocol (Multiplexer)
- `occupancy_class in ['HABITATIONAL', 'APARTMENT', 'SENIOR_LIVING', 'HOTEL', 'DORM']`
- `tiv >= 1000000`

### Three-Layer Weight Distribution
> *DSI requires that weights for Risk, Loss, and Exposure each sum to 1.0 across all signal groups.*

**Validation:** PASS

| Group | Risk | Loss | Exposure |
|-------|------|------|----------|
| Construction & Life Safety | 0.55 | 0.50 | 0.30 |
| Occupancy & Tenancy | 0.35 | 0.40 | 0.55 |
| Corporate Footprint | 0.05 | 0.05 | 0.10 |
| Firm Stability | 0.05 | 0.05 | 0.05 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

**Group Definitions:**
- **Construction & Life Safety:** Construction class, sprinkler / fire-alarm, roof, age
- **Occupancy & Tenancy:** Occupancy hazard, tenant concentration, vacancy

*Reading the table: a group's three weights are independent. The same group can be a dominant driver of one pillar and a minor input to another — e.g. a group may carry most of the Exposure weight while contributing little to Risk.*

### Signal Architecture Rationale
This configuration contains **8 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `DIRECT_OBSERVABLE` (2 signals): Highest confidence
- `INFERRED_PROXY` (6 signals): Medium confidence

**Signal Count by Group:**
- `technical_infrastructure`: 5 signals
- `structured_data`: 3 signals

**Selection Rationale:**
- 25% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Detail by Group
> *Each signal is an objectively observable data point. The weights show how strongly that signal informs each assessment pillar; correlation direction indicates whether a higher observed value increases (+) or decreases (-) the assessed exposure.*

#### Construction & Life Safety
*Construction class, sprinkler / fire-alarm, roof, age*

| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `construction_class` | DIRECT_OBSERVABLE | 0.20 | 0.00 / 0.20 | 0.00 | + |
| `sprinkler_coverage` | DIRECT_OBSERVABLE | 0.15 | 0.18 / 0.00 | 0.00 | - |
| `fire_alarm_quality` | INFERRED_PROXY | 0.10 | 0.10 / 0.00 | 0.00 | - |
| `building_age_condition` | INFERRED_PROXY | 0.12 | 0.10 / 0.00 | 0.00 | + |
| `roof_condition` | INFERRED_PROXY | 0.08 | 0.10 / 0.00 | 0.00 | + |

#### Occupancy & Tenancy
*Occupancy hazard, tenant concentration, vacancy*

| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `occupancy_hazard_grade` | INFERRED_PROXY | 0.15 | 0.15 / 0.00 | 0.00 | + |
| `tenant_concentration` | INFERRED_PROXY | 0.10 | 0.00 / 0.10 | 0.00 | + |
| `vacancy_rate` | INFERRED_PROXY | 0.10 | 0.07 / 0.00 | 0.00 | + |

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 | Construction & Life Safety | 1.35 | 0.55 | 0.50 | 0.30 |
| 2 | Occupancy & Tenancy | 1.30 | 0.35 | 0.40 | 0.55 |
| 3 | Corporate Footprint | 0.20 | 0.05 | 0.05 | 0.10 |
| 4 | Firm Stability | 0.15 | 0.05 | 0.05 | 0.05 |

**Primary Assessment Driver:** `Construction & Life Safety` with combined weight of 1.35
**Secondary Driver:** `Occupancy & Tenancy` with combined weight of 1.30

### Three-Layer Pricing Translation
> *How each pillar's tier score becomes a concrete underwriting action or pricing modifier. This is the bridge between signal observation and premium.*

**Risk -> Underwriting Action & Base Rate**

| Tier | Score Band | Action | Rate / Method |
|------|-----------|--------|---------------|
| PREFERRED | 800-1000 | APPROVE | 0.1% (MULTIPLIER) |
| STANDARD_PLUS | 650-799 | APPROVE | 0.2% (MULTIPLIER) |
| STANDARD | 500-649 | REFER | 0.35% (MULTIPLIER) |
| SUBSTANDARD | 350-499 | REFER | 0.55% (MULTIPLIER) |
| DECLINE | 0-349 | DECLINE | 0.8% (MULTIPLIER) |

**Loss -> Frequency & Severity Modifiers**

| Tier | Score Band | Frequency Modifier | Severity Modifier |
|------|-----------|--------------------|-------------------|
| VERY_LOW | 80-100 | 0.7 | 0.8 |
| LOW | 60-79 | 0.85 | 0.9 |
| MODERATE | 40-59 | 1.0 | 1.0 |
| ELEVATED | 20-39 | 1.2 | 1.25 |
| HIGH | 0-19 | 1.5 | 1.6 |

*Loss modifier is bounded: floor 0.55, cap 1.7.*

**Exposure (size) -> Scale Modifier**

| Band | Score Band | Modifier | Implied Value Range |
|------|-----------|----------|---------------------|
| MICRO | 0-20 | 0.5 | $0 - $1,000,000 |
| SMALL | 21-40 | 0.75 | $1,000,000 - $10,000,000 |
| MEDIUM | 41-60 | 1.0 | $10,000,000 - $50,000,000 |
| LARGE | 61-80 | 1.5 | $50,000,000 - $250,000,000 |
| VERY_LARGE | 81-100 | 2.5 | $250,000,000 - $1,000,000,000 |

**Exposure (complexity) -> Scale Modifier**

| Band | Score Band | Modifier | Implied Value Range |
|------|-----------|----------|---------------------|
| SIMPLE | 0-20 | 0.85 | n/a |
| MODERATE | 21-40 | 0.95 | n/a |
| COMPLEX | 41-60 | 1.15 | n/a |
| HIGHLY_COMPLEX | 61-80 | 1.35 | n/a |
| EXTREMELY_COMPLEX | 81-100 | 1.7 | n/a |

### Theoretical Premium Calculation (Worked Example)
> *Per the DSI Premium Calculation Methodology v2.0, the full factor chain is:*
> *P_final = (Basis × Base Rate) × ILF_relativity × Deductible_Factor × Loss_Modifier × Exposure_Modifier*

**Worked example — Risk Tier 3 (STANDARD), Loss Tier 4 (ELEVATED), requesting the anchor limit/deductible:**

| Factor | Source | Value |
|--------|--------|-------|
| `tiv` (rating basis) | Routing-valid assumption | $3,000,000 |
| Base Rate | Risk Tier 3 (STANDARD) | 0.35% |
| **Base Premium** | `tiv` × Base Rate | **$10,500** |
| ILF relativity | Limit = anchor ($10,000,000) | 1.00 |
| Deductible factor | Deductible = anchor ($100,000) | 1.00 |
| Loss frequency modifier | Loss Tier 4 (ELEVATED) | 1.20 |
| Loss severity modifier | Loss Tier 4 (ELEVATED) | 1.25 |
| **Loss modifier** | Frequency × Severity, bounded [0.55, 1.7] | **1.50** |
| Exposure modifier | Size band SMALL | 0.75 |
| **Technical Premium** | Product of all factors | **$11,812** |

*Basis vs. limit: `tiv` is the total insured value the rate is applied to — a Base Rate of 0.35% on `tiv` is the rated cost of risk, not the policy limit. The policy Limit (anchored at $10,000,000) is the maximum payout and scales premium independently via the ILF curve; requesting a limit above the anchor lifts the ILF relativity above 1.00.*

**Loss Tier Sensitivity** — holding Risk Tier 3 and the Exposure modifier constant, the technical premium moves with the Loss tier:

| Loss Tier | Freq Mod | Sev Mod | Loss Modifier | Technical Premium |
|-----------|----------|---------|---------------|-------------------|
| 1 VERY_LOW | 0.70 | 0.80 | 0.56 | $4,410 |
| 2 LOW | 0.85 | 0.90 | 0.77 | $6,024 |
| 3 MODERATE | 1.00 | 1.00 | 1.00 | $7,875 |
| 4 ELEVATED  *(example)* | 1.20 | 1.25 | 1.50 | $11,812 |
| 5 HIGH | 1.50 | 1.60 | 1.70 | $13,388 |



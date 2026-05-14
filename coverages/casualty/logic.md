# DSI Logic Document: `CASUALTY`
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

## Model: `casualty_gl`
*Commercial general liability — premises, operations, products/completed ops*

### Routing Protocol (Multiplexer)
- `product_type in ['general_liability', 'products_liability']`
- `revenue >= 5000000`

### Three-Layer Weight Distribution
> *DSI requires that weights for Risk, Loss, and Exposure each sum to 1.0 across all signal groups.*

**Validation:** PASS

| Group | Risk | Loss | Exposure |
|-------|------|------|----------|
| General Liability Class Risk | 0.55 | 0.55 | 0.40 |
| Corporate Footprint | 0.15 | 0.10 | 0.20 |
| Firm Stability | 0.10 | 0.10 | 0.15 |
| Regulatory Standing | 0.20 | 0.25 | 0.25 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

**Group Definitions:**
- **General Liability Class Risk:** ISO GL class code, premises hazard, products/completed operations, contractual exposure

*Reading the table: a group's three weights are independent. The same group can be a dominant driver of one pillar and a minor input to another — e.g. a group may carry most of the Exposure weight while contributing little to Risk.*

### Signal Architecture Rationale
This configuration contains **15 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `DIRECT_OBSERVABLE` (5 signals): Highest confidence
- `INFERRED_PROXY` (9 signals): Medium confidence
- `COHORT_INFERENCE` (1 signals): Lowest confidence

**Signal Count by Group:**
- `structured_data`: 15 signals

**Selection Rationale:**
- 33% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Detail by Group
> *Each signal is an objectively observable data point. The weights show how strongly that signal informs each assessment pillar; correlation direction indicates whether a higher observed value increases (+) or decreases (-) the assessed exposure.*

#### General Liability Class Risk
*ISO GL class code, premises hazard, products/completed operations, contractual exposure*

| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `premises_condition` | INFERRED_PROXY | 0.20 | 0.25 / 0.10 | 0.00 | + |
| `products_completed_ops` | INFERRED_PROXY | 0.15 | 0.15 / 0.25 | 0.15 | + |
| `contractual_liability` | INFERRED_PROXY | 0.10 | 0.00 / 0.15 | 0.15 | + |
| `subcontractor_management` | INFERRED_PROXY | 0.15 | 0.15 / 0.00 | 0.10 | + |
| `litigation_environment` | COHORT_INFERENCE | 0.10 | 0.00 / 0.20 | 0.10 | + |
| `public_access_volume` | INFERRED_PROXY | 0.15 | 0.20 / 0.00 | 0.15 | + |
| `security_measures` | DIRECT_OBSERVABLE | 0.20 | 0.15 / 0.10 | 0.00 | + |
| `incident_response_capability` | INFERRED_PROXY | 0.15 | 0.00 / 0.15 | 0.00 | + |
| `alcohol_service` | DIRECT_OBSERVABLE | 0.10 | 0.15 / 0.15 | 0.00 | + |
| `multi_location_complexity` | DIRECT_OBSERVABLE | 0.10 | 0.00 / 0.00 | 0.35 | + |
| `premises_occupancy_class` | DIRECT_OBSERVABLE | 0.05 | 0.05 / 0.00 | 0.00 | + |
| `crowd_density_proxy` | INFERRED_PROXY | 0.03 | 0.04 / 0.00 | 0.00 | + |
| `slip_fall_benchmark` | INFERRED_PROXY | 0.03 | 0.04 / 0.00 | 0.00 | + |
| `guest_injury_disclosure_trail` | INFERRED_PROXY | 0.03 | 0.00 / 0.03 | 0.00 | + |

**Categorical signal `gl_class_code`** — proxy tier: `DIRECT_OBSERVABLE`, source: `metadata.gl_class_code`

| Category | Label | Applied Factor |
|----------|-------|----------------|
| `LOW` | Low Hazard (Office/Professional Services) | 0.65 |
| `MODERATE` | Moderate (Retail/Hospitality/Light Mfg) | 1.0 |
| `HIGH` | High Hazard (Construction/Heavy Mfg/Trucking) | 1.45 |
| `SEVERE` | Severe (Demolition/Roofing/Blasting) | 2.0 |

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 | General Liability Class Risk | 1.50 | 0.55 | 0.55 | 0.40 |
| 2 | Regulatory Standing | 0.70 | 0.20 | 0.25 | 0.25 |
| 3 | Corporate Footprint | 0.45 | 0.15 | 0.10 | 0.20 |
| 4 | Firm Stability | 0.35 | 0.10 | 0.10 | 0.15 |

**Primary Assessment Driver:** `General Liability Class Risk` with combined weight of 1.50
**Secondary Driver:** `Regulatory Standing` with combined weight of 0.70

### Three-Layer Pricing Translation
> *How each pillar's tier score becomes a concrete underwriting action or pricing modifier. This is the bridge between signal observation and premium.*

**Risk -> Underwriting Action & Base Rate**

| Tier | Score Band | Action | Rate / Method |
|------|-----------|--------|---------------|
| PREFERRED | 800-1000 | APPROVE | 0.12% (MULTIPLIER) |
| STANDARD_PLUS | 650-799 | APPROVE | 0.22% (MULTIPLIER) |
| STANDARD | 500-649 | REFER | 0.4% (MULTIPLIER) |
| SUBSTANDARD | 350-499 | REFER | 0.68% (MULTIPLIER) |
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
| MICRO | 0-20 | 0.5 | $0 - $2,000,000 |
| SMALL | 21-40 | 0.75 | $2,000,000 - $25,000,000 |
| MEDIUM | 41-60 | 1.0 | $25,000,000 - $250,000,000 |
| LARGE | 61-80 | 1.5 | $250,000,000 - $1,000,000,000 |
| VERY_LARGE | 81-100 | 2.5 | $1,000,000,000 - $10,000,000,000 |

**Exposure (complexity) -> Scale Modifier**

| Band | Score Band | Modifier | Implied Value Range |
|------|-----------|----------|---------------------|
| SIMPLE | 0-20 | 0.85 | n/a |
| MODERATE | 21-40 | 0.95 | n/a |
| COMPLEX | 41-60 | 1.1 | n/a |
| HIGHLY_COMPLEX | 61-80 | 1.3 | n/a |
| EXTREMELY_COMPLEX | 81-100 | 1.6 | n/a |

### Theoretical Premium Calculation (Tier 3 Standard)
> *Per the DSI Premium Calculation Methodology v2.0, the full factor chain is:*
> *P_final = (Basis × Base Rate) × ILF_relativity × Deductible_Factor × Loss_Frequency_Mod × Loss_Severity_Mod × Exposure_Mod*

**Worked example — standard-tier risk, requesting the anchor limit/deductible:**

| Factor | Source | Value |
|--------|--------|-------|
| `revenue` (rating basis) | Routing-valid assumption | $15,000,000 |
| Base Rate | Risk Tier 3 (STANDARD) | 0.4% |
| **Base Premium** | `revenue` × Base Rate | **$60,000** |
| ILF relativity | Limit = anchor ($1,000,000) | 1.00 |
| Deductible factor | Deductible = anchor ($10,000) | 1.00 |
| Loss frequency modifier | Loss Tier 3 (MODERATE) | 1.00 |
| Loss severity modifier | Loss Tier 3 (MODERATE) | 1.00 |
| Exposure modifier | Size band SMALL | 0.75 |
| **Technical Premium** | Product of all factors | **$45,000** |

*Basis vs. limit: `revenue` is the total insured value the rate is applied to — a Base Rate of 0.4% on `revenue` is the rated cost of risk, not the policy limit. The policy Limit (anchored at $1,000,000) is the maximum payout and scales premium independently via the ILF curve; requesting a limit above the anchor lifts the ILF relativity above 1.00. The Loss and Exposure modifiers are shown here at their standard-tier values and move with the tier scores in the Three-Layer Pricing Translation tables above.*

---

## Model: `casualty_wc`
*Workers compensation — payroll-based, experience mod driven, state-specific*

### Routing Protocol (Multiplexer)
- `product_type == workers_compensation`
- `payroll >= 1000000`

### Three-Layer Weight Distribution
> *DSI requires that weights for Risk, Loss, and Exposure each sum to 1.0 across all signal groups.*

**Validation:** PASS

| Group | Risk | Loss | Exposure |
|-------|------|------|----------|
| Workplace Safety | 0.55 | 0.60 | 0.40 |
| Premises & Operations | 0.15 | 0.15 | 0.20 |
| Corporate Footprint | 0.15 | 0.10 | 0.25 |
| Firm Stability | 0.15 | 0.15 | 0.15 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

**Group Definitions:**
- **Workplace Safety:** OSHA compliance, experience modification, safety programmes, injury patterns
- **Premises & Operations:** Public access, security measures, incident response, contractual controls

*Reading the table: a group's three weights are independent. The same group can be a dominant driver of one pillar and a minor input to another — e.g. a group may carry most of the Exposure weight while contributing little to Risk.*

### Signal Architecture Rationale
This configuration contains **10 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `DIRECT_OBSERVABLE` (5 signals): Highest confidence
- `INFERRED_PROXY` (5 signals): Medium confidence

**Signal Count by Group:**
- `public_record`: 5 signals
- `structured_data`: 5 signals

**Selection Rationale:**
- 50% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Detail by Group
> *Each signal is an objectively observable data point. The weights show how strongly that signal informs each assessment pillar; correlation direction indicates whether a higher observed value increases (+) or decreases (-) the assessed exposure.*

#### Workplace Safety
*OSHA compliance, experience modification, safety programmes, injury patterns*

| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `experience_modification` | DIRECT_OBSERVABLE | 0.30 | 0.25 / 0.15 | 0.00 | + |
| `osha_compliance` | DIRECT_OBSERVABLE | 0.25 | 0.20 / 0.00 | 0.00 | + |
| `safety_programme_quality` | INFERRED_PROXY | 0.20 | 0.20 / 0.10 | 0.00 | + |
| `return_to_work_programme` | INFERRED_PROXY | 0.10 | 0.00 / 0.20 | 0.00 | + |
| `occupational_disease_exposure` | INFERRED_PROXY | 0.10 | 0.00 / 0.20 | 0.15 | + |

#### Premises & Operations
*Public access, security measures, incident response, contractual controls*

| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `public_access_volume` | INFERRED_PROXY | 0.15 | 0.20 / 0.00 | 0.15 | + |
| `security_measures` | DIRECT_OBSERVABLE | 0.20 | 0.15 / 0.10 | 0.00 | + |
| `incident_response_capability` | INFERRED_PROXY | 0.15 | 0.00 / 0.15 | 0.00 | + |
| `alcohol_service` | DIRECT_OBSERVABLE | 0.10 | 0.15 / 0.15 | 0.00 | + |
| `multi_location_complexity` | DIRECT_OBSERVABLE | 0.10 | 0.00 / 0.00 | 0.35 | + |

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 | Workplace Safety | 1.55 | 0.55 | 0.60 | 0.40 |
| 2 | Premises & Operations | 0.50 | 0.15 | 0.15 | 0.20 |
| 3 | Corporate Footprint | 0.50 | 0.15 | 0.10 | 0.25 |
| 4 | Firm Stability | 0.45 | 0.15 | 0.15 | 0.15 |

**Primary Assessment Driver:** `Workplace Safety` with combined weight of 1.55
**Secondary Driver:** `Premises & Operations` with combined weight of 0.50

### Three-Layer Pricing Translation
> *How each pillar's tier score becomes a concrete underwriting action or pricing modifier. This is the bridge between signal observation and premium.*

**Risk -> Underwriting Action & Base Rate**

| Tier | Score Band | Action | Rate / Method |
|------|-----------|--------|---------------|
| PREFERRED | 800-1000 | APPROVE | 0.8% (MULTIPLIER) |
| STANDARD_PLUS | 650-799 | APPROVE | 1.5% (MULTIPLIER) |
| STANDARD | 500-649 | REFER | 2.5% (MULTIPLIER) |
| SUBSTANDARD | 350-499 | REFER | 4.5% (MULTIPLIER) |
| DECLINE | 0-349 | DECLINE | 7% (MULTIPLIER) |

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
| MICRO | 0-20 | 0.5 | $0 - $2,000,000 |
| SMALL | 21-40 | 0.75 | $2,000,000 - $25,000,000 |
| MEDIUM | 41-60 | 1.0 | $25,000,000 - $250,000,000 |
| LARGE | 61-80 | 1.5 | $250,000,000 - $1,000,000,000 |
| VERY_LARGE | 81-100 | 2.5 | $1,000,000,000 - $10,000,000,000 |

**Exposure (complexity) -> Scale Modifier**

| Band | Score Band | Modifier | Implied Value Range |
|------|-----------|----------|---------------------|
| SIMPLE | 0-20 | 0.85 | n/a |
| MODERATE | 21-40 | 0.95 | n/a |
| COMPLEX | 41-60 | 1.1 | n/a |
| HIGHLY_COMPLEX | 61-80 | 1.3 | n/a |
| EXTREMELY_COMPLEX | 81-100 | 1.6 | n/a |

### Theoretical Premium Calculation (Tier 3 Standard)
> *Per the DSI Premium Calculation Methodology v2.0, the full factor chain is:*
> *P_final = (Basis × Base Rate) × ILF_relativity × Deductible_Factor × Loss_Frequency_Mod × Loss_Severity_Mod × Exposure_Mod*

**Worked example — standard-tier risk, requesting the anchor limit/deductible:**

| Factor | Source | Value |
|--------|--------|-------|
| `payroll` (rating basis) | Routing-valid assumption | $3,000,000 |
| Base Rate | Risk Tier 3 (STANDARD) | 2.5% |
| **Base Premium** | `payroll` × Base Rate | **$75,000** |
| ILF relativity | Limit = anchor ($1,000,000) | 1.00 |
| Deductible factor | Deductible = anchor ($10,000) | 1.00 |
| Loss frequency modifier | Loss Tier 3 (MODERATE) | 1.00 |
| Loss severity modifier | Loss Tier 3 (MODERATE) | 1.00 |
| Exposure modifier | Size band SMALL | 0.75 |
| **Technical Premium** | Product of all factors | **$56,250** |

*Basis vs. limit: `payroll` is the total insured value the rate is applied to — a Base Rate of 2.5% on `payroll` is the rated cost of risk, not the policy limit. The policy Limit (anchored at $1,000,000) is the maximum payout and scales premium independently via the ILF curve; requesting a limit above the anchor lifts the ILF relativity above 1.00. The Loss and Exposure modifiers are shown here at their standard-tier values and move with the tier scores in the Three-Layer Pricing Translation tables above.*

---

## Model: `casualty_auto`
*Commercial auto fleet liability — fleet-value based, driver quality, telematics*

### Routing Protocol (Multiplexer)
- `product_type == commercial_auto`
- `fleet_value >= 500000`

### Three-Layer Weight Distribution
> *DSI requires that weights for Risk, Loss, and Exposure each sum to 1.0 across all signal groups.*

**Validation:** PASS

| Group | Risk | Loss | Exposure |
|-------|------|------|----------|
| Auto Fleet Risk | 0.50 | 0.50 | 0.40 |
| Corporate Footprint | 0.15 | 0.10 | 0.20 |
| Firm Stability | 0.15 | 0.15 | 0.15 |
| Regulatory Standing | 0.20 | 0.25 | 0.25 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

**Group Definitions:**
- **Auto Fleet Risk:** Fleet composition, driver quality, telematics, route hazard, accident frequency

*Reading the table: a group's three weights are independent. The same group can be a dominant driver of one pillar and a minor input to another — e.g. a group may carry most of the Exposure weight while contributing little to Risk.*

### Signal Architecture Rationale
This configuration contains **17 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `DIRECT_OBSERVABLE` (10 signals): Highest confidence
- `INFERRED_PROXY` (7 signals): Medium confidence

**Signal Count by Group:**
- `structured_data`: 17 signals

**Selection Rationale:**
- 59% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Detail by Group
> *Each signal is an objectively observable data point. The weights show how strongly that signal informs each assessment pillar; correlation direction indicates whether a higher observed value increases (+) or decreases (-) the assessed exposure.*

#### Auto Fleet Risk
*Fleet composition, driver quality, telematics, route hazard, accident frequency*

| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `driver_quality` | DIRECT_OBSERVABLE | 0.25 | 0.30 / 0.10 | 0.00 | + |
| `telematics_adoption` | DIRECT_OBSERVABLE | 0.15 | 0.15 / 0.10 | 0.00 | + |
| `route_hazard` | INFERRED_PROXY | 0.10 | 0.10 / 0.10 | 0.10 | + |
| `accident_frequency` | DIRECT_OBSERVABLE | 0.20 | 0.25 / 0.20 | 0.00 | + |
| `fleet_maintenance` | INFERRED_PROXY | 0.15 | 0.10 / 0.00 | 0.00 | + |
| `public_access_volume` | INFERRED_PROXY | 0.15 | 0.20 / 0.00 | 0.15 | + |
| `security_measures` | DIRECT_OBSERVABLE | 0.20 | 0.15 / 0.10 | 0.00 | + |
| `incident_response_capability` | INFERRED_PROXY | 0.15 | 0.00 / 0.15 | 0.00 | + |
| `alcohol_service` | DIRECT_OBSERVABLE | 0.10 | 0.15 / 0.15 | 0.00 | + |
| `multi_location_complexity` | DIRECT_OBSERVABLE | 0.10 | 0.00 / 0.00 | 0.35 | + |
| `fmcsa_sms_basic_scores` | DIRECT_OBSERVABLE | 0.05 | 0.05 / 0.00 | 0.00 | + |
| `dot_inspection_history` | DIRECT_OBSERVABLE | 0.04 | 0.04 / 0.00 | 0.00 | + |
| `csa_crash_indicator` | DIRECT_OBSERVABLE | 0.05 | 0.05 / 0.03 | 0.00 | + |
| `fleet_telematics_benchmark` | INFERRED_PROXY | 0.03 | 0.03 / 0.00 | 0.00 | - |
| `vehicle_age_distribution` | INFERRED_PROXY | 0.03 | 0.00 / 0.03 | 0.00 | + |
| `driver_hos_compliance` | INFERRED_PROXY | 0.03 | 0.03 / 0.00 | 0.00 | - |

**Categorical signal `fleet_composition`** — proxy tier: `DIRECT_OBSERVABLE`, source: `metadata.fleet_composition`

| Category | Label | Applied Factor |
|----------|-------|----------------|
| `LIGHT` | Light Vehicles (Cars/Vans/Pickups) | 0.8 |
| `MEDIUM` | Medium Trucks (Class 3-6) | 1.0 |
| `HEAVY` | Heavy Trucks (Class 7-8/Long Haul) | 1.35 |
| `SPECIALIZED` | Specialized (Tankers/Hazmat/Oversized) | 1.6 |
| `MIXED` | Mixed Fleet | 1.1 |

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 | Auto Fleet Risk | 1.40 | 0.50 | 0.50 | 0.40 |
| 2 | Regulatory Standing | 0.70 | 0.20 | 0.25 | 0.25 |
| 3 | Corporate Footprint | 0.45 | 0.15 | 0.10 | 0.20 |
| 4 | Firm Stability | 0.45 | 0.15 | 0.15 | 0.15 |

**Primary Assessment Driver:** `Auto Fleet Risk` with combined weight of 1.40
**Secondary Driver:** `Regulatory Standing` with combined weight of 0.70

### Three-Layer Pricing Translation
> *How each pillar's tier score becomes a concrete underwriting action or pricing modifier. This is the bridge between signal observation and premium.*

**Risk -> Underwriting Action & Base Rate**

| Tier | Score Band | Action | Rate / Method |
|------|-----------|--------|---------------|
| PREFERRED | 800-1000 | APPROVE | 1.2% (MULTIPLIER) |
| STANDARD_PLUS | 650-799 | APPROVE | 2% (MULTIPLIER) |
| STANDARD | 500-649 | REFER | 3.5% (MULTIPLIER) |
| SUBSTANDARD | 350-499 | REFER | 5.5% (MULTIPLIER) |
| DECLINE | 0-349 | DECLINE | 8% (MULTIPLIER) |

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
| MICRO | 0-20 | 0.5 | $0 - $2,000,000 |
| SMALL | 21-40 | 0.75 | $2,000,000 - $25,000,000 |
| MEDIUM | 41-60 | 1.0 | $25,000,000 - $250,000,000 |
| LARGE | 61-80 | 1.5 | $250,000,000 - $1,000,000,000 |
| VERY_LARGE | 81-100 | 2.5 | $1,000,000,000 - $10,000,000,000 |

**Exposure (complexity) -> Scale Modifier**

| Band | Score Band | Modifier | Implied Value Range |
|------|-----------|----------|---------------------|
| SIMPLE | 0-20 | 0.85 | n/a |
| MODERATE | 21-40 | 0.95 | n/a |
| COMPLEX | 41-60 | 1.1 | n/a |
| HIGHLY_COMPLEX | 61-80 | 1.3 | n/a |
| EXTREMELY_COMPLEX | 81-100 | 1.6 | n/a |

### Theoretical Premium Calculation (Tier 3 Standard)
> *Per the DSI Premium Calculation Methodology v2.0, the full factor chain is:*
> *P_final = (Basis × Base Rate) × ILF_relativity × Deductible_Factor × Loss_Frequency_Mod × Loss_Severity_Mod × Exposure_Mod*

**Worked example — standard-tier risk, requesting the anchor limit/deductible:**

| Factor | Source | Value |
|--------|--------|-------|
| `fleet_value` (rating basis) | Routing-valid assumption | $1,500,000 |
| Base Rate | Risk Tier 3 (STANDARD) | 3.5% |
| **Base Premium** | `fleet_value` × Base Rate | **$52,500** |
| ILF relativity | Limit = anchor ($1,000,000) | 1.00 |
| Deductible factor | Deductible = anchor ($10,000) | 1.00 |
| Loss frequency modifier | Loss Tier 3 (MODERATE) | 1.00 |
| Loss severity modifier | Loss Tier 3 (MODERATE) | 1.00 |
| Exposure modifier | Size band MICRO | 0.50 |
| **Technical Premium** | Product of all factors | **$26,250** |

*Basis vs. limit: `fleet_value` is the total insured value the rate is applied to — a Base Rate of 3.5% on `fleet_value` is the rated cost of risk, not the policy limit. The policy Limit (anchored at $1,000,000) is the maximum payout and scales premium independently via the ILF curve; requesting a limit above the anchor lifts the ILF relativity above 1.00. The Loss and Exposure modifiers are shown here at their standard-tier values and move with the tier scores in the Three-Layer Pricing Translation tables above.*

---

## Model: `casualty_umbrella`
*Umbrella/excess liability — underlying-premium based, tower position, nuclear verdict exposure*

### Routing Protocol (Multiplexer)
- `product_type == umbrella_excess`
- `underlying_premium >= 25000`

### Three-Layer Weight Distribution
> *DSI requires that weights for Risk, Loss, and Exposure each sum to 1.0 across all signal groups.*

**Validation:** PASS

| Group | Risk | Loss | Exposure |
|-------|------|------|----------|
| Umbrella & Excess Exposure | 0.60 | 0.60 | 0.55 |
| Corporate Footprint | 0.15 | 0.10 | 0.20 |
| Firm Stability | 0.10 | 0.10 | 0.10 |
| Litigation History | 0.15 | 0.20 | 0.15 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

**Group Definitions:**
- **Umbrella & Excess Exposure:** Underlying programme quality, attachment adequacy, stacking, nuclear verdict exposure

*Reading the table: a group's three weights are independent. The same group can be a dominant driver of one pillar and a minor input to another — e.g. a group may carry most of the Exposure weight while contributing little to Risk.*

### Signal Architecture Rationale
This configuration contains **18 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `DIRECT_OBSERVABLE` (7 signals): Highest confidence
- `INFERRED_PROXY` (9 signals): Medium confidence
- `COHORT_INFERENCE` (2 signals): Lowest confidence

**Signal Count by Group:**
- `structured_data`: 18 signals

**Selection Rationale:**
- 39% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Detail by Group
> *Each signal is an objectively observable data point. The weights show how strongly that signal informs each assessment pillar; correlation direction indicates whether a higher observed value increases (+) or decreases (-) the assessed exposure.*

#### Umbrella & Excess Exposure
*Underlying programme quality, attachment adequacy, stacking, nuclear verdict exposure*

| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `premises_condition` | INFERRED_PROXY | 0.20 | 0.25 / 0.10 | 0.00 | + |
| `products_completed_ops` | INFERRED_PROXY | 0.15 | 0.15 / 0.25 | 0.15 | + |
| `contractual_liability` | INFERRED_PROXY | 0.10 | 0.00 / 0.15 | 0.15 | + |
| `subcontractor_management` | INFERRED_PROXY | 0.15 | 0.15 / 0.00 | 0.10 | + |
| `litigation_environment` | COHORT_INFERENCE | 0.10 | 0.00 / 0.20 | 0.10 | + |
| `underlying_programme_quality` | DIRECT_OBSERVABLE | 0.30 | 0.20 / 0.15 | 0.00 | + |
| `attachment_point_adequacy` | INFERRED_PROXY | 0.25 | 0.25 / 0.10 | 0.00 | + |
| `nuclear_verdict_exposure` | COHORT_INFERENCE | 0.20 | 0.00 / 0.30 | 0.15 | + |
| `tower_position` | DIRECT_OBSERVABLE | 0.15 | 0.00 / 0.15 | 0.20 | + |
| `public_access_volume` | INFERRED_PROXY | 0.15 | 0.20 / 0.00 | 0.15 | + |
| `security_measures` | DIRECT_OBSERVABLE | 0.20 | 0.15 / 0.10 | 0.00 | + |
| `incident_response_capability` | INFERRED_PROXY | 0.15 | 0.00 / 0.15 | 0.00 | + |
| `alcohol_service` | DIRECT_OBSERVABLE | 0.10 | 0.15 / 0.15 | 0.00 | + |
| `multi_location_complexity` | DIRECT_OBSERVABLE | 0.10 | 0.00 / 0.00 | 0.35 | + |
| `underlying_schedule_consistency` | INFERRED_PROXY | 0.04 | 0.00 / 0.04 | 0.00 | - |
| `attachment_point_coherence` | INFERRED_PROXY | 0.03 | 0.00 / 0.04 | 0.00 | - |
| `lead_carrier_quality` | DIRECT_OBSERVABLE | 0.03 | 0.00 / 0.04 | 0.00 | - |

**Categorical signal `gl_class_code`** — proxy tier: `DIRECT_OBSERVABLE`, source: `metadata.gl_class_code`

| Category | Label | Applied Factor |
|----------|-------|----------------|
| `LOW` | Low Hazard (Office/Professional Services) | 0.65 |
| `MODERATE` | Moderate (Retail/Hospitality/Light Mfg) | 1.0 |
| `HIGH` | High Hazard (Construction/Heavy Mfg/Trucking) | 1.45 |
| `SEVERE` | Severe (Demolition/Roofing/Blasting) | 2.0 |

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 | Umbrella & Excess Exposure | 1.75 | 0.60 | 0.60 | 0.55 |
| 2 | Litigation History | 0.50 | 0.15 | 0.20 | 0.15 |
| 3 | Corporate Footprint | 0.45 | 0.15 | 0.10 | 0.20 |
| 4 | Firm Stability | 0.30 | 0.10 | 0.10 | 0.10 |

**Primary Assessment Driver:** `Umbrella & Excess Exposure` with combined weight of 1.75
**Secondary Driver:** `Litigation History` with combined weight of 0.50

### Three-Layer Pricing Translation
> *How each pillar's tier score becomes a concrete underwriting action or pricing modifier. This is the bridge between signal observation and premium.*

**Risk -> Underwriting Action & Base Rate**

| Tier | Score Band | Action | Rate / Method |
|------|-----------|--------|---------------|
| PREFERRED | 800-1000 | APPROVE | 20% (MULTIPLIER) |
| STANDARD_PLUS | 650-799 | APPROVE | 30% (MULTIPLIER) |
| STANDARD | 500-649 | REFER | 40% (MULTIPLIER) |
| SUBSTANDARD | 350-499 | REFER | 55% (MULTIPLIER) |
| DECLINE | 0-349 | DECLINE | 120% (MULTIPLIER) |

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
| MICRO | 0-20 | 0.5 | $0 - $2,000,000 |
| SMALL | 21-40 | 0.75 | $2,000,000 - $25,000,000 |
| MEDIUM | 41-60 | 1.0 | $25,000,000 - $250,000,000 |
| LARGE | 61-80 | 1.5 | $250,000,000 - $1,000,000,000 |
| VERY_LARGE | 81-100 | 2.5 | $1,000,000,000 - $10,000,000,000 |

**Exposure (complexity) -> Scale Modifier**

| Band | Score Band | Modifier | Implied Value Range |
|------|-----------|----------|---------------------|
| SIMPLE | 0-20 | 0.85 | n/a |
| MODERATE | 21-40 | 0.95 | n/a |
| COMPLEX | 41-60 | 1.1 | n/a |
| HIGHLY_COMPLEX | 61-80 | 1.3 | n/a |
| EXTREMELY_COMPLEX | 81-100 | 1.6 | n/a |

### Theoretical Premium Calculation (Tier 3 Standard)
> *Per the DSI Premium Calculation Methodology v2.0, the full factor chain is:*
> *P_final = (Basis × Base Rate) × ILF_relativity × Deductible_Factor × Loss_Frequency_Mod × Loss_Severity_Mod × Exposure_Mod*

**Worked example — standard-tier risk, requesting the anchor limit/deductible:**

| Factor | Source | Value |
|--------|--------|-------|
| `underlying_premium` (rating basis) | Routing-valid assumption | $75,000 |
| Base Rate | Risk Tier 3 (STANDARD) | 40% |
| **Base Premium** | `underlying_premium` × Base Rate | **$30,000** |
| ILF relativity | Limit = anchor ($1,000,000) | 1.00 |
| Deductible factor | Deductible = anchor ($10,000) | 1.00 |
| Loss frequency modifier | Loss Tier 3 (MODERATE) | 1.00 |
| Loss severity modifier | Loss Tier 3 (MODERATE) | 1.00 |
| Exposure modifier | Size band MICRO | 0.50 |
| **Technical Premium** | Product of all factors | **$15,000** |

*Basis vs. limit: `underlying_premium` is the total insured value the rate is applied to — a Base Rate of 40% on `underlying_premium` is the rated cost of risk, not the policy limit. The policy Limit (anchored at $1,000,000) is the maximum payout and scales premium independently via the ILF curve; requesting a limit above the anchor lifts the ILF relativity above 1.00. The Loss and Exposure modifiers are shown here at their standard-tier values and move with the tier scores in the Three-Layer Pricing Translation tables above.*

---

## Model: `casualty_environmental`
*Environmental liability — pollution, remediation, regulatory defence, third-party claims*

### Routing Protocol (Multiplexer)
- `product_type == environmental_liability`
- `revenue >= 5000000`

### Three-Layer Weight Distribution
> *DSI requires that weights for Risk, Loss, and Exposure each sum to 1.0 across all signal groups.*

**Validation:** PASS

| Group | Risk | Loss | Exposure |
|-------|------|------|----------|
| Environmental Liability | 0.55 | 0.60 | 0.45 |
| General Liability Class Risk | 0.20 | 0.20 | 0.25 |
| Corporate Footprint | 0.15 | 0.10 | 0.20 |
| Firm Stability | 0.10 | 0.10 | 0.10 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

**Group Definitions:**
- **Environmental Liability:** Pollution conditions, remediation history, tank compliance, regulatory exposure
- **General Liability Class Risk:** ISO GL class code, premises hazard, products/completed operations, contractual exposure

*Reading the table: a group's three weights are independent. The same group can be a dominant driver of one pillar and a minor input to another — e.g. a group may carry most of the Exposure weight while contributing little to Risk.*

### Signal Architecture Rationale
This configuration contains **40 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `DIRECT_OBSERVABLE` (11 signals): Highest confidence
- `INFERRED_PROXY` (27 signals): Medium confidence
- `COHORT_INFERENCE` (2 signals): Lowest confidence

**Signal Count by Group:**
- `public_record`: 29 signals
- `structured_data`: 11 signals

**Selection Rationale:**
- 28% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Detail by Group
> *Each signal is an objectively observable data point. The weights show how strongly that signal informs each assessment pillar; correlation direction indicates whether a higher observed value increases (+) or decreases (-) the assessed exposure.*

#### Environmental Liability
*Pollution conditions, remediation history, tank compliance, regulatory exposure*

| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `pollution_conditions` | DIRECT_OBSERVABLE | 0.25 | 0.15 / 0.25 | 0.00 | + |
| `ust_ast_compliance` | DIRECT_OBSERVABLE | 0.20 | 0.20 / 0.15 | 0.00 | + |
| `regulatory_enforcement_history` | DIRECT_OBSERVABLE | 0.20 | 0.15 / 0.15 | 0.00 | + |
| `waste_management_practices` | INFERRED_PROXY | 0.15 | 0.15 / 0.10 | 0.00 | + |
| `third_party_site_exposure` | COHORT_INFERENCE | 0.10 | 0.00 / 0.20 | 0.15 | + |
| `epa_echo_violation_depth` | DIRECT_OBSERVABLE | 0.05 | 0.04 / 0.04 | 0.00 | + |
| `superfund_proximity` | DIRECT_OBSERVABLE | 0.03 | 0.00 / 0.04 | 0.00 | + |
| `tri_reportable_volume` | DIRECT_OBSERVABLE | 0.04 | 0.03 / 0.04 | 0.00 | + |
| `state_dep_action_history` | DIRECT_OBSERVABLE | 0.04 | 0.04 / 0.00 | 0.00 | + |
| `casualty_primary_derived_01` | INFERRED_PROXY | 0.01 | 0.01 / 0.00 | 0.00 | + |
| `casualty_primary_derived_02` | INFERRED_PROXY | 0.01 | 0.00 / 0.00 | 0.00 | + |
| `casualty_primary_derived_03` | INFERRED_PROXY | 0.01 | 0.00 / 0.01 | 0.00 | + |
| `casualty_primary_derived_04` | INFERRED_PROXY | 0.01 | 0.01 / 0.00 | 0.00 | + |
| `casualty_primary_derived_05` | INFERRED_PROXY | 0.01 | 0.00 / 0.00 | 0.00 | + |
| `casualty_primary_derived_06` | INFERRED_PROXY | 0.01 | 0.00 / 0.01 | 0.00 | + |
| `casualty_primary_derived_07` | INFERRED_PROXY | 0.01 | 0.01 / 0.00 | 0.00 | + |
| `casualty_primary_derived_08` | INFERRED_PROXY | 0.01 | 0.00 / 0.00 | 0.00 | + |
| `casualty_primary_derived_09` | INFERRED_PROXY | 0.01 | 0.00 / 0.01 | 0.00 | + |
| `casualty_primary_derived_10` | INFERRED_PROXY | 0.01 | 0.01 / 0.00 | 0.00 | + |
| `casualty_primary_derived_11` | INFERRED_PROXY | 0.01 | 0.00 / 0.00 | 0.00 | + |
| `casualty_primary_derived_12` | INFERRED_PROXY | 0.01 | 0.00 / 0.01 | 0.00 | + |
| `casualty_primary_derived_13` | INFERRED_PROXY | 0.01 | 0.01 / 0.00 | 0.00 | + |
| `casualty_primary_derived_14` | INFERRED_PROXY | 0.01 | 0.00 / 0.00 | 0.00 | + |
| `casualty_primary_derived_15` | INFERRED_PROXY | 0.01 | 0.00 / 0.01 | 0.00 | + |
| `casualty_primary_derived_16` | INFERRED_PROXY | 0.01 | 0.01 / 0.00 | 0.00 | + |
| `casualty_primary_derived_17` | INFERRED_PROXY | 0.01 | 0.00 / 0.00 | 0.00 | + |
| `casualty_primary_derived_18` | INFERRED_PROXY | 0.01 | 0.00 / 0.01 | 0.00 | + |
| `casualty_primary_derived_19` | INFERRED_PROXY | 0.01 | 0.01 / 0.00 | 0.00 | + |
| `casualty_primary_derived_20` | INFERRED_PROXY | 0.01 | 0.00 / 0.00 | 0.00 | + |

#### General Liability Class Risk
*ISO GL class code, premises hazard, products/completed operations, contractual exposure*

| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `premises_condition` | INFERRED_PROXY | 0.20 | 0.25 / 0.10 | 0.00 | + |
| `products_completed_ops` | INFERRED_PROXY | 0.15 | 0.15 / 0.25 | 0.15 | + |
| `contractual_liability` | INFERRED_PROXY | 0.10 | 0.00 / 0.15 | 0.15 | + |
| `subcontractor_management` | INFERRED_PROXY | 0.15 | 0.15 / 0.00 | 0.10 | + |
| `litigation_environment` | COHORT_INFERENCE | 0.10 | 0.00 / 0.20 | 0.10 | + |
| `public_access_volume` | INFERRED_PROXY | 0.15 | 0.20 / 0.00 | 0.15 | + |
| `security_measures` | DIRECT_OBSERVABLE | 0.20 | 0.15 / 0.10 | 0.00 | + |
| `incident_response_capability` | INFERRED_PROXY | 0.15 | 0.00 / 0.15 | 0.00 | + |
| `alcohol_service` | DIRECT_OBSERVABLE | 0.10 | 0.15 / 0.15 | 0.00 | + |
| `multi_location_complexity` | DIRECT_OBSERVABLE | 0.10 | 0.00 / 0.00 | 0.35 | + |

**Categorical signal `gl_class_code`** — proxy tier: `DIRECT_OBSERVABLE`, source: `metadata.gl_class_code`

| Category | Label | Applied Factor |
|----------|-------|----------------|
| `LOW` | Low Hazard (Office/Professional Services) | 0.65 |
| `MODERATE` | Moderate (Retail/Hospitality/Light Mfg) | 1.0 |
| `HIGH` | High Hazard (Construction/Heavy Mfg/Trucking) | 1.45 |
| `SEVERE` | Severe (Demolition/Roofing/Blasting) | 2.0 |

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 | Environmental Liability | 1.60 | 0.55 | 0.60 | 0.45 |
| 2 | General Liability Class Risk | 0.65 | 0.20 | 0.20 | 0.25 |
| 3 | Corporate Footprint | 0.45 | 0.15 | 0.10 | 0.20 |
| 4 | Firm Stability | 0.30 | 0.10 | 0.10 | 0.10 |

**Primary Assessment Driver:** `Environmental Liability` with combined weight of 1.60
**Secondary Driver:** `General Liability Class Risk` with combined weight of 0.65

### Three-Layer Pricing Translation
> *How each pillar's tier score becomes a concrete underwriting action or pricing modifier. This is the bridge between signal observation and premium.*

**Risk -> Underwriting Action & Base Rate**

| Tier | Score Band | Action | Rate / Method |
|------|-----------|--------|---------------|
| PREFERRED | 800-1000 | APPROVE | 0.15% (MULTIPLIER) |
| STANDARD_PLUS | 650-799 | APPROVE | 0.28% (MULTIPLIER) |
| STANDARD | 500-649 | REFER | 0.5% (MULTIPLIER) |
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
| MICRO | 0-20 | 0.5 | $0 - $2,000,000 |
| SMALL | 21-40 | 0.75 | $2,000,000 - $25,000,000 |
| MEDIUM | 41-60 | 1.0 | $25,000,000 - $250,000,000 |
| LARGE | 61-80 | 1.5 | $250,000,000 - $1,000,000,000 |
| VERY_LARGE | 81-100 | 2.5 | $1,000,000,000 - $10,000,000,000 |

**Exposure (complexity) -> Scale Modifier**

| Band | Score Band | Modifier | Implied Value Range |
|------|-----------|----------|---------------------|
| SIMPLE | 0-20 | 0.85 | n/a |
| MODERATE | 21-40 | 0.95 | n/a |
| COMPLEX | 41-60 | 1.1 | n/a |
| HIGHLY_COMPLEX | 61-80 | 1.3 | n/a |
| EXTREMELY_COMPLEX | 81-100 | 1.6 | n/a |

### Theoretical Premium Calculation (Tier 3 Standard)
> *Per the DSI Premium Calculation Methodology v2.0, the full factor chain is:*
> *P_final = (Basis × Base Rate) × ILF_relativity × Deductible_Factor × Loss_Frequency_Mod × Loss_Severity_Mod × Exposure_Mod*

**Worked example — standard-tier risk, requesting the anchor limit/deductible:**

| Factor | Source | Value |
|--------|--------|-------|
| `revenue` (rating basis) | Routing-valid assumption | $15,000,000 |
| Base Rate | Risk Tier 3 (STANDARD) | 0.5% |
| **Base Premium** | `revenue` × Base Rate | **$75,000** |
| ILF relativity | Limit = anchor ($1,000,000) | 1.00 |
| Deductible factor | Deductible = anchor ($25,000) | 1.00 |
| Loss frequency modifier | Loss Tier 3 (MODERATE) | 1.00 |
| Loss severity modifier | Loss Tier 3 (MODERATE) | 1.00 |
| Exposure modifier | Size band SMALL | 0.75 |
| **Technical Premium** | Product of all factors | **$56,250** |

*Basis vs. limit: `revenue` is the total insured value the rate is applied to — a Base Rate of 0.5% on `revenue` is the rated cost of risk, not the policy limit. The policy Limit (anchored at $1,000,000) is the maximum payout and scales premium independently via the ILF curve; requesting a limit above the anchor lifts the ILF relativity above 1.00. The Loss and Exposure modifiers are shown here at their standard-tier values and move with the tier scores in the Three-Layer Pricing Translation tables above.*

---

## Model: `casualty_sme`
*Small-to-medium casualty — revenue under $5M, simplified GL + products*

### Routing Protocol (Multiplexer)
- `product_type in ['general_liability', 'products_liability']`
- `revenue < 5000000`

### Three-Layer Weight Distribution
> *DSI requires that weights for Risk, Loss, and Exposure each sum to 1.0 across all signal groups.*

**Validation:** PASS

| Group | Risk | Loss | Exposure |
|-------|------|------|----------|
| General Liability Class Risk | 0.60 | 0.60 | 0.50 |
| Corporate Footprint | 0.15 | 0.15 | 0.20 |
| Firm Stability | 0.15 | 0.15 | 0.15 |
| Regulatory Standing | 0.10 | 0.10 | 0.15 |
| **TOTAL** | **1.00** | **1.00** | **1.00** |

**Group Definitions:**
- **General Liability Class Risk:** ISO GL class code, premises hazard, products/completed operations, contractual exposure

*Reading the table: a group's three weights are independent. The same group can be a dominant driver of one pillar and a minor input to another — e.g. a group may carry most of the Exposure weight while contributing little to Risk.*

### Signal Architecture Rationale
This configuration contains **11 signals** distributed as follows:

**By Proxy Tier (Confidence Hierarchy):**
- `DIRECT_OBSERVABLE` (4 signals): Highest confidence
- `INFERRED_PROXY` (6 signals): Medium confidence
- `COHORT_INFERENCE` (1 signals): Lowest confidence

**Signal Count by Group:**
- `structured_data`: 11 signals

**Selection Rationale:**
- 36% of signals are directly observable, ensuring objective, machine-readable assessment.
- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.
- Signal selection prioritizes external observability (DSI Foundational Principle #1).

### Signal Detail by Group
> *Each signal is an objectively observable data point. The weights show how strongly that signal informs each assessment pillar; correlation direction indicates whether a higher observed value increases (+) or decreases (-) the assessed exposure.*

#### General Liability Class Risk
*ISO GL class code, premises hazard, products/completed operations, contractual exposure*

| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |
|--------|-----------|------|-----------------|----------|-----|
| `premises_condition` | INFERRED_PROXY | 0.20 | 0.25 / 0.10 | 0.00 | + |
| `products_completed_ops` | INFERRED_PROXY | 0.15 | 0.15 / 0.25 | 0.15 | + |
| `contractual_liability` | INFERRED_PROXY | 0.10 | 0.00 / 0.15 | 0.15 | + |
| `subcontractor_management` | INFERRED_PROXY | 0.15 | 0.15 / 0.00 | 0.10 | + |
| `litigation_environment` | COHORT_INFERENCE | 0.10 | 0.00 / 0.20 | 0.10 | + |
| `public_access_volume` | INFERRED_PROXY | 0.15 | 0.20 / 0.00 | 0.15 | + |
| `security_measures` | DIRECT_OBSERVABLE | 0.20 | 0.15 / 0.10 | 0.00 | + |
| `incident_response_capability` | INFERRED_PROXY | 0.15 | 0.00 / 0.15 | 0.00 | + |
| `alcohol_service` | DIRECT_OBSERVABLE | 0.10 | 0.15 / 0.15 | 0.00 | + |
| `multi_location_complexity` | DIRECT_OBSERVABLE | 0.10 | 0.00 / 0.00 | 0.35 | + |

**Categorical signal `gl_class_code`** — proxy tier: `DIRECT_OBSERVABLE`, source: `metadata.gl_class_code`

| Category | Label | Applied Factor |
|----------|-------|----------------|
| `LOW` | Low Hazard (Office/Professional Services) | 0.65 |
| `MODERATE` | Moderate (Retail/Hospitality/Light Mfg) | 1.0 |
| `HIGH` | High Hazard (Construction/Heavy Mfg/Trucking) | 1.45 |
| `SEVERE` | Severe (Demolition/Roofing/Blasting) | 2.0 |

### Signal Group Importance Ranking
> *Groups ranked by combined weight across all three assessment layers.*

| Rank | Group | Combined | Risk | Loss | Exposure |
|------|-------|----------|------|------|----------|
| 1 | General Liability Class Risk | 1.70 | 0.60 | 0.60 | 0.50 |
| 2 | Corporate Footprint | 0.50 | 0.15 | 0.15 | 0.20 |
| 3 | Firm Stability | 0.45 | 0.15 | 0.15 | 0.15 |
| 4 | Regulatory Standing | 0.35 | 0.10 | 0.10 | 0.15 |

**Primary Assessment Driver:** `General Liability Class Risk` with combined weight of 1.70
**Secondary Driver:** `Corporate Footprint` with combined weight of 0.50

### Three-Layer Pricing Translation
> *How each pillar's tier score becomes a concrete underwriting action or pricing modifier. This is the bridge between signal observation and premium.*

**Risk -> Underwriting Action & Base Rate**

| Tier | Score Band | Action | Rate / Method |
|------|-----------|--------|---------------|
| PREFERRED | 800-1000 | APPROVE | 0.18% (MULTIPLIER) |
| STANDARD_PLUS | 650-799 | APPROVE | 0.3% (MULTIPLIER) |
| STANDARD | 500-649 | REFER | 0.5% (MULTIPLIER) |
| SUBSTANDARD | 350-499 | REFER | 0.8% (MULTIPLIER) |
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
| MICRO | 0-20 | 0.5 | $0 - $2,000,000 |
| SMALL | 21-40 | 0.75 | $2,000,000 - $25,000,000 |
| MEDIUM | 41-60 | 1.0 | $25,000,000 - $250,000,000 |
| LARGE | 61-80 | 1.5 | $250,000,000 - $1,000,000,000 |
| VERY_LARGE | 81-100 | 2.5 | $1,000,000,000 - $10,000,000,000 |

**Exposure (complexity) -> Scale Modifier**

| Band | Score Band | Modifier | Implied Value Range |
|------|-----------|----------|---------------------|
| SIMPLE | 0-20 | 0.85 | n/a |
| MODERATE | 21-40 | 0.95 | n/a |
| COMPLEX | 41-60 | 1.1 | n/a |
| HIGHLY_COMPLEX | 61-80 | 1.3 | n/a |
| EXTREMELY_COMPLEX | 81-100 | 1.6 | n/a |

### Theoretical Premium Calculation (Tier 3 Standard)
> *Per the DSI Premium Calculation Methodology v2.0, the full factor chain is:*
> *P_final = (Basis × Base Rate) × ILF_relativity × Deductible_Factor × Loss_Frequency_Mod × Loss_Severity_Mod × Exposure_Mod*

**Worked example — standard-tier risk, requesting the anchor limit/deductible:**

| Factor | Source | Value |
|--------|--------|-------|
| `revenue` (rating basis) | Routing-valid assumption | $2,500,000 |
| Base Rate | Risk Tier 3 (STANDARD) | 0.5% |
| **Base Premium** | `revenue` × Base Rate | **$12,500** |
| ILF relativity | Limit = anchor ($500,000) | 1.00 |
| Deductible factor | Deductible = anchor ($5,000) | 1.00 |
| Loss frequency modifier | Loss Tier 3 (MODERATE) | 1.00 |
| Loss severity modifier | Loss Tier 3 (MODERATE) | 1.00 |
| Exposure modifier | Size band SMALL | 0.75 |
| **Technical Premium** | Product of all factors | **$9,375** |

*Basis vs. limit: `revenue` is the total insured value the rate is applied to — a Base Rate of 0.5% on `revenue` is the rated cost of risk, not the policy limit. The policy Limit (anchored at $500,000) is the maximum payout and scales premium independently via the ILF curve; requesting a limit above the anchor lifts the ILF relativity above 1.00. The Loss and Exposure modifiers are shown here at their standard-tier values and move with the tier scores in the Three-Layer Pricing Translation tables above.*


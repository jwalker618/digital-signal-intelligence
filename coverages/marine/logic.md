# Marine Coverage Configuration

**Coverage ID:** `marine`
**Generated:** 2026-02-15 09:41
**Schema Version:** v2.2

This document describes the configuration, decision logic, and pricing structure
for the Marine coverage vertical in the DSI platform.

## Table of Contents

1. [Configuration Overview](#configuration-overview)
2. [Signal Groups](#signal-groups)
3. [Scoring Logic](#scoring-logic)
4. [Pricing Structure](#pricing-structure)
5. [Direct Queries](#direct-queries)
6. [Decision Flow](#decision-flow)


---


## Configuration: Marine General

### Metadata

- **Name:** DSI Marine Technical Pricing Model
- **Version:** 2.2.0
- **Description:** Marine hull and liability coverage based on observable operator behavior, safety records, and fleet patterns
- **Product Types:** `hull_machinery`, `total_loss`, `increased_value`, `loss_of_hire`, `war_risks`, `pi_liability`, `cargo`
- **Markets:** GLOBAL
- **Minimum Premium:** $50,000
- **Currency:** USD

#### Multiplexer Configuration (V4)

- **Model Specificity:** 1 (General)
- **Routing Constraints:** None (accepts all)

### Signal Registry

**Total Signals:** 50


#### Group: `corporate_footprint`

| Signal ID | Type | Weight | Direction | Proxy Tier |
|-----------|------|--------|-----------|------------|
| `website_quality` | Scoring | 15.00% | positive | DIRECT_OBSERVABLE |
| `fleet_disclosure` | Scoring | 20.00% | positive | DIRECT_OBSERVABLE |
| `sustainability_reporting` | Scoring | 20.00% | positive | DIRECT_OBSERVABLE |
| `safety_communication` | Scoring | 20.00% | positive | INFERRED_PROXY |
| `crew_welfare` | Scoring | 10.00% | positive | INFERRED_PROXY |
| `industry_presence` | Scoring | 15.00% | positive | DIRECT_OBSERVABLE |

#### Group: `environmental`

| Signal ID | Type | Weight | Direction | Proxy Tier |
|-----------|------|--------|-----------|------------|
| `imo2020_compliance` | Scoring | 30.00% | positive | DIRECT_OBSERVABLE |
| `bwm_compliance` | Scoring | 25.00% | positive | DIRECT_OBSERVABLE |
| `cii_rating` | Scoring | 25.00% | positive | DIRECT_OBSERVABLE |
| `environmental_incident` | Scoring | 20.00% | positive | DIRECT_OBSERVABLE |

#### Group: `flag_state_quality`

| Signal ID | Type | Weight | Direction | Proxy Tier |
|-----------|------|--------|-----------|------------|
| `flag_state_quality` | Categorical | N/A | modifier | INFERRED_PROXY |

#### Group: `fleet_age_band`

| Signal ID | Type | Weight | Direction | Proxy Tier |
|-----------|------|--------|-----------|------------|
| `fleet_age_band` | Categorical | N/A | modifier | INFERRED_PROXY |

#### Group: `fleet_profile`

| Signal ID | Type | Weight | Direction | Proxy Tier |
|-----------|------|--------|-----------|------------|
| `fleet_age` | Scoring | 30.00% | negative | INFERRED_PROXY |
| `fleet_stability` | Scoring | 20.00% | positive | INFERRED_PROXY |
| `vessel_quality` | Scoring | 20.00% | positive | INFERRED_PROXY |
| `crew_certification` | Scoring | 15.00% | positive | DIRECT_OBSERVABLE |
| `management_consistency` | Scoring | 15.00% | positive | INFERRED_PROXY |

#### Group: `network_authority`

| Signal ID | Type | Weight | Direction | Proxy Tier |
|-----------|------|--------|-----------|------------|
| `classification_society` | Scoring | 15.00% | positive | DIRECT_OBSERVABLE |
| `pi_club` | Scoring | 15.00% | positive | DIRECT_OBSERVABLE |
| `charterer_quality` | Scoring | 15.00% | positive | INFERRED_PROXY |
| `banking_relationship` | Scoring | 10.00% | positive | INFERRED_PROXY |
| `flag_state` | Scoring | 15.00% | positive | DIRECT_OBSERVABLE |
| `industry_association` | Scoring | 10.00% | positive | DIRECT_OBSERVABLE |
| `technical_manager` | Scoring | 10.00% | positive | INFERRED_PROXY |
| `port_relationship` | Scoring | 0.00% | positive | INFERRED_PROXY |
| `port_state_control` | Scoring | 5.00% | positive | DIRECT_OBSERVABLE |
| `classification_society_quality` | Scoring | 5.00% | positive | DIRECT_OBSERVABLE |

#### Group: `operational_telemetry`

| Signal ID | Type | Weight | Direction | Proxy Tier |
|-----------|------|--------|-----------|------------|
| `ais_compliance` | Scoring | 25.00% | positive | DIRECT_OBSERVABLE |
| `dark_activity` | Scoring | 25.00% | negative | DIRECT_OBSERVABLE |
| `route_risk` | Scoring | 20.00% | negative | DIRECT_OBSERVABLE |
| `psc_region_exposure` | Scoring | 10.00% | positive | DIRECT_OBSERVABLE |
| `operational_efficiency` | Scoring | 10.00% | positive | INFERRED_PROXY |
| `weather_routing` | Scoring | 10.00% | positive | INFERRED_PROXY |

#### Group: `operator_type`

| Signal ID | Type | Weight | Direction | Proxy Tier |
|-----------|------|--------|-----------|------------|
| `operator_type` | Categorical | N/A | modifier | INFERRED_PROXY |

#### Group: `safety_compliance`

| Signal ID | Type | Weight | Direction | Proxy Tier |
|-----------|------|--------|-----------|------------|
| `psc_detention` | Scoring | 25.00% | positive | DIRECT_OBSERVABLE |
| `psc_deficiency` | Scoring | 20.00% | positive | DIRECT_OBSERVABLE |
| `class_status` | Scoring | 20.00% | positive | DIRECT_OBSERVABLE |
| `ism_compliance` | Scoring | 15.00% | positive | DIRECT_OBSERVABLE |
| `casualty_history` | Scoring | 10.00% | positive | DIRECT_OBSERVABLE |
| `total_loss` | Scoring | 10.00% | positive | DIRECT_OBSERVABLE |

#### Group: `sanctions_compliance`

| Signal ID | Type | Weight | Direction | Proxy Tier |
|-----------|------|--------|-----------|------------|
| `sanctions_status` | Scoring | 30.00% | positive | DIRECT_OBSERVABLE |
| `ownership_transparency` | Scoring | 20.00% | positive | INFERRED_PROXY |
| `jurisdiction_risk` | Scoring | 20.00% | negative | DIRECT_OBSERVABLE |
| `sts_pattern` | Scoring | 15.00% | negative | DIRECT_OBSERVABLE |
| `historical_sanctions` | Scoring | 15.00% | positive | DIRECT_OBSERVABLE |

#### Group: `structured_data`

| Signal ID | Type | Weight | Direction | Proxy Tier |
|-----------|------|--------|-----------|------------|
| `vetting` | Scoring | 50.00% | positive | DIRECT_OBSERVABLE |
| `esg_rating` | Scoring | 30.00% | positive | DIRECT_OBSERVABLE |
| `credit_rating` | Scoring | 20.00% | positive | DIRECT_OBSERVABLE |

#### Group: `trading_pattern`

| Signal ID | Type | Weight | Direction | Proxy Tier |
|-----------|------|--------|-----------|------------|
| `trading_pattern` | Categorical | N/A | modifier | INFERRED_PROXY |

#### Group: `vessel_category`

| Signal ID | Type | Weight | Direction | Proxy Tier |
|-----------|------|--------|-----------|------------|
| `vessel_category` | Categorical | N/A | modifier | INFERRED_PROXY |

### Signal Groups

#### Categorical Groups

These groups apply modifiers based on classification:

| Group ID | Label | Impact | Default |
|----------|-------|--------|---------|
| `operator_type` | Operator Type | MODIFIER | UNKNOWN |
| `vessel_category` | Vessel Category | MODIFIER | OTHER |
| ` trading_pattern` | Trading Pattern | MODIFIER | OTHER |
| `flag_state_quality` | Flag State Quality | MODIFIER | OTHER |
| `fleet_age_band` | Fleet Age Band | MODIFIER | OTHER |

#### Three-Layer Assessment Groups

These groups contribute to Risk, Loss, and Exposure scoring:

| Group ID | Risk Weight | Loss Weight | Exposure Weight |
|----------|-------------|-------------|-----------------|
| `network_authority` | 15% | 10% | 5% |
| `operational_telemetry` | 20% | 15% | 15% |
| `safety_compliance` | 25% | 35% | 10% |
| `fleet_profile` | 10% | 15% | 35% |
| `sanctions_compliance` | 15% | 10% | 10% |
| `environmental` | 5% | 5% | 10% |
| `corporate_footprint` | 5% | 5% | 10% |
| `structured_data` | 5% | 5% | 5% |

### Risk Tier Bands

Risk tiers determine the base pricing and underwriting action:

| Tier | Label | Score Range | Action | Base Premium |
|------|-------|-------------|--------|--------------|
| 1 | PREFERRED | 800-1000 | APPROVE | 0.0015x |
| 2 | STANDARD_PLUS | 650-799 | APPROVE | 0.0022x |
| 3 | STANDARD | 500-649 | REFER | 0.0032x |
| 4 | SUBSTANDARD | 350-499 | REFER | 0.005x |
| 5 | DECLINE | 0-349 | DECLINE | 0.008x |

**Decision Logic:**
- Scores 0-1000 (composite from weighted signals)
- Higher scores = better risk = lower tier number
- APPROVE: Automatic binding eligible
- REFER: Requires underwriter review
- DECLINE: Outside risk appetite

### Loss Tier Bands

Loss tiers adjust premium based on expected loss frequency and severity:

| Tier | Label | Score Range | Freq Modifier | Sev Modifier |
|------|-------|-------------|---------------|--------------|
| 1 | VERY_LOW | 80-100 | 0.70x | 0.80x |
| 2 | LOW | 60-79 | 0.85x | 0.90x |
| 3 | MODERATE | 40-59 | 1.00x | 1.00x |
| 4 | ELEVATED | 20-39 | 1.15x | 1.15x |
| 5 | HIGH | 0-19 | 1.35x | 1.40x |

**Constraints:** Floor = 0.55, Cap = 1.60

### Direct Queries

Binary questions that cannot be inferred from external signals:

| Query ID | Question | Trigger | Action | Impact |
|----------|----------|---------|--------|--------|
| `psc_detentions` | Any vessels detained by port state control in past... | Answer = True | REFER | Override to Tier 3 |
| `total_losses` | Any total losses or major casualties in past 5 yea... | Answer = True | REFER | Override to Tier 4 |
| `third_party_manager` | Is the fleet managed by a third-party technical ma... | Answer = True | FLAG | Third-party technical management |
| `sanctioned_trade` | Any vessels currently trading to sanctioned region... | Answer = True | REFER | Override to Tier 5 |

**Action Types:**
- **FLAG:** Adds note to underwriter; no pricing impact
- **MODIFIER:** Applies premium multiplier
- **REFER:** Forces underwriter review regardless of score

### Limit & Deductible Configuration

**Type:** `DECOUPLED`

**Mode:** Tower Pricing (Independent Selection)

Clients independently select from valid limits and deductibles. 
Pricing scales via ILF curves and deductible factors.

**Available Limits:**

- $5,000,000
- $10,000,000
- $25,000,000
- $50,000,000
- $100,000,000
- $250,000,000
- $500,000,000
- $1,000,000,000

**Available Deductibles:**

- $10,000
- $25,000
- $50,000
- $100,000
- $250,000
- $500,000
- $1,000,000

### Pricing Structure

Pricing varies by product type:


#### Hull Machinery

**Pricing Anchors (V5):**
- Base Limit Reference: $10,000,000
- Base Deductible Reference: $50,000

**Increased Limit Factors (ILF):**

| Limit | Factor | Premium Multiplier |
|-------|--------|-------------------|
| $10,000,000 (base) | 1.00 | 1.00x base |
| $25,000,000 | 2.10 | 2.10x base |
| $50,000,000 | 3.80 | 3.80x base |
| $100,000,000 | 6.50 | 6.50x base |
| $250,000,000 | 13.00 | 13.00x base |
| $500,000,000 | 22.00 | 22.00x base |
| $1,000,000,000 | 38.00 | 38.00x base |

**Deductible Factors (V5):**

| Deductible | Factor | Effect |
|------------|--------|--------|
| $10,000 | 1.50 | +50% loading |
| $25,000 | 1.15 | +15% loading |
| $50,000 (anchor) | 1.00 | Base price |
| $100,000 | 0.95 | -5% credit |
| $250,000 | 0.90 | -10% credit |
| $500,000 | 0.70 | -30% credit |
| $1,000,000 | 0.70 | -30% credit |


#### Total Loss

**Pricing Anchors (V5):**
- Base Limit Reference: $10,000,000
- Base Deductible Reference: $50,000

**Increased Limit Factors (ILF):**

| Limit | Factor | Premium Multiplier |
|-------|--------|-------------------|
| $10,000,000 (base) | 1.00 | 1.00x base |
| $25,000,000 | 1.90 | 1.90x base |
| $50,000,000 | 3.30 | 3.30x base |
| $100,000,000 | 5.50 | 5.50x base |
| $250,000,000 | 10.50 | 10.50x base |
| $500,000,000 | 17.50 | 17.50x base |
| $1,000,000,000 | 30.00 | 30.00x base |

**Deductible Factors (V5):**

| Deductible | Factor | Effect |
|------------|--------|--------|
| $10,000 | 1.50 | +50% loading |
| $25,000 | 1.15 | +15% loading |
| $50,000 (anchor) | 1.00 | Base price |
| $100,000 | 0.96 | -4% credit |
| $250,000 | 0.92 | -8% credit |
| $500,000 | 0.70 | -30% credit |
| $1,000,000 | 0.70 | -30% credit |


#### Increased Value

**Pricing Anchors (V5):**
- Base Limit Reference: $5,000,000
- Base Deductible Reference: $50,000

**Increased Limit Factors (ILF):**

| Limit | Factor | Premium Multiplier |
|-------|--------|-------------------|
| $5,000,000 (base) | 1.00 | 1.00x base |
| $10,000,000 | 1.80 | 1.80x base |
| $25,000,000 | 3.60 | 3.60x base |
| $50,000,000 | 6.00 | 6.00x base |
| $100,000,000 | 10.50 | 10.50x base |
| $250,000,000 | 21.00 | 21.00x base |
| $500,000,000 | 36.00 | 36.00x base |

**Deductible Factors (V5):**

| Deductible | Factor | Effect |
|------------|--------|--------|
| $10,000 | 1.50 | +50% loading |
| $25,000 | 1.15 | +15% loading |
| $50,000 (anchor) | 1.00 | Base price |
| $100,000 | 0.95 | -5% credit |
| $250,000 | 0.90 | -10% credit |
| $500,000 | 0.70 | -30% credit |
| $1,000,000 | 0.70 | -30% credit |


#### Loss Of Hire

**Pricing Anchors (V5):**
- Base Limit Reference: $5,000,000
- Base Deductible Reference: $50,000

**Increased Limit Factors (ILF):**

| Limit | Factor | Premium Multiplier |
|-------|--------|-------------------|
| $5,000,000 (base) | 1.00 | 1.00x base |
| $10,000,000 | 1.95 | 1.95x base |
| $25,000,000 | 4.20 | 4.20x base |
| $50,000,000 | 7.20 | 7.20x base |
| $100,000,000 | 12.80 | 12.80x base |
| $250,000,000 | 26.00 | 26.00x base |
| $500,000,000 | 45.00 | 45.00x base |

**Deductible Factors (V5):**

| Deductible | Factor | Effect |
|------------|--------|--------|
| $10,000 | 1.50 | +50% loading |
| $25,000 | 1.15 | +15% loading |
| $50,000 (anchor) | 1.00 | Base price |
| $100,000 | 0.96 | -4% credit |
| $250,000 | 0.92 | -8% credit |
| $500,000 | 0.70 | -30% credit |
| $1,000,000 | 0.70 | -30% credit |


#### War Risks

**Pricing Anchors (V5):**
- Base Limit Reference: $10,000,000
- Base Deductible Reference: $50,000

**Increased Limit Factors (ILF):**

| Limit | Factor | Premium Multiplier |
|-------|--------|-------------------|
| $10,000,000 (base) | 1.00 | 1.00x base |
| $25,000,000 | 2.30 | 2.30x base |
| $50,000,000 | 4.40 | 4.40x base |
| $100,000,000 | 7.80 | 7.80x base |
| $250,000,000 | 16.00 | 16.00x base |
| $500,000,000 | 28.00 | 28.00x base |
| $1,000,000,000 | 50.00 | 50.00x base |

**Deductible Factors (V5):**

| Deductible | Factor | Effect |
|------------|--------|--------|
| $10,000 | 1.50 | +50% loading |
| $25,000 | 1.15 | +15% loading |
| $50,000 (anchor) | 1.00 | Base price |
| $100,000 | 0.97 | -3% credit |
| $250,000 | 0.94 | -6% credit |
| $500,000 | 0.70 | -30% credit |
| $1,000,000 | 0.70 | -30% credit |


#### Pi Liability

**Pricing Anchors (V5):**
- Base Limit Reference: $10,000,000
- Base Deductible Reference: $50,000

**Increased Limit Factors (ILF):**

| Limit | Factor | Premium Multiplier |
|-------|--------|-------------------|
| $10,000,000 (base) | 1.00 | 1.00x base |
| $25,000,000 | 2.20 | 2.20x base |
| $50,000,000 | 4.10 | 4.10x base |
| $100,000,000 | 7.20 | 7.20x base |
| $250,000,000 | 15.00 | 15.00x base |
| $500,000,000 | 26.00 | 26.00x base |
| $1,000,000,000 | 46.00 | 46.00x base |

**Deductible Factors (V5):**

| Deductible | Factor | Effect |
|------------|--------|--------|
| $10,000 | 1.50 | +50% loading |
| $25,000 | 1.15 | +15% loading |
| $50,000 (anchor) | 1.00 | Base price |
| $100,000 | 0.96 | -4% credit |
| $250,000 | 0.92 | -8% credit |
| $500,000 | 0.70 | -30% credit |
| $1,000,000 | 0.70 | -30% credit |


#### Cargo

**Pricing Anchors (V5):**
- Base Limit Reference: $5,000,000
- Base Deductible Reference: $50,000

**Increased Limit Factors (ILF):**

| Limit | Factor | Premium Multiplier |
|-------|--------|-------------------|
| $5,000,000 (base) | 1.00 | 1.00x base |
| $10,000,000 | 1.75 | 1.75x base |
| $25,000,000 | 3.50 | 3.50x base |
| $50,000,000 | 5.80 | 5.80x base |
| $100,000,000 | 10.00 | 10.00x base |
| $250,000,000 | 20.00 | 20.00x base |
| $500,000,000 | 34.00 | 34.00x base |

**Deductible Factors (V5):**

| Deductible | Factor | Effect |
|------------|--------|--------|
| $10,000 | 1.50 | +50% loading |
| $25,000 | 1.15 | +15% loading |
| $50,000 (anchor) | 1.00 | Base price |
| $100,000 | 0.95 | -5% credit |
| $250,000 | 0.90 | -10% credit |
| $500,000 | 0.70 | -30% credit |
| $1,000,000 | 0.70 | -30% credit |



---

## Decision Flow Summary

```
┌─────────────────────────────────────────────────────────────┐
│                    DSI Decision Flow                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. SIGNAL EXTRACTION                                       │
│     └─► External APIs → Normalized Scores (0-100)          │
│                                                             │
│  2. GROUP AGGREGATION                                       │
│     └─► Weighted combination within groups                  │
│                                                             │
│  3. THREE-LAYER ASSESSMENT                                  │
│     ├─► Risk Score (0-1000)                                │
│     ├─► Loss Score (frequency × severity)                  │
│     └─► Exposure Score (size × complexity)                 │
│                                                             │
│  4. TIER ASSIGNMENT                                         │
│     └─► Risk Score → Tier Band → Base Premium              │
│                                                             │
│  5. DIRECT QUERIES                                          │
│     └─► Binary answers → FLAGS / MODIFIERS / REFERS        │
│                                                             │
│  6. PRICING CALCULATION                                     │
│     └─► Base × ILF × Ded Factor × Modifiers × Tax          │
│                                                             │
│  7. DECISION OUTPUT                                         │
│     └─► APPROVE / REFER / DECLINE + Audit Trail            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

*Generated by DSI Coverage Documentation Generator*

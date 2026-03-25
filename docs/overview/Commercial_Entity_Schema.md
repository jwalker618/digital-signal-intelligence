# ${\color{blue}Digital\space Signal\space Intelligence\space (DSI)}$

## Commercial Entity Schema

| Item | Value |
|-|-|
|Version|1.0|
|Date|March 2026|
|Classification|Schema Reference|
|Schema Version|v2.3|

---

## 1. Overview

A **Commercial Entity** represents a distribution platform, syndicate, branch, or MGA that writes business using DSI's technical pricing engine. Each entity has its own economics (commission, taxes, distribution type) and writes a specific set of coverages with entity-scoped appetite constraints.

Entity definitions live in `commercial/entities/{entity_id}.yaml` and are loaded by the `load_entity()` / `load_all_entities()` functions in `infrastructure/models/commercial_schema.py`.

### Why Entities?

The DSI pricing engine produces a **technical premium in USD** — a currency-neutral, entity-agnostic price derived from signals and actuarial models. However, the same technical premium is offered to the market differently depending on *who* is writing the business:

- A **US MGA** offers bundled SME packages with 15% brokerage and US state taxes.
- A **Lloyd's syndicate** takes a 10% signed line on a £500M energy programme with 20% brokerage and UK IPT.
- An **EU fronted program** cedes 100% to the risk carrier through an Allianz SE fronting arrangement with German IPT.

The entity schema captures these differences in a single, declarative YAML file.

---

## 2. File Structure

Each entity is a standalone YAML file:

```
commercial/
  entities/
    mga_us_cyber.yaml          # BUNDLED — US MGA, cyber + D&O
    syndicate_example.yaml     # SUBSCRIPTION/FOLLOW — Lloyd's energy/marine/aerospace
    syndicate_lead.yaml        # SUBSCRIPTION/LEAD — Lloyd's lead underwriter
    tower_us_energy.yaml       # TOWER — US E&S layered energy program
    direct_fi_pi.yaml          # DIRECT — US direct writer, FI + PI
    eu_fronted.yaml            # FRONTED — EU cross-border cyber/D&O/PI
```

---

## 3. Schema Reference

### 3.1 Root Structure

```yaml
entity:
  id: mga_us_cyber              # Unique identifier (snake_case)
  name: "US Cyber MGA"          # Display name
  market: us                    # Market: us, lloyds, eu, apac
  base_currency: USD            # Operating currency (ISO 4217)

  coverages: [...]              # What this entity writes (§3.2)
  distribution: {...}           # How limits are distributed (§3.3)
  commission: {...}             # Commission structure (§3.4)
  taxes_and_levies: {...}       # Tax and regulatory charges (§3.5)
  fronting: {...}               # Fronting arrangement (§3.6)
  pricing_adjustments: {...}    # Offered premium controls (§3.7)
```

| Field | Type | Required | Description |
|-|-|-|-|
| `id` | string | Yes | Unique entity identifier, used as cache key and foreign key |
| `name` | string | Yes | Human-readable display name |
| `market` | string | No | Market identifier: `us`, `lloyds`, `eu`, `apac` |
| `base_currency` | string | Yes | ISO 4217 currency code. Technical premium (USD) is converted to this currency. |

---

### 3.2 Coverages (Appetite)

The `coverages` array declares which coverage lines and configs the entity writes, along with appetite constraints.

```yaml
coverages:
  - coverage: cyber
    configs:
      - cyber_general
      - cyber_sme
    max_single_limit: 25_000_000
    constraints:
      - field: revenue
        operator: "<="
        value: 10_000_000_000
        reason: "Revenue exceeds MGA cyber binding authority"
```

| Field | Type | Required | Description |
|-|-|-|-|
| `coverage` | string | Yes | Coverage line identifier (e.g., `cyber`, `energy`, `marine`) |
| `configs` | list[string] | No | Specific configs within the coverage this entity writes. Empty = all configs. |
| `max_single_limit` | integer | No | Maximum limit per risk for this coverage |
| `max_aggregate_limit` | integer | No | Maximum aggregate across all limits. `null` = no cap. |
| `constraints` | list[Constraint] | No | Field-level appetite constraints |

#### Constraint Object

| Field | Type | Description |
|-|-|-|
| `field` | string | Submission field to evaluate: `revenue`, `tiv`, `hull_value`, `total_assets` |
| `operator` | string | Comparison: `<=`, `>=`, `<`, `>`, `==`, `!=`, `in`, `not_in` |
| `value` | any | Threshold value |
| `reason` | string | Human-readable decline reason shown to the underwriter |

#### How Appetite is Evaluated

When `evaluate_appetite(coverage, submission_data, entity)` is called:

1. Find the `CoverageBinding` matching the requested coverage.
2. If the entity does not write this coverage → **decline**.
3. Check `max_single_limit` against the submission's requested limit.
4. Check `max_aggregate_limit` against aggregate exposure.
5. Evaluate each constraint against the submission data field.
6. If any check fails → **decline** with collected reasons.

---

### 3.3 Distribution

The `distribution` block defines how the entity distributes limits to the market. This is separate from the coverage config's `limit_configuration` (BUNDLED/DECOUPLED), which defines what limit/deductible options exist — distribution defines how they are offered.

```yaml
distribution:
  type: SUBSCRIPTION       # BUNDLED | SUBSCRIPTION | TOWER | DIRECT
```

#### Type: BUNDLED

Pre-packaged limit/deductible combinations for SME markets.

```yaml
distribution:
  type: BUNDLED
  bundled:
    packages:
      - id: 1
        label: STARTER
        limit: 250_000
        deductible: 1_000
      - id: 2
        label: STANDARD
        limit: 1_000_000
        deductible: 5_000
  decoupled:               # Optional fallback for mid-market
    min_limit: 250_000
    max_limit: 25_000_000
    min_deductible: 1_000
    max_deductible: 500_000
```

#### Type: SUBSCRIPTION

London/Lloyd's subscription market. The entity takes a percentage line on a larger programme.

```yaml
distribution:
  type: SUBSCRIPTION
  subscription:
    minimum_line: 0.05         # Minimum signed line (5%)
    maximum_line: 0.25         # Maximum signed line (25%)
    default_signed_line: 0.10  # Default if not specified (10%)
    role: FOLLOW               # LEAD or FOLLOW
    lead_loading_factor: 1.0   # 1.0 for followers, >1.0 for leads
```

| Field | Description |
|-|-|
| `minimum_line` | Floor for the entity's participation |
| `maximum_line` | Ceiling for the entity's participation |
| `default_signed_line` | Used when no specific line is negotiated |
| `role` | `LEAD` — sets the price, takes larger line; `FOLLOW` — accepts the lead's terms |
| `lead_loading_factor` | Multiplier on technical premium for leads (e.g., 1.10 = 10% lead loading) |

**Lead vs Follow:** The lead underwriter sets the terms and pricing for the programme. Their premium includes a loading factor to compensate for the underwriting work. Followers accept the lead's terms at par (`lead_loading_factor: 1.0`).

#### Type: TOWER

Layered excess-of-loss structure. Each layer has an attachment point and limit expressed as percentages of the total programme.

```yaml
distribution:
  type: TOWER
  tower:
    layer_templates:
      - id: 1
        label: "Primary"
        attachment_pct: 0.0
        limit_pct: 0.10          # First 10%
      - id: 2
        label: "1st Excess"
        attachment_pct: 0.10
        limit_pct: 0.20          # 10% to 30%
      - id: 3
        label: "2nd Excess"
        attachment_pct: 0.30
        limit_pct: 0.30          # 30% to 60%
      - id: 4
        label: "3rd Excess"
        attachment_pct: 0.60
        limit_pct: 0.40          # 60% to 100%
    subscription:                # Subscription overlay per layer
      minimum_line: 0.05
      maximum_line: 0.25
      default_signed_line: 0.10
      role: FOLLOW
      lead_loading_factor: 1.0
```

Tower programs often include a subscription overlay — each layer is itself a subscription programme with multiple participants.

#### Type: DIRECT

100% ground-up writer. No subscription or tower structure.

```yaml
distribution:
  type: DIRECT
```

No additional configuration required. The entity retains the full premium.

---

### 3.4 Commission

```yaml
commission:
  brokerage_rate: 0.20                # 20% brokerage
  overrider_rate: 0.025               # 2.5% overrider
  profit_commission_rate: 0.15        # 15% profit commission
  profit_commission_threshold: 0.70   # Triggers below 70% loss ratio
```

| Field | Type | Description |
|-|-|-|
| `brokerage_rate` | float | Standard brokerage deducted from gross premium |
| `overrider_rate` | float | Additional broker compensation (volume incentive) |
| `profit_commission_rate` | float | Share of underwriting profit returned to broker |
| `profit_commission_threshold` | float | Loss ratio below which profit commission applies |

**Calculation:**

$$P_{net} = P_{gross} \times (1 - brokerage - overrider)$$

Profit commission is a post-period calculation based on actual loss experience and is not deducted from the initial premium.

---

### 3.5 Taxes and Levies

```yaml
taxes_and_levies:
  insurance_premium_tax_rate: 0.12   # UK IPT 12%
  stamp_duty_rate: 0.0               # Not applicable
  regulatory_levy_rate: 0.01         # Lloyd's central fund
```

| Field | Type | Description |
|-|-|-|
| `insurance_premium_tax_rate` | float | Jurisdiction-specific IPT (e.g., 12% UK, 19% Germany, 3% US avg) |
| `stamp_duty_rate` | float | Stamp duty where applicable |
| `regulatory_levy_rate` | float | Market-specific regulatory charges (e.g., Lloyd's central fund) |

These are applied additively to the net premium:

$$P_{gross} = P_{net} \times (1 + IPT + stamp + levy)$$

---

### 3.6 Fronting

```yaml
fronting:
  enabled: true
  fronting_fee_rate: 0.05
  fronting_carrier: "Allianz SE"
```

| Field | Type | Description |
|-|-|-|
| `enabled` | boolean | Whether this is a fronted arrangement |
| `fronting_fee_rate` | float | Fee charged by the fronting carrier (e.g., 5%) |
| `fronting_carrier` | string | Name of the fronting carrier |

**Context:** Post-Solvency II, US/UK carriers writing EU-domiciled risks typically need a locally-licensed carrier to issue the policy. The fronting carrier issues the paper and cedes 100% of the risk to the actual risk carrier, charging a fee for the service.

---

### 3.7 Pricing Adjustments

```yaml
pricing_adjustments:
  offered_premium_discretion: 0.10   # ±10% underwriter discretion
  minimum_gross_premium: 7500        # £7,500 minimum
```

| Field | Type | Description |
|-|-|-|
| `offered_premium_discretion` | float | Maximum ±% the underwriter can adjust the gross premium |
| `minimum_gross_premium` | float | Floor premium in the entity's base currency |

**Offered Premium Discretion** is the only subjective adjustment permitted in the DSI pipeline. It operates on the *output* of the mathematical model (the gross premium), not on the inputs (signals, modifiers, rates). This preserves the signal-to-loss-ratio correlation required for model training.

---

## 4. Entity Inventory

| Entity ID | Distribution | Market | Currency | Coverages | Key Characteristic |
|-|-|-|-|-|-|
| `mga_us_cyber` | BUNDLED | US | USD | Cyber, D&O | SME packages, 15% brokerage |
| `syndicate_example` | SUBSCRIPTION/FOLLOW | Lloyd's | GBP | Energy, Marine, Aerospace | 10% signed line, 20% brokerage |
| `syndicate_lead` | SUBSCRIPTION/LEAD | Lloyd's | GBP | Energy, Marine, Aerospace | 20% signed line, 1.10x lead loading |
| `tower_us_energy` | TOWER | US | USD | Energy | 4-layer excess-of-loss, subscription overlay |
| `direct_fi_pi` | DIRECT | US | USD | FI, PI | 100% ground-up writer, 12.5% brokerage |
| `eu_fronted` | FRONTED | EU | EUR | Cyber, D&O, PI | Allianz SE fronting, 19% German IPT |

---

## 5. Premium Assembly

The `PremiumAssembler` uses the entity definition to transform a technical premium into a commercial premium. The full pipeline is documented in [Premium Calculation Methodology §8](Premium_Calculation_Methodology.md#8-premium-assembly-pipeline).

### Assembly Signature

```python
assembler = PremiumAssembler(fx_converter)
breakdown = assembler.assemble(
    technical_premium_usd=42_500.00,
    submission_data=submission,
    config=config,
    entity=entity,
)
```

### Output: PremiumBreakdown

The `PremiumBreakdown` contains a full audit trail:

| Field | Description |
|-|-|
| `technical_premium_usd` | Input from the pricing engine |
| `technical_premium_local` | After FX conversion |
| `fx_rate` | USD → local rate used |
| `distribution_type` | Entity's distribution type |
| `signed_line` | For SUBSCRIPTION — the entity's participation |
| `line_premium` | Premium for the entity's share |
| `brokerage` | Brokerage deduction amount |
| `overrider` | Overrider deduction amount |
| `net_premium` | After commission deductions |
| `taxes` | IPT + stamp + levy amounts |
| `fronting_fee` | If fronting enabled |
| `gross_premium` | Total payable |
| `offered_premium` | After underwriter discretion |
| `at_minimum_premium` | Whether floor was applied |

---

## 6. Data Model

Entity data flows into two database records:

### CommercialTermsRecord

Captures the full premium assembly for a given pricing run. Stored in the `commercial_terms` table with fields for entity identification, FX context, distribution structure, commission deductions, taxes, gross and offered premium, and audit timestamps.

### RiskTermsRecord

Captures deductible and coverage nuance for reporting. Linked to `CommercialTermsRecord` via foreign key. Includes deductible type/basis, SIR provisions, waiting periods, aggregate limits, reinstatement terms, attachment points, sub-limits, and coverage extensions/exclusions.

These records are created during the seed process and the pricing workflow, providing a complete audit trail from technical premium to offered premium for every priced submission.

---

## 7. Relationship to Other Components

```
┌──────────────────────────┐
│  Coverage Config          │  What limits/deductibles exist
│  (config.yaml)            │  ILF curves, deductible factors
└──────────┬───────────────┘
           │ pricing parameters
           ▼
┌──────────────────────────┐
│  Pricing Engine           │  Computes technical premium (USD)
│  (workflow.py)            │  Signals → Tier → Base → Scale → Modify
└──────────┬───────────────┘
           │ technical_premium_usd
           ▼
┌──────────────────────────┐
│  Commercial Entity        │  How the premium is offered
│  (entities/*.yaml)        │  Distribution, commission, taxes, FX
└──────────┬───────────────┘
           │ entity terms
           ▼
┌──────────────────────────┐
│  Premium Assembler        │  Transforms technical → gross → offered
│  (premium_assembly.py)    │  FX, distribution, commission, taxes
└──────────┬───────────────┘
           │ PremiumBreakdown
           ▼
┌──────────────────────────┐
│  Database Records         │  CommercialTermsRecord
│  (models.py)              │  RiskTermsRecord
└──────────────────────────┘
```

The key architectural principle is: **the pricing engine knows nothing about commercial terms.** It produces a technical premium in USD. The entity schema and premium assembler handle everything downstream — currency, distribution, commission, taxes, and the final offered premium.

# Phase 5: Advanced Pricing Architecture (Anchors & Towers)

## Context
The current pricing architecture relies on implicit assumptions about the relationship between "Base Premium" and coverage limits. It also rigidly couples limits to deductibles (Menu Pricing).
- **Ambiguity:** If a Base Rate is 0.10%, the system does not explicitly know if that buys a $1M limit or a $5M limit.
- **Rigidity:** Corporate clients cannot select a $10M Limit with a $250k Deductible if that specific combination isn't pre-defined in a list.

## Purpose
To implement a **Polymorphic Pricing Engine** that supports two distinct behaviors:
1.  **Bundled (Menu) Pricing:** For SME/Micro (Fixed Packages).
2.  **Decoupled (Tower) Pricing:** For Corporate/Enterprise (Independent Limits & Deductibles).

Crucially, this phase introduces **Pricing Anchors**—explicit reference points that normalize the "Base Rate" or "Base Premium" to a specific unit of coverage, enabling accurate mathematical scaling.

## Key Deliverables
1.  **Schema Polymorphism:** Support for both `limit_bandings` (List) and `limit_configuration` (Rules).
2.  **Anchor Logic:** New fields `base_limit_reference` and `base_deductible_reference` to normalize inputs.
3.  **Math Engine Update:** Refactor `calculate_premium` to handle ILF and Deductible scaling relative to the Anchor.

## Detailed Plan

### 5.1 Schema Updates

#### A. The Pricing Anchor
We introduce specific reference points in the `pricing` block. This tells the math engine what the "Risk Tier Price" actually buys.

```yaml
pricing:
  base_limit_reference: 1000000       # The Base Price buys $1M Limit
  base_deductible_reference: 50000    # The Base Price assumes $50k Deductible
```

#### B. Limit Configuration Types
The limit_bandings section is upgraded to support two modes:

Mode 1: BUNDLED (Legacy/SME) Existing behavior. Fixed list of ID-based packages.

```yaml
limit_bandings:
  - id: 1
    limit: 1000000
    deductible: 5000
```

Mode 2: DECOUPLED (New/Corp) New behavior. Valid sets for independent selection.

```yaml
limit_configuration:
  type: "DECOUPLED"
  valid_limits: [1000000, 5000000, 10000000]
  valid_deductibles: [25000, 50000, 100000]
```

### 5.2 Mathematical LogicThe premium calculation formula changes to explicit relativity:


### 5.3 Implementation Tasks

|Category|Task|File|
|-|-|-|
|Schema|Add base_limit_reference to master layout|master_config_layout.yaml|
|Schema|Define limit_configuration structure|master_config_layout.yaml|
|Engine|Implement PricingEngine.calculate_ilf_factor using Anchor|engine/pricing.py|
|Engine|Implement PricingEngine.calculate_deductible_factor|engine/pricing.py|
|Validation|Ensure base_limit_reference exists in ILF curve keys|validators/schema.py|

## Integration Notes
1. Backward Compatibility: If limit_bandings is present, the engine defaults to BUNDLED mode.
2. Data Validation: The Anchor Limit MUST exist as a key in the ilf_curve. The Anchor Deductible MUST exist in deductible_factors (with factor 1.0).

# Phase R3: Coverage Configuration Rebuilds

**Status:** ✅ Complete
**Parent Plan:** `dsi_restructure_plan.md`

## Objective

Rebuild all 7 coverage configurations to the v2.0 schema, ensuring structural consistency and cross-coverage validation.

## Deliverables

- All 7 configs rebuilt: aerospace, cyber, D&O, energy, FI, marine, PI
- `signal_registry` with `three_layer_assessment` (risk/loss/exposure) per signal
- `groups` section with `categories` and `three_layer_assessment` sub-sections
- `risk_tier_bands` with `interpretation` blocks (0-1000 scale)
- `loss_tier_bands` with frequency/severity modifiers and constraints
- Nested `exposure: { size, complexity }` with implied thresholds
- Cross-coverage structural validation passed (all 7 configs consistent)
- 21 inference function name typos corrected

## Key Files

- `coverages/aerospace/config.yaml` — 21 signals
- `coverages/cyber/config.yaml` — Reference implementation
- `coverages/do/config.yaml` — Directors & Officers
- `coverages/energy/config.yaml` — Energy
- `coverages/fi/config.yaml` — Financial Institutions
- `coverages/marine/config.yaml` — Marine
- `coverages/pi/config.yaml` — Professional Indemnity

# Calibration & Guardrails Integration Plan

## Problem
The `development/dsi_calibration.py` and `development/dsi_guardrails.py` files contain sound concepts (modifier clamping, premium-vs-limit caps, premium-vs-revenue caps, grid-based calibration testing) but exist as standalone proof-of-concepts disconnected from the actual pipeline.

The DSI pricing engine is multiplicative. Without guardrails enforced at runtime and calibration validated at CI time, miscalibrated configs silently produce absurd premiums.

## Approach: Two distinct integrations

### 1. Runtime Guardrails — into the pricer and config schema

**Where:** `infrastructure/models/config_schema.py` + `layers/risk/pricer.py` + each `coverages/*/config.yaml`

**What:**
- Add a `Guardrails` Pydantic model to `config_schema.py` with:
  - `modifier_floor` (float, default 0.50) — minimum allowed total modifier
  - `modifier_cap` (float, default 2.50) — maximum allowed total modifier
  - `max_premium_to_limit_ratio` (float, default 0.35) — premium cannot exceed 35% of limit
  - `max_premium_to_revenue_ratio` (float, default 0.01) — premium cannot exceed 1% of revenue
  - `max_base_premium_to_revenue_ratio` (float, default 0.005) — base premium (pre-ILF) sanity check
- Add `guardrails: Optional[Guardrails]` field to `CoverageConfig`
- Add each coverage config's guardrail section to their YAML
- In `ModelPricer.apply_modifiers()`: clamp `total_modifier` between floor and cap
- In `ModelPricer.price_submission()` after final premium calculation: evaluate premium-vs-limit and premium-vs-revenue checks, attach warnings to `PricingResult`
- Add `guardrail_warnings: List[str]` field to `PricingResult`

This is the safety net — it caps outputs even if configs are miscalibrated.

### 2. Calibration Validation — as a pytest test suite

**Where:** `tests/unit/test_calibration.py`

**What:**
A test suite that loads compiled configs and runs representative pricing scenarios through the pricer, asserting that premiums fall within expected market ranges. This runs in CI and catches config miscalibration before deployment.

Test scenarios per coverage:
- Small company (e.g., $10M revenue, $1M limit) → assert premium in range [$X, $Y]
- Mid-market (e.g., $500M revenue, $10M limit) → assert premium in range
- Enterprise (e.g., $50B revenue, $25M limit) → assert premium in range
- Stress test: maximum modifier stack at highest tier → assert guardrails contain it

This replaces the grid-generation approach in `dsi_calibration.py` with real config + real pricer execution, validated automatically.

### 3. Remove development/ proof-of-concept files

Once the logic is integrated, delete:
- `development/dsi_calibration.py`
- `development/dsi_guardrails.py`
- `development/dsi_calibration_guardrails.md`

Their purpose was to define the concepts. The concepts now live in production code and tests.

## What this does NOT change
- The pricing methodology (steps 8-12) remains unchanged
- ILF curves, deductible factors, tier bands — structure is untouched
- Signal scoring, tier overrides — unchanged
- The seed script — not modified (it consumes configs; fixing configs fixes its output)

## Order of execution
1. Add `Guardrails` to config schema
2. Add guardrail sections to coverage YAML configs
3. Integrate guardrails into pricer (modifier clamping + premium caps)
4. Add `guardrail_warnings` to `PricingResult`
5. Write calibration test suite
6. Remove development/ files
7. Run existing tests to confirm no regressions

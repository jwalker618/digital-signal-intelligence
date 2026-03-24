# DSI Coverage Builder

## Overview

The Coverage Builder provides two generation pipelines:

1. **`build`** — Create an entirely new coverage line from a `CoverageSpec` (name, industry, market). Generates a single `_general` configuration with signal selection and weighting.

2. **`expand`** — Expand an existing coverage line with multiple segment-specific sub-configurations from a structured `ExpansionSpec`. Generates complete config YAML, extractor stubs, aggregator stubs, and inference function registrations.

**Use `build` when**: Creating a new coverage line from scratch (e.g., "create a new Casualty coverage").

**Use `expand` when**: Adding multiple sub-configurations to an existing coverage line (e.g., Phase 6 — expanding PI from 2 configs to 13 profession-specific configs). This is the standard workflow for coverage expansion phases.

Generated configs are immediately usable by the DSI scoring engine, pricing engine, and workflow orchestrator without manual editing.

## Quick Start

### Expand an Existing Coverage (Coverage Expansion Phases)

```bash
# Preview what will be generated (no files written)
python -m infrastructure.builder.cli expand \
    --spec development/project/version/4/phase_6_spec.yaml

# Generate and write all files
python -m infrastructure.builder.cli expand \
    --spec development/project/version/4/phase_6_spec.yaml \
    --existing-config coverages/pi/config.yaml \
    --write

# Dry run with JSON output
python -m infrastructure.builder.cli expand \
    --spec development/project/version/4/phase_6_spec.yaml \
    --dry-run --json
```

This generates:
- Config YAML sub-configurations (appended to existing config.yaml)
- Extractor stubs (`signal_architecture/signals/extractors/stubs/{coverage}/`)
- Aggregator stubs (`signal_architecture/signals/aggregators/implementations/{coverage}/`)
- Inference function registrations (`signal_architecture/signals/inference/functions/{coverage}/`)

### Build a New Coverage

```bash
# Generate a Cyber coverage for the Japanese market
python -m infrastructure.builder.cli build \
    --name "Cyber Japan" \
    --industry technology \
    --description "Cyber liability model for the Japanese market" \
    --market jp \
    --strategy conservative \
    --write

# Generate a Casualty coverage
python -m infrastructure.builder.cli build \
    --name "Casualty" \
    --industry manufacturing \
    --description "General casualty coverage for US market" \
    --write
```

### Validate an Existing Config

```bash
# Validate any coverage config against v2.0 schema
python -m infrastructure.builder.cli validate coverages/cyber/config.yaml

# JSON output for tooling
python -m infrastructure.builder.cli validate coverages/cyber/config.yaml --json
```

### List Available Options

```bash
# See supported industries
python -m infrastructure.builder.cli list-industries

# See available signal groups
python -m infrastructure.builder.cli list-signals
```

## How Coverage Expansions Work

### Overview

Coverage expansion is the standard workflow for phases that add multiple sub-configurations to an existing coverage line (e.g., Phase 5 energy, Phase 6 PI, Phase 7 cyber). The pipeline takes a structured YAML expansion spec and generates all required config YAML and signal architecture code.

### Step 1: Author the Expansion Spec

Create a `phase_N_spec.yaml` file. The spec captures all machine-consumable parameters in a compact format. See `development/project/version/4/phase_6_spec.yaml` as a reference (~1,500 lines for 11 configs + 58 signals).

```yaml
coverage_line: pi
coverage_key: professional_indemnity
phase: phase_6
description: "Phase 6 PI Expansion"
version: "2.3.0"

default_product_types: [professional_liability, errors_omissions]
default_markets: [us, uk, eu, apac]
routing_field: profession_segment

new_signal_groups:
  - id: partner_practice_mix
    label: Partner Practice Mix
    description: "Tail-risk drivers for large legal practice"
    group_type: three_layer_assessment
    signals:
      - id: lateral_hire_volume
        name: Lateral Hire Volume
        description: "Rate of lateral partner additions"
        group_id: partner_practice_mix
        proxy_tier: INFERRED_PROXY
        three_layer:
          risk_weight: 0.15
          loss_frequency_weight: 0.15
          exposure_size_weight: 0.15

configurations:
  - id: pi_legal_large
    name: DSI PI Large Law Firm Pricing Model
    description: "AmLaw 200, Magic Circle"
    model_specificity: 4
    min_premium: 100000
    routing_constraints:
      - {field: profession_segment, operator: "==", value: LEGAL, required_in_input: true}
      - {field: revenue, operator: ">", value: 100000000, required_in_input: true}
    direct_queries:
      - id: pending_claims
        question: Any pending or threatened malpractice claims?
        conditions: [{action: REFER, override: 4, note: Pending malpractice claims}]
    group_weights:
      - {group_id: regulatory_standing, risk_weight: 0.20, loss_weight: 0.20, exposure_weight: 0.10}
      - {group_id: partner_practice_mix, risk_weight: 0.10, loss_weight: 0.10, exposure_weight: 0.25}
    risk_tier_bands:
      method: MULTIPLIER
      basis: revenue
      preferred_rate: 0.0012
      standard_rate: 0.0028
      decline_rate: 0.0065
```

### Step 2: Run the Generator

```bash
python -m infrastructure.builder.cli expand \
    --spec development/project/version/4/phase_6_spec.yaml \
    --existing-config coverages/pi/config.yaml \
    --write
```

### Step 3: Review, Validate, and Calibrate

```bash
# Validate the generated config
python -m infrastructure.builder.cli validate coverages/pi/config.yaml

# Run calibration harness (automatically runs after --write, but can be run manually)
python -m infrastructure.builder.cli calibrate pi

# Regenerate logic.md documentation
python coverages/doc_generator.py

# Run project assessment
python development/project/assessments/scripts/assess_project.py
```

> **Note:** The calibration harness runs automatically when using `expand --write` or `build --write`. If calibration fails, adjust the config's `max_premium_to_limit_ratio` or `basis_damping` values and re-run until the guardrail hit rate is below 15%.

### Step 4: Register New Modules

Update the `__init__.py` files in the extractor, aggregator, and inference function directories to import and export the new phase modules.

### Expansion Spec Schema Reference

| Section | Description |
|---------|-------------|
| `coverage_line` | Coverage directory name (e.g., `pi`, `energy`, `cyber`) |
| `coverage_key` | Top-level YAML key (e.g., `professional_indemnity`, `energy`) |
| `default_*` | Shared defaults (product_types, markets, pricing, tier bands) |
| `routing_field` | Pre-routing field name (e.g., `profession_segment`) |
| `new_signal_groups` | New groups with their signals (three_layer or categorical) |
| `configurations` | Per-config: routing, weights, queries, pricing, tier bands |

Each signal in `new_signal_groups` supports:
- `signal_type: three_layer` — Scored signal with risk/loss/exposure weights
- `signal_type: categorical` — Category signal with modifier features
- `proxy_tier` — DIRECT_OBSERVABLE, INFERRED_PROXY, or COHORT_INFERENCE
- `score_conditions` — Threshold-based actions (FLAG/MODIFIER/REFER)
- `extractor_fields` — Field hints for stub generation

### Companion Documentation

For each expansion phase, create a light prose companion doc alongside the spec. Template: `development/project/templates/expansion_companion.md`. The companion provides strategic rationale, design decisions, and pricing philosophy — context that doesn't belong in a machine-consumable spec.

---

## How New Coverages Are Created

### Step 1: Define the Coverage Specification

A `CoverageSpec` describes what you want to build:

```python
from infrastructure.builder.types import CoverageSpec

spec = CoverageSpec(
    name="Cyber Japan",                          # Coverage name
    description="Cyber liability for Japan",     # Description
    industry="technology",                       # Industry profile to use
    target_market="Japan mid-market",            # Target market description
    product_types=["cyber_liability"],           # Product type identifiers
    applicable_markets=["jp"],                   # ISO market codes
    tier_strategy="conservative",                # standard | conservative | aggressive
    min_signals=15,                              # Minimum signal count
    max_signals=40,                              # Maximum signal count
    min_premium=5000,                            # Minimum premium (USD)
    default_currency="USD",                      # Currency
)
```

**Available industries**: `technology`, `financial_services`, `healthcare`, `manufacturing`, `retail`. Unknown industries fall back to a generic signal set.

**Tier strategies**:
- `standard` — balanced risk/reward thresholds
- `conservative` — wider DECLINE band, higher premiums
- `aggressive` — narrower DECLINE band, lower premiums

### Step 2: Run the Builder

```python
import asyncio
from infrastructure.builder.coverage_builder import CoverageBuilder

builder = CoverageBuilder()
result = asyncio.run(builder.create_coverage(spec))

if result.success:
    print(result.config_yaml)       # The generated YAML
    print(result.config_path)       # Where to save it
    print(result.generated_files)   # Code stubs created
else:
    print(result.warnings)
    print(result.human_review_required)
```

### Step 3: Review the Output

The builder generates a complete v2.0 config with this structure:

```yaml
cyber_japan:                          # coverage_id (snake_case of name)
  cyber_japan_general:                # coverage_id + "_general"
    metadata:                         # Product metadata
      name: "DSI Cyber Japan Technical Pricing Model"
      version: "2.0.0"
      minimum_viable_input: [...]
    direct_queries:                   # Binary questions (max 10)
      - id: "claims_history"
        question: "Has the insured had any claims in the past 5 years?"
        query_condition:              # NOT "bands" — v2.0 uses query_condition
          - return: true
            action: "REFER"
            note: "Prior claims - review required"
    signal_registry:                  # All signals defined here once
      - id: "security_headers"
        inference_utility_function: "security_headers_basefunction"
        proxy_tier: "DIRECT_OBSERVABLE"
        three_layer_assessment:       # Risk/Loss/Exposure dimensions
          group_id: "technical_infrastructure"
          risk:
            correlation_direction: "positive"
            weight: 0.0357
          loss:
            frequency: { correlation_direction: "negative", weight: 0.025 }
            severity: { correlation_direction: "negative", weight: 0.0107 }
    groups:
      categories:                     # Categorical modifier groups
        - id: "industry_classification"
          impact: "MODIFIER"
      three_layer_assessment:         # Scoring dimension groups
        - id: "technical_infrastructure"
          risk: { weight: 0.25 }
          loss: { weight: 0.25 }
          exposure: { weight: 0.25 }
    risk_tier_bands:                  # 0-1000 composite risk scale
      bands:
        - id: 1
          label: "PREFERRED"
          interpretation:
            bands: { min: 800, max: 1000 }
            action: "APPROVE"
            application: { method: "PREMIUM_BASE", applied: 8000 }
        - id: 5
          label: "DECLINE"
          interpretation:
            bands: { min: 0, max: 349 }
            action: "DECLINE"           # DECLINE is tier-level ONLY
            application: { method: "PREMIUM_BASE", applied: 50000 }
    loss_tier_bands:                  # 0-100 loss score scale
      bands:
        - id: 1
          label: "VERY_LOW"
          interpretation:
            bands: { min: 80, max: 100 }
            application:
              frequency_modifier: 0.70
              severity_modifier: 0.80
      constraints:
        floor: 0.55
        cap: 1.60
    exposure:                         # Nested size + complexity
      size:
        weight: 0.60
        bands:
          - id: 1
            label: "MICRO"
            interpretation:
              bands: { min: 0, max: 20 }
              application:
                method: "MODIFIER"
                applied: 0.50
                implied_thresholds: { min: 0, max: 1000000 }
      complexity:
        weight: 0.40
        bands: [...]
    limit_bandings:                   # Standard limit/deductible combos
      - { id: 1, limit: 1000000, deductible: 25000 }
    pricing:                          # ILF curve + deductible credits
      ilf_curve:
        base_limit: 1000000
        factors: [...]
      deductible_credits: [...]
      taxes_fees_rate: 0.05
```

### Step 4: Place the Config

Save the generated config to the coverages directory:

```
coverages/
  cyber_japan/
    config.yaml          ← generated config
```

The workflow engine will discover it via `config_manager.py` when `run_assessment(coverage="cyber_japan", ...)` is called.

### Step 5: Implement Signal Extractors

The builder generates extractor and aggregator stubs for signals that don't yet have implementations. These go into the signal architecture:

```
signals/
  cyber_japan/
    extractors.py        ← stub: implement API calls here
    aggregators.py       ← stub: implement score normalization
tests/
  unit/
    test_cyber_japan.py  ← stub: implement tests
```

Each extractor must return a score (0-100) or category value that feeds the `inference_utility_function` referenced in the config.

## v2.0 Schema Rules

These rules are **enforced by the validator** and must not be violated:

### Score Conditions

```
score_conditions actions: FLAG | MODIFIER | REFER
```

- **`DECLINE` is NEVER a score_condition action** — it is tier-level only (in `risk_tier_bands`)
- Score conditions are always **banded** (a list of multiple conditions)
- Score conditions apply to `signal_registry` signals and `groups` — NOT to tier bands

### Structure

- Config nesting: `coverage_id → coverage_id_general → {sections}`
- Signals defined **once** in `signal_registry` with `group_id` reference
- Groups define both `categories` (modifiers) and `three_layer_assessment` (scoring)
- Use `query_condition` (not `bands`) for direct queries

### Scales

| Dimension | Scale | Description |
|-----------|-------|-------------|
| Risk (composite) | 0-1000 | Weighted sum × 10, mapped to risk_tier_bands |
| Loss | 0-100 | Mapped to loss_tier_bands |
| Exposure (size) | 0-100 | Mapped to exposure.size.bands |
| Exposure (complexity) | 0-100 | Mapped to exposure.complexity.bands |

### Weights

- Signal weights within a group must sum to ~1.0
- Group weights across `three_layer_assessment` must sum to ~1.0
- `exposure.size.weight` + `exposure.complexity.weight` must sum to 1.0

## Extending an Existing Coverage

To create a variant of an existing coverage (e.g., Cyber for Japan based on the US Cyber model):

1. Use `base_coverage` in the spec:
   ```python
   spec = CoverageSpec(
       name="Cyber Japan",
       base_coverage="cyber",     # Start from existing cyber config
       ...
   )
   ```

2. The builder will use the same signal groups but allow market-specific adjustments to:
   - Direct queries (locale-specific regulatory questions)
   - Tier strategy (conservative/aggressive for different markets)
   - Pricing (market-appropriate ILF curves and premiums)

## Programmatic API

### CoverageBuilder Methods

| Method | Description |
|--------|-------------|
| `create_coverage(spec)` | Full build pipeline: analyze → select → generate → validate → stubs |
| `analyze_industry(description, examples)` | Identify risk factors and signal groups for an industry |
| `select_signals(analysis, spec)` | Select and weight signals based on analysis |
| `generate_config(spec, selections)` | Generate v2.0 YAML from selections |
| `validate_config(yaml_string)` | Validate against v2.0 schema |
| `generate_stubs(spec, new_signals)` | Generate code stubs for unimplemented signals |

### ConfigValidator Methods

| Method | Description |
|--------|-------------|
| `validate_yaml(yaml_string)` | Validate YAML string against v2.0 schema |
| `validate_file(file_path)` | Validate a YAML file |

### SignalLibrary Methods

| Method | Description |
|--------|-------------|
| `get_signals_for_industry(industry)` | Get signal recommendations with proxy tiers |
| `get_registry_signals_for_coverage(coverage)` | Get signals from metadata registry |
| `get_industry_profile(industry)` | Get industry configuration profile |
| `has_signal(signal_id)` | Check if signal exists in library |

## Signal Metadata Registry Integration

The builder integrates with `signal_architecture/signals/inference/metadata_registry.py` to:

1. **Validate proxy tiers** — signals get accurate `DIRECT_OBSERVABLE`, `INFERRED_PROXY`, or `COHORT_INFERENCE` classification from the registry
2. **Check signal existence** — verify that recommended signals have actual implementations
3. **Cross-coverage reuse** — identify signals already implemented for other coverages

When the registry is unavailable, the builder falls back to its built-in signal library with hardcoded proxy tier mappings.

## Testing

```bash
# Run builder tests (24 tests)
python -m pytest tests/unit/test_coverage_builder_v2.py -v

# Run calibration harness tests (30 tests)
python -m pytest tests/unit/test_calibration_harness.py -v

# Validate all existing configs
for config in coverages/*/config.yaml; do
    python -m infrastructure.builder.cli validate "$config"
done

# Run calibration harness across all configs (~140K fixtures)
python -m infrastructure.builder.cli calibrate

# Calibrate a single coverage
python -m infrastructure.builder.cli calibrate energy --json
```

## Files

```
infrastructure/builder/
  __init__.py              Module exports
  coverage_builder.py      Core builder logic (v2.0 config generation — new coverage lines)
  expansion_types.py       Expansion spec schema (ExpansionSpec, ConfigurationSpec, SignalSpec, etc.)
  expansion_generator.py   Expansion generator (config YAML + signal code from spec)
  validator.py             v2.0/v2.3 schema validation
  signal_library.py        Signal groups, industry profiles, registry integration
  types.py                 CoverageSpec, SignalSelection, ValidationResult, etc.
  migrator.py              Config version migration (v2.0 → v2.2)
  cli.py                   CLI interface (build, expand, validate, list)
  README.md                This file

development/project/
  templates/
    expansion_companion.md   Template for expansion phase companion docs
  version/4/
    phase_6_spec.yaml        Reference expansion spec (PI, 11 configs, 58 signals)

tests/unit/
  test_coverage_builder_v2.py    24 tests covering structure, constraints, validation
```

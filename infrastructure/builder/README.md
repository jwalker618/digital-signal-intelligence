# DSI Coverage Builder

## Overview

The Coverage Builder generates **v2.0 compliant** coverage configurations for the DSI framework. It produces YAML configs matching the canonical schema used by all existing coverages (cyber, D&O, aerospace, etc.).

A generated config is immediately usable by the DSI scoring engine, pricing engine, and workflow orchestrator without manual editing.

## Quick Start

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

# Validate all existing configs
for config in coverages/*/config.yaml; do
    python -m infrastructure.builder.cli validate "$config"
done
```

## Files

```
infrastructure/builder/
  __init__.py              Module exports
  coverage_builder.py      Core builder logic (v2.0 config generation)
  validator.py             v2.0 schema validation
  signal_library.py        Signal groups, industry profiles, registry integration
  types.py                 CoverageSpec, SignalSelection, ValidationResult, etc.
  cli.py                   CLI interface (build, validate, list)

tests/unit/
  test_coverage_builder_v2.py    24 tests covering structure, constraints, validation
```

# DSI Coverage Configurations

This directory contains the coverage configuration files for the Digital Signal Intelligence (DSI) platform.

## Directory Structure

```
coverages/
├── README.md                    # This file
├── doc_generator.py             # Documentation generator script
├── master_config_layout.yaml    # Master schema template
├── aerospace/
│   ├── config.yaml              # Configuration definitions
│   └── logic.md                 # Generated documentation
├── cyber/
│   ├── config.yaml
│   └── logic.md
├── {coverage}/
    ├── config.yaml
    └── logic.md
```

## Documentation Generator

The `doc_generator.py` script generates `logic.md` files for each coverage, documenting:

- Configuration metadata and routing constraints
- Signal registry with weights and directions
- Group structure and tier bands
- Pricing structure (ILF curves, deductible factors)
- Direct queries and their actions
- Limit configuration (BUNDLED or DECOUPLED)

### Usage

```bash
# From project root:
python coverages/doc_generator.py
```

### When to Run

Run the documentation generator:
- After any change to a config.yaml file
- After adding a new coverage
- Before release to ensure documentation is current

### Output

Each coverage directory receives a `logic.md` file containing comprehensive documentation for all configurations in that coverage (e.g., `cyber_general` and `cyber_sme` are both documented in `coverages/cyber/logic.md`).

## Configuration Structure

Each `config.yaml` follows the structure defined in `master_config_layout.yaml`:

```yaml
{coverage_id}:
  {config_id}:
    metadata:           # Name, version, product types, routing constraints
    direct_queries:     # Binary questions with actions
    signal_registry:    # Signals with weights and directions
    groups:            # Signal groupings for aggregation
    risk_tier_bands:   # Risk tier definitions
    loss_tier_bands:   # Loss tier definitions
    exposure:          # Size and complexity bands
    limit_configuration: # BUNDLED (packages) or DECOUPLED (limits/deductibles)
    pricing:           # ILF curves, deductible factors, taxes
```

### Limit Configuration Modes

**BUNDLED (Menu Pricing):** Fixed packages for SME segments
```yaml
limit_configuration:
  type: BUNDLED
  packages:
    - id: 1
      label: "STARTER"
      limit: 250000
      deductible: 10000
```

**DECOUPLED (Tower Pricing):** Independent selection for corporate segments
```yaml
limit_configuration:
  type: DECOUPLED
  valid_limits: [1000000, 2000000, 5000000]
  valid_deductibles: [10000, 25000, 50000]
```

## Calibration Harness

Every config must pass the calibration harness before deployment. The harness generates synthetic fixtures across the full parameter space and validates that pricing outputs are sensible.

```bash
# Calibrate all coverages
python -m infrastructure.builder.cli calibrate

# Calibrate a single coverage
python -m infrastructure.builder.cli calibrate energy

# Direct invocation
python -m layers.risk.calibration_harness
```

### Per-Config Guardrails

Each configuration has independently tuned guardrails in its `guardrails:` section:

| Guardrail | Description | Range |
|-----------|-------------|-------|
| `max_premium_to_limit_ratio` | Premium cap as fraction of limit | 0.15 – 0.80 |
| `max_premium_to_revenue_ratio` | Premium cap as fraction of revenue | 0.001 – 0.002 |
| `modifier_floor` / `modifier_cap` | Bounds on categorical modifier product | 0.1 – 2.5 |

These values are calibrated per-config using natural P/L distributions from the harness. When adding or modifying a config, run the harness and adjust guardrails until the config passes (guardrail hit rate < 15%).

### Workflow After Config Changes

1. Edit `config.yaml` (rates, damping, guardrails, tier bands)
2. Run `python -m infrastructure.builder.cli calibrate {coverage}`
3. If calibration fails, adjust `max_premium_to_limit_ratio` or `basis_damping`
4. Run `python coverages/doc_generator.py` to regenerate `logic.md`
5. Run `pytest tests/ -x` to verify unit tests still pass

## Related Documentation

- [Premium Calculation Methodology](../docs/overview/Premium_Calculation_Methodology.md)
- [Configuration Architecture](../docs/overview/Configuration_Architecture.md)
- [Master Config Layout](./master_config_layout.yaml)

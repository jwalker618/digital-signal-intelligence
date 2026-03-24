# ${\color{blue}Digital\space Signal\space Intelligence\space (DSI)}$

## A New Information Substrate for Insurance

| Item | Value |
|-|-|
|Version|0.1.0|
|Date|January 2025|
|Classification|tests|

---

# Tests

This folder contains end-to-end and system-level tests. Unit and integration tests for the main package are in `technical_pricing/tests/`.

## Test Structure

```
tests/
├── api/           # API endpoint tests
├── unit/          # Unit tests for shared utilities
└── integration/   # End-to-end integration tests
```

## Main Test Suite

The primary test suite (380+ tests) is in `technical_pricing/tests/`:

```bash
# Run all tests
pytest technical_pricing/tests/ -v

# Run with coverage
pytest technical_pricing/tests/ --cov=technical_pricing --cov-report=html

# Run specific test categories
pytest technical_pricing/tests/unit/ -v
pytest technical_pricing/tests/integration/ -v
```

## Test Categories

| Category | Location | Purpose |
|----------|----------|---------|
| Unit Tests | `technical_pricing/tests/unit/` | Individual component testing |
| Integration Tests | `technical_pricing/tests/integration/` | Cross-component workflows |
| API Tests | `tests/api/` | REST endpoint testing |
| Routing Tests | `technical_pricing/tests/unit/test_routing.py` | Jurisdiction routing |
| Workflow Tests | `technical_pricing/tests/unit/test_workflow.py` | 14-step workflow |
| Coverage Tests | `technical_pricing/tests/unit/test_coverage_configs.py` | YAML configuration |
| Calibration Tests | `tests/unit/test_calibration_harness.py` | Calibration harness validation |

## Running Tests

```bash
# Prerequisites
pip install -r requirements-dev.txt

# All tests with verbose output
pytest -v

# Specific test file
pytest technical_pricing/tests/unit/test_workflow.py -v

# Tests matching pattern
pytest -k "test_sanctions" -v

# Generate HTML coverage report
pytest technical_pricing/tests/ --cov=technical_pricing --cov-report=html
open htmlcov/index.html
```

## Calibration Harness

The calibration harness (`layers/risk/calibration_harness.py`) is a comprehensive validation tool that exercises the full pricing pipeline across all 22 coverage configurations. It generates ~140,000 synthetic fixtures spanning every product type, risk tier, exposure size band, limit cohort, deductible option, and modifier scenario.

### Running the Harness

```bash
# Run all configs
python -m layers.risk.calibration_harness

# Run a single coverage
python -m layers.risk.calibration_harness energy

# JSON output for tooling
python -m layers.risk.calibration_harness --json

# Via the builder CLI
python -m infrastructure.builder.cli calibrate
python -m infrastructure.builder.cli calibrate cyber
```

### What It Validates

| Check | Threshold | Description |
|-------|-----------|-------------|
| Guardrail hit rate | < 15% | Guardrails should not act as primary pricing control |
| P/L ratio cap | Per-config | Premium must not exceed the config's `max_premium_to_limit_ratio` |
| Tier monotonicity | 0 violations | Worse tiers must produce higher premiums than better tiers |
| Pipeline errors | < 10% | Pricing pipeline must execute without exceptions |

### Integration with the Builder

The calibration harness runs automatically after `build --write` and `expand --write` operations. If calibration fails, the output shows which configs need guardrail tuning. The health gate (`config_health_gate.py`) also exposes `run_deep_calibration()` for runtime checks.

### When to Run

- After changing any `config.yaml` pricing parameters (rates, damping, guardrails)
- After building or expanding coverage configurations
- Before release to ensure all configs produce sensible pricing
- As part of CI (see `.github/workflows/ci.yml`)

## Test Configuration

See `pyproject.toml` for pytest configuration:

```toml
[tool.pytest.ini_options]
testpaths = ["technical_pricing/tests", "tests"]
python_files = "test_*.py"
python_functions = "test_*"
```

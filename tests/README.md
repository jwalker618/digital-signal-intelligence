# ${\color{blue}Digital\space Signal\space Intelligence\space (DSI)}$

## A New Information Substrate for Insurance

| Item | Value |
|-|-|
|Version|0.4.0|
|Date|March 2026|
|Classification|tests|

---

# Tests

This folder contains unit, integration, and API tests for the DSI framework.

## Test Structure

```
tests/
├── api/           # API endpoint tests
├── unit/          # Unit tests
├── integration/   # End-to-end integration tests
└── performance/   # Performance benchmarks
```

## Running Tests

```bash
# Prerequisites
pip install -r requirements-dev.txt

# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov --cov-report=html

# Run specific test categories
pytest tests/unit/ -v
pytest tests/integration/ -v
pytest tests/api/ -v

# Tests matching pattern
pytest -k "test_sanctions" -v
```

## Test Categories

| Category | Location | Purpose |
|----------|----------|---------|
| Unit Tests | `tests/unit/` | Individual component testing |
| Integration Tests | `tests/integration/` | Cross-component workflows (21 E2E tests) |
| API Tests | `tests/api/` | REST endpoint testing |
| Calibration Tests | `tests/unit/test_calibration_harness.py` | Calibration harness validation |
| Performance Tests | `tests/performance/` | Benchmarks (workflow ~80ms, scoring ~12ms) |

## Calibration Harness

The calibration harness (`layers/risk/calibration_harness.py`) is a comprehensive validation tool that exercises the full pricing pipeline across all coverage configurations. It generates synthetic fixtures spanning every product type, risk tier, exposure size band, limit cohort, deductible option, and modifier scenario.

### Running the Harness

```bash
# All coverages
python -m layers.risk.calibration_harness

# Single coverage
python -m layers.risk.calibration_harness pi

# JSON output
python -m layers.risk.calibration_harness --json
```

### Pass Criteria

- 0 failures
- < 10% error rate
- < 15% guardrail hit rate

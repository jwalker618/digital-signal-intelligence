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

## Test Configuration

See `pyproject.toml` for pytest configuration:

```toml
[tool.pytest.ini_options]
testpaths = ["technical_pricing/tests", "tests"]
python_files = "test_*.py"
python_functions = "test_*"
```

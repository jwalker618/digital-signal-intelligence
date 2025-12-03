# DSI Test Framework

## Overview

Comprehensive test suite for Digital Signal Intelligence covering:

1. **Structural Tests** - Model instantiation, types, configuration
2. **Functional Tests** - Pricing logic, tier assignment, calculations
3. **Actuarial Validity Tests** - Risk differentiation, pricing relativities

## Architecture

```
tests/
├── conftest.py                    # Base classes, fixtures, test data generators
├── README_TEST_FRAMEWORK.md       # This file
├── run_tests.py                   # Test runner script
└── models/
    ├── cyber/tests/
    │   └── test_dsi_cyber_pricing.py    # 26 tests
    ├── fi/tests/
    │   └── test_dsi_fi_pricing.py
    ├── do/tests/
    │   └── test_dsi_do_pricing.py
    ├── energy/tests/
    │   └── test_dsi_energy_pricing.py
    └── ... (other models)
```

## Running Tests

### Run All Tests
```bash
pytest -v
```

### Run Specific Coverage
```bash
# Cyber only
pytest models/cyber/tests/ -v

# Actuarial tests only
pytest -v -k "actuarial"

# Structural tests only
pytest -v -k "structure"
```

### Run with Coverage
```bash
pytest --cov=models --cov-report=html --cov-report=term
```

### Run Markers
```bash
# Integration tests
pytest -v -m integration

# Exclude slow tests
pytest -v -m "not slow"
```

## Test Categories

### 1. Structural Tests

**Purpose:** Ensure models instantiate correctly and have expected structure

**Examples:**
- Engine instantiation
- Enum values
- Dataclass structures
- Return types

```python
def test_engine_instantiates(self):
    """Test CyberPricingEngine instantiates correctly."""
    engine = CyberPricingEngine()
    assert engine is not None
```

### 2. Functional Tests

**Purpose:** Verify pricing logic works correctly

**Examples:**
- Premium calculation
- Tier assignment
- Score ranges
- Limit scaling
- Deductible credits

```python
def test_premium_scales_with_limit(self, average_cyber_entity, limit):
    """Test premium scales appropriately with limit."""
    # Test doubling limit doubles premium (roughly)
```

### 3. Actuarial Validity Tests

**Purpose:** Ensure pricing differentiates risk appropriately

**Examples:**
- Poor security costs more
- Risk progression
- Breach history impact
- Vulnerability count impact

```python
def test_poor_security_costs_more(self, excellent_cyber_entity, poor_cyber_entity):
    """Test that poor security profile results in higher premium."""
    # Poor security should cost at least 30% more
```

## Test Fixtures

### Entity Profiles

Pre-defined test entities with known characteristics:

```python
@pytest.fixture
def excellent_cyber_entity():
    """Entity with excellent cyber security profile."""
    return TestDataGenerator.create_test_signal_set(
        "SecureTech Corp",
        "cyber",
        TestEntityProfile.EXCELLENT_SECURITY
    )
```

**Available Profiles:**
- `EXCELLENT_SECURITY` - Should get Tier 1-2, Score 750-1000
- `AVERAGE_SECURITY` - Should get Tier 2-3, Score 600-799
- `POOR_SECURITY` - Should get Tier 4-5, Score 0-499
- `STRONG_GOVERNANCE` - For D&O testing
- `WEAK_GOVERNANCE` - For D&O testing
- `WELL_CAPITALIZED` - For FI testing
- `UNDERCAPITALIZED` - For FI testing

### Test Data Generator

Creates consistent test signals:

```python
signals = TestDataGenerator.generate_cyber_signals(
    TestEntityProfile.POOR_SECURITY
)
# Returns: {"security_rating": {"score": 42, "grade": "D"}, ...}
```

## Base Test Classes

### BaseStructuralTest

Helper methods for structural validation:

```python
class MyStructuralTests(BaseStructuralTest):
    def test_my_structure(self):
        self.verify_dataclass_structure(instance, expected_fields)
        self.verify_enum_values(enum_class, expected_values)
        self.verify_return_type(value, expected_type)
```

### BaseFunctionalTest

Helper methods for functional validation:

```python
class MyFunctionalTests(BaseFunctionalTest):
    def test_my_logic(self):
        self.assert_tier_in_range(tier, min_tier, max_tier)
        self.assert_score_in_range(score, min_score, max_score)
        self.assert_premium_positive(premium)
        self.assert_premium_reasonable(premium, limit)
```

### BaseActuarialTest

Helper methods for actuarial validation:

```python
class MyActuarialTests(BaseActuarialTest):
    def test_my_pricing(self):
        self.assert_better_profile_cheaper(premium_good, premium_poor, min_ratio=1.3)
        self.assert_tier_progression(tiers)
        self.assert_score_progression(scores)
        self.assert_limit_scaling(prem_low, prem_high, limit_low, limit_high)
```

## Assertions

### TestAssertions

Common validation checks:

```python
TestAssertions.assert_valid_tier(tier)           # 1-5
TestAssertions.assert_valid_score(score)         # 0-1000
TestAssertions.assert_valid_confidence(conf)     # 0.0-1.0
TestAssertions.assert_valid_tier_label(tier, label)
TestAssertions.assert_flags_consistent(score, green, red)
```

## Test Coverage Status

| Model | Structural | Functional | Actuarial | Total Tests |
|-------|-----------|------------|-----------|-------------|
| **Cyber** | ✅ 6 tests | ✅ 12 tests | ✅ 8 tests | **26** |
| FI | 🔄 Pending | 🔄 Pending | 🔄 Pending | 0 |
| D&O | 🔄 Pending | 🔄 Pending | 🔄 Pending | 0 |
| Energy | 🔄 Pending | 🔄 Pending | 🔄 Pending | 0 |
| Marine | 🔄 Pending | 🔄 Pending | 🔄 Pending | 0 |
| PI | 🔄 Pending | 🔄 Pending | 🔄 Pending | 0 |
| Aerospace | 🔄 Pending | 🔄 Pending | 🔄 Pending | 0 |

## Example Test Output

```bash
$ pytest models/cyber/tests/test_dsi_cyber_pricing.py -v

test_dsi_cyber_pricing.py::TestCyberStructure::test_engine_instantiates PASSED
test_dsi_cyber_pricing.py::TestCyberStructure::test_tier_enum_values PASSED
test_dsi_cyber_pricing.py::TestCyberStructure::test_coverage_type_enum PASSED
test_dsi_cyber_pricing.py::TestCyberFunctional::test_calculates_premium PASSED
test_dsi_cyber_pricing.py::TestCyberFunctional::test_tier_assignment_logic PASSED
test_dsi_cyber_pricing.py::TestCyberActuarial::test_poor_security_costs_more PASSED
test_dsi_cyber_pricing.py::TestCyberActuarial::test_risk_progression PASSED
test_dsi_cyber_pricing.py::TestCyberActuarial::test_breach_history_impact PASSED

======================== 26 passed in 2.34s ========================
```

## Writing New Tests

### 1. Structural Test Template

```python
class TestMyModelStructure(BaseStructuralTest):
    """Test structural integrity of my model."""

    def test_engine_instantiates(self):
        engine = MyEngine()
        assert engine is not None
        assert isinstance(engine, MyEngine)

    def test_required_fields(self):
        profile = MyProfile(entity_id="test", entity_name="Test")
        required_fields = ["entity_id", "entity_name"]
        self.verify_dataclass_structure(profile, required_fields)
```

### 2. Functional Test Template

```python
class TestMyModelFunctional(BaseFunctionalTest):
    """Test functional behavior."""

    def setup_method(self):
        self.engine = MyEngine()

    def test_calculates_premium(self, average_entity):
        result = self.engine.calculate_premium(...)

        self.assert_premium_positive(result.gross_premium)
        self.assert_premium_reasonable(result.gross_premium, limit)
        TestAssertions.assert_valid_score(result.composite_score)
        TestAssertions.assert_valid_tier(result.tier)
```

### 3. Actuarial Test Template

```python
class TestMyModelActuarial(BaseActuarialTest):
    """Test actuarial validity."""

    def test_risk_differentiation(self, good_entity, poor_entity):
        result_good = self.engine.calculate_premium(good_entity, ...)
        result_poor = self.engine.calculate_premium(poor_entity, ...)

        # Poor risk should cost more (at least 30% more)
        self.assert_better_profile_cheaper(
            result_good.gross_premium,
            result_poor.gross_premium,
            min_ratio=1.3
        )
```

## CI/CD Integration

### GitHub Actions

The test suite runs automatically on:
- Push to any branch
- Pull request creation
- Manual workflow dispatch

```yaml
# .github/workflows/ci.yml
- name: Run tests
  run: |
    pytest -v --cov=models --cov-report=xml

- name: Upload coverage
  uses: codecov/codecov-action@v3
```

## Best Practices

### 1. Test Naming

```python
def test_<what>_<condition>_<expected>():
    """Test that <what> <expected> when <condition>."""
```

Examples:
- `test_premium_increases_with_poor_security()`
- `test_tier_assignment_follows_score_ranges()`
- `test_deductible_credit_reduces_premium()`

### 2. Test Independence

Each test should be independent:

```python
def setup_method(self):
    """Run before each test."""
    self.engine = MyEngine()  # Fresh instance

def teardown_method(self):
    """Run after each test."""
    pass  # Clean up if needed
```

### 3. Clear Assertions

Use descriptive assertion messages:

```python
assert result.tier == 2, \
    f"Expected tier 2, got {result.tier} with score {result.composite_score}"
```

### 4. Parametrized Tests

Test multiple scenarios efficiently:

```python
@pytest.mark.parametrize("limit,expected_min", [
    (1_000_000, 2_000),
    (5_000_000, 10_000),
    (10_000_000, 20_000),
])
def test_minimum_premiums(self, limit, expected_min):
    result = self.engine.calculate_premium(limit=limit)
    assert result.gross_premium >= expected_min
```

## Troubleshooting

### Import Errors

If you see `ModuleNotFoundError`:

```bash
# Ensure you're in the project root
cd /home/user/digital-signal-intelligence

# Run with python -m
python -m pytest models/cyber/tests/test_dsi_cyber_pricing.py
```

### Fixture Not Found

Ensure `conftest.py` is in the `tests/` directory and pytest can find it.

### Test Failures

Run with verbose output and traceback:

```bash
pytest -vv --tb=long models/cyber/tests/test_dsi_cyber_pricing.py
```

## Future Enhancements

- [ ] Add property-based testing with Hypothesis
- [ ] Add mutation testing with mutmut
- [ ] Add performance benchmarks
- [ ] Add contract tests for API
- [ ] Add stress tests for high volumes
- [ ] Add comparative tests (model vs model)

## Contact

For questions about the test framework:
- See main CONTRIBUTING.md
- Check test examples in `models/cyber/tests/`
- Review `tests/conftest.py` for available fixtures

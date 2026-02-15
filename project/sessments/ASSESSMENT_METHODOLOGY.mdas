# DSI Project Assessment Methodology

| Item | Value |
|-|-|
| Version | 1.0.0 |
| Date | February 2026 |
| Classification | Process Documentation |

---

## Overview

This document defines the comprehensive assessment methodology for validating the DSI (Digital Signal Intelligence) project. The assessment framework ensures consistency, completeness, and compliance across all project components.

## Assessment Tools

The DSI project uses a layered assessment approach with multiple tools:

### 1. Comprehensive Project Assessor (Primary)

**Location:** `tests/comprehensive_assessor.py`

The primary assessment tool that validates all aspects of the project:

```bash
# Full assessment
python tests/comprehensive_assessor.py

# Configuration compliance only
python tests/comprehensive_assessor.py --config-only

# Structure assessment only
python tests/comprehensive_assessor.py --structure-only

# JSON output for CI/CD
python tests/comprehensive_assessor.py --json

# Show all results including passes
python tests/comprehensive_assessor.py --show-passes
```

**Assessment Categories:**

| Category | Description | Typical Checks |
|-|-|-|
| CONFIG | Configuration compliance | Schema version, weights, anchors, pricing methodology |
| STRUCTURE | Project structure | Required directories, files, documentation |
| CONSISTENCY | Cross-coverage consistency | Structural patterns, version alignment |
| REGISTRY | Inference function registry | All referenced functions exist |
| TESTS | Test infrastructure | Test directories, collection, fixtures |
| DOCS | Documentation | logic.md files, key documentation |

### 2. Phase 5 Configuration Assessor

**Location:** `tests/assess_completeness.py`

Focused assessment for Phase 5 pricing compliance:

```bash
# Assess single coverage config
python tests/assess_completeness.py coverages/cyber/config.yaml

# Assess all coverages
for config in coverages/*/config.yaml; do
    python tests/assess_completeness.py "$config"
done
```

**Phase 5 Compliance Checks:**

1. **Schema Version** - Must be >= 2.2.0
2. **Weight Sums** - Risk, loss, exposure weights sum to 1.0
3. **Routing Exclusivity** - SME/Corporate configs have mutually exclusive constraints
4. **Scalability Trap** - PREMIUM_BASE has routing ceiling
5. **Multiplier Basis** - MULTIPLIER basis field in minimum_viable_input
6. **Actuarial Monotonicity** - Tier pricing strictly increases
7. **Penalty Ratio** - Tier 5/Tier 1 ratio >= 2.0
8. **Pricing Anchors** - base_limit_reference and base_deductible_reference defined
9. **ILF Normalization** - Anchor limit has factor = 1.0
10. **Deductible Normalization** - Anchor deductible has factor = 1.0
11. **Phase 5 Deprecation** - No legacy deductible_credits fields

### 3. Configuration Validator

**Location:** `infrastructure/validation/config_validator.py`

Schema validation for individual configurations:

```bash
# Via builder CLI
python -m infrastructure.builder.cli validate coverages/cyber/config.yaml
```

---

## Assessment Workflow

### When to Run Assessments

| Trigger | Assessment Type | Command |
|-|-|-|
| Before commit | Full assessment | `python tests/comprehensive_assessor.py` |
| After config change | Phase 5 compliance | `python tests/assess_completeness.py coverages/{coverage}/config.yaml` |
| CI/CD pipeline | Full + JSON | `python tests/comprehensive_assessor.py --json` |
| Adding new coverage | Full assessment | `python tests/comprehensive_assessor.py` |
| Release preparation | Full + show-passes | `python tests/comprehensive_assessor.py --show-passes` |

### Severity Levels

| Level | Meaning | Action Required |
|-|-|-|
| PASS | Check succeeded | None |
| WARNING | Non-critical issue | Review, fix if time permits |
| FAIL | Critical issue | Must fix before proceeding |
| SKIP | Check not applicable | None |

### Score Calculation

```
Category Score = (PASS + WARNING * 0.5) / TOTAL * 100
Overall Score = Sum(All PASS + All WARNING * 0.5) / Sum(All TOTAL) * 100
```

---

## Configuration Compliance Requirements

### Required Configuration Sections

Every coverage configuration must include:

```yaml
{coverage_id}:
  {config_id}:
    metadata:           # Required: name, version, product_types, minimum_viable_input
    direct_queries:     # Required: max 10 binary questions
    signal_registry:    # Required: >= 10 signals recommended
    groups:            # Required: categories and three_layer_assessment
    risk_tier_bands:   # Required: 5 tiers, 0-1000 coverage
    loss_tier_bands:   # Required: with floor/cap constraints
    exposure:          # Required: size and complexity bands
    limit_configuration: # Required: DECOUPLED type with valid_limits/deductibles
    pricing:           # Required: anchors, ILF curves, deductible factors
```

### limit_configuration Structure

All configurations must use the DECOUPLED limit_configuration format:

```yaml
limit_configuration:
  type: DECOUPLED
  valid_limits:
    - 1000000
    - 2000000
    - 5000000
  valid_deductibles:
    - 10000
    - 25000
    - 50000
```

**Note:** The legacy `limit_bandings` (bundled menu pricing) has been deprecated.

### Pricing Anchor Requirements

1. `base_limit_reference` must be defined
2. `base_deductible_reference` must be defined
3. ILF curve must include anchor limit with factor = 1.0
4. Deductible factors must include anchor deductible with factor = 1.0

---

## Project Structure Requirements

### Required Directories

```
/home/user/digital-signal-intelligence/
  coverages/           # Coverage configurations
    aerospace/
    cyber/
    do/
    energy/
    fi/
    marine/
    pi/
  layers/             # Assessment layers (risk, loss, exposure)
  signal_architecture/ # Signal extraction and inference
  infrastructure/      # API, database, validation
  tests/              # Test suite
  docs/               # Documentation
  schemas/            # YAML schemas
```

### Required Files per Coverage

| File | Purpose |
|-|-|
| `config.yaml` | Coverage configuration |
| `logic.md` | Rationale for signal selection and weighting (recommended) |

### Required Documentation

| Document | Path |
|-|-|
| Premium Methodology | `docs/overview/Premium_Calculation_Methodology.md` |
| Configuration Architecture | `docs/overview/Configuration_Architecture.md` |
| Foundational Principles | `docs/overview/Foundational Principles.md` |
| Completeness Checklist | `development/project/version/project_completeness_checklist.md` |
| Master Config Layout | `coverages/master_config_layout.yaml` |

---

## Cross-Coverage Consistency

### Structural Consistency

All configurations should have identical structural components:
- direct_queries
- signal_registry
- groups (categories, three_layer_assessment)
- risk_tier_bands
- loss_tier_bands
- exposure
- limit_configuration
- pricing

### Version Alignment

While minor version differences are acceptable during development, all production configurations should align on the same schema version.

---

## Inference Registry Validation

The assessment verifies that all `inference_utility_function` references in coverage configs resolve to registered functions in the inference registry.

**Expected in Development:** Missing functions flagged as FAIL, but this is expected when using stub extractors.

**Expected in Production:** All referenced functions must exist and be registered.

---

## Test Infrastructure Assessment

### Required Test Structure

```
tests/
  conftest.py          # Shared fixtures
  unit/                # Unit tests
  integration/         # Integration tests
  api/                 # API tests
  performance/         # Performance benchmarks
```

### Test Collection

The assessor runs `pytest --collect-only` to verify tests can be collected without import errors.

---

## CI/CD Integration

### Example GitHub Actions Workflow

```yaml
- name: Run DSI Assessment
  run: |
    python tests/comprehensive_assessor.py --json > assessment.json

- name: Check Assessment Score
  run: |
    SCORE=$(cat assessment.json | jq '.overall_score')
    FAILURES=$(cat assessment.json | jq '.total_failures')
    echo "Score: $SCORE%, Failures: $FAILURES"
    if [ "$FAILURES" -gt 0 ]; then
      exit 1
    fi
```

### Exit Codes

| Code | Meaning |
|-|-|
| 0 | All checks passed (no failures) |
| 1 | One or more failures detected |

---

## Remediation Guidelines

### Configuration Failures

| Issue | Resolution |
|-|-|
| Schema version low | Update metadata.version to >= 2.2.0 |
| Weights don't sum to 1.0 | Adjust group weights |
| Missing anchors | Add base_limit_reference and base_deductible_reference |
| ILF anchor != 1.0 | Ensure anchor limit has factor: 1.0 |
| Using limit_bandings | Convert to limit_configuration with DECOUPLED type |
| Scalability Trap | Add routing_constraints with ceiling operator |

### Documentation Failures

| Issue | Resolution |
|-|-|
| Missing logic.md | Create logic.md explaining signal selection rationale |
| Missing key docs | Create required documentation files |

### Registry Failures

| Issue | Resolution |
|-|-|
| Missing inference functions | Register functions or use stub mode |

---

## Extending the Assessment Framework

### Adding New Checks

1. Add test method to `DSIComprehensiveAssessor` class
2. Use `_add_result()` helper to record results
3. Call new method from appropriate `assess_*` method

Example:
```python
def _test_custom_requirement(self, config_name: str, config: Dict):
    """Test custom requirement."""
    passes = config.get('custom_field') is not None
    self._add_result(
        "CONFIG", "Custom Requirement",
        passes,
        "Custom requirement met" if passes else "Missing custom_field",
        config_name=config_name
    )
```

### Adding New Categories

1. Add category to `CATEGORIES` dict
2. Create `assess_*` method for the category
3. Call from `run_full_assessment()`

---

## Version History

| Version | Date | Changes |
|-|-|-|
| 1.0.0 | February 2026 | Initial comprehensive assessment framework |

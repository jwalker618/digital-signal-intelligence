# DSI Project Assessment Methodology

| Item | Value |
|-|-|
| Version | 2.0.0 |
| Date | February 2026 |
| Classification | Process Documentation |

---

## Overview

This document defines the comprehensive assessment methodology for validating the DSI (Digital Signal Intelligence) project. The assessment framework ensures consistency, completeness, and compliance across all project components.

## Assessment Tools

The DSI project uses a layered assessment approach with multiple tools:

### 1. Comprehensive Project Assessor (Primary)

**Location:** `development/project/assessments/scripts/assess_project.py`

The primary assessment tool that validates all aspects of the project:

```bash
# Full assessment
python development/project/assessments/scripts/assess_project.py

# Configuration compliance only
python development/project/assessments/scripts/assess_project.py --config-only

# Structure assessment only
python development/project/assessments/scripts/assess_project.py --structure-only

# JSON output for CI/CD
python development/project/assessments/scripts/assess_project.py --json

# Show all results including passes
python development/project/assessments/scripts/assess_project.py --show-passes

# Save report to results directory
python development/project/assessments/scripts/assess_project.py --save-report

# Custom output directory
python development/project/assessments/scripts/assess_project.py --save-report --output-dir /path/to/output
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

### 2. Configuration Compliance Assessor

**Location:** `development/project/assessments/scripts/assess_config_compliance.py`

Focused assessment for individual configuration compliance:

```bash
# Assess single coverage config
python development/project/assessments/scripts/assess_config_compliance.py coverages/cyber/config.yaml

# Assess all coverages
for config in coverages/*/config.yaml; do
    python development/project/assessments/scripts/assess_config_compliance.py "$config"
done
```

**Compliance Checks:**

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
12. **Limit Configuration** - Valid BUNDLED packages or DECOUPLED limits/deductibles

### 3. Configuration Validator

**Location:** `infrastructure/builder/validator.py`

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
| Before commit | Full assessment | `python development/project/assessments/scripts/assess_project.py` |
| After config change | Config compliance | `python development/project/assessments/scripts/assess_config_compliance.py coverages/{coverage}/config.yaml` |
| CI/CD pipeline | Full + JSON | `python development/project/assessments/scripts/assess_project.py --json` |
| Adding new coverage | Full assessment | `python development/project/assessments/scripts/assess_project.py` |
| Release preparation | Full + save report | `python development/project/assessments/scripts/assess_project.py --save-report --show-passes` |

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
    limit_configuration: # Required: BUNDLED or DECOUPLED type
    pricing:           # Required: anchors, ILF curves, deductible factors
```

### limit_configuration Structure

Two modes are supported based on the segment:

**BUNDLED (Menu Pricing) - For SME Segments:**

```yaml
limit_configuration:
  type: BUNDLED
  packages:
    - id: 1
      label: "STARTER"
      limit: 250000
      deductible: 10000
    - id: 2
      label: "STANDARD"
      limit: 500000
      deductible: 25000
    - id: 3
      label: "PREMIUM"
      limit: 1000000
      deductible: 50000
```

**DECOUPLED (Tower Pricing) - For Corporate/General Segments:**

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
  development/project/assessments/  # Assessment tooling
```

### Required Files per Coverage

| File | Purpose |
|-|-|
| `config.yaml` | Coverage configuration |
| `logic.md` | Rationale for signal selection and weighting (generated by doc_generator.py) |

### Required Documentation

| Document | Path |
|-|-|
| Premium Methodology | `docs/overview/Premium_Calculation_Methodology.md` |
| Configuration Architecture | `docs/overview/Configuration_Architecture.md` |
| Foundational Principles | `docs/overview/Foundational Principles.md` |
| Completeness Checklist | `development/project/assessments/project_completeness_checklist.md` |
| Master Config Layout | `coverages/master_config_layout.yaml` |
| Assessment Methodology | `development/project/assessments/ASSESSMENT_METHODOLOGY.md` |

---

## Assessment Results

### Results Directory

Assessment results are stored in `development/project/assessments/results/`:

```
results/
├── assessment_results_2026-02-15.md   # Latest results
├── assessment_results_2026-02-14.md   # Previous results
└── assessment_results_2026-02-01.md   # Historical results
```

### Relationship to Checklist

The `project_completeness_checklist.md` provides a comprehensive list of 293+ items across all project categories. The assessment scripts validate a subset of these items automatically. Manual review is required for items not covered by automated checks.

---

## CI/CD Integration

### Example GitHub Actions Workflow

```yaml
- name: Run DSI Assessment
  run: |
    python development/project/assessments/scripts/assess_project.py --json > assessment.json

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
| Invalid limit_configuration | Use BUNDLED with packages or DECOUPLED with valid_limits/valid_deductibles |
| Scalability Trap | Add routing_constraints with ceiling operator |

### Documentation Failures

| Issue | Resolution |
|-|-|
| Missing logic.md | Run `python coverages/doc_generator.py` |
| Missing key docs | Create required documentation files |

### Registry Failures

| Issue | Resolution |
|-|-|
| Missing inference functions | Register functions or use stub mode |

---

## Version History

| Version | Date | Changes |
|-|-|-|
| 2.0.0 | February 2026 | Consolidated to development/project/assessments/, added BUNDLED support |
| 1.0.0 | February 2026 | Initial comprehensive assessment framework |

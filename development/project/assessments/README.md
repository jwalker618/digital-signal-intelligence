# DSI Assessment Tooling

This directory contains all project assessment tools and results for the Digital Signal Intelligence (DSI) system.

## Directory Structure

```
assessments/
├── README.md                              # This file
├── ASSESSMENT_METHODOLOGY.md              # Process documentation
├── project_completeness_checklist.md      # Master checklist (293+ items)
├── results/                               # Assessment output files
│   ├── assessment_results_YYYY-MM-DD.md   # Timestamped results
│   └── ...
└── scripts/                               # Assessment tools
    ├── assess_project.py                  # Full project assessment
    └── assess_config_compliance.py        # Single config validation
```

## Scripts

### assess_project.py (Comprehensive Project Assessment)

Full project-wide assessment covering 6 categories:
- Configuration compliance (Phase 5 schema, pricing anchors, weights)
- Project structure (required files, directories, documentation)
- Cross-coverage consistency (structural patterns, signal reuse)
- Inference function registry (all referenced functions exist)
- Test infrastructure status (import checks, test collection)
- Documentation completeness

**Usage:**
```bash
# Full assessment
python development/project/assessments/scripts/assess_project.py

# Config assessment only
python development/project/assessments/scripts/assess_project.py --config-only

# Structure assessment only
python development/project/assessments/scripts/assess_project.py --structure-only

# JSON output
python development/project/assessments/scripts/assess_project.py --json

# Specific coverage
python development/project/assessments/scripts/assess_project.py --coverage cyber

# Save report to results directory
python development/project/assessments/scripts/assess_project.py --save-report
```

**When to run:**
- Before committing significant changes
- In CI/CD pipelines
- To generate assessment reports

### assess_config_compliance.py (Single Configuration Validation)

Validates a single config.yaml against Phase 5 rules:
- Schema version compliance (>= 2.2.0)
- Signal weights sum to 1.0 per group
- Pricing anchors present and normalized (factor = 1.0)
- No deprecated fields (deductible_credits, deductible_buy_down_rates)
- Actuarial monotonicity (pricing increases with tier)
- Limit configuration validity (BUNDLED packages or DECOUPLED limits/deductibles)

**Usage:**
```bash
python development/project/assessments/scripts/assess_config_compliance.py coverages/cyber/config.yaml
```

**When to run:**
- After editing any config.yaml
- Before committing config changes

## Results

Assessment results are stored in `results/` with timestamped filenames:
- `assessment_results_2026-02-14.md` - Full project assessment from Feb 14
- `assessment_results_2026-02-01.md` - Earlier assessment

## Relationship to Checklist

The `project_completeness_checklist.md` provides a comprehensive list of 293+ items across all project categories. The assessment scripts validate a subset of these items automatically. Manual review is required for items not covered by automated checks.

## Exit Codes

Both scripts return:
- `0` - All checks passed
- `1` - One or more checks failed

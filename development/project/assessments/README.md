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
│   ├── checklist_assessment_YYYY-MM-DD.md # Checklist-driven results
│   └── ...
└── scripts/                               # Assessment tools
    ├── assess_project.py                  # Full project assessment
    ├── assess_config_compliance.py        # Single config validation
    └── assess_checklist.py                # Checklist-driven assessment
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

### assess_checklist.py (Checklist-Driven Assessment)

Comprehensive assessment tool that evaluates the project directly against the
`project_completeness_checklist.md` structure. Unlike `assess_project.py` which
runs its own category checks, this tool:

1. Parses the actual checklist markdown structure
2. Maps each **(Test)** item to automated verification
3. Tracks **(Manual)** items requiring human review
4. Produces output in the checklist's own summary template format

**Usage:**
```bash
# Full assessment
python development/project/assessments/scripts/assess_checklist.py

# Specific section only
python development/project/assessments/scripts/assess_checklist.py --section layers

# Only (Test) items
python development/project/assessments/scripts/assess_checklist.py --test-only

# Only (Manual) items
python development/project/assessments/scripts/assess_checklist.py --manual-only

# JSON output
python development/project/assessments/scripts/assess_checklist.py --json

# Detailed per-section report
python development/project/assessments/scripts/assess_checklist.py --detailed

# Save report to results/
python development/project/assessments/scripts/assess_checklist.py --save-report
```

**When to run:**
- For comprehensive project assessment against checklist
- When tracking progress against checklist items
- To identify gaps in automated vs manual verification

## Results

Assessment results are stored in `results/` with timestamped filenames:
- `assessment_results_2026-02-14.md` - Full project assessment from Feb 14
- `assessment_results_2026-02-01.md` - Earlier assessment

## Relationship to Checklist

The `project_completeness_checklist.md` provides a comprehensive list of 293+ items across all project categories.

**Two approaches to automated assessment:**

| Script | Approach | Coverage |
|-|-|-|
| `assess_project.py` | Category-based checks (~6 categories) | Quick validation of key metrics |
| `assess_checklist.py` | Checklist-driven (parses actual checklist) | Maps directly to checklist items |

Use `assess_project.py` for quick CI/CD validation. Use `assess_checklist.py` for detailed progress tracking against the full checklist. Manual review is required for items marked **(Manual)**.

## Exit Codes

Both scripts return:
- `0` - All checks passed
- `1` - One or more checks failed

# Phase 7: Structural Corrections & Tooling Consolidation

## Context

Several items have drifted from their intended design during recent development phases:

1. **BUNDLED limit configuration was removed entirely** rather than standardised alongside DECOUPLED. Phase V5 explicitly designed a polymorphic approach supporting both BUNDLED (Menu Pricing) for SME risks and DECOUPLED (Tower Pricing) for corporate risks. The master schema and all SME configs now only reference DECOUPLED, and `Premium_Calculation_Methodology.md` explicitly deprecates BUNDLED — contradicting the agreed design.

2. **Assessment tooling is fragmented.** Two assessment scripts (`tests/assess_completeness.py` and `tests/comprehensive_assessor.py`), a checklist (`project_completeness_checklist.md`), a methodology document (`ASSESSMENT_METHODOLOGY.md`), and prior results are spread across multiple directories with unclear relationships. The user has created `development/project/assessments/` as the intended home for this work.

3. **The doc_generator.py needs relocation and improvement.** It currently lives in `infrastructure/builder/` and outputs to `docs/coverages/`. The user has moved the generated docs into `coverages/<name>/logic.md` and wants the generator relocated to `coverages/`, updated to produce per-configuration documentation (not per-coverage), and re-executed to produce comprehensive logic.md files.

4. **SKILL.md and README.md lack references** to the assessment tooling and logic.md generation — two important repeatable processes that must be discoverable for future work.

## Purpose

Correct structural drift, consolidate assessment tooling, improve documentation generation, and ensure all repeatable processes are properly referenced in project governance documents.

---

## Work Stream 1: Reintroduce BUNDLED Limit Configuration

### 1.1 Problem Statement

Phase V5 (`phase_v5.md`) defined two modes:
- **BUNDLED (Menu Pricing):** Fixed packages with coupled limit/deductible, appropriate for SME risks
- **DECOUPLED (Tower Pricing):** Independent limit/deductible selection, appropriate for corporate risks

During implementation, only DECOUPLED was applied. The BUNDLED option was removed from the master schema and all configs. The `Premium_Calculation_Methodology.md` (line 146) incorrectly states: *"Legacy bundled (menu-style) configurations where limits and deductibles were locked together have been deprecated."*

### 1.2 Agreed Format

```yaml
# OPTION A: BUNDLED (Menu Pricing)
limit_configuration:
  type: "BUNDLED"
  packages:
    - id: {integer}
      label: "{string}"               # e.g., "GOLD PACKAGE"
      limit: {integer}
      deductible: {integer}

# OPTION B: DECOUPLED (Tower Pricing)
limit_configuration:
  type: "DECOUPLED"
  valid_limits:
    - {integer}
  valid_deductibles:
    - {integer}
```

### 1.3 Tasks

| # | Task | File(s) | Detail |
|---|------|---------|--------|
| 1.3.1 | Update master schema to support both types | `coverages/master_config_layout.yaml` | Replace the current DECOUPLED-only `limit_configuration` block (lines 513-518) with a polymorphic definition showing both BUNDLED and DECOUPLED options, using the agreed format above. Add inline comments explaining when each is appropriate. |
| 1.3.2 | Convert SME configs to BUNDLED | `coverages/cyber/config.yaml` (cyber_sme, ~line 1809), `coverages/do/config.yaml` (do_sme, ~line 1993), `coverages/aerospace/config.yaml` (aerospace_sme, ~line 2066) | Replace `type: DECOUPLED` + `valid_limits`/`valid_deductibles` with `type: BUNDLED` + `packages` list. Each package should have an `id`, `label`, `limit`, and `deductible` that represent sensible fixed options for the SME segment of that coverage. |
| 1.3.3 | Leave corporate/general configs as DECOUPLED | All `*_general` configurations | No changes needed — these correctly use DECOUPLED. Verify they conform to the agreed format. |
| 1.3.4 | Correct Premium Calculation Methodology | `docs/overview/Premium_Calculation_Methodology.md` | Remove the deprecation note at line 146. Replace Section 5a with a description of both modes: BUNDLED for SME (fixed packages, simpler selection) and DECOUPLED for corporate (independent selection, ILF/deductible factor scaling). Explain that `type` determines engine behaviour. |
| 1.3.5 | Verify Phase V5 alignment | `development/project/version/active/phase_v5.md` | Confirm phase_v5.md still accurately describes the dual-mode design. No changes expected — this is the source of truth. |

### 1.4 Validation

- [ ] `master_config_layout.yaml` documents both BUNDLED and DECOUPLED under `limit_configuration`
- [ ] All 3 SME configs (`cyber_sme`, `do_sme`, `aerospace_sme`) use `type: BUNDLED` with `packages`
- [ ] All general/corporate configs retain `type: DECOUPLED` with `valid_limits`/`valid_deductibles`
- [ ] `Premium_Calculation_Methodology.md` describes both modes without deprecation language
- [ ] YAML parsing succeeds for all modified config files

---

## Work Stream 2: Assessment Tooling Consolidation

### 2.1 Problem Statement

Assessment-related files are currently scattered:

| File | Current Location | Purpose |
|------|-----------------|---------|
| `project_completeness_checklist.md` | `development/project/version/` | Master checklist (293+ items) |
| `assessment_results_2026-02-14.md` | `development/project/version/` | Most recent results |
| `completeness_assessment.md` | `development/project/version/active/` | Earlier assessment (2026-02-01) |
| `ASSESSMENT_METHODOLOGY.md` | `docs/assessment/` | Process documentation |
| `assess_completeness.py` | `tests/` | Phase 5 config compliance (11 checks) |
| `comprehensive_assessor.py` | `tests/` | Full project assessment (6 categories) |

The intended home is `development/project/assessments/`. The relationship between these files is unclear, and the two Python scripts have overlapping but distinct scopes.

### 2.2 Proposed Structure

```
development/project/assessments/
├── README.md                              # How to run assessments, what each file does
├── ASSESSMENT_METHODOLOGY.md              # Moved from docs/assessment/
├── project_completeness_checklist.md      # Moved from development/project/version/
├── results/
│   ├── assessment_results_2026-02-01.md   # Renamed from completeness_assessment.md
│   └── assessment_results_2026-02-14.md   # Moved from development/project/version/
└── scripts/
    ├── assess_project.py                  # Consolidated assessment script (see 2.3)
    └── assess_config_compliance.py        # Renamed from assess_completeness.py
```

### 2.3 Script Consolidation Analysis

The two current scripts serve different purposes:

| Aspect | `assess_completeness.py` | `comprehensive_assessor.py` |
|--------|--------------------------|----------------------------|
| **Scope** | Single config.yaml file | Entire project |
| **Checks** | 11 pricing/schema compliance | ~50+ structural/consistency/registry |
| **Input** | CLI path to one config | Scans project root |
| **Output** | PASS/FAIL per assertion | Categorised report with severity |
| **Use Case** | After editing a config | Before commit / CI/CD |

**Recommendation:** Keep as two scripts with distinct purposes. They are complementary, not redundant.

- `assess_config_compliance.py` — Validates a single config.yaml against Phase V5 rules. Run after editing any config.
- `assess_project.py` — Comprehensive project-wide assessment. Run before commits, in CI/CD, and to generate assessment reports.

Both scripts should be updated to:
1. Output results to `development/project/assessments/results/` with timestamped filenames
2. Reference the `project_completeness_checklist.md` items where applicable
3. Support `--output-dir` flag to override default output location

### 2.4 Tasks

| # | Task | Detail |
|---|------|--------|
| 2.4.1 | Create directory structure | Create `development/project/assessments/`, `development/project/assessments/results/`, `development/project/assessments/scripts/` |
| 2.4.2 | Move documentation files | Move `project_completeness_checklist.md` from `development/project/version/` to `development/project/assessments/`. Move `ASSESSMENT_METHODOLOGY.md` from `docs/assessment/` to `development/project/assessments/`. Move `assessment_results_2026-02-14.md` to `development/project/assessments/results/`. Move `completeness_assessment.md` to `development/project/assessments/results/assessment_results_2026-02-01.md`. |
| 2.4.3 | Relocate and rename scripts | Move `tests/comprehensive_assessor.py` to `development/project/assessments/scripts/assess_project.py`. Move `tests/assess_completeness.py` to `development/project/assessments/scripts/assess_config_compliance.py`. |
| 2.4.4 | Update `assess_project.py` | Update import paths. Add `--output-dir` flag (default: `development/project/assessments/results/`). Ensure output filename uses format `assessment_results_YYYY-MM-DD.md`. Review and update check categories to align with current project state. Add BUNDLED limit_configuration validation alongside DECOUPLED. |
| 2.4.5 | Update `assess_config_compliance.py` | Update import paths. Add BUNDLED type validation (packages structure). Ensure it handles both BUNDLED and DECOUPLED configs correctly. |
| 2.4.6 | Update `ASSESSMENT_METHODOLOGY.md` | Update all file paths to reflect new locations. Update script invocation commands. Clarify the relationship between checklist, scripts, and results. Document the two-script approach and when to use each. |
| 2.4.7 | Create `README.md` for assessments | Concise guide: what each file does, how to run each script, how to interpret results, how results map to the checklist. |
| 2.4.8 | Clean up old locations | Remove files from old locations. Remove `docs/assessment/` directory if empty. Update any references in other files pointing to old paths. |
| 2.4.9 | Execute new assessment | Run `assess_project.py` to produce `assessment_results_2026-02-15.md` in the results directory. Review output for accuracy. |

### 2.5 Validation

- [ ] All assessment files consolidated under `development/project/assessments/`
- [ ] Both scripts execute without errors from new locations
- [ ] `assess_project.py` produces a timestamped results file in `results/`
- [ ] `assess_config_compliance.py` correctly validates both BUNDLED and DECOUPLED configs
- [ ] `ASSESSMENT_METHODOLOGY.md` paths and commands are accurate
- [ ] `README.md` clearly explains the assessment workflow
- [ ] No orphaned files remain in old locations

---

## Work Stream 3: Documentation Generator & logic.md Files

### 3.1 Problem Statement

`infrastructure/builder/doc_generator.py` generates coverage documentation but has several issues:

1. **Wrong location:** Lives in `infrastructure/builder/`, should be in `coverages/`
2. **Per-coverage, not per-configuration:** Generates one file per coverage directory (e.g., `cyber.md`) rather than one per configuration (e.g., `cyber_general` and `cyber_sme` get merged into a single file)
3. **Wrong output path:** Outputs to `docs/coverages/`, but logic.md files now live under `coverages/<name>/logic.md`
4. **No README:** No documentation explaining how to run the generator
5. **Incomplete output:** General structure needs review for completeness of generated content

### 3.2 Proposed Structure

```
coverages/
├── doc_generator.py                       # Moved from infrastructure/builder/
├── README.md                              # How to use the generator
├── master_config_layout.yaml
├── aerospace/
│   ├── __init__.py
│   ├── config.yaml
│   └── logic.md                           # Generated: one section per configuration
├── cyber/
│   ├── __init__.py
│   ├── config.yaml
│   └── logic.md                           # Generated: cyber_general + cyber_sme sections
├── do/
│   ├── __init__.py
│   ├── config.yaml
│   └── logic.md                           # Generated: do_general + do_sme sections
├── energy/
│   ├── ...
│   └── logic.md
├── fi/
│   ├── ...
│   └── logic.md
├── marine/
│   ├── ...
│   └── logic.md
└── pi/
    ├── ...
    └── logic.md
```

### 3.3 Tasks

| # | Task | Detail |
|---|------|--------|
| 3.3.1 | Move doc_generator.py | Move `infrastructure/builder/doc_generator.py` to `coverages/doc_generator.py`. Update any imports/paths within the script. |
| 3.3.2 | Refactor for per-configuration output | Currently the generator iterates coverage directories and produces one document per directory. Refactor to iterate each configuration *within* a config.yaml (e.g., `cyber_general`, `cyber_sme`) and produce a logic.md that documents each configuration as a separate section. |
| 3.3.3 | Update output paths | Change output from `docs/coverages/<name>.md` to `coverages/<name>/logic.md`. |
| 3.3.4 | Add BUNDLED limit_configuration support | The current `_document_limit_bandings()` method references the old `limit_bandings` key. Update to handle the new `limit_configuration` structure for both BUNDLED (packages) and DECOUPLED (valid_limits/valid_deductibles). |
| 3.3.5 | Review and improve output completeness | Ensure all sections of a configuration are documented: metadata (including routing_constraints, model_specificity), direct_queries, signal_registry (with weights/directions), groups (categorical + three_layer_assessment), risk_tier_bands, loss_tier_bands, exposure, limit_configuration, pricing (anchors, ILF curves, deductible_factors, taxes). Add a summary section per configuration showing key statistics (signal count, group count, tier count, pricing method). |
| 3.3.6 | Create coverages/README.md | Document: purpose of the generator, how to run it (`python coverages/doc_generator.py`), what it produces, when to re-run (after any config.yaml change), relationship between config.yaml and logic.md. |
| 3.3.7 | Clean up old output | Remove `docs/coverages/` directory (content now lives in `coverages/<name>/logic.md`). Update any references in other files. |
| 3.3.8 | Execute generator | Run the updated generator to produce new logic.md files for all 7 coverages. |
| 3.3.9 | Verify output | Confirm a logic.md exists in each of the 7 coverage directories. Confirm multi-configuration coverages (cyber, do, aerospace) have sections for each config. Confirm BUNDLED and DECOUPLED limit configs are correctly documented. |

### 3.4 Validation

- [ ] `doc_generator.py` lives in `coverages/` and runs from project root
- [ ] 7 logic.md files produced (one per coverage directory)
- [ ] Multi-config coverages have distinct sections per configuration
- [ ] BUNDLED packages documented correctly in SME sections
- [ ] DECOUPLED limits/deductibles documented correctly in corporate sections
- [ ] `coverages/README.md` explains usage
- [ ] `docs/coverages/` removed or repurposed
- [ ] Generator is idempotent (re-running produces identical output)

---

## Work Stream 4: SKILL.md & README.md References

### 4.1 Problem Statement

Two important repeatable processes now exist in the project:

1. **Assessment execution** — `development/project/assessments/scripts/assess_project.py`
2. **Logic documentation generation** — `coverages/doc_generator.py`

Neither is referenced in SKILL.md or README.md, meaning future development work may not discover or use them.

### 4.2 Tasks

| # | Task | Detail |
|---|------|--------|
| 4.2.1 | Update SKILL.md — Development Workflow | Add a step (or sub-step) to the 14-step development workflow referencing assessment execution before committing significant changes. |
| 4.2.2 | Update SKILL.md — Outstanding Work / Tools | Add a section or entries documenting both the assessment tooling and the doc_generator as project tools. Include invocation commands and output locations. |
| 4.2.3 | Update SKILL.md — File Structure | Update the file structure section to reflect new locations: `development/project/assessments/`, `coverages/doc_generator.py`, `coverages/<name>/logic.md`. |
| 4.2.4 | Update README.md — Repository Structure | Update the repository structure overview to include the assessments directory and the logic.md files under coverages. |
| 4.2.5 | Update README.md — Tooling | Add a brief section or entries under an existing section describing the two repeatable tools (assessment and doc generation) with invocation examples. |
| 4.2.6 | Cross-reference verification | Ensure no stale references remain to `docs/coverages/`, `docs/assessment/`, `tests/comprehensive_assessor.py`, `tests/assess_completeness.py`, or `infrastructure/builder/doc_generator.py`. |

### 4.3 Validation

- [ ] SKILL.md references assessment tooling with correct paths and commands
- [ ] SKILL.md references doc_generator with correct path and command
- [ ] SKILL.md file structure section is accurate
- [ ] README.md repository structure includes assessments and logic.md
- [ ] README.md mentions both tools with invocation examples
- [ ] No stale file paths remain in either document

---

## Execution Order

The four work streams have dependencies:

```
Work Stream 1 (BUNDLED limits)
    │
    ├──► Work Stream 3 (doc_generator — needs BUNDLED format to document)
    │        │
    │        └──► Work Stream 4 (SKILL.md/README.md — needs final paths)
    │
    └──► Work Stream 2 (assessment — needs BUNDLED to validate)
             │
             └──► Work Stream 4 (SKILL.md/README.md — needs final paths)
```

**Recommended sequence:**

1. **Work Stream 1** — Reintroduce BUNDLED to schema and configs (foundation for everything else)
2. **Work Stream 2** — Consolidate assessment tooling (can validate Work Stream 1 changes)
3. **Work Stream 3** — Update and relocate doc_generator, produce logic.md files
4. **Work Stream 4** — Update SKILL.md and README.md (references all final paths)

---

## Success Criteria

| Criterion | Measurable |
|-----------|-----------|
| Polymorphic limit_configuration | Master schema documents both BUNDLED and DECOUPLED; 3 SME configs use BUNDLED; remaining configs use DECOUPLED |
| Assessment consolidated | All assessment files under `development/project/assessments/`; both scripts run; new assessment produced |
| Documentation generated | 7 logic.md files produced by `coverages/doc_generator.py`; per-configuration sections; README explains usage |
| Governance updated | SKILL.md and README.md reference both tools with correct paths |
| No orphaned files | Old locations cleaned up; no stale references in documentation |

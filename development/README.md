# Development Documentation

This folder contains internal planning documents, validation studies, and implementation guides that support DSI development. These documents are referenced by SKILL.md and provide detailed specifications beyond the main architecture documentation.

## Contents

### Implementation Plans

| Document | Purpose | Referenced By |
|-|-|-|
| `extractor_implementation_plan.md` | **Master document** for production extractor implementation. Contains API pricing, cost estimates, implementation timeline, and technical architecture. | SKILL.md Phase 15 |

### Historical Loss Analysis

| Document | Purpose | Coverage Areas |
|-|-|-|
| `historical_loss_analysis.md` | Case-by-case analysis of major insurance losses (2019-2024) demonstrating DSI's predictive power | FI, Marine, Energy, Aerospace |
| `signal_mapping_to_historical_loss.md` | Technical mapping of DSI signal paths to observable indicators from each case | All coverages |

These documents provide the evidence base for the "Recommended Signal Enhancements" section in SKILL.md.

### Cyber Retrospective Validation

| Document | Purpose | Cases Covered |
|-|-|-|
| `retrospective_case_study_detail.md` | Detailed cyber incident validation using pre-breach signals | SolarWinds, Colonial Pipeline, Equifax, Change Healthcare, 23andMe, MOVEit |
| `retrospective_case_study_executive_summary.md` | Executive summary of cyber validation results | Same 6 cases |
| `retrospective_methodology.md` | Methodology defense document for actuarial/regulatory review | N/A (methodology focus) |

These documents focus specifically on **Cyber coverage** validation, complementing the broader cross-coverage analysis in `docs/case_studies/retrospective_loss_case_studies.pdf`.

### Client Assessment Samples

| Document | Purpose | Companies Assessed |
|-|-|-|
| `client_assessment_samples.md` | Sample DSI assessments using real-world entities | Petrobras (Tier 2), PEMEX (Tier 4), Boeing (Tier 3) |

This document demonstrates how DSI scoring differentiates risk quality using externally observable signals.

## Document Relationships

```
SKILL.md (Architecture)
    │
    ├── Phase 15 ──→ extractor_implementation_plan.md (Master impl doc)
    │
    ├── Recommended Signal Enhancements ──→ historical_loss_analysis.md
    │                                    ──→ signal_mapping_to_historical_loss.md
    │
    └── Validation Evidence ──→ dsi_retrospective_*.md (Cyber)
                           ──→ dsi_client_assessment_samples.md (Sample clients)

docs/case_studies/retrospective_loss_case_studies.pdf
    ↑
    └── Supported by all development_docs historical analysis
```

### Coverage Expansion Specs & Templates

| Document | Purpose | Location |
|-|-|-|
| `project/templates/expansion_companion.md` | Template for prose companion docs for expansion phases | Templates |
| `project/version/4/phase_6_spec.yaml` | Reference expansion spec (PI, 11 configs, 58 signals) | Phase 6 |

**Expansion specs** are the machine-consumable input to the `CoverageExpansionGenerator`. They replace the manual process of transcribing phase docs into config YAML and signal code. See `infrastructure/builder/README.md` for full documentation.

**Companion docs** provide strategic rationale alongside the spec — design decisions, pricing philosophy, underwriting context.

## Usage

1. **For coverage expansion phases**: Author an expansion spec YAML, then run `python -m infrastructure.builder.cli expand --spec <path> --write`. See `infrastructure/builder/README.md` and `project/version/4/phase_6_spec.yaml` as reference.
2. **For extractor implementation**: Start with `extractor_implementation_plan.md`
3. **For methodology questions**: Reference `retrospective_methodology.md`
4. **For signal enhancement work**: See `historical_loss_analysis.md` and `signal_mapping_to_historical_loss.md`
5. **For validation evidence**: Use cyber retrospective documents and client assessments

## Updates

- March 2026: Added coverage expansion spec format and companion doc template
- January 2026: Initial organization of development documents
- November 2025: Original case study documents created

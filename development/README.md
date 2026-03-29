# Development Documentation

This folder contains internal planning documents and implementation guides that support DSI development. These documents are referenced by SKILL.md and provide detailed specifications beyond the main architecture documentation.

## Contents

### Implementation Plans

| Document | Purpose | Referenced By |
|-|-|-|
| `extractor_implementation_plan.md` | **Master document** for production extractor implementation. Contains API pricing, cost estimates, implementation timeline, and technical architecture. | SKILL.md, Deployment guidance |

### Coverage Expansion Specs & Phase Plans

| Document | Purpose | Location |
|-|-|-|
| `project/templates/expansion_companion.md` | Template for prose companion docs for expansion phases | Templates |
| `project/version/4/phase_6_spec.yaml` | PI expansion spec (11 configs, 58 signals) | Phase 6 |
| `project/version/4/phase_7_spec.yaml` | Cyber expansion spec (9 configs, ~70 signals) | Phase 7 |

**Expansion specs** are the machine-consumable input to the `CoverageExpansionGenerator`. See `infrastructure/builder/README.md` for full documentation.

### Utility Scripts

| Script | Purpose |
|-|-|
| `bundle_code.py` | Code bundling utility for context sharing |
| `bundle_pyfile.py` | Python file bundling utility |

## Usage

1. **For coverage expansion phases**: Author an expansion spec YAML, then run `python -m infrastructure.builder.cli expand --spec <path> --write`. See `infrastructure/builder/README.md` and `project/version/4/phase_6_spec.yaml` as reference.
2. **For extractor implementation**: Start with `extractor_implementation_plan.md`
3. **For project phase history**: See `project/version/` directories (versions 1-4)
4. **For validation evidence**: See `docs/case_studies/`

## Updates

- March 2026: Cleaned up completed validation docs. Coverage expansion specs for Phase 6 (PI) and Phase 7 (Cyber) complete.
- January 2026: Initial organization of development documents

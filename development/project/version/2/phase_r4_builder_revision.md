# Phase R4: Infrastructure Builder Revision

**Status:** ✅ Complete
**Parent Plan:** `dsi_restructure_plan.md`

## Objective

Overhaul the coverage builder to generate v2.0 compliant configurations that pass validation, with CLI tooling and metadata registry integration.

## Deliverables

- Builder generates full v2.0 configs: signal_registry, groups, risk/loss_tier_bands, nested exposure, pricing
- Validator rewritten for v2.0 schema (rejects v1.x flat structure)
- Score condition action enforcement (FLAG|MODIFIER|REFER; DECLINE tier-level only)
- Signal library integrated with metadata registry for proxy_tier validation
- CLI tool: build, validate, list-industries, list-signals
- 24 builder tests passing (structure, constraints, multi-industry, validation)
- Builder output passes its own validator; existing cyber config also passes

## Key Files

- `infrastructure/builder/coverage_builder.py` — Core builder (~550 lines)
- `infrastructure/builder/validator.py` — v2.0 schema validator (~500 lines)
- `infrastructure/builder/signal_library.py` — Signal groups + registry integration
- `infrastructure/builder/cli.py` — CLI interface
- `infrastructure/builder/types.py` — CoverageSpec, SignalSelection, etc.
- `infrastructure/builder/README.md` — Usage documentation
- `tests/unit/test_coverage_builder_v2.py` — 24 tests

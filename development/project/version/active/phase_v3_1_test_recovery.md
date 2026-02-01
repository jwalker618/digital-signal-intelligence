# Phase V3-1: Test Suite Recovery

**Status:** Not Started
**Priority:** Critical

## Problem

The test suite has significant rot from the restructure phases:
- 10 unit test files fail at collection time due to stale imports
- Missing modules referenced: `analytics`, `orchestration`, `SignalConfig`, `LimitBand`
- API test failures from incorrect `api.auth` module paths
- Loss workflow tests fail on `SeverityPropensityBand` enum casing (`'high'` vs `HIGH`)
- Only 54 tests pass (integration + performance + builder); 10 test files cannot even load

**Current passing:** 54 passed, 9 skipped (Rust not compiled)
**Current broken:** 10 test files with collection errors

## Objective

Restore all test files to passing state. Achieve minimum 60% test coverage on critical paths (workflow, scorer, pricer, config_manager).

## Tasks

1. Fix stale imports in 10 broken unit test files
2. Update test assertions for v2.0 types (score ranges, enum values, method signatures)
3. Fix API test auth module paths
4. Fix loss workflow SeverityPropensityBand casing
5. Add missing unit tests for scorer, pricer, workflow
6. Target: all tests passing, 60%+ coverage on layers/risk/

## Affected Files

- `tests/unit/test_scorer.py` — stale imports
- `tests/unit/test_pricer.py` — stale imports
- `tests/unit/test_workflow.py` — stale imports
- `tests/unit/test_analytics.py` — missing analytics types
- `tests/unit/test_builder.py` — old builder API
- `tests/unit/test_config_manager.py` — stale types
- `tests/unit/test_model_data.py` — stale types
- `tests/unit/test_multi_coverage.py` — orchestration imports
- `tests/unit/test_portfolio_analytics.py` — portfolio types
- `tests/integration/test_integrations.py` — integration imports

## Success Criteria

- All test files load without collection errors
- 80+ tests passing
- 60%+ coverage on `layers/risk/` package
- CI pipeline green

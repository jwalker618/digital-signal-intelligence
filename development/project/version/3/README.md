# DSI Active Development Plan

**Version:** 3 (Active)
**Date:** 2026-02-01
**Status:** IN PROGRESS

## Prior Versions

| Version | Description | Location | Status |
|---------|-------------|----------|--------|
| 1 | Original phases 1-23 (Foundation → Config Architecture) | `development/project/version/1/` | Complete |
| 2 | Restructure R1-R11 + Production Readiness P1-P7 | `development/project/version/2/` | Complete |
| **3** | **Production hardening, test coverage, continuous monitoring** | **`development/project/version/active/`** | **Active** |

## Context

Versions 1 and 2 built the DSI framework from concept to functional prototype:
- 7 coverage verticals with v2.0 compliant configs
- Three-layer assessment (risk/loss/exposure) operational
- Organisational graph with derivatives (entropy/velocity/drift)
- Rust accelerators for performance-critical paths
- API, database, observability, deployment pipeline
- Coverage builder producing validated configs

The framework can process submissions end-to-end. What remains is production hardening, test reliability, and delivering on the vision paper's promises around continuous monitoring and simulation.

## Active Phases

| Phase | Name | Status | Priority | Plan |
|-------|------|--------|----------|------|
| V3-1 | Test Suite Recovery | Not Started | Critical | `phase_v3_1_test_recovery.md` |
| V3-2 | Continuous Monitoring Pipeline | Not Started | High | `phase_v3_2_continuous_monitoring.md` |
| V3-3 | LLM Integration for Builder | Not Started | Medium | `phase_v3_3_llm_builder.md` |
| V3-4 | Production Signal Extractors | Not Started | Medium | `phase_v3_4_production_extractors.md` |
| V3-5 | Simulation Engine Foundation | Not Started | Medium | `phase_v3_5_simulation_engine.md` |
| V3-6 | Release v1.0.0 | Not Started | High | `phase_v3_6_release.md` |

## Dependency Graph

```
V3-1 (Test Recovery) ──────────────────────────┐
    │                                           │
    ├──► V3-2 (Continuous Monitoring)            │
    │        │                                  │
    │        └──► V3-5 (Simulation Engine)      ├──► V3-6 (Release v1.0.0)
    │                                           │
    ├──► V3-3 (LLM Builder)                     │
    │                                           │
    └──► V3-4 (Production Extractors) ──────────┘
```

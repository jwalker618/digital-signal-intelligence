# Changelog

All notable changes to the Digital Signal Intelligence project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.4.0] - 2026-03-24

### Added

- **Phase A: Foundation & Transparency**
  - `uncapped_premium` field on PricingResult and ModelVersion — captures pre-guardrail premium for audit trail
  - `LimitPremiumDetail` structured output replacing flat `Dict[str, float]` — stores discrete `ilf_factor` and `deductible_factor` per limit option
  - Modifier visibility — each modifier categorized with before/after premium tracking
  - `TierMarginContext` — distance to adjacent tier boundaries, percentile within current tier
  - Table-based ILF removed — parametric-only enforcement in schema and ILFCurve
  - Comprehensive unit tests for all Phase A features

- **Phase B: Scoring Completeness**
  - `evaluate_signal_conditions()` extended to process loss and exposure dimension score_conditions (previously only risk)
  - Exposure dimension breakdown surfaced — magnitude vs complexity scores persisted separately
  - Loss score fields clarified with semantic naming and individual frequency/severity trend fields
  - Unit tests for loss/exposure score_conditions and dimension breakdown output

- **Phase C: ROL Engine**
  - ROL curve validator (`layers/risk/rol_validator.py`) — replaces PremiumValidator, per-coverage ROL appetite bands
  - Dual recommendation engine (`layers/risk/rol_recommender.py`) — upper/lower ROL-optimal limit recommendations
  - Limit re-calculation method — reprice with different limit selection without re-running entire workflow
  - ConfigHealthGate updated to use ROL validator for boot-time config validation
  - PremiumValidator removed entirely
  - Comprehensive unit tests for ROL validator, dual recommender, and re-calculation

- **Phase D: Config Strictness & Cleanup**
  - `extra="forbid"` added to key Pydantic schema models — unknown YAML fields now rejected
  - Comparison operators standardized — aliases removed, single canonical form enforced
  - Cross-coverage field consistency validation in builder/validator
  - All 7 coverage config YAML files cleaned up to pass strict validation

- **Phase E: Tower & Subscription Market Structure**
  - Tower (excess-of-loss) layer support: `TOWER` type in `LimitConfigType`, `TowerLayer` model with attachment/limit
  - Multi-layer pricing engine: tower pricing via `ILF(attachment + limit) - ILF(attachment)` from existing cumulative curves
  - Bespoke tower support: arbitrary attachment/limit combinations with validation (ordering, overlap, ILF range)
  - Subscription market: `SUBSCRIPTION` type with order/line model, `SubscriptionOrder` and `SubscriptionLine` models
  - Lead/follow role: `LineRole` enum, configurable lead loading factor
  - `LayerPremiumDetail` output type — per-layer ILF differentials, order/line premiums, lead/follow roles
  - `DualRecommendation` extended with `structure_type`, `layers`, `signed_line`, `role` fields
  - Design document: `development/project/phase_e_design.md`
  - Phase E seed script demonstrations

### Changed
- Config schema version updated to v2.3 (added `expectation_level`, tower/subscription types, strict validation)
- Pricing engine (`pricer.py`) now polymorphic for ground-up, tower, and subscription limit configurations
- ConfigHealthGate uses ROL validator instead of PremiumValidator
- All coverage configs pass strict `extra="forbid"` schema validation

### Removed
- PremiumValidator (replaced by ROL curve validator)
- Table-based ILF support (parametric-only)
- `_EXPOSURE_BANDS` display table (dual-exposure disconnect eliminated)

## [0.3.0] - 2026-02-21

### Added
- **Architecture Restructuring** (Phase 18)
  - Extracted signals to `signal_architecture/` as shared infrastructure
  - Created `layers/` directory for risk, exposure, and loss assessment layers
  - Updated all imports from `technical_pricing/` to new package structure

- **Three-Layer Assessment Architecture** (Phases 20-22)
  - Unified signal definitions with `risk:`, `loss:`, `exposure:` subsections in all 7 coverage configs
  - Loss Correlation Layer: loss config adapter, tier band mapping, frequency/severity propensity
  - Exposure Shadow Layer: exposure scorer, magnitude/band assessment, complexity categories
  - All 7 coverage configs updated with proxy_tier, correlation_direction, loss/exposure dimensions

- **Organisational Graph Runtime** (Phase 23/R8)
  - 6 node types, 6 edge types, 5 derivatives (entropy, velocity, drift, concentration, fragility)
  - PageRank propagation, risk propagation, exposure aggregation algorithms
  - Graph builder pipeline: node factory, edge inferencer, storage

- **Multi-Configuration Multiplexer** (Phase V4)
  - DSIMultiplexer signal broker with deduplication and parallel execution
  - ConfigArbiter ranking: validity, confidence, specificity, margin
  - Schema additions: model_specificity, routing_constraints
  - 16 unit tests covering broker, arbiter, constraints, integration

- **Rust Performance Modules** (R9)
  - `rust/dsi-core/`: PyO3 crate with PageRank, derivatives, config validation
  - `rust/dsi-sim/`: Simulation engine with portfolio, shock, formula modules
  - Release builds with LTO optimisation

- **Production Readiness** (P1-P7)
  - Lazy imports in `infrastructure/__init__.py` (no hard FastAPI dependency)
  - Alembic migrations with 8-table initial schema, lazy DB engine singletons
  - Dual storage: DB persistence with in-memory fallback
  - Unified extractor resolver: stub/production/hybrid modes via `FEATURE_USE_STUBS`
  - 21 E2E integration tests (full pipeline: submission, scoring, tier, decision)
  - Structured JSON logging with correlation IDs, Prometheus metrics instrumentation
  - Rate limiting middleware (in-memory + Redis backends, per-API-key tiers)
  - CI/CD pipeline: Rust build, integration tests, Docker build+push, staging/prod deploy
  - Performance benchmarks: workflow ~80ms, scoring ~12ms, graph build <1ms

- **Coverage Builder v2.0 Overhaul**
  - Builder generates v2.0 compliant configs (signal_registry, three_layer_assessment, groups, tiers)
  - Validator aligned with v2.0 schema (rejects v1.x flat structure)
  - Signal library integrated with metadata registry
  - CLI tool: `python -m infrastructure.builder.cli build|validate|list-industries|list-signals`
  - 24 builder tests passing

- **Deployment Infrastructure**
  - Dockerfile with multi-stage build, non-root user, health checks
  - Production Docker Compose (API + PostgreSQL + Redis + optional Nginx)
  - Kubernetes manifests: namespace, deployment, service, ingress, HPA, configmap, secrets
  - Prometheus config with alert rules, Grafana dashboard
  - GitHub Actions CI/CD: lint, test (Python 3.10-3.12), Rust build, Docker push, deploy

### Changed
- Restructured from `technical_pricing/` to `signal_architecture/`, `infrastructure/`, `layers/`
- Coverage configs upgraded from v1.x to v2.0 structure (banded score_conditions, loss/exposure tier bands)
- All 7 coverage configs rebuilt with consistent structure
- Updated documentation (README.md, SKILL.md, CONTRIBUTING.md, deploy guides)

## [0.2.0] - 2025-12-28

### Added
- **Technical Pricing Architecture** (`technical_pricing/`)
  - Complete signal extraction framework with Extractor → Aggregator → Categorizer pipeline
  - Model layer implementing the 14-step workflow
  - Coverage configurations for 7 insurance lines (aerospace, cyber, D&O, energy, FI, marine, PI)
  - Inference registry for connecting YAML configs to Python implementations
  - Content-addressable configuration storage pattern

- **Model Layer Components** (`technical_pricing/model/`)
  - `types.py` - Comprehensive type definitions for the workflow
  - `config_manager.py` - YAML config loading, hashing, and validation
  - `model_data.py` - Model version tracking and audit trail
  - `scorer.py` - Signal extraction and composite score calculation (Steps 4-6)
  - `query_evaluator.py` - Direct query evaluation (Step 7)
  - `pricer.py` - Premium calculation with modifiers and limit bands (Steps 8-12)
  - `workflow.py` - Complete 14-step workflow orchestration

- **Discovery Module** (`technical_pricing/discovery/`)
  - Website discovery engine for entity identification
  - Batch processing support
  - Corporate registry integration framework

- **Comprehensive Test Suite** (`technical_pricing/tests/`)
  - Unit tests for all model layer components
  - Integration tests with test profile scenarios
  - Happy path, referral flow, tier override, and edge case coverage

### Changed
- Restructured project to use `technical_pricing/` as the main package
- Updated CI/CD pipeline for new architecture
- Simplified dependencies to core requirements
- Bumped minimum Python version to 3.10

### Removed
- Legacy `models/` directory (functionality replaced by `technical_pricing/`)
- Legacy `api/` directory (to be reimplemented for new architecture)
- Legacy `workflow/` directory (replaced by `technical_pricing/model/workflow.py`)
- Legacy `tests/` directory (replaced by `technical_pricing/tests/`)

## [0.1.0] - 2025-11-22

### Added
- Initial release of Digital Signal Intelligence pricing models
- Cyber Insurance Pricing Model
  - 28 security signal metrics
  - 5-tier risk classification
  - 3 coverage types (First-Party, Third-Party, Comprehensive)
- Energy Sector Pricing Model
  - 24 digital signal metrics
  - 3 segment models (Upstream, Midstream, Downstream)
- Financial Institutions Pricing Model
  - 36 specialized signals across 6 categories
  - 10 institution types supported
- Portfolio Analytics Module
- Documentation and case studies

---

## Version History Summary

| Version | Date | Description |
|---------|------|-------------|
| 0.4.0 | 2026-03-24 | Phases A-E: pricing transparency, ROL engine, config strictness, tower/subscription markets |
| 0.3.0 | 2026-02-21 | Three-layer assessment, production readiness, deployment infrastructure |
| 0.2.0 | 2025-12-28 | Architecture refactor with technical_pricing |
| 0.1.0 | 2025-11-22 | Initial release with 3 pricing models |

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for details on our development process.

# Changelog

All notable changes to the Digital Signal Intelligence project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
| 0.2.0 | 2025-12-28 | Architecture refactor with technical_pricing |
| 0.1.0 | 2025-11-22 | Initial release with 3 pricing models |

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for details on our development process.

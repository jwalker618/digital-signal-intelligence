# Phase P3: Production Extractor Wiring

**Status:** Complete
**Parent Plan:** `production_readiness_plan.md`

## Objective

Create a unified extractor resolver that supports stub, production, and hybrid modes, controlled by environment configuration, enabling seamless switching between test stubs and real data sources.

## Deliverables

- Unified extractor resolver supporting three modes: stub, production, and hybrid
- `FEATURE_USE_STUBS` environment variable for mode selection
- Factory pattern mapping extractor names to their concrete implementations
- Clean separation between stub extractors (for testing) and production extractors (for live data)

## Key Files

- `signal_architecture/discovery/website_discovery.py`

## Notes

The hybrid mode allows running with a mix of real and stub extractors, which is useful during incremental rollout of new data sources or when specific external services are unavailable.

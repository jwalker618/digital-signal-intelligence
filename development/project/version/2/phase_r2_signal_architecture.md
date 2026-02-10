# Phase R2: Signal Architecture Alignment

**Status:** ✅ Complete
**Parent Plan:** `dsi_restructure_plan.md`

## Objective

Align inference functions, metadata, and normalisers to the v2.0 config schema. Create a centralised signal metadata registry covering all signals across all 7 coverages.

## Deliverables

- Signal metadata registry with per-signal: proxy_tier, category, TTL, required extractors, output type, coverage applicability
- All inference function names corrected (21 typos fixed across 6 configs)
- Proxy tier classification (DIRECT_OBSERVABLE, INFERRED_PROXY, COHORT_INFERENCE) for every signal
- Cross-coverage signal reuse identification
- Signal validation against registry at config load time

## Key Files

- `signal_architecture/signals/inference/metadata_registry.py` — Central registry (~1300 lines, all 7 coverages + cross-coverage)
- `signal_architecture/orchestration/aggregator.py` — Signal aggregation pipeline
- `signal_architecture/orchestration/locale_detection.py` — Locale-aware signal routing

# World Engine: Integration Summary & Dependency Chain

| Item | Value |
|------|-------|
| Version | 1.1 |
| Date | April 2026 |
| Classification | Master Reference |

---

## Refinements from v1.0

This v1.1 plan addresses 8 gaps identified in review against the Architecture Specification and Pricing & Portfolio Addendum:

| # | Gap | Resolution | Phase |
|---|-----|------------|-------|
| 1 | Drift Alerts missing as first-class concept | Added `DriftAlert` type, `we_drift_alerts` table, `/drift-alerts` API, `DriftDetector` subsystem | WE-1, WE-3e |
| 2 | Population-level outputs not addressed | Added `PopulationIntelligence` class: cohort evolution, regime detection, predictive horizon, cross-coverage | WE-3f |
| 3 | Maturity model has no runtime enforcement | Added `MaturityEvaluator`, `MaturityState` type, capability gating throughout | WE-1b, WE-3g, WE-4a |
| 4 | Portfolio concentration does not feed back into CAF | Added `PortfolioCafEnricher` -- concentration loading with cap, activates at SIMULATE maturity | WE-5d |
| 5 | Missing intermediate types in WE-1 | Added `CandidateRelationship`, `DirectedCandidate`, `ValidationResult`, `StabilityResult`, `PredictiveResult`, `ScanRunReport` | WE-1a |
| 6 | Autonomous constraint widening has no mechanism | Added `ConstraintCalibrator` with absolute guardrails ([0.60, 2.00]), gradual step widening, backtesting requirement | WE-4b |
| 7 | Population-level consistency aggregation missing | Added `PopulationConsistencyAggregator` batch process, `we_population_consistency` table | WE-2b |
| 8 | Marginal portfolio impact missing | Added `MarginalImpactAnalyser`, `/marginal-impact` POST endpoint | WE-5e |

**Practical implementation clarifications**:
- Granger causality uses pooled panel approach (cross-entity first-differences), valid with 2+ assessments per entity if 50+ entities
- WE-2 <50ms achieved via scipy `pdist` vectorised operations on pre-computed score arrays
- WE-5 Portfolio Graphs are pre-computed in batch and cached, not built per-request

---

## Phase Dependency Chain

```
WE-1 (Foundation)
  |
  +---> WE-2 (Consistency Scorer)
  |       |
  +---> WE-3 (Discovery & Validation)  [parallel with WE-2]
          |
          +---> WE-4 (Causal Graph Pricing)
          |
          +---> WE-5 (Portfolio Intelligence)  [parallel with WE-4]
                  |
                  +---> WE-5d (Concentration -> CAF feedback)  [requires WE-4]
```

WE-2 and WE-3 can run in parallel after WE-1. WE-4 and WE-5 can run in parallel after WE-3. WE-5d (concentration CAF enrichment) requires WE-4 to be complete.

---

## Maturity Gating

| Capability | Minimum Stage | Rationale |
|------------|---------------|-----------|
| Consistency scoring (inline) | SEED | Works from first assessment |
| Population consistency (batch) | SEED | Aggregates individual scores |
| Discovery pipeline | LEARN | Requires 500+ entities, 6+ months |
| CAF computation | EMERGE | Requires active relationships |
| CAF constraint widening | EMERGE + 12 months | Requires proven predictive accuracy |
| Portfolio concentration | EMERGE | Requires active relationships for pathway detection |
| Scenario simulation | SIMULATE | Requires mature causal graph |
| Concentration-aware CAF | SIMULATE | Requires validated portfolio intelligence |
| Marginal impact analysis | EMERGE | Requires concentration detection |

---

## Estimated Effort

| Phase | Backend | Frontend | Total |
|-------|---------|----------|-------|
| WE-1: Foundation | 1-2 weeks | -- | 1-2 weeks |
| WE-2: Consistency | 1 week | 3-4 days | ~2 weeks |
| WE-3: Discovery | 3-4 weeks | -- | 3-4 weeks |
| WE-4: CAF | 2-3 weeks | 1 week | 3-4 weeks |
| WE-5: Portfolio | 4-5 weeks | 2 weeks | 6-7 weeks |
| **Total** | | | **16-20 weeks** |

Note: WE-4 and WE-5 estimates increased slightly vs v1.0 due to constraint widening and marginal impact additions.

---

## Cross-Workstream Integration Points

| WE Phase | Other Workstream | Integration |
|----------|------------------|-------------|
| WE-1 | A-1 (Auth) | Registry API should be permission-gated when auth exists |
| WE-2 | B-1 (System Health) | Population consistency metrics in admin dashboard |
| WE-3 | B-1 (System Health) | Scan run history, drift alerts in admin dashboard |
| WE-4 | B-1 (System Health) | CAF distribution metrics, constraint regime in admin |
| WE-4 | C-2 (Recalibration) | CAF accuracy data feeds recalibration engine |
| WE-5 | A-1 (Auth) | Portfolio Dashboard permission-gated |
| WE-5 | B-1 (System Health) | Portfolio health metrics in admin |

These integrations are noted but not blocking. WE phases can proceed independently of Workstreams A/B/C, with integration hooks added when the other workstreams are ready.

---

## New Files Summary

| Phase | New Files |
|-------|-----------|
| WE-1 | `world_engine/__init__.py`, `types.py`, `maturity.py`, `registry/{__init__,store,api,types}.py`, placeholder `__init__.py` for 8 subdirectories |
| WE-2 | `world_engine/consistency/scorer.py`, `population.py` |
| WE-3 | `world_engine/scanner/correlation_scanner.py`, `inferencer/{granger,confound_control}.py`, `validator/{holdout,stability,predictive}.py`, `lifecycle/manager.py`, `drift/detector.py`, `population/intelligence.py`, `scheduler.py` |
| WE-4 | `world_engine/causal_pricing/{engine,trajectory,constraints}.py` |
| WE-5 | `world_engine/portfolio/{graph_builder,types,concentration,caf_enrichment,marginal_impact,simulation}.py` |

## Modified Files Summary

| Phase | Modified Files |
|-------|---------------|
| WE-1 | `infrastructure/api/main.py` (router mount, health check) |
| WE-2 | `layers/risk/workflow.py`, `layers/risk/types.py`, `infrastructure/api/types.py`, `seed_dsi_bench.py`, frontend (SummaryTab, dsiStore) |
| WE-4 | `layers/risk/workflow.py`, `layers/risk/pricer.py`, `layers/risk/types.py`, `infrastructure/db/models.py`, `infrastructure/api/types.py`, `seed_dsi_bench.py`, frontend (PremiumAssemblyTab) |
| WE-5 | `infrastructure/models/commercial_schema.py`, `layers/risk/workflow.py`, `seed_dsi_bench.py`, frontend (new portfolio route) |

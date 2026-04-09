# Phase WE-3: Discovery & Validation Pipeline

| Item | Value |
|------|-------|
| Version | 1.1 |
| Depends on | WE-1, WE-2 |

---

## Overview

The autonomous offline process that discovers emergent cross-signal causal relationships, validates them statistically, manages their lifecycle, detects structural drift, and produces population-level intelligence outputs. This is the core intelligence engine. It operates as a batch process, completely separate from the real-time pricing pipeline.

## Current State

No discovery, validation, or drift detection capability exists. The intelligence registry (WE-1) and consistency scorer (WE-2) provide the foundation.

## Target State

A fully autonomous batch pipeline that: mines assessment data for cross-signal relationships, validates them, manages lifecycle without human intervention, detects structural drift in the signal landscape, and publishes population-level intelligence (cohort evolution, regime detection, predictive horizon, cross-coverage insights).

---

## Implementation Plan

### WE-3a: Correlation Scanner

**New file**: `world_engine/scanner/correlation_scanner.py`

```python
class CorrelationScanner:
    """Mines the assessment database for cross-signal correlations."""

    def scan(self, min_entities: int = 50) -> list[CandidateRelationship]:
        """
        1. Load all signal scores from assessment database (ModelVersionSignal)
        2. Build entity x signal matrix (entities as rows, signals as columns)
        3. Coverage-agnostic: entity assessed for Cyber+D&O contributes both
        4. For each signal pair, compute Spearman's rho (scipy.stats.spearmanr)
        5. Filter: |rho| > 0.3, p < 0.01
        6. Exclude same-group pairs (designed to correlate)
        7. Return candidates with full statistical evidence
        """
```

**Design decisions**:
- Coverage-agnostic: cross-coverage correlations are the highest-value discoveries
- Spearman's rho: handles non-linear monotonic relationships without normality assumption
- Same-group exclusion: signals in same group share weights, correlation is by design

### WE-3b: Causal Inferencer

**New file**: `world_engine/inferencer/granger.py`

```python
class CausalInferencer:
    """Determines causal direction for correlated signal pairs."""

    def infer(self, candidates: list[CandidateRelationship]) -> list[DirectedCandidate]:
        """
        Pooled panel Granger causality (not per-entity time series).
        Entities with >= 2 assessments provide first-difference observations.
        With 50+ entities this gives sufficient statistical power.

        For each candidate:
        1. Load time-series data for both signals across all entities
        2. Pool first-differences across entities
        3. Apply Granger causality test (statsmodels) in both directions
        4. Assign direction: A->B, B->A, bidirectional, or contemporaneous
        5. Estimate lag from optimal lag order
        """
```

**New file**: `world_engine/inferencer/confound_control.py`

```python
class ConfoundController:
    """Eliminates spurious relationships explained by confounders."""

    CONFOUNDERS = ["entity_size_band", "industry_code", "geography", "assessment_vintage"]

    def filter(self, candidates: list[DirectedCandidate]) -> list[DirectedCandidate]:
        """
        Partial correlation (statsmodels) controlling for each confounder.
        Discard if |partial_rho| < 0.2 after controlling. Record which tested.
        """
```

### WE-3c: Validation Engine

**New files**:
- `world_engine/validator/holdout.py` -- `HoldoutValidator`: 70/30 split, replicate |rho| > 0.2, p < 0.05
- `world_engine/validator/stability.py` -- `TemporalStabilityTracker`: rolling window persistence, min 3 consecutive windows, sign-flip detection
- `world_engine/validator/predictive.py` -- `PredictiveValidator`: track entities where precursor crossed threshold, check if target follows within lag window, compute hit rate

### WE-3d: Lifecycle Manager

**New file**: `world_engine/lifecycle/manager.py`

```python
class LifecycleManager:
    """Autonomous state machine for relationship lifecycle."""

    PROMOTION_CRITERIA = {
        "candidate_to_provisional": {
            "holdout_rho_min": 0.2,
            "holdout_p_max": 0.05,
            "stability_windows_min": 3,
        },
        "provisional_to_active": {
            "predictive_hit_rate_min": 0.6,
            "effect_size_min": 0.3,
            "min_age_months": 6,
        },
        "active_to_deprecated": {
            "predictive_hit_rate_below": 0.4,
            "consecutive_windows_below": 3,
        },
    }

    def evaluate_all(self) -> list[StateTransition]:
        """
        All transitions autonomous. No human gate.
        - CANDIDATE: holdout + stability -> PROVISIONAL or discard
        - PROVISIONAL: predictive validation -> ACTIVE or demote
        - ACTIVE: ongoing predictive power -> maintain or deprecate
        - DEPRECATED: re-discovered in latest scan -> potentially re-promote
        """
```

### WE-3e: Drift Detection

**New file**: `world_engine/drift/detector.py`

```python
class DriftDetector:
    """Detects structural changes in the signal landscape."""

    def detect(self, current_scan: ScanRunReport, registry: IntelligenceRegistry) -> list[DriftAlert]:
        """
        Four detection modes:
        1. Relationship shift: Active relationship's rho changed > 0.15 since last scan
        2. Correlation inversion: Sign flip in a previously stable correlation
        3. Signal regime change: Significant shift in a signal's population distribution
           (KS test, p < 0.01 between current and historical distribution)
        4. Emergence burst: Unusually high number of new candidates in a single scan
           (> 2 std devs above historical mean)

        Each produces a DriftAlert stored via registry.store_drift_alert().
        """
```

### WE-3f: Population-Level Intelligence

**New file**: `world_engine/population/intelligence.py`

```python
class PopulationIntelligence:
    """Produces population-level outputs from accumulated assessment data."""

    def compute_cohort_evolution(self) -> dict:
        """Track how signal-derived peer groups change over time."""

    def detect_signal_regimes(self) -> list[DriftAlert]:
        """Has the relationship structure between signals changed?
        Compares correlation matrices across time windows."""

    def estimate_predictive_horizon(self) -> dict:
        """How far in advance can validated relationships predict?
        Analyses lag distributions of active relationships."""

    def summarise_cross_coverage(self) -> dict:
        """Relationships spanning different coverage lines.
        Groups active relationships by coverage pair."""
```

These outputs are stored as structured JSON in the registry and exposed via the `/stats` endpoint.

### WE-3g: Scheduler

**New file**: `world_engine/scheduler.py`

```python
class WorldEngineScheduler:
    """Orchestrates the discovery-validation-lifecycle pipeline."""

    def run_cycle(self) -> ScanRunReport:
        """
        1. Check maturity -- refuse to run discovery at SEED stage
        2. CorrelationScanner.scan() -> candidates
        3. CausalInferencer.infer() -> directed candidates
        4. ConfoundController.filter() -> cleaned candidates
        5. HoldoutValidator.validate() -> validated candidates
        6. Registry.register_candidate() for survivors
        7. LifecycleManager.evaluate_all() -> state transitions
        8. DriftDetector.detect() -> drift alerts
        9. PopulationIntelligence (all four outputs)
        10. Store ScanRunReport for audit
        """

    def should_run(self) -> bool:
        """
        Run if:
        - Maturity >= LEARN
        - AND (new assessments since last run > 100 OR time since last run > 7 days)
        - AND min population met (50 entities with >= 2 assessments)
        """
```

### WE-3h: Unit Tests

**New directory**: `tests/unit/test_world_engine/`

| Test File | Tests |
|-----------|-------|
| `test_correlation_scanner.py` | Synthetic data with known correlations; verify detection and filtering |
| `test_granger.py` | Synthetic time series with known causality; verify direction (pooled panel approach) |
| `test_confound_control.py` | Synthetic data with known confounders; verify elimination |
| `test_holdout.py` | Split validation with known replicable/non-replicable relationships |
| `test_lifecycle.py` | State machine transitions with mocked validation results |
| `test_drift_detector.py` | Synthetic regime changes; verify alert generation |
| `test_scheduler.py` | Full pipeline with synthetic data; maturity gating |

---

## Constraints

1. No impact on real-time pipeline -- entire phase runs as offline batch
2. Use `scipy.stats` for Spearman/Granger, `statsmodels` for partial correlation. No custom statistics.
3. Scanner refuses to run with < 50 entities with temporal data
4. Scheduler refuses to run at SEED maturity stage
5. Audit everything: every scan run, candidate, transition, drift alert persisted with full evidence

## Success Criteria

1. Scanner discovers known correlations in synthetic seeded data
2. Lifecycle manager correctly promotes/demotes based on evidence thresholds
3. Drift detector raises alerts for synthetic regime changes
4. Population intelligence outputs are computed and stored
5. Full pipeline runs end-to-end on seed data without errors
6. Maturity gating prevents discovery at SEED stage
7. All transitions recorded in `we_state_transitions` with evidence
8. No changes to existing pricing, scoring, or assessment code

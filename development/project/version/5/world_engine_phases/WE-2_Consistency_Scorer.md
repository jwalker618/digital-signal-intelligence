# Phase WE-2: Consistency Scorer

| Item | Value |
|------|-------|
| Version | 1.1 |
| Depends on | WE-1 |

---

## Overview

First operational subsystem. Computes cross-signal and cross-layer consistency for every assessment inline, plus population-level aggregates in batch. Produces immediate anti-gaming value and generates structured divergence data that the discovery engine (WE-3) requires.

## Current State

The three-layer assessment runs in parallel (risk, exposure, loss) on the same signals with different weights (`layers/risk/workflow.py`). No system measures whether layers agree or whether signals within/across categories tell a consistent story.

## Target State

- Every assessment produces a `ConsistencyScore` stored in the registry (inline, non-blocking)
- Population-level consistency aggregates computed in batch and stored
- ConsistencyCard visible in the frontend workbench

---

## Implementation Plan

### WE-2a: Consistency Computation Engine

**New file**: `world_engine/consistency/scorer.py`

```python
class ConsistencyScorer:
    """Computes intra-assessment consistency metrics."""

    WEIGHTS = {"signal_pair": 0.3, "cross_group": 0.4, "cross_layer": 0.3}

    def score(self, assessment: AssessmentResult) -> ConsistencyScore:
        """
        1. Signal-pair consistency: normalised distance between scores within
           same group. Divergence beyond threshold flagged. Output: per-pair 0-1.
        2. Cross-group consistency: normalised distance between group composites.
           Independent groups (e.g. Network Authority vs Public Records) weighted
           higher -- agreement between independent sources = strong evidence.
        3. Cross-layer consistency: compare risk tier, exposure band, loss band.
           Tier 1 risk + High loss propensity = significant gap (informative, not wrong).
        4. Overall: weighted average per WEIGHTS dict.
        """
```

**Implementation note**: Use numpy vectorised operations on the signal score arrays. For ~400 signals, the pairwise matrix is ~80K pairs; with vectorised `pdist` from scipy this completes in <5ms. The <50ms constraint is achievable.

### WE-2b: Population-Level Aggregation

**New file**: `world_engine/consistency/population.py`

```python
class PopulationConsistencyAggregator:
    """Batch computation of population-level consistency metrics."""

    def aggregate(self, coverage: str | None = None, period: str | None = None) -> dict:
        """
        Queries we_consistency_scores and computes:
        - Mean/median/P10/P90 consistency by coverage
        - Mean consistency by industry, geography
        - Consistency trend over time (rolling windows)
        - Most common divergent signal pairs across population
        - Cross-layer disagreement frequency distribution
        """
```

Scheduled to run daily or on-demand. Results stored in `we_population_consistency` table.

### WE-2c: Inline Integration

**File to modify**: `layers/risk/workflow.py`

After three-layer assessment completes (Steps 5a/5b/5c) and before pricing (Step 8), insert a non-blocking consistency scoring step:

```python
# After three-layer assessment
try:
    consistency_scorer = ConsistencyScorer()
    consistency_score = consistency_scorer.score(assessment_result)
    registry.store_consistency_score(consistency_score)
    assessment_result.consistency_score = consistency_score.overall_consistency
    assessment_result.divergent_pairs = consistency_score.divergent_pairs
except Exception:
    assessment_result.consistency_score = None  # Graceful degradation
```

### WE-2d: Assessment Output Extension

**Files to modify**:
- `layers/risk/types.py` -- Add `consistency_score: float | None` and `divergent_pairs: list[str] | None` to `WorkflowResult`
- `infrastructure/api/types.py` -- Add consistency fields to API response schemas

### WE-2e: Frontend -- Consistency Display

**New file**: `frontend/src/components/submissions/Workbench/ConsistencyCard.tsx`

Displays:
1. Overall consistency gauge (0-1): green >0.8, amber 0.5-0.8, red <0.5
2. Divergent pairs listed with specific signals and scores
3. Cross-layer summary: mini-table of risk tier vs exposure band vs loss band with agreement/divergence indicators

**Files to modify**:
- `frontend/src/components/submissions/Workbench/SummaryTab.tsx` -- Add ConsistencyCard
- `frontend/src/stores/dsiStore.ts` -- Add consistency score to store

### WE-2f: Seed Script

**File to modify**: `seed_dsi_bench.py`

Run consistency scoring for all seeded assessments, populating `we_consistency_scores`. Run population aggregation once to populate `we_population_consistency`.

---

## Constraints

1. Consistency scoring must add <50ms to assessment time
2. Failure must not block the assessment pipeline
3. No changes to scoring logic, tier assignment, or pricing

## Success Criteria

1. Every seeded assessment has a consistency score in the database
2. Population aggregates computed and queryable via registry API
3. ConsistencyCard renders in frontend with real data
4. Divergent pairs correctly identified for assessments with known disagreements
5. Assessment pipeline latency increase <50ms
6. All existing tests pass unchanged

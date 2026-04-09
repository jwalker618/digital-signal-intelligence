# Phase WE-4: Causal Graph Pricing (CAF)

| Item | Value |
|------|-------|
| Version | 1.1 |
| Depends on | WE-1, WE-3 (at least partially -- active relationships in registry) |

---

## Overview

The parallel pricing track. For every assessment, the World Engine evaluates the entity against the validated causal graph and produces a Causal Adjustment Factor (CAF) that enters the premium formula as a multiplicative adjustment: `P_final = P_static x CAF`. Includes an autonomous constraint widening mechanism with guardrails.

## Current State

The pricing formula is: `P = (B x R) x ILF x D x M_risk x M_loss x M_exp`

All modifiers computed inside the pricing engine from YAML-configured bands (`layers/risk/pricer.py`). `ModelPricer.price_submission()` returns a `PricingResult`. No mechanism for external intelligence to influence the premium.

## Target State

Formula becomes: `P = (B x R) x ILF x D x M_risk x M_loss x M_exp x CAF`

CAF computed by the World Engine, arrives at the pricing engine as an external input, appears as a distinct line item in the premium audit trail. When the Engine has no active relationships, is below EMERGE maturity, or has insufficient confidence, CAF defaults to 1.0.

---

## Implementation Plan

### WE-4a: Causal Pricing Engine

**New file**: `world_engine/causal_pricing/engine.py`

```python
class CausalPricingEngine:
    """Computes the Causal Adjustment Factor for an entity assessment."""

    def __init__(self, registry: IntelligenceRegistry):
        self.registry = registry
        self.constraints = self._load_active_constraints()

    def compute_caf(
        self,
        entity_id: str,
        signal_scores: dict[str, float],
        derivative_values: dict[str, float],
        current_tier: int,
        tier_rates: dict[int, float],
        policy_period_months: int = 12,
    ) -> CausalAdjustmentFactor:
        """
        1. Check maturity >= EMERGE; if not, return neutral CAF
        2. Query registry for active relationships matching entity's signals
        3. If < MIN_RELATIONSHIPS matched, return neutral CAF
        4. Evaluate precursor state for each relationship
        5. Synthesise tier migration trajectory (TrajectoryEngine)
        6. Compute CAF from trajectory
        7. Apply constraints (floor, cap, confidence gate)
        8. Return with full provenance chain
        """

    def _load_active_constraints(self) -> dict:
        """Load current constraint regime from we_constraint_history."""
```

**New file**: `world_engine/causal_pricing/trajectory.py`

```python
class TrajectoryEngine:
    """Synthesises forward risk trajectory from precursor evaluations."""

    def compute_trajectory(
        self,
        precursors: list[PrecursorEvaluation],
        current_tier: int,
        policy_period_months: int,
    ) -> TierMigrationDistribution:
        """
        Each precursor implies P(target signal degradation).
        Map degradation to composite score impact.
        Map composite impact to tier migration probability.
        Combine independent precursors using probability union.
        """
```

### WE-4b: Autonomous Constraint Widening

**New file**: `world_engine/causal_pricing/constraints.py`

```python
class ConstraintCalibrator:
    """Autonomously widens CAF constraints based on demonstrated accuracy."""

    # Hard guardrails -- these NEVER change regardless of evidence
    ABSOLUTE_FLOOR = 0.60       # Maximum 40% credit -- prevents gross underpricing
    ABSOLUTE_CAP = 2.00         # Maximum 100% loading -- prevents pricing out of market
    ABSOLUTE_CONFIDENCE_MIN = 0.4  # Never apply CAF with confidence below this

    # Initial constraints (effective at EMERGE stage)
    INITIAL_FLOOR = 0.80
    INITIAL_CAP = 1.50
    INITIAL_CONFIDENCE_GATE = 0.6
    INITIAL_MIN_RELATIONSHIPS = 2

    # Widening criteria
    WIDENING_CRITERIA = {
        "min_active_relationships": 10,       # Need broad evidence base
        "min_predictive_accuracy": 0.70,      # 70% aggregate hit rate
        "min_evaluation_months": 12,          # 12 months of CAF history
        "min_caf_evaluations": 500,           # Statistical significance
        "max_constraint_hit_rate": 0.25,      # > 25% hitting floor/cap = too tight
    }

    # Step sizes -- constraints widen gradually
    FLOOR_STEP = 0.05           # Floor drops by 0.05 per calibration (0.80 -> 0.75 -> 0.70...)
    CAP_STEP = 0.10             # Cap rises by 0.10 per calibration (1.50 -> 1.60 -> 1.70...)

    def evaluate_widening(self, registry: IntelligenceRegistry) -> dict | None:
        """
        Returns proposed new constraints if criteria met, else None.
        Checks:
        1. All WIDENING_CRITERIA thresholds met
        2. Proposed new values within ABSOLUTE bounds
        3. Backtested: rerun CAF on historical assessments with proposed
           constraints, verify no pathological outcomes
        4. Store decision + evidence in we_constraint_history
        """
```

Every constraint change is recorded in `we_constraint_history` with the full evidence that triggered it. The `ABSOLUTE_*` guardrails are code constants that prevent any autonomous process from producing unrealistic pricing.

### WE-4c: Pricing Engine Integration

**Files to modify**:
- `layers/risk/workflow.py` -- Add CAF computation after three-layer assessment, before pricing
- `layers/risk/pricer.py` -- Accept `caf_value: float = 1.0` parameter, multiply into final premium
- `layers/risk/types.py` -- Add `caf_value`, `caf_confidence`, `caf_detail` to `WorkflowResult`
- `infrastructure/db/models.py` -- Add `caf_value`, `caf_confidence`, `caf_constrained` to `ModelVersionRecord`

In `workflow.py` (after three-layer assessment, before pricing):
```python
try:
    maturity = registry.get_maturity_state()
    if maturity.capabilities.get("caf"):
        causal_engine = CausalPricingEngine(registry)
        caf_result = causal_engine.compute_caf(...)
        registry.store_caf(caf_result)
    else:
        caf_result = CausalAdjustmentFactor.neutral()
except Exception:
    caf_result = CausalAdjustmentFactor.neutral()
```

In `pricer.py`:
```python
# Existing
final_premium = base_premium * ilf * ded_factor * m_risk * m_loss * m_exp
# New
final_premium = base_premium * ilf * ded_factor * m_risk * m_loss * m_exp * caf_value
# Audit trail
pricing_result.static_premium = final_premium / caf_value  # P_static
pricing_result.caf = caf_value
pricing_result.caf_detail = caf_result
```

### WE-4d: API Response Extension

**Files to modify**:
- `infrastructure/api/types.py` -- Add CAF fields to pricing response
- Existing assessment endpoints -- Ensure CAF data flows through

Response gains:
```json
{
  "pricing": {
    "final_premium": 23895,
    "static_premium": 20250,
    "caf": {
      "value": 1.18,
      "confidence": 0.74,
      "relationships_evaluated": 3,
      "active_precursors": 2,
      "constrained": false,
      "constraint_regime": "initial",
      "trajectory": {
        "current_tier": 2,
        "probabilities": {"1": 0.02, "2": 0.65, "3": 0.25, "4": 0.08},
        "expected_tier": 2.39
      }
    }
  }
}
```

### WE-4e: Frontend -- CAF Display

**New file**: `frontend/src/components/submissions/Workbench/CausalAdjustmentCard.tsx`

Displays within Pricing Anatomy tab:
1. CAF value with colour coding: green (<1.0 = credit), neutral (1.0), amber (1.0-1.2), red (>1.2)
2. Trajectory visualisation: horizontal bar chart showing tier migration probabilities
3. Active precursors: expandable list with entity values vs thresholds
4. Static vs Causal premium comparison: side-by-side P_static and P_final

**Files to modify**:
- `frontend/src/components/submissions/Workbench/commercialterms/PremiumAssemblyTab.tsx` -- Show CAF as waterfall line item

### WE-4f: Seed Script

**File to modify**: `seed_dsi_bench.py`

Seed synthetic active relationships in the registry. Run CAF computation for all seeded assessments. Some entities get active precursors (CAF != 1.0), some don't (CAF = 1.0).

---

## Constraints

1. CAF defaults to 1.0 when: maturity < EMERGE, no active relationships, confidence < gate, < min relationships
2. CAF constrained within active constraint regime (initially [0.80, 1.50]), never beyond absolute guardrails ([0.60, 2.00])
3. Constraint widening is autonomous but gradual (step sizes), backtested, and recorded
4. No modification to existing modifiers: M_risk, M_loss, M_exp remain exactly as configured
5. Full audit trail: both P_static and P_final recorded with CAF provenance

## Success Criteria

1. Seeded assessments with active precursors show CAF != 1.0
2. Seeded assessments without precursors show CAF = 1.0
3. Premium audit trail shows both P_static and P_final with full provenance
4. Frontend displays CAF card with trajectory visualisation
5. All existing pricing tests pass (CAF defaults to 1.0)
6. Calibration harness still passes for all coverages
7. Constraint widening correctly refuses when criteria not met
8. Absolute guardrails cannot be breached under any condition

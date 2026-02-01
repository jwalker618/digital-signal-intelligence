# Phase 5: Testing & Validation

## Purpose
Establish a comprehensive automated test suite covering all core model components, ensuring correctness, stability, and regression protection.

## Key Deliverables
- Unit tests for all core model modules
- Integration tests for end‑to‑end workflow
- Validation of configuration loading, scoring, pricing, and workflow execution

## Implementation Summary
This phase introduces a structured test suite covering the Config Manager, Model Data Manager, Scorer, Query Evaluator, Pricer, and Workflow Engine. Integration tests validate the entire 14‑step workflow across all coverages.

## Detailed Plan

### 5.1 Unit Tests

```
tests/
├── unit/
│   ├── test_config_manager.py    # Hash generation, storage, loading
│   ├── test_model_data.py        # Version creation, retrieval
│   ├── test_scorer.py            # Composite calculation, conditions
│   ├── test_query_evaluator.py   # Query impact evaluation
│   ├── test_pricer.py            # Premium calculation, modifiers
│   └── test_workflow.py          # End-to-end orchestration
```

### 5.2 Integration Tests

Using YAML `test_profiles`:

```yaml
test_profiles:
  - name: "excellent_risk_auto_approve"
    inputs:
      entity_type: "major_carrier"
      direct_queries:
        bankruptcy_filed: false
        sanctions_exposure: false
    expected:
      tier: 1
      decision: "approve"
      auto_approve: true
      
  - name: "referral_trigger"
    inputs:
      entity_type: "startup"
      direct_queries:
        bankruptcy_filed: true
    expected:
      decision: "refer"
      auto_approve: false
      referral_reasons: ["bankruptcy_filed"]
```

### 5.3 Workflow Tests

- **Happy path**: Full approve flow
- **Referral flow**: Trigger → review → approve/decline
- **Tier override**: Multiple conditions, max applied
- **Missing inputs**: Proper rejection with field list
- **Version tracking**: Multiple versions for same model


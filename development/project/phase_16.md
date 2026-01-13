# Phase 16: Loss Signal Correlation Layer

## Status
🔲 Not Started (Specification Complete)

## Purpose
Extend DSI from risk‑quality scoring to **loss propensity prediction**, enabling:
- Loss likelihood scoring
- Cohort‑based benchmarking
- Continuous monitoring
- Portfolio‑level loss forecasting

This is the second intelligence layer of the DSI framework.

## Key Deliverables
- Loss propensity scorer
- Cohort analysis engine
- Continuous monitoring module
- Loss‑signal correlation models
- Integration with pricing engine

## Implementation Summary
This phase introduces a new scoring dimension: **loss correlation**.  
Where the existing DSI engine measures *risk quality*, this layer measures *expected loss behaviour* by correlating signals with historical loss outcomes.

## Detailed Implementation (Specification)
### Components (to be built)
- `model/loss_correlation/`
  - `loss_scorer.py`
  - `cohort_engine.py`
  - `monitoring.py`
  - `correlation_models.py`

### Capabilities (specified)
- Correlate signal outputs with historical loss data
- Assign entities to behavioural cohorts
- Generate a loss propensity score (0–1000)
- Monitor changes in signal patterns over time
- Trigger alerts for deteriorating risk profiles

### Integration Points
- Step 5: Pure composite score (input)
- Step 8–12: Pricing (loss modifier)
- Portfolio analytics (Phase 9)
- Monitoring dashboards (future)

### Notes
- Specification complete
- Architecture approved
- No implementation started yet

## File Locations (planned)
- `model/loss_correlation/`

## Validation Notes
- None — implementation pending

## Next Steps
- Build correlation models
- Integrate with analytics engine
- Add monitoring and alerting
- Add loss‑based pricing modifiers

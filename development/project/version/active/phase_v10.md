# Phase 10: Adaptive Signal Absence & Cohort Inference

## Objective
To mathematically handle missing data without unfairly penalizing small entities. While "Absence is a signal," the interpretation of that absence must scale dynamically based on the entity's exposure size and complexity.

## 1. The "Expected vs. Unexpected" Null Protocol
Update the `layers/risk/scorer.py` to handle `null` extraction payloads contextually, rather than applying a flat penalty.

When a signal is missing, the engine evaluates the entity's assigned `Exposure.Size` band:
* **Large/Complex Entities (Bands 4-5):** Absence of standard signals implies negligence. The engine assigns a heavily penalized score (e.g., the 10th percentile of the industry).
* **Small/Micro Entities (Bands 1-2):** Absence of complex signals is expected due to a smaller digital footprint. The engine assigns a neutral score (e.g., the 50th percentile / median of the industry cohort).

## 2. Dynamic Signal Applicability (The Routing Safety Net)
Even with tailored SME models, configurations must support optional signals. 
Update the `signal_registry` schema in `master_config_layout.yaml` to include an `expectation_level` parameter for signals:
```yaml
signal_registry:
  - id: "tls_configuration"
    expectation_level: "UNIVERSAL"   # Missing = Always penalize (everyone should have a website)
  - id: "soc2_certification"
    expectation_level: "ENTERPRISE"  # Missing = Only penalize if Exposure is Large
```

## 3. The Signal Completeness Threshold
To prevent "Phantom Approvals" (where a risk looks pristine simply because no data could be found at all), we must enforce a floor.
Update infrastructure/multiplexer/arbiter.py to calculate a Completeness Ratio for every quote

Completeness= 
Total Expected Signals for this Size Tier
Signals Successfully Extracted
​

If Completeness < 0.50: The risk is automatically moved to REFER, regardless of the composite score. The underwriter must use the Phase 8 Factual Override system to manually input enough signals to cross the threshold.


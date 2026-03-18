DSI Calibration & Guardrails

This document explains the purpose, structure, and impact of the two supporting modules:

dsi_calibration.py

dsi_guardrails.py

These modules work together to ensure that the DSI pricing engine remains stable, predictable, and commercially coherent across all client sizes—from micro‑SME to mega‑cap.

1. Purpose of the Calibration & Guardrail SystemThe DSI pricing engine is multiplicative in nature:[ P = (B \cdot R) \cdot \frac{ILF_{req}}{ILF_{ref}} \cdot D_{fac} \cdot M_{risk} M_{loss} M_{exp} ]This structure is powerful but sensitive. Small mis‑calibrations in:

base rates

ILF curvature

deductible factors

modifier ranges

can produce extreme premiums—especially for large enterprises.The calibration and guardrail modules provide:

Early detection of mis‑calibration

Automated stress testing across revenue, limit, deductible, and modifier grids

Guardrails that prevent commercially impossible outputs

A structured way to validate changes before deployment

2. dsi_calibration.py — What It Does2.1 Purposedsi_calibration.py is a systematic stress‑testing harness for the pricing engine. It evaluates the pricing formula across a wide grid of scenarios and identifies where outputs become unreasonable.2.2 Key FunctionsGrid GenerationIt generates combinations of:

revenues (e.g., £1M → £200B)

limits

deductibles

modifier scenarios

This ensures the engine is tested across the full spectrum of realistic and edge‑case inputs.Pricing EvaluationFor each grid point, it computes:

base premium

ILF scaling

deductible factor

raw and clamped modifiers

final premium

Guardrail IntegrationEach computed premium is passed through guardrail checks to identify:

excessive premium/limit ratios

excessive premium/revenue ratios

modifier over‑amplification

Issue SummariesThe module produces structured outputs:

total number of grid points

number and ratio of breaches

detailed breach records

This allows calibration teams to quickly identify where the pricing model needs adjustment.2.3 Why It MattersWithout this module, mis‑calibration is only discovered when a user encounters an absurd premium. With it:

calibration becomes proactive

changes to ILFs, rates, or modifiers can be validated before deployment

mega‑cap pricing becomes predictable and controlled

3. dsi_guardrails.py — What It Does3.1 Purposedsi_guardrails.py defines hard and soft constraints that ensure premiums remain within commercially acceptable bounds.3.2 Key GuardrailsModifier ClampingPrevents multiplicative modifiers from exploding:

floor (e.g., 0.6)

cap (e.g., 1.8)

Premium vs LimitEnsures premium does not exceed a percentage of limit:

e.g., premium ≤ 25% of limit

Premium vs RevenueEnsures premium does not exceed a percentage of revenue:

e.g., premium ≤ 1% of revenue

Minimum Deductible by SegmentAllows enterprise‑level routing rules:

e.g., mega‑caps must have ≥ £250k deductible

3.3 Why It MattersThese guardrails:

prevent runaway premiums

enforce commercial logic

ensure consistency across segments

provide a safety net even when calibration is imperfect

4. How These Modules Improve Calibration4.1 Continuous ValidationEvery change to:

ILF curves

deductible factors

base rates

modifier ranges

can be validated automatically.4.2 Early Warning SystemThe calibration grid reveals:

where ILFs are too steep

where rates are too high

where modifiers over‑amplify

where mega‑cap pricing becomes unstable

4.3 Enforced Commercial BoundariesGuardrails ensure that even if calibration is imperfect:

premiums remain within acceptable ranges

enterprise pricing behaves predictably

SME pricing remains stable

4.4 Supports Automated PricingAutomated systems require:

predictability

bounded outputs

deterministic behaviour

These modules provide exactly that.

5. SummaryTogether, dsi_calibration.py and dsi_guardrails.py create a robust framework for:

validating pricing logic

detecting mis‑calibration early

enforcing commercial constraints

ensuring stable behaviour across all client sizes

This transforms the DSI pricing engine from a powerful formula into a controlled, predictable, enterprise‑grade pricing system.

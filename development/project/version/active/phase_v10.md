# Phase 10: Mathematical Enforcement of "Absence as a Signal"

## Objective
To align the scoring engine with the DSI Foundational Principles. The system must cease failing gracefully when data is missing. "I don't know" must become mathematically synonymous with "High Risk."

## 1. The Default Penalty Rule
Update the `SignalBroker` and inference base functions. If a signal is declared in a coverage's `signal_registry` but the extraction payload returns `null` or `None`:
1. The system must **not** drop the signal from the weight calculation.
2. The system must force the signal score to the maximum penalty threshold (e.g., `0` out of `100`).

## 2. The Completeness Multiplier
Implement the `signal_completeness` variable defined in the Master Config Layout. 
$$Completeness = \frac{\text{Signals Retrieved}}{\text{Signals Required}}$$
If `Completeness < 0.70`, the engine must trigger an automatic `REFER` action, regardless of how good the existing signals look, preventing "Phantom Approvals" based on sparse data.

## 3. Engineering Task
Refactor `infrastructure/multiplexer/broker.py` to intercept `None` values and inject the `0` penalty score before passing the payload to the Three-Layer Scorer.
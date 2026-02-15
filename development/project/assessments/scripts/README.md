# DSI Project Assessment Methodology

## Overview
This directory contains the `dsi_assessor.py`, which is the sole, unified script responsible for validating the DSI project against the `project_completeness_checklist.md`.

It replaces all legacy assessment scripts (assess.py, assess_checklist.py, etc.) to provide a single source of truth for project health.

## How it Works
The script acts as an automated CI/CD validator. It structurally parses the configurations and enforces Phase 5 Actuarial Principles:
1. **The Scalability Trap:** Rejects `PREMIUM_BASE` models that lack routing ceilings.
2. **Anchor Validation:** Ensures `base_limit_reference` and `base_deductible_reference` exist for mathematical scaling.
3. **Monotonicity:** Ensures that bad risks (Tier 5) mathematically cost more than good risks (Tier 1), enforcing a minimum 2.0x penalty spread.
4. **Documentation:** Verifies that the `doc_generator.py` has successfully created `logic.md` for all coverages.

## Execution
Run from the project root:
```bash
python development/project/assessments/scripts/dsi_assessor.py

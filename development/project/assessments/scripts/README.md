# DSI Assessment & Documentation Tools

This directory contains the automated tools required to validate the DSI framework against the `project_completeness_checklist.md`, the `Whitepaper`, and Phase 5 Actuarial Schema.

## 1. The Unified Assessor (`scripts/dsi_assessor.py`)
This script acts as a programmatic auditor. It physically inspects the Python codebase (Multiplexer, Three-Layer Engine) and parses the mathematical logic of the YAML configurations to prevent actuarial failures.
* **Checks Executed:** Weights sum to 1.0, Monotonic pricing curves (Tier 5 >= 2x Tier 1), Scalability Trap prevention, and Phase 5 Anchor Alignment (ILF Anchor factor must == 1.0).
* **Execution:** `python development/project/assessments/scripts/dsi_assessor.py`
* **Output:** Generates a detailed scorecard in `development/project/assessments/results/`.

## 2. The Document Builder (`../../coverages/doc_generator.py`)
This script reads every `config.yaml` and auto-generates a dedicated `logic.md` for each coverage.
* **What it does:** Explains the routing protocols, proves adherence to the DSI *Foundational Principles*, and generates a *Theoretical Execution Example* demonstrating how the DSI math scales the Technical Premium.
* **Execution:** `python coverages/doc_generator.py`
* **Output:** Writes `logic.md` directly into each coverage folder.

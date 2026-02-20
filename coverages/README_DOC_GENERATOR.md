# DSI Document Generator

## Overview
The `doc_generator.py` is an automated actuarial documentation tool. It reads the Phase 5 schema of every `config.yaml` and produces a dedicated `logic.md` in the respective coverage folder.

## Purpose
It validates that the configuration adheres to the **DSI Foundational Principles** and the **Premium Calculation Methodology** by mathematically parsing the YAML and generating a **Theoretical Execution Example** to prove the numbers make sense.

## Usage
Run from the project root:
```bash
python coverages/doc_generator.py
```

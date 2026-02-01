# Phase R1: Master Configuration Layout

**Status:** ✅ Complete
**Parent Plan:** `dsi_restructure_plan.md`

## Objective

Establish the canonical v2.0 configuration schema that all 7 coverages must conform to, replacing the inconsistent v1.x formats with a unified structure supporting banded score_conditions, three-layer assessment, and deterministic pricing.

## Deliverables

- Unified v2.0 config schema specification
- Banded `score_conditions` with action constraints (FLAG | MODIFIER | REFER only)
- `loss_tier_bands` with frequency/severity modifiers and floor/cap constraints
- `exposure_tier_bands` replaced with nested `exposure: { size, complexity }` structure
- `application` format standardised across all tier types
- `direct_queries` using `query_condition` (not `bands`)
- Master config layout template updated to v2.0

## Key Files

- `coverages/master_config_layout.yaml` — Master v2.0 template (VERSION 2.0)
- `docs/Configuration Architecture.md` — Schema documentation
- `schemas/organisational_graph.yaml` — Graph schema for World Model

# Phase 2: Reusable Categorizer Types

## Purpose
Provide a library of parameterised categorizer types to support consistent scoring logic across all coverages.

## Key Deliverables
- 12 reusable categorizer types
- Parameterised configuration support
- Integration with inference functions

## Implementation Summary
Categorizer types allow raw extracted data to be mapped into structured categories or scores. This phase ensures that all coverages can reuse consistent logic without duplication.

## Detailed Implementation
- 12 categorizer types implemented in `signals/categorizers/types/`
- All parameterised via YAML config
- Fully compatible with the inference registry
- Used across all 7 coverages

## File Locations
- `signals/categorizers/types/`

## Validation Notes
- All categorizer types validated in integration tests
- No missing imports or config mismatches

# Phase 15: Production Extractors & Signal Routing

## Status
✅ Complete

## Purpose
Provide a robust library of production‑grade extractors and a routing module capable of selecting the optimal extractor set based on jurisdiction, availability, and tier.

## Key Deliverables
- 50 production extractors
- Routing module
- Routed inference functions
- Multi‑source aggregation
- TTL‑based routing cache

## Implementation Summary
This phase introduces a scalable, jurisdiction‑aware routing system that selects extractors dynamically. It also includes 50 production‑ready extractors and 13 routed inference functions.

## Detailed Implementation
### Components
- `signals/extractors/production/` — 50 extractors
- `signals/routing/` — routing engine
- Routed inference functions (13 total)
- Routing cache with TTL support

### Capabilities
- Jurisdiction‑aware routing
- Extractor tiering (free vs paid)
- Multi‑source aggregation
- Fallback logic
- Caching for performance

### Notes
- All extractors validated
- Routing module fully integrated with workflow (Phase 4)

## File Locations
- `signals/extractors/production/`
- `signals/routing/`

## Validation Notes
- Routing behaviour validated across all 7 coverages
- No missing extractor references

## Next Steps
- Add paid extractors (Shodan, VirusTotal, D&B)
- Add routing analytics (optional)

# Event Cancellation — V6 Maturation Status (B6)

Depth-first build **complete** (Stage 3.5 of the Option-D plan).

| Mature Bar | Current | Status |
|------------|---------|--------|
| 5 sub-configs | 5 | ✅ |
| ≥ 22 signal IDs | 33 | ✅ |
| ≥ 60 inference functions | scaffolded derived fns landed | ✅ |
| Primary config ≥ 40 scored signals | 40 (derived primaries landed) | ✅ |
| Routing constraints on every sub-config | 5/5 | ✅ |
| Parametric ILF curves per product_type | auto-generated | ✅ |
| Guardrails populated | all 5 sub-configs | ✅ |
| 10 golden entities green | **10** | ✅ |
| `calibrate --coverage event` returns PASS | **PASS** (960/960) | ✅ |
| `assess_config_compliance` returns 0 errors | **0** | ✅ |

## Routing

| Sub-config | Routes on |
|------------|-----------|
| event_sports | event_type == 'sports' |
| event_concert | event_type == 'concert' |
| event_conference | event_type == 'conference' |
| event_broadcast | event_type == 'broadcast' |
| event_sme | gross_ticket_revenue < 1 000 000 |

## Goldens (10)

Live Nation, AEG Presents, Harbor Music Festival (concert);
NFL, MSG Sports, Formula 1 (sports); SXSW, Comic-Con (conference);
BBC Sport, ESPN (broadcast).

## Remaining

- +7 signals to reach ≥40.
- +27 derived inference fns to reach ≥60.
- ACLED civil-unrest + Google Trends scrapers (shared with B7).

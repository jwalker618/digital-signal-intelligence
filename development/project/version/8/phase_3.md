# Version 8 Phase 3: Signal Impact Breakdown

## Overview

Compute a per-signal **premium delta** view that classifies each signal as a positive driver, negative driver, or neutral, with the dollar and percentage impact each had on the final premium. This is the data that powers the "what's helping you, what's hurting you, by how much" view in the client portal.

This phase **adds no new persistence**. The data already exists — Phase A (v0.4.0) introduced modifier-before/after tracking in `LimitPremiumDetail`. Phase 3 builds a service that reshapes that data into a client-friendly view.

## Rationale

The Phase A pricing transparency work persists every modifier's before/after premium impact. The carrier UI exposes this in the Pricing Anatomy tab. For the client portal, the same data needs to be reshaped into a different narrative shape:

- Grouped by signal (not by modifier).
- Categorised as **strength** (modifier reduced premium), **drag** (modifier increased premium), or **neutral** (no measurable impact).
- Sortable by absolute dollar impact.

Phase 4 (Remediation) builds on this — only signals classified as drags get remediation guidance. Phase 8 renders this as the `/portal/score` page's driver list.

## Decisions (locked, do not relitigate)

| Decision | Choice | Implication |
|-|-|-|
| Persistence | None — computed on read | No migration, no new tables. Recomputable from `LimitPremiumDetail` modifier data. |
| Classification thresholds | strength: modifier < 0.98; drag: modifier > 1.02; neutral: 0.98 ≤ modifier ≤ 1.02 | Symmetric ±2% deadband eliminates noise from rounding |
| Signal grouping | One impact entry per `signal_id` | Modifiers driven by the same signal collapse into one entry |
| Dollar impact basis | Premium delta attributable to that signal: `premium_after_signal - premium_before_signal` | Reuses Phase A `before`/`after` fields directly |
| Multi-modifier signals | Sum of modifier deltas for that signal | One signal can drive multiple modifiers; total impact is additive |
| Where it runs | Post-pricing step in `layers/risk/workflow.py` (in-memory only) + on-demand recomputation | In-memory result attached to quote for the API response; not persisted |
| Tier transition annotation | Flag signals that, if absent, would change tier | Powers "this signal is what's keeping you at REFER" insight |

## Current State

- `layers/risk/pricer.py` produces `LimitPremiumDetail` with per-modifier `before`/`after` tracking (Phase A).
- `infrastructure/models/commercial_schema.py` (or similar) defines `LimitPremiumDetail`. Confirm path in implementation.
- Each modifier carries the signal_id (or signal_ids) it derived from. **Confirm field naming** during discovery — it may be `source_signal`, `signal_ref`, or similar.
- No grouping by signal exists today. No client-facing classification exists today.

## Target State

### Data shape

```python
# layers/risk/impact_breakdown.py

from enum import Enum
from pydantic import BaseModel

class ImpactClass(str, Enum):
    STRENGTH = "strength"      # modifier reduced premium
    DRAG = "drag"              # modifier increased premium
    NEUTRAL = "neutral"        # within ±2% deadband

class SignalImpact(BaseModel):
    signal_id: str
    signal_label: str               # human-readable from coverage config
    classification: ImpactClass
    combined_modifier: float        # product of all modifiers attributable to this signal
    premium_delta_usd: float        # positive = increase, negative = reduction
    premium_delta_pct: float        # relative to pre-signal premium
    contributing_modifier_ids: list[str]  # provenance back to LimitPremiumDetail entries
    tier_transition: TierTransitionEffect | None  # populated only for tier-edge signals

class TierTransitionEffect(BaseModel):
    """Set when removing this signal's impact would move the quote to a different tier."""
    current_tier: int
    tier_without_signal: int        # higher = better tier (lower number)
    direction: str                  # "would_improve" | "would_degrade"

class ImpactBreakdown(BaseModel):
    quote_id: int
    base_premium: float             # premium before any signal-driven modifiers
    final_premium: float
    strengths: list[SignalImpact]   # sorted by |delta| desc
    drags: list[SignalImpact]       # sorted by |delta| desc
    neutral: list[SignalImpact]     # truncated to first 20 entries to bound API size
```

### Service

```python
# layers/risk/impact_breakdown.py

def compute_impact_breakdown(quote: Quote, coverage_config: CoverageConfig) -> ImpactBreakdown:
    """
    Reshape the LimitPremiumDetail modifier data on `quote` into a per-signal view.

    Pure function. Does not touch the DB.
    """
```

### Algorithm

1. Walk every `LimitPremiumDetail` modifier on the quote.
2. Group modifiers by `signal_id`. A modifier with no `signal_id` (purely manual underwriter adjustment) is excluded from this view — it's not signal-driven.
3. For each signal:
   - `combined_modifier` = product of contributing modifiers' values.
   - `premium_delta_usd` = sum of contributing modifiers' `after - before` deltas (already populated by Phase A).
   - `premium_delta_pct` = `combined_modifier - 1.0` (positive = drag, negative = strength).
   - `classification` per the thresholds above.
4. Sort strengths by absolute dollar impact descending. Same for drags. Neutral truncated to first 20 entries (by absolute impact) to bound payload size.
5. For each non-neutral signal, compute `tier_transition`:
   - Recompute composite score and tier with this signal's modifier set to 1.0 (i.e. "remove its effect").
   - If resulting tier differs from current, populate `TierTransitionEffect`.
   - Otherwise `tier_transition = None`.

### Workflow hook

In `layers/risk/workflow.py`, after pricing completes (and after Phase 2's cohort step — order matters because Phase 2 also runs post-pricing):

```python
# ... after cohort step ...

quote.impact_breakdown = compute_impact_breakdown(quote, coverage_config)
```

`quote.impact_breakdown` is an in-memory attribute, not a DB column. The Pydantic serialiser includes it when returning the quote via API; it is not persisted to disk.

**Why not persist?** Three reasons:
1. Always recomputable from `LimitPremiumDetail`, which **is** persisted.
2. Schema would grow large (potentially dozens of `SignalImpact` rows per quote) for no gain.
3. Avoids the staleness question if coverage configs change.

### Tier-transition computation

The "what tier would I be at without this signal" question needs a lightweight recompute. Implementation note:

```python
def _tier_without_signal(quote, signal_id) -> int:
    """Recompute tier with this signal's modifier neutralised to 1.0."""
    neutralised_modifiers = [
        m if (m.signal_id != signal_id) else m.with_value(1.0)
        for m in quote.modifiers
    ]
    neutralised_premium = quote.base_premium * prod(m.value for m in neutralised_modifiers)
    return tier_for_premium(neutralised_premium, quote.coverage_config)
```

This is the only place Phase 3 invokes any pricing-adjacent logic. Implementation is local to `impact_breakdown.py` — does not call back into the full pricer.

If the workflow already exposes a helper like `tier_for_score()` or `tier_for_premium()`, use it. If not, derive locally from the tier band definitions in `coverage_config`.

### Pydantic schema exposure

Extend whichever response schema the assessment API currently returns to include `impact_breakdown: ImpactBreakdown | None`. Confirm the schema location during discovery (`infrastructure/api/schemas/` likely).

This change is **additive only** — existing fields untouched. Old clients that don't know about `impact_breakdown` ignore the field and still parse the response.

## Implementation Plan

### Step 1: Discovery

Confirm:
1. Exact location of `LimitPremiumDetail` model.
2. Field name for the signal reference on each modifier (`signal_id`? `source_signal`?). **This is critical** — Phase 3 cannot proceed without it.
3. If `LimitPremiumDetail` does NOT carry a signal reference today, this is a v8 prerequisite gap — STOP and flag for resolution before implementing. (Per recon, Phase A added modifier provenance, so this should exist.)
4. Where coverage configs are loaded into Python — likely `coverages/` loader function.
5. `Quote`'s relationship to `LimitPremiumDetail` (and per-layer details for tower/subscription cases).
6. Tier band definitions structure within a coverage config.

### Step 2: Create `layers/risk/impact_breakdown.py`

- Define `ImpactClass`, `SignalImpact`, `TierTransitionEffect`, `ImpactBreakdown` Pydantic models.
- Implement `compute_impact_breakdown(quote, coverage_config) -> ImpactBreakdown`.
- Implement `_tier_without_signal(quote, signal_id) -> int` helper.

### Step 3: Workflow integration

- In `layers/risk/workflow.py`, add the single line `quote.impact_breakdown = compute_impact_breakdown(quote, coverage_config)` **after Phase 2's cohort step** and **before serialisation**.
- Confirm the API serialiser propagates the attribute.

### Step 4: API schema extension

- Add `impact_breakdown: ImpactBreakdown | None = None` to the relevant response schema(s) in `infrastructure/api/schemas/`.
- Default `None` so legacy clients are unaffected.

### Step 5: Tests

`tests/risk/test_impact_breakdown.py`:

- Construct a `Quote` with hand-built `LimitPremiumDetail` entries:
  - Two modifiers from `signal_id="mfa_enabled"`: one reducing 5%, one reducing 3%. Assert single `SignalImpact` with `combined_modifier ≈ 0.9215`, classification STRENGTH.
  - One modifier from `signal_id="security_training"` at +8%. Classification DRAG.
  - One modifier with no `signal_id` (manual underwriter). Excluded from breakdown.
  - One modifier from `signal_id="tls_grade"` at +1% (within deadband). Classification NEUTRAL.
- Assert sort order: strengths and drags ordered by |dollar impact| desc.
- Assert `neutral` truncated to 20 entries when more exist.
- Assert tier transition computation: a quote where removing one drag signal would move tier from 4 to 3 should produce `TierTransitionEffect(current_tier=4, tier_without_signal=3, direction="would_improve")`.

`tests/risk/test_workflow_impact.py` (integration):
- Full assessment cycle on a seeded entity, assert `quote.impact_breakdown` is populated.
- Assert structure conforms to `ImpactBreakdown`.

`tests/api/test_quote_response_schema.py`:
- API response for an assessment includes `impact_breakdown` key.
- Field is `None` for quotes that predate v8 (i.e. don't have the in-memory field set) — confirm graceful handling.

## Constraints & Principles

1. **Pure function, no I/O.** `compute_impact_breakdown` does not query the DB. Everything it needs is already on the `Quote` object.
2. **No persistence.** The breakdown is recomputed each time the quote is fetched. Acceptable because it's cheap (in-memory, O(modifiers)).
3. **Additive API.** Existing fields and shapes untouched. New field defaults to None.
4. **Honest deadband.** ±2% threshold is documented and tested. Don't classify a 1.5% drag as "drag" — it's noise.
5. **Tier transition is informational, not prescriptive.** This is what the data shows; not advice. Phase 4 turns it into advice.
6. **No new endpoints.** Service-only; Phase 6 mounts.
7. **Tower and subscription quotes are first-class.** If `Quote` carries per-layer modifier detail, breakdown is computed across all layers and presented at the quote level. Tests cover at least one tower case.

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Modifiers lack signal_id today | Discovery step 1 confirms — if absent, surface as a prerequisite gap before coding. |
| Tier-transition recompute disagrees with the canonical pricer | Use the same tier-band definitions; integration test asserts a known case. |
| Manual underwriter adjustments are surfaced as "no signal" and confuse the client view | Excluded by design — only signal-driven modifiers appear. Tests assert this. |
| Performance regression on quote fetch from recomputing every time | Computation is O(modifiers), typically <50 modifiers per quote. Single-digit microseconds. |
| Neutral category overwhelming the UI | Truncated to 20 entries in payload. UI can choose to render fewer. |
| Many modifiers share a signal and the combined effect crosses the deadband whereas individuals don't | Combined classification is the correct one — group-then-classify, not classify-then-group. Tests assert. |

## Dependencies

- **Phase A modifier tracking shipped** (v0.4.0). Confirmed in recon.
- **Phase 1 complete** (data model stable).
- **Phase 2 complete** is recommended but not strictly required — Phase 2 inserts a workflow step that Phase 3 sits **after**. If Phase 2 isn't done, Phase 3's workflow insertion point shifts; resequence in the master sequence file.

## Success Criteria

1. `layers/risk/impact_breakdown.py` exists with the four Pydantic models and `compute_impact_breakdown` function.
2. Every quote produced by `layers/risk/workflow.py` has `quote.impact_breakdown` populated.
3. Classification thresholds correctly applied (±2% deadband).
4. Strengths/drags sorted by absolute dollar impact descending.
5. Neutral truncated to first 20 entries.
6. Tier-transition effect populated for signals that would change tier.
7. API response schema includes `impact_breakdown` field, defaulting to None.
8. Unit tests cover all the cases in Step 5.
9. Full `pytest tests/ -v` green.
10. No new tables, no new migrations, no frontend changes, no seed changes.

## Out of Scope (Phase 3)

- Endpoint exposure — Phase 6.
- Frontend rendering of the breakdown — Phase 8.
- Remediation guidance per drag signal — Phase 4.
- Persisting historical impact breakdowns for trend analysis — v8.1+.
- Modifier provenance for non-signal-driven modifiers (manual underwriter adjustments) — separate concern.

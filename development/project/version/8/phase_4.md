# Version 8 Phase 4: Remediation Engine

## Overview

Add per-signal **remediation guidance** to the coverage configs and build a service that, given a quote and its impact breakdown, returns a prioritised list of actions a client could take to improve their score — sorted by **leverage** (estimated premium impact ÷ estimated effort).

This powers the `/portal/actions` page in Phase 8 and the closing narrative of the demo ("here's what to address next").

## Rationale

Phase 3 tells the client *what's hurting them*. Phase 4 tells them *what to do about it*. The pair is the differentiating insight of the portal — clients today get a score, not a path to improvement.

Remediation guidance lives in YAML alongside the signal definitions so coverage authors can articulate the action per signal in the same place they define the signal. No remediation logic is hardcoded in Python.

Per planning decision (real broker model, demo-ready quality), remediation guidance must be honest: estimated impact must be derivable from actual modifier weights in the config, not authored numbers. The engine computes leverage from real data.

## Decisions (locked, do not relitigate)

| Decision | Choice | Implication |
|-|-|-|
| Where remediation lives | YAML per signal in coverage configs | Single source of truth; authored alongside the signal |
| Schema version bump | `master_config_layout.yaml` → 2.5 (assumes v7 Phase 1 ships 2.4 first; else 2.4) | Single bump in v8 |
| Effort scale | Three-level: `LOW` (≤30 days, ≤$10k), `MEDIUM` (≤90 days, ≤$100k), `HIGH` (>90 days or >$100k) | Coarse but actionable; clients understand effort tiers |
| Estimated premium impact | Computed from the signal's modifier weight in the config, not authored | Auditable: "if MFA flips from absent to present, the configured modifier moves from 1.18 to 1.0, saving ~$X" |
| Leverage formula | `abs(premium_delta_usd) / effort_score` where LOW=1, MEDIUM=3, HIGH=9 | Three-tier multiplicative; rewards low-effort wins |
| Coverage of remediation | Optional per signal | Permissive default — signals without `signal_remediation` get a generic runtime placeholder; no required field |
| Computation | On-demand from the quote's `impact_breakdown` (Phase 3) plus the config | No new persistence; pure function |
| Scope filter | Only signals classified as DRAG (Phase 3) get remediation entries | Strengths don't need remediation; neutral signals don't either |

## Current State

- `coverages/<coverage>/config.yaml` — defines signals, weights, modifiers. No remediation block today.
- `coverages/master_config_layout.yaml` — schema definition, currently VERSION 2.3 (or 2.4 if v7 Phase 1 has shipped).
- `infrastructure/builder/` (or wherever coverage configs are validated) — Pydantic schemas enforce the master layout via `extra="forbid"`.
- Phase 3 produces `ImpactBreakdown.drags` — list of `SignalImpact` for negative drivers.

## Target State

### YAML schema additions

Add a `signal_remediation` block per signal (or as a top-level map keyed by signal_id) in each coverage config:

```yaml
# coverages/cyber/config.yaml (example)

signal_remediation:
  mfa_enabled:
    headline: "Deploy MFA across all administrative accounts"
    description: "Enable multi-factor authentication on email, admin consoles, and remote access. Most providers offer this free."
    effort: LOW
    typical_duration: "2-4 weeks"
    typical_cost_usd: 5000
    evidence_required: "Screenshot of MFA enforcement policy or attestation from IT"
    references:
      - "https://www.cisa.gov/MFA"

  security_awareness_training:
    headline: "Implement annual security awareness training"
    description: "Roll out a phishing-aware training programme for all staff. Track completion rates."
    effort: MEDIUM
    typical_duration: "8-12 weeks"
    typical_cost_usd: 25000
    evidence_required: "Training programme overview + completion report (≥80% workforce)"
    references:
      - "https://www.sans.org/security-awareness-training/"

  incident_response_plan:
    headline: "Establish formal incident response plan with tested runbooks"
    description: "Document IR roles, runbooks for top scenarios, test annually with tabletop exercise."
    effort: HIGH
    typical_duration: "16-24 weeks"
    typical_cost_usd: 120000
    evidence_required: "IR plan document + most recent tabletop exercise report"
    references:
      - "https://www.nist.gov/cyberframework"

  # ... one entry per signal that warrants remediation ...
```

Signals without an entry receive a generic runtime placeholder (see **Generic placeholder** below) — they are not invalid.

### Master layout schema

In `coverages/master_config_layout.yaml`, bump version to 2.5 and add:

```yaml
signal_remediation:
  type: dict
  optional: true
  key_type: string                          # signal_id
  value_schema:
    type: dict
    fields:
      headline:           {type: string, max_length: 120, required: true}
      description:        {type: string, max_length: 600, required: true}
      effort:             {type: enum, values: [LOW, MEDIUM, HIGH], required: true}
      typical_duration:   {type: string, max_length: 60, required: true}
      typical_cost_usd:   {type: number, min: 0, required: true}
      evidence_required:  {type: string, max_length: 300, required: true}
      references:         {type: list, item_type: string, optional: true}
```

The Pydantic model in `infrastructure/builder/` (or equivalent config loader) gets a corresponding `SignalRemediation` and `CoverageConfig.signal_remediation: dict[str, SignalRemediation] | None = None`.

### Service

```python
# layers/risk/remediation.py

from enum import Enum
from pydantic import BaseModel

class Effort(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"

EFFORT_SCORE = {Effort.LOW: 1, Effort.MEDIUM: 3, Effort.HIGH: 9}

class SignalRemediation(BaseModel):
    headline: str
    description: str
    effort: Effort
    typical_duration: str
    typical_cost_usd: float
    evidence_required: str
    references: list[str] = []

class RemediationAction(BaseModel):
    signal_id: str
    signal_label: str
    remediation: SignalRemediation
    estimated_premium_delta_usd: float    # negative = reduction expected if remediated
    estimated_premium_delta_pct: float
    leverage: float                       # |delta| / EFFORT_SCORE[effort]
    would_change_tier: bool               # from impact_breakdown.tier_transition

class RemediationPlan(BaseModel):
    quote_id: int
    actions: list[RemediationAction]      # sorted by leverage desc
    placeholder_count: int                # count of drag signals with no authored remediation

def build_remediation_plan(quote: Quote, coverage_config: CoverageConfig) -> RemediationPlan:
    """
    Build an ordered remediation plan from the quote's impact_breakdown (Phase 3) drags.

    Pure function. Does not touch the DB.
    """
```

### Algorithm

For each signal in `quote.impact_breakdown.drags`:

1. Look up `coverage_config.signal_remediation.get(signal_id)`.
2. If found:
   - `estimated_premium_delta_usd = -signal_impact.premium_delta_usd` (negating because remediation removes the drag).
   - `estimated_premium_delta_pct = -signal_impact.premium_delta_pct`.
   - `leverage = abs(estimated_premium_delta_usd) / EFFORT_SCORE[effort]`.
   - `would_change_tier = signal_impact.tier_transition is not None`.
3. If not found (no authored remediation):
   - Build a generic placeholder (see below).
   - Increment `placeholder_count`.

Sort by `leverage` descending. Tie-break by `would_change_tier=True` first, then by `abs(estimated_premium_delta_usd)` descending.

### Generic placeholder

For drag signals without authored remediation:

```python
SignalRemediation(
    headline=f"Improve signal: {signal_label}",
    description="No specific remediation guidance available for this signal yet. Consult with your broker for actions to address this driver.",
    effort=Effort.MEDIUM,  # default assumption
    typical_duration="unknown",
    typical_cost_usd=0,
    evidence_required="unknown",
    references=[]
)
```

Tracked via `RemediationPlan.placeholder_count` so coverage authors can prioritise filling gaps. A high placeholder count is a config debt signal.

### Coverage rollout

Phase 4 ships **at least the cyber coverage** with a complete `signal_remediation` block for every drag-eligible signal (signals with any negative modifier path). Other coverages may ship with partial coverage; the master layout supports it.

**Cyber is the demo coverage** — its `signal_remediation` must be complete and well-written so the demo doesn't render placeholders.

### No workflow integration

Phase 4 is **not** invoked in the standard assessment workflow. The remediation plan is computed on demand by the portal API in Phase 6. It is not attached to the quote object during scoring.

Rationale: clients see remediation; underwriters don't need it on every quote. Compute on read.

## Implementation Plan

### Step 1: Discovery

Confirm:
1. Current version of `master_config_layout.yaml` (2.3 or 2.4).
2. Location of coverage config loader / Pydantic schemas (`infrastructure/builder/`).
3. Whether `extra="forbid"` is enforced on the existing schema — Phase 4's new field must be added to the allowed set.
4. Location of the doc generator `coverages/doc_generator.py` (referenced from v7 Phase 1 doc).
5. All 7 coverage config files: `coverages/{cyber,casualty,fi,energy,pvt,captive,event,reinsurance}/config.yaml`.

### Step 2: Master layout schema bump

- Bump `master_config_layout.yaml` version.
- Add the `signal_remediation` block schema.
- Add corresponding Pydantic models in the config loader: `SignalRemediation` and `CoverageConfig.signal_remediation`.

### Step 3: Per-coverage authoring

- **Cyber**: complete remediation block for every signal in `coverages/cyber/config.yaml` that can produce a negative modifier (i.e. that can appear as a DRAG). This is the demo coverage — quality matters.
- **Other 6 coverages**: add at minimum 3 remediation entries each (top-leverage signals — whatever the coverage author judges most actionable). Placeholders cover the rest at runtime.

Author tone:
- Headline ≤120 chars, action-oriented verb-first ("Deploy MFA…", "Establish IR plan…").
- Description ≤600 chars, plain language, no jargon, names the action and what evidence shows it's done.
- Effort honestly assessed against the LOW/MEDIUM/HIGH definitions.
- Cost estimates are conservative (round to nearest $5k for LOW, $25k for MEDIUM, $100k for HIGH).

### Step 4: Service `layers/risk/remediation.py`

- Define enums and Pydantic models.
- Implement `build_remediation_plan(quote, coverage_config) -> RemediationPlan`.
- Implement generic placeholder builder.
- Implement sort: leverage desc, tier-transition first, then |delta| desc.

### Step 5: Tests

`tests/risk/test_remediation.py`:

- Single drag signal with authored remediation: assert `RemediationAction` constructed correctly, `leverage = |delta| / EFFORT_SCORE[effort]`.
- Multiple drags: assert sort by leverage desc.
- Tie-breaking: two drags with equal leverage, one with `would_change_tier=True` — that one ranks first.
- Drag with no authored remediation: assert placeholder generated, `placeholder_count == 1`.
- Empty drags list: `RemediationPlan.actions == []`, `placeholder_count == 0`.

`tests/coverages/test_signal_remediation_schema.py`:

- Load each coverage config; assert it parses without error (including the new `signal_remediation` block).
- Assert cyber config has every drag-eligible signal covered (whitelist test — list the drag-eligible signal_ids and assert each is present).
- Assert headline/description length caps enforced.
- Assert invalid effort enum rejected.

`tests/coverages/test_master_config_layout.py`:

- Schema version bumped.
- `signal_remediation` block validates.

### Step 6: Doc generator

Run `python coverages/doc_generator.py`. The doc generator may need a small update to include remediation entries in the rendered `logic.md` files — confirm during implementation and update if so. Add a section like "## Remediation Guidance" listing each signal's remediation block per coverage.

If updating the doc generator, include in this phase (single touch on `coverages/doc_generator.py`).

## Constraints & Principles

1. **YAML is truth.** Every remediation entry lives in YAML. No remediation strings hardcoded in Python.
2. **Honest under absence.** No authored remediation → explicit placeholder, tracked. Don't fake plausible-looking entries for missing signals.
3. **Audited via doc generator.** Every coverage's remediation is visible in its `logic.md`. Coverage debt (placeholders) is visible.
4. **Service is pure.** No DB access. Inputs: quote + coverage_config. Output: `RemediationPlan`.
5. **No workflow integration.** Phase 4 does not modify `workflow.py`. Computed on demand by Phase 6.
6. **Effort scale is fixed.** Three levels, multiplicative scores 1/3/9. Don't add a "VERY_HIGH" or change the multipliers — the demo's leverage ranking depends on this stable.
7. **Cyber must be complete.** No demo placeholder renders.

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Coverage authors disagree on effort categorisation | Three-level scale is coarse on purpose. Document the boundary criteria in the master layout. |
| Estimated premium delta is misleading if other signals change too | Show as "estimated, all else equal." UI copy must reflect this caveat (Phase 8 concern). |
| Placeholder count high for non-cyber coverages on launch | Acceptable — non-cyber not in demo. Track as v8.1 follow-on. |
| Coverage config schema bump breaks existing config validation | Phase E added `extra="forbid"`; the new field is added to the allowed set. Configs without the new block continue to validate (optional field). |
| Doc generator chokes on the new block | Phase 4 includes the doc generator update if needed. Single touch on `coverages/doc_generator.py`. |
| Generic placeholder language sounds canned in the UI | Acceptable for v8 — surfaces as a tooltip "no specific guidance" rather than fake-rich text. |

## Dependencies

- **Phase 1 complete** (schema stable).
- **Phase 3 complete** — `ImpactBreakdown.drags` shape is the input. If Phase 3 isn't done, this phase has no input to operate on.
- **v7 Phase 1 (Evidence Grade) compatibility**: if Evidence Grade ships first and bumps to 2.4, this phase bumps to 2.5. If not, this phase bumps to 2.4. Both paths are clean — no field collisions.

## Success Criteria

1. `master_config_layout.yaml` version bumped, `signal_remediation` block schema added.
2. Pydantic `SignalRemediation` model in config loader.
3. `CoverageConfig.signal_remediation: dict[str, SignalRemediation] | None` field present.
4. Every `coverages/<coverage>/config.yaml` parses cleanly under the new schema.
5. **Cyber config has remediation for every drag-eligible signal.** Whitelist test passes.
6. `layers/risk/remediation.py` exists with the four Pydantic models and `build_remediation_plan` function.
7. Sorting is leverage-desc, tier-transition first, |delta|-desc fallback.
8. Generic placeholder built for drags without authored remediation, `placeholder_count` tracked.
9. All Step 5 tests pass.
10. `python coverages/doc_generator.py` runs without error; remediation appears in `logic.md` per coverage.
11. Full `pytest tests/ -v` green.
12. No endpoints (Phase 6), no frontend (Phase 8), no seed (Phase 7) changes.

## Out of Scope (Phase 4)

- Endpoint exposure — Phase 6.
- Frontend rendering — Phase 8.
- Tracking remediation actions completed by the client (a "to do" feature) — v8.1+.
- Re-running an assessment with remediation simulated in (a "what-if" feature) — v8.1+ (could leverage Phase 3's `tier_transition` computation).
- Industry-tailored remediation language (NAICS-aware) — v8.1+.
- Authoring remediation for coverages other than cyber beyond the minimum 3 entries — coverage subject-matter pass, separate from v8.

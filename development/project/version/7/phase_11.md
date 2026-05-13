# V7 Phase 11: Variant Loop — Within-Cycle Amplification

## Depends on
- Phase 6 (validator-confirmed signals exist).
- Phase 10 (root-cause clusters exist; symptoms preserved).

## Blocks
- Phase 15 (frontend surfaces variant-discovered signals distinctly).

## Scope

Lifted from Clearwing's `variant_loop.py:38-98`. When a high-grade signal is confirmed by the validator (Phase 6) AND its root-cause cluster has ≥1 contributor (Phase 10), auto-generate **sibling queries** and run them within the same cycle. One confirmed STRUCTURED_ATTESTED sanctions hit becomes a search vector for related entities (subsidiaries, common officers, common addresses, alternate spellings).

Result is compounding finding density per entity per cycle without re-extracting the entire signal_registry.

The variant loop is **bounded**: per cycle, per entity, per fact_class, the loop produces at most N=5 sibling queries. Each sibling is itself a fresh extraction with full pipeline (extractor → aggregator → root-cause-clustering → validator), so siblings carry their own grades. Siblings cannot themselves spawn siblings — single-hop only.

## Decisions (locked)

| # | Decision | Choice |
|---|----------|--------|
| D1 | Trigger | Signal has `evidence_grade >= structured_attested` AND validator `advance=True` AND root-cause cluster has ≥1 deterministic contributor |
| D2 | Variant kinds | `name_variant`, `subsidiary`, `common_officer`, `common_address`, `alternate_jurisdiction` |
| D3 | Generation | LLM prompt that takes the confirmed signal + cluster + entity profile, returns up to N=5 typed variant queries |
| D4 | Fan-out cap | 5 variants per (signal_id, entity_id) per cycle. Hard cap; LLM is asked for exactly N |
| D5 | Single-hop | Variants do not themselves spawn variants. The metadata flag `variant_of` on a sibling SignalResult marks it as a hop-1 variant and the workflow refuses to spawn further hops |
| D6 | Score contribution | Variant findings score normally — they are real signals with real sources. **No special weight**. They are *amplifying* discovery, not synthetic signals |
| D7 | Audit | Each variant generation + each variant result logged to `compliance_audit_logs` with `event_type` in `{variant_generated, variant_extracted, variant_no_op}` |
| D8 | Toggleable | YAML `evidence_grade_policy.variant_loop: {enabled: bool, max_per_entity_per_cycle: int}`. Default `enabled: true`, `max_per_entity_per_cycle: 25` (i.e. up to 5 variants from each of 5 distinct triggering signals) |
| D9 | Concurrency | Variants extract concurrently via the existing extractor pool. Cap on wall-clock budget per variant: 30 seconds |
| D10 | No mechanism memory | Phase 12 stores **abstract patterns** across cycles; this phase fans out **concrete queries** within one cycle. Distinct |

## Files

### Create
- `signal_architecture/variants/__init__.py`
- `signal_architecture/variants/loop.py`
- `signal_architecture/variants/prompts.py`
- `signal_architecture/variants/types.py`
- `tests/unit/test_variant_loop.py`
- `tests/integration/test_variant_loop_end_to_end.py`

### Modify
- `signal_architecture/signals/types.py` — add `variant_of: Optional[str] = None` field (carries the parent `signal_id` if this `SignalResult` was discovered via the variant loop)
- `infrastructure/models/config_schema.py` — add `VariantLoopPolicy` to `EvidenceGradePolicy`
- `layers/risk/workflow.py` — after validator runs, run the variant loop. Variant results merged back into the cycle and re-scored

## Types

`signal_architecture/variants/types.py`:

```python
"""V7 Phase 11 — variant-loop types."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

VariantKind = Literal[
    "name_variant",
    "subsidiary",
    "common_officer",
    "common_address",
    "alternate_jurisdiction",
]


@dataclass(frozen=True)
class VariantQuery:
    """One generated query: a typed, bounded sibling-search recipe."""
    kind: VariantKind
    target_ref: str         # the candidate entity/officer/address/etc
    rationale: str          # ≤200 chars, from the LLM
    parent_signal_id: str
    parent_cluster_id: str


@dataclass
class VariantResult:
    query: VariantQuery
    success: bool
    signal_id: str | None       # if a signal was actually produced
    grade: str | None
    note: str = ""
```

## Loop

`signal_architecture/variants/loop.py`:

```python
"""V7 Phase 11 — within-cycle variant amplification.

Public API:
    run_variant_loop(workflow_ctx, confirmed_signals, *, policy) -> list[SignalResult]
"""
from __future__ import annotations

import asyncio
import logging
from typing import Iterable

from signal_architecture.signals.types import SignalResult
from .types import VariantKind, VariantQuery, VariantResult
from .prompts import generate_variants_for

logger = logging.getLogger("dsi.variant_loop")


VARIANT_BUDGET_SECONDS = 30


def _is_trigger(sig: SignalResult, validator_verdicts: dict[str, "ValidatorVerdict"]) -> bool:
    if sig.variant_of is not None:
        return False  # already a hop-1 variant; no further hops
    if sig.evidence_grade not in ("structured_attested", "behaviourally_validated"):
        return False
    v = validator_verdicts.get(sig.signal_id)
    if v is None or not v.advance:
        return False
    if not sig.metadata or not sig.metadata.get("cluster_id"):
        return False
    if sig.metadata.get("deterministic") is False:
        return False
    return True


async def _extract_one_variant(workflow_ctx, q: VariantQuery) -> VariantResult:
    try:
        result = await asyncio.wait_for(
            workflow_ctx.extract_for_variant(q),  # workflow helper, see step 11.5
            timeout=VARIANT_BUDGET_SECONDS,
        )
    except asyncio.TimeoutError:
        return VariantResult(query=q, success=False, signal_id=None, grade=None, note="timeout")
    except Exception as e:  # noqa: BLE001
        return VariantResult(query=q, success=False, signal_id=None, grade=None, note=f"error:{e}")
    if result is None:
        return VariantResult(query=q, success=False, signal_id=None, grade=None, note="no_result")
    # Tag the variant
    result.variant_of = q.parent_signal_id
    result.metadata = (result.metadata or {}) | {
        "variant_kind": q.kind,
        "variant_target_ref": q.target_ref,
        "variant_parent_cluster_id": q.parent_cluster_id,
    }
    return VariantResult(query=q, success=True, signal_id=result.signal_id, grade=result.evidence_grade)


async def run_variant_loop(
    workflow_ctx,
    triggers: Iterable[SignalResult],
    *,
    policy,
    validator_verdicts: dict,
) -> list[SignalResult]:
    enabled_triggers = [s for s in triggers if _is_trigger(s, validator_verdicts)]
    if not enabled_triggers:
        return []
    cap_per_entity = policy.variant_loop.max_per_entity_per_cycle

    queries: list[VariantQuery] = []
    for sig in enabled_triggers:
        new_qs = generate_variants_for(workflow_ctx.llm, sig, max_n=5)
        queries.extend(new_qs)
        workflow_ctx.audit("variant_generated", signal_id=sig.signal_id, payload={
            "parent_cluster_id": sig.metadata["cluster_id"],
            "count": len(new_qs),
        })

    if len(queries) > cap_per_entity:
        queries = queries[:cap_per_entity]

    results = await asyncio.gather(*[
        _extract_one_variant(workflow_ctx, q) for q in queries
    ])

    new_signals: list[SignalResult] = []
    for r in results:
        if r.success:
            new_signals.append(workflow_ctx.signal_by_id(r.signal_id))  # the freshly stored result
            workflow_ctx.audit("variant_extracted", signal_id=r.signal_id, payload={
                "parent": r.query.parent_signal_id, "kind": r.query.kind,
            })
        else:
            workflow_ctx.audit("variant_no_op", signal_id=None, payload={
                "parent": r.query.parent_signal_id, "kind": r.query.kind, "note": r.note,
            })
    return new_signals
```

## Variant generation prompt

`signal_architecture/variants/prompts.py`:

```python
"""V7 Phase 11 — LLM prompt for variant generation.

Input: the confirmed signal + its cluster + the entity profile (name,
country, sector). Output: up to N=5 typed variant queries.
"""
from __future__ import annotations

import json
import re
from typing import List

from signal_architecture.signals.types import SignalResult
from .types import VariantKind, VariantQuery


SYSTEM = """\
You generate at most {n} SEARCH QUERIES that hunt for sibling findings related
to a verified signal. Each query is typed by kind:

  name_variant            — alternate spelling / former name of the same entity
  subsidiary              — known or likely subsidiary
  common_officer          — director / officer that may sit on related boards
  common_address          — registered address that suggests group affiliation
  alternate_jurisdiction  — same entity registered in another country

Output JSON ONLY:
{{
  "variants": [
    {{"kind": "name_variant", "target_ref": "...", "rationale": "..."}},
    ...
  ]
}}
"""

VALID_KINDS = {"name_variant", "subsidiary", "common_officer", "common_address", "alternate_jurisdiction"}


def _user(sig: SignalResult) -> str:
    return json.dumps({
        "signal_id": sig.signal_id,
        "score": sig.score,
        "category": sig.category,
        "evidence_basis": sig.evidence_basis,
        "evidence_grade": sig.evidence_grade,
        "cluster_id": sig.metadata.get("cluster_id"),
        "fact_class": sig.metadata.get("fact_class"),
        "symptoms_sample": (sig.metadata.get("symptoms") or [])[:3],
    }, indent=2)


def generate_variants_for(llm, sig: SignalResult, *, max_n: int = 5) -> List[VariantQuery]:
    response = llm.aask_text(
        system=SYSTEM.format(n=max_n),
        user=_user(sig),
    ).first_text() or ""
    match = re.search(r"\{[\s\S]*\}", response)
    if not match:
        return []
    try:
        data = json.loads(match.group(0))
    except json.JSONDecodeError:
        return []
    queries: List[VariantQuery] = []
    for v in data.get("variants", []):
        kind = v.get("kind")
        if kind not in VALID_KINDS:
            continue
        target = (v.get("target_ref") or "").strip()
        if not target:
            continue
        rationale = (v.get("rationale") or "")[:200]
        queries.append(VariantQuery(
            kind=kind,
            target_ref=target,
            rationale=rationale,
            parent_signal_id=sig.signal_id,
            parent_cluster_id=sig.metadata["cluster_id"],
        ))
        if len(queries) >= max_n:
            break
    return queries
```

## Workflow integration

`layers/risk/workflow.py` extension:

```python
from signal_architecture.variants.loop import run_variant_loop


async def _run_phase_11_variants(self, ctx, signals_after_validator, validator_verdicts, policy):
    if not policy.variant_loop.enabled:
        return []
    new_signals = await run_variant_loop(
        workflow_ctx=ctx,
        triggers=signals_after_validator,
        policy=policy,
        validator_verdicts=validator_verdicts,
    )
    return new_signals
```

After variant signals are produced, the workflow:

1. Re-runs the aggregators (clusters may absorb a variant if it falls within an existing event window).
2. Re-runs the validator on any newly-emitted high-grade signal.
3. Re-rolls up group / composite grade.
4. Re-evaluates `evidence_grade_policy` referrals.
5. Commits via Phase 5 stores. Persisted `metadata.variant_of` is searchable.

Re-running these steps is bounded: variants do not themselves spawn variants (D5), so the recursion is one level deep.

## Pydantic policy

`infrastructure/models/config_schema.py`:

```python
class VariantLoopPolicy(StrictModel):
    enabled: bool = True
    max_per_entity_per_cycle: int = Field(default=25, ge=0, le=200)


class EvidenceGradePolicy(StrictModel):
    # ... existing fields ...
    variant_loop: VariantLoopPolicy = Field(default_factory=VariantLoopPolicy)
```

## Steps

### 11.1 — Types and prompts
**Files**: `signal_architecture/variants/{__init__,types,prompts}.py`.
**Action**: Drop in code.

### 11.2 — Loop module
**File**: `signal_architecture/variants/loop.py`.
**Action**: Drop in code.
**Test**: `tests/unit/test_variant_loop.py`:
- `_is_trigger` returns False for graded-below-structured-attested, validator-rejected, no-cluster, variant-already.
- Cap enforced.
- Single-hop enforced.
- Audit events emitted at the right boundaries (use a mock `workflow_ctx`).

### 11.3 — Workflow ctx helper
**File**: `layers/risk/workflow.py`.
**Action**: Add three helper methods on the workflow object the loop calls:
- `extract_for_variant(query) -> SignalResult | None` — resolves an inference function based on `query.kind`, runs it with `query.target_ref` as the entity, returns the produced signal.
- `signal_by_id(signal_id) -> SignalResult` — lookup after extraction.
- `audit(event_type, signal_id, payload)` — wraps `compliance_audit_store.log_event`.

### 11.4 — Pydantic schema
**File**: `infrastructure/models/config_schema.py`.
**Action**: Add `VariantLoopPolicy`.

### 11.5 — Rollout the policy block to existing configs
**File**: `scripts/add_evidence_grade_policy.py` (extend) OR a sibling script. Make it idempotent (re-running over a config that already has `variant_loop:` is a no-op).
**Action**: Inject:
```yaml
evidence_grade_policy:
  variant_loop:
    enabled: true
    max_per_entity_per_cycle: 25
```

### 11.6 — End-to-end test
**File**: `tests/integration/test_variant_loop_end_to_end.py`.
**Action**: Build a fake cycle with one confirmed STRUCTURED_ATTESTED sanctions hit. Mock the LLM to return 2 variants (one subsidiary, one common_officer). Mock the extractors to return one valid result and one no-op. Assert: one new SignalResult lands with `variant_of=` set; audit events `variant_generated`, `variant_extracted`, `variant_no_op` all written; commit includes the new signal.

## Test gates

```bash
pytest tests/unit/test_variant_loop.py tests/integration/test_variant_loop_end_to_end.py -v
pytest tests/ -x -q

python -m seed bench
psql -c "SELECT event_type, COUNT(*) FROM compliance_audit_logs WHERE event_type LIKE 'variant_%' GROUP BY event_type"

# Calibration unchanged: variant findings are real signals that score normally;
# in seed bench (synthetic) they may or may not appear. Either way no drift.
python -m layers.risk.calibration_harness fi cyber casualty
```

## Done when

- [ ] Variants generated only for graded-structured-attested + validator-advanced + clustered signals.
- [ ] Hard cap of 25 per cycle per entity enforced.
- [ ] Single-hop enforced: `variant_of` populated, and variant signals never spawn further variants.
- [ ] Variant signals carry `variant_of`, `metadata.variant_kind`, `metadata.variant_target_ref`, `metadata.variant_parent_cluster_id`.
- [ ] Audit events `variant_generated`, `variant_extracted`, `variant_no_op` land in `compliance_audit_logs`.
- [ ] Re-aggregation, re-validation, re-rollup all run after variants.
- [ ] Calibration unchanged on seed.
- [ ] Full pytest green.

## Out of scope

- Variant generation for non-cluster signals. → out of V7.
- Multi-hop. → forbidden.
- Variant-specific score weighting. → forbidden by D6.
- Frontend display of variant-discovered signals. → Phase 15.

## Invariants

1. No variant signal spawns further variants.
2. Per cycle, per entity, total variant signals committed ≤ `max_per_entity_per_cycle`.
3. Every variant signal has a populated `variant_of` and the parent's `cluster_id` in metadata.
4. Variant extraction respects the per-source TTL cache and rate limits.
5. Pricing impact only from genuine real-source signals that variants happen to discover — not from synthetic amplification.

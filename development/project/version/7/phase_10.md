# V7 Phase 10: Root-Cause Dedup Audit

## Depends on
- Phase 9 (`primitive_type` populated on every signal).
- Phase 3 (promotion-merge in aggregators).

## Blocks
- Phase 11 (variant loop fans out from confirmed root-cause clusters).
- Phase 12 (mechanism memory keys on root-cause primitives, not symptoms).

## Scope

Audit and refactor the routing-aggregators (`sanctions_aggregator.py`, `corporate_aggregator.py`) — and any other multi-source aggregator — to cluster contributing observations by **root cause**, not by surface symptom. Lifted from Clearwing's `findings_pool.py:128-143` rule: *"Two bugs with identical stack traces but different root causes are NOT duplicates. One bug presenting with different crashes IS a duplicate."*

DSI analog: a single OFAC hit surfaced via CourtListener + state-court index + a wire-news mention is **one event**, not three signals. A litigation against the same director by two unrelated plaintiffs over different facts is **two events** even if the search returns near-identical case names.

Introduces a `RootCauseCluster` concept persisted alongside each `SignalResult` that aggregates multiple sources. The aggregator emits one signal per cluster, with `evidence_sources` listing every contributor.

## Decisions (locked)

| # | Decision | Choice |
|---|----------|--------|
| D1 | Clustering scope | Per (entity_id, primitive_type) window. Sanctions, litigation, regulatory actions, news/sentiment are the high-priority aggregators |
| D2 | Cluster key | A composite key: `(canonical_entity_ref, event_date_bucket, fact_class)` where `fact_class` is per-aggregator (e.g. `sdn_listing`, `civil_case_filing`, `enforcement_action`) |
| D3 | Equivalence | Deterministic first (e.g. matching OFAC list ID, court case docket, FCA reference number). LLM dedup is fallback only — never as primary clustering signal |
| D4 | Date bucket | ±30 days for legal/regulatory events; ±7 days for press/media |
| D5 | Emitted signal | One `SignalResult` per cluster. `evidence_basis` names the event; `evidence_sources` lists every contributing source; `evidence_pro` collects supporting facts; `evidence_counter` collects contradictions |
| D6 | Symptom retention | Symptoms preserved in `metadata["symptoms"]: list[dict]` — every individual hit kept verbatim for audit. Cluster ID stored in `metadata["cluster_id"]` |
| D7 | Backward compat | Existing `sanctions_aggregator.py` and `corporate_aggregator.py` interfaces unchanged from the caller's perspective. Internal refactor only |
| D8 | LLM dedup gating | Only invoked when ≥2 candidate clusters have the same `fact_class` AND their `canonical_entity_ref` strings are >0.85 Levenshtein-similar (suggests possible same-event-renamed) |
| D9 | Audit | Every clustering decision logged to `compliance_audit_logs` with `event_type="root_cause_cluster"` and payload `{cluster_id, contributor_count, deterministic_key, llm_invoked}` |
| D10 | Test fixture | Add `tests/fixtures/root_cause_dedup/` with positive and negative pairs hand-curated for sanctions and litigation |

## Files

### Create
- `signal_architecture/signals/routing/root_cause_cluster.py` — pure clustering logic
- `signal_architecture/signals/routing/dedup_keys.py` — per-fact-class canonicalisation rules
- `tests/unit/test_root_cause_cluster.py`
- `tests/integration/test_sanctions_aggregator_dedup.py`
- `tests/integration/test_corporate_aggregator_dedup.py`
- `tests/fixtures/root_cause_dedup/` (fixture files)

### Modify
- `signal_architecture/signals/routing/sanctions_aggregator.py` — replace symptom-grouping with cluster-grouping (caller-visible behaviour unchanged for happy path; aggregated counts and grades now reflect cluster counts)
- `signal_architecture/signals/routing/corporate_aggregator.py` — same
- Any other aggregator in `signal_architecture/signals/aggregators/implementations/` that combines >1 record into a single signal — apply the pattern

## Cluster module

`signal_architecture/signals/routing/root_cause_cluster.py`:

```python
"""V7 Phase 10 — root-cause clustering of multi-source observations.

Input: a list of `ContributingObservation` records from disparate sources.
Output: a list of `RootCauseCluster` objects, one per distinct event.
Each cluster carries the contributors, a canonical key, and a
deterministic_or_llm flag.
"""
from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Callable, Optional, Sequence

from signal_architecture.signals.evidence import EvidenceSource


@dataclass(frozen=True)
class ContributingObservation:
    """One hit from one source. The aggregator builds these from raw extractor output."""
    source_id: str           # 'ofac', 'courtlistener', 'sec_edgar', ...
    canonical_entity_ref: str  # normalised entity-or-event identifier
    event_date: Optional[datetime]
    fact_class: str          # 'sdn_listing' | 'civil_case_filing' | 'enforcement_action' | 'news_event'
    deterministic_key: Optional[str]  # e.g. OFAC ID, court docket
    payload: dict            # full original record — kept for the symptom log
    evidence_source: EvidenceSource


@dataclass
class RootCauseCluster:
    cluster_id: str
    fact_class: str
    canonical_entity_ref: str
    event_date_bucket: Optional[str]  # ISO date of bucket centre
    contributors: list[ContributingObservation] = field(default_factory=list)
    deterministic: bool = True  # False if LLM dedup was involved


def _bucket_for(d: Optional[datetime], width_days: int) -> Optional[str]:
    if d is None:
        return None
    epoch = d - timedelta(days=d.day % width_days)
    return epoch.date().isoformat()


def _bucket_width(fact_class: str) -> int:
    return 7 if fact_class in {"news_event", "media_mention"} else 30


def _candidate_key(obs: ContributingObservation) -> str:
    """Deterministic cluster key for fast first-pass grouping."""
    if obs.deterministic_key:
        return f"{obs.fact_class}::{obs.deterministic_key}"
    width = _bucket_width(obs.fact_class)
    return f"{obs.fact_class}::{obs.canonical_entity_ref}::{_bucket_for(obs.event_date, width)}"


def cluster_deterministic(observations: Sequence[ContributingObservation]) -> list[RootCauseCluster]:
    """First pass: deterministic grouping by key. No LLM."""
    by_key: dict[str, RootCauseCluster] = {}
    for obs in observations:
        key = _candidate_key(obs)
        c = by_key.get(key)
        if c is None:
            c = RootCauseCluster(
                cluster_id=_uuid_for_key(key),
                fact_class=obs.fact_class,
                canonical_entity_ref=obs.canonical_entity_ref,
                event_date_bucket=_bucket_for(obs.event_date, _bucket_width(obs.fact_class)),
                deterministic=True,
            )
            by_key[key] = c
        c.contributors.append(obs)
    return list(by_key.values())


def _uuid_for_key(key: str) -> str:
    return str(uuid.UUID(bytes=hashlib.md5(key.encode("utf-8")).digest()))


# ---------------------------------------------------------------------------
# Optional LLM merge over near-duplicate clusters
# ---------------------------------------------------------------------------

def _levenshtein_ratio(a: str, b: str) -> float:
    """Tiny pure-python implementation. Avoids adding a dependency."""
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    if a == b:
        return 1.0
    m = len(a)
    n = len(b)
    prev = list(range(n + 1))
    for i, ca in enumerate(a, 1):
        curr = [i] + [0] * n
        for j, cb in enumerate(b, 1):
            ins = curr[j - 1] + 1
            dele = prev[j] + 1
            sub = prev[j - 1] + (ca != cb)
            curr[j] = min(ins, dele, sub)
        prev = curr
    dist = prev[-1]
    return 1.0 - dist / max(m, n)


def maybe_llm_merge(
    clusters: list[RootCauseCluster],
    *,
    llm_callable: Optional[Callable[[RootCauseCluster, RootCauseCluster], bool]] = None,
    similarity_floor: float = 0.85,
) -> list[RootCauseCluster]:
    """Second pass: look at near-duplicate clusters (same fact_class,
    >0.85 ref similarity) and ask the LLM whether they're the same event.
    No-op when `llm_callable is None`.
    """
    if llm_callable is None or len(clusters) < 2:
        return clusters
    merged: list[RootCauseCluster] = []
    consumed: set[str] = set()
    by_fact: dict[str, list[RootCauseCluster]] = {}
    for c in clusters:
        by_fact.setdefault(c.fact_class, []).append(c)
    for fact_class, group in by_fact.items():
        for i, a in enumerate(group):
            if a.cluster_id in consumed:
                continue
            for b in group[i + 1:]:
                if b.cluster_id in consumed:
                    continue
                sim = _levenshtein_ratio(a.canonical_entity_ref, b.canonical_entity_ref)
                if sim < similarity_floor:
                    continue
                if llm_callable(a, b):
                    a.contributors.extend(b.contributors)
                    a.deterministic = False
                    consumed.add(b.cluster_id)
            merged.append(a)
    # any clusters not in by_fact map (none — but defensive)
    for c in clusters:
        if c.cluster_id not in consumed and not any(c.cluster_id == m.cluster_id for m in merged):
            merged.append(c)
    return merged
```

## Sanctions aggregator refactor

`signal_architecture/signals/routing/sanctions_aggregator.py` outline of the change:

```python
from .root_cause_cluster import (
    ContributingObservation, cluster_deterministic, maybe_llm_merge,
)

def aggregate(self, extractor_results, *, entity_id, llm=None):
    observations: list[ContributingObservation] = []
    for er in extractor_results:
        for hit in self._hits_from(er):
            observations.append(ContributingObservation(
                source_id=er.source,
                canonical_entity_ref=self._canonicalise(hit["name"]),
                event_date=self._parse_date(hit.get("listed_on")),
                fact_class="sdn_listing",
                deterministic_key=hit.get("list_id"),
                payload=hit,
                evidence_source=self._evidence_source_for(er, hit),
            ))

    clusters = cluster_deterministic(observations)
    clusters = maybe_llm_merge(clusters, llm_callable=(
        self._llm_dedup(llm) if llm else None
    ))

    signals: list[SignalResult] = []
    for c in clusters:
        signals.append(self._build_signal_from_cluster(c))
    return signals
```

The `_build_signal_from_cluster` helper:

```python
def _build_signal_from_cluster(self, cluster: RootCauseCluster) -> SignalResult:
    # Promotion: cluster of N independent sources → corroborated (or higher if any is structured_attested)
    sources = [obs.evidence_source for obs in cluster.contributors]
    grade = "observed"
    for obs in cluster.contributors:
        if obs.evidence_source.kind == "register":
            grade = bump_evidence(grade, "structured_attested")
        elif len(cluster.contributors) > 1:
            grade = bump_evidence(grade, "corroborated")

    basis = (
        f"Cluster of {len(cluster.contributors)} contributors; "
        f"fact_class={cluster.fact_class}; "
        f"key={cluster.canonical_entity_ref}; "
        f"date_bucket={cluster.event_date_bucket}"
    )[:500]

    return SignalResult(
        signal_id=self.SIGNAL_ID,
        score=...,  # aggregator-specific scoring
        confidence=...,
        evidence_grade=grade,
        evidence_basis=basis,
        evidence_sources=sources,
        metadata={
            "cluster_id": cluster.cluster_id,
            "fact_class": cluster.fact_class,
            "symptoms": [obs.payload for obs in cluster.contributors],
            "deterministic": cluster.deterministic,
        },
    )
```

## Audit hook

After clustering, the aggregator logs:

```python
from infrastructure.db.compliance_audit_store import log_event

for cluster in clusters:
    log_event(
        db, event_type="root_cause_cluster",
        signal_id=self.SIGNAL_ID,
        payload={
            "cluster_id": cluster.cluster_id,
            "fact_class": cluster.fact_class,
            "canonical_entity_ref": cluster.canonical_entity_ref,
            "contributor_count": len(cluster.contributors),
            "deterministic": cluster.deterministic,
        },
    )
```

## Steps

### 10.1 — Cluster module
**File**: `signal_architecture/signals/routing/root_cause_cluster.py`.
**Action**: Drop in code.
**Test**: `tests/unit/test_root_cause_cluster.py`:
- Same OFAC list ID across 3 sources → 1 cluster.
- Different list IDs but same name + same week → 2 clusters (deterministic key is the list ID, distinct keys mean distinct clusters).
- Same canonical_entity_ref + same date bucket, no deterministic key → 1 cluster.
- LLM merge collapses 0.90-similar refs when the mock LLM returns True; leaves them distinct when False.

### 10.2 — Canonicalisation rules
**File**: `signal_architecture/signals/routing/dedup_keys.py`.
**Action**: Per-fact-class canonicalisation:
```python
def canonicalise_entity_name(name: str) -> str:
    # lowercase, strip Ltd/Inc/PLC/AG/SA suffixes, drop punctuation, collapse whitespace
    ...

def canonicalise_docket(docket: str) -> str:
    # Strip court prefix, normalise case-number form
    ...
```

### 10.3 — Refactor sanctions_aggregator
**File**: `signal_architecture/signals/routing/sanctions_aggregator.py`.
**Action**: Replace existing per-hit grouping with the cluster pattern. Re-test against existing fixtures and the new ones.
**Test**: `tests/integration/test_sanctions_aggregator_dedup.py`:
- Three different feeds reporting the same SDN listing → one signal with cluster_id, three sources, grade `structured_attested`.
- Two genuinely different listings → two signals, different cluster_ids.

### 10.4 — Refactor corporate_aggregator
**File**: `signal_architecture/signals/routing/corporate_aggregator.py`.
**Action**: Apply the same pattern to corporate registry hits (Companies House + state secretary of state + Bloomberg corporate).

### 10.5 — Apply to other multi-source aggregators
**Find**:
```bash
grep -rln "def aggregate" signal_architecture/signals/aggregators/implementations/
grep -rln "def aggregate" signal_architecture/signals/routing/
```
**Action**: Audit each. For aggregators that today produce one signal per source hit, refactor to cluster-and-emit-per-cluster. Don't change scoring logic — only the grouping.

### 10.6 — Audit logging
**Files**: every refactored aggregator.
**Action**: Insert `log_event("root_cause_cluster", ...)` at the end of clustering. Test: `tests/integration/test_root_cause_audit.py` asserts an audit row exists per cluster.

### 10.7 — Test fixtures
**Path**: `tests/fixtures/root_cause_dedup/`.
**Action**: Hand-curated fixtures: 5 positive pairs (same event, different sources), 5 negative pairs (different events, similar names), per fact_class. Used by both unit and integration tests.

## Test gates

```bash
pytest tests/unit/test_root_cause_cluster.py -v
pytest tests/integration/test_sanctions_aggregator_dedup.py \
        tests/integration/test_corporate_aggregator_dedup.py \
        tests/integration/test_root_cause_audit.py -v
pytest tests/ -x -q

# Calibration unchanged (clustering doesn't change scores in the happy path
# — same N hits cluster to 1 signal with weighted score still in the
# correct band)
python -m layers.risk.calibration_harness fi cyber casualty
```

## Done when

- [ ] `cluster_deterministic` covers all five fact_classes used by current aggregators.
- [ ] `sanctions_aggregator` and `corporate_aggregator` emit one signal per cluster.
- [ ] Symptom payloads preserved in `metadata["symptoms"]`.
- [ ] Cluster id present on every signal emitted from a refactored aggregator.
- [ ] LLM merge gated by 0.85 similarity floor and same fact_class.
- [ ] Audit log row per cluster.
- [ ] Calibration unchanged.
- [ ] Full pytest green.

## Out of scope

- Cross-entity cluster sharing (would let one company's confirmed sanctions cluster pre-populate against affiliates). → V8.
- LLM dedup as primary clustering. → forbidden by D3.
- Replacing the per-fact-class canonicalisation with NLP entity-resolution. → too heavyweight for V7.

## Invariants

1. Deterministic key match always wins. LLM is only invoked when no deterministic key exists for a pair AND they're >0.85 similar.
2. No information is lost: `metadata["symptoms"]` carries every contributing hit verbatim.
3. Every cluster decision is logged to `compliance_audit_logs`.
4. Pricing outputs unchanged (same N contributors → same aggregated score).

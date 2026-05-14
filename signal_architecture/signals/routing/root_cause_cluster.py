"""V7 Phase 10 — root-cause clustering of multi-source observations.

Lifted from Clearwing's findings_pool rule: two reports with identical
surface symptoms but different root causes are NOT duplicates; one root
cause presenting through different symptoms IS a duplicate.

DSI analog: a single OFAC SDN listing surfaced via OpenSanctions + a
state-court index + a wire-news mention is ONE event, not three signals.
Two genuinely distinct enforcement actions against the same entity are
TWO events even when their names look near-identical.

Pipeline:
    observations  -> cluster_deterministic()  -> clusters
                  -> maybe_llm_merge()        -> merged clusters

`cluster_deterministic` groups by a deterministic key (an authoritative
ID where available, else fact_class + canonical_entity_ref + date bucket).
`maybe_llm_merge` is an optional second pass that only looks at
near-duplicate clusters of the same fact_class — it never runs as the
primary clustering signal.
"""
from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Callable, Optional, Sequence


@dataclass(frozen=True)
class ContributingObservation:
    """One hit from one source. The aggregator builds these from raw matches."""
    source_id: str               # 'ofac', 'opensanctions', 'companies_house', ...
    canonical_entity_ref: str    # normalised entity-or-event identifier
    event_date: Optional[datetime]
    fact_class: str              # 'sdn_listing' | 'corporate_record' | 'enforcement_action' | ...
    deterministic_key: Optional[str]  # authoritative ID (OFAC list ID, LEI, docket) or None
    payload: dict                # full original record — kept for the symptom log
    weight: float = 1.0          # match_score-derived weight, if available


@dataclass
class RootCauseCluster:
    """One distinct event, assembled from >=1 contributing observation."""
    cluster_id: str
    fact_class: str
    canonical_entity_ref: str
    event_date_bucket: Optional[str]  # ISO date of the bucket centre
    contributors: list[ContributingObservation] = field(default_factory=list)
    deterministic: bool = True        # False if an LLM merge was involved

    @property
    def contributor_count(self) -> int:
        return len(self.contributors)

    @property
    def source_ids(self) -> list[str]:
        # Stable, de-duplicated list of contributing source IDs.
        seen: list[str] = []
        for obs in self.contributors:
            if obs.source_id not in seen:
                seen.append(obs.source_id)
        return seen

    @property
    def symptoms(self) -> list[dict]:
        """Every contributing observation's raw payload — the audit trail."""
        return [obs.payload for obs in self.contributors]

    def to_summary(self) -> dict:
        """Compact audit-log-friendly summary."""
        return {
            "cluster_id": self.cluster_id,
            "fact_class": self.fact_class,
            "canonical_entity_ref": self.canonical_entity_ref,
            "event_date_bucket": self.event_date_bucket,
            "contributor_count": self.contributor_count,
            "source_ids": self.source_ids,
            "deterministic": self.deterministic,
        }


# ---------------------------------------------------------------------------
# Date bucketing
# ---------------------------------------------------------------------------

# Legal / regulatory events get a wider window than press mentions.
_BUCKET_WIDTH_DAYS = {
    "news_event": 7,
    "media_mention": 7,
}
_DEFAULT_BUCKET_WIDTH = 30


def _bucket_width(fact_class: str) -> int:
    return _BUCKET_WIDTH_DAYS.get(fact_class, _DEFAULT_BUCKET_WIDTH)


def _bucket_for(d: Optional[datetime], width_days: int) -> Optional[str]:
    """Quantise a date to a bucket-aligned ISO date string."""
    if d is None:
        return None
    # Align to a width-day grid anchored at the epoch so the same event
    # date always lands in the same bucket regardless of observation order.
    ordinal = d.toordinal()
    aligned = ordinal - (ordinal % width_days)
    return datetime.fromordinal(aligned).date().isoformat()


def _candidate_key(obs: ContributingObservation) -> str:
    """Deterministic cluster key.

    Authoritative ID wins outright (an OFAC list ID identifies the listing
    no matter who reported it). Without one, fall back to fact_class +
    canonical_entity_ref + date bucket.
    """
    if obs.deterministic_key:
        return f"{obs.fact_class}::id::{obs.deterministic_key}"
    width = _bucket_width(obs.fact_class)
    bucket = _bucket_for(obs.event_date, width)
    return f"{obs.fact_class}::{obs.canonical_entity_ref}::{bucket}"


def _uuid_for_key(key: str) -> str:
    """Stable cluster_id derived from the cluster key (md5 -> UUID)."""
    return str(uuid.UUID(bytes=hashlib.md5(key.encode("utf-8")).digest()))


# ---------------------------------------------------------------------------
# Pass 1 — deterministic clustering
# ---------------------------------------------------------------------------

def cluster_deterministic(
    observations: Sequence[ContributingObservation],
) -> list[RootCauseCluster]:
    """Group observations by deterministic key. No LLM. Order-independent."""
    by_key: dict[str, RootCauseCluster] = {}
    for obs in observations:
        key = _candidate_key(obs)
        cluster = by_key.get(key)
        if cluster is None:
            cluster = RootCauseCluster(
                cluster_id=_uuid_for_key(key),
                fact_class=obs.fact_class,
                canonical_entity_ref=obs.canonical_entity_ref,
                event_date_bucket=_bucket_for(obs.event_date, _bucket_width(obs.fact_class)),
                deterministic=True,
            )
            by_key[key] = cluster
        cluster.contributors.append(obs)
    # Deterministic output ordering — sorted by cluster_id.
    return sorted(by_key.values(), key=lambda c: c.cluster_id)


# ---------------------------------------------------------------------------
# Pass 2 — optional LLM merge over near-duplicate clusters
# ---------------------------------------------------------------------------

def _levenshtein_ratio(a: str, b: str) -> float:
    """Pure-python similarity ratio in [0, 1]. Avoids adding a dependency."""
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    if a == b:
        return 1.0
    m, n = len(a), len(b)
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
    """Second pass: collapse near-duplicate clusters that the deterministic
    pass couldn't merge (no shared authoritative ID).

    Only pairs of the SAME fact_class with >= `similarity_floor` ref
    similarity are even shown to the LLM. No-op when `llm_callable is None`.
    The LLM is NEVER the primary clustering signal — it only adjudicates
    near-duplicates the deterministic pass left apart.
    """
    if llm_callable is None or len(clusters) < 2:
        return clusters

    by_fact: dict[str, list[RootCauseCluster]] = {}
    for c in clusters:
        by_fact.setdefault(c.fact_class, []).append(c)

    consumed: set[str] = set()
    merged: list[RootCauseCluster] = []

    for group in by_fact.values():
        # Stable iteration order.
        group = sorted(group, key=lambda c: c.cluster_id)
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

    # Any cluster not consumed and not already in `merged` (defensive).
    merged_ids = {c.cluster_id for c in merged}
    for c in clusters:
        if c.cluster_id not in consumed and c.cluster_id not in merged_ids:
            merged.append(c)

    return sorted(merged, key=lambda c: c.cluster_id)

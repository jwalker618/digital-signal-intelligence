"""V7 Phase 11 — variant-generation LLM prompt.

Given a validator-confirmed parent signal + its root-cause cluster, the
LLM proposes up to N typed sibling queries. Output is strict JSON; any
field of unknown shape is silently dropped (the loop runner rejects junk
quietly rather than failing the cycle).
"""
from __future__ import annotations

import json
import re
from typing import List

from signal_architecture.signals.types import SignalResult

from .types import VariantQuery, VARIANT_KINDS

_VALID_KINDS: frozenset[str] = frozenset(VARIANT_KINDS)


SYSTEM = """\
You generate at most {n} SEARCH QUERIES that hunt for sibling findings
related to a verified signal. Each query is typed by kind:

  name_variant            — alternate spelling / former name of the same entity
  subsidiary              — known or likely subsidiary
  common_officer          — director / officer that may sit on related boards
  common_address          — registered address that suggests group affiliation
  alternate_jurisdiction  — same entity registered in another country

Constraints:
  - Return at most {n} variants total.
  - Each `target_ref` must be a concrete string the system can search for.
  - Each `rationale` must be <=200 chars.
  - Do NOT propose variants that the verified signal already covers.

Output JSON ONLY (no prose, no markdown fences):
{{
  "variants": [
    {{"kind": "name_variant", "target_ref": "...", "rationale": "..."}},
    ...
  ]
}}
"""

_JSON_RE = re.compile(r"\{[\s\S]*\}")


def _build_user(sig: SignalResult) -> str:
    """Compact JSON view of the parent signal + cluster for the LLM."""
    md = sig.metadata or {}
    payload = {
        "signal_id": sig.signal_id,
        "score": sig.score,
        "category": sig.category,
        "evidence_basis": sig.evidence_basis,
        "evidence_grade": sig.evidence_grade,
        "cluster_id": md.get("cluster_id"),
        "fact_class": md.get("fact_class"),
        # Sample (not all) symptoms — keeps the prompt small.
        "symptoms_sample": (md.get("symptoms") or [])[:3],
    }
    return json.dumps(payload, indent=2, sort_keys=True, default=str)


def generate_variants_for(
    llm_callable,
    sig: SignalResult,
    *,
    max_n: int = 5,
) -> List[VariantQuery]:
    """Produce up to `max_n` typed variant queries for `sig`.

    `llm_callable` is the (system: str, user: str) -> str protocol used
    elsewhere in V7. Returns [] on LLM error, unparseable JSON, or no
    well-formed variants. Caller is responsible for the cap enforcement
    AND for refusing to run when sig.variant_of is already set
    (single-hop invariant).
    """
    md = sig.metadata or {}
    cluster_id = md.get("cluster_id")
    if not cluster_id:
        # Variants require a parent cluster — bail.
        return []

    try:
        raw = llm_callable(system=SYSTEM.format(n=max_n), user=_build_user(sig)) or ""
    except Exception:  # noqa: BLE001
        return []

    match = _JSON_RE.search(raw)
    if not match:
        return []
    try:
        data = json.loads(match.group(0))
    except json.JSONDecodeError:
        return []

    queries: List[VariantQuery] = []
    seen_refs: set[tuple[str, str]] = set()  # (kind, target_ref) dedup
    for entry in (data.get("variants") or []):
        if not isinstance(entry, dict):
            continue
        kind = entry.get("kind")
        if kind not in _VALID_KINDS:
            continue
        target = (entry.get("target_ref") or "").strip()
        if not target:
            continue
        rationale = str(entry.get("rationale") or "")[:200]
        key = (kind, target)
        if key in seen_refs:
            continue
        seen_refs.add(key)
        queries.append(VariantQuery(
            kind=kind,  # type: ignore[arg-type]
            target_ref=target,
            rationale=rationale,
            parent_signal_id=sig.signal_id,
            parent_cluster_id=str(cluster_id),
        ))
        if len(queries) >= max_n:
            break
    return queries

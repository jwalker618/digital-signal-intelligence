"""V7 Phase 11 — within-cycle variant amplification.

Pure-function gating + a lightweight orchestrator. The actual extraction
of a variant query is dispatched through a caller-supplied
`extract_for_variant(query) -> Optional[SignalResult]` callable; this
module knows nothing about the workflow's async DB / extractor registry.

Locked rules:
  - is_trigger(sig, verdict): True only when grade>=structured_attested
    AND validator advance=True AND a deterministic root-cause cluster
    exists AND sig.variant_of is None (single-hop).
  - Per-trigger cap defaults to 5 queries; per-cycle cap (across all
    triggers) defaults to 25 — sourced from VariantLoopPolicy.
  - Variants emitted carry variant_of=<parent signal_id> + cluster ref
    metadata; the loop refuses to spawn second hops because is_trigger
    returns False when variant_of is set.
"""
from __future__ import annotations

import logging
from typing import Callable, Optional, Sequence

from signal_architecture.signals.evidence import EvidenceGrade
from signal_architecture.signals.types import SignalResult

from .prompts import generate_variants_for
from .types import VariantQuery, VariantResult

logger = logging.getLogger("dsi.variant_loop")


# A "validator verdict" is anything with .advance: bool. Keeping the
# dependency loose so the loop can also accept a plain bool or a stub
# in tests.
class _HasAdvance:
    advance: bool


def is_trigger(
    sig: SignalResult,
    *,
    validator_advanced: Optional[bool],
) -> bool:
    """Locked Phase 11 trigger predicate.

    All five conditions must hold:
      1. sig.variant_of is None         (single-hop)
      2. evidence_grade in {structured_attested, behaviourally_validated}
      3. validator_advanced is True
      4. metadata['cluster_id'] is present
      5. metadata['deterministic'] is not False (None or True is fine —
         the deterministic-cluster pass produced this signal)
    """
    if sig.variant_of is not None:
        return False
    if sig.evidence_grade not in ("structured_attested", "behaviourally_validated"):
        return False
    if not validator_advanced:
        return False
    md = sig.metadata or {}
    if not md.get("cluster_id"):
        return False
    if md.get("deterministic") is False:
        return False
    return True


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------

# The extractor dispatch is caller-supplied. Each call returns either a
# SignalResult (the variant fired and yielded a finding) or None
# (variant ran but yielded nothing — a clean no_op).
ExtractForVariant = Callable[[VariantQuery], Optional[SignalResult]]

# The audit hook is also caller-supplied — keeps the loop DB-free.
# (event_type, signal_id, payload) -> None
AuditCallback = Callable[[str, Optional[str], dict], None]


def select_triggers(
    signals: Sequence[SignalResult],
    validator_verdicts: dict[str, "_HasAdvance | bool | None"],
) -> list[SignalResult]:
    """Filter the cycle's signals down to those that qualify as triggers.

    `validator_verdicts` is a mapping signal_id -> {bool | obj with .advance}.
    Missing entries treated as not-advanced.
    """
    out: list[SignalResult] = []
    for sig in signals:
        v = validator_verdicts.get(sig.signal_id)
        if v is None:
            advanced = False
        elif isinstance(v, bool):
            advanced = v
        else:
            advanced = bool(getattr(v, "advance", False))
        if is_trigger(sig, validator_advanced=advanced):
            out.append(sig)
    return out


def run_variant_loop(
    triggers: Sequence[SignalResult],
    *,
    llm_callable,
    extract_for_variant: ExtractForVariant,
    audit: Optional[AuditCallback] = None,
    max_per_trigger: int = 5,
    max_per_entity_per_cycle: int = 25,
) -> tuple[list[SignalResult], list[VariantResult]]:
    """Generate + execute variants for each trigger; honour per-cycle cap.

    Returns (new_signals, all_variant_results) — new_signals are the
    sub-set of variant_results that successfully yielded a SignalResult.
    Each new signal has variant_of populated and metadata flags set so
    the trigger predicate refuses to fan out from it on a future hop.

    The audit callback is invoked at the boundaries:
        ("variant_generated", parent_signal_id, {count, cluster_id})
        ("variant_extracted", child_signal_id,   {parent, kind})
        ("variant_no_op",     None,              {parent, kind, note})
    Caller writes these into compliance_audit_logs.
    """
    audit_fn = audit or (lambda _et, _sid, _p: None)

    # Build the full query list, capping per-trigger and per-cycle.
    queries: list[VariantQuery] = []
    for trigger in triggers:
        new_qs = generate_variants_for(llm_callable, trigger, max_n=max_per_trigger)
        audit_fn(
            "variant_generated",
            trigger.signal_id,
            {
                "parent_cluster_id": (trigger.metadata or {}).get("cluster_id"),
                "count": len(new_qs),
            },
        )
        queries.extend(new_qs)
        if len(queries) >= max_per_entity_per_cycle:
            queries = queries[:max_per_entity_per_cycle]
            break

    new_signals: list[SignalResult] = []
    results: list[VariantResult] = []

    for q in queries:
        try:
            produced = extract_for_variant(q)
        except Exception as e:  # noqa: BLE001
            logger.warning("variant extract failed for %s: %s", q.target_ref, e)
            audit_fn(
                "variant_no_op",
                None,
                {"parent": q.parent_signal_id, "kind": q.kind, "note": f"error:{e}"},
            )
            results.append(VariantResult(
                query=q, success=False, signal_id=None, grade=None,
                note=f"error:{e}",
            ))
            continue

        if produced is None:
            audit_fn(
                "variant_no_op",
                None,
                {"parent": q.parent_signal_id, "kind": q.kind, "note": "no_result"},
            )
            results.append(VariantResult(
                query=q, success=False, signal_id=None, grade=None, note="no_result",
            ))
            continue

        # Tag the child signal so single-hop is provable from the data.
        produced.variant_of = q.parent_signal_id
        produced.metadata = {
            **(produced.metadata or {}),
            "variant_kind": q.kind,
            "variant_target_ref": q.target_ref,
            "variant_parent_cluster_id": q.parent_cluster_id,
        }
        new_signals.append(produced)
        audit_fn(
            "variant_extracted",
            produced.signal_id,
            {"parent": q.parent_signal_id, "kind": q.kind},
        )
        results.append(VariantResult(
            query=q, success=True,
            signal_id=produced.signal_id,
            grade=produced.evidence_grade,
        ))

    return new_signals, results

"""V7 — sync helpers that bridge ``WorkflowResult`` / ``SignalOutput``
into the kwargs the existing repositories accept.

The route layer (``infrastructure/api/routes/*``) is async; the workflow
output is sync. These helpers stay pure and sync so the route layer can
do tiny wrappers like:

    kwargs = mv_create_kwargs_from_result(workflow_result)
    mv = await mv_repo.create(submission_id=sub.id, **kwargs)
    signals_payload = signal_records_from_outputs(workflow_result.signal_outputs)
    await mvs_repo.bulk_record(model_version_id=mv.id, signals=signals_payload)

Keeping the bridge here means future writer call sites don't need to
re-derive the same conversions — and the V7 fields can't be silently
dropped on a path because the helper enumerates them in one place.
"""
from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional

from .types import SignalOutput, WorkflowResult


def mv_create_kwargs_from_result(
    result: WorkflowResult,
    *,
    version_type: str = "initial",
) -> Dict[str, Any]:
    """Build the kwargs ``ModelVersionRepository.create(**kwargs)`` accepts.

    Excludes ``submission_id`` — caller passes it explicitly. Includes V7
    composite-grade fields so they land on the ORM row.
    """
    return {
        "version_type": version_type,
        "coverage": result.coverage,
        "pure_composite_score": result.composite_score,
        "final_composite_score": result.composite_score,
        "confidence": result.confidence,
        "signal_coverage": getattr(result, "signal_completeness", 1.0),
        "final_tier": result.tier,
        "tier_label": result.tier_label,
        # V7 composite grade rollup.
        "composite_min_grade": result.composite_min_grade,
        "composite_weighted_mean_grade": result.composite_weighted_mean_grade,
        "composite_grade_distribution": dict(result.composite_grade_distribution or {}),
    }


def signal_records_from_outputs(
    signal_outputs: Iterable[SignalOutput],
    *,
    entity_code: str,
) -> List[Dict[str, Any]]:
    """Build the payload list ``ModelVersionSignalRepository.bulk_record`` accepts.

    The repository resolves ``signal_code`` -> integer ID itself, so we
    pass the signal_id string. evidence_sources is included verbatim
    (each entry is already a JSON-able dict because Phase 5's
    ``EvidenceSource.to_dict`` produces dicts before they reach here).
    """
    records: List[Dict[str, Any]] = []
    for so in signal_outputs:
        records.append({
            "signal_code": so.signal_id,
            "signal_cache_id": None,  # caller fills in if applicable
            "entity_code": entity_code,
            "score": so.raw_score,
            "weight": so.weight,
            "contribution": so.weighted_score,
            "group_code": so.group_id,
            "proxy_tier": None,
            "expectation_level": None,
            "was_absent": bool(so.error),
            # V7 evidence-grade fields.
            "evidence_grade": so.evidence_grade,
            "evidence_basis": so.evidence_basis,
            "evidence_sources": [],  # populated when route layer has the source dicts
            "evidence_pro": so.evidence_pro,
            "evidence_counter": so.evidence_counter,
            "evidence_tie_breaker": so.evidence_tie_breaker,
            "absence_sub_type": so.absence_sub_type,
            "primitive_type": so.primitive_type,
        })
    return records


def quote_dict_evidence_fields(result: WorkflowResult) -> Dict[str, Any]:
    """V7 composite-grade fields formatted for inclusion in a quote payload.

    The route-layer ``workflow_result_to_quote`` helper merges this into
    the quote dict so the frontend has access without an extra GET.
    """
    return {
        "composite_min_grade": result.composite_min_grade,
        "composite_weighted_mean_grade": result.composite_weighted_mean_grade,
        "composite_grade_distribution": dict(result.composite_grade_distribution or {}),
        "group_grade_rollups": dict(result.group_grade_rollups or {}),
        "primitive_grade_rollups": dict(result.primitive_grade_rollups or {}),
    }


def disclosure_packet_payload_from_result(
    result: WorkflowResult,
    *,
    model_version_id: Any,
) -> Optional[Dict[str, Any]]:
    """Return a cached-packet payload (Markdown + canonical JSON) if the
    workflow result has any grade-driven referral reasons.

    Caller assigns the returned dict to ``Referral.disclosure_packet``.
    Returns ``None`` when no grade referral fired (no packet needed yet
    — the disclosure endpoint generates on demand).
    """
    grade_reasons = [
        r for r in (result.referral_reasons or [])
        if r.startswith("[evidence_grade]")
    ]
    if not grade_reasons:
        return None
    # Lazy import to avoid jinja2 dependency in code paths that don't need it.
    from signal_architecture.disclosure import PacketSection, build_packet

    sections: List[PacketSection] = []
    for so in (result.model_version.signal_outputs if result.model_version else []):
        if not getattr(so, "evidence_grade", None):
            continue
        sections.append(PacketSection(
            title=so.signal_id.replace("_", " ").title(),
            signal_id=so.signal_id,
            grade=so.evidence_grade,
            pro=so.evidence_pro or "",
            counter=so.evidence_counter or "",
            tie_breaker=so.evidence_tie_breaker or "",
            reproducibility=so.reproducibility,
        ))

    md, payload = build_packet(
        model_version_id=model_version_id,
        composite_min_grade=result.composite_min_grade,
        composite_distribution=dict(result.composite_grade_distribution or {}),
        referral_reasons=grade_reasons,
        sections=sections,
    )
    return {"markdown": md, "payload": payload}

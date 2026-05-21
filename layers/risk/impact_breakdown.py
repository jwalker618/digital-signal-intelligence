"""v8 Phase 3: signal impact breakdown.

Reshapes the persisted `modifiers_applied` audit trail (Phase A
modifier-before/after tracking, v0.4.0) into a per-signal premium-delta
view suitable for the client portal. Classifies each signal-equivalent
as a strength (modifier reduced premium), drag (modifier increased
premium), or neutral (within +-2% deadband).

This module is a pure function over the modifier audit trail. It does
not touch the DB and does not modify the workflow. The portal API
(v8 Phase 6) calls `compute_impact_breakdown` on demand when serving
/portal/entities/{id}/score, taking the persisted `modifiers_applied`
JSONB directly from a ModelVersionRecord.

Why no tier_transition: tier in this codebase is score-based
(model_versions.score_based_tier / final_tier are derived from
composite score, not premium). Neutralising a premium-side modifier
moves premium within a tier; it does not move tier. The
"tier improved by N points" narrative belongs in Phase 5's
re-assessment loop (full workflow re-run with signal value override),
not Phase 3's modifier reshaping.
"""
from __future__ import annotations

from enum import Enum
from typing import Any, Iterable, Optional

from pydantic import BaseModel, Field


# Symmetric deadband around 1.0. A modifier whose factor falls within
# +-2% of neutral is treated as NEUTRAL -- prevents rounding noise from
# being classified as a meaningful driver.
DEADBAND_LOWER: float = 0.98
DEADBAND_UPPER: float = 1.02

# Cap on how many neutral signals appear in the API response. Strengths
# and drags are unbounded; neutral is truncated by |dollar impact| desc
# because the long tail of negligible-impact signals is uninteresting.
NEUTRAL_MAX_ENTRIES: int = 20


class ImpactClass(str, Enum):
    STRENGTH = "strength"   # combined modifier < deadband lower -> reduces premium
    DRAG = "drag"           # combined modifier > deadband upper -> increases premium
    NEUTRAL = "neutral"     # within +-2% of 1.0


class SignalImpact(BaseModel):
    """One signal-equivalent's contribution to the final premium.

    `signal_key` is the canonical identifier formed from (source, source_id)
    on the underlying AppliedModifier records. Multiple modifier rows that
    share the same (source, source_id) collapse into a single SignalImpact
    -- their effects are multiplied for `combined_modifier` and summed for
    `premium_delta_usd`.
    """
    signal_key: str
    signal_source: str           # "categorical" | "direct_query" | "experience" | ...
    signal_source_id: str
    signal_label: str            # human-readable name from the underlying modifier(s)
    classification: ImpactClass
    combined_modifier: float
    premium_delta_usd: float     # positive = drag (increased premium); negative = strength
    premium_delta_pct: float     # combined_modifier - 1.0
    contributing_modifier_count: int


class ImpactBreakdown(BaseModel):
    """Per-quote summary of how each signal moved the premium.

    Returned by `compute_impact_breakdown` for any persisted set of
    AppliedModifier records (e.g. from model_versions.modifiers_applied
    JSONB). Strengths and drags are sorted by absolute dollar impact
    desc; neutral is truncated to NEUTRAL_MAX_ENTRIES.
    """
    base_premium: float
    final_premium: float
    total_modifier: float        # final / base, approximately the product of all signal factors
    strengths: list[SignalImpact] = Field(default_factory=list)
    drags: list[SignalImpact] = Field(default_factory=list)
    neutral: list[SignalImpact] = Field(default_factory=list)


def _classify(combined_modifier: float) -> ImpactClass:
    if combined_modifier < DEADBAND_LOWER:
        return ImpactClass.STRENGTH
    if combined_modifier > DEADBAND_UPPER:
        return ImpactClass.DRAG
    return ImpactClass.NEUTRAL


def _signal_key(source: str, source_id: str) -> str:
    return f"{source}:{source_id}"


def _coerce_modifier_dict(m: Any) -> Optional[dict]:
    """Normalise an AppliedModifier or its JSONB-serialised form to a dict.

    Accepts both the dataclass (with attribute access) and JSONB shapes
    (dicts) so the same function works against either ModelVersion in
    memory or ModelVersionRecord rows from the DB.
    """
    if isinstance(m, dict):
        d = m
    else:
        # AppliedModifier dataclass or any object with the expected attrs
        try:
            d = {
                "source": getattr(m, "source"),
                "source_id": getattr(m, "source_id"),
                "name": getattr(m, "name", ""),
                "factor": float(getattr(m, "factor")),
                "premium_before": float(getattr(m, "premium_before")),
                "premium_after": float(getattr(m, "premium_after")),
            }
        except AttributeError:
            return None

    if not d.get("source") or d.get("source_id") in (None, ""):
        # Modifier lacks provenance -- cannot be grouped by signal
        return None
    try:
        return {
            "source": str(d["source"]),
            "source_id": str(d["source_id"]),
            "name": str(d.get("name", "")) or str(d["source_id"]),
            "factor": float(d.get("factor", 1.0)),
            "premium_before": float(d.get("premium_before", 0.0)),
            "premium_after": float(d.get("premium_after", 0.0)),
        }
    except (TypeError, ValueError):
        return None


def compute_impact_breakdown(
    modifiers_applied: Iterable[Any],
    *,
    base_premium: float,
    final_premium: float,
) -> ImpactBreakdown:
    """Group modifiers by (source, source_id) and classify each group.

    Inputs:
      modifiers_applied -- iterable of AppliedModifier dataclasses or
        their JSONB-serialised dict equivalents.
      base_premium -- pricing's pre-modifier base (model_versions.base_premium)
      final_premium -- pricing's post-modifier final
        (model_versions.final_premium or premium_after_modifiers)

    Pure function. No DB. Safe to call repeatedly.
    """
    # Group modifiers by (source, source_id)
    groups: dict[str, dict[str, Any]] = {}
    for raw in modifiers_applied:
        m = _coerce_modifier_dict(raw)
        if m is None:
            continue
        key = _signal_key(m["source"], m["source_id"])
        g = groups.setdefault(key, {
            "source": m["source"],
            "source_id": m["source_id"],
            "label_candidates": [],
            "combined_modifier": 1.0,
            "premium_delta_usd": 0.0,
            "count": 0,
        })
        g["label_candidates"].append(m["name"])
        g["combined_modifier"] *= m["factor"]
        # premium_delta is signed: positive when after > before (drag), negative for strength
        g["premium_delta_usd"] += m["premium_after"] - m["premium_before"]
        g["count"] += 1

    strengths: list[SignalImpact] = []
    drags: list[SignalImpact] = []
    neutral: list[SignalImpact] = []

    for key, g in groups.items():
        cls = _classify(g["combined_modifier"])
        label = g["label_candidates"][0] if g["label_candidates"] else g["source_id"]
        impact = SignalImpact(
            signal_key=key,
            signal_source=g["source"],
            signal_source_id=g["source_id"],
            signal_label=label,
            classification=cls,
            combined_modifier=round(g["combined_modifier"], 4),
            premium_delta_usd=round(g["premium_delta_usd"], 2),
            premium_delta_pct=round(g["combined_modifier"] - 1.0, 4),
            contributing_modifier_count=g["count"],
        )
        if cls is ImpactClass.STRENGTH:
            strengths.append(impact)
        elif cls is ImpactClass.DRAG:
            drags.append(impact)
        else:
            neutral.append(impact)

    # Sort by absolute dollar impact desc within each bucket
    strengths.sort(key=lambda s: abs(s.premium_delta_usd), reverse=True)
    drags.sort(key=lambda s: abs(s.premium_delta_usd), reverse=True)
    neutral.sort(key=lambda s: abs(s.premium_delta_usd), reverse=True)

    return ImpactBreakdown(
        base_premium=round(float(base_premium), 2),
        final_premium=round(float(final_premium), 2),
        total_modifier=(
            round(final_premium / base_premium, 4)
            if base_premium and base_premium > 0
            else 1.0
        ),
        strengths=strengths,
        drags=drags,
        neutral=neutral[:NEUTRAL_MAX_ENTRIES],
    )


def compute_from_model_version(model_version: Any) -> ImpactBreakdown:
    """Convenience wrapper that pulls the inputs from a ModelVersion / record.

    Works against either:
      - layers.risk.types.ModelVersion (in-memory dataclass)
      - infrastructure.db.models.ModelVersionRecord (DB row)
    """
    mods = getattr(model_version, "modifiers_applied", None) or []
    base = float(getattr(model_version, "base_premium", 0.0) or 0.0)
    # Prefer premium_after_modifiers when present (pre-guardrail final);
    # fall back to final_premium otherwise.
    final = float(
        getattr(model_version, "premium_after_modifiers", None)
        or getattr(model_version, "final_premium", 0.0)
        or 0.0
    )
    return compute_impact_breakdown(mods, base_premium=base, final_premium=final)

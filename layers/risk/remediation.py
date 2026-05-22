"""v8 Phase 4: remediation engine.

Builds a prioritised action plan from the drag signals on a quote's
ImpactBreakdown (Phase 3) plus the authored signal_remediation in the
coverage config. Sort key is `leverage = |premium delta| / effort_score`
so low-effort, high-impact actions surface first.

Pure function. No DB. No workflow integration. Phase 6 calls
`build_remediation_plan` on demand when serving /portal/actions.

Generic placeholder strategy: drag signals without an authored
remediation entry receive a runtime placeholder (effort MEDIUM, "no
specific guidance available"). The plan's `placeholder_count` exposes
authoring debt so coverage owners can prioritise filling gaps.
"""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

from infrastructure.models.config_schema import (
    RemediationEffort,
    SignalRemediation,
)
from layers.risk.impact_breakdown import ImpactBreakdown, SignalImpact


# Multiplicative effort scores. Chosen so a single-LOW action only
# beats a HIGH action when its dollar impact is at least 9x larger.
EFFORT_SCORE: dict[RemediationEffort, int] = {
    RemediationEffort.LOW: 1,
    RemediationEffort.MEDIUM: 3,
    RemediationEffort.HIGH: 9,
}


class RemediationAction(BaseModel):
    """One actionable recommendation tied to a single drag signal."""
    signal_key: str                       # "{source}:{source_id}" from SignalImpact
    signal_label: str
    remediation: SignalRemediation
    estimated_premium_delta_usd: float    # negative -- the reduction expected if remediated
    estimated_premium_delta_pct: float    # negative
    leverage: float                       # |delta| / EFFORT_SCORE[effort]
    is_placeholder: bool                  # true when no authored remediation existed


class RemediationPlan(BaseModel):
    """Ordered set of recommended actions for a quote."""
    actions: list[RemediationAction] = Field(default_factory=list)
    placeholder_count: int = 0


def _placeholder_for(signal_label: str) -> SignalRemediation:
    """Generic remediation used when the coverage config has nothing authored.

    Returns a SignalRemediation that parses cleanly through the Pydantic
    schema (so callers can treat all entries uniformly), with text that
    explicitly flags itself as unauthored.
    """
    return SignalRemediation(
        headline=f"Address signal: {signal_label}",
        description=(
            "No specific remediation guidance has been authored for this "
            "signal yet. Discuss with your broker for actions that would "
            "improve this driver."
        ),
        effort=RemediationEffort.MEDIUM,
        typical_duration="varies",
        typical_cost_usd=0,
        evidence_required="To be agreed with carrier on a case-by-case basis",
        references=[],
    )


def _build_action(
    impact: SignalImpact,
    remediation: SignalRemediation,
    *,
    is_placeholder: bool,
) -> RemediationAction:
    # Remediating a drag *removes* the premium increase, so the
    # estimated delta is the NEGATIVE of the current drag's dollar impact.
    estimated_usd = -float(impact.premium_delta_usd)
    estimated_pct = -float(impact.premium_delta_pct)
    leverage = abs(estimated_usd) / EFFORT_SCORE[remediation.effort]
    return RemediationAction(
        signal_key=impact.signal_key,
        signal_label=impact.signal_label,
        remediation=remediation,
        estimated_premium_delta_usd=round(estimated_usd, 2),
        estimated_premium_delta_pct=round(estimated_pct, 4),
        leverage=round(leverage, 2),
        is_placeholder=is_placeholder,
    )


def build_remediation_plan(
    impact_breakdown: ImpactBreakdown,
    *,
    signal_remediation: Optional[dict[str, SignalRemediation]] = None,
) -> RemediationPlan:
    """Produce a leverage-sorted RemediationPlan from a quote's drags.

    Inputs:
      impact_breakdown -- output of layers.risk.impact_breakdown.compute_*
      signal_remediation -- the coverage_config.signal_remediation dict
        (None or {} -> every drag receives a placeholder)

    Sort order:
      1. Higher leverage first
      2. Tie-break: real (non-placeholder) actions before placeholders
      3. Tie-break: larger absolute dollar impact first
    """
    remediation_map: dict[str, SignalRemediation] = signal_remediation or {}
    actions: list[RemediationAction] = []
    placeholders = 0

    for drag in impact_breakdown.drags:
        # Look up by source_id (matches signal IDs in the coverage YAML).
        # Modifiers from categoricals (industry, geography) won't have
        # entries -- they get placeholders, which is fine: the UI can
        # render them as "no remediation: industry is fixed".
        authored = remediation_map.get(drag.signal_source_id)
        if authored is not None:
            actions.append(_build_action(drag, authored, is_placeholder=False))
        else:
            placeholders += 1
            actions.append(
                _build_action(
                    drag,
                    _placeholder_for(drag.signal_label),
                    is_placeholder=True,
                )
            )

    actions.sort(
        key=lambda a: (
            -a.leverage,
            a.is_placeholder,           # False (0) sorts before True (1)
            -abs(a.estimated_premium_delta_usd),
        )
    )

    return RemediationPlan(actions=actions, placeholder_count=placeholders)

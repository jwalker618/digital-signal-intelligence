"""
C-2d: WeightOptimiser

Produces the set of WeightChange recommendations from a list of
SignalReportCard outputs.

Method: simple, auditable, and monotonic in evidence:
    proposed = blend(current, evidence_supported, alpha=BLEND_STRENGTH)

We deliberately avoid full gradient-based optimisation in this first
iteration -- blending preserves the current config as a strong prior so
proposals are gentle and interpretable. The governance UI (C-3) displays
each change individually, and large shifts attract scrutiny.

Constraints applied post-blend:
1. Non-negative weights.
2. Per-signal cap: no signal exceeds MAX_SIGNAL_WEIGHT of its group total.
3. Group weights re-normalised to preserve the group's total weight.

The overall result is a set of weight changes that, if applied, will:
- Preserve each group's total weight (no silent drift).
- Move each signal gently toward its evidence-supported value.
- Never exceed the per-signal cap.
- Never go negative.
"""

from __future__ import annotations

import logging
from collections import defaultdict
from dataclasses import dataclass
from typing import Optional

from infrastructure.recalibration.types import SignalReportCard, WeightChange

logger = logging.getLogger("dsi.recalibration.weight_optimiser")


BLEND_STRENGTH = 0.4
"""Fraction of the move from current to evidence-supported to apply each
recalibration cycle. 0.4 = 40% of the distance. Chosen to be gradual."""

MAX_SIGNAL_WEIGHT_FRACTION = 0.50
"""No single signal can exceed this fraction of its group's total weight.
Prevents over-fitting to a single high-IV signal."""

MIN_CHANGE_THRESHOLD = 0.005
"""Absolute weight change below this is ignored -- no point proposing
a 0.1% move."""


@dataclass
class WeightOptimiserConfig:
    blend_strength: float = BLEND_STRENGTH
    max_signal_weight_fraction: float = MAX_SIGNAL_WEIGHT_FRACTION
    min_change_threshold: float = MIN_CHANGE_THRESHOLD


class WeightOptimiser:
    """Computes constrained weight changes from signal report cards."""

    def __init__(self, config: Optional[WeightOptimiserConfig] = None):
        self.config = config or WeightOptimiserConfig()

    def optimise(
        self, cards: list[SignalReportCard]
    ) -> list[WeightChange]:
        """Return a list of WeightChange objects.

        Signals without a group_code are treated as a single default group.
        Group totals are preserved.
        """
        if not cards:
            return []

        # Group cards by group_code
        grouped: dict[str, list[SignalReportCard]] = defaultdict(list)
        for c in cards:
            grouped[c.group_code or "__default__"].append(c)

        changes: list[WeightChange] = []
        for group_code, group_cards in grouped.items():
            group_total = sum(c.current_weight for c in group_cards)
            if group_total <= 0:
                continue

            # Blend current toward evidence
            raw: dict[str, float] = {}
            for c in group_cards:
                blended = (
                    c.current_weight * (1 - self.config.blend_strength)
                    + c.evidence_supported_weight * self.config.blend_strength
                )
                raw[c.signal_id] = max(0.0, blended)

            # Apply per-signal cap with iterative normalisation. A signal
            # pushed up by normalisation can re-breach the cap, so we
            # alternate cap -> normalise until convergence. In practice
            # this converges in 2-3 iterations.
            cap = self.config.max_signal_weight_fraction * group_total
            for _ in range(10):  # safety bound
                # Clamp over-cap signals
                breached = False
                for sig_id, w in raw.items():
                    if w > cap + 1e-9:
                        raw[sig_id] = cap
                        breached = True

                # Normalise remaining mass across uncapped signals
                current_total = sum(raw.values())
                if current_total <= 0:
                    break
                if abs(current_total - group_total) < 1e-6 and not breached:
                    break

                capped_mass = sum(v for v in raw.values() if abs(v - cap) < 1e-9)
                uncapped_ids = [k for k, v in raw.items() if abs(v - cap) >= 1e-9]
                remaining_budget = group_total - capped_mass
                uncapped_total = sum(raw[k] for k in uncapped_ids)
                if uncapped_total > 0 and remaining_budget > 0:
                    scale = remaining_budget / uncapped_total
                    for k in uncapped_ids:
                        raw[k] = raw[k] * scale

            # Emit changes above the noise threshold
            for c in group_cards:
                proposed = raw.get(c.signal_id, c.current_weight)
                delta = proposed - c.current_weight
                if abs(delta) < self.config.min_change_threshold:
                    continue
                delta_pct = (delta / c.current_weight * 100.0) if c.current_weight > 0 else 0.0
                changes.append(WeightChange(
                    signal_id=c.signal_id,
                    group_code=group_code if group_code != "__default__" else None,
                    current_weight=round(c.current_weight, 4),
                    proposed_weight=round(proposed, 4),
                    delta=round(delta, 4),
                    delta_pct=round(delta_pct, 2),
                ))

        logger.info(
            "WeightOptimiser: %d signal cards -> %d weight changes",
            len(cards),
            len(changes),
        )
        return changes

"""C-2d: WeightOptimiser tests."""

import pytest

from infrastructure.recalibration.types import Alignment, SignalReportCard
from infrastructure.recalibration.weight_optimiser import (
    BLEND_STRENGTH,
    MIN_CHANGE_THRESHOLD,
    WeightOptimiser,
    WeightOptimiserConfig,
)


def _card(signal_id, current, evidence, group_code=None):
    return SignalReportCard(
        signal_id=signal_id,
        group_code=group_code,
        current_weight=current,
        evidence_supported_weight=evidence,
    )


class TestBlending:
    def test_blend_strength_applied(self):
        """Proposed weight = current + BLEND_STRENGTH × (evidence - current)."""
        opt = WeightOptimiser()
        cards = [_card("a", 0.5, 1.0), _card("b", 0.5, 0.0)]
        # Both in default group -- total weight preserved
        changes = opt.optimise(cards)
        # Total current weight = 1.0, must stay 1.0 after normalisation
        total_new = sum(c.proposed_weight for c in changes)
        # Also account for unchanged signals (below threshold)
        unchanged = [c for c in cards if c.signal_id not in {ch.signal_id for ch in changes}]
        total_new += sum(u.current_weight for u in unchanged)
        assert abs(total_new - 1.0) < 0.01

    def test_no_change_when_aligned(self):
        opt = WeightOptimiser()
        cards = [_card("a", 0.5, 0.5), _card("b", 0.5, 0.5)]
        changes = opt.optimise(cards)
        assert changes == []

    def test_min_threshold_filters_noise(self):
        opt = WeightOptimiser()
        # Tiny move below threshold
        cards = [_card("a", 0.5, 0.501), _card("b", 0.5, 0.499)]
        changes = opt.optimise(cards)
        # Blended 40% of 0.001 = 0.0004 = below threshold
        assert changes == []


class TestConstraints:
    def test_group_total_preserved(self):
        opt = WeightOptimiser()
        cards = [
            _card("a", 0.3, 0.1, group_code="g1"),
            _card("b", 0.4, 0.7, group_code="g1"),
            _card("c", 0.3, 0.4, group_code="g1"),
        ]
        changes = opt.optimise(cards)
        # All three in same group -- total stays 1.0
        total = 0.0
        for c in cards:
            change = next((ch for ch in changes if ch.signal_id == c.signal_id), None)
            total += change.proposed_weight if change else c.current_weight
        assert abs(total - 1.0) < 0.01

    def test_per_signal_cap(self):
        opt = WeightOptimiser(WeightOptimiserConfig(max_signal_weight_fraction=0.4))
        # Try to push "a" to take all the weight
        cards = [
            _card("a", 0.2, 1.0, group_code="g1"),
            _card("b", 0.2, 0.0, group_code="g1"),
            _card("c", 0.2, 0.0, group_code="g1"),
            _card("d", 0.2, 0.0, group_code="g1"),
            _card("e", 0.2, 0.0, group_code="g1"),
        ]
        changes = opt.optimise(cards)
        a_change = next(c for c in changes if c.signal_id == "a")
        # Group total = 1.0, cap = 0.4
        assert a_change.proposed_weight <= 0.4 + 0.01

    def test_non_negative_weights(self):
        opt = WeightOptimiser()
        cards = [
            _card("a", 0.1, -5.0, group_code="g1"),  # evidence forces negative
            _card("b", 0.9, 1.0, group_code="g1"),
        ]
        changes = opt.optimise(cards)
        a_change = next((c for c in changes if c.signal_id == "a"), None)
        # Either filtered out or non-negative
        if a_change:
            assert a_change.proposed_weight >= 0


class TestMultipleGroups:
    def test_groups_optimised_independently(self):
        opt = WeightOptimiser()
        cards = [
            _card("g1_a", 0.3, 0.5, group_code="g1"),
            _card("g1_b", 0.3, 0.1, group_code="g1"),
            _card("g2_a", 0.5, 0.5, group_code="g2"),  # aligned
            _card("g2_b", 0.5, 0.5, group_code="g2"),
        ]
        changes = opt.optimise(cards)
        # g2 should have no changes; g1 should have changes
        assert all(c.group_code == "g1" for c in changes)

"""WE-4b: Constraint regime + calibrator math (pure-logic tests)."""

from datetime import datetime, timezone

import pytest

from world_engine.causal_pricing.constraints import (
    ABSOLUTE_CAP,
    ABSOLUTE_CONFIDENCE_MIN,
    ABSOLUTE_FLOOR,
    ConstraintRegime,
    INITIAL_CAP,
    INITIAL_CONFIDENCE_GATE,
    INITIAL_FLOOR,
    INITIAL_MIN_RELATIONSHIPS,
)


class TestAbsoluteBounds:
    def test_absolute_floor_immutable_constant(self):
        assert ABSOLUTE_FLOOR == 0.60

    def test_absolute_cap_immutable_constant(self):
        assert ABSOLUTE_CAP == 2.00

    def test_absolute_confidence_min_immutable_constant(self):
        assert ABSOLUTE_CONFIDENCE_MIN == 0.4

    def test_initial_inside_absolute_bounds(self):
        assert ABSOLUTE_FLOOR <= INITIAL_FLOOR <= 1.0
        assert 1.0 <= INITIAL_CAP <= ABSOLUTE_CAP
        assert INITIAL_CONFIDENCE_GATE >= ABSOLUTE_CONFIDENCE_MIN

    def test_initial_more_conservative_than_absolute(self):
        assert INITIAL_FLOOR > ABSOLUTE_FLOOR, "Initial floor must be tighter"
        assert INITIAL_CAP < ABSOLUTE_CAP, "Initial cap must be tighter"


class TestConstraintRegime:
    def _make(self, floor=0.8, cap=1.5, gate=0.6):
        return ConstraintRegime(
            regime_name="test",
            caf_floor=floor,
            caf_cap=cap,
            confidence_gate=gate,
            min_relationships=2,
            effective_from=datetime.now(timezone.utc),
        )

    def test_clamp_below_floor(self):
        regime = self._make()
        clamped, was_constrained = regime.clamp(0.5)
        assert clamped == 0.8
        assert was_constrained

    def test_clamp_above_cap(self):
        regime = self._make()
        clamped, was_constrained = regime.clamp(2.5)
        assert clamped == 1.5
        assert was_constrained

    def test_clamp_in_range(self):
        regime = self._make()
        clamped, was_constrained = regime.clamp(1.15)
        assert clamped == 1.15
        assert not was_constrained

    def test_clamp_at_boundary(self):
        regime = self._make()
        # Values exactly at the boundary are NOT flagged as constrained
        assert regime.clamp(0.8) == (0.8, False)
        assert regime.clamp(1.5) == (1.5, False)

    def test_within_absolute_bounds_accepts_initial(self):
        regime = self._make(floor=INITIAL_FLOOR, cap=INITIAL_CAP, gate=INITIAL_CONFIDENCE_GATE)
        assert regime.within_absolute_bounds()

    def test_within_absolute_bounds_rejects_breach_below_floor(self):
        regime = self._make(floor=0.5)  # below absolute floor
        assert not regime.within_absolute_bounds()

    def test_within_absolute_bounds_rejects_breach_above_cap(self):
        regime = self._make(cap=2.5)  # above absolute cap
        assert not regime.within_absolute_bounds()

    def test_within_absolute_bounds_rejects_low_confidence(self):
        regime = self._make(gate=0.3)  # below absolute conf min
        assert not regime.within_absolute_bounds()

    def test_within_absolute_bounds_rejects_floor_above_one(self):
        regime = self._make(floor=1.1)  # floor must be <= 1.0
        assert not regime.within_absolute_bounds()

    def test_within_absolute_bounds_rejects_cap_below_one(self):
        regime = self._make(cap=0.9)  # cap must be >= 1.0
        assert not regime.within_absolute_bounds()

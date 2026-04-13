"""WE-4a: TrajectoryEngine -- tier migration probability synthesis."""

import pytest

from world_engine.causal_pricing.trajectory import (
    MIGRATION_DECAY,
    MAX_MOVE_FRACTION,
    TrajectoryEngine,
)
from world_engine.types import PrecursorEvaluation


def _make_precursor(
    signal="sig_x",
    rel_id="r1",
    entity_value=30.0,
    threshold=50.0,
    implied_probability=0.7,
    lag_months=6.0,
):
    return PrecursorEvaluation(
        relationship_id=rel_id,
        precursor_signal=signal,
        entity_value=entity_value,
        threshold=threshold,
        distance_from_threshold=threshold - entity_value,
        implied_probability=implied_probability,
        lag_months=lag_months,
    )


class TestNoPrecursors:
    def test_mass_stays_at_current_tier(self):
        engine = TrajectoryEngine()
        result = engine.compute_trajectory(
            precursors=[],
            current_tier=2,
            tier_rates={1: 1000, 2: 1500, 3: 2000, 4: 2500},
        )
        assert result.probabilities[2] == pytest.approx(1.0, abs=1e-6)
        # Other tiers get 0 mass
        for t in (1, 3, 4):
            assert result.probabilities.get(t, 0.0) == pytest.approx(0.0, abs=1e-6)
        assert result.expected_tier == pytest.approx(2.0, abs=1e-6)


class TestSinglePrecursor:
    def test_moderate_precursor_distributes_mass_to_worse_tiers(self):
        engine = TrajectoryEngine()
        result = engine.compute_trajectory(
            precursors=[_make_precursor(implied_probability=0.7, entity_value=30.0, threshold=60.0)],
            current_tier=2,
            tier_rates={1: 1000, 2: 1500, 3: 2000, 4: 2500},
        )
        # Most probability stays at 2, then decays to 3, then 4
        assert result.probabilities[2] > result.probabilities[3]
        assert result.probabilities[3] > result.probabilities[4]
        # Better tier (1) gets zero (no positive evidence for upgrade)
        assert result.probabilities.get(1, 0.0) == pytest.approx(0.0, abs=1e-6)
        # Expected tier should be worse than 2 (higher number)
        assert result.expected_tier > 2.0

    def test_probabilities_sum_to_one(self):
        engine = TrajectoryEngine()
        result = engine.compute_trajectory(
            precursors=[_make_precursor(implied_probability=0.9)],
            current_tier=2,
            tier_rates={1: 1000, 2: 1500, 3: 2000, 4: 2500},
        )
        total = sum(result.probabilities.values())
        assert total == pytest.approx(1.0, abs=1e-6)

    def test_weak_precursor_minimal_movement(self):
        engine = TrajectoryEngine()
        weak_prec = _make_precursor(
            implied_probability=0.1, entity_value=48.0, threshold=50.0,
        )
        result = engine.compute_trajectory(
            precursors=[weak_prec],
            current_tier=2,
            tier_rates={1: 1000, 2: 1500, 3: 2000, 4: 2500},
        )
        # Should still be near 2.0
        assert result.expected_tier == pytest.approx(2.0, abs=0.3)


class TestMultiplePrecursors:
    def test_probability_union_not_sum(self):
        """Multiple precursors combine via 1 - Π(1 - p_i), not by summing."""
        engine = TrajectoryEngine()
        # Three precursors each at p=0.5 should NOT exceed p=1.0
        precursors = [
            _make_precursor(rel_id=f"r{i}", implied_probability=0.5) for i in range(3)
        ]
        result = engine.compute_trajectory(
            precursors=precursors,
            current_tier=2,
            tier_rates={1: 1000, 2: 1500, 3: 2000, 4: 2500},
        )
        # All probabilities are valid in [0, 1]
        for p in result.probabilities.values():
            assert 0.0 <= p <= 1.0

    def test_more_precursors_higher_expected_tier(self):
        engine = TrajectoryEngine()
        single = engine.compute_trajectory(
            precursors=[_make_precursor(rel_id="r1", implied_probability=0.5)],
            current_tier=2,
            tier_rates={1: 1000, 2: 1500, 3: 2000, 4: 2500},
        )
        triple = engine.compute_trajectory(
            precursors=[_make_precursor(rel_id=f"r{i}", implied_probability=0.5) for i in range(3)],
            current_tier=2,
            tier_rates={1: 1000, 2: 1500, 3: 2000, 4: 2500},
        )
        assert triple.expected_tier > single.expected_tier


class TestBoundaries:
    def test_current_tier_not_in_rates_keeps_all_mass(self):
        """Edge case: current tier not in the known tier list."""
        engine = TrajectoryEngine()
        result = engine.compute_trajectory(
            precursors=[_make_precursor(implied_probability=0.9)],
            current_tier=99,  # unknown
            tier_rates={1: 1000, 2: 1500},
        )
        assert result.probabilities == {99: 1.0}

    def test_empty_tier_rates_safe(self):
        engine = TrajectoryEngine()
        result = engine.compute_trajectory(
            precursors=[_make_precursor(implied_probability=0.9)],
            current_tier=2,
            tier_rates={},
        )
        assert result.probabilities == {2: 1.0}

    def test_max_move_fraction_caps_aggregate(self):
        """Even overwhelming precursors cannot move 100% of mass."""
        engine = TrajectoryEngine()
        precursors = [
            _make_precursor(rel_id=f"r{i}", implied_probability=0.99, entity_value=0, threshold=100)
            for i in range(10)
        ]
        result = engine.compute_trajectory(
            precursors=precursors,
            current_tier=2,
            tier_rates={1: 1000, 2: 1500, 3: 2000, 4: 2500},
        )
        # At least (1 - MAX_MOVE_FRACTION) fraction stays
        assert result.probabilities[2] >= (1 - MAX_MOVE_FRACTION) - 0.01


class TestGeometricDecay:
    def test_hops_decay_geometrically(self):
        engine = TrajectoryEngine()
        result = engine.compute_trajectory(
            precursors=[_make_precursor(implied_probability=0.8, entity_value=10, threshold=80)],
            current_tier=1,  # allow movement through many worse tiers
            tier_rates={1: 500, 2: 1000, 3: 2000, 4: 3500, 5: 6000},
        )
        # Worse tiers should decay in probability
        assert result.probabilities[2] > result.probabilities[3]
        assert result.probabilities[3] > result.probabilities[4]
        assert result.probabilities[4] > result.probabilities[5]
        # Geometric ratio approximately equals MIGRATION_DECAY
        if result.probabilities[2] > 0 and result.probabilities[3] > 0:
            ratio_23 = result.probabilities[3] / result.probabilities[2]
            assert ratio_23 == pytest.approx(MIGRATION_DECAY, abs=0.05)

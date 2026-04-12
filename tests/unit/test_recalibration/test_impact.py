"""C-2f: ImpactAssessor helper logic (no DB required)."""

import numpy as np

from infrastructure.recalibration.impact import ImpactAssessor
from infrastructure.recalibration.types import TierThresholdChange


class TestWeightedScore:
    def test_empty_weights_returns_zero(self):
        a = ImpactAssessor(db=None)
        assert a._weighted_score({"s1": 80.0}, {}) == 0.0

    def test_weighted_average_scaled(self):
        a = ImpactAssessor(db=None)
        # signal=80, weight=1 -> 80 * 10 = 800 (0-1000 scale)
        assert a._weighted_score({"s1": 80.0}, {"s1": 1.0}) == 800.0

    def test_missing_signal_skipped(self):
        a = ImpactAssessor(db=None)
        # Only s1 present; s2's weight is ignored
        result = a._weighted_score({"s1": 50.0}, {"s1": 1.0, "s2": 1.0})
        assert result == 500.0


class TestTierForScore:
    def test_score_in_first_tier(self):
        a = ImpactAssessor(db=None)
        boundaries = [(1, 0, 300), (2, 300, 700), (3, 700, 1000)]
        assert a._tier_for_score(150, boundaries) == 1

    def test_score_in_middle_tier(self):
        a = ImpactAssessor(db=None)
        boundaries = [(1, 0, 300), (2, 300, 700), (3, 700, 1000)]
        assert a._tier_for_score(500, boundaries) == 2

    def test_score_on_boundary(self):
        a = ImpactAssessor(db=None)
        boundaries = [(1, 0, 300), (2, 300, 700), (3, 700, 1000)]
        # 300 is in both tier 1 (max) and tier 2 (min); first match wins
        assert a._tier_for_score(300, boundaries) == 1

    def test_empty_boundaries(self):
        a = ImpactAssessor(db=None)
        assert a._tier_for_score(500, []) == 0


class TestApplyTierChanges:
    def test_max_boundary_shifts_both_tiers(self):
        a = ImpactAssessor(db=None)
        boundaries = [(1, 0, 300), (2, 300, 700)]
        changes = [TierThresholdChange(
            band_id=1, boundary="max",
            current_value=300, proposed_value=250, delta=-50,
        )]
        result = a._apply_tier_changes(boundaries, changes)
        # Tier 1's max dropped, tier 2's min dropped to match
        result_by_id = {t[0]: t for t in result}
        assert result_by_id[1][2] == 250  # tier 1 max
        assert result_by_id[2][1] == 250  # tier 2 min

    def test_no_changes_preserves_boundaries(self):
        a = ImpactAssessor(db=None)
        boundaries = [(1, 0, 300), (2, 300, 700)]
        result = a._apply_tier_changes(boundaries, [])
        assert result == boundaries


class TestAUC:
    def test_perfect_separation(self):
        a = ImpactAssessor(db=None)
        # Lower scores associated with loss=1; higher with loss=0
        # Our AUC convention: higher AUC = more predictive
        scores = np.array([20, 25, 30, 70, 75, 80])
        labels = np.array([1, 1, 1, 0, 0, 0])
        auc = a._auc(scores, labels)
        assert auc > 0.9  # near-perfect separation

    def test_random_separation(self):
        a = ImpactAssessor(db=None)
        rng = np.random.default_rng(0)
        scores = rng.normal(50, 10, 100)
        labels = rng.integers(0, 2, 100)
        auc = a._auc(scores, labels)
        # Random data should give AUC near 0.5
        assert 0.35 < auc < 0.65

    def test_all_one_class_returns_half(self):
        a = ImpactAssessor(db=None)
        scores = np.array([20, 25, 30])
        labels = np.array([1, 1, 1])
        assert a._auc(scores, labels) == 0.5

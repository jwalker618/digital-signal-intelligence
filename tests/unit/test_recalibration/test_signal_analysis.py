"""C-2c: SignalAnalyser statistical primitives (no DB required)."""

import numpy as np
import pytest

from infrastructure.recalibration.signal_analysis import SignalAnalyser


class TestInformationValue:
    def test_iv_high_when_distributions_differ(self):
        analyser = SignalAnalyser(db=None)
        # Loss cohort: low scores; No-loss: high scores (strongly predictive)
        loss = list(np.random.default_rng(0).normal(25, 10, 200))
        no_loss = list(np.random.default_rng(1).normal(75, 10, 200))
        iv = analyser._compute_iv(loss, no_loss, n_bins=5)
        assert iv > 0.5, f"Expected strong IV for separated distributions, got {iv:.3f}"

    def test_iv_near_zero_when_distributions_overlap(self):
        analyser = SignalAnalyser(db=None)
        # Both cohorts drawn from identical distribution
        loss = list(np.random.default_rng(2).normal(50, 10, 200))
        no_loss = list(np.random.default_rng(3).normal(50, 10, 200))
        iv = analyser._compute_iv(loss, no_loss, n_bins=5)
        assert iv < 0.1, f"Expected near-zero IV for overlapping distributions, got {iv:.3f}"

    def test_iv_handles_empty(self):
        analyser = SignalAnalyser(db=None)
        assert analyser._compute_iv([], [], n_bins=5) == 0.0
        assert analyser._compute_iv([50.0], [], n_bins=5) == 0.0

    def test_iv_handles_constant_values(self):
        analyser = SignalAnalyser(db=None)
        loss = [50.0] * 100
        no_loss = [50.0] * 100
        iv = analyser._compute_iv(loss, no_loss, n_bins=5)
        # All in one bin -> no discrimination possible
        assert iv == 0.0


class TestStability:
    def test_stable_when_splits_agree(self):
        analyser = SignalAnalyser(db=None)
        rng = np.random.default_rng(42)
        # Both distributions are stable -- splits should have similar medians
        loss = list(rng.normal(30, 5, 30))
        no_loss = list(rng.normal(70, 5, 30))
        stability = analyser._compute_stability(loss, no_loss)
        assert stability > 0.6

    def test_unstable_when_splits_disagree(self):
        analyser = SignalAnalyser(db=None)
        # First third of loss = high scores; last two-thirds = low scores
        loss = [80.0] * 10 + [20.0] * 20
        no_loss = [50.0] * 30
        stability = analyser._compute_stability(loss, no_loss)
        assert stability < 0.5

    def test_returns_zero_with_insufficient_data(self):
        analyser = SignalAnalyser(db=None)
        assert analyser._compute_stability([1, 2, 3], [4, 5, 6]) == 0.0


class TestAlignmentClassification:
    def _m(self, iv, rho=None):
        return {"iv": iv, "rho": rho if rho is not None else 0.3}

    def test_low_iv_and_nonzero_weight_flagged(self):
        analyser = SignalAnalyser(db=None)
        from infrastructure.recalibration.types import Alignment
        alignment = analyser._classify_alignment(self._m(0.005), 0.2, 0.05)
        assert alignment == Alignment.SIGNIFICANT_MISALIGNMENT

    def test_healthy_signal_marked_well_calibrated(self):
        analyser = SignalAnalyser(db=None)
        from infrastructure.recalibration.types import Alignment
        alignment = analyser._classify_alignment(self._m(0.3, 0.6), 0.15, 0.16)
        assert alignment == Alignment.WELL_CALIBRATED

    def test_large_weight_gap_marked_adjustment_suggested(self):
        analyser = SignalAnalyser(db=None)
        from infrastructure.recalibration.types import Alignment
        # Current 0.1, evidence suggests 0.4 (+300% gap)
        alignment = analyser._classify_alignment(self._m(0.3, 0.6), 0.1, 0.4)
        assert alignment == Alignment.ADJUSTMENT_SUGGESTED

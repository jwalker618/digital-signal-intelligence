"""WE-3b: Confound controller -- partial correlation math."""

import numpy as np
import pytest

from world_engine.inferencer.confound_control import ConfoundController


class TestPartialCorrelation:
    def _prepare(self, n=200):
        rng = np.random.default_rng(42)
        return rng

    def test_spurious_relationship_detected(self):
        """x and y both caused by z -> partial rho collapses."""
        rng = self._prepare()
        z = rng.normal(0, 1, 200)
        x = z + rng.normal(0, 0.1, 200)
        y = z + rng.normal(0, 0.1, 200)

        cc = ConfoundController()
        raw_rho = np.corrcoef(x, y)[0, 1]
        partial = cc._partial_correlation(x, y, z)

        assert raw_rho > 0.9, "Raw correlation should be very high"
        assert abs(partial) < 0.2, f"Partial rho should collapse, got {partial}"

    def test_genuine_relationship_preserved(self):
        """x directly causes y, z is independent -> partial rho ≈ raw rho."""
        rng = self._prepare()
        z = rng.normal(0, 1, 200)
        x = rng.normal(0, 1, 200)
        y = 0.8 * x + rng.normal(0, 0.3, 200)

        cc = ConfoundController()
        raw_rho = np.corrcoef(x, y)[0, 1]
        partial = cc._partial_correlation(x, y, z)

        assert raw_rho > 0.8
        assert abs(partial - raw_rho) < 0.1, f"Partial should stay close to raw: {partial} vs {raw_rho}"

    def test_nan_values_handled(self):
        """Partial rho drops rows with NaN in any series and still computes."""
        cc = ConfoundController()
        rng = np.random.default_rng(0)
        x = rng.normal(0, 1, 50)
        y = x + rng.normal(0, 0.3, 50)
        z = rng.normal(0, 1, 50)
        # Introduce some NaN values
        x[5] = np.nan
        y[10] = np.nan
        partial = cc._partial_correlation(x, y, z)
        assert partial is not None  # 48 valid rows is above the min threshold
        assert partial > 0.5  # x and y are strongly related independently of z

    def test_insufficient_data(self):
        cc = ConfoundController()
        x = np.array([1.0, 2.0])
        y = np.array([3.0, 4.0])
        z = np.array([5.0, 6.0])
        partial = cc._partial_correlation(x, y, z)
        assert partial is None  # below minimum n

    def test_constant_series_guard(self):
        cc = ConfoundController()
        x = np.ones(50)
        y = np.random.default_rng(0).normal(0, 1, 50)
        z = np.random.default_rng(1).normal(0, 1, 50)
        partial = cc._partial_correlation(x, y, z)
        assert partial is None  # constant x has zero variance

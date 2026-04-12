"""WE-3b: Granger causality pooled panel test -- tests the pure math."""

import numpy as np
import pytest

from world_engine.inferencer.granger import CausalInferencer, GrangerConfig


class TestPooledFTest:
    """Direct tests on _pooled_f_test -- no DB required."""

    def _random_observations(self, n, y_depends_on_lag_s: bool, seed: int = 42):
        rng = np.random.default_rng(seed)
        lag_s = rng.normal(0, 1, n)
        lag_t = rng.normal(0, 1, n)
        noise = rng.normal(0, 0.5, n)
        if y_depends_on_lag_s:
            y = 0.8 * lag_s + 0.3 * lag_t + noise
        else:
            y = 0.3 * lag_t + noise
        return list(zip(y, lag_s, lag_t))

    def test_detects_real_relationship(self):
        inferencer = CausalInferencer()
        obs = self._random_observations(500, y_depends_on_lag_s=True)
        f, p = inferencer._pooled_f_test(obs)
        assert f is not None
        assert p < 0.01, f"Expected p < 0.01 for real relationship, got {p}"

    def test_rejects_null_relationship(self):
        inferencer = CausalInferencer()
        obs = self._random_observations(500, y_depends_on_lag_s=False)
        f, p = inferencer._pooled_f_test(obs)
        # Not dependent on lag_s -> F-test should not be significant
        assert p is None or p >= 0.05, f"Expected non-significance, got p={p}"

    def test_insufficient_data(self):
        inferencer = CausalInferencer()
        obs = [(1.0, 2.0, 3.0)]  # n=1
        f, p = inferencer._pooled_f_test(obs)
        assert f is None and p is None

    def test_zero_variance_guard(self):
        """Constant series should not raise -- returns None."""
        inferencer = CausalInferencer()
        obs = [(1.0, 2.0, 3.0)] * 100  # all identical
        f, p = inferencer._pooled_f_test(obs)
        assert f is None and p is None


class TestEffectSize:
    def test_zero_rho_is_zero(self):
        inferencer = CausalInferencer()
        assert inferencer._effect_size(0.0) == 0.0

    def test_increases_with_rho(self):
        inferencer = CausalInferencer()
        assert inferencer._effect_size(0.1) < inferencer._effect_size(0.3)
        assert inferencer._effect_size(0.3) < inferencer._effect_size(0.5)

    def test_near_one_bounded(self):
        inferencer = CausalInferencer()
        # Should not produce inf even as rho -> 1
        d = inferencer._effect_size(0.999)
        assert d == 5.0  # capped

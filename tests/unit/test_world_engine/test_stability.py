"""WE-3c: TemporalStabilityTracker -- sign-flip + windowing."""

from world_engine.validator.stability import StabilityConfig, TemporalStabilityTracker


class TestStabilityConfig:
    def test_defaults(self):
        cfg = StabilityConfig()
        assert cfg.num_windows == 4
        assert cfg.min_stable_windows == 3
        assert cfg.rho_threshold == 0.2

    def test_stable_windows_cannot_exceed_num_windows(self):
        # Sanity: config should never require more stable windows than total
        cfg = StabilityConfig()
        assert cfg.min_stable_windows <= cfg.num_windows

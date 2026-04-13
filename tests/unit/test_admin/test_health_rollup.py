"""B-1b: SystemHealthAggregator rollup logic (no DB required)."""

from infrastructure.admin.health import (
    HealthStatus,
    SubsystemHealth,
    SystemHealthAggregator,
)


class TestRollupStatus:
    def test_all_ok_is_ok(self):
        subs = [
            SubsystemHealth(name="a", status=HealthStatus.OK),
            SubsystemHealth(name="b", status=HealthStatus.OK),
        ]
        assert SystemHealthAggregator._rollup_status(subs) == HealthStatus.OK

    def test_any_down_is_down(self):
        subs = [
            SubsystemHealth(name="a", status=HealthStatus.OK),
            SubsystemHealth(name="b", status=HealthStatus.DOWN),
            SubsystemHealth(name="c", status=HealthStatus.DEGRADED),
        ]
        assert SystemHealthAggregator._rollup_status(subs) == HealthStatus.DOWN

    def test_degraded_beats_unknown(self):
        subs = [
            SubsystemHealth(name="a", status=HealthStatus.UNKNOWN),
            SubsystemHealth(name="b", status=HealthStatus.DEGRADED),
            SubsystemHealth(name="c", status=HealthStatus.OK),
        ]
        assert SystemHealthAggregator._rollup_status(subs) == HealthStatus.DEGRADED

    def test_unknown_beats_ok(self):
        subs = [
            SubsystemHealth(name="a", status=HealthStatus.UNKNOWN),
            SubsystemHealth(name="b", status=HealthStatus.OK),
        ]
        assert SystemHealthAggregator._rollup_status(subs) == HealthStatus.UNKNOWN

    def test_empty_is_unknown(self):
        assert SystemHealthAggregator._rollup_status([]) == HealthStatus.UNKNOWN


class TestHealthStatusEnum:
    def test_values(self):
        assert HealthStatus.OK.value == "ok"
        assert HealthStatus.DEGRADED.value == "degraded"
        assert HealthStatus.DOWN.value == "down"
        assert HealthStatus.UNKNOWN.value == "unknown"

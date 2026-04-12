"""WE-3g: Scheduler -- trigger logic + configuration."""

from world_engine.scheduler import SchedulerConfig


class TestSchedulerConfig:
    def test_defaults(self):
        cfg = SchedulerConfig()
        assert cfg.min_new_assessments == 100
        assert cfg.max_days_between_runs == 7
        assert cfg.min_entities_for_discovery == 50

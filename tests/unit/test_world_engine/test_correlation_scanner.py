"""WE-3a: CorrelationScanner -- pure logic tests (no DB required)."""

import numpy as np

from world_engine.scanner import CorrelationScanner, ScannerConfig


class TestScannerConfig:
    def test_defaults(self):
        cfg = ScannerConfig()
        assert cfg.min_entities == 50
        assert cfg.min_observations_per_pair == 30
        assert cfg.rho_threshold == 0.3
        assert cfg.p_threshold == 0.01

    def test_override(self):
        cfg = ScannerConfig(min_entities=25, rho_threshold=0.5)
        assert cfg.min_entities == 25
        assert cfg.rho_threshold == 0.5


class TestCoverageScope:
    def test_union_across_entities(self):
        scanner = CorrelationScanner()
        coverages = {0: {"cyber"}, 1: {"do"}, 2: {"cyber", "fi"}}
        scope = scanner._coverage_scope(np.array([0, 1, 2]), coverages)
        assert scope == ["cyber", "do", "fi"]

    def test_empty_entities(self):
        scanner = CorrelationScanner()
        scope = scanner._coverage_scope(np.array([]), {})
        assert scope == []

    def test_single_coverage(self):
        scanner = CorrelationScanner()
        scope = scanner._coverage_scope(
            np.array([0, 1, 2]),
            {0: {"cyber"}, 1: {"cyber"}, 2: {"cyber"}},
        )
        assert scope == ["cyber"]

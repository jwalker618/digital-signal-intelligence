"""WE-1b maturity evaluator tests (stage determination logic).

Tests the pure stage-determination function. DB-dependent evaluate() is
covered in integration tests.
"""

import pytest

from world_engine.maturity import MaturityEvaluator
from world_engine.types import MaturityStage


class TestStageDetermination:
    def setup_method(self):
        self.ev = MaturityEvaluator()

    def test_seed_with_no_data(self):
        assert self.ev._determine_stage(0, 0.0) == MaturityStage.SEED

    def test_seed_with_insufficient_population(self):
        assert self.ev._determine_stage(100, 12.0) == MaturityStage.SEED

    def test_seed_with_insufficient_time(self):
        assert self.ev._determine_stage(1000, 3.0) == MaturityStage.SEED

    def test_learn_threshold(self):
        assert self.ev._determine_stage(500, 6.0) == MaturityStage.LEARN
        assert self.ev._determine_stage(4999, 17.9) == MaturityStage.LEARN

    def test_emerge_threshold(self):
        assert self.ev._determine_stage(5000, 18.0) == MaturityStage.EMERGE
        assert self.ev._determine_stage(49999, 35.9) == MaturityStage.EMERGE

    def test_simulate_threshold(self):
        assert self.ev._determine_stage(50000, 36.0) == MaturityStage.SIMULATE
        assert self.ev._determine_stage(1_000_000, 60.0) == MaturityStage.SIMULATE


class TestCapabilities:
    def test_seed_capabilities(self):
        caps = MaturityEvaluator.CAPABILITIES[MaturityStage.SEED]
        assert caps["consistency"] is True
        assert caps["discovery"] is False
        assert caps["caf"] is False
        assert caps["simulation"] is False

    def test_learn_enables_discovery(self):
        caps = MaturityEvaluator.CAPABILITIES[MaturityStage.LEARN]
        assert caps["consistency"] is True
        assert caps["discovery"] is True
        assert caps["caf"] is False

    def test_emerge_enables_caf_and_concentration(self):
        caps = MaturityEvaluator.CAPABILITIES[MaturityStage.EMERGE]
        assert caps["caf"] is True
        assert caps["portfolio_concentration"] is True
        assert caps["simulation"] is False

    def test_simulate_enables_all(self):
        caps = MaturityEvaluator.CAPABILITIES[MaturityStage.SIMULATE]
        assert all(caps.values()), f"Expected all True, got {caps}"

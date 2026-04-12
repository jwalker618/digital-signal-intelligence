"""WE-3c: Holdout validator -- deterministic partitioning."""

from world_engine.validator.holdout import HoldoutConfig, HoldoutValidator


class TestDeterministicPartitioning:
    def test_same_entity_always_in_same_bucket(self):
        v = HoldoutValidator()
        # Running the hash many times must yield the same result
        results = [v._in_holdout("acme_corp") for _ in range(100)]
        assert len(set(results)) == 1

    def test_holdout_ratio_approximates_target(self):
        v = HoldoutValidator(HoldoutConfig(holdout_fraction=0.3))
        entities = [f"entity_{i}" for i in range(1000)]
        in_holdout = sum(1 for e in entities if v._in_holdout(e))
        # ~30% with tolerance
        assert 250 <= in_holdout <= 350, f"Expected ~300, got {in_holdout}"

    def test_different_fractions_different_splits(self):
        v_small = HoldoutValidator(HoldoutConfig(holdout_fraction=0.1))
        v_large = HoldoutValidator(HoldoutConfig(holdout_fraction=0.5))
        entities = [f"entity_{i}" for i in range(200)]
        small_count = sum(1 for e in entities if v_small._in_holdout(e))
        large_count = sum(1 for e in entities if v_large._in_holdout(e))
        assert small_count < large_count

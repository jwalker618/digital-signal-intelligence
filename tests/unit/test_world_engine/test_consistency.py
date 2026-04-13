"""WE-2: Consistency Scorer unit tests."""

import time

import pytest

from world_engine.consistency import ConsistencyInputs, ConsistencyScorer, SignalScore


def _make_signals(group: str, scores: list[float]) -> list[SignalScore]:
    return [SignalScore(f"{group}_s{i}", group, s) for i, s in enumerate(scores)]


class TestSignalPair:
    """Component 1: within-group signal pair consistency."""

    def test_perfectly_agreeing_signals(self):
        scorer = ConsistencyScorer()
        inputs = ConsistencyInputs(
            entity_id="e1",
            assessment_id="a1",
            signals=_make_signals("g1", [70.0, 70.0, 70.0]),
        )
        s = scorer.score(inputs)
        # 3 signals in one group = 3 pairs, all at 1.0
        assert all(v == 1.0 for v in s.signal_pair_scores.values())
        assert s.divergent_pairs == []

    def test_maximally_divergent_signals(self):
        scorer = ConsistencyScorer()
        inputs = ConsistencyInputs(
            entity_id="e1", assessment_id="a1",
            signals=_make_signals("g1", [0.0, 100.0]),
        )
        s = scorer.score(inputs)
        pair_key = next(iter(s.signal_pair_scores))
        assert s.signal_pair_scores[pair_key] == 0.0  # max distance
        assert pair_key in s.divergent_pairs

    def test_singleton_groups_skipped(self):
        scorer = ConsistencyScorer()
        inputs = ConsistencyInputs(
            entity_id="e1", assessment_id="a1",
            signals=[SignalScore("s1", "g1", 70.0), SignalScore("s2", "g2", 80.0)],
        )
        s = scorer.score(inputs)
        assert s.signal_pair_scores == {}

    def test_divergent_flagged(self):
        """Pairs below 0.5 threshold land in divergent_pairs."""
        scorer = ConsistencyScorer()
        inputs = ConsistencyInputs(
            entity_id="e1", assessment_id="a1",
            signals=_make_signals("g1", [80.0, 20.0]),  # distance 0.6 -> consistency 0.4
        )
        s = scorer.score(inputs)
        assert len(s.divergent_pairs) == 1

    def test_not_divergent_above_threshold(self):
        scorer = ConsistencyScorer()
        inputs = ConsistencyInputs(
            entity_id="e1", assessment_id="a1",
            signals=_make_signals("g1", [80.0, 50.0]),  # distance 0.3 -> consistency 0.7
        )
        s = scorer.score(inputs)
        assert s.divergent_pairs == []


class TestCrossGroup:
    """Component 2: between-group composite consistency."""

    def test_fully_aligned_groups(self):
        scorer = ConsistencyScorer()
        inputs = ConsistencyInputs(
            entity_id="e1", assessment_id="a1",
            group_composites={"g1": 75.0, "g2": 75.0, "g3": 75.0},
        )
        s = scorer.score(inputs)
        assert all(v == 1.0 for v in s.cross_group_scores.values())

    def test_divergent_groups(self):
        scorer = ConsistencyScorer()
        inputs = ConsistencyInputs(
            entity_id="e1", assessment_id="a1",
            group_composites={"g1": 20.0, "g2": 80.0},  # distance 0.6 -> 0.4
        )
        s = scorer.score(inputs)
        assert 0.39 <= list(s.cross_group_scores.values())[0] <= 0.41

    def test_single_group_produces_no_pairs(self):
        scorer = ConsistencyScorer()
        inputs = ConsistencyInputs(
            entity_id="e1", assessment_id="a1",
            group_composites={"g1": 50.0},
        )
        s = scorer.score(inputs)
        assert s.cross_group_scores == {}

    def test_0_1000_composite_scale_rescaled(self):
        """Composite scores on the 0-1000 scale get auto-normalised."""
        scorer = ConsistencyScorer()
        inputs = ConsistencyInputs(
            entity_id="e1", assessment_id="a1",
            group_composites={"g1": 750.0, "g2": 750.0},
        )
        s = scorer.score(inputs)
        assert list(s.cross_group_scores.values())[0] == 1.0


class TestCrossLayer:
    """Component 3: cross-layer tier agreement."""

    def test_fully_aligned_layers(self):
        scorer = ConsistencyScorer()
        inputs = ConsistencyInputs(
            entity_id="e1", assessment_id="a1",
            risk_tier=2, loss_tier=2, exposure_tier=2, max_tier=5,
        )
        s = scorer.score(inputs)
        assert s.cross_layer_divergence == {
            "risk_vs_loss": 1.0, "risk_vs_exposure": 1.0, "loss_vs_exposure": 1.0,
        }

    def test_maximally_divergent_layers(self):
        scorer = ConsistencyScorer()
        inputs = ConsistencyInputs(
            entity_id="e1", assessment_id="a1",
            risk_tier=1, loss_tier=5, exposure_tier=1, max_tier=5,
        )
        s = scorer.score(inputs)
        # risk_vs_loss gap = 4/5 = 0.8 -> consistency 0.2
        assert s.cross_layer_divergence["risk_vs_loss"] == pytest.approx(0.2, abs=0.01)
        assert s.cross_layer_divergence["risk_vs_exposure"] == 1.0
        assert s.cross_layer_divergence["loss_vs_exposure"] == pytest.approx(0.2, abs=0.01)

    def test_missing_layers_skipped(self):
        scorer = ConsistencyScorer()
        inputs = ConsistencyInputs(
            entity_id="e1", assessment_id="a1",
            risk_tier=2, loss_tier=None, exposure_tier=3, max_tier=5,
        )
        s = scorer.score(inputs)
        # Only risk_vs_exposure can be computed
        assert set(s.cross_layer_divergence.keys()) == {"risk_vs_exposure"}


class TestOverallAggregation:
    """Weighted overall score + dynamic weight renormalisation."""

    def test_perfect_all_components(self):
        scorer = ConsistencyScorer()
        inputs = ConsistencyInputs(
            entity_id="e1", assessment_id="a1",
            signals=_make_signals("g1", [70.0, 70.0]),
            group_composites={"g1": 70.0, "g2": 70.0},
            risk_tier=2, loss_tier=2, exposure_tier=2, max_tier=5,
        )
        s = scorer.score(inputs)
        assert s.overall_consistency == 1.0

    def test_no_data_returns_neutral(self):
        scorer = ConsistencyScorer()
        inputs = ConsistencyInputs(entity_id="e1", assessment_id="a1")
        s = scorer.score(inputs)
        # With no data we have nothing to disagree with -> 1.0
        assert s.overall_consistency == 1.0

    def test_weighted_average(self):
        """0.3/0.4/0.3 weighting verified via a constructed test case."""
        scorer = ConsistencyScorer()
        # Design:
        #   signal-pair component = 1.0  (perfectly aligned)
        #   cross-group component = 0.0  (max divergence)
        #   cross-layer component = 1.0  (aligned)
        # Expected overall = 0.3*1 + 0.4*0 + 0.3*1 = 0.6
        inputs = ConsistencyInputs(
            entity_id="e1", assessment_id="a1",
            signals=_make_signals("g1", [70.0, 70.0]),
            group_composites={"g1": 0.0, "g2": 100.0},
            risk_tier=2, loss_tier=2, exposure_tier=2, max_tier=5,
        )
        s = scorer.score(inputs)
        assert s.overall_consistency == pytest.approx(0.6, abs=0.01)

    def test_partial_data_renormalised(self):
        """If cross-group is missing, weights over the remaining components
        sum to 1.0 (no free ride for the missing component)."""
        scorer = ConsistencyScorer()
        inputs = ConsistencyInputs(
            entity_id="e1", assessment_id="a1",
            signals=_make_signals("g1", [70.0, 70.0]),
            risk_tier=2, loss_tier=2, exposure_tier=2, max_tier=5,
        )
        s = scorer.score(inputs)
        # Both remaining components are 1.0 -> overall is 1.0
        assert s.overall_consistency == 1.0


class TestPerformance:
    """Latency must stay under the WE-2 <50ms budget."""

    def test_large_signal_set_under_50ms(self):
        # Simulate a coverage with 400 signals across 20 groups
        signals = []
        for group_idx in range(20):
            for sig_idx in range(20):
                signals.append(SignalScore(
                    signal_id=f"sig_{group_idx}_{sig_idx}",
                    group_id=f"group_{group_idx}",
                    raw_score=50.0 + (sig_idx % 30),
                ))
        inputs = ConsistencyInputs(
            entity_id="e1", assessment_id="a1",
            signals=signals,
            group_composites={f"group_{i}": 50.0 + i for i in range(20)},
            risk_tier=2, loss_tier=3, exposure_tier=2, max_tier=5,
        )

        scorer = ConsistencyScorer()
        # Warm up (first call has import overhead)
        scorer.score(inputs)

        start = time.perf_counter()
        for _ in range(100):
            scorer.score(inputs)
        elapsed_ms = (time.perf_counter() - start) * 1000 / 100

        assert elapsed_ms < 50.0, f"Scorer took {elapsed_ms:.2f}ms/run, budget is 50ms"
        # Sanity: we computed a lot of pairs
        # 20 groups × 20 signals × 19/2 = 3800 within-group pairs
        # 20 groups × 19/2 = 190 cross-group pairs


class TestStableKeys:
    """Pair keys must be stable regardless of signal insertion order."""

    def test_pair_key_sorted(self):
        scorer = ConsistencyScorer()
        inputs_a = ConsistencyInputs(
            entity_id="e1", assessment_id="a1",
            signals=[SignalScore("z_sig", "g1", 50.0), SignalScore("a_sig", "g1", 80.0)],
        )
        inputs_b = ConsistencyInputs(
            entity_id="e1", assessment_id="a1",
            signals=[SignalScore("a_sig", "g1", 80.0), SignalScore("z_sig", "g1", 50.0)],
        )
        a = scorer.score(inputs_a)
        b = scorer.score(inputs_b)
        assert list(a.signal_pair_scores.keys()) == list(b.signal_pair_scores.keys())
        assert list(a.signal_pair_scores.keys())[0] == "a_sig|z_sig"

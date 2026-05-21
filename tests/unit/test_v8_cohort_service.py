"""v8 Phase 2 — cohort key derivation + pure percentile math."""
from __future__ import annotations

import pytest

from layers.cohort.service import (
    MIN_COHORT_SIZE,
    CohortKey,
    MissingCohortAttributesError,
    cohort_id_for,
    cohort_stats_from_scores,
    derive_cohort_key,
    normalize_entity_key,
    percentile_from_scores,
    signal_ranking_from_values,
)


class TestNormalizeEntityKey:
    def test_lowercases_and_strips(self):
        assert normalize_entity_key("  Acme Industries  ") == "acme industries"

    def test_already_normalized(self):
        assert normalize_entity_key("acme industries") == "acme industries"

    def test_internal_whitespace_preserved(self):
        # Only leading/trailing stripped; internal whitespace stays
        assert normalize_entity_key("acme  industries") == "acme  industries"


class TestDeriveCohortKey:
    def test_basic_extraction(self):
        key = derive_cohort_key(
            {"naics": "5112", "revenue": 180_000_000},
            coverage="cyber",
        )
        assert key == CohortKey(
            coverage="cyber",
            naics_section="51",
            revenue_band="50-250M",
        )

    def test_accepts_naics_code_alias(self):
        key = derive_cohort_key(
            {"naics_code": "6221", "revenue": 95_000_000},
            coverage="cyber",
        )
        assert key.naics_section == "62"

    def test_accepts_annual_revenue_alias(self):
        key = derive_cohort_key(
            {"naics": "5112", "annual_revenue": 25_000_000},
            coverage="cyber",
        )
        assert key.revenue_band == "10-50M"

    def test_missing_naics_raises(self):
        with pytest.raises(MissingCohortAttributesError, match="NAICS"):
            derive_cohort_key({"revenue": 100_000_000}, coverage="cyber")

    def test_missing_revenue_raises(self):
        with pytest.raises(MissingCohortAttributesError, match="revenue"):
            derive_cohort_key({"naics": "5112"}, coverage="cyber")

    def test_empty_submission_data_raises(self):
        with pytest.raises(MissingCohortAttributesError):
            derive_cohort_key({}, coverage="cyber")

    def test_none_submission_data_raises(self):
        with pytest.raises(MissingCohortAttributesError):
            derive_cohort_key(None, coverage="cyber")  # type: ignore[arg-type]


class TestCohortIdFor:
    def test_format(self):
        key = CohortKey(coverage="cyber", naics_section="51", revenue_band="50-250M")
        assert cohort_id_for(key) == "cyber:51:50-250M"

    def test_round_trip(self):
        # Re-derived key from same inputs produces identical cohort_id
        a = derive_cohort_key(
            {"naics": "5112", "revenue": 180_000_000}, coverage="cyber"
        )
        b = derive_cohort_key(
            {"naics": 511210, "revenue": "180000000"}, coverage="cyber"
        )
        assert cohort_id_for(a) == cohort_id_for(b)


class TestPercentileFromScores:
    def test_too_thin_returns_none(self):
        scores = [100.0] * (MIN_COHORT_SIZE - 1)
        assert percentile_from_scores(scores, 100.0) is None

    def test_below_all(self):
        scores = [float(i * 10) for i in range(1, 21)]  # 10..200
        assert percentile_from_scores(scores, 0.0) == 0.0

    def test_above_all(self):
        scores = [float(i * 10) for i in range(1, 21)]  # 10..200
        assert percentile_from_scores(scores, 9999.0) == 100.0

    def test_median(self):
        # 10 scores 1..10; target 5 has 4 below (1-4), 1 tie -> 4.5/10 = 45%
        scores = [float(i) for i in range(1, 11)]
        assert percentile_from_scores(scores, 5.0) == 45.0

    def test_tie_half_credit(self):
        # 10 scores all equal to 100 -> any target of 100 gets 50%
        scores = [100.0] * 10
        assert percentile_from_scores(scores, 100.0) == 50.0

    def test_unique_value(self):
        # 10 scores 1..10; target 11 (above all) -> 100
        scores = [float(i) for i in range(1, 11)]
        assert percentile_from_scores(scores, 11.0) == 100.0

    def test_just_at_threshold(self):
        # Exactly MIN_COHORT_SIZE -- returns a value
        scores = [float(i) for i in range(MIN_COHORT_SIZE)]
        assert percentile_from_scores(scores, scores[0]) is not None


class TestCohortStatsFromScores:
    def test_below_threshold(self):
        scores = [100.0] * (MIN_COHORT_SIZE - 1)
        assert cohort_stats_from_scores("cyber:51:50-250M", scores) is None

    def test_at_threshold(self):
        scores = [float(i) for i in range(1, MIN_COHORT_SIZE + 1)]
        stats = cohort_stats_from_scores("cyber:51:50-250M", scores)
        assert stats is not None
        assert stats.size == MIN_COHORT_SIZE
        assert stats.cohort_id == "cyber:51:50-250M"
        assert stats.mean == 5.5
        assert stats.median == 5.5

    def test_p25_p75(self):
        scores = list(range(1, 101))  # 1..100
        stats = cohort_stats_from_scores("test", [float(s) for s in scores])
        assert stats is not None
        # Approximately 25th and 75th percentile
        assert 20 <= stats.p25 <= 30
        assert 70 <= stats.p75 <= 80


class TestSignalRanking:
    def test_strengths_and_weaknesses(self):
        # Entity excels at mfa (3 stddev above mean), weak on dr_plan
        entity = {"mfa": 100.0, "dr_plan": 20.0, "tls": 80.0}
        cohort = {
            "mfa": [70.0] * 20,
            "dr_plan": [80.0] * 20,
            "tls": [80.0] * 20,  # zero variance -> skipped
        }
        # Pad cohort entries with some variance for stddev to compute
        cohort["mfa"] = [70.0, 72.0, 68.0, 71.0, 69.0, 73.0]
        cohort["dr_plan"] = [80.0, 82.0, 78.0, 79.0, 81.0, 77.0]
        ranking = signal_ranking_from_values(entity, cohort)
        signal_ids = {s.signal_id for s in ranking.strengths}
        assert "mfa" in signal_ids
        weak_ids = {s.signal_id for s in ranking.weaknesses}
        assert "dr_plan" in weak_ids
        # tls had zero variance -> should be skipped entirely
        all_ids = signal_ids | weak_ids
        assert "tls" not in all_ids

    def test_thin_cohort_signal_skipped(self):
        entity = {"mfa": 100.0}
        cohort = {"mfa": [70.0, 72.0]}  # below 5-member threshold
        ranking = signal_ranking_from_values(entity, cohort)
        assert ranking.strengths == []
        assert ranking.weaknesses == []

    def test_empty_inputs(self):
        ranking = signal_ranking_from_values({}, {})
        assert ranking.strengths == []
        assert ranking.weaknesses == []

    def test_truncated_to_top_n(self):
        entity = {f"sig_{i}": 100.0 for i in range(10)}
        cohort = {f"sig_{i}": [50.0, 52.0, 48.0, 51.0, 49.0, 53.0] for i in range(10)}
        ranking = signal_ranking_from_values(entity, cohort, top_n=3)
        assert len(ranking.strengths) <= 3
        # All entries are strengths (entity_value > cohort_mean)
        assert ranking.weaknesses == []

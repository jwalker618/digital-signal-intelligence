"""V7 Phase 8 — reproducibility classifier + value-hash."""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

from signal_architecture.signals.stability import (
    canonical_value_hash,
    classify_ratio,
)
from signal_architecture.signals.types import SignalResult


# ---------------------------------------------------------------------------
# classify_ratio — mirrors the alembic-026 matview CASE expression
# ---------------------------------------------------------------------------

class TestClassifyRatio:
    def test_unknown_below_min_observations(self):
        assert classify_ratio(n=1, distinct_values=1, race_sensitive=False) == "unknown"
        assert classify_ratio(n=2, distinct_values=2, race_sensitive=False) == "unknown"

    def test_stable_when_all_agree(self):
        # 10 pulls, all identical -> ratio 0.1 -> stable
        assert classify_ratio(n=10, distinct_values=1, race_sensitive=False) == "stable"

    def test_stable_at_default_threshold(self):
        # ratio exactly 0.10
        assert classify_ratio(n=10, distinct_values=1, race_sensitive=False) == "stable"

    def test_flaky_between_thresholds(self):
        # 10 pulls, 4 distinct -> ratio 0.4 -> flaky
        assert classify_ratio(n=10, distinct_values=4, race_sensitive=False) == "flaky"

    def test_flaky_at_50pct(self):
        assert classify_ratio(n=10, distinct_values=5, race_sensitive=False) == "flaky"

    def test_unstable_above_flaky_threshold(self):
        # 10 pulls, 6 distinct -> ratio 0.6 -> unstable
        assert classify_ratio(n=10, distinct_values=6, race_sensitive=False) == "unstable"

    def test_race_sensitive_relaxed_threshold(self):
        # 10 pulls, 3 distinct -> ratio 0.3.
        # Default: flaky. Race-sensitive: stable (0.30 cutoff).
        assert classify_ratio(n=10, distinct_values=3, race_sensitive=False) == "flaky"
        assert classify_ratio(n=10, distinct_values=3, race_sensitive=True) == "stable"

    def test_race_sensitive_still_flaky_above_30pct(self):
        # ratio 0.4 > 0.30 -> flaky even for race-sensitive
        assert classify_ratio(n=10, distinct_values=4, race_sensitive=True) == "flaky"

    def test_min_observations_boundary(self):
        # n == 3 is the boundary — it classifies (not 'unknown'). At n=3 the
        # smallest possible ratio is 1/3 = 0.33, which exceeds the 0.10
        # default 'stable' cutoff, so the best a 3-pull window can be is
        # 'flaky'. Reaching 'stable' under the default threshold needs
        # n >= 10 with all pulls agreeing.
        assert classify_ratio(n=3, distinct_values=1, race_sensitive=False) == "flaky"
        assert classify_ratio(n=2, distinct_values=1, race_sensitive=False) == "unknown"
        # Race-sensitive triple at n=3 with full agreement IS stable (0.33 <= 0.30? no -> flaky)
        # 1/3 = 0.333 still > 0.30, so even race-sensitive n=3 is flaky.
        assert classify_ratio(n=3, distinct_values=1, race_sensitive=True) == "flaky"
        # A 10-pull race-sensitive window with 3 distinct (ratio 0.30) IS stable.
        assert classify_ratio(n=10, distinct_values=3, race_sensitive=True) == "stable"


# ---------------------------------------------------------------------------
# canonical_value_hash
# ---------------------------------------------------------------------------

def _sig(score=None, category=None):
    return SignalResult(
        signal_id="x", score=score, category=category, confidence=1.0,
        evidence_grade="observed", evidence_basis="b",
    )


class TestCanonicalValueHash:
    def test_identical_scores_hash_equal(self):
        assert canonical_value_hash(_sig(score=72.0)) == canonical_value_hash(_sig(score=72.0))

    def test_quantises_to_one_decimal(self):
        # 72.01 and 72.04 both round to 72.0 -> same hash
        assert canonical_value_hash(_sig(score=72.01)) == canonical_value_hash(_sig(score=72.04))

    def test_meaningfully_different_scores_differ(self):
        assert canonical_value_hash(_sig(score=72.0)) != canonical_value_hash(_sig(score=85.0))

    def test_category_exact_match(self):
        assert canonical_value_hash(_sig(category="A")) == canonical_value_hash(_sig(category="A"))
        assert canonical_value_hash(_sig(category="A")) != canonical_value_hash(_sig(category="B"))

    def test_empty_signal_fixed_sentinel(self):
        a = canonical_value_hash(_sig())
        b = canonical_value_hash(_sig())
        assert a == b
        # An empty signal hashes differently from a scored one.
        assert a != canonical_value_hash(_sig(score=0.0))


# ---------------------------------------------------------------------------
# SignalResult.reproducibility field
# ---------------------------------------------------------------------------

class TestReproducibilityField:
    def test_default_none(self):
        assert _sig(score=50.0).reproducibility is None

    def test_accepts_valid_values(self):
        for v in ("stable", "flaky", "unstable", "unknown"):
            s = SignalResult(
                signal_id="x", score=50.0, confidence=1.0,
                evidence_grade="observed", evidence_basis="b",
                reproducibility=v,
            )
            assert s.reproducibility == v


# ---------------------------------------------------------------------------
# Alembic 026 shape
# ---------------------------------------------------------------------------

_MIGRATION = Path("alembic/versions/026_signal_stability.py")


def _load_026():
    spec = importlib.util.spec_from_file_location("_v7_026", _MIGRATION)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


class TestAlembic026:
    def test_revision_lineage(self):
        mod = _load_026()
        assert mod.revision == "026"
        assert mod.down_revision == "025"

    def test_creates_observations_table(self):
        text = _MIGRATION.read_text(encoding="utf-8")
        assert "signal_stability_observations" in text

    def test_creates_materialised_view(self):
        text = _MIGRATION.read_text(encoding="utf-8")
        assert "CREATE MATERIALIZED VIEW signal_stability_classification" in text
        # The CASE expression mirrors classify_ratio thresholds.
        assert "0.30" in text and "0.10" in text and "0.50" in text

    def test_in_chain(self):
        from alembic.config import Config
        from alembic.script import ScriptDirectory
        cfg = Config("alembic.ini")
        sd = ScriptDirectory.from_config(cfg)
        rev = sd.get_revision("026")
        assert rev is not None
        assert rev.down_revision == "025"

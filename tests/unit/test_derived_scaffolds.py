"""V6/A-deep — derived-scaffold padding tests.

Each coverage's ``derived_signals.py`` registers N neutral-scaffold
inference functions that produce scores deterministically derived
from a hash of (entity_id, signal_id). These tests validate:

1. Determinism — same (entity, signal) yields the same score on every
   call.
2. Per-entity variation — different entities produce different scores
   for the same signal.
3. Per-signal variation — different signals produce different scores
   for the same entity.
4. Score range — within SignalResult's [0, 100] validation window.
5. Confidence range — within [0.50, 0.85].
"""
from __future__ import annotations

import pytest

# Register everything at import time.
import signal_architecture.signals.inference.functions  # noqa: F401
from signal_architecture.signals.inference.registry import get_inference_function


COVERAGES = [
    "aerospace", "captive", "casualty", "construction", "crop",
    "do", "env_liab", "event", "fi", "fpr", "marine", "medprof",
    "prodlib", "property", "pvt", "reinsurance", "specie", "teo", "wc",
]


def _call(fn_name: str, entity_id: str):
    fn = get_inference_function(fn_name)
    return fn(entity_id, None)


@pytest.mark.parametrize("coverage", COVERAGES)
def test_derived_signal_is_deterministic(coverage):
    fn_name = f"{coverage}_derived_01_basefunction"
    r1 = _call(fn_name, "entity-x")
    r2 = _call(fn_name, "entity-x")
    assert r1.score == r2.score
    assert r1.confidence == r2.confidence


@pytest.mark.parametrize("coverage", COVERAGES)
def test_derived_signal_varies_across_entities(coverage):
    fn_name = f"{coverage}_derived_01_basefunction"
    r1 = _call(fn_name, "entity-a")
    r2 = _call(fn_name, "entity-b")
    # Two deterministic hashes should differ almost always.
    assert r1.score != r2.score


@pytest.mark.parametrize("coverage", COVERAGES)
def test_derived_signal_varies_across_signals(coverage):
    r1 = _call(f"{coverage}_derived_01_basefunction", "entity-a")
    r2 = _call(f"{coverage}_derived_02_basefunction", "entity-a")
    assert r1.score != r2.score


@pytest.mark.parametrize("coverage", COVERAGES)
def test_derived_signal_score_in_range(coverage):
    fn_name = f"{coverage}_derived_01_basefunction"
    r = _call(fn_name, "entity-a")
    assert 30.0 <= r.score <= 70.0
    assert 0.50 <= r.confidence <= 0.85


def test_all_derived_fns_registered():
    """Every planned derived fn should be registered."""
    from signal_architecture.signals.inference.registry import list_inference_functions
    registered = set(list_inference_functions())
    expected_counts = {
        "aerospace": 32, "captive": 28, "casualty": 32, "construction": 34,
        "crop": 34, "do": 34, "env_liab": 34, "event": 27, "fi": 32,
        "fpr": 39, "marine": 34, "medprof": 28, "prodlib": 27, "property": 33,
        "pvt": 34, "reinsurance": 28, "specie": 27, "teo": 26, "wc": 27,
    }
    missing: dict[str, list[str]] = {}
    for cov, count in expected_counts.items():
        for i in range(1, count + 1):
            name = f"{cov}_derived_{i:02d}_basefunction"
            if name not in registered:
                missing.setdefault(cov, []).append(name)
    assert not missing, f"missing derived registrations: {missing}"

    total = sum(expected_counts.values())
    assert total == 590

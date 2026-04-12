"""B-2c: ConfigDiffEngine tests."""

import pytest

from infrastructure.admin.config_diff import (
    ConfigDiffEngine,
    _deep_field_changes,
    _get_signal_group,
    _get_signal_weight,
    _normalise_groups,
    _normalise_signal_registry,
    _normalise_tiers,
)


def _yaml_with_signals(signals: dict) -> str:
    """Build a minimal coverage YAML with the given signal dict."""
    import yaml
    return yaml.safe_dump({
        "coverage": {
            "configuration": {
                "signal_registry": signals,
            }
        }
    })


class TestNormalisation:
    def test_signal_registry_dict(self):
        assert _normalise_signal_registry({"s1": {"weight": 0.5}}) == {"s1": {"weight": 0.5}}

    def test_signal_registry_list(self):
        out = _normalise_signal_registry([{"id": "s1", "weight": 0.5}])
        assert out == {"s1": {"id": "s1", "weight": 0.5}}

    def test_signal_registry_none(self):
        assert _normalise_signal_registry(None) == {}

    def test_tiers_list(self):
        assert _normalise_tiers([{"id": 1}, {"id": 2}]) == [{"id": 1}, {"id": 2}]

    def test_tiers_bands_form(self):
        result = _normalise_tiers({"bands": [{"id": 1}]})
        assert result == [{"id": 1}]

    def test_groups_three_layer_form(self):
        result = _normalise_groups({
            "three_layer_assessment": [
                {"id": "g1", "risk_weight": 0.6},
                {"id": "g2", "risk_weight": 0.4},
            ]
        })
        assert "g1" in result and "g2" in result


class TestSignalWeightExtraction:
    def test_flat_weight(self):
        assert _get_signal_weight({"weight": 0.5}) == 0.5

    def test_nested_three_layer(self):
        assert _get_signal_weight({"three_layer_assessment": {"risk_weight": 0.3}}) == 0.3

    def test_none(self):
        assert _get_signal_weight(None) is None

    def test_group_id_flat(self):
        assert _get_signal_group({"group_id": "g1"}) == "g1"

    def test_group_id_nested(self):
        assert _get_signal_group({"three_layer_assessment": {"group_id": "g1"}}) == "g1"


class TestDeepFieldChanges:
    def test_watched_change(self):
        changes = _deep_field_changes(
            {"weight": 0.5}, {"weight": 0.7},
            watched={"weight"},
        )
        assert len(changes) == 1
        assert changes[0]["old"] == 0.5 and changes[0]["new"] == 0.7

    def test_unwatched_change_ignored(self):
        changes = _deep_field_changes(
            {"irrelevant": "x"}, {"irrelevant": "y"},
            watched={"weight"},
        )
        assert changes == []

    def test_nested_path_recorded(self):
        changes = _deep_field_changes(
            {"three_layer": {"risk_weight": 0.5}},
            {"three_layer": {"risk_weight": 0.7}},
            watched={"risk_weight"},
        )
        assert len(changes) == 1
        assert "risk_weight" in changes[0]["field"]


class TestDiffEngine:
    def test_empty_diff(self):
        engine = ConfigDiffEngine()
        same = _yaml_with_signals({"s1": {"weight": 0.5}})
        result = engine.diff(same, same)
        assert result.total_changes == 0
        assert not result.has_structural_changes

    def test_signal_added(self):
        engine = ConfigDiffEngine()
        a = _yaml_with_signals({"s1": {"weight": 0.5, "group_id": "g1"}})
        b = _yaml_with_signals({
            "s1": {"weight": 0.5, "group_id": "g1"},
            "s2": {"weight": 0.5, "group_id": "g1"},
        })
        result = engine.diff(a, b)
        assert len(result.signals_added) == 1
        assert result.signals_added[0]["signal_id"] == "s2"

    def test_signal_removed(self):
        engine = ConfigDiffEngine()
        a = _yaml_with_signals({"s1": {"weight": 0.5}, "s2": {"weight": 0.5}})
        b = _yaml_with_signals({"s1": {"weight": 0.5}})
        result = engine.diff(a, b)
        assert len(result.signals_removed) == 1
        assert result.signals_removed[0]["signal_id"] == "s2"

    def test_weight_change(self):
        engine = ConfigDiffEngine()
        a = _yaml_with_signals({"s1": {"weight": 0.5}})
        b = _yaml_with_signals({"s1": {"weight": 0.7}})
        result = engine.diff(a, b)
        assert len(result.signals_changed) == 1

    def test_invalid_yaml_handled(self):
        engine = ConfigDiffEngine()
        # Both invalid -- engine should not crash
        result = engine.diff(": : bad :: !", ": : bad :: !")
        assert result.total_changes == 0

    def test_raw_text_unified_populated(self):
        engine = ConfigDiffEngine()
        a = _yaml_with_signals({"s1": {"weight": 0.5}})
        b = _yaml_with_signals({"s1": {"weight": 0.7}})
        result = engine.diff(a, b, label_a="v1", label_b="v2")
        assert result.raw_text_unified is not None
        assert "v1" in result.raw_text_unified
        assert "v2" in result.raw_text_unified

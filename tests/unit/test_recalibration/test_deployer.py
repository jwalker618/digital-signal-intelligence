"""C-3: ProposalDeployer YAML-mutation helpers (no DB required)."""

import yaml

from infrastructure.recalibration.deployer import (
    ProposalDeployer,
    _apply_signal_weight,
    _apply_tier_changes,
    _ensure_path,
    _set_weight_in_signal,
)


class TestEnsurePath:
    def test_creates_missing_nested_dicts(self):
        d: dict = {}
        leaf = _ensure_path(d, ["a", "b", "c"])
        leaf["x"] = 1
        assert d == {"a": {"b": {"c": {"x": 1}}}}

    def test_preserves_existing_dicts(self):
        d = {"a": {"b": {"existing": True}}}
        leaf = _ensure_path(d, ["a", "b"])
        assert leaf["existing"] is True

    def test_replaces_non_dict_leaf(self):
        d = {"a": "not-a-dict"}
        leaf = _ensure_path(d, ["a", "b"])
        leaf["v"] = 2
        assert d["a"]["b"]["v"] == 2


class TestSetWeightInSignal:
    def test_flat_weight_field_updated(self):
        entry = {"id": "s1", "weight": 0.1}
        _set_weight_in_signal(entry, 0.25)
        assert entry["weight"] == 0.25

    def test_three_layer_risk_weight_updated(self):
        entry = {"id": "s1", "three_layer_assessment": {"risk_weight": 0.3}}
        _set_weight_in_signal(entry, 0.5)
        assert entry["three_layer_assessment"]["risk_weight"] == 0.5

    def test_three_layer_weight_fallback(self):
        entry = {"id": "s1", "three_layer_assessment": {"weight": 0.2}}
        _set_weight_in_signal(entry, 0.4)
        assert entry["three_layer_assessment"]["weight"] == 0.4

    def test_no_existing_weight_defaults_to_flat(self):
        entry = {"id": "s1"}
        _set_weight_in_signal(entry, 0.1)
        assert entry["weight"] == 0.1


class TestApplySignalWeight:
    def test_dict_registry(self):
        registry = {"s1": {"weight": 0.1}, "s2": {"weight": 0.2}}
        _apply_signal_weight(registry, "s1", 0.5)
        assert registry["s1"]["weight"] == 0.5
        assert registry["s2"]["weight"] == 0.2

    def test_list_registry_with_id(self):
        registry = [{"id": "s1", "weight": 0.1}, {"id": "s2", "weight": 0.2}]
        _apply_signal_weight(registry, "s2", 0.8)
        assert registry[1]["weight"] == 0.8
        assert registry[0]["weight"] == 0.1

    def test_list_registry_with_signal_id_key(self):
        registry = [{"signal_id": "s1", "weight": 0.1}]
        _apply_signal_weight(registry, "s1", 0.9)
        assert registry[0]["weight"] == 0.9

    def test_unknown_signal_noop(self):
        registry = {"s1": {"weight": 0.1}}
        _apply_signal_weight(registry, "ghost", 0.99)
        assert registry == {"s1": {"weight": 0.1}}


class TestApplyTierChanges:
    def test_bands_list_min_max_updated(self):
        section = {
            "bands": [
                {"id": 1, "interpretation": {"bands": {"min": 0, "max": 300}}},
                {"id": 2, "interpretation": {"bands": {"min": 300, "max": 700}}},
            ]
        }
        _apply_tier_changes(
            section,
            [
                {"band_id": 2, "boundary": "min", "proposed_value": 350},
                {"band_id": 2, "boundary": "max", "proposed_value": 650},
            ],
        )
        assert section["bands"][1]["interpretation"]["bands"]["min"] == 350
        assert section["bands"][1]["interpretation"]["bands"]["max"] == 650
        # Band 1 untouched
        assert section["bands"][0]["interpretation"]["bands"]["min"] == 0

    def test_invalid_boundary_ignored(self):
        section = {
            "bands": [{"id": 1, "interpretation": {"bands": {"min": 0, "max": 300}}}]
        }
        _apply_tier_changes(
            section,
            [{"band_id": 1, "boundary": "middle", "proposed_value": 150}],
        )
        assert section["bands"][0]["interpretation"]["bands"] == {"min": 0, "max": 300}

    def test_unknown_band_ignored(self):
        section = {
            "bands": [{"id": 1, "interpretation": {"bands": {"min": 0, "max": 300}}}]
        }
        _apply_tier_changes(
            section,
            [{"band_id": 42, "boundary": "min", "proposed_value": 500}],
        )
        assert section["bands"][0]["interpretation"]["bands"]["min"] == 0


class TestApplyProposalToYaml:
    SAMPLE_YAML = """
coverage:
  configuration:
    signal_registry:
      s1:
        weight: 0.10
      s2:
        weight: 0.40
    risk_tier_bands:
      bands:
        - id: 1
          interpretation:
            bands:
              min: 0
              max: 300
        - id: 2
          interpretation:
            bands:
              min: 300
              max: 700
"""

    def _deployer(self) -> ProposalDeployer:
        # ProposalDeployer.__init__ needs a Session, but the methods we
        # exercise here are pure. Create a stand-in.
        dep = ProposalDeployer.__new__(ProposalDeployer)
        dep.db = None  # type: ignore[assignment]
        dep.config_service = None  # type: ignore[assignment]
        return dep

    def test_weight_and_tier_changes_applied_end_to_end(self):
        dep = self._deployer()
        new_yaml = dep._apply_proposal_to_yaml(
            self.SAMPLE_YAML,
            weight_changes=[
                {"signal_id": "s1", "proposed_weight": 0.20},
                {"signal_id": "s2", "proposed_weight": 0.35},
            ],
            tier_threshold_changes=[
                {"band_id": 2, "boundary": "min", "proposed_value": 350},
            ],
        )
        parsed = yaml.safe_load(new_yaml)
        cfg = parsed["coverage"]["configuration"]
        assert cfg["signal_registry"]["s1"]["weight"] == 0.20
        assert cfg["signal_registry"]["s2"]["weight"] == 0.35
        bands = cfg["risk_tier_bands"]["bands"]
        band2 = next(b for b in bands if b["id"] == 2)
        assert band2["interpretation"]["bands"]["min"] == 350
        # Band 1 untouched
        band1 = next(b for b in bands if b["id"] == 1)
        assert band1["interpretation"]["bands"]["max"] == 300

    def test_malformed_change_entries_skipped(self):
        dep = self._deployer()
        new_yaml = dep._apply_proposal_to_yaml(
            self.SAMPLE_YAML,
            weight_changes=[
                {"signal_id": None, "proposed_weight": 0.99},  # skipped
                {"signal_id": "s1"},  # no proposed_weight -> skipped
            ],
            tier_threshold_changes=[],
        )
        parsed = yaml.safe_load(new_yaml)
        assert parsed["coverage"]["configuration"]["signal_registry"]["s1"]["weight"] == 0.10

    def test_empty_yaml_tolerated(self):
        dep = self._deployer()
        # Empty YAML -> we just get back a shell with the ensured path
        new_yaml = dep._apply_proposal_to_yaml(
            "",
            weight_changes=[],
            tier_threshold_changes=[],
        )
        parsed = yaml.safe_load(new_yaml)
        assert "coverage" in parsed

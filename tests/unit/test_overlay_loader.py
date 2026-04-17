"""V6/E4 — per-tenant overlay loader tests."""
from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from infrastructure.models.overlay_loader import (
    OverlayValidationError,
    _deep_merge,
    _path_allowed,
    _walk_mutations,
    apply_overlay,
    load_overlay,
)


def _base_config():
    return {
        "cyber": {
            "cyber_general": {
                "metadata": {
                    "coverage_id": "cyber_general",
                    "routing_constraints": [],
                },
                "signal_registry": [
                    {"id": "sig_a", "weight": 1.0},
                ],
                "groups": {
                    "three_layer_assessment": [
                        {"id": "network_authority", "risk": {"weight": 0.4}},
                    ],
                },
                "guardrails": {
                    "premium_ceiling": {"enabled": True},
                },
                "pricing": {"basis_damping": 0.85},
            }
        }
    }


def test_allowed_paths():
    assert _path_allowed(["groups", "three_layer_assessment"])
    assert _path_allowed(["guardrails", "max_ilf_factor"])
    assert _path_allowed(["pricing", "basis_damping"])
    assert _path_allowed(["metadata", "routing_constraints"])


def test_disallowed_paths():
    assert not _path_allowed(["signal_registry"])
    assert not _path_allowed(["metadata", "version"])
    assert not _path_allowed(["risk_tier_bands"])


def test_walk_mutations_shallow():
    muts = _walk_mutations(
        {"a": 1, "b": 2},
        {"a": 1, "b": 3, "c": 4},
    )
    assert set(muts) == {"b", "c"}


def test_walk_mutations_nested():
    muts = _walk_mutations(
        {"groups": {"three_layer_assessment": [{"id": "x"}]}},
        {"groups": {"three_layer_assessment": [{"id": "x", "risk": {"weight": 0.5}}]}},
    )
    assert any(m.startswith("groups.three_layer_assessment") for m in muts)


def test_deep_merge_overrides_only_declared_keys():
    base = {"a": {"x": 1, "y": 2}, "b": 3}
    overlay = {"a": {"y": 99}}
    merged = _deep_merge(base, overlay)
    assert merged == {"a": {"x": 1, "y": 99}, "b": 3}


def test_load_overlay_returns_none_when_absent(tmp_path: Path):
    assert load_overlay("cyber", "missing-tenant", root=tmp_path) is None


def test_apply_overlay_merges_allowed(tmp_path: Path):
    coverages = tmp_path / "coverages"
    (coverages / "cyber" / "overlays").mkdir(parents=True)
    overlay = {
        "_overlay_version": "v1",
        "cyber": {
            "cyber_general": {
                "groups": {
                    "three_layer_assessment": [
                        {"id": "network_authority", "risk": {"weight": 0.5}},
                    ],
                },
            }
        }
    }
    (coverages / "cyber" / "overlays" / "tenant-x.yaml").write_text(yaml.safe_dump(overlay))

    result = apply_overlay(
        _base_config(),
        "cyber",
        "cyber_general",
        "tenant-x",
        root=coverages,
    )
    assert result.overlay_version == "v1"
    merged = result.merged_config["cyber"]["cyber_general"]
    assert merged["groups"]["three_layer_assessment"][0]["risk"]["weight"] == 0.5
    # Untouched sections preserved.
    assert merged["signal_registry"][0]["id"] == "sig_a"


def test_apply_overlay_rejects_disallowed(tmp_path: Path):
    coverages = tmp_path / "coverages"
    (coverages / "cyber" / "overlays").mkdir(parents=True)
    overlay = {
        "cyber": {
            "cyber_general": {
                "signal_registry": [{"id": "sneaky_new_signal", "weight": 0.1}],
            }
        }
    }
    (coverages / "cyber" / "overlays" / "tenant-y.yaml").write_text(yaml.safe_dump(overlay))

    with pytest.raises(OverlayValidationError):
        apply_overlay(
            _base_config(),
            "cyber",
            "cyber_general",
            "tenant-y",
            root=coverages,
        )


def test_apply_overlay_noop_when_overlay_missing(tmp_path: Path):
    result = apply_overlay(
        _base_config(),
        "cyber",
        "cyber_general",
        "absent-tenant",
        root=tmp_path,
    )
    assert result.overlay_path is None
    assert result.overlay_version is None
    assert result.merged_config == _base_config()

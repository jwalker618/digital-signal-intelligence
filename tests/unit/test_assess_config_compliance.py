"""Tests for the V6 config-compliance gate script.

Covers: discovery, per-sub-config structural checks, baseline round-trip,
and a live smoke test against the real coverages tree.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from textwrap import dedent

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "development" / "project" / "assessments" / "scripts" / "assess_config_compliance.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("assess_config_compliance", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules["assess_config_compliance"] = module
    spec.loader.exec_module(module)
    return module


acc = _load_module()


def test_assess_sub_config_flags_missing_sections():
    findings = acc._assess_sub_config(
        "cyber_general",
        {"metadata": {}, "signal_registry": [], "groups": {}},
        scope="cyber/cyber_general",
        path="coverages/cyber/config.yaml",
    )
    msgs = {f.message for f in findings if f.severity == "error"}
    assert any("missing required section 'guardrails'" in m for m in msgs)
    assert any("missing required section 'pricing'" in m for m in msgs)


def test_assess_sub_config_flags_empty_three_layer_assessment():
    findings = acc._assess_sub_config(
        "cyber_general",
        {
            "metadata": {},
            "signal_registry": [],
            "groups": {"three_layer_assessment": []},
            "risk_tier_bands": {},
            "loss_tier_bands": {},
            "exposure": {},
            "pricing": {},
            "limit_configuration": {},
            "guardrails": {},
        },
        scope="cyber/cyber_general",
        path="coverages/cyber/config.yaml",
    )
    msgs = {f.message for f in findings if f.severity == "error"}
    assert any("three_layer_assessment" in m for m in msgs)


def test_assess_sub_config_warns_on_non_canonical_category():
    findings = acc._assess_sub_config(
        "cyber_general",
        {
            "metadata": {},
            "signal_registry": [],
            "groups": {
                "three_layer_assessment": [
                    {"id": "custom_nonstandard_category"},
                    {"id": "network_authority"},
                ],
            },
            "risk_tier_bands": {},
            "loss_tier_bands": {},
            "exposure": {},
            "pricing": {},
            "limit_configuration": {},
            "guardrails": {},
        },
        scope="cyber/cyber_general",
        path="coverages/cyber/config.yaml",
    )
    non_canonical = [f for f in findings if f.category == "canonical_category"]
    # Only the non-canonical id should produce a warning.
    assert len(non_canonical) == 1
    assert non_canonical[0].severity == "warning"
    assert "custom_nonstandard_category" in non_canonical[0].message


def test_baseline_round_trip(tmp_path: Path):
    # Build a report with one known error finding.
    rep = acc.Report()
    cfg = acc.ConfigReport(file="coverages/fake/config.yaml", coverage_id="fake")
    cfg.findings.append(acc.Finding(
        severity="error",
        category="structure",
        path="coverages/fake/config.yaml",
        scope="fake/fake_general",
        message="missing required section 'guardrails'",
    ))
    rep.configs.append(cfg)

    baseline = tmp_path / "baseline.json"
    acc.write_baseline(baseline, rep)
    assert baseline.exists()
    data = json.loads(baseline.read_text())
    assert len(data["findings"]) == 1

    keys = acc.load_baseline(baseline)
    assert cfg.findings[0].key() in keys

    acc.apply_baseline(rep, keys)
    assert cfg.findings[0].baselined is True
    assert cfg.unbaselined_error_count == 0
    assert rep.passed is True


def test_new_finding_not_in_baseline_is_unbaselined(tmp_path: Path):
    rep = acc.Report()
    cfg = acc.ConfigReport(file="coverages/fake/config.yaml", coverage_id="fake")
    cfg.findings.append(acc.Finding(
        severity="error",
        category="structure",
        path="coverages/fake/config.yaml",
        scope="fake/fake_general",
        message="brand new regression",
    ))
    rep.configs.append(cfg)

    baseline = tmp_path / "baseline.json"
    baseline.write_text(json.dumps({"findings": []}))
    acc.apply_baseline(rep, acc.load_baseline(baseline))

    assert cfg.unbaselined_error_count == 1
    assert rep.passed is False


def test_discover_configs_picks_up_all(tmp_path: Path):
    root = tmp_path / "coverages"
    (root / "a").mkdir(parents=True)
    (root / "b").mkdir(parents=True)
    (root / "a" / "config.yaml").write_text("x: 1\n")
    (root / "b" / "config.yaml").write_text("x: 1\n")
    (root / "c").mkdir()
    (root / "c" / "README.md").write_text("no config here")

    discovered = acc.discover_configs(root)
    names = [p.parent.name for p in discovered]
    assert names == ["a", "b"]


def test_production_coverages_pass_with_baseline(capsys):
    """Live smoke test — real repo must pass with its committed baseline."""
    exit_code = acc.main([
        "--coverages-root", str(REPO_ROOT / "coverages"),
    ])
    assert exit_code == 0

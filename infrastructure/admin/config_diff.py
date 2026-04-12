"""
B-2c: ConfigDiffEngine

Structured diff between two YAML config versions. Focuses on fields that
actuarial/product teams care about reviewing before deployment:

- Signal weight changes (with old vs new)
- Signal additions / removals
- Tier threshold changes
- Score-condition changes
- Group weight changes

Raw-text diff is also available as a fallback. The structured output
drives the governance UI's diff viewer.
"""

from __future__ import annotations

import difflib
import logging
from dataclasses import dataclass, field
from typing import Any, Optional

import yaml

logger = logging.getLogger("dsi.admin.config_diff")


@dataclass
class ConfigDiff:
    """Structured diff between two coverage config YAMLs."""

    version_a_label: str
    version_b_label: str

    # Additions: signal_id / group_id / tier_id / condition key
    signals_added: list[dict] = field(default_factory=list)
    signals_removed: list[dict] = field(default_factory=list)
    signals_changed: list[dict] = field(default_factory=list)   # weight / expectation / proxy_tier deltas

    groups_changed: list[dict] = field(default_factory=list)    # group weight deltas
    tiers_changed: list[dict] = field(default_factory=list)     # tier threshold deltas
    score_conditions_changed: list[dict] = field(default_factory=list)

    # Meta + fallback
    metadata_changes: list[dict] = field(default_factory=list)
    has_structural_changes: bool = False
    raw_text_unified: Optional[str] = None

    @property
    def total_changes(self) -> int:
        return (
            len(self.signals_added)
            + len(self.signals_removed)
            + len(self.signals_changed)
            + len(self.groups_changed)
            + len(self.tiers_changed)
            + len(self.score_conditions_changed)
            + len(self.metadata_changes)
        )


class ConfigDiffEngine:
    """Computes a structured diff between two coverage config YAMLs."""

    def diff(
        self,
        yaml_a: str,
        yaml_b: str,
        label_a: str = "current",
        label_b: str = "proposed",
    ) -> ConfigDiff:
        """Return a ConfigDiff describing yaml_b - yaml_a."""
        try:
            a = yaml.safe_load(yaml_a) or {}
        except yaml.YAMLError as exc:
            logger.warning("Failed to parse yaml_a: %s", exc)
            a = {}
        try:
            b = yaml.safe_load(yaml_b) or {}
        except yaml.YAMLError as exc:
            logger.warning("Failed to parse yaml_b: %s", exc)
            b = {}

        result = ConfigDiff(version_a_label=label_a, version_b_label=label_b)

        # Descend into the coverage/configuration namespace where
        # structured fields typically live. Both schemas start with
        # coverage.configuration.{signal_registry, groups, risk_tier_bands, ...}
        a_cfg = _deep_get(a, "coverage", "configuration") or a
        b_cfg = _deep_get(b, "coverage", "configuration") or b

        # Signal registry
        a_sigs = _normalise_signal_registry(a_cfg.get("signal_registry"))
        b_sigs = _normalise_signal_registry(b_cfg.get("signal_registry"))
        self._diff_signals(a_sigs, b_sigs, result)

        # Groups
        a_groups = _normalise_groups(a_cfg.get("groups"))
        b_groups = _normalise_groups(b_cfg.get("groups"))
        self._diff_groups(a_groups, b_groups, result)

        # Risk tier bands
        a_tiers = _normalise_tiers(a_cfg.get("risk_tier_bands"))
        b_tiers = _normalise_tiers(b_cfg.get("risk_tier_bands"))
        self._diff_tiers(a_tiers, b_tiers, result)

        # Score conditions (if signals carry conditions)
        self._diff_score_conditions(a_sigs, b_sigs, result)

        # Metadata changes (name, version, min_premium etc)
        a_meta = (a_cfg.get("metadata") or {}) if isinstance(a_cfg.get("metadata"), dict) else {}
        b_meta = (b_cfg.get("metadata") or {}) if isinstance(b_cfg.get("metadata"), dict) else {}
        for key in set(list(a_meta.keys()) + list(b_meta.keys())):
            if a_meta.get(key) != b_meta.get(key):
                result.metadata_changes.append({
                    "field": key,
                    "old": a_meta.get(key),
                    "new": b_meta.get(key),
                })

        result.has_structural_changes = result.total_changes > 0

        # Raw unified diff as fallback
        result.raw_text_unified = "".join(difflib.unified_diff(
            yaml_a.splitlines(keepends=True),
            yaml_b.splitlines(keepends=True),
            fromfile=label_a,
            tofile=label_b,
            lineterm="",
        ))

        return result

    # ------------------------------------------------------------------
    # Per-section diffs
    # ------------------------------------------------------------------

    def _diff_signals(
        self,
        a: dict[str, dict],
        b: dict[str, dict],
        result: ConfigDiff,
    ) -> None:
        for sig_id in b.keys() - a.keys():
            result.signals_added.append({
                "signal_id": sig_id,
                "weight": _get_signal_weight(b[sig_id]),
                "group": _get_signal_group(b[sig_id]),
            })
        for sig_id in a.keys() - b.keys():
            result.signals_removed.append({
                "signal_id": sig_id,
                "weight": _get_signal_weight(a[sig_id]),
                "group": _get_signal_group(a[sig_id]),
            })
        for sig_id in a.keys() & b.keys():
            changes = self._signal_field_changes(a[sig_id], b[sig_id])
            if changes:
                result.signals_changed.append({
                    "signal_id": sig_id,
                    "changes": changes,
                })

    @staticmethod
    def _signal_field_changes(a: dict, b: dict) -> list[dict]:
        """Compare key fields between two signal definitions."""
        watched = {
            "risk_weight", "loss_frequency_weight", "exposure_size_weight",
            "weight", "proxy_tier", "expectation_level",
        }
        # Signals often nest weights inside three_layer_assessment -- walk both
        return _deep_field_changes(a, b, watched)

    def _diff_groups(
        self,
        a: dict[str, dict],
        b: dict[str, dict],
        result: ConfigDiff,
    ) -> None:
        for gid in a.keys() | b.keys():
            a_g = a.get(gid, {})
            b_g = b.get(gid, {})
            if a_g == b_g:
                continue
            changes = _deep_field_changes(a_g, b_g, {"risk_weight", "loss_weight", "exposure_weight", "weight"})
            if changes:
                result.groups_changed.append({
                    "group_id": gid,
                    "changes": changes,
                })

    def _diff_tiers(
        self,
        a: list[dict],
        b: list[dict],
        result: ConfigDiff,
    ) -> None:
        a_by_id = {t.get("id"): t for t in a}
        b_by_id = {t.get("id"): t for t in b}
        for tid in a_by_id.keys() | b_by_id.keys():
            ta = a_by_id.get(tid, {})
            tb = b_by_id.get(tid, {})
            if ta == tb:
                continue
            changes = _deep_field_changes(
                ta, tb, {"min", "max", "label", "action", "value", "applied"}
            )
            if changes:
                result.tiers_changed.append({"tier_id": tid, "changes": changes})

    def _diff_score_conditions(
        self,
        a_sigs: dict[str, dict],
        b_sigs: dict[str, dict],
        result: ConfigDiff,
    ) -> None:
        for sig_id in a_sigs.keys() & b_sigs.keys():
            a_conds = (a_sigs[sig_id] or {}).get("score_conditions")
            b_conds = (b_sigs[sig_id] or {}).get("score_conditions")
            if a_conds != b_conds:
                result.score_conditions_changed.append({
                    "signal_id": sig_id,
                    "old": a_conds,
                    "new": b_conds,
                })


# ==========================================================================
# Normalisation helpers (tolerate both dict and list forms)
# ==========================================================================


def _deep_get(d: dict, *keys) -> Any:
    """Walk keys into nested dicts; return None if any step is missing."""
    cur = d
    for k in keys:
        if not isinstance(cur, dict):
            return None
        cur = cur.get(k)
    return cur


def _normalise_signal_registry(value) -> dict[str, dict]:
    """signal_registry may be dict or list in different YAML styles."""
    if value is None:
        return {}
    if isinstance(value, dict):
        return value
    if isinstance(value, list):
        out: dict = {}
        for item in value:
            if not isinstance(item, dict):
                continue
            sig_id = item.get("id") or item.get("signal_id") or item.get("code")
            if sig_id:
                out[str(sig_id)] = item
        return out
    return {}


def _normalise_groups(value) -> dict[str, dict]:
    if value is None:
        return {}
    # Groups often looks like {three_layer_assessment: [...], categories: {...}}.
    # We pull the three_layer_assessment list as the primary source.
    if isinstance(value, dict) and "three_layer_assessment" in value:
        tla = value["three_layer_assessment"]
        if isinstance(tla, list):
            return {g.get("id"): g for g in tla if isinstance(g, dict) and g.get("id")}
        if isinstance(tla, dict):
            return tla
    if isinstance(value, dict):
        return value
    if isinstance(value, list):
        return {g.get("id"): g for g in value if isinstance(g, dict) and g.get("id")}
    return {}


def _normalise_tiers(value) -> list[dict]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, dict) and "bands" in value:
        bands = value["bands"]
        return bands if isinstance(bands, list) else []
    return []


def _get_signal_weight(signal: dict) -> Any:
    """Pull a representative weight from a signal definition."""
    if not isinstance(signal, dict):
        return None
    if "weight" in signal:
        return signal["weight"]
    tla = signal.get("three_layer_assessment") or signal.get("three_layer")
    if isinstance(tla, dict):
        return tla.get("risk_weight") or tla.get("weight")
    return None


def _get_signal_group(signal: dict) -> Any:
    if not isinstance(signal, dict):
        return None
    if "group_id" in signal:
        return signal["group_id"]
    tla = signal.get("three_layer_assessment") or signal.get("three_layer")
    if isinstance(tla, dict):
        return tla.get("group_id")
    return None


def _deep_field_changes(a: Any, b: Any, watched: set[str]) -> list[dict]:
    """Walk two structures in parallel, returning a flat list of
    {field, old, new} records for any watched field that differs."""
    changes: list[dict] = []

    def _walk(path: str, a_val: Any, b_val: Any):
        if isinstance(a_val, dict) or isinstance(b_val, dict):
            a_dict = a_val if isinstance(a_val, dict) else {}
            b_dict = b_val if isinstance(b_val, dict) else {}
            for key in set(list(a_dict.keys()) + list(b_dict.keys())):
                _walk(f"{path}.{key}" if path else key, a_dict.get(key), b_dict.get(key))
            return

        # Scalar / list comparison
        if a_val == b_val:
            return

        # If the leaf key is in the watched set, emit
        leaf = path.split(".")[-1]
        if leaf in watched:
            changes.append({"field": path, "old": a_val, "new": b_val})

    _walk("", a, b)
    return changes

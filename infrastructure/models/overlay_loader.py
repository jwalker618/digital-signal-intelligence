"""V6/E4 — per-tenant config overlay loader.

Overlays live at ``coverages/{name}/overlays/{tenant_id}.yaml`` and
deep-merge into the base config at load time. Enforcement: overlays
may only adjust weights, modifiers, guardrails, ILF-curve parameters,
and ``routing_constraints`` — they cannot change the signal-registry
structure (signal IDs, groupings, inference function references).

Consumers:
- ``infrastructure.models.compiler.get_config(coverage_id, config_id,
  tenant_id=...)`` merges the overlay before returning the
  CoverageConfig.
- The overlay version is recorded in the audit table for every quote.
"""
from __future__ import annotations

import copy
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

log = logging.getLogger("dsi.overlay")

REPO_ROOT = Path(__file__).resolve().parents[2]


ALLOWED_MUTATIONS = {
    # (section_path...) that an overlay may modify.
    ("groups",),                         # weights + modifiers per group
    ("guardrails",),
    ("pricing",),                        # ILF params, damping
    ("metadata", "routing_constraints"),
}


class OverlayValidationError(ValueError):
    pass


@dataclass(frozen=True)
class OverlayResult:
    tenant_id: str
    coverage_id: str
    config_id: str
    overlay_path: Optional[Path]
    overlay_version: Optional[str]
    merged_config: Dict[str, Any]


def _path_allowed(path: List[str]) -> bool:
    """True if the modified key path begins with an allowed prefix."""
    for prefix in ALLOWED_MUTATIONS:
        if len(path) >= len(prefix) and tuple(path[: len(prefix)]) == prefix:
            return True
    return False


def _walk_mutations(
    base: Any,
    overlay: Any,
    *,
    path: Optional[List[str]] = None,
) -> List[str]:
    """Return list of `dotted.paths` where ``overlay`` differs from ``base``."""
    path = path or []
    if isinstance(overlay, dict):
        mutations: List[str] = []
        for key, val in overlay.items():
            sub_path = path + [str(key)]
            if isinstance(base, dict) and key in base:
                mutations.extend(_walk_mutations(base[key], val, path=sub_path))
            else:
                mutations.append(".".join(sub_path))
        return mutations
    if base != overlay:
        return [".".join(path)]
    return []


def _deep_merge(base: Dict[str, Any], overlay: Dict[str, Any]) -> Dict[str, Any]:
    """Return a deep-merged copy of ``base`` with ``overlay`` values applied."""
    out = copy.deepcopy(base)
    for key, val in overlay.items():
        if (
            key in out
            and isinstance(out[key], dict)
            and isinstance(val, dict)
        ):
            out[key] = _deep_merge(out[key], val)
        else:
            out[key] = copy.deepcopy(val)
    return out


def load_overlay(
    coverage_id: str,
    tenant_id: str,
    *,
    root: Optional[Path] = None,
) -> Optional[Dict[str, Any]]:
    """Load the raw overlay YAML for ``tenant_id``; None when absent."""
    root = root or (REPO_ROOT / "coverages")
    path = root / coverage_id / "overlays" / f"{tenant_id}.yaml"
    if not path.exists():
        return None
    return yaml.safe_load(path.read_text())


def apply_overlay(
    base_config: Dict[str, Any],
    coverage_id: str,
    config_id: str,
    tenant_id: str,
    *,
    root: Optional[Path] = None,
) -> OverlayResult:
    """Merge the tenant overlay (if present) into ``base_config``.

    The input ``base_config`` is the v2.0 layout
    ``{coverage_id: {config_id: {...sections...}}}``. The overlay
    YAML mirrors that shape but contains only the fields to override.

    Raises:
        OverlayValidationError — if the overlay tries to modify a
            section outside ``ALLOWED_MUTATIONS``.
    """
    overlay = load_overlay(coverage_id, tenant_id, root=root)
    if overlay is None:
        return OverlayResult(
            tenant_id=tenant_id,
            coverage_id=coverage_id,
            config_id=config_id,
            overlay_path=None,
            overlay_version=None,
            merged_config=base_config,
        )

    # Pull the inner block for both base + overlay.
    base_inner = (base_config.get(coverage_id) or {}).get(config_id)
    if base_inner is None:
        raise OverlayValidationError(
            f"base config missing {coverage_id}/{config_id}"
        )
    overlay_inner = (overlay.get(coverage_id) or {}).get(config_id) or {}
    overlay_version = overlay.get("_overlay_version")

    mutations = _walk_mutations(base_inner, overlay_inner)
    violations = [
        m for m in mutations
        if not _path_allowed(m.split("."))
    ]
    if violations:
        raise OverlayValidationError(
            f"overlay {coverage_id}/{tenant_id} touches disallowed sections: "
            f"{violations}"
        )

    merged_inner = _deep_merge(base_inner, overlay_inner)
    merged = copy.deepcopy(base_config)
    merged[coverage_id][config_id] = merged_inner

    return OverlayResult(
        tenant_id=tenant_id,
        coverage_id=coverage_id,
        config_id=config_id,
        overlay_path=((root or (REPO_ROOT / "coverages"))
                      / coverage_id / "overlays" / f"{tenant_id}.yaml"),
        overlay_version=overlay_version,
        merged_config=merged,
    )

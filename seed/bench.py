"""seed.bench — thin wrapper around the V5-era seed_dsi_bench script.

C4-interim (Q1): the legacy script is still the source of truth. This
module imports it and re-exports its ``main`` / ``seed_database`` entry
points so ``python -m seed bench`` works end-to-end. C4-final (Q4) will
move the logic here and delete the root-level script.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

LEGACY_SCRIPT = Path(__file__).resolve().parents[1] / "seed_dsi_bench.py"


def _load_legacy():
    if not LEGACY_SCRIPT.exists():
        raise FileNotFoundError(
            f"legacy seed script missing: {LEGACY_SCRIPT}. "
            "The repository is likely in a broken C4-final state with neither "
            "the new nor the old seed path available."
        )
    spec = importlib.util.spec_from_file_location("_seed_dsi_bench_legacy", LEGACY_SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules["_seed_dsi_bench_legacy"] = module
    spec.loader.exec_module(module)
    return module


def run() -> int:
    """Execute the bench seed. Returns 0 on success."""
    mod = _load_legacy()
    main = getattr(mod, "main", None) or getattr(mod, "seed_database", None)
    if main is None:
        raise RuntimeError(
            "legacy seed_dsi_bench.py exposes neither main() nor seed_database()"
        )
    result = main()
    return int(result or 0)

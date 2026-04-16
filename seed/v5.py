"""seed.v5 — thin wrapper around the V5 companion seed script.

See seed/bench.py docstring for the C4-interim vs C4-final contract.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

LEGACY_SCRIPT = Path(__file__).resolve().parents[1] / "seed_v5.py"


def _load_legacy():
    if not LEGACY_SCRIPT.exists():
        raise FileNotFoundError(f"legacy seed_v5 script missing: {LEGACY_SCRIPT}")
    spec = importlib.util.spec_from_file_location("_seed_v5_legacy", LEGACY_SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules["_seed_v5_legacy"] = module
    spec.loader.exec_module(module)
    return module


def run() -> int:
    mod = _load_legacy()
    main = getattr(mod, "main", None) or getattr(mod, "seed_v5", None)
    if main is None:
        raise RuntimeError("legacy seed_v5.py exposes neither main() nor seed_v5()")
    return int(main() or 0)

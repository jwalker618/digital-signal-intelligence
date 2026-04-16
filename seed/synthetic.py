"""seed.synthetic — thin wrapper around synthetic_generator.py.

See seed/bench.py docstring for the C4-interim vs C4-final contract.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Optional

LEGACY_SCRIPT = Path(__file__).resolve().parents[1] / "synthetic_generator.py"


def _load_legacy():
    if not LEGACY_SCRIPT.exists():
        raise FileNotFoundError(f"legacy synthetic_generator missing: {LEGACY_SCRIPT}")
    spec = importlib.util.spec_from_file_location("_synthetic_generator_legacy", LEGACY_SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules["_synthetic_generator_legacy"] = module
    spec.loader.exec_module(module)
    return module


def run(coverage: Optional[str] = None, n: int = 1000) -> int:
    mod = _load_legacy()
    # Prefer main(coverage, n); fall back to main() if signature differs.
    main = getattr(mod, "main", None)
    if main is None:
        raise RuntimeError("legacy synthetic_generator.py exposes no main()")
    try:
        return int(main(coverage=coverage, n=n) or 0)
    except TypeError:
        # Older signature: main() with no kwargs
        return int(main() or 0)

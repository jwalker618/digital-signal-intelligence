"""V6/E10 — CI guard: block non-test modules from importing stub extractors.

Part of the stub-retirement workstream. Runs in the Config Health Gate
CI job. Scans the tree for any Python module that imports from either:
- ``signal_architecture.signals.extractors.stubs`` (current location)
- ``tests.fixtures.stub_extractors`` (post-move location)

from OUTSIDE the ``tests/`` tree. Any hit fails CI.

Usage::

    python development/project/assessments/scripts/check_no_stub_imports.py
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path
from typing import List, Optional, Sequence, Tuple

REPO_ROOT = Path(__file__).resolve().parents[4]

STUB_IMPORT_PATTERNS = (
    re.compile(r"\bfrom\s+signal_architecture\.signals\.extractors\.stubs\b"),
    re.compile(r"\bimport\s+signal_architecture\.signals\.extractors\.stubs\b"),
    re.compile(r"\bfrom\s+tests\.fixtures\.stub_extractors\b"),
    re.compile(r"\bimport\s+tests\.fixtures\.stub_extractors\b"),
)

# Directories that may legitimately import stubs (tests + seed scripts +
# the stubs package itself).
ALLOWED_PREFIXES = (
    "tests/",
    "seed/",                # seed script re-uses stubs intentionally
    "seed_dsi_bench.py",    # legacy; retires with C4-final
    "synthetic_generator.py",  # legacy; retires with C4-final
    "signal_architecture/signals/extractors/stubs/",
    "signal_architecture/signals/extractors/resolver.py",  # resolver itself
    "development/project/",  # docs/specs
    # Pre-V6 inference-function <-> stub imports. Each coverage's A1-A8
    # maturation PR migrates its phase_N_signals.py to production
    # extractors via the D1-D8 factories. These entries are removed as
    # those migrations complete — the guard fails if any NEW inference
    # module imports from stubs.
    "signal_architecture/signals/inference/functions/aerospace/phase_5_signals.py",
    "signal_architecture/signals/inference/functions/casualty/phase_4_signals.py",
    "signal_architecture/signals/inference/functions/cyber/phase_7_signals.py",
    "signal_architecture/signals/inference/functions/do/phase_6_signals.py",
    "signal_architecture/signals/inference/functions/energy/",  # all phase files
    "signal_architecture/signals/inference/functions/fi/phase_7_signals.py",
    "signal_architecture/signals/inference/functions/fpr/phase_8_signals.py",
    "signal_architecture/signals/inference/functions/marine/phase_3_signals.py",
    "signal_architecture/signals/inference/functions/pi/phase_6_signals.py",
    "signal_architecture/signals/inference/functions/property/phase_2_signals.py",
)

SCAN_EXTENSIONS = {".py"}


def is_allowed(rel_path: str) -> bool:
    return any(rel_path.startswith(prefix) for prefix in ALLOWED_PREFIXES)


def scan(root: Path) -> List[Tuple[str, int, str]]:
    hits: List[Tuple[str, int, str]] = []
    for dirpath, dirnames, filenames in os.walk(root):
        # Skip hidden + build dirs.
        dirnames[:] = [
            d for d in dirnames
            if not d.startswith(".") and d not in ("__pycache__", "node_modules", "build", "dist")
        ]
        for fname in filenames:
            if not any(fname.endswith(ext) for ext in SCAN_EXTENSIONS):
                continue
            path = Path(dirpath) / fname
            rel = path.relative_to(root).as_posix()
            if is_allowed(rel):
                continue
            try:
                text = path.read_text()
            except (OSError, UnicodeDecodeError):
                continue
            for lineno, line in enumerate(text.splitlines(), start=1):
                if not ("stub" in line and "import" in line):
                    continue
                for pat in STUB_IMPORT_PATTERNS:
                    if pat.search(line):
                        hits.append((rel, lineno, line.strip()))
                        break
    return hits


def main(argv: Optional[Sequence[str]] = None) -> int:
    p = argparse.ArgumentParser(prog="check_no_stub_imports")
    p.add_argument("--root", default=str(REPO_ROOT))
    args = p.parse_args(argv)

    hits = scan(Path(args.root))
    if not hits:
        print("stub-import guard: PASS (no non-test module imports stubs).")
        return 0

    print("stub-import guard: FAIL", file=sys.stderr)
    for path, line, src in hits:
        print(f"  {path}:{line}: {src}", file=sys.stderr)
    print(
        "\nStubs are test fixtures only. Move the import into the tests/ tree,"
        " or mark the file with an allow-listed prefix in check_no_stub_imports.py.",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())

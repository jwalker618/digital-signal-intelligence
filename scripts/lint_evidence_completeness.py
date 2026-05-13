"""V7 Phase 2 — static check: every SignalResult construction in production
paths supplies evidence_grade, or is an error-only / skipped-only construction.

Run: ``python scripts/lint_evidence_completeness.py``.
CI exit code: 0 ok, 1 violations found.

Scope: signal_architecture/signals/{extractors,inference,aggregators,routing}.
Skips: tests/, **/__pycache__, error-only and skipped-only constructions.

Rationale: Phase 2 makes ``evidence_grade`` a contract for every produced
SignalResult. A static check is the cheapest enforcement — keeps the gate
visible at PR time without needing the full pipeline to run.
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

ROOTS = [
    Path("signal_architecture/signals/extractors"),
    Path("signal_architecture/signals/inference/functions"),
    Path("signal_architecture/signals/aggregators"),
    Path("signal_architecture/signals/routing"),
]

# Allowlist for genuine edge cases. Keep this short; prefer adding a real
# evidence_grade over allowlisting. Path values must be relative to repo root.
ALLOWLIST: set[str] = set()


def has_evidence_kw(call: ast.Call) -> bool:
    """Return True if the call satisfies the evidence-completeness contract."""
    keywords = {kw.arg for kw in call.keywords if kw.arg}
    if "evidence_grade" in keywords:
        return True
    # Error-only constructions: permitted without grade. Recognised by having
    # `error=...` and *neither* score nor category in the kwargs.
    if "error" in keywords and "score" not in keywords and "category" not in keywords:
        return True
    # Skipped constructions: permitted only when `skipped=True` is a literal.
    if "skipped" in keywords:
        for kw in call.keywords:
            if kw.arg == "skipped" and isinstance(kw.value, ast.Constant) and kw.value.value is True:
                return True
    return False


def is_signal_result_call(call: ast.Call) -> bool:
    f = call.func
    if isinstance(f, ast.Name) and f.id == "SignalResult":
        return True
    if isinstance(f, ast.Attribute) and f.attr == "SignalResult":
        return True
    return False


def violations_in(path: Path) -> list[tuple[int, str]]:
    if str(path) in ALLOWLIST:
        return []
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except SyntaxError as e:
        return [(e.lineno or 0, f"parse error: {e}")]
    out: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and is_signal_result_call(node):
            if not has_evidence_kw(node):
                out.append((node.lineno, "missing evidence_grade kwarg"))
    return out


def main() -> int:
    total = 0
    for root in ROOTS:
        if not root.exists():
            continue
        for path in sorted(root.rglob("*.py")):
            if "__pycache__" in path.parts:
                continue
            for lineno, msg in violations_in(path):
                print(f"{path}:{lineno}: {msg}")
                total += 1
    if total:
        print(f"\n{total} violation(s)")
        return 1
    print("evidence-completeness lint: clean")
    return 0


if __name__ == "__main__":
    sys.exit(main())

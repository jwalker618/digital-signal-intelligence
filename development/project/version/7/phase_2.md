# V7 Phase 2: Extractor Migration

## Depends on
- Phase 1 complete. `EvidenceGrade`, `EvidenceSource`, `bump_evidence`, `BaseExtractor.MAX_EVIDENCE_GRADE` present.

## Blocks
- Phase 3 (aggregator promotion-merge needs every contributing signal to carry a grade).
- Phase 6 (validator cannot tighten `evidence_grade` to required until every producer sets it).

## Scope

Touch every `SignalResult(...)` construction site in the codebase (60 in `signal_architecture/`, 62 total non-test) and every extractor in `signal_architecture/signals/extractors/` (71 files). Each construction site gains `evidence_grade=`, `evidence_basis=`, `evidence_sources=`. Each extractor class declares its `MAX_EVIDENCE_GRADE`. Stub extractors universally declare themselves with `evidence_grade="inferred"` and `evidence_basis="Stub extractor: deterministic synthetic value"`.

Migration is batched by coverage to keep PRs reviewable. CI enforces "every extractor file imports `EvidenceGrade`" and "every `SignalResult(` construction in production paths has `evidence_grade=` in its kwargs" via a static check (added in this phase). Phase 1's `_EVIDENCE_ENFORCEMENT_MODE` flips from `"warn"` to `"raise"` at the end.

## Decisions (locked)

| # | Decision | Choice |
|---|----------|--------|
| D1 | Migration order | (1) Stubs first, (2) production web/HTTP, (3) production multi-source, (4) production register/feed, (5) routed signals last |
| D2 | Default grade mapping | Stub → `inferred`; single HTTP → `observed`; multi-source agreement → `corroborated`; register/feed → `structured_attested`; ≥2 captures across ≥30d → `behaviourally_validated` |
| D3 | `evidence_basis` style | Terse, ≤500 chars. Format: `"<kind> from <source_id>; <why-this-grade>"`. URLs go in `evidence_sources`, not basis. |
| D4 | Enforcement | End-of-phase: `BaseExtractor._EVIDENCE_ENFORCEMENT_MODE = "raise"`. Subclasses that need warn-mode declare it explicitly. |
| D5 | Static check | New script `scripts/lint_evidence_completeness.py` runs in CI; greps for `SignalResult(` constructions missing `evidence_grade=`. Configurable allowlist for known exceptions. |
| D6 | Error path | Existing code that returns `SignalResult(error=...)` retains `evidence_grade=None` permitted — error results don't carry evidence. Static check skips error-only constructions. |
| D7 | Skipped path | `SignalResult(skipped=True)` also permitted without grade. Static check skips. |
| D8 | Routed signals | The router in `signal_architecture/signals/routing/router.py` synthesises a `SignalResult` from sub-signals. It takes the min-grade across its routed contributions via `bump_evidence` chained from `None`. |

## Files

### Create
- `scripts/lint_evidence_completeness.py` — static check
- `tests/unit/test_evidence_completeness_lint.py` — meta-test of the linter
- One test file per migrated coverage batch (extend existing `tests/unit/test_<coverage>.py` files; no new test files unless absent)

### Modify (in this order)

**Batch A — stubs** (~25 files):
- All extractors with class name containing `Stub` or inheriting `StubExtractor`. Find via:
  ```bash
  grep -rln "StubExtractor\|class.*Stub.*Extractor" signal_architecture/signals/extractors/
  ```
- All inference functions returning synthetic values. Find via:
  ```bash
  grep -rln "SignalResult(" signal_architecture/signals/inference/functions/ | xargs grep -l "stub\|synthetic\|profile"
  ```

**Batch B — production web/HTTP** (~10 files):
- `signal_architecture/signals/extractors/production/web.py`
- `signal_architecture/signals/extractors/production/sentiment.py`
- `signal_architecture/signals/extractors/production/hiring.py`
- `signal_architecture/signals/extractors/production/stack.py`
- Set `MAX_EVIDENCE_GRADE = "observed"`.

**Batch C — production multi-source** (~5 files):
- `signal_architecture/signals/extractors/production/litigation.py`
- `signal_architecture/signals/extractors/production/sector.py`
- Set `MAX_EVIDENCE_GRADE = "corroborated"` where the extractor aggregates ≥2 independent feeds.

**Batch D — production register/feed** (~10 files):
- `signal_architecture/signals/extractors/production/climate.py` (NOAA, FEMA, ENERGY STAR)
- Any extractor pulling from a structured register (SEC, Companies House, S&P, classification societies)
- Set `MAX_EVIDENCE_GRADE = "structured_attested"`.

**Batch E — routed signals** (last):
- `signal_architecture/signals/inference/functions/routed/signals.py`
- `signal_architecture/signals/routing/router.py`
- The router computes the grade of a routed `SignalResult` as the max grade among its contributing sub-results (via repeated `bump_evidence`).

### Flip the enforcement default
- `signal_architecture/signals/base.py`: change `_EVIDENCE_ENFORCEMENT_MODE` default from `"warn"` to `"raise"` at the very end of this phase (after every extractor is migrated).

## Construction-site mechanics

### Pattern: stub extractor
Before:
```python
return SignalResult(signal_id="alliance_membership", score=70.0, confidence=0.6)
```
After:
```python
return SignalResult(
    signal_id="alliance_membership",
    score=70.0,
    confidence=0.6,
    evidence_grade="inferred",
    evidence_basis="Stub extractor: deterministic synthetic value",
    evidence_sources=[],
)
```

### Pattern: single HTTP fetch (`observed`)
```python
src = EvidenceSource(
    source_id="entity_website",
    kind="scrape",
    ref=f"https://{context.discovered_domain}/security.txt",
    fetched_at=utcnow(),
    response_hash=compute_response_hash(body),
)
return SignalResult(
    signal_id="security_headers",
    score=score,
    confidence=confidence,
    evidence_grade="observed",
    evidence_basis=f"Single HTTP fetch from {src.ref}",
    evidence_sources=[src],
)
```

### Pattern: multi-source agreement (`corroborated`)
```python
sources = [es_courtlistener, es_pacer]
agreed = courtlistener_count == pacer_count
return SignalResult(
    signal_id="director_litigation_history",
    score=score,
    confidence=confidence,
    evidence_grade="corroborated" if agreed else "observed",
    evidence_basis=(
        f"Multi-source agreement on case count={courtlistener_count}"
        if agreed
        else f"CourtListener={courtlistener_count} disagrees with PACER={pacer_count}; took max"
    ),
    evidence_sources=sources,
)
```

### Pattern: structured register (`structured_attested`)
```python
src = EvidenceSource(
    source_id="sec_edgar",
    kind="register",
    ref=f"https://data.sec.gov/submissions/CIK{cik}.json",
    fetched_at=utcnow(),
    response_hash=compute_response_hash(body),
)
return SignalResult(
    signal_id="sec_filing_recency",
    score=score,
    confidence=confidence,
    evidence_grade="structured_attested",
    evidence_basis="SEC EDGAR submissions feed (authoritative register)",
    evidence_sources=[src],
)
```

### Pattern: behaviourally validated (`behaviourally_validated`)
Requires ≥2 captures separated by ≥30 days. Phase 8 introduces a stability-verifier that drives this; for Phase 2 only extractors that already pull historical time-series qualify.
```python
captures = fetch_cert_rotation_history(entity_id)  # returns list of (date, cert)
if len(captures) >= 2 and (captures[-1][0] - captures[0][0]).days >= 30:
    grade = "behaviourally_validated"
    basis = f"Cert rotation observed across {len(captures)} captures spanning {(captures[-1][0]-captures[0][0]).days}d"
else:
    grade = "observed"
    basis = "Insufficient history for behavioural validation"
return SignalResult(
    signal_id="cert_rotation_cadence",
    score=...,
    confidence=...,
    evidence_grade=grade,
    evidence_basis=basis,
    evidence_sources=[...],
)
```

### Pattern: error / skipped (no grade)
```python
return SignalResult(signal_id="x", error="fetch failed")  # evidence_grade stays None — OK
return SignalResult(signal_id="x", skipped=True)          # also OK
```

### Pattern: routed signal (post-aggregation by router)
```python
# In signal_architecture/signals/routing/router.py
grade: Optional[EvidenceGrade] = None
sources: list[EvidenceSource] = []
for sub in routed_results:
    if sub.evidence_grade is not None:
        grade = bump_evidence(grade, sub.evidence_grade)
        sources.extend(sub.evidence_sources)
basis = f"Routed across {len(routed_results)} sub-extractors; max grade taken"
return SignalResult(
    signal_id=signal_id,
    score=composite_score,
    confidence=composite_confidence,
    evidence_grade=grade,
    evidence_basis=basis,
    evidence_sources=sources,
)
```

## Steps

### 2.1 — Land the linter
**File**: `scripts/lint_evidence_completeness.py` (create).

```python
"""V7 Phase 2 — static check: every SignalResult construction in production
paths supplies evidence_grade or is an error/skipped construction.

Run: `python scripts/lint_evidence_completeness.py`.
CI exit code: 0 ok, 1 violations found.

Scope: signal_architecture/signals/{extractors,inference,aggregators,routing}.
Skips: tests/, **/__pycache__, error-only and skipped-only constructions.
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

ALLOWLIST: set[str] = set()  # add file paths here only as a last resort


def has_evidence_kw(call: ast.Call) -> bool:
    keywords = {kw.arg for kw in call.keywords if kw.arg}
    if "evidence_grade" in keywords:
        return True
    # error-only or skipped-only constructions: permitted without grade
    if "error" in keywords and "score" not in keywords and "category" not in keywords:
        return True
    if "skipped" in keywords:
        # Inspect the value — only True permits omission
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
```

**Action**: Add it to CI in `.github/workflows/` or the project's existing lint config. Initially it will report many violations — that's the work of this phase.
**Test**: `tests/unit/test_evidence_completeness_lint.py` constructs a tmpdir with one violating fixture and one clean fixture; asserts the linter flags exactly the violator.

### 2.2 — Batch A (stubs)
**Files**: every stub extractor and every stub inference function.
**Action**: Apply the stub-extractor pattern. Add `MAX_EVIDENCE_GRADE = "inferred"` to every `Stub*Extractor` class.
**Test**: After Batch A, run linter — count of violations should drop by ~40% (stub-heavy area).

### 2.3 — Batch B (production web/HTTP)
**Files**: production extractors that pull from a single HTTP source.
**Action**: Apply the single-HTTP pattern. Add `MAX_EVIDENCE_GRADE = "observed"` to each class.

### 2.4 — Batch C (production multi-source)
**Files**: production extractors that combine ≥2 feeds.
**Action**: Apply the multi-source pattern. `MAX_EVIDENCE_GRADE = "corroborated"`.

### 2.5 — Batch D (production register/feed)
**Files**: extractors hitting authoritative registers.
**Action**: Apply the register pattern. `MAX_EVIDENCE_GRADE = "structured_attested"`.

### 2.6 — Batch E (routed signals)
**File**: `signal_architecture/signals/routing/router.py` (and any consumers of routed signals in `inference/functions/routed/`).
**Action**: Implement the routed-signal pattern. Router takes max grade across contributions via `bump_evidence` chained from `None`.

### 2.7 — Flip enforcement
**File**: `signal_architecture/signals/base.py`.
**Action**: Change `BaseExtractor._EVIDENCE_ENFORCEMENT_MODE` default from `"warn"` to `"raise"`. Any extractor that genuinely needs warn mode declares it explicitly on its own class.
**Test**: Construct an instance of a subclass that exceeds its cap → `EvidenceRoleViolation`.

### 2.8 — Calibration smoke
**Files**: none.
**Action**: Run `python -m layers.risk.calibration_harness` across every coverage. Assert <15% guardrail hit rate per existing rule; since grade has no scoring effect in this phase, calibration must be unchanged within rounding.
**Test**: `python -m seed bench && pytest tests/ -x -q`. Calibration harness exits 0 for all 24 configs.

## Test gates

```bash
# Linter is clean
python scripts/lint_evidence_completeness.py

# Per-batch
pytest tests/unit/ -k evidence -v

# Role binding raises after the flip
python -c "
from signal_architecture.signals.base import BaseExtractor
assert BaseExtractor._EVIDENCE_ENFORCEMENT_MODE == 'raise'
"

# Full suite
pytest tests/ -x -q

# Calibration unchanged
python -m seed bench
python -m layers.risk.calibration_harness aerospace cyber casualty fi fpr energy property marine pi do
```

## Done when

- [ ] `scripts/lint_evidence_completeness.py` exits 0.
- [ ] Every extractor class under `signal_architecture/signals/extractors/` declares `MAX_EVIDENCE_GRADE`.
- [ ] Every non-error/non-skipped `SignalResult(` construction supplies `evidence_grade=`.
- [ ] `BaseExtractor._EVIDENCE_ENFORCEMENT_MODE == "raise"`.
- [ ] Full pytest green.
- [ ] Calibration harness green across all 24 configs (no shift; grade has no pricing impact in this phase).

## Out of scope

- Group-level / composite-level grade aggregation. → Phase 3.
- Absence sub-typing. → Phase 3.
- YAML policy & referral wiring. → Phase 4.
- DB persistence. → Phase 5.
- Adversarial pro/counter population. → Phase 6.

## Invariants

1. No `SignalResult` is constructed with a grade above its producer's `MAX_EVIDENCE_GRADE`.
2. Pricing outputs are bit-identical to pre-phase outputs on the same seed (grade is metadata only here).
3. Linter is a CI gate from end of this phase onward; merging code that drops `evidence_grade=` from new constructions fails CI.

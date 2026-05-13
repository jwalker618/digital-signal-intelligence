# V7 Phase 1: Evidence Ladder Foundation

> **Doc audience**: implementation LLM. Self-contained. Paths confirmed against the current tree on `claude/review-dsi-upgrade-phase-1-IXI2f`.

## Depends on
- V6 complete (migration 022 applied, calibration green across 24 configs).
- `signal_provenance` table present (migration 021).

## Blocks
- Phases 2–14. Nothing else can start until the foundation types compile and tests pass.

## V7 Sequence (for context only; each phase is its own doc)

| # | Title | What it lands |
|---|-------|---------------|
| 1 | **Foundation** | EvidenceGrade taxonomy, `bump_evidence`, role-binding, new SignalResult fields, transition helper |
| 2 | Extractor migration | Apply transition to every extractor; enforce role binding |
| 3 | Aggregation | Promotion-merge in aggregators; `(min, distribution)` rollup; absence sub-typing |
| 4 | YAML policy + referral | `evidence_grade_policy` block; three condition types; scripted rollout to 24 configs |
| 5 | Persistence | DB columns, history table, SHA3-224 commitments, dual audit log |
| 6 | Adversarial validator | 4-axis blind validator; pro/counter/tie-breaker stored fields |
| 7 | Calibration store | Triple-source calibration with human-in-loop sampling |
| 8 | Reproducibility class | `reproducibility` field; multi-pull verification |
| 9 | Risk primitives | Orthogonal primitive_type taxonomy |
| 10 | Root-cause dedup audit | Refactor `sanctions_aggregator` / `corporate_aggregator` to root-cause clustering |
| 11 | Variant loop | Within-cycle sibling-signal amplification |
| 12 | Mechanism memory | Cross-cycle abstract pattern store |
| 13 | Delta-aware re-extraction | Entity-event triggered signal-subset recompute |
| 14 | API + server-side disclosure packets | Pydantic exposure, templated underwriter packets, commitment-verify endpoint (backend only — touches no `frontend/**`) |
| 15 | Frontend (Workbench + Calibration UI) | All `frontend/**` work, last. Deferred so it merges cleanly after the in-flight styling / generateweb prep |

## Scope (this phase)

Add an ordered evidence-strength taxonomy to `SignalResult` and the propagation machinery to support cycle-time **promotion** (monotonic climb up the ladder). Lock the taxonomy as a string `Literal` with a rank dict so domain-specific rungs can be inserted later without schema migration. Bind rungs to producer roles so an HTTP-scrape extractor cannot assert `STRUCTURED_ATTESTED`. Add transition helpers so Phase 2 can migrate 60+ call sites without a big-bang break.

## Decisions (locked, do not relitigate)

| # | Decision | Choice | Rationale |
|---|----------|--------|-----------|
| D1 | Taxonomy storage | `Literal[...]` string + `_EVIDENCE_RANK: dict[str, int]` | Decouples persisted value from position. Inserting a rung between two existing ones is a two-line edit, not a migration. |
| D2 | Initial rungs | 5: `inferred`, `observed`, `corroborated`, `structured_attested`, `behaviourally_validated` | Five-rung baseline. Domain rungs interleave in later phases. |
| D3 | Promotion semantics | `bump_evidence(new)` monotonic — only climbs | Findings accumulate evidence; never demote. Lifted directly from Clearwing `findings/types.py:341-349`. |
| D4 | Role binding | Each extractor class declares `MAX_EVIDENCE_GRADE`; runtime guard rejects higher | Web-scrape cannot return STRUCTURED_ATTESTED. Enforced in base class. |
| D5 | New fields on `SignalResult` | `evidence_grade`, `evidence_basis`, `evidence_sources: list[EvidenceSource]`, `evidence_pro`, `evidence_counter`, `evidence_tie_breaker` | All `Optional[]` initially with deprecation warning; Phase 2 batched migration; Phase 6 tightens `evidence_grade`/`evidence_basis` to required. |
| D6 | Sources typing | `EvidenceSource` dataclass, not `list[str]` | URLs go in structured records; free text only in `evidence_basis`. |
| D7 | Scalar weighted mean | Computed for display only; never a referral threshold | Cardinal arithmetic on an ordinal taxonomy is suspect. Referrals key on min+distribution (Phase 4). |
| D8 | Pro/counter/tie-breaker | Stored fields on every `SignalResult`, populated when adversarial validator runs in Phase 6 | Optional until Phase 6 lands. |
| D9 | Confidence orthogonality | Unchanged; grade is independent of confidence | The two metrics never compute from each other. |
| D10 | Absence handling | Absence carries no grade in Phase 1; Phase 3 introduces `absence_sub_type` | Don't conflate failed-to-fetch with authoritatively-empty in foundation. |

## Files

### Create
- `signal_architecture/signals/evidence.py` — taxonomy, rank dict, `EvidenceSource`, `bump_evidence`, role-binding helpers
- `tests/unit/test_evidence.py` — taxonomy tests
- `tests/unit/test_evidence_role_binding.py` — role-binding guard tests

### Modify
- `signal_architecture/signals/types.py` — extend `SignalResult` with evidence fields (all `Optional[]`)
- `signal_architecture/signals/base.py` — add `MAX_EVIDENCE_GRADE` class attr to `BaseExtractor`; expose `evidence_for()` helper on `BaseAggregator`
- `signal_architecture/signals/__init__.py` — re-export `EvidenceGrade`, `EvidenceSource`, `bump_evidence`

### Do not modify (yet)
- Any file under `inference/functions/` — Phase 2
- Any file under `aggregators/implementations/` — Phase 3
- `layers/risk/scorer.py` — Phase 3 for composite-level rollup
- Any YAML — Phase 4
- Any ORM or alembic file — Phase 5

## Types (exact code to land)

`signal_architecture/signals/evidence.py`:

```python
"""V7/Phase 1 — Evidence-grade taxonomy and promotion mechanics.

Imported by `signal_architecture.signals.types` (SignalResult fields),
`signal_architecture.signals.base` (role-binding), and downstream by
the aggregator/scorer/validator/calibration layers in later phases.

Design references:
    - V7 phase_1.md decision table.
    - Clearwing `findings/types.py:38-67, 341-349` for the
      string-Literal + rank-dict + monotonic-bump pattern.
"""
from __future__ import annotations

import warnings
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Literal, Optional, Sequence

EvidenceGrade = Literal[
    "inferred",
    "observed",
    "corroborated",
    "structured_attested",
    "behaviourally_validated",
]

EVIDENCE_GRADES: tuple[EvidenceGrade, ...] = (
    "inferred",
    "observed",
    "corroborated",
    "structured_attested",
    "behaviourally_validated",
)

_EVIDENCE_RANK: dict[str, int] = {g: i for i, g in enumerate(EVIDENCE_GRADES)}


def evidence_rank(grade: EvidenceGrade) -> int:
    """Return 0-indexed rank. Raises KeyError on unknown grade."""
    return _EVIDENCE_RANK[grade]


def evidence_compare(a: EvidenceGrade, b: EvidenceGrade) -> int:
    """-1 / 0 / 1 like Python 2 cmp."""
    ra, rb = _EVIDENCE_RANK[a], _EVIDENCE_RANK[b]
    return (ra > rb) - (ra < rb)


def evidence_at_or_above(grade: EvidenceGrade, floor: EvidenceGrade) -> bool:
    return _EVIDENCE_RANK[grade] >= _EVIDENCE_RANK[floor]


def bump_evidence(current: Optional[EvidenceGrade], new: EvidenceGrade) -> EvidenceGrade:
    """Monotonic promotion. Returns the stronger of current/new.

    `current` may be None (no grade yet) — `new` always wins in that case.
    Never demotes. This is the canonical operation; every place that
    'updates' an evidence_grade goes through this function.
    """
    if new not in _EVIDENCE_RANK:
        raise ValueError(f"unknown evidence grade: {new!r}")
    if current is None:
        return new
    if current not in _EVIDENCE_RANK:
        # Tolerate legacy/garbage strings by promoting unconditionally.
        return new
    if _EVIDENCE_RANK[new] > _EVIDENCE_RANK[current]:
        return new
    return current


@dataclass(frozen=True)
class EvidenceSource:
    """One structured source record. Machine-readable; never free text.

    `kind` is one of:
        api        — direct API call (REST/GRPC)
        scrape     — HTML scrape from entity-owned domain
        register   — authoritative register pull (SEC EDGAR, Companies House, S&P, IACS class society)
        feed       — subscription feed (Refinitiv, Moody's, etc.)
        observation — multi-time observation (cert rotation, patch cadence)
        derived    — computed from other signals; `ref` is the derivation function name
        absence    — authoritative empty (Phase 3 will lean on this)
    """
    source_id: str           # short stable ID, e.g. "sec_edgar"
    kind: Literal["api", "scrape", "register", "feed", "observation", "derived", "absence"]
    ref: str                 # URL, dataset name, function name — opaque to evidence module
    fetched_at: datetime
    response_hash: Optional[str] = None  # ties to signal_provenance.response_hash when applicable
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_id": self.source_id,
            "kind": self.kind,
            "ref": self.ref,
            "fetched_at": self.fetched_at.isoformat(),
            "response_hash": self.response_hash,
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "EvidenceSource":
        return cls(
            source_id=d["source_id"],
            kind=d["kind"],
            ref=d["ref"],
            fetched_at=datetime.fromisoformat(d["fetched_at"]),
            response_hash=d.get("response_hash"),
            notes=d.get("notes", ""),
        )


# ---------------------------------------------------------------------------
# Role binding
# ---------------------------------------------------------------------------

class EvidenceRoleViolation(ValueError):
    """Raised when an extractor tries to claim a grade above its declared max.

    Caught nowhere by default — fail loud in dev. Phase 2 swaps to warn-mode
    during migration; Phase 6 makes it hard-error in production.
    """


def assert_within_role(
    producer_class_name: str,
    max_grade: EvidenceGrade,
    claimed: EvidenceGrade,
    *,
    mode: Literal["raise", "warn"] = "raise",
) -> None:
    """Reject grades above what the producer's role permits."""
    if _EVIDENCE_RANK[claimed] > _EVIDENCE_RANK[max_grade]:
        msg = (
            f"{producer_class_name} declares MAX_EVIDENCE_GRADE={max_grade!r} "
            f"but constructed a SignalResult with evidence_grade={claimed!r}. "
            f"Either lower the grade or change the extractor base class."
        )
        if mode == "raise":
            raise EvidenceRoleViolation(msg)
        warnings.warn(msg, stacklevel=3)


# ---------------------------------------------------------------------------
# Default role caps for the standard extractor patterns
# ---------------------------------------------------------------------------

DEFAULT_ROLE_CAPS: dict[str, EvidenceGrade] = {
    # Class name → highest grade it may assert. Tighter caps allowed; looser
    # caps disallowed. Subclasses override via MAX_EVIDENCE_GRADE.
    "StubExtractor": "inferred",
    "BaseExtractor": "behaviourally_validated",  # generic; subclasses tighten
    "WebScrapeExtractor": "observed",
    "MultiSourceExtractor": "corroborated",
    "RegisterExtractor": "structured_attested",
    "FeedExtractor": "structured_attested",
    "TimeSeriesExtractor": "behaviourally_validated",
}


def default_cap_for(class_name: str) -> EvidenceGrade:
    """Look up default cap; falls back to BaseExtractor's cap."""
    return DEFAULT_ROLE_CAPS.get(class_name, DEFAULT_ROLE_CAPS["BaseExtractor"])
```

`signal_architecture/signals/types.py` — additions to `SignalResult` (do **not** remove or reorder existing fields):

```python
# At the top, alongside existing imports:
from .evidence import EvidenceGrade, EvidenceSource

# Append new fields to the SignalResult dataclass, ALL Optional with defaults:
@dataclass
class SignalResult:
    # ... existing fields unchanged ...

    # --- V7 Phase 1: evidence fields. Optional during migration. ---
    # Phase 2 populates them in every extractor.
    # Phase 6 tightens `evidence_grade` and `evidence_basis` to required.
    evidence_grade: Optional[EvidenceGrade] = None
    evidence_basis: Optional[str] = None
    evidence_sources: List[EvidenceSource] = field(default_factory=list)

    # Adversarial validation (populated by Phase 6).
    evidence_pro: Optional[str] = None
    evidence_counter: Optional[str] = None
    evidence_tie_breaker: Optional[str] = None

    def __post_init__(self):
        # ... existing __post_init__ body unchanged ...

        # V7 Phase 1: validate evidence_basis length only if present.
        if self.evidence_basis is not None and len(self.evidence_basis) > 500:
            raise ValueError(
                f"evidence_basis must be <=500 chars, got {len(self.evidence_basis)}"
            )
        if self.evidence_basis is not None and len(self.evidence_basis) == 0:
            raise ValueError("evidence_basis must be non-empty if present")
```

`signal_architecture/signals/base.py` — additions to `BaseExtractor`:

```python
# At the top:
from .evidence import EvidenceGrade, assert_within_role, default_cap_for

class BaseExtractor(ABC):
    # ... existing class body unchanged ...

    # V7 Phase 1: per-class evidence cap. Subclasses override.
    MAX_EVIDENCE_GRADE: EvidenceGrade = "behaviourally_validated"

    # Phase 2 flips this to "raise". Stays "warn" during migration so existing
    # call sites that haven't been updated yet don't crash CI.
    _EVIDENCE_ENFORCEMENT_MODE: str = "warn"

    def _check_evidence_role(self, claimed: EvidenceGrade) -> None:
        """Call from any extractor that asserts a grade on a SignalResult."""
        assert_within_role(
            type(self).__name__,
            self.MAX_EVIDENCE_GRADE,
            claimed,
            mode=self._EVIDENCE_ENFORCEMENT_MODE,  # type: ignore[arg-type]
        )
```

`signal_architecture/signals/base.py` — additions to `BaseAggregator`:

```python
def aggregate_evidence(
    self,
    contributing: Sequence[SignalResult],
) -> tuple[Optional[EvidenceGrade], list[EvidenceSource]]:
    """Stub for Phase 1. Returns (None, []).

    Phase 3 supplies the real implementation: promotion-merge over the
    contributing signals, with role-bound producer roles respected.
    Kept here so aggregator subclasses can call it from Phase 1 without
    knowing whether Phase 3 has landed.
    """
    return None, []
```

`signal_architecture/signals/__init__.py` — re-exports:

```python
from .evidence import (
    EvidenceGrade,
    EvidenceSource,
    EvidenceRoleViolation,
    EVIDENCE_GRADES,
    bump_evidence,
    evidence_compare,
    evidence_at_or_above,
    evidence_rank,
    default_cap_for,
)
```

## Steps

### 1.1 — Create `evidence.py`
**Files**: `signal_architecture/signals/evidence.py` (create).
**Action**: Drop in the code from the "Types" block above verbatim.
**Test**: `pytest tests/unit/test_evidence.py -v` — see test gates below.

### 1.2 — Extend `SignalResult`
**Files**: `signal_architecture/signals/types.py` (modify).
**Action**: Add the import + the six new `Optional` fields + the `__post_init__` extension shown above. Do **not** alter existing field order or types.
**Test**: Construct a `SignalResult(signal_id="x")` with no evidence args; assert all six new fields are `None` / `[]`.

### 1.3 — Wire `BaseExtractor` role binding
**Files**: `signal_architecture/signals/base.py` (modify).
**Action**: Add `MAX_EVIDENCE_GRADE`, `_EVIDENCE_ENFORCEMENT_MODE`, `_check_evidence_role()` to `BaseExtractor`. Add `aggregate_evidence()` stub to `BaseAggregator`.
**Test**: `tests/unit/test_evidence_role_binding.py`.

### 1.4 — Re-export from package init
**Files**: `signal_architecture/signals/__init__.py` (modify).
**Action**: Add re-exports.
**Test**: `python -c "from signal_architecture.signals import EvidenceGrade, bump_evidence, EvidenceSource"` — exits 0.

### 1.5 — Author tests
**Files**: `tests/unit/test_evidence.py`, `tests/unit/test_evidence_role_binding.py` (create).
**Action**: Land the test code from "Test gates" below.
**Test**: `pytest tests/unit/test_evidence.py tests/unit/test_evidence_role_binding.py -v` green.

### 1.6 — Smoke-test integration
**Files**: none modified.
**Action**: Run the existing full pytest suite. Nothing should break — every change is additive and all new fields are `Optional` with defaults.
**Test**: `pytest tests/ -x -q` — green.

## Test gates (exact code)

`tests/unit/test_evidence.py`:

```python
"""V7 Phase 1 — evidence taxonomy tests."""
import pytest
from datetime import datetime, timezone

from signal_architecture.signals.evidence import (
    EVIDENCE_GRADES,
    EvidenceSource,
    bump_evidence,
    evidence_at_or_above,
    evidence_compare,
    evidence_rank,
)


class TestRanking:
    def test_grades_are_ordered(self):
        ranks = [evidence_rank(g) for g in EVIDENCE_GRADES]
        assert ranks == sorted(ranks)
        assert len(set(ranks)) == len(ranks)

    def test_compare(self):
        assert evidence_compare("inferred", "observed") == -1
        assert evidence_compare("structured_attested", "structured_attested") == 0
        assert evidence_compare("behaviourally_validated", "corroborated") == 1

    def test_at_or_above(self):
        assert evidence_at_or_above("structured_attested", "observed") is True
        assert evidence_at_or_above("observed", "structured_attested") is False
        assert evidence_at_or_above("observed", "observed") is True


class TestBump:
    def test_none_promotes_to_anything(self):
        assert bump_evidence(None, "inferred") == "inferred"
        assert bump_evidence(None, "structured_attested") == "structured_attested"

    def test_monotonic(self):
        assert bump_evidence("inferred", "observed") == "observed"
        assert bump_evidence("observed", "inferred") == "observed"  # never demotes
        assert bump_evidence("corroborated", "corroborated") == "corroborated"

    def test_rejects_unknown(self):
        with pytest.raises(ValueError):
            bump_evidence("inferred", "made_up")  # type: ignore[arg-type]

    def test_tolerates_garbage_current(self):
        # Forward-compat: an unknown current value gets overwritten cleanly.
        assert bump_evidence("legacy_value", "observed") == "observed"  # type: ignore[arg-type]


class TestEvidenceSource:
    def test_roundtrip(self):
        s = EvidenceSource(
            source_id="sec_edgar",
            kind="register",
            ref="https://www.sec.gov/cgi-bin/browse-edgar?...",
            fetched_at=datetime.now(timezone.utc),
            response_hash="abc123",
            notes="10-K filing",
        )
        d = s.to_dict()
        assert EvidenceSource.from_dict(d) == s
```

`tests/unit/test_evidence_role_binding.py`:

```python
"""V7 Phase 1 — role-binding guard tests."""
import pytest
import warnings

from signal_architecture.signals.base import BaseExtractor
from signal_architecture.signals.evidence import EvidenceRoleViolation, assert_within_role


class _StubScraper(BaseExtractor):
    MAX_EVIDENCE_GRADE = "observed"
    _EVIDENCE_ENFORCEMENT_MODE = "raise"
    SOURCE_NAME = "stub"

    def extract(self, entity_id, context=None, **kwargs):
        raise NotImplementedError


class _StubRegister(BaseExtractor):
    MAX_EVIDENCE_GRADE = "structured_attested"
    _EVIDENCE_ENFORCEMENT_MODE = "raise"
    SOURCE_NAME = "stub"

    def extract(self, entity_id, context=None, **kwargs):
        raise NotImplementedError


def test_assert_within_role_passes_at_or_below_cap():
    assert_within_role("Foo", "structured_attested", "observed")  # no raise
    assert_within_role("Foo", "structured_attested", "structured_attested")


def test_assert_within_role_raises_above_cap():
    with pytest.raises(EvidenceRoleViolation):
        assert_within_role("Foo", "observed", "corroborated")


def test_extractor_check_in_raise_mode():
    s = _StubScraper()
    with pytest.raises(EvidenceRoleViolation):
        s._check_evidence_role("corroborated")
    s._check_evidence_role("observed")  # passes


def test_extractor_check_in_warn_mode():
    class _Warner(BaseExtractor):
        MAX_EVIDENCE_GRADE = "observed"
        _EVIDENCE_ENFORCEMENT_MODE = "warn"
        SOURCE_NAME = "stub"

        def extract(self, entity_id, context=None, **kwargs):
            raise NotImplementedError

    w = _Warner()
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        w._check_evidence_role("corroborated")
    assert any("MAX_EVIDENCE_GRADE" in str(x.message) for x in caught)


def test_register_extractor_can_assert_structured_attested():
    r = _StubRegister()
    r._check_evidence_role("structured_attested")  # passes
    with pytest.raises(EvidenceRoleViolation):
        r._check_evidence_role("behaviourally_validated")
```

## Done when

- [ ] `signal_architecture/signals/evidence.py` exists; mypy `--follow-imports=silent` clean against it.
- [ ] `SignalResult` carries six new `Optional` fields; all existing constructions still work without args.
- [ ] `BaseExtractor.MAX_EVIDENCE_GRADE` and `_check_evidence_role()` present; defaults to `"behaviourally_validated"` for backward compat.
- [ ] `pytest tests/unit/test_evidence.py tests/unit/test_evidence_role_binding.py -v` green.
- [ ] `pytest tests/ -x -q` green — no existing test breaks.
- [ ] `python -c "from signal_architecture.signals import EvidenceGrade, bump_evidence, EvidenceSource, EvidenceRoleViolation"` exits 0.

## Out of scope

- Modifying any extractor or inference function. → Phase 2.
- Aggregation, group-level rollup. → Phase 3.
- YAML, builder validation, referral wiring. → Phase 4.
- DB columns, migrations, ORM. → Phase 5.
- Pro/counter/tie-breaker *population* (fields exist, but nothing writes to them). → Phase 6.
- Frontend, API schema exposure. → Phase 14.

## Invariants that must hold at end of Phase 1

1. Every `SignalResult` in the codebase can still be constructed without supplying evidence fields.
2. `bump_evidence` never demotes.
3. `EvidenceRoleViolation` is raise-mode for explicit subclasses and warn-mode for `BaseExtractor` itself. Phase 2 flips the default.
4. No YAML, ORM, migration, or frontend file changes in this phase.

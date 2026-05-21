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
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Literal, Optional

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

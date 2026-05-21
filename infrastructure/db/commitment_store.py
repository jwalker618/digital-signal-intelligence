"""V7 Phase 5 — SHA3-224 commitments over canonical-JSON signal payloads.

Modelled on signal_architecture/signals/provenance.py's canonicalisation
so digest comparisons stay interoperable with the V6 provenance layer.

Four commitment scopes:

    full_payload      — entire SignalResult dict (auditor-grade)
    value_and_grade   — minimum tuple sufficient to dispute later
    pro_counter       — pro/counter/tie-breaker text only (Phase 6 writes these)
    composite         — composite_min_grade + distribution + referral list

Determinism: identical inputs -> identical digest. The canonical JSON
serialisation uses sort_keys=True + separators=(",",":") + default=str so
non-JSON-native types (datetime, UUID) hash deterministically.
"""
from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timezone
from typing import Any, Literal, Optional

from sqlalchemy.orm import Session

from infrastructure.db.models import SignalCommitment
from signal_architecture.signals.types import SignalResult


CommitmentScope = Literal[
    "full_payload",
    "value_and_grade",
    "pro_counter",
    "composite",
]


def _canonical_bytes(payload: Any) -> bytes:
    """Canonicalise to deterministic JSON bytes."""
    return json.dumps(
        payload, sort_keys=True, separators=(",", ":"), default=str
    ).encode("utf-8")


def sha3_224(payload: Any) -> str:
    return hashlib.sha3_224(_canonical_bytes(payload)).hexdigest()


def _payload_for_scope(sig: SignalResult, scope: CommitmentScope) -> tuple[dict[str, Any], list[str]]:
    """Return (canonical_payload, keys) for the given scope.

    Sources are serialised separately as `evidence_sources` (list of dicts)
    so they stay stable under hash even when their dataclass changes.
    """
    if scope == "full_payload":
        keys = sorted([
            "signal_id", "score", "category", "confidence",
            "evidence_grade", "evidence_basis",
            "evidence_pro", "evidence_counter", "evidence_tie_breaker",
            "absence_sub_type",
        ])
        payload: dict[str, Any] = {k: getattr(sig, k, None) for k in keys}
        payload["evidence_sources"] = [
            s.to_dict() for s in (sig.evidence_sources or [])
        ]
        return payload, keys + ["evidence_sources"]
    if scope == "value_and_grade":
        keys = ["signal_id", "score", "category", "evidence_grade"]
        return {k: getattr(sig, k, None) for k in keys}, keys
    if scope == "pro_counter":
        keys = [
            "signal_id", "evidence_pro", "evidence_counter", "evidence_tie_breaker",
        ]
        return {k: getattr(sig, k, None) for k in keys}, keys
    raise ValueError(f"unknown scope: {scope}")


def commit_signal(
    db: Session,
    *,
    model_version_id: uuid.UUID,
    sig: SignalResult,
    scope: CommitmentScope = "full_payload",
) -> str:
    """Hash + persist. Returns the hex digest."""
    payload, keys = _payload_for_scope(sig, scope)
    digest = sha3_224(payload)
    row = SignalCommitment(
        model_version_id=model_version_id,
        signal_id=sig.signal_id,
        scope=scope,
        algorithm="sha3_224",
        digest=digest,
        committed_at=datetime.now(timezone.utc),
        canonical_keys=keys,
    )
    db.add(row)
    return digest


def commit_composite(
    db: Session,
    *,
    model_version_id: uuid.UUID,
    composite_min_grade: Optional[str],
    composite_weighted_mean_grade: Optional[float],
    composite_grade_distribution: dict[str, float],
    referral_reasons: list[str],
) -> str:
    payload = {
        "composite_min_grade": composite_min_grade,
        "composite_weighted_mean_grade": composite_weighted_mean_grade,
        "composite_grade_distribution": composite_grade_distribution,
        "referral_reasons": sorted(referral_reasons),
    }
    digest = sha3_224(payload)
    row = SignalCommitment(
        model_version_id=model_version_id,
        signal_id=None,
        scope="composite",
        algorithm="sha3_224",
        digest=digest,
        committed_at=datetime.now(timezone.utc),
        canonical_keys=sorted(payload.keys()),
    )
    db.add(row)
    return digest


def verify(
    db: Session,
    *,
    model_version_id: uuid.UUID,
    signal_id: Optional[str],
    scope: CommitmentScope,
    candidate_payload: dict[str, Any],
) -> bool:
    """True if the stored digest matches the candidate's canonical hash.

    Returns False when no row exists for the (mv, signal, scope) triple OR
    when the digests disagree.
    """
    row = (
        db.query(SignalCommitment)
        .filter_by(model_version_id=model_version_id, signal_id=signal_id, scope=scope)
        .one_or_none()
    )
    if row is None:
        return False
    return row.digest == sha3_224(candidate_payload)

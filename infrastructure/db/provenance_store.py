"""V6/E2 — signal-provenance persistence helpers.

Thin wrappers that write Provenance records + chain edges into the
tables added by alembic migration 021. Keeps the DB details isolated
from `ProductionExtractor` so the extractor layer stays orchestration-
free and testable.
"""
from __future__ import annotations

import logging
import uuid
from typing import Any, Dict, Iterable, Optional, Sequence, Tuple

from sqlalchemy import text
from sqlalchemy.orm import Session

from signal_architecture.signals.provenance import Provenance, build_provenance

log = logging.getLogger("dsi.provenance_store")


def persist_provenance(
    db: Session,
    *,
    signal_id: str,
    model_version_id: uuid.UUID,
    assessment_id: Optional[uuid.UUID],
    provenance: Provenance,
) -> str:
    """Insert a single provenance row. Returns the stored `self_hash`.

    Idempotent-by-hash: repeated writes of the identical provenance
    payload are coalesced into one row thanks to the UNIQUE constraint
    on ``self_hash`` in migration 021.
    """
    self_hash = provenance.self_hash()
    db.execute(
        text(
            "INSERT INTO signal_provenance "
            "  (id, model_version_id, assessment_id, signal_id, source_name, "
            "   extractor_version, cache_hit, response_status_code, "
            "   response_hash, self_hash, provenance, request_timestamp) "
            "VALUES "
            "  (gen_random_uuid(), :mvid, :aid, :sid, :source, "
            "   :ver, :cache, :status, :rhash, :shash, :prov, :ts) "
            "ON CONFLICT (self_hash) DO NOTHING"
        ),
        {
            "mvid": model_version_id,
            "aid": assessment_id,
            "sid": signal_id,
            "source": provenance.source_name,
            "ver": provenance.extractor_version,
            "cache": provenance.cache_hit,
            "status": provenance.response_status_code,
            "rhash": provenance.response_hash,
            "shash": self_hash,
            "prov": provenance.to_dict(),
            "ts": provenance.request_timestamp,
        },
    )
    return self_hash


def persist_chain(
    db: Session,
    *,
    assessment_id: uuid.UUID,
    edges: Iterable[Tuple[str, str]],
) -> int:
    """Insert ``(parent_hash, child_hash)`` edges for an assessment.

    Returns the number of edges written (duplicates are silently
    dropped thanks to the unique constraint from migration 021).
    """
    count = 0
    for parent, child in edges:
        db.execute(
            text(
                "INSERT INTO provenance_chain "
                "  (id, assessment_id, parent_hash, child_hash) "
                "VALUES (gen_random_uuid(), :aid, :p, :c) "
                "ON CONFLICT (assessment_id, parent_hash, child_hash) "
                "DO NOTHING"
            ),
            {"aid": assessment_id, "p": parent, "c": child},
        )
        count += 1
    return count


def persist_extractor_result(
    db: Session,
    *,
    signal_id: str,
    model_version_id: uuid.UUID,
    assessment_id: Optional[uuid.UUID],
    extractor_result: Any,
) -> Optional[str]:
    """Convenience: write the Provenance already attached by
    ``ProductionExtractor.extract()`` into ``metadata["provenance"]``.

    Returns the new row's ``self_hash`` or None if the extractor didn't
    attach a provenance payload (e.g. absence-as-signal results with
    kill-switch / missing-key paths).
    """
    meta = extractor_result.metadata or {}
    payload = meta.get("provenance")
    if not payload:
        return None

    # Re-derive the Provenance object from the stored dict using
    # build_provenance so the hash is recomputed deterministically — this
    # guards against any client that tampered with the metadata.
    import datetime as _dt

    ts_str = payload.get("request_timestamp")
    ts = _dt.datetime.fromisoformat(ts_str) if ts_str else None
    provenance = build_provenance(
        source_name=payload["source_name"],
        source_url=payload.get("source_url", ""),
        response_body={"response_hash": payload["response_hash"]},
        response_status_code=payload.get("response_status_code", 200),
        response_etag=payload.get("response_etag"),
        extractor_version=payload.get("extractor_version", "1.0"),
        cache_hit=bool(payload.get("cache_hit", False)),
        parent_hashes=list(payload.get("parent_hashes") or []),
        request_timestamp=ts,
    )
    # Use the *original* response_hash so the round-trip is stable
    # (build_provenance hashes {"response_hash": ...} not the raw body).
    persisted = Provenance(
        source_name=provenance.source_name,
        source_url=provenance.source_url,
        request_timestamp=provenance.request_timestamp,
        response_hash=payload["response_hash"],
        response_status_code=provenance.response_status_code,
        cache_hit=provenance.cache_hit,
        extractor_version=provenance.extractor_version,
        response_etag=provenance.response_etag,
        parent_hashes=list(provenance.parent_hashes),
    )
    return persist_provenance(
        db,
        signal_id=signal_id,
        model_version_id=model_version_id,
        assessment_id=assessment_id,
        provenance=persisted,
    )

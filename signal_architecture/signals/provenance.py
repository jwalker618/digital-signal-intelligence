"""V6/E2 — Signal-lineage chain-of-custody.

Every successful extraction produces a ``Provenance`` record that
hashes the normalised response body (sha256), captures
source_url / request_timestamp / response_etag / response_status /
cache_hit / extractor_version, and links to the parent provenance
hash so a quote's premium is auditable end-to-end.

Storage (added in follow-up alembic migration `021_signal_provenance`):

- ``signal_provenance`` table: id, model_version_id FK, signal_id,
  provenance JSONB, hash (unique), created_at.
- ``provenance_chain`` table: parent_hash, child_hash, assessment_id FK.

API (follow-up): ``GET /api/v1/quotes/{id}/provenance`` returns the
full chain.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _canonical_bytes(body: Any) -> bytes:
    """Render ``body`` as a canonical deterministic JSON byte-string.

    Used for the response_hash so two semantically-equivalent responses
    produce the same hash (dict key ordering, whitespace stripped).
    """
    if isinstance(body, (bytes, bytearray)):
        return bytes(body)
    if isinstance(body, str):
        return body.encode("utf-8")
    return json.dumps(
        body, sort_keys=True, separators=(",", ":"), default=str
    ).encode("utf-8")


def compute_response_hash(body: Any) -> str:
    """Return a hex-encoded sha256 of the canonical JSON body."""
    return hashlib.sha256(_canonical_bytes(body)).hexdigest()


@dataclass(frozen=True)
class Provenance:
    source_name: str
    source_url: str
    request_timestamp: datetime
    response_hash: str
    response_status_code: int
    cache_hit: bool
    extractor_version: str
    response_etag: Optional[str] = None
    parent_hashes: List[str] = field(default_factory=list)

    def self_hash(self) -> str:
        """Deterministic hash over the provenance fields themselves.

        Used to anchor this provenance record inside the Merkle-style
        chain of trust. Including ``parent_hashes`` in the hash means
        any tampering up-chain invalidates the child's self_hash.
        """
        payload = {
            "source_name": self.source_name,
            "source_url": self.source_url,
            "request_timestamp": self.request_timestamp.isoformat(),
            "response_hash": self.response_hash,
            "response_status_code": self.response_status_code,
            "cache_hit": self.cache_hit,
            "extractor_version": self.extractor_version,
            "response_etag": self.response_etag,
            "parent_hashes": list(self.parent_hashes),
        }
        return hashlib.sha256(_canonical_bytes(payload)).hexdigest()

    def chain_of_trust(self) -> List[str]:
        """Return ``[parent_hash, ..., self_hash]`` for audit display."""
        return list(self.parent_hashes) + [self.self_hash()]

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["request_timestamp"] = self.request_timestamp.isoformat()
        d["self_hash"] = self.self_hash()
        return d


def build_provenance(
    *,
    source_name: str,
    source_url: str,
    response_body: Any,
    response_status_code: int = 200,
    response_etag: Optional[str] = None,
    extractor_version: str = "1.0",
    cache_hit: bool = False,
    parent_hashes: Optional[List[str]] = None,
    request_timestamp: Optional[datetime] = None,
) -> Provenance:
    """Convenience constructor computing ``response_hash`` automatically."""
    return Provenance(
        source_name=source_name,
        source_url=source_url,
        request_timestamp=request_timestamp or _utcnow(),
        response_hash=compute_response_hash(response_body),
        response_status_code=response_status_code,
        cache_hit=cache_hit,
        extractor_version=extractor_version,
        response_etag=response_etag,
        parent_hashes=list(parent_hashes or []),
    )


def verify_chain(nodes: List[Provenance]) -> bool:
    """Return True if every node in ``nodes`` lists the previous node's
    ``self_hash`` as a parent. Empty chains are trivially valid.
    """
    if not nodes:
        return True
    prev_hash: Optional[str] = None
    for node in nodes:
        if prev_hash is not None and prev_hash not in node.parent_hashes:
            return False
        prev_hash = node.self_hash()
    return True

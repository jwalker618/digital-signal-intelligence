"""V7 Phase 13 — SEC EDGAR new-filing webhook adapter (stub).

Production wiring is deferred to deploy time; this stub establishes the
contract:
    verify_hmac(body, signature) -> bool      — HMAC SHA-256 with env
                                                 secret DSI_SEC_EDGAR_HMAC_SECRET.
    parse(body)                  -> dict      — kwargs ready for
                                                 receive_event().
"""
from __future__ import annotations

import json

from ._common import verify_hmac_sha256

HMAC_ENV = "DSI_SEC_EDGAR_HMAC_SECRET"


def verify_hmac(body: bytes, signature: str) -> bool:
    return verify_hmac_sha256(body, signature, secret_env=HMAC_ENV)


def parse(body: bytes) -> dict:
    """Map a SEC EDGAR webhook payload into receive_event kwargs."""
    data = json.loads(body.decode("utf-8") or "{}")
    # SEC EDGAR uses accession_number as the canonical filing key.
    accession = data.get("accessionNumber") or data.get("accession_number")
    cik = data.get("cik") or data.get("CIK")
    return {
        "event_type": "entity_filing",
        "source_feed": "sec_edgar",
        "entity_id": str(cik) if cik else data.get("entityId", "unknown"),
        "payload": data,
        "dedup_key": f"sec_edgar:{accession}" if accession else None,
        "hinted_signal_id": "sec_filing_recency",
    }

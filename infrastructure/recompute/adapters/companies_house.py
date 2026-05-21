"""V7 Phase 13 — Companies House change webhook adapter (stub)."""
from __future__ import annotations

import json

from ._common import verify_hmac_sha256

HMAC_ENV = "DSI_COMPANIES_HOUSE_HMAC_SECRET"


def verify_hmac(body: bytes, signature: str) -> bool:
    return verify_hmac_sha256(body, signature, secret_env=HMAC_ENV)


def parse(body: bytes) -> dict:
    data = json.loads(body.decode("utf-8") or "{}")
    # Companies House dedups on event_id; mapping based on resource_kind.
    event_id = data.get("event", {}).get("transaction_id") or data.get("event_id")
    company_number = data.get("resource_id") or data.get("company_number")
    kind = (data.get("resource_kind") or "").lower()

    if "officer" in kind:
        event_type = "entity_directorship"
        hint = "director_litigation_history"
    else:
        event_type = "entity_filing"
        hint = "corporate_registry_routed"

    return {
        "event_type": event_type,
        "source_feed": "companies_house",
        "entity_id": str(company_number) if company_number else data.get("entityId", "unknown"),
        "payload": data,
        "dedup_key": f"companies_house:{event_id}" if event_id else None,
        "hinted_signal_id": hint,
    }

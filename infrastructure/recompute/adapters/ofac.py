"""V7 Phase 13 — OFAC SDN list-update webhook adapter (stub).

OFAC doesn't itself push webhooks — production typically subscribes to
a notifier (OpenSanctions push, internal cron) that wraps the SDN refresh
into a webhook to this endpoint. The contract is the same.
"""
from __future__ import annotations

import json

from ._common import verify_hmac_sha256

HMAC_ENV = "DSI_OFAC_HMAC_SECRET"


def verify_hmac(body: bytes, signature: str) -> bool:
    return verify_hmac_sha256(body, signature, secret_env=HMAC_ENV)


def parse(body: bytes) -> dict:
    data = json.loads(body.decode("utf-8") or "{}")
    sdn_id = data.get("sdn_id") or data.get("list_id") or data.get("id")
    entity = data.get("entity_id") or data.get("name", "unknown")
    return {
        "event_type": "sanctions_update",
        "source_feed": "ofac",
        "entity_id": str(entity),
        "payload": data,
        "dedup_key": f"ofac:{sdn_id}" if sdn_id else None,
        "hinted_signal_id": "sanctions_screening_result",
    }

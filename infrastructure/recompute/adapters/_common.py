"""V7 Phase 13 — shared HMAC verification for webhook adapters."""
from __future__ import annotations

import hashlib
import hmac
import os
from typing import Optional


def verify_hmac_sha256(body: bytes, signature: str, *, secret_env: str) -> bool:
    """Constant-time HMAC-SHA256 verification.

    Returns False (never raises) when:
      - secret env var is missing
      - signature header empty
      - hex-decoding fails
      - digests don't match
    """
    secret = os.environ.get(secret_env, "")
    if not secret or not signature:
        return False
    expected = hmac.new(
        secret.encode("utf-8"), body, hashlib.sha256,
    ).hexdigest()
    # Strip optional "sha256=" prefix and whitespace.
    candidate = signature.strip()
    if candidate.lower().startswith("sha256="):
        candidate = candidate[len("sha256="):]
    try:
        return hmac.compare_digest(expected, candidate.lower())
    except Exception:  # noqa: BLE001
        return False

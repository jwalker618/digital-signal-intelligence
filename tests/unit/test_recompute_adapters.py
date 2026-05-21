"""V7 Phase 13 — adapter HMAC verification + payload parsing."""
from __future__ import annotations

import hashlib
import hmac
import json
import os
from unittest.mock import patch

import pytest

from infrastructure.recompute.adapters import (
    _common,
    companies_house,
    ofac,
    sec_edgar,
)


def _sign(body: bytes, secret: str) -> str:
    return hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


SECRET = "phase13_test_secret"


class TestSecEdgar:
    def test_verify_hmac_accepts_valid_signature(self):
        body = b'{"accessionNumber":"0001234"}'
        with patch.dict(os.environ, {sec_edgar.HMAC_ENV: SECRET}):
            assert sec_edgar.verify_hmac(body, _sign(body, SECRET)) is True

    def test_verify_hmac_accepts_prefixed_signature(self):
        body = b'{"x":1}'
        with patch.dict(os.environ, {sec_edgar.HMAC_ENV: SECRET}):
            sig = f"sha256={_sign(body, SECRET)}"
            assert sec_edgar.verify_hmac(body, sig) is True

    def test_verify_hmac_rejects_tampered(self):
        body = b'{"x":1}'
        with patch.dict(os.environ, {sec_edgar.HMAC_ENV: SECRET}):
            assert sec_edgar.verify_hmac(body, _sign(b'{"x":2}', SECRET)) is False

    def test_verify_hmac_rejects_missing_secret(self):
        body = b'{"x":1}'
        # Ensure secret absent.
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop(sec_edgar.HMAC_ENV, None)
            assert sec_edgar.verify_hmac(body, "anything") is False

    def test_parse_extracts_entity_filing_kwargs(self):
        body = json.dumps({
            "accessionNumber": "0001234-56-789",
            "cik": "0001065088",
        }).encode()
        kw = sec_edgar.parse(body)
        assert kw["event_type"] == "entity_filing"
        assert kw["source_feed"] == "sec_edgar"
        assert kw["entity_id"] == "0001065088"
        assert kw["dedup_key"] == "sec_edgar:0001234-56-789"
        assert kw["hinted_signal_id"] == "sec_filing_recency"


class TestCompaniesHouse:
    def test_parse_officer_change_maps_to_directorship(self):
        body = json.dumps({
            "resource_kind": "company-officers",
            "resource_id": "12345678",
            "event": {"transaction_id": "tx-abc"},
        }).encode()
        kw = companies_house.parse(body)
        assert kw["event_type"] == "entity_directorship"
        assert kw["entity_id"] == "12345678"
        assert kw["dedup_key"] == "companies_house:tx-abc"
        assert kw["hinted_signal_id"] == "director_litigation_history"

    def test_parse_filing_maps_to_entity_filing(self):
        body = json.dumps({
            "resource_kind": "company-filing",
            "resource_id": "12345678",
            "event": {"transaction_id": "tx-def"},
        }).encode()
        kw = companies_house.parse(body)
        assert kw["event_type"] == "entity_filing"
        assert kw["hinted_signal_id"] == "corporate_registry_routed"


class TestOfac:
    def test_parse_extracts_sanctions_update(self):
        body = json.dumps({"sdn_id": "SDN-9999", "entity_id": "AcmeCorp"}).encode()
        kw = ofac.parse(body)
        assert kw["event_type"] == "sanctions_update"
        assert kw["source_feed"] == "ofac"
        assert kw["entity_id"] == "AcmeCorp"
        assert kw["dedup_key"] == "ofac:SDN-9999"
        assert kw["hinted_signal_id"] == "sanctions_screening_result"


class TestCommonHMACSafety:
    def test_empty_signature_rejected(self):
        with patch.dict(os.environ, {"X_TEST_SECRET": "s"}):
            assert _common.verify_hmac_sha256(b"body", "", secret_env="X_TEST_SECRET") is False

    def test_invalid_hex_rejected(self):
        with patch.dict(os.environ, {"X_TEST_SECRET": "s"}):
            assert _common.verify_hmac_sha256(b"body", "not-hex-at-all", secret_env="X_TEST_SECRET") is False
